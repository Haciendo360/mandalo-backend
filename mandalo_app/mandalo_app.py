import reflex as rx

from .components.LoginView import login_view
from .components.KYC_Dashboard import kyc_dashboard
from .components.AdminKYCView import admin_kyc_view
from .components.Mapa_Tracking import mapa_tracking_view

# # Se instancia la aplicación
app = rx.App(
    theme=rx.theme(
        appearance="light",
        has_background=True,
        radius="large",
        accent_color="teal",
    )
)

# Vistas PWA
app.add_page(login_view, route="/", title="MANDALO - Login")
app.add_page(kyc_dashboard, route="/kyc", title="MANDALO - KYC Dashboard")
app.add_page(admin_kyc_view, route="/admin/kyc", title="MANDALO - Admin KYC")
app.add_page(mapa_tracking_view, route="/map", title="MANDALO - Map Tracking")
