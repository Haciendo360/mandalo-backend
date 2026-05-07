from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
from mandalo_app.utils.auth import require_kyc_level
from mandalo_app.utils.supabase_client import get_supabase_client

router = APIRouter(prefix="/api/kyc", tags=["KYC"])

class DocumentUpdate(BaseModel):
    document_id: str
    action: str  # 'aprobar' o 'rechazar'

@router.get("/status")
def get_kyc_status(user_id: str = Depends(require_kyc_level(1))) -> Dict[str, Any]:
    """
    Endpoint de prueba para usuarios con Nivel 1+.
    """
    return {"message": "You have at least KYC Nivel 1", "user_id": user_id}

@router.post("/review")
def review_kyc_document(data: DocumentUpdate, admin_id: str = Depends(require_kyc_level(3))) -> Dict[str, Any]:
    """
    Endpoint de administración para aprobar o rechazar documentos.
    Requiere Nivel 3 (Admin / Premium).
    """
    supabase = get_supabase_client()
    try:
        if data.action not in ["aprobar", "rechazar"]:
            raise HTTPException(status_code=400, detail="Acción no válida")
        
        nuevo_estado = "aprobado" if data.action == "aprobar" else "rechazado"
        
        # Actualizamos el estado del documento
        response = supabase.table("kyc_documentos").update(
            {"estado_aprobacion": nuevo_estado}
        ).eq("id", data.document_id).execute()
        
        if not response.data:
             raise HTTPException(status_code=404, detail="Documento no encontrado o no actualizado")
             
        # Si la acción fue aprobar, hipotéticamente deberíamos revisar si hay que subirle el nivel al usuario
        # Por simplicidad, aumentaremos el nivel_verificacion del usuario a 2 si un doc es aprobado
        if data.action == "aprobar":
            usuario_id = response.data[0]['usuario_id']
            # Supongamos que subimos a Nivel 2
            supabase.table("perfiles").update({"nivel_verificacion": 2}).eq("id", usuario_id).execute()
        
        return {"message": f"Documento {nuevo_estado} exitosamente"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
