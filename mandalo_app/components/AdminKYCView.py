import reflex as rx
from mandalo_app.utils.supabase_client import get_supabase_client
from mandalo_app.components.navbar import navbar

GRADIENT = "linear-gradient(135deg, #FF6B00 0%, #FFB347 100%)"
SURFACE  = "#13131A"
ACCENT   = "#FF6B00"


class AdminKYCState(rx.State):
    documentos: list[dict] = []
    is_loading: bool = False
    error: str = ""
    success: str = ""

    async def on_mount(self):
        self.is_loading = True
        try:
            client = get_supabase_client()
            res = client.table("kyc_documentos").select(
                "id, usuario_id, tipo_documento, url_archivo, estado_aprobacion, created_at"
            ).order("created_at", desc=True).limit(50).execute()
            self.documentos = res.data or []
        except Exception as e:
            self.error = str(e)
        self.is_loading = False

    async def aprobar_documento(self, doc_id: str):
        self.success = ""
        self.error = ""
        try:
            client = get_supabase_client()
            res = client.rpc("review_kyc_document_admin", {
                "p_doc_id": doc_id, "p_action": "aprobar"
            }).execute()
            # Fallback directo si no existe el RPC
            if not res.data:
                upd = client.table("kyc_documentos").update(
                    {"estado_aprobacion": "aprobado"}
                ).eq("id", doc_id).execute()
                if upd.data:
                    uid = upd.data[0]["usuario_id"]
                    client.table("perfiles").update(
                        {"nivel_verificacion": 2}
                    ).eq("id", uid).execute()
            self.success = "Documento aprobado exitosamente"
            await self.on_mount()
        except Exception as e:
            self.error = str(e)

    async def rechazar_documento(self, doc_id: str):
        self.success = ""
        self.error = ""
        try:
            client = get_supabase_client()
            client.table("kyc_documentos").update(
                {"estado_aprobacion": "rechazado"}
            ).eq("id", doc_id).execute()
            self.success = "Documento rechazado"
            await self.on_mount()
        except Exception as e:
            self.error = str(e)


def estado_chip(estado: str) -> rx.Component:
    colores = {
        "pendiente": ("#FFD700", "rgba(255,215,0,0.1)", "rgba(255,215,0,0.3)"),
        "aprobado":  ("#00E676", "rgba(0,230,118,0.1)", "rgba(0,230,118,0.3)"),
        "rechazado": ("#FF4757", "rgba(255,71,87,0.1)",  "rgba(255,71,87,0.3)"),
    }
    color, bg, border = colores.get(estado, ("#A0A0B0", "rgba(160,160,176,0.1)", "rgba(160,160,176,0.3)"))
    return rx.box(
        rx.text(estado.upper(), size="1", weight="700", color=color),
        padding="4px 10px",
        background=bg,
        border=f"1px solid {border}",
        border_radius="20px",
        display="inline-flex",
        align_items="center",
    )


def doc_row(doc: dict) -> rx.Component:
    return rx.table.row(
        rx.table.cell(
            rx.text(doc["id"][:8] + "...", size="1",
                    color="#5A5A6E", font_family="monospace"),
        ),
        rx.table.cell(
            rx.text(doc["usuario_id"][:10] + "...", size="2", color="#A0A0B0"),
        ),
        rx.table.cell(
            rx.hstack(
                rx.icon(tag="file-text", size=14, color=ACCENT),
                rx.text(doc["tipo_documento"], size="2", weight="500", color="white"),
                spacing="2", align="center",
            ),
        ),
        rx.table.cell(
            rx.cond(
                doc["url_archivo"] != "",
                rx.link(
                    rx.hstack(
                        rx.icon(tag="external-link", size=12, color=ACCENT),
                        rx.text("Ver Doc", size="1", color=ACCENT, weight="600"),
                        spacing="1",
                    ),
                    href=doc["url_archivo"],
                    is_external=True,
                    text_decoration="none",
                ),
                rx.text("Sin URL", size="1", color="#3A3A4E"),
            ),
        ),
        rx.table.cell(estado_chip(doc["estado_aprobacion"])),
        rx.table.cell(
            rx.hstack(
                rx.cond(
                    doc["estado_aprobacion"] == "pendiente",
                    rx.hstack(
                        rx.button(
                            rx.hstack(
                                rx.icon(tag="check", size=12, color="white"),
                                rx.text("Aprobar", size="1", weight="600", color="white"),
                                spacing="1",
                            ),
                            on_click=AdminKYCState.aprobar_documento(doc["id"]),
                            size="1",
                            style={"background": "rgba(0,230,118,0.15)",
                                   "border": "1px solid rgba(0,230,118,0.4)",
                                   "color": "#00E676",
                                   "border-radius": "8px",
                                   "cursor": "pointer",
                                   "padding": "5px 10px",
                                   "transition": "all 0.2s"},
                        ),
                        rx.button(
                            rx.hstack(
                                rx.icon(tag="x", size=12, color="white"),
                                rx.text("Rechazar", size="1", weight="600", color="white"),
                                spacing="1",
                            ),
                            on_click=AdminKYCState.rechazar_documento(doc["id"]),
                            size="1",
                            style={"background": "rgba(255,71,87,0.15)",
                                   "border": "1px solid rgba(255,71,87,0.4)",
                                   "color": "#FF4757",
                                   "border-radius": "8px",
                                   "cursor": "pointer",
                                   "padding": "5px 10px",
                                   "transition": "all 0.2s"},
                        ),
                        spacing="2",
                    ),
                    rx.text("—", color="#3A3A4E", size="2"),
                ),
                spacing="2",
            ),
        ),
        class_name="table-row",
        style={"border-bottom": "1px solid rgba(255,255,255,0.04)"},
    )


def admin_kyc_view() -> rx.Component:
    return rx.box(
        navbar(),
        rx.box(
            rx.vstack(
                # Header
                rx.hstack(
                    rx.vstack(
                        rx.hstack(
                            rx.icon(tag="shield-alert", size=26, color=ACCENT),
                            rx.text("Panel Admin — Revisión KYC", weight="800",
                                    font_size="1.5rem", color="white"),
                            spacing="3", align="center",
                        ),
                        rx.text("Aprueba o rechaza documentos para actualizar el nivel KYC de los usuarios.",
                                color="#A0A0B0", size="3"),
                        spacing="1", align_items="start",
                    ),
                    rx.spacer(),
                    rx.button(
                        rx.hstack(
                            rx.icon(tag="refresh-cw", size=14),
                            rx.text("Actualizar", size="2"),
                            spacing="2",
                        ),
                        on_click=AdminKYCState.on_mount,
                        size="2", variant="ghost", color_scheme="gray",
                    ),
                    width="100%", align="start",
                ),

                # Alerts
                rx.cond(
                    AdminKYCState.error != "",
                    rx.hstack(
                        rx.icon(tag="alert-circle", size=16, color="#FF4757"),
                        rx.text(AdminKYCState.error, color="#FF4757", size="2"),
                        spacing="2", padding="10px 14px",
                        border_radius="10px",
                        background="rgba(255,71,87,0.08)",
                        border="1px solid rgba(255,71,87,0.3)",
                        width="100%",
                    ),
                ),
                rx.cond(
                    AdminKYCState.success != "",
                    rx.hstack(
                        rx.icon(tag="check-circle", size=16, color="#00E676"),
                        rx.text(AdminKYCState.success, color="#00E676", size="2"),
                        spacing="2", padding="10px 14px",
                        border_radius="10px",
                        background="rgba(0,230,118,0.08)",
                        border="1px solid rgba(0,230,118,0.3)",
                        width="100%",
                        class_name="fade-in",
                    ),
                ),

                # Tabla
                rx.box(
                    rx.cond(
                        AdminKYCState.is_loading,
                        rx.center(rx.box(class_name="spinner"), padding="60px"),
                        rx.cond(
                            AdminKYCState.documentos.length() > 0,
                            rx.table.root(
                                rx.table.header(
                                    rx.table.row(
                                        *[rx.table.column_header_cell(
                                            rx.text(h, size="1", weight="600",
                                                    color="#5A5A6E",
                                                    text_transform="uppercase",
                                                    letter_spacing="0.05em"),
                                        ) for h in ["ID", "Usuario", "Tipo Doc",
                                                    "Archivo", "Estado", "Acciones"]],
                                    ),
                                ),
                                rx.table.body(
                                    rx.foreach(AdminKYCState.documentos, doc_row)
                                ),
                                width="100%",
                            ),
                            rx.center(
                                rx.vstack(
                                    rx.icon(tag="file-search", size=48, color="#2A2A3E"),
                                    rx.text("No hay documentos pendientes",
                                            color="#5A5A6E", size="3", weight="500"),
                                    rx.text("Los documentos nuevos aparecerán aquí",
                                            color="#3A3A4E", size="2"),
                                    spacing="2", align="center",
                                ),
                                padding="64px",
                            ),
                        ),
                    ),
                    padding="24px",
                    background=SURFACE,
                    border="1px solid rgba(255,255,255,0.06)",
                    border_radius="16px",
                    width="100%",
                    overflow_x="auto",
                ),

                width="100%",
                spacing="6",
                padding_bottom="48px",
            ),
            max_width="1200px",
            margin="0 auto",
            padding="2rem",
            on_mount=AdminKYCState.on_mount,
        ),
        background="#0A0A0F",
        min_height="100vh",
    )
