from fastapi import Request, HTTPException, Depends
from typing import Callable
from functools import wraps
from .supabase_client import get_supabase_client

def get_current_user_id(request: Request) -> str:
    """Extrae el token del header Authorization y obtiene el usuario de Supabase."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    
    token = auth_header.split(" ")[1]
    supabase = get_supabase_client()
    try:
        user_response = supabase.auth.get_user(token)
        if not user_response or not user_response.user:
             raise HTTPException(status_code=401, detail="Invalid token")
        return user_response.user.id
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Unauthorized: {str(e)}")

def require_kyc_level(nivel: int) -> Callable:
    """
    Dependencia de FastAPI / middleware para proteger endpoints.
    Nivel 1: OTP validado (Lectura)
    Nivel 2: Documento (Operaciones)
    Nivel 3: Premium (Biometría)
    
    Ejemplo de uso en endpoint:
    @app.get("/premium-data")
    def get_data(user_id: str = Depends(require_kyc_level(3))):
        ...
    """
    def check_kyc_level(request: Request) -> str:
        user_id = get_current_user_id(request)
        supabase = get_supabase_client()
        
        try:
            # Verify user's KYC level in DB
            response = supabase.table("perfiles").select("nivel_verificacion").eq("id", user_id).execute()
            if not response.data:
                raise HTTPException(status_code=403, detail="Perfil de usuario no encontrado")
            
            user_level = response.data[0].get("nivel_verificacion", 0)
            if user_level < nivel:
                raise HTTPException(
                    status_code=403, 
                    detail=f"Nivel KYC {nivel} requerido, tienes nivel {user_level}"
                )
            return user_id
        except HTTPException:
            raise
        except Exception as e:
             raise HTTPException(status_code=500, detail=f"Error validando KYC: {str(e)}")
             
    return check_kyc_level
