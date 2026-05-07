import pytest
from httpx import AsyncClient
from unittest.mock import MagicMock

@pytest.mark.asyncio
async def test_escrow_exitoso(async_client: AsyncClient, mock_supabase, mocker):
    # Mock de autenticación exitosa (Level 1 req para pagar)
    mocker.patch("mandalo_app.utils.auth.get_current_user_id", return_value="user_123")
    mock_supabase.table().select().eq().execute.return_value = MagicMock(data=[{"nivel_verificacion": 1}])
    
    mock_rpc_escrow = mocker.MagicMock()
    mock_rpc_escrow.execute.return_value = mocker.MagicMock(data=True)
    
    mock_rpc_release = mocker.MagicMock()
    mock_rpc_release.execute.return_value = mocker.MagicMock(data=True)

    def rpc_side_effect(procedure_name, params):
        if procedure_name == "congelar_fondos_pedido":
            return mock_rpc_escrow
        elif procedure_name == "liberar_pago_entrega":
            return mock_rpc_release
        return mocker.MagicMock()
        
    mock_supabase.rpc.side_effect = rpc_side_effect

    # 1. Pago (Escrow)
    res_pay = await async_client.post("/api/finance/pedidos/ped_123/pagar", json={"monto_exacto": 10.50}, headers={"Authorization": "Bearer tok"})
    assert res_pay.status_code == 200
    assert res_pay.json()["status"] == "escrow_retenido"
    assert "pin_entrega" in res_pay.json()
    
    # 2. Re-Mock auth to Operador Level 2
    mock_supabase.table().select().eq().execute.return_value = mocker.MagicMock(data=[{"nivel_verificacion": 2}])
    mocker.patch("mandalo_app.utils.auth.get_current_user_id", return_value="operator_123")
    
    # 3. Liberación
    res_release = await async_client.post("/api/finance/pedidos/ped_123/confirmar_entrega", json={"pin_seguridad": "1234"}, headers={"Authorization": "Bearer tok"})
    assert res_release.status_code == 200
    assert "Viaje verificado" in res_release.json()["message"]

@pytest.mark.asyncio
async def test_fallo_transaccional_rollback(async_client: AsyncClient, mock_supabase, mocker):
    mocker.patch("mandalo_app.utils.auth.get_current_user_id", return_value="user_123")
    mock_supabase.table().select().eq().execute.return_value = mocker.MagicMock(data=[{"nivel_verificacion": 1}])
    
    mock_rpc_fail = mocker.MagicMock()
    # Emulamos un Raise del SQL Error por fondos insuficientes
    mock_rpc_fail.execute.side_effect = Exception("Saldo insuficiente en el Escrow.")
    
    def rpc_side_effect(procedure_name, params):
         return mock_rpc_fail
    mock_supabase.rpc.side_effect = rpc_side_effect
    
    res_pay = await async_client.post("/api/finance/pedidos/ped_555/pagar", json={"monto_exacto": 1000.0}, headers={"Authorization": "Bearer tok"})
    assert res_pay.status_code == 400
    assert "Pago falló" in res_pay.json()["detail"]
