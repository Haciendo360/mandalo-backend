CREATE EXTENSION IF NOT EXISTS postgis;
-- Script para crear tablas y polÃ­ticas RLS para MANDALO

-- Activar RLS
-- Tabla Perfiles que extiende auth.users (Supabase Auth)
CREATE TABLE IF NOT EXISTS public.perfiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    rol TEXT NOT NULL CHECK (rol IN ('usuario', 'comercio', 'operador')),
    nivel_verificacion INTEGER NOT NULL DEFAULT 0 CHECK (nivel_verificacion IN (0, 1, 2, 3)),
    telefono TEXT,
    estado_cuenta TEXT NOT NULL DEFAULT 'activo' CHECK (estado_cuenta IN ('activo', 'suspendido', 'baneado')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Tabla KYC_Documentos
CREATE TABLE IF NOT EXISTS public.kyc_documentos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    usuario_id UUID NOT NULL REFERENCES public.perfiles(id) ON DELETE CASCADE,
    tipo_documento TEXT NOT NULL,
    url_archivo TEXT NOT NULL,
    estado_aprobacion TEXT NOT NULL DEFAULT 'pendiente' CHECK (estado_aprobacion IN ('pendiente', 'aprobado', 'rechazado')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- RLS (Row Level Security)
ALTER TABLE public.perfiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.kyc_documentos ENABLE ROW LEVEL SECURITY;

-- PolÃ­ticas para perfiles
-- Los usuarios pueden leer su propio perfil
CREATE POLICY "Users can view own profile" 
    ON public.perfiles FOR SELECT 
    USING (auth.uid() = id);

-- Los usuarios pueden actualizar su propio perfil (solo ciertos campos)
CREATE POLICY "Users can update own profile" 
    ON public.perfiles FOR UPDATE 
    USING (auth.uid() = id);

-- PolÃ­ticas para KYC
-- Los usuarios pueden ver sus propios documentos
CREATE POLICY "Users can view own KYC documents" 
    ON public.kyc_documentos FOR SELECT 
    USING (auth.uid() = usuario_id);

-- Los usuarios pueden subir sus propios documentos
CREATE POLICY "Users can insert own KYC documents" 
    ON public.kyc_documentos FOR INSERT 
    WITH CHECK (auth.uid() = usuario_id);

-- Trigger para crear perfil en auth.users (opcional, dependiendo del flujo)
/*
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS trigger AS $$
BEGIN
  INSERT INTO public.perfiles (id, rol, nivel_verificacion, telefono)
  VALUES (new.id, 'usuario', 0, '');
  RETURN new;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE PROCEDURE public.handle_new_user();
*/
-- Extensiones
CREATE EXTENSION IF NOT EXISTS postgis SCHEMA extensions;

-- Tabla para rastreo de operadores en TIEMPO REAL
CREATE TABLE IF NOT EXISTS public.ubicacion_operadores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    operador_id UUID NOT NULL REFERENCES public.perfiles(id) ON DELETE CASCADE,
    coordenadas geometry(Point, 4326) NOT NULL,
    estado_conexion TEXT NOT NULL DEFAULT 'activo' CHECK (estado_conexion IN ('activo', 'inactivo', 'en_ruta')),
    ultima_actualizacion TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- RLS
ALTER TABLE public.ubicacion_operadores ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Operador gestionar ubicacion" 
    ON public.ubicacion_operadores FOR ALL 
    USING (auth.uid() = operador_id);

CREATE POLICY "Usuarios pueden ver ubicaciones" 
    ON public.ubicacion_operadores FOR SELECT 
    USING (
        EXISTS (
            SELECT 1 FROM public.pedidos 
            WHERE pedidos.usuario_id = auth.uid() 
              AND pedidos.operador_id = ubicacion_operadores.operador_id 
              AND pedidos.estado IN ('asignado', 'recogido', 'en_transito')
        )
    );

-- ConfiguraciÃ³n de Supabase Realtime (WebSockets)
ALTER TABLE public.ubicacion_operadores REPLICA IDENTITY FULL;

BEGIN;
  DROP PUBLICATION IF EXISTS supabase_realtime;
  CREATE PUBLICATION supabase_realtime;
COMMIT;

ALTER PUBLICATION supabase_realtime ADD TABLE public.ubicacion_operadores;

-- FunciÃ³n RPC para calcular operadores mÃ¡s cercanos usando Indexing espacial de PostGIS
CREATE OR REPLACE FUNCTION public.obtener_operadores_cercanos(lat double precision, lng double precision, radio_km double precision)
RETURNS TABLE (
    operador_uuid UUID, 
    estado TEXT, 
    latitud double precision, 
    longitud double precision, 
    distancia_km double precision
)
LANGUAGE sql
SECURITY DEFINER
AS $$
  SELECT 
    operador_id,
    estado_conexion,
    ST_Y(coordenadas::geometry) as latitud,
    ST_X(coordenadas::geometry) as longitud,
    ST_Distance(
        coordenadas::geography, 
        ST_SetSRID(ST_MakePoint(lng, lat), 4326)::geography
    ) / 1000 AS distancia_km
  FROM public.ubicacion_operadores
  WHERE ST_DWithin(
    coordenadas::geography,
    ST_SetSRID(ST_MakePoint(lng, lat), 4326)::geography,
    radio_km * 1000
  )
  ORDER BY distancia_km ASC;
$$;
-- 1. Zonas de Fidelidad Operador
CREATE TABLE IF NOT EXISTS public.zonas_fidelidad_operador (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    operador_id UUID NOT NULL REFERENCES public.perfiles(id) ON DELETE CASCADE,
    zona_nombre TEXT NOT NULL,
    zona_geometria geometry(Polygon, 4326),
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
    origen_coordenadas geometry(Point, 4326) NOT NULL,
    destino_coordenadas geometry(Point, 4326) NOT NULL,
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

-- Ãndices geoespaciales crÃ­ticos para la escalabilidad de Fase 3
CREATE INDEX idx_pedidos_origen ON public.pedidos USING GIST(origen_coordenadas);
CREATE INDEX idx_zonas_geom ON public.zonas_fidelidad_operador USING GIST(zona_geometria);

-- ========================================================================
-- FUNCIONES RPC DE LOGÃSTICA PARA SUPABASE 
-- ========================================================================

-- A. Procedimiento Seguro para Aceptar Pedido con "Pessimistic Lock" (Previene Race Conditions MÃºltiples Operadores)
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
    COALESCE(z.puntuacion, 0) DESC,  -- 1er Criterio: Prioridad zonal de afiliaciÃ³n
    distancia_km ASC;                -- 2do Criterio: CercanÃ­a real GPS
END;
$$;
-- Tablas Financieras y de Fidelidad (Fase 4: Antigravity Financial Engine)

-- 1. Monederos (Wallets)
CREATE TABLE IF NOT EXISTS public.wallets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    usuario_id UUID NOT NULL REFERENCES public.perfiles(id) ON DELETE CASCADE,
    saldo_real NUMERIC(12,2) NOT NULL DEFAULT 0.00,
    saldo_mandalocoins NUMERIC(12,2) NOT NULL DEFAULT 0.00,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    CONSTRAINT saldo_positivo CHECK (saldo_real >= 0)
);

-- 2. Transacciones 
DO $$ BEGIN
    CREATE TYPE tipo_transaccion AS ENUM ('pago_envio', 'recarga', 'retiro', 'penalizacion', 'cashback', 'comision');
    CREATE TYPE estado_transaccion AS ENUM ('retenido', 'completado', 'revertido');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

CREATE TABLE IF NOT EXISTS public.transacciones (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pedido_id UUID REFERENCES public.pedidos(id),
    origen_wallet_id UUID REFERENCES public.wallets(id),
    destino_wallet_id UUID REFERENCES public.wallets(id),
    monto NUMERIC(12,2) NOT NULL,
    tipo tipo_transaccion NOT NULL,
    estado estado_transaccion NOT NULL DEFAULT 'completado',
    comentario TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 3. AÃ±adir tracking financiero al Pedido
ALTER TABLE public.pedidos ADD COLUMN IF NOT EXISTS pin_seguridad VARCHAR(6);
ALTER TABLE public.pedidos ADD COLUMN IF NOT EXISTS comision_plataforma NUMERIC(12,2) DEFAULT 0.00;

-- 4. Calificaciones y GamificaciÃ³n
CREATE TABLE IF NOT EXISTS public.reviews (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pedido_id UUID NOT NULL REFERENCES public.pedidos(id),
    evaluador_id UUID NOT NULL REFERENCES public.perfiles(id),
    evaluado_id UUID NOT NULL REFERENCES public.perfiles(id),
    puntuacion INTEGER NOT NULL CHECK (puntuacion >= 1 AND puntuacion <= 5),
    comentario TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

ALTER TABLE public.wallets ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.transacciones ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.reviews ENABLE ROW LEVEL SECURITY;

-- ========================================================================
-- MOTOR TRANSACCIONAL EXTREMO (ACID STORED PROCEDURES)
-- ========================================================================

-- A. Pagar Pedido (Congela el Saldo en Escrow previniendo Double-Spending)
CREATE OR REPLACE FUNCTION public.congelar_fondos_pedido(p_pedido_id UUID, p_usuario_id UUID, p_monto NUMERIC, p_pin VARCHAR)
RETURNS BOOLEAN
LANGUAGE plpgsql
AS $$
DECLARE
    v_wallet_origen UUID;
    v_saldo NUMERIC;
BEGIN
    -- Validar y restar saldo de origen utilizando BLOQUEO DE FILA ACTIVO
    SELECT id, saldo_real INTO v_wallet_origen, v_saldo 
    FROM public.wallets 
    WHERE usuario_id = p_usuario_id 
    FOR UPDATE;

    IF v_wallet_origen IS NULL THEN
        RAISE EXCEPTION 'Monedero virtual no encontrado para el usuario';
    END IF;

    IF v_saldo < p_monto THEN
        RAISE EXCEPTION 'Saldo insuficiente en el Escrow.';
    END IF;

    -- Descontar el saldo (sale de saldo_real)
    UPDATE public.wallets SET saldo_real = saldo_real - p_monto, updated_at = now() WHERE id = v_wallet_origen;
    
    -- Registrar envio en modo ESCROW (Retenido)
    INSERT INTO public.transacciones (pedido_id, origen_wallet_id, monto, tipo, estado)
    VALUES (p_pedido_id, v_wallet_origen, p_monto, 'pago_envio', 'retenido');

    -- Guardar PIN ultra-seguro y cambiar metadata del pedido a pagado list para despachar
    UPDATE public.pedidos SET pin_seguridad = p_pin, updated_at = now() WHERE id = p_pedido_id;

    RETURN TRUE;
END;
$$;

-- B. Liberar Pago Segun Proof of Delivery (Cashout al Operador)
CREATE OR REPLACE FUNCTION public.liberar_pago_entrega(p_pedido_id UUID, p_operador_id UUID, p_pin_intento VARCHAR)
RETURNS BOOLEAN
LANGUAGE plpgsql
AS $$
DECLARE
    v_pin_real VARCHAR;
    v_transaccion RECORD;
    v_wallet_destino UUID;
    v_comision NUMERIC;
    v_pago_operador NUMERIC;
BEGIN
    -- 1. Validar PIN mediante Lock Pesimista
    SELECT pin_seguridad INTO v_pin_real 
    FROM public.pedidos 
    WHERE id = p_pedido_id AND operador_id = p_operador_id AND estado = 'en_transito'
    FOR UPDATE;

    IF v_pin_real IS NULL OR v_pin_real != p_pin_intento THEN
        RAISE EXCEPTION 'CÃ³digo de entrega INVÃLIDO. El pago sigue retenido.';
    END IF;

    -- 2. Consolidar la TransacciÃ³n 'Retenido' original
    SELECT id, monto, origen_wallet_id INTO v_transaccion
    FROM public.transacciones
    WHERE pedido_id = p_pedido_id AND tipo = 'pago_envio' AND estado = 'retenido'
    FOR UPDATE;

    IF v_transaccion.id IS NULL THEN
        RAISE EXCEPTION 'Fallo de Escrow: TransacciÃ³n origen inexistente';
    END IF;

    SELECT id INTO v_wallet_destino FROM public.wallets WHERE usuario_id = p_operador_id FOR UPDATE;

    -- 3. Calcular matemÃ¡ticas exactas
    v_comision := ROUND((v_transaccion.monto * 0.15), 2);
    v_pago_operador := v_transaccion.monto - v_comision;

    -- Sumar saldo al wallet del Operador
    UPDATE public.wallets SET saldo_real = saldo_real + v_pago_operador, updated_at = now() WHERE id = v_wallet_destino;

    -- Concluir rastreo transaccional principal y liquidarlo
    UPDATE public.transacciones SET estado = 'completado', destino_wallet_id = v_wallet_destino WHERE id = v_transaccion.id;
    
    -- Agregar fee de compaÃ±ia
    INSERT INTO public.transacciones (pedido_id, origen_wallet_id, monto, tipo, estado)
    VALUES (p_pedido_id, v_transaccion.origen_wallet_id, v_comision, 'comision', 'completado');

    -- Terminar ciclo de Pedido
    UPDATE public.pedidos SET estado = 'entregado', comision_plataforma = v_comision, updated_at = now() WHERE id = p_pedido_id;

    RETURN TRUE;
END;
$$;

-- C. Funciones para Penalidad Directa AsÃ­ncrona (Penalties Inteligentes)
CREATE OR REPLACE FUNCTION public.aplicar_penalidad_cancelacion(p_pedido_id UUID, p_operador_id UUID)
RETURNS BOOLEAN
LANGUAGE plpgsql
AS $$
DECLARE
    v_estado_actual estado_pedido;
    v_wallet UUID;
BEGIN
    SELECT estado INTO v_estado_actual FROM public.pedidos WHERE id = p_pedido_id AND operador_id = p_operador_id FOR UPDATE;
    
    IF v_estado_actual IN ('asignado', 'recogido') THEN
        -- Degradamos temporalmente Nivel KYC del Operador (Nivel 3 -> Nivel 2 o Nivel 2 -> Nivel 1)
        UPDATE public.perfiles SET nivel_verificacion = GREATEST(1, nivel_verificacion - 1) WHERE id = p_operador_id;
        
        -- Quitamos operador del pedido para que reentre al pool
        UPDATE public.pedidos SET operador_id = NULL, estado = 'buscando_operador' WHERE id = p_pedido_id;
        
        -- Insertamos registro de la falta en transacciones si cobra multa:
        SELECT id INTO v_wallet FROM public.wallets WHERE usuario_id = p_operador_id;
        IF v_wallet IS NOT NULL THEN
            UPDATE public.wallets SET saldo_real = GREATEST(0, saldo_real - 5.00) WHERE id = v_wallet;
            INSERT INTO public.transacciones (pedido_id, origen_wallet_id, monto, tipo, estado) VALUES (p_pedido_id, v_wallet, 5.00, 'penalizacion', 'completado');
        END IF;

        RETURN TRUE;
    END IF;
    RETURN FALSE;
END;
$$;

-- D. FunciÃ³n para Cashback y GamificaciÃ³n
CREATE OR REPLACE FUNCTION public.procesar_cashback_por_review(p_pedido_id UUID, p_usuario_id UUID, p_monto_gasto NUMERIC)
RETURNS NUMERIC
LANGUAGE plpgsql
AS $$
DECLARE
    v_mandalocoins_generados NUMERIC;
    v_wallet UUID;
BEGIN
    v_mandalocoins_generados := ROUND(p_monto_gasto * 0.03, 2); 
    
    SELECT id INTO v_wallet FROM public.wallets WHERE usuario_id = p_usuario_id FOR UPDATE;
    IF v_wallet IS NOT NULL THEN
        UPDATE public.wallets SET saldo_mandalocoins = saldo_mandalocoins + v_mandalocoins_generados, updated_at = now() WHERE id = v_wallet;
        INSERT INTO public.transacciones (pedido_id, destino_wallet_id, monto, tipo, estado)
        VALUES (p_pedido_id, v_wallet, v_mandalocoins_generados, 'cashback', 'completado');
    END IF;

    RETURN v_mandalocoins_generados;
END;
$$;

