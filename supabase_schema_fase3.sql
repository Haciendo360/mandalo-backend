-- 1. Zonas de Fidelidad Operador
CREATE TABLE IF NOT EXISTS public.zonas_fidelidad_operador (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    operador_id UUID NOT NULL REFERENCES public.perfiles(id) ON DELETE CASCADE,
    zona_nombre TEXT NOT NULL,
    zona_geometria public.geometry(Polygon, 4326),
    puntuacion INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Estado enum
-- Es posible que postgres lance excepcion si el tipo de dato enum ya existe, usamos un try catch rustico o verificamos
DO $$ BEGIN
    CREATE TYPE estado_pedido AS ENUM ('creado', 'buscando_operador', 'asignado', 'recogido', 'en_transito', 'entregado', 'cancelado');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

CREATE TABLE IF NOT EXISTS public.pedidos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    usuario_id UUID NOT NULL REFERENCES public.perfiles(id),
    comercio_id UUID REFERENCES public.perfiles(id),
    operador_id UUID REFERENCES public.perfiles(id),
    estado estado_pedido NOT NULL DEFAULT 'creado',
    origen_coordenadas public.geometry(Point, 4326) NOT NULL,
    destino_coordenadas public.geometry(Point, 4326) NOT NULL,
    precio_calculado NUMERIC(10,2) NOT NULL,
    distancia_km NUMERIC(10,2) NOT NULL,
    tipo_vehiculo_requerido TEXT NOT NULL DEFAULT 'moto',
    nivel_kyc_requerido INTEGER DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Tabla Dummy para notificaciones Push web
CREATE TABLE IF NOT EXISTS public.notificaciones_push (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    operador_id UUID,
    pedido_id UUID,
    mensaje TEXT,
    creado TIMESTAMP DEFAULT now()
);

ALTER TABLE public.zonas_fidelidad_operador ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.pedidos ENABLE ROW LEVEL SECURITY;

-- Índices geoespaciales críticos para la escalabilidad de Fase 3
CREATE INDEX idx_pedidos_origen ON public.pedidos USING GIST(origen_coordenadas);
CREATE INDEX idx_zonas_geom ON public.zonas_fidelidad_operador USING GIST(zona_geometria);

-- ========================================================================
-- FUNCIONES RPC DE LOGÍSTICA PARA SUPABASE 
-- ========================================================================

-- A. Procedimiento Seguro para Aceptar Pedido con "Pessimistic Lock" (Previene Race Conditions Múltiples Operadores)
CREATE OR REPLACE FUNCTION public.asignar_pedido_seguro(p_pedido_id UUID, p_operador_id UUID)
RETURNS BOOLEAN
LANGUAGE plpgsql
AS $$
DECLARE
    v_estado estado_pedido;
BEGIN
    -- Bloquear el pedido utilizando FOR UPDATE. El primero que llega bloquea el row, los demas esperan.
    SELECT estado INTO v_estado 
    FROM public.pedidos 
    WHERE id = p_pedido_id 
    FOR UPDATE;

    -- Si alguien mas lo tomo mientras esperabamos el lock, el estado habra cambiado
    IF v_estado = 'buscando_operador' THEN
        UPDATE public.pedidos
        SET operador_id = p_operador_id,
            estado = 'asignado',
            updated_at = now()
        WHERE id = p_pedido_id;
        RETURN TRUE;
    END IF;
    
    RETURN FALSE; -- Ya fue tomado por otro o cancelado
END;
$$;

-- B. Calculo crudo de distancia via base de datos
CREATE OR REPLACE FUNCTION public.distancia_entre_puntos(lat1 double precision, lng1 double precision, lat2 double precision, lng2 double precision)
RETURNS numeric
LANGUAGE sql AS $$
  SELECT (ST_Distance(
        ST_SetSRID(ST_MakePoint(lng1, lat1), 4326)::geography, 
        ST_SetSRID(ST_MakePoint(lng2, lat2), 4326)::geography
    ) / 1000.0)::numeric;
$$;

-- C. El Cerebro Espacial: obtener_operadores_candidatos cruzando con KYC y SCORE de fidelidad zonal
CREATE OR REPLACE FUNCTION public.obtener_operadores_candidatos(p_lat double precision, p_lng double precision, p_radio_km double precision)
RETURNS TABLE (
    operador_id UUID, 
    estado_conexion TEXT, 
    nivel_verificacion INTEGER,
    distancia_km double precision,
    score_zona INTEGER
)
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
  RETURN QUERY
  SELECT 
    u.operador_id,
    u.estado_conexion,
    p.nivel_verificacion,
    (ST_Distance(u.coordenadas::geography, ST_SetSRID(ST_MakePoint(p_lng, p_lat), 4326)::geography) / 1000.0) AS distancia_km,
    COALESCE(z.puntuacion, 0) AS score_zona
  FROM public.ubicacion_operadores u
  JOIN public.perfiles p ON p.id = u.operador_id
  LEFT JOIN public.zonas_fidelidad_operador z 
       ON z.operador_id = u.operador_id 
       AND ST_Contains(z.zona_geometria, ST_SetSRID(ST_MakePoint(p_lng, p_lat), 4326))
  WHERE ST_DWithin(u.coordenadas::geography, ST_SetSRID(ST_MakePoint(p_lng, p_lat), 4326)::geography, p_radio_km * 1000)
    AND u.estado_conexion IN ('activo', 'en_ruta')
  ORDER BY 
    COALESCE(z.puntuacion, 0) DESC,  -- 1er Criterio: Prioridad zonal de afiliación
    distancia_km ASC;                -- 2do Criterio: Cercanía real GPS
END;
$$;
