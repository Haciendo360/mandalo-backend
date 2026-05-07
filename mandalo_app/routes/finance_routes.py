from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, Any, Optional
from decimal import Decimal
import secrets
import string

from mandalo_app.utils.auth import require_kyc_level
from mandalo_app.utils.supabase_client import get_supabase_client

router = APIRouter(prefix="/api/finance", tags=["Finanzas", "Pagos y Fidelidad"])

class PagarPedidoReq(BaseModel):
    monto_exacto: Decimal

@router.post("/pedidos/{pedido_id}/pagar")
async def pagar_pedido_escrow(pedido_id: str, req: PagarPedidoReq, usuario_id: str = Depends(require_kyc_level(1))) -> Dict[str, Any]:
    """
    Toma fondos reales del Wallet del usuario y los congela en ESCROW Transaccional.
    Genera el PIN ultra seguro para Prueba de Entregas posteriores.
    """
    supabase = get_supabase_client()
    try:
        # Generamos PIN Alfanumerico 4 digitos
        pin_seguro = ''.join(secrets.choice(string.digits) for i in range(4))
        
        # Ejecutamos PL/PGSQL Stored Procedure Anti-Concurrencia (Garantiza ACID Compliance)
        res = supabase.rpc("congelar_fondos_pedido", {
            "p_pedido_id": pedido_id,
            "p_usuario_id": usuario_id,
            "p_monto": float(req.monto_exacto),
            "p_pin": pin_seguro
        }).execute()
        
        if not res.data:
            raise Exception("No se congelaron los fondos. Verifica el balance.")
            
        # El PIN se retorna al usuario que pagó para que lo entregue cara-a-cara al operador
        return {"status": "escrow_retenido", "pin_entrega": pin_seguro, "monto_congelado": req.monto_exacto}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Pago falló: {str(e)}")

class ConfirmarEntregaReq(BaseModel):
    pin_seguridad: str

@router.post("/pedidos/{pedido_id}/confirmar_entrega")
async def confirmar_entrega_y_liberar(pedido_id: str, req: ConfirmarEntregaReq, operador_id: str = Depends(require_kyc_level(2))) -> Dict[str, Any]:
    """
    El Operador envía el PIN provisto por el usuario receptor. Si pasa, los fondos del Escrow se liberan hacia él.
    """
    supabase = get_supabase_client()
    try:
        # Peticion pesimista Lock DB que rompe y hace Exception si el PIN es falso (para evitar Bruteforce basico)
        res = supabase.rpc("liberar_pago_entrega", {
            "p_pedido_id": pedido_id,
            "p_operador_id": operador_id,
            "p_pin_intento": req.pin_seguridad
        }).execute()
        
        if not res.data:
             raise Exception("Código incorrecto o paquete no retenido.")
             
        return {"message": "Viaje verificado por Proof of Delivery y Pago Liberado Instantáneamente en Wallet."}
    except Exception as e:
        raise HTTPException(status_code=403, detail=f"Fallo Prueba de Entrega: {str(e)}")

class ReviewReq(BaseModel):
    evaluado_id: str
    puntuacion: int # 1 a 5
    comentario: Optional[str] = ""

@router.post("/pedidos/{pedido_id}/calificar")
async def calificar_y_cashback(pedido_id: str, req: ReviewReq, eval_id: str = Depends(require_kyc_level(1))) -> Dict[str, Any]:
    """
    Permite dar una review. Motor Gamificación: Si se asigna 4 o 5 estrellas, 
    se transfiere el 3% del pago del pedido al saldo MANDALOCOINS del usuario.
    """
    if req.puntuacion < 1 or req.puntuacion > 5:
        raise HTTPException(status_code=400, detail="Score debe ser entre 1 y 5.")
        
    supabase = get_supabase_client()
    try:
        # Guardar observacion en tabla
        supabase.table("reviews").insert({
            "pedido_id": pedido_id,
            "evaluador_id": eval_id,
            "evaluado_id": req.evaluado_id,
            "puntuacion": req.puntuacion,
            "comentario": req.comentario
        }).execute()

        # Engine de Cashback Asíncrono
        mensaje_bonus = ""
        if req.puntuacion >= 4:
            # Obtener costo del viaje (o buscarlo desde la db directo es mejor, para simplificar pedimos query aqui)
            ped = supabase.table("pedidos").select("precio_calculado").eq("id", pedido_id).execute()
            if ped.data:
                gasto = ped.data[0]['precio_calculado']
                res_cb = supabase.rpc("procesar_cashback_por_review", {
                    "p_pedido_id": pedido_id,
                    "p_usuario_id": eval_id,
                    "p_monto_gasto": float(gasto)
                }).execute()
                mensaje_bonus = f" ¡Has ganado {res_cb.data} Mandalocoins de Cashback!"

        return {"message": "Calificación registrada." + mensaje_bonus}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/pedidos/{pedido_id}/cancelar_operador")
async def abandono_de_pedido(pedido_id: str, op_id: str = Depends(require_kyc_level(1))) -> Dict[str, Any]:
    """
    Smart Penalty System. Si un operario abandona la carga tras aceptar sin el PANIC_MODE, 
    recibe degradación de estatus o multas restadas directo al monedero.
    """
    supabase = get_supabase_client()
    try:
        # Usa Lock procedure
        res = supabase.rpc("aplicar_penalidad_cancelacion", {
            "p_pedido_id": pedido_id,
            "p_operador_id": op_id
        }).execute()
        
        if res.data:
            return {"message": "Te has retirado de la ruta. Tu nivel de Verificación se ha degradado con penalización financiera."}
        else:
            return {"message": "No estabas asignado a este pedido. Nada alterado."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
