import reflex as rx

from .components.LoginView import login_view, AuthState
from .components.RegisterView import register_view
from .components.KYC_Dashboard import kyc_dashboard
from .components.AdminKYCView import admin_kyc_view
from .components.AdminPanelView import admin_panel_view
from .components.Mapa_Tracking import mapa_tracking_view
from .components.Dashboard import dashboard_view
from .components.Wallet import wallet_view

# Aplicación con tema dark premium
app = rx.App(
    theme=rx.theme(
        appearance="dark",
        has_background=True,
        radius="large",
        accent_color="orange",
        gray_color="slate",
        panel_background="translucent",
    ),
    stylesheets=[
        "/custom.css",
    ],
    head_components=[
        rx.el.link(rel="icon", href="/favicon.ico?v=2", type="image/x-icon"),
        rx.el.link(rel="preconnect", href="https://fonts.googleapis.com"),
        rx.el.link(rel="preconnect", href="https://fonts.gstatic.com", crossorigin=""),
        rx.el.link(
            href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap",
            rel="stylesheet"
        ),
        rx.el.meta(name="theme-color", content="#FF6B00"),
    ],
)

# Rutas de la PWA
app.add_page(login_view,       route="/",            title="MÁNDALO — Inicia Sesión")
app.add_page(register_view,    route="/register",    title="MÁNDALO — Crear Cuenta")
app.add_page(dashboard_view,   route="/dashboard",   title="MÁNDALO — Dashboard")
app.add_page(kyc_dashboard,    route="/kyc",         title="MÁNDALO — Verificación KYC")
app.add_page(admin_kyc_view,   route="/admin/kyc",   title="MÁNDALO — Admin KYC")
app.add_page(admin_panel_view, route="/super-admin", title="MÁNDALO — Test Engine Admin")
app.add_page(mapa_tracking_view, route="/map",       title="MÁNDALO — Radar en Vivo")
app.add_page(wallet_view,      route="/wallet",      title="MÁNDALO — Mi Wallet")
