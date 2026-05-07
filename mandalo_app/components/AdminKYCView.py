import reflex as rx

class AdminKYCState(rx.State):
    # Estado ficticio, en realidad esto vendría por un GET request al backend
    documentos: list[dict] = [
        {"id": "doc-1", "usuario": "user123", "tipo": "Cédula", "estado": "pendiente"},
        {"id": "doc-2", "usuario": "comercio45", "tipo": "RIF Comercial", "estado": "pendiente"},
    ]
    
    def aprobar_documento(self, doc_id: str):
        # Aquí se llamaría a la API: POST /api/kyc/review {"document_id": doc_id, "action": "aprobar"}
        for doc in self.documentos:
            if doc["id"] == doc_id:
                doc["estado"] = "aprobado"
                
    def rechazar_documento(self, doc_id: str):
        for doc in self.documentos:
            if doc["id"] == doc_id:
                doc["estado"] = "rechazado"

def table_row(doc: dict) -> rx.Component:
    return rx.table.row(
        rx.table.cell(doc["id"]),
        rx.table.cell(doc["usuario"]),
        rx.table.cell(doc["tipo"]),
        rx.table.cell(
            rx.badge(doc["estado"], color_scheme=rx.cond(doc["estado"] == "aprobado", "green", rx.cond(doc["estado"] == "rechazado", "red", "yellow")))
        ),
        rx.table.cell(
            rx.hstack(
                rx.button("Aprobar", on_click=lambda: AdminKYCState.aprobar_documento(doc["id"]), color_scheme="green", size="1", disabled=doc["estado"] != "pendiente"),
                rx.button("Rechazar", on_click=lambda: AdminKYCState.rechazar_documento(doc["id"]), color_scheme="red", size="1", disabled=doc["estado"] != "pendiente")
            )
        )
    )

def admin_kyc_view() -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.heading("Administrador - Revisión de KYC", size="7"),
            rx.text("Aprobar o rechazar documentos para permitir a los usuarios subir de nivel."),
            
            rx.table.root(
                rx.table.header(
                    rx.table.row(
                        rx.table.column_header_cell("Doc ID"),
                        rx.table.column_header_cell("Usuario"),
                        rx.table.column_header_cell("Tipo Documento"),
                        rx.table.column_header_cell("Estado"),
                        rx.table.column_header_cell("Acciones"),
                    )
                ),
                rx.table.body(
                    rx.foreach(AdminKYCState.documentos, table_row)
                ),
                width="100%"
            ),
            
            width="100%",
            spacing="4",
            padding="2rem",
            bg=rx.color("gray", 1),
            border_radius="12px"
        ),
        width="100%",
        max_width="900px",
        margin="0 auto",
        padding_top="2rem"
    )
