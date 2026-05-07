-- Extensiones
CREATE EXTENSION IF NOT EXISTS postgis SCHEMA extensions;

-- Tabla para rastreo de operadores en TIEMPO REAL
CREATE TABLE IF NOT EXISTS public.ubicacion_operadores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    operador_id UUID NOT NULL REFERENCES public.perfiles(id) ON DELETE CASCADE,
    coordenadas public.geometry(Point, 4326) NOT NULL,
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
    USING (auth.uid() IS NOT NULL);

-- Configuración de Supabase Realtime (WebSockets)
ALTER TABLE public.ubicacion_operadores REPLICA IDENTITY FULL;

BEGIN;
  DROP PUBLICATION IF EXISTS supabase_realtime;
  CREATE PUBLICATION supabase_realtime;
COMMIT;

ALTER PUBLICATION supabase_realtime ADD TABLE public.ubicacion_operadores;

-- Función RPC para calcular operadores más cercanos usando Indexing espacial de PostGIS
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
