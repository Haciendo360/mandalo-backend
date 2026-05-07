from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, Any, Optional
from mandalo_app.utils.auth import require_kyc_level
from mandalo_app.utils.supabase_client import get_supabase_client
from mandalo_app.utils.allocation import motor_asignacion_pedidos

router = APIRouter(prefix="/api/pedidos", tags=["Cotización", "Pedir", "Máquina de Estados"])

class CotizacionReq(BaseModel):
    origen_lat: float
    origen_lng: float
    destino_lat: float
    destino_lng: float
    comercio_id: Optional[str] = None
    tipo_vehiculo: str = "moto"

@router.post("/cotizar")
def cotizar_pedido(req: CotizacionReq, bg_tasks: BackgroundTasks, usuario_id: str = Depends(require_kyc_level(1))) -> Dict[str, Any]:
    supabase = get_supabase_client()
    try:
        # Calcular de forma geométrica distancias
        q_dist = supabase.rpc("distancia_entre_puntos", {
            "lat1": req.origen_lat,
            "lng1": req.origen_lng,
            "lat2": req.destino_lat,
            "lng2": req.destino_lng
        }).execute()
        
        distancia_km = float(q_dist.data) if q_dist.data is not None else 3.5
        
        # Algoritmo Base de Dinero
        tarifa_base = 2.0
        tarifa_por_km = 1.2
        multiplicador_demanda = 1.15
        precio_estimado = tarifa_base + (distancia_km * tarifa_por_km * multiplicador_demanda)
        
        punto_origen = f"POINT({req.origen_lng} {req.origen_lat})"
        punto_destino = f"POINT({req.destino_lng} {req.destino_lat})"
        
        pedido_data = {
            "usuario_id": usuario_id,
            "comercio_id": req.comercio_id,
            "estado": "buscando_operador",
            "origen_coordenadas": punto_origen,
            "destino_coordenadas": punto_destino,
            "precio_calculado": round(precio_estimado, 2),
            "distancia_km": round(distancia_km, 2),
            "nivel_kyc_requerido": 2 # Logistica estandar exige Nivel 2
        }
        res = supabase.table("pedidos").insert(pedido_data).execute()
        
        if not res.data:
            raise HTTPException(status_code=500, detail="Fallo BD al registrar pedido. Reintente.")
            
        pedido_id = res.data[0]["id"]
        
        # Inyectar el Cerebro en el ciclo asíncrono
        bg_tasks.add_task(motor_asignacion_pedidos, pedido_id, req.origen_lat, req.origen_lng)
        
        return {
            "pedido_id": pedido_id, 
            "precio": round(precio_estimado, 2), 
            "distancia_km": round(distancia_km, 2)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class AceptarPedidoReq(BaseModel):
    operador_id: str

@router.post("/{pedido_id}/aceptar")
def aceptar_pedido(pedido_id: str, req: AceptarPedidoReq, op_token_uid: str = Depends(require_kyc_level(2))):
    """
    Ruta con protección Anti-Race Condition contra doble asignación.
    """
    supabase = get_supabase_client()
    # Usando el SQL con Lock previene doble booking (Pesimistic Lock PostgreSQL)
    res = supabase.rpc("asignar_pedido_seguro", {
        "p_pedido_id": pedido_id,
        "p_operador_id": req.operador_id
    }).execute()
    
    if not res.data:
        raise HTTPException(status_code=409, detail="Pedido expiró o fue aceptado por otro conductor más veloz.")
        
    return {"message": "Viaje asegurado."}

@router.post("/{pedido_id}/recoger")
def recoger_pedido(pedido_id: str, op_token_uid: str = Depends(require_kyc_level(2))):
    supabase = get_supabase_client()
    supabase.table("pedidos").update({"estado": "recogido", "updated_at": "now()"}).eq("id", pedido_id).execute()
    # Dispararía otra notificación al usuario...
    return {"message": "Paquete recogido. Comienza el viaje de entrega."}

@router.post("/{pedido_id}/entregar")
def entregar_pedido(pedido_id: str, op_token_uid: str = Depends(require_kyc_level(2))):
    supabase = get_supabase_client()
    supabase.table("pedidos").update({"estado": "entregado", "updated_at": "now()"}).eq("id", pedido_id).execute()
    return {"message": "Misión completada. Viaje finalizado."}
