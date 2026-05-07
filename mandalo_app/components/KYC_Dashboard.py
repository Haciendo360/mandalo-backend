import reflex as rx
from mandalo_app.utils.supabase_client import get_supabase_client
from mandalo_app.components.navbar import navbar

GRADIENT = "linear-gradient(135deg, #FF6B00 0%, #FFB347 100%)"
SURFACE  = "#13131A"
ACCENT   = "#FF6B00"


class KYCState(rx.State):
    nivel_actual: int = 1
    tipo_documento: str = "Cédula"
    rif_value: str = ""
    error_message: str = ""
    upload_success: bool = False
    is_uploading: bool = False

    def set_tipo_documento(self, value: str):
        self.tipo_documento = value
        self.error_message = ""

    def set_rif_value(self, value: str):
        self.rif_value = value

    async def on_mount(self):
        try:
            client = get_supabase_client()
            session = client.auth.get_session()
            if session and session.user:
                res = client.table("perfiles").select("nivel_verificacion").eq(
                    "id", session.user.id
                ).single().execute()
                if res.data:
                    self.nivel_actual = res.data["nivel_verificacion"]
        except Exception:
            pass

    async def handle_upload(self, files: list[rx.UploadFile]):
        if self.tipo_documento == "RIF Comercial" and not self.rif_value.startswith("C-"):
            self.error_message = "El RIF Comercial debe iniciar con 'C-' (ej: C-123456789)"
            return
        if not files:
            self.error_message = "Selecciona un archivo primero"
            return
        self.is_uploading = True
        self.error_message = ""
        try:
            client = get_supabase_client()
            session = client.auth.get_session()
            user_id = session.user.id if session and session.user else "anonimo"
            for file in files:
                content = await file.read()
                filename = f"{user_id}/{self.tipo_documento}/{file.filename}"
                client.storage.from_("kyc-documentos").upload(
                    filename, content,
                    file_options={"content-type": file.content_type or "application/octet-stream"}
                )
                file_url = client.storage.from_("kyc-documentos").get_public_url(filename)
                client.table("kyc_documentos").insert({
                    "usuario_id": user_id,
                    "tipo_documento": self.tipo_documento,
                    "url_archivo": file_url,
                    "estado_aprobacion": "pendiente",
                }).execute()
            self.upload_success = True
        except Exception as e:
            self.error_message = f"Error al subir: {str(e)[:80]}"
        self.is_uploading = False


def step_indicator(numero: int, titulo: str, desc: str,
                   completado: bool, activo: bool) -> rx.Component:
    return rx.vstack(
        rx.box(
            rx.text(
                rx.cond(completado, "✓", str(numero)),
                weight="bold",
                size="3",
                color=rx.cond(completado, "white",
                              rx.cond(activo, ACCENT, "#3A3A4E")),
            ),
            width="44px", height="44px",
            border_radius="50%",
            background=rx.cond(
                completado, GRADIENT,
                rx.cond(activo,
                        "rgba(255,107,0,0.15)",
                        "rgba(255,255,255,0.05)")
            ),
            border=rx.cond(
                completado, "none",
                rx.cond(activo,
                        f"2px solid {ACCENT}",
                        "2px solid rgba(255,255,255,0.1)")
            ),
            display="flex",
            align_items="center",
            justify_content="center",
            box_shadow=rx.cond(activo, "0 0 16px rgba(255,107,0,0.4)", "none"),
        ),
        rx.text(titulo, weight="bold", size="2",
                color=rx.cond(activo, "white", "#5A5A6E")),
        rx.text(desc, size="1", color="#3A3A4E",
                text_align="center", max_width="100px"),
        spacing="2", align="center",
    )


def kyc_dashboard() -> rx.Component:
    return rx.box(
        navbar(),
        rx.box(
            rx.vstack(
                # Header
                rx.vstack(
                    rx.hstack(
                        rx.icon(tag="shield", size=28, color=ACCENT),
                        rx.text("Verificación KYC", weight="bold",
                                font_size="1.6rem", color="white"),
                        spacing="3", align="center",
                    ),
                    rx.text(
                        "Completa los 3 niveles para acceder a todas las funciones de MANDALO.",
                        color="#A0A0B0", size="3",
                    ),
                    spacing="1", align_items="start", width="100%",
                ),

                # Stepper
                rx.box(
                    rx.hstack(
                        step_indicator(1, "Nivel 1", "OTP validado",
                                       KYCState.nivel_actual >= 1,
                                       KYCState.nivel_actual == 1),
                        rx.box(flex="1", height="2px",
                               background=rx.cond(KYCState.nivel_actual >= 2,
                                                  GRADIENT,
                                                  "rgba(255,255,255,0.08)")),
                        step_indicator(2, "Nivel 2", "Docs verificados",
                                       KYCState.nivel_actual >= 2,
                                       KYCState.nivel_actual == 2),
                        rx.box(flex="1", height="2px",
                               background=rx.cond(KYCState.nivel_actual >= 3,
                                                  GRADIENT,
                                                  "rgba(255,255,255,0.08)")),
                        step_indicator(3, "Nivel 3", "Premium/Élite",
                                       KYCState.nivel_actual >= 3,
                                       KYCState.nivel_actual == 3),
                        align="center", width="100%", spacing="0",
                    ),
                    padding="28px 32px",
                    background=SURFACE,
                    border="1px solid rgba(255,255,255,0.06)",
                    border_radius="16px",
                    width="100%",
                ),

                # Info del nivel actual
                rx.box(
                    rx.hstack(
                        rx.box(
                            rx.icon(tag="info", size=18, color=ACCENT),
                            padding="10px",
                            background="rgba(255,107,0,0.1)",
                            border_radius="10px",
                        ),
                        rx.vstack(
                            rx.text(
                                rx.cond(KYCState.nivel_actual == 1,
                                        "Nivel 1 activo: Puedes explorar y cotizar envíos",
                                        rx.cond(KYCState.nivel_actual == 2,
                                                "Nivel 2 activo: Puedes enviar y recibir pedidos",
                                                "Nivel 3 activo: Acceso completo — Operador Élite")),
                                weight="medium", color="white", size="3",
                            ),
                            rx.text(
                                rx.cond(KYCState.nivel_actual < 3,
                                        "Sube documento para avanzar al siguiente nivel",
                                        "¡Verificación completada! Todos los beneficios desbloqueados."),
                                color="#A0A0B0", size="2",
                            ),
                            spacing="1", align_items="start",
                        ),
                        spacing="4", align="center", width="100%",
                    ),
                    padding="16px 20px",
                    background="rgba(255,107,0,0.07)",
                    border="1px solid rgba(255,107,0,0.2)",
                    border_radius="12px",
                    width="100%",
                ),

                # Formulario de carga
                rx.box(
                    rx.vstack(
                        rx.hstack(
                            rx.icon(tag="upload-cloud", size=20, color=ACCENT),
                            rx.text("Subir Documento de Verificación",
                                    weight="bold", size="4", color="white"),
                            spacing="3", align="center",
                        ),
                        rx.box(height="4px"),

                        # Tipo de documento
                        rx.vstack(
                            rx.text("Tipo de Documento", size="2",
                                    weight="medium", color="#A0A0B0"),
                            rx.select(
                                ["Cédula", "RIF Personal", "RIF Comercial", "Licencia de Conducir"],
                                value=KYCState.tipo_documento,
                                on_change=KYCState.set_tipo_documento,
                                width="100%",
                            ),
                            width="100%", spacing="2",
                        ),

                        # Campo RIF
                        rx.cond(
                            KYCState.tipo_documento == "RIF Comercial",
                            rx.vstack(
                                rx.text("Número de RIF", size="2",
                                        weight="medium", color="#A0A0B0"),
                                rx.el.input(
                                    placeholder="C-123456789",
                                    value=KYCState.rif_value,
                                    on_change=KYCState.set_rif_value,
                                    style={"width": "100%", "padding": "10px 14px",
                                           "background": "rgba(255,255,255,0.05)",
                                           "border": "1px solid rgba(255,255,255,0.1)",
                                           "border-radius": "8px", "color": "white",
                                           "font-size": "13px", "outline": "none"},
                                ),
                                width="100%", spacing="2",
                                class_name="fade-in",
                            ),
                        ),

                        # Zona de upload
                        rx.upload(
                            rx.vstack(
                                rx.icon(tag="file-up", size=36,
                                        color="rgba(255,107,0,0.5)"),
                                rx.text("Arrastra tu documento aquí",
                                        weight="medium", color="white", size="3"),
                                rx.text("o haz click para seleccionar",
                                        color="#5A5A6E", size="2"),
                                rx.text("PDF, JPG, PNG — máx. 5MB",
                                        color="#3A3A4E", size="1"),
                                spacing="2", align="center",
                            ),
                            id="doc_upload",
                            multiple=False,
                            accept={"application/pdf": [".pdf"],
                                    "image/png": [".png"],
                                    "image/jpeg": [".jpg", ".jpeg"]},
                            padding="40px",
                            border="2px dashed rgba(255,107,0,0.3)",
                            border_radius="12px",
                            background="rgba(255,107,0,0.03)",
                            width="100%",
                            cursor="pointer",
                            _hover={"border_color": ACCENT,
                                    "background": "rgba(255,107,0,0.07)"},
                            transition="all 0.2s",
                        ),

                        # Mensajes
                        rx.cond(
                            KYCState.error_message != "",
                            rx.hstack(
                                rx.icon(tag="alert-circle", size=16, color="#FF4757"),
                                rx.text(KYCState.error_message,
                                        color="#FF4757", size="2"),
                                spacing="2", padding="10px 14px",
                                border_radius="10px",
                                background="rgba(255,71,87,0.1)",
                                border="1px solid rgba(255,71,87,0.3)",
                                width="100%",
                            ),
                        ),
                        rx.cond(
                            KYCState.upload_success,
                            rx.hstack(
                                rx.icon(tag="check-circle", size=16, color="#00E676"),
                                rx.text("¡Documento enviado! Tu solicitud está en revisión.",
                                        color="#00E676", size="2"),
                                spacing="2", padding="10px 14px",
                                border_radius="10px",
                                background="rgba(0,230,118,0.08)",
                                border="1px solid rgba(0,230,118,0.3)",
                                width="100%",
                                class_name="fade-in",
                            ),
                        ),

                        # Botón enviar
                        rx.el.button(
                            rx.cond(
                                KYCState.is_uploading,
                                rx.hstack(
                                    rx.box(class_name="spinner"),
                                    rx.text("Subiendo...", color="white", weight="medium"),
                                    spacing="2", align="center",
                                ),
                                rx.hstack(
                                    rx.icon(tag="send", size=16, color="white"),
                                    rx.text("Enviar para Revisión",
                                            color="white", weight="bold"),
                                    spacing="2", align="center",
                                ),
                            ),
                            on_click=KYCState.handle_upload(
                                rx.upload_files(upload_id="doc_upload")
                            ),
                            disabled=KYCState.is_uploading,
                            class_name="glow-button",
                            style={"width": "100%", "padding": "13px",
                                   "font-size": "14px"},
                        ),

                        width="100%", spacing="5",
                    ),
                    padding="28px",
                    background=SURFACE,
                    border="1px solid rgba(255,255,255,0.06)",
                    border_radius="16px",
                    width="100%",
                ),

                width="100%",
                spacing="6",
                padding_bottom="48px",
                max_width="700px",
            ),
            margin="0 auto",
            padding="2rem",
            on_mount=KYCState.on_mount,
        ),
        background="#0A0A0F",
        min_height="100vh",
    )
