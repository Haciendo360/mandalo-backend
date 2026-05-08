import reflex as rx
import os
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

    async def on_register(self):
        self.error = ""
        self.success = ""
        
        if not self.email or not self.password:
            self.error = "Completa correo y contraseña."
            return
            
        if self.password != self.confirm_password:
            self.error = "Las contraseñas no coinciden."
            return
            
        if len(self.password) < 6:
            self.error = "La contraseña debe tener al menos 6 caracteres."
            return

        self.is_loading = True
        try:
            client = get_supabase_client()
            res = client.auth.sign_up({
                "email": self.email,
                "password": self.password,
            })
            if res and res.user:
                # If sign up is successful, manually insert into perfiles table if the trigger didn't catch it
                # or just as a fallback (will fail gracefully if already exists due to trigger).
                try:
                    client.table("perfiles").insert({
                        "id": res.user.id,
                        "rol": self.role,
                        "nivel_verificacion": 0
                    }).execute()
                except Exception as e:
                    # Ignore duplicate key error if trigger handles it, else we might actually need an upsert.
                    # As a safe measure, an upsert is better:
                    client.table("perfiles").upsert({
                        "id": res.user.id,
                        "rol": self.role,
                        "nivel_verificacion": 0
                    }).execute()

                self.success = "¡Registro exitoso! Revisa tu correo o inicia sesión directamente."
                self.email = ""
                self.password = ""
                self.confirm_password = ""
            else:
                self.error = "Error al intentar crear la cuenta."
        except Exception as e:
            msg = str(e)
            if "User already registered" in msg:
                 self.error = "Este correo ya está registrado."
            else:
                 self.error = "Ocurrió un error en el registro."
        self.is_loading = False


def register_view() -> rx.Component:
    return rx.box(
        rx.flex(
            # Mitad Izquierda - Formulario
            rx.box(
                rx.vstack(
                    # Logo & Header
                    rx.box(
                        rx.text("🛵", font_size="64px",
                                style={"display": "inline-block", "transform": "scaleX(-1)", "animation": "float 3s ease-in-out infinite"}),
                        mb="4",
                    ),
                    rx.text(
                        "Crear Cuenta",
                        weight="bold",
                        font_size="3rem",
                        letter_spacing="-1px",
                        background=GRADIENT,
                        class_name="gradient-text",
                    ),
                    rx.text("Únete a la evolución logística.",
                            color="#A0A0B0", size="4", mb="6"),

                    # Mensajes
                    rx.cond(
                        RegisterState.error != "",
                        rx.box(
                            rx.text(RegisterState.error, color="#FF4757", size="2"),
                            background="rgba(255, 71, 87, 0.1)",
                            padding="12px", border_radius="8px", mb="4", width="100%",
                            border="1px solid rgba(255, 71, 87, 0.3)"
                        )
                    ),
                    rx.cond(
                        RegisterState.success != "",
                        rx.box(
                            rx.text(RegisterState.success, color="#00E676", size="2"),
                            background="rgba(0, 230, 118, 0.1)",
                            padding="12px", border_radius="8px", mb="4", width="100%",
                            border="1px solid rgba(0, 230, 118, 0.3)"
                        )
                    ),

                    # Formulario
                    rx.vstack(
                        rx.text("Correo Electrónico", size="2", weight="medium", color="#A0A0B0"),
                        rx.el.input(
                            type="email",
                            placeholder="tu@email.com",
                            value=RegisterState.email,
                            on_change=RegisterState.set_email,
                            class_name="custom-input",
                            style={"width": "100%", "padding": "12px", "border_radius": "8px", 
                                   "background": "rgba(255,255,255,0.03)", "border": "1px solid rgba(255,255,255,0.1)", 
                                   "color": "white", "outline": "none"}
                        ),

                        rx.text("Contraseña", size="2", weight="medium", color="#A0A0B0", mt="3"),
                        rx.el.input(
                            type="password",
                            placeholder="••••••••",
                            value=RegisterState.password,
                            on_change=RegisterState.set_password,
                            class_name="custom-input",
                            style={"width": "100%", "padding": "12px", "border_radius": "8px", 
                                   "background": "rgba(255,255,255,0.03)", "border": "1px solid rgba(255,255,255,0.1)", 
                                   "color": "white", "outline": "none"}
                        ),
                        
                        rx.text("Confirmar Contraseña", size="2", weight="medium", color="#A0A0B0", mt="3"),
                        rx.el.input(
                            type="password",
                            placeholder="••••••••",
                            value=RegisterState.confirm_password,
                            on_change=RegisterState.set_confirm_password,
                            class_name="custom-input",
                            style={"width": "100%", "padding": "12px", "border_radius": "8px", 
                                   "background": "rgba(255,255,255,0.03)", "border": "1px solid rgba(255,255,255,0.1)", 
                                   "color": "white", "outline": "none"}
                        ),

                        rx.text("Quiero registrararme como:", size="2", weight="medium", color="#A0A0B0", mt="3"),
                        rx.select(
                            ["usuario", "operador", "comercio"],
                            value=RegisterState.role,
                            on_change=RegisterState.set_role,
                            width="100%",
                        ),

                        rx.box(height="16px"),

                        rx.el.button(
                            rx.cond(
                                RegisterState.is_loading,
                                rx.hstack(
                                    rx.box(class_name="spinner"),
                                    rx.text("Procesando...", color="white", weight="medium"),
                                    spacing="2", align="center",
                                ),
                                rx.text("Suscribirse", color="white", weight="bold", size="3"),
                            ),
                            on_click=RegisterState.on_register,
                            disabled=RegisterState.is_loading,
                            class_name="glow-button",
                            style={"width": "100%", "padding": "14px", "font_size": "16px", "margin_top": "10px"}
                        ),
                        
                        rx.hstack(
                            rx.text("¿Ya tienes una cuenta?", color="#A0A0B0", size="2"),
                            rx.link("Inicia Sesión", href="/", color=ACCENT, weight="bold", size="2", text_decoration="none", _hover={"text_decoration": "underline"}),
                            spacing="2",
                            margin_top="24px",
                            justify="center",
                            width="100%"
                        ),

                        spacing="1",
                        align_items="start",
                        width="100%",
                        max_width="400px",
                    ),
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
            
            # Mitad Derecha - Imagen Visual
            rx.box(
                rx.box(
                    rx.vstack(
                        rx.text("Entra a MÁNDALO", weight="bold", font_size="2.5rem", color="white"),
                        rx.text("Conviértete en usuario, comercio activo, o un Operador sumamente veloz hoy mismo.", color="rgba(255,255,255,0.8)", size="4", max_width="400px", text_align="center"),
                        spacing="4",
                        align_items="center",
                        justify_content="center",
                        height="100%",
                        background="rgba(10, 10, 15, 0.7)",
                        backdrop_filter="blur(10px)",
                    ),
                    width="100%",
                    height="100%",
                    border_radius="24px",
                    overflow="hidden",
                    border="1px solid rgba(255,255,255,0.1)",
                    box_shadow="0 0 40px rgba(255, 107, 0, 0.15)",
                ),
                flex="1",
                display=["none", "none", "block"],
                padding="2rem",
                background="url('https://images.unsplash.com/photo-1581091226825-a6a2a5aee158?q=80&w=2070&auto=format&fit=crop') center/cover",
            ),
            
            width="100%",
            height="100vh",
            overflow="hidden", # Para prevenir scroll global
        ),
        background="#0A0A0F",
    )
