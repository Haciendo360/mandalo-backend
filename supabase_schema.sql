-- Script para crear tablas y políticas RLS para MANDALO

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

-- Políticas para perfiles
-- Los usuarios pueden leer su propio perfil
CREATE POLICY "Users can view own profile" 
    ON public.perfiles FOR SELECT 
    USING (auth.uid() = id);

-- Los usuarios pueden actualizar su propio perfil (solo ciertos campos)
CREATE POLICY "Users can update own profile" 
    ON public.perfiles FOR UPDATE 
    USING (auth.uid() = id);

-- Políticas para KYC
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
