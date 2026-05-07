import reflex as rx
import os
from mandalo_app.utils.supabase_client import get_supabase_client

GRADIENT  = "linear-gradient(135deg, #FF6B00 0%, #FFB347 100%)"
DARK_BG   = "#0A0A0F"
SURFACE   = "#13131A"
ACCENT    = "#FF6B00"


class AuthState(rx.State):
    email: str = ""
    password: str = ""
    error_message: str = ""
    is_loading: bool = False
    rol: str = "usuario"

    def set_email(self, value: str):
        self.email = value
        self.error_message = ""

    def set_password(self, value: str):
        self.password = value
        self.error_message = ""

    def set_rol(self, value: str):
        self.rol = value

    async def on_login(self):
        if not self.email or not self.password:
            self.error_message = "Por favor completa todos los campos"
            return
        self.is_loading = True
        self.error_message = ""
        try:
            client = get_supabase_client()
            result = client.auth.sign_in_with_password(
                {"email": self.email, "password": self.password}
            )
            if result.user:
                self.is_loading = False
                return rx.redirect("/dashboard")
            else:
                self.error_message = "Credenciales incorrectas"
        except Exception as e:
            msg = str(e)
            if "Invalid login" in msg or "invalid_credentials" in msg:
                self.error_message = "Email o contraseña incorrectos"
            elif "Email not confirmed" in msg:
                self.error_message = "Confirma tu correo antes de ingresar"
            else:
                self.error_message = f"Error: {msg[:80]}"
        self.is_loading = False


def rol_card(icon: str, label: str, value: str, desc: str) -> rx.Component:
    is_selected = AuthState.rol == value
    return rx.box(
        rx.vstack(
            rx.icon(tag=icon, size=22, color=rx.cond(is_selected, ACCENT, "#A0A0B0")),
            rx.text(label, weight="600", size="2",
                    color=rx.cond(is_selected, "white", "#A0A0B0")),
            rx.text(desc, size="1", color="#5A5A6E", text_align="center"),
            spacing="1", align="center",
        ),
        on_click=AuthState.set_rol(value),
        padding="12px 8px",
        border_radius="12px",
        border=rx.cond(is_selected,
                       f"2px solid {ACCENT}",
                       "2px solid rgba(255,255,255,0.06)"),
        background=rx.cond(is_selected,
                           "rgba(255,107,0,0.1)",
                           "rgba(255,255,255,0.03)"),
        cursor="pointer",
        transition="all 0.2s",
        flex="1",
        _hover={"border_color": ACCENT, "background": "rgba(255,107,0,0.07)"},
    )


def login_view() -> rx.Component:
    return rx.box(
        rx.hstack(
            # ======== PANEL IZQUIERDO — BRANDING ========
            rx.box(
                rx.vstack(
                    rx.box(height="60px"),
                    rx.box(
                        rx.text("🛵", font_size="64px",
                                style={"animation": "float 3s ease-in-out infinite"}),
                        mb="4",
                    ),
                    rx.text(
                        "MANDALO",
                        weight="900",
                        font_size="3.5rem",
                        letter_spacing="-1px",
                        style={"background": GRADIENT,
                               "-webkit-background-clip": "text",
                               "-webkit-text-fill-color": "transparent",
                               "background-clip": "text"},
                    ),
                    rx.text(
                        "Logística de última milla,",
                        color="rgba(255,255,255,0.8)",
                        size="4",
                        weight="400",
                    ),
                    rx.text(
                        "segura y en tiempo real.",
                        color="rgba(255,255,255,0.5)",
                        size="4",
                        weight="300",
                    ),
                    rx.box(height="40px"),
                    # Feature pills
                    rx.vstack(
                        *[rx.hstack(
                            rx.box(width="8px", height="8px",
                                   border_radius="50%",
                                   background=GRADIENT,
                                   flex_shrink="0"),
                            rx.text(feat, color="rgba(255,255,255,0.6)", size="3"),
                            spacing="3", align="center",
                        ) for feat in [
                            "Verificación KYC progresiva (3 niveles)",
                            "Rastreo GPS en tiempo real",
                            "Pago seguro con sistema Escrow",
                            "Cashback con MandaloCoins 🪙",
                        ]],
                        spacing="3", align_items="start",
                    ),
                    rx.spacer(),
                    rx.text("© 2026 Tecnimas · MANDALO",
                            color="rgba(255,255,255,0.2)", size="1"),
                    rx.box(height="32px"),
                    spacing="3",
                    align_items="start",
                    height="100%",
                    padding="3rem 2.5rem",
                ),
                flex="1",
                min_height="100vh",
                background=f"linear-gradient(160deg, #0A0A0F 0%, #1A0A00 50%, #0A0A0F 100%)",
                border_right="1px solid rgba(255,107,0,0.1)",
                display=["none", "none", "flex"],
                position="relative",
                overflow="hidden",
                # decorative circles
                _before={
                    "content": '""',
                    "position": "absolute",
                    "width": "400px",
                    "height": "400px",
                    "background": "radial-gradient(circle, rgba(255,107,0,0.12) 0%, transparent 70%)",
                    "top": "10%",
                    "right": "-100px",
                    "border-radius": "50%",
                },
            ),

            # ======== PANEL DERECHO — FORMULARIO ========
            rx.center(
                rx.box(
                    rx.vstack(
                        # Header
                        rx.vstack(
                            rx.text("Bienvenido de vuelta", weight="800",
                                    font_size="1.75rem", color="white",
                                    class_name="fade-in-up"),
                            rx.text("Ingresa a tu cuenta para continuar",
                                    color="#A0A0B0", size="3",
                                    class_name="fade-in"),
                            spacing="1", align_items="start", width="100%",
                        ),

                        rx.box(height="24px"),

                        # Selector de rol
                        rx.vstack(
                            rx.text("Soy un:", size="2", weight="500",
                                    color="#A0A0B0"),
                            rx.hstack(
                                rol_card("user", "Usuario",   "usuario",  "Envíos"),
                                rol_card("store", "Comercio", "comercio", "Despacho"),
                                rol_card("bike", "Operador",  "operador", "Reparto"),
                                spacing="2", width="100%",
                            ),
                            width="100%", spacing="2",
                        ),

                        rx.box(height="8px"),

                        # Error message
                        rx.cond(
                            AuthState.error_message != "",
                            rx.hstack(
                                rx.icon(tag="alert-circle", size=16, color="#FF4757"),
                                rx.text(AuthState.error_message,
                                        color="#FF4757", size="2"),
                                spacing="2",
                                padding="10px 14px",
                                border_radius="10px",
                                background="rgba(255,71,87,0.1)",
                                border="1px solid rgba(255,71,87,0.3)",
                                width="100%",
                            ),
                        ),

                        # Campos
                        rx.vstack(
                            rx.vstack(
                                rx.text("Correo electrónico", size="2",
                                        weight="500", color="#A0A0B0"),
                                rx.el.input(
                                    type="email",
                                    placeholder="tu@correo.com",
                                    on_change=AuthState.set_email,
                                    class_name="input-field",
                                    style={"width": "100%", "padding": "12px 14px",
                                           "font-size": "14px", "outline": "none",
                                           "background": "rgba(255,255,255,0.05)",
                                           "border": "1px solid rgba(255,255,255,0.1)",
                                           "border-radius": "10px",
                                           "color": "white"},
                                ),
                                width="100%", spacing="2",
                            ),
                            rx.vstack(
                                rx.text("Contraseña", size="2",
                                        weight="500", color="#A0A0B0"),
                                rx.el.input(
                                    type="password",
                                    placeholder="••••••••",
                                    on_change=AuthState.set_password,
                                    on_key_up=rx.cond(
                                        True, AuthState.on_login, None
                                    ),
                                    class_name="input-field",
                                    style={"width": "100%", "padding": "12px 14px",
                                           "font-size": "14px", "outline": "none",
                                           "background": "rgba(255,255,255,0.05)",
                                           "border": "1px solid rgba(255,255,255,0.1)",
                                           "border-radius": "10px",
                                           "color": "white"},
                                ),
                                width="100%", spacing="2",
                            ),
                            width="100%", spacing="4",
                        ),

                        # Botón principal
                        rx.el.button(
                            rx.cond(
                                AuthState.is_loading,
                                rx.hstack(
                                    rx.box(class_name="spinner"),
                                    rx.text("Verificando...", color="white",
                                            weight="600"),
                                    spacing="2", align="center",
                                ),
                                rx.text("Ingresar a MANDALO", color="white",
                                        weight="700", size="3"),
                            ),
                            on_click=AuthState.on_login,
                            class_name="glow-button",
                            style={"width": "100%", "padding": "14px",
                                   "font-size": "15px", "cursor": "pointer"},
                            disabled=AuthState.is_loading,
                        ),

                        # Divider
                        rx.hstack(
                            rx.box(flex="1", height="1px",
                                   background="rgba(255,255,255,0.08)"),
                            rx.text("o continúa con", color="#5A5A6E", size="1"),
                            rx.box(flex="1", height="1px",
                                   background="rgba(255,255,255,0.08)"),
                            align="center", width="100%",
                        ),

                        # Botón Google
                        rx.el.button(
                            rx.hstack(
                                rx.html(
                                    '<svg width="18" height="18" viewBox="0 0 18 18">'
                                    '<path fill="#4285F4" d="M16.51 8H8.98v3h4.3c-.18 1-.74 1.48-1.6 2.04v2.01h2.6a7.8 7.8 0 002.38-5.88c0-.57-.05-.66-.15-1.18z"/>'
                                    '<path fill="#34A853" d="M8.98 17c2.16 0 3.97-.72 5.3-1.94l-2.6-2a4.8 4.8 0 01-7.18-2.54H1.83v2.07A8 8 0 008.98 17z"/>'
                                    '<path fill="#FBBC05" d="M4.5 10.52a4.8 4.8 0 010-3.04V5.41H1.83a8 8 0 000 7.18l2.67-2.07z"/>'
                                    '<path fill="#EA4335" d="M8.98 4.18c1.17 0 2.23.4 3.06 1.2l2.3-2.3A8 8 0 001.83 5.4L4.5 7.49a4.77 4.77 0 014.48-3.3z"/>'
                                    '</svg>'
                                ),
                                rx.text("Continuar con Google", weight="600",
                                        color="white", size="3"),
                                spacing="3", align="center",
                                justify="center",
                            ),
                            style={"width": "100%", "padding": "12px",
                                   "background": "rgba(255,255,255,0.05)",
                                   "border": "1px solid rgba(255,255,255,0.1)",
                                   "border-radius": "10px",
                                   "cursor": "pointer",
                                   "transition": "all 0.2s"},
                        ),

                        rx.hstack(
                            rx.text("¿No tienes cuenta?", color="#5A5A6E", size="2"),
                            rx.link("Regístrate aquí", color=ACCENT, size="2",
                                    weight="600", href="/register"),
                            spacing="1",
                        ),

                        width="100%",
                        spacing="4",
                    ),
                    width="100%",
                    max_width="420px",
                    padding="2.5rem",
                    background=SURFACE,
                    border_radius="20px",
                    border=f"1px solid rgba(255,107,0,0.15)",
                    box_shadow="0 24px 64px rgba(0,0,0,0.6)",
                ),
                flex="1",
                min_height="100vh",
                background=DARK_BG,
                padding_x=["1rem", "2rem", "3rem"],
            ),

            spacing="0",
            width="100vw",
            min_height="100vh",
            align_items="stretch",
        ),
        background=DARK_BG,
        min_height="100vh",
    )
