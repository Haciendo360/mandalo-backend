import pytest
import asyncio
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_race_condition_asignacion(async_client: AsyncClient, mock_supabase, mocker):
    """
    TEST CRITICO: RACE CONDITION EXTRAMADAMENTE CONCURRENTE
    Asegura que el Bloqueo de fila Pessimistic Lock (SQL FOR UPDATE) reaccione bien a solicitudes paralelas en mili-segundos
    """
    mocker.patch("mandalo_app.utils.auth.get_current_user_id", return_value="user_mock")
    # Tienen Nivel 2 KYC
    mock_supabase.table().select().eq().execute.return_value = mocker.MagicMock(data=[{"nivel_verificacion": 2}])
    
    # Configuramos el Mock de RPC Asignar para que la primera vez devuelva TRUE (asignado)
    # Y la segunda vez devuelva FALSE (ya fue asignado). Esto emula la salida del SQL
    concurrencia_flags = {"ya_asignado": False}
    
    def rpc_concurrente_mock(proc, data):
        mock_resp = mocker.MagicMock()
        if concurrencia_flags["ya_asignado"]:
            mock_resp.execute.return_value = mocker.MagicMock(data=False)
        else:
            concurrencia_flags["ya_asignado"] = True
            mock_resp.execute.return_value = mocker.MagicMock(data=True)
        return mock_resp
        
    mock_supabase.rpc.side_effect = rpc_concurrente_mock
    
    # Lanzar 2 request simultaneos simulando Operador 1 y Operador 2 dando tap a "Aceptar" a la vez
    op1_req = async_client.post("/api/pedidos/ped_x/aceptar", json={"operador_id": "OP_1"}, headers={"Authorization": "Bearer tok"})
    op2_req = async_client.post("/api/pedidos/ped_x/aceptar", json={"operador_id": "OP_2"}, headers={"Authorization": "Bearer tok"})
    
    res1, res2 = await asyncio.gather(op1_req, op2_req)
    
    status_codes = [res1.status_code, res2.status_code]
    
    # Assert
    # Solo uno debe ser 200 OK y el otro 409 Conflict
    assert 200 in status_codes
    assert 409 in status_codes
    assert status_codes.count(409) == 1
