import pytest
from httpx import AsyncClient, ASGITransport
from api_server import app_fastapi
from unittest.mock import MagicMock

@pytest.fixture
async def async_client():
    # Setup test HTTP client connected to our FastAPI app directly
    async with AsyncClient(transport=ASGITransport(app=app_fastapi), base_url="http://test") as ac:
        yield ac

@pytest.fixture
def mock_supabase(mocker):
    import os
    # Si estamos en modo de integración, devolvemos el cliente real (ya autenticado por get_supabase_client si tiene el env cargado)
    if os.environ.get("MANDALO_ENV") == "integration":
        from mandalo_app.utils.supabase_client import get_supabase_client
        return get_supabase_client()
        
    # Mock global de dependencias para entornos unittests o de CI (sin base de datos real o sin conexión)
    mock_client = MagicMock()
    # Path everywhere it is imported
    mocker.patch("mandalo_app.utils.auth.get_supabase_client", return_value=mock_client)
    mocker.patch("mandalo_app.routes.finance_routes.get_supabase_client", return_value=mock_client)
    mocker.patch("mandalo_app.routes.orders_routes.get_supabase_client", return_value=mock_client)
    mocker.patch("mandalo_app.utils.allocation.get_supabase_client", return_value=mock_client)
    return mock_client
