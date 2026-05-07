import reflex as rx

class AuthState(rx.State):
    email: str = ""
    password: str = ""
    error_message: str = ""
    
    def on_login(self):
        # Aquí llamaríamos a backend o al cliente de supabase para SignIn
        # Por ahora simulamos
        if not self.email or not self.password:
            self.error_message = "Ingresa email y contraseña"
            return None
        else:
            self.error_message = ""
            return rx.redirect("/map")
            
    def set_email(self, value):
        self.email = value
        
    def set_password(self, value):
        self.password = value

def login_view() -> rx.Component:
    return rx.center(
        rx.vstack(
            rx.heading("MANDALO", size="8", weight="bold"),
            rx.text("Logística Segura y Confiable", color="gray"),
            
            rx.cond(
                AuthState.error_message != "",
                rx.text(AuthState.error_message, color="red", size="2")
            ),
            
            rx.input(
                placeholder="Correo electrónico", 
                on_change=AuthState.set_email, 
                width="100%",
                radius="large"
            ),
            rx.input(
                placeholder="Contraseña", 
                type="password", 
                on_change=AuthState.set_password, 
                width="100%",
                radius="large"
            ),
            
            rx.button(
                "Ingresar", 
                on_click=AuthState.on_login, 
                width="100%", 
                size="3",
                radius="large"
            ),
            
            rx.divider(),
            
            rx.button(
                rx.hstack(
                    rx.icon(tag="chrome"),
                    rx.text("Continuar con Google")
                ),
                width="100%", 
                size="3", 
                variant="outline",
                radius="large"
            ),
            
            width="100%",
            max_width="400px",
            spacing="4",
            padding="2rem",
            bg=rx.color("gray", 2),
            border_radius="16px",
            box_shadow="0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)"
        ),
        width="100vw",
        height="100vh",
        bg=rx.color("gray", 1)
    )
