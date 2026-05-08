import reflex as rx
import re
from mandalo_app.utils.supabase_client import get_supabase_client

GRADIENT = "linear-gradient(135deg, #FF6B00 0%, #FFB347 100%)"
SURFACE  = "#13131A"
ACCENT   = "#FF6B00"


class RegisterState(rx.State):
    email: str = ""
    password: str = ""
    confirm_password: str = ""
    role: str = "usuario"

    is_loading: bool = False
    error: str = ""
    success: str = ""

    # Password strength indicators
    has_min_length: bool = False
    has_uppercase: bool = False
    has_number: bool = False
    has_symbol: bool = False

    def set_email(self, value: str):
        self.email = value

    def set_password(self, value: str):
        self.password = value
        self.has_min_length = len(value) >= 8
        self.has_uppercase = bool(re.search(r"[A-Z]", value))
        self.has_number = bool(re.search(r"[0-9]", value))
        self.has_symbol = bool(re.search(r"[!@#$%^&*(),.?\":{}|<>_\-+=\[\]\\;'/~`]", value))

    def set_confirm_password(self, value: str):
        self.confirm_password = value

    def select_role(self, new_role: str):
        self.role = new_role

    async def on_register(self):
        self.error = ""
        self.success = ""

        if not self.email or not self.password:
            self.error = "Completa correo y contraseña."
            return

        if not self.has_min_length:
            self.error = "La contraseña debe tener al menos 8 caracteres."
            return

        if not self.has_uppercase:
            self.error = "La contraseña debe incluir al menos una letra mayúscula."
            return

        if not self.has_number:
            self.error = "La contraseña debe incluir al menos un número."
            return

        if not self.has_symbol:
            self.error = "La contraseña debe incluir al menos un símbolo (!@#$%...)."
            return

        if self.password != self.confirm_password:
            self.error = "Las contraseñas no coinciden."
            return

        self.is_loading = True
        try:
            client = get_supabase_client()
            res = client.auth.sign_up({
                "email": self.email,
                "password": self.password,
            })

            if res and res.user:
                # Insert profile with role
                try:
                    client.table("perfiles").upsert({
                        "id": res.user.id,
                        "rol": self.role,
                        "nivel_verificacion": 0
                    }).execute()
                except Exception:
                    pass  # Trigger may handle it

                self.success = "¡Registro exitoso! Revisa tu correo para confirmar o inicia sesión."
                self.email = ""
                self.password = ""
                self.confirm_password = ""
                self.has_min_length = False
                self.has_uppercase = False
                self.has_number = False
                self.has_symbol = False
            else:
                self.error = "No se pudo crear la cuenta. Intenta nuevamente."
        except Exception as e:
            msg = str(e)
            if "User already registered" in msg or "already been registered" in msg:
                self.error = "Este correo ya está registrado. Intenta iniciar sesión."
            elif "rate limit" in msg.lower():
                self.error = "Demasiados intentos. Espera unos segundos y reintenta."
            elif "invalid" in msg.lower() and "email" in msg.lower():
                self.error = "El formato del correo electrónico no es válido."
            elif "weak" in msg.lower() or "password" in msg.lower():
                self.error = f"Contraseña rechazada por Supabase: {msg[:120]}"
            else:
                self.error = f"Error del servidor: {msg[:150]}"
        self.is_loading = False


def password_check(label: str, is_valid) -> rx.Component:
    return rx.hstack(
        rx.icon(
            tag="check-circle",
            size=14,
            color=rx.cond(is_valid, "#00E676", "#3A3A4E"),
        ),
        rx.text(
            label,
            size="1",
            color=rx.cond(is_valid, "#00E676", "#5A5A6E"),
        ),
        spacing="1",
        align="center",
    )


def role_card(icon_tag: str, title: str, role_value: str, desc: str) -> rx.Component:
    is_active = RegisterState.role == role_value
    return rx.box(
        rx.vstack(
            rx.icon(
                tag=icon_tag, size=22,
                color=rx.cond(is_active, "white", "#5A5A6E"),
            ),
            rx.text(
                title, weight="bold", size="2",
                color=rx.cond(is_active, "white", "#A0A0B0"),
            ),
            rx.text(desc, size="1", color="#5A5A6E"),
            spacing="1", align="center",
        ),
        flex="1",
        padding="14px 8px",
        border_radius="12px",
        cursor="pointer",
        text_align="center",
        background=rx.cond(is_active, "rgba(255,107,0,0.15)", "rgba(255,255,255,0.03)"),
        border=rx.cond(is_active, f"2px solid {ACCENT}", "2px solid rgba(255,255,255,0.06)"),
        box_shadow=rx.cond(is_active, "0 0 16px rgba(255,107,0,0.25)", "none"),
        transition="all 0.2s ease",
        on_click=RegisterState.select_role(role_value),
        _hover={"border_color": ACCENT, "background": "rgba(255,107,0,0.08)"},
    )


INPUT_STYLE = {
    "width": "100%",
    "padding": "12px 14px",
    "border_radius": "10px",
    "background": "rgba(255,255,255,0.04)",
    "border": "1px solid rgba(255,255,255,0.1)",
    "color": "white",
    "font_size": "14px",
    "outline": "none",
    "transition": "border 0.2s",
}


def register_view() -> rx.Component:
    return rx.box(
        rx.flex(
            # ======== PANEL IZQUIERDO — FORMULARIO ========
            rx.box(
                rx.vstack(
                    rx.box(height="40px"),

                    # Logo
                    rx.box(
                        rx.text("🛵", font_size="56px",
                                style={"display": "inline-block", "transform": "scaleX(-1)"}),
                        style={"animation": "float 3s ease-in-out infinite"},
                        mb="2",
                    ),
                    rx.text(
                        "Crear Cuenta",
                        weight="bold",
                        font_size="2.5rem",
                        letter_spacing="-1px",
                        background=GRADIENT,
                        class_name="gradient-text",
                    ),
                    rx.text("Únete a la revolución logística de MÁNDALO.",
                            color="#A0A0B0", size="3", mb="4"),

                    # ---- Mensajes ----
                    rx.cond(
                        RegisterState.error != "",
                        rx.hstack(
                            rx.icon(tag="alert-circle", size=16, color="#FF4757"),
                            rx.text(RegisterState.error, color="#FF4757", size="2"),
                            spacing="2",
                            padding="10px 14px",
                            border_radius="10px",
                            background="rgba(255,71,87,0.08)",
                            border="1px solid rgba(255,71,87,0.3)",
                            width="100%",
                        ),
                    ),
                    rx.cond(
                        RegisterState.success != "",
                        rx.hstack(
                            rx.icon(tag="check-circle", size=16, color="#00E676"),
                            rx.text(RegisterState.success, color="#00E676", size="2"),
                            spacing="2",
                            padding="10px 14px",
                            border_radius="10px",
                            background="rgba(0,230,118,0.08)",
                            border="1px solid rgba(0,230,118,0.3)",
                            width="100%",
                        ),
                    ),

                    # ---- Formulario ----
                    rx.vstack(
                        # Email
                        rx.vstack(
                            rx.text("Correo Electrónico", size="2", weight="medium", color="#A0A0B0"),
                            rx.el.input(
                                type="email",
                                placeholder="tu@correo.com",
                                value=RegisterState.email,
                                on_change=RegisterState.set_email,
                                style=INPUT_STYLE,
                            ),
                            width="100%", spacing="1",
                        ),

                        # Contraseña
                        rx.vstack(
                            rx.text("Contraseña", size="2", weight="medium", color="#A0A0B0"),
                            rx.el.input(
                                type="password",
                                placeholder="Mínimo 8 caracteres",
                                value=RegisterState.password,
                                on_change=RegisterState.set_password,
                                style=INPUT_STYLE,
                            ),
                            # Validaciones en tiempo real
                            rx.hstack(
                                password_check("8+ chars", RegisterState.has_min_length),
                                password_check("Mayúsc.", RegisterState.has_uppercase),
                                password_check("Número", RegisterState.has_number),
                                password_check("Símbolo", RegisterState.has_symbol),
                                spacing="3",
                                flex_wrap="wrap",
                                mt="1",
                            ),
                            width="100%", spacing="1",
                        ),

                        # Confirmar
                        rx.vstack(
                            rx.text("Confirmar Contraseña", size="2", weight="medium", color="#A0A0B0"),
                            rx.el.input(
                                type="password",
                                placeholder="Repite tu contraseña",
                                value=RegisterState.confirm_password,
                                on_change=RegisterState.set_confirm_password,
                                style=INPUT_STYLE,
                            ),
                            width="100%", spacing="1",
                        ),

                        # Selector de rol (tarjetas)
                        rx.vstack(
                            rx.text("Quiero registrarme como:", size="2", weight="medium", color="#A0A0B0"),
                            rx.hstack(
                                role_card("user", "Usuario", "usuario", "Envíos"),
                                role_card("store", "Comercio", "comercio", "Despacho"),
                                role_card("bike", "Operador", "operador", "Reparto"),
                                spacing="2", width="100%",
                            ),
                            width="100%", spacing="2",
                        ),

                        rx.box(height="8px"),

                        # Botón
                        rx.el.button(
                            rx.cond(
                                RegisterState.is_loading,
                                rx.hstack(
                                    rx.box(class_name="spinner"),
                                    rx.text("Creando cuenta...", color="white", weight="medium"),
                                    spacing="2", align="center",
                                ),
                                rx.hstack(
                                    rx.icon(tag="user-plus", size=16, color="white"),
                                    rx.text("Crear mi cuenta", color="white", weight="bold", size="3"),
                                    spacing="2", align="center",
                                ),
                            ),
                            on_click=RegisterState.on_register,
                            disabled=RegisterState.is_loading,
                            class_name="glow-button",
                            style={"width": "100%", "padding": "14px", "font_size": "15px"},
                        ),

                        # Link de login
                        rx.hstack(
                            rx.text("¿Ya tienes una cuenta?", color="#5A5A6E", size="2"),
                            rx.link(
                                "Inicia Sesión",
                                href="/",
                                color=ACCENT,
                                weight="bold",
                                size="2",
                                text_decoration="none",
                                _hover={"text_decoration": "underline"},
                            ),
                            spacing="2", mt="5", justify="center", width="100%",
                        ),

                        spacing="4",
                        align_items="start",
                        width="100%",
                        max_width="420px",
                    ),

                    rx.spacer(),
                    rx.text("© 2026 Tecnisystem · MÁNDALO",
                            color="rgba(255,255,255,0.15)", size="1"),
                    rx.box(height="20px"),

                    spacing="2",
                    align_items="center",
                    width="100%",
                ),
                flex="1",
                height="100vh",
                overflow_y="auto",
                display="flex",
                flex_direction="column",
                align_items="center",
                justify_content="center",
                padding="2rem",
                background=SURFACE,
            ),

            # ======== PANEL DERECHO — HERO VISUAL ========
            rx.box(
                rx.center(
                    rx.vstack(
                        rx.text("🛵", font_size="80px",
                                style={"display": "inline-block", "transform": "scaleX(-1)", "animation": "float 3s ease-in-out infinite"}),
                        rx.text("Únete a MÁNDALO", weight="bold",
                                font_size="2.5rem", color="white"),
                        rx.text(
                            "Conviértete en usuario, comercio o un operador veloz.",
                            color="rgba(255,255,255,0.75)", size="4",
                            max_width="380px", text_align="center",
                        ),
                        spacing="4", align="center",
                    ),
                    height="100%",
                    background="rgba(10,10,15,0.75)",
                    backdrop_filter="blur(12px)",
                ),
                flex="1",
                display=["none", "none", "block"],
                background=f"linear-gradient(135deg, rgba(255,107,0,0.2), rgba(10,10,15,0.95)), url('https://images.unsplash.com/photo-1581091226825-a6a2a5aee158?q=80&w=2070&auto=format&fit=crop') center/cover",
            ),

            width="100%",
            height="100vh",
            overflow="hidden",
        ),
        background="#0A0A0F",
    )
