import reflex as rx
import os

# En producción, el backend Python de Reflex corre en Railway.
# En desarrollo local, corre en la misma máquina (localhost).
RAILWAY_URL = os.environ.get("RAILWAY_PUBLIC_DOMAIN", "")
backend_url = f"https://{RAILWAY_URL}" if RAILWAY_URL else ""

config = rx.Config(
    app_name="mandalo_app",
    api_url=backend_url or "http://localhost:8000",
    plugins=[
        rx.plugins.SitemapPlugin(),
        rx.plugins.TailwindV4Plugin(),
    ]
)