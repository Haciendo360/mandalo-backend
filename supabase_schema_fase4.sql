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

-- 3. Añadir tracking financiero al Pedido
ALTER TABLE public.pedidos ADD COLUMN IF NOT EXISTS pin_seguridad VARCHAR(6);
ALTER TABLE public.pedidos ADD COLUMN IF NOT EXISTS comision_plataforma NUMERIC(12,2) DEFAULT 0.00;

-- 4. Calificaciones y Gamificación
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
        RAISE EXCEPTION 'Código de entrega INVÁLIDO. El pago sigue retenido.';
    END IF;

    -- 2. Consolidar la Transacción 'Retenido' original
    SELECT id, monto, origen_wallet_id INTO v_transaccion
    FROM public.transacciones
    WHERE pedido_id = p_pedido_id AND tipo = 'pago_envio' AND estado = 'retenido'
    FOR UPDATE;

    IF v_transaccion.id IS NULL THEN
        RAISE EXCEPTION 'Fallo de Escrow: Transacción origen inexistente';
    END IF;

    SELECT id INTO v_wallet_destino FROM public.wallets WHERE usuario_id = p_operador_id FOR UPDATE;

    -- 3. Calcular matemáticas exactas
    v_comision := ROUND((v_transaccion.monto * 0.15), 2);
    v_pago_operador := v_transaccion.monto - v_comision;

    -- Sumar saldo al wallet del Operador
    UPDATE public.wallets SET saldo_real = saldo_real + v_pago_operador, updated_at = now() WHERE id = v_wallet_destino;

    -- Concluir rastreo transaccional principal y liquidarlo
    UPDATE public.transacciones SET estado = 'completado', destino_wallet_id = v_wallet_destino WHERE id = v_transaccion.id;
    
    -- Agregar fee de compañia
    INSERT INTO public.transacciones (pedido_id, origen_wallet_id, monto, tipo, estado)
    VALUES (p_pedido_id, v_transaccion.origen_wallet_id, v_comision, 'comision', 'completado');

    -- Terminar ciclo de Pedido
    UPDATE public.pedidos SET estado = 'entregado', comision_plataforma = v_comision, updated_at = now() WHERE id = p_pedido_id;

    RETURN TRUE;
END;
$$;

-- C. Funciones para Penalidad Directa Asíncrona (Penalties Inteligentes)
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

-- D. Función para Cashback y Gamificación
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
