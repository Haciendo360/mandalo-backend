from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List
from mandalo_app.utils.auth import require_kyc_level
from mandalo_app.utils.supabase_client import get_supabase_client

router = APIRouter(prefix="/api/ubicacion", tags=["Logistica", "Geoespacial"])

class UbicacionUpdate(BaseModel):
    latitud: float
    longitud: float
    estado: str = "activo"

@router.post("/actualizar")
async def actualizar_ubicacion(data: UbicacionUpdate, operador_id: str = Depends(require_kyc_level(2))) -> Dict[str, Any]:
    """
    Ruta para actualizar el GPS del operador.
    Requiere que el operador tenga validación KYC a nivel 2 o superior.
    Para el cliente se recomienda integrar De-bounding en los WebSockets (actualizar maximo cada 5s).
    """
    supabase = get_supabase_client()
    try:
        # Generar geometría tipo Point en texto bien conocido WKT Longitud Latitud
        punto = f"POINT({data.longitud} {data.latitud})"
        
        # Verificamos si existe registro previo con llamada asincrónica (si el cliente de api lo soporta, o standar async)
        existe = supabase.table("ubicacion_operadores").select("id").eq("operador_id", operador_id).execute()
        
        if existe.data:
            row_id = existe.data[0]['id']
            supabase.table("ubicacion_operadores").update({
                "coordenadas": punto,
                "estado_conexion": data.estado,
                "ultima_actualizacion": "now()"
            }).eq("id", row_id).execute()
        else:
            supabase.table("ubicacion_operadores").insert({
                "operador_id": operador_id,
                "coordenadas": punto,
                "estado_conexion": data.estado
            }).execute()
            
        return {"message": "Ubicación actualizada en la capa PostGIS"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class GeoQuery(BaseModel):
    latitud: float
    longitud: float
    radio_km: float

@router.post("/cercanos")
async def buscar_operadores(query: GeoQuery, user_id: str = Depends(require_kyc_level(1))) -> List[Any]:
    """
    Busca operadores según un radio estipulado, ejecutando una RPC sobre PostgreSQL en Supabase.
    """
    supabase = get_supabase_client()
    try:
        res = supabase.rpc("obtener_operadores_cercanos", {
            "lat": query.latitud, 
            "lng": query.longitud, 
            "radio_km": query.radio_km
        }).execute()
        return res.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
