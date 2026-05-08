import reflex as rx
import os
from mandalo_app.utils.supabase_client import get_supabase_client
from mandalo_app.components.navbar import navbar

GRADIENT = "linear-gradient(135deg, #FF6B00 0%, #FFB347 100%)"
SURFACE  = "#13131A"
ACCENT   = "#FF6B00"

class AdminPanelState(rx.State):
    # Auth
    is_authenticated_admin: bool = False
    admin_password_input: str = ""
    auth_error: str = ""

    # User Creation
    new_email: str = ""
    new_password: str = ""
    new_role: str = "operador"
    
    is_loading: bool = False
    error: str = ""
    success: str = ""

    def set_admin_password_input(self, value: str):
        self.admin_password_input = value

    def set_new_email(self, value: str):
        self.new_email = value

    def set_new_password(self, value: str):
        self.new_password = value

    def set_new_role(self, value: str):
        self.new_role = value

    def login_admin(self):
        # We use a preset super password for this dashboard
        real_password = os.getenv("ADMIN_PASSWORD", "admin123")
        if self.admin_password_input == real_password:
            self.is_authenticated_admin = True
            self.auth_error = ""
        else:
            self.auth_error = "Contraseña maestra incorrecta."
            self.admin_password_input = ""

    def logout_admin(self):
        self.is_authenticated_admin = False
        self.admin_password_input = ""
        self.error = ""
        self.success = ""

    async def create_test_user(self):
        self.error = ""
        self.success = ""
        
        if not self.new_email or not self.new_password:
            self.error = "Faltan datos de correo o contraseña."
            return
            
        self.is_loading = True
        try:
            client = get_supabase_client()
            
            # Since standard sign_up replaces the current active session in Supabase Python client,
            # we will create the user via sign_up, then force insert into perfiles, and optionally log out.
            # Using service role key is ideal for admin actions. Since we don't know if we have it,
            # we will attempt the standard sign up. NOTE: In a real backend, we would use auth.admin.create_user.
            
            res = client.auth.sign_up({
                "email": self.new_email,
                "password": self.new_password
            })
            
            if res and res.user:
                try:
                    # Insert in perfiles bypassing triggers just in case (if trigger exists, upsert avoids clash)
                    client.table("perfiles").upsert({
                        "id": res.user.id,
                        "rol": self.new_role,
                        "nivel_verificacion": 1 if self.new_role == "operador" else 0
                    }).execute()
                except Exception as ex:
                    pass # Ignore if duplicate from DB trigger
                
                self.success = f"¡Usuario {self.new_role} creado con éxito! UUID: {res.user.id[:8]}..."
                self.new_email = ""
                self.new_password = ""
            else:
                self.error = "Error al comunicarse con Auth Supabase."
        except Exception as e:
            msg = str(e)
            if "already registered" in msg:
                self.error = "Esa cuenta ya existe en Auth."
            else:
                self.error = f"Excepción de creación: {msg[:100]}"
                
        self.is_loading = False


def auth_wall() -> rx.Component:
    return rx.center(
        rx.vstack(
            rx.icon(tag="shield-alert", size=48, color=ACCENT),
            rx.text("Acceso Restringido", weight="bold", size="6", color="white"),
            rx.text("Panel Super Admin — MANDALO", color="#A0A0B0", size="2"),
            rx.box(height="10px"),
            rx.cond(
                AdminPanelState.auth_error != "",
                rx.text(AdminPanelState.auth_error, color="#FF4757", size="2")
            ),
            rx.el.input(
                type="password",
                placeholder="Contraseña Maestra",
                value=AdminPanelState.admin_password_input,
                on_change=AdminPanelState.set_admin_password_input,
                style={"width": "100%", "padding": "12px", "border_radius": "8px", 
                       "background": "rgba(255,255,255,0.05)", "border": "1px solid rgba(255,255,255,0.1)", 
                       "color": "white", "outline": "none", "text_align": "center"}
            ),
            rx.el.button(
                rx.text("Autenticar", color="white", weight="bold"),
                on_click=AdminPanelState.login_admin,
                class_name="glow-button",
                style={"width": "100%", "padding": "12px", "margin_top": "10px"}
            ),
            spacing="3",
            align_items="center",
            padding="40px",
            background=SURFACE,
            border="1px solid rgba(255,107,0,0.2)",
            border_radius="16px",
            box_shadow="0 0 40px rgba(255,107,0,0.1)",
            width="400px"
        ),
        padding="80px 20px"
    )

def dashboard_admin() -> rx.Component:
    return rx.box(
        # Header
        rx.hstack(
            rx.vstack(
                rx.hstack(
                    rx.icon(tag="terminal", size=26, color=ACCENT),
                    rx.text("Test Users Engine", weight="bold", font_size="1.5rem", color="white"),
                    spacing="3", align="center",
                ),
                rx.text("Genera usuarios falsos/de prueba para Operadores y Clientes.", color="#A0A0B0", size="3"),
                spacing="1", align_items="start",
            ),
            rx.spacer(),
            rx.button(
                rx.hstack(rx.icon(tag="log-out", size=14), rx.text("Cerrar Sesión", size="2"), spacing="2"),
                on_click=AdminPanelState.logout_admin,
                size="2", variant="ghost", color_scheme="red",
            ),
            width="100%", align="start",
        ),

        rx.box(height="30px"),

        # Create User Form
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.icon(tag="user-plus", size=20, color=ACCENT),
                    rx.text("Crear Datos de Prueba", weight="bold", size="4", color="white"),
                    spacing="3", align="center",
                ),
                
                rx.cond(
                    AdminPanelState.error != "",
                    rx.box(
                        rx.text(AdminPanelState.error, color="#FF4757", size="2"),
                        background="rgba(255,71,87,0.1)", padding="10px", border_radius="8px", width="100%"
                    )
                ),
                rx.cond(
                    AdminPanelState.success != "",
                    rx.box(
                        rx.text(AdminPanelState.success, color="#00E676", size="2"),
                        background="rgba(0,230,118,0.1)", padding="10px", border_radius="8px", width="100%"
                    )
                ),

                rx.text("Correo Electrónico (Ficticio)", size="2", color="#A0A0B0", mt="2"),
                rx.el.input(
                    placeholder="ej: mario.operador@test.com",
                    value=AdminPanelState.new_email,
                    on_change=AdminPanelState.set_new_email,
                    style={"width": "100%", "padding": "10px", "background": "rgba(255,255,255,0.05)", "color": "white", "border_radius": "6px", "border": "1px solid rgba(255,255,255,0.1)", "outline": "none"}
                ),

                rx.text("Contraseña (Min 6 chars)", size="2", color="#A0A0B0", mt="2"),
                rx.el.input(
                    type="password",
                    placeholder="••••••••",
                    value=AdminPanelState.new_password,
                    on_change=AdminPanelState.set_new_password,
                    style={"width": "100%", "padding": "10px", "background": "rgba(255,255,255,0.05)", "color": "white", "border_radius": "6px", "border": "1px solid rgba(255,255,255,0.1)", "outline": "none"}
                ),

                rx.text("Rol dentro de la PWA", size="2", color="#A0A0B0", mt="2"),
                rx.select(
                    ["operador", "usuario", "comercio"],
                    value=AdminPanelState.new_role,
                    on_change=AdminPanelState.set_new_role,
                    width="100%"
                ),

                rx.box(height="10px"),

                rx.el.button(
                    rx.cond(
                        AdminPanelState.is_loading,
                        rx.hstack(rx.box(class_name="spinner"), rx.text("Inyectando..."), spacing="2", align="center"),
                        rx.text("Crear Usuario"),
                    ),
                    on_click=AdminPanelState.create_test_user,
                    disabled=AdminPanelState.is_loading,
                    style={"width": "100%", "padding": "12px", "background": GRADIENT, "border_radius": "8px", "color": "white", "font_weight": "bold", "border": "none", "cursor": "pointer"}
                ),

                spacing="3",
                align_items="start",
                width="100%",
            ),
            padding="30px",
            background=SURFACE,
            border="1px solid rgba(255,255,255,0.06)",
            border_radius="16px",
            width="100%",
            max_width="600px",
        ),
        
        rx.text("IMPORTANTE: Estos usuarios son creados vía auth normal, si Supabase tiene Confirm Email activado tendrán que confirmarlo salvo que sea dummy. También alterará la sesión auth actual local de caché del navegador.", 
                color="rgba(255,255,255,0.3)", size="1", mt="4", max_width="600px")
    )


def admin_panel_view() -> rx.Component:
    return rx.box(
        navbar(),
        rx.box(
            rx.cond(
                AdminPanelState.is_authenticated_admin,
                dashboard_admin(),
                auth_wall(),
            ),
            max_width="1200px",
            margin="0 auto",
            padding="2rem"
        ),
        background="#0A0A0F",
        min_height="100vh",
    )
