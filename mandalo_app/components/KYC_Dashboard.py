import reflex as rx

class KYCState(rx.State):
    nivel_actual: int = 1
    tipo_documento: str = "Cédula"
    rif_value: str = ""
    error_message: str = ""
    upload_success: bool = False
    
    def set_tipo_documento(self, value):
        self.tipo_documento = value
        
    def set_rif_value(self, value):
        self.rif_value = value
        
    def handle_upload(self, files: list[rx.UploadFile]):
        # Validar si es RIF_Comercial
        if self.tipo_documento == "RIF Comercial":
            if not self.rif_value.startswith("C-"):
                self.error_message = "El RIF Comercial debe iniciar con 'C-'"
                self.upload_success = False
                return
                
        self.error_message = ""
        self.upload_success = True
        # En una app real, aquí se enviarían los archivos a Supabase Storage y a la API FastAPI.

def kyc_progress_bar(nivel: int) -> rx.Component:
    progreso = (nivel / 3) * 100
    return rx.vstack(
        rx.text(f"Nivel de Verificación Actual: {nivel} de 3", weight="bold"),
        rx.progress(value=progreso, max=100, width="100%", color_scheme="blue"),
        rx.hstack(
            rx.text("L1: OTP", size="1"),
            rx.spacer(),
            rx.text("L2: Docs", size="1"),
            rx.spacer(),
            rx.text("L3: Premium", size="1"),
            width="100%"
        ),
        width="100%",
        spacing="2"
    )

def kyc_dashboard() -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.heading("Dashboard KYC", size="7"),
            rx.text("Completa tu verificación progresiva para habilitar operaciones en la plataforma."),
            
            kyc_progress_bar(KYCState.nivel_actual),
            
            rx.divider(),
            
            rx.heading("Subir Documento", size="5"),
            rx.select(
                ["Cédula", "RIF Personal", "RIF Comercial", "Licencia"],
                value=KYCState.tipo_documento,
                on_change=KYCState.set_tipo_documento,
                width="100%"
            ),
            
            rx.cond(
                KYCState.tipo_documento == "RIF Comercial",
                rx.input(
                    placeholder="E.g. C-123456789", 
                    value=KYCState.rif_value,
                    on_change=KYCState.set_rif_value,
                    width="100%"
                )
            ),
            
            rx.upload(
                rx.vstack(
                    rx.button("Seleccionar Archivo"),
                    rx.text("Arrastre y suelte su archivo aquí o haga click")
                ),
                id="doc_upload",
                multiple=False,
                padding="2em",
                border="1px dashed var(--gray-8)"
            ),
            
            rx.button("Enviar para Revisión", on_click=KYCState.handle_upload(rx.upload_files(upload_id="doc_upload"))),
            
            rx.cond(
                KYCState.error_message != "",
                rx.text(KYCState.error_message, color="red")
            ),
            rx.cond(
                KYCState.upload_success,
                rx.text("Archivo enviado correctamente. Esperando aprobación.", color="green")
            ),
            
            width="100%",
            spacing="4",
            padding="2rem",
            bg=rx.color("gray", 2),
            border_radius="12px",
            box_shadow="md"
        ),
        width="100%",
        max_width="600px",
        margin="0 auto",
        padding_top="2rem"
    )
