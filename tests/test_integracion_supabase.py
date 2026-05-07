import pytest
import os
import uuid
import time
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_sanity_check_real_database(async_client: AsyncClient):
    """
    Este test NO SE EJECUTARÁ a menos que MANDALO_ENV sea 'integration'
    Verifica que podemos conectarnos a Mandalo_DB y consultar usuarios actuales.
    """
    if os.environ.get("MANDALO_ENV") != "integration":
        pytest.skip("Test de integración requiere que MANDALO_ENV=integration en el entorno (.env o PowerShell)")
        
    from mandalo_app.utils.supabase_client import get_supabase_client
    supabase = get_supabase_client()
    
    # 1. Realizar una consulta de prueba. Por ejemplo, contar cuantos perfiles existen.
    # En supabase "select" con configuracion count=exact, pero haremos un simple fetch del primer perfíl
    # No fallará la aserción de cantidad porque la RLS podría estar limitando la respuesta.
    # Pero lo importante es que no arroje excepcion de conexion (504, 401, ConnectionRefused, etc)
    try:
        response = supabase.table("perfiles").select("*").limit(1).execute()
        assert response is not None
        # Que se conecte no significa que devuelva algo (si RLS nos frena). Está bien con tal que no dé timeout ni de AuthError
    except Exception as e:
        pytest.fail(f"La base de datos Mandalo_DB arrojó un error o las credenciales son inválidas: {e}")
        
@pytest.mark.asyncio
async def test_integracion_rpc_real():
    """
    Llama remotamente a una funcion RPC (como calcular distancias crudas).
    Solo para comprobar que supabase RPC existe y esta bien parametrizado
    """
    if os.environ.get("MANDALO_ENV") != "integration":
        pytest.skip()
        
    from mandalo_app.utils.supabase_client import get_supabase_client
    supabase = get_supabase_client()
    
    # distancia entre dos puntos identicos deberia ser 0.0
    try:
        res = supabase.rpc("distancia_entre_puntos", {
            "lat1": 10.0,
            "lng1": -60.0,
            "lat2": 10.0,
            "lng2": -60.0
        }).execute()
        
        # O devuelve un string o float
        assert res is not None
        assert float(res.data) == 0.0
    except Exception as e:
        pytest.fail(f"Falla RPC en BD REAL. ¿Estás seguro que ejecutaste el MANDALO_MASTER_SCHEMA.sql allá? Detalle: {e}")
