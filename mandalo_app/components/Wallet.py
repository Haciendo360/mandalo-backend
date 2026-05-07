import reflex as rx
from mandalo_app.utils.supabase_client import get_supabase_client
from mandalo_app.components.navbar import navbar

GRADIENT = "linear-gradient(135deg, #FF6B00 0%, #FFB347 100%)"
SURFACE  = "#13131A"
ACCENT   = "#FF6B00"


class WalletState(rx.State):
    saldo_real: float = 0.0
    saldo_coins: float = 0.0
    transacciones: list[dict[str, str]] = []
    is_loading: bool = False
    error: str = ""

    async def on_mount(self):
        self.is_loading = True
        try:
            client = get_supabase_client()
            session = client.auth.get_session()
            user_id = session.user.id if session and session.user else None
            if user_id:
                w = client.table("wallets").select(
                    "saldo_real, saldo_mandalocoins"
                ).eq("usuario_id", user_id).single().execute()
                if w.data:
                    self.saldo_real  = float(w.data["saldo_real"])
                    self.saldo_coins = float(w.data["saldo_mandalocoins"])

                tx = client.table("transacciones").select(
                    "id, tipo, estado, monto, created_at"
                ).or_(
                    f"origen_wallet_id.eq.{user_id},"
                    f"destino_wallet_id.eq.{user_id}"
                ).order("created_at", desc=True).limit(20).execute()
                self.transacciones = tx.data or []
        except Exception as e:
            self.error = str(e)
        self.is_loading = False


def tipo_badge(tipo: str) -> rx.Component:
    iconos = {
        "pago_envio":  ("arrow-up-right",  "#FF4757", "rgba(255,71,87,0.1)"),
        "recarga":     ("arrow-down-left", "#00E676", "rgba(0,230,118,0.1)"),
        "retiro":      ("arrow-up-right",  "#FF4757", "rgba(255,71,87,0.1)"),
        "penalizacion":("alert-triangle",  "#FFD700", "rgba(255,215,0,0.1)"),
        "cashback":    ("gift",            "#BE6BD8", "rgba(190,107,216,0.1)"),
        "comision":    ("percent",         "#A0A0B0", "rgba(160,160,176,0.1)"),
    }
    icon, color, bg = iconos.get(tipo, ("circle", "#A0A0B0", "rgba(160,160,176,0.1)"))
    return rx.hstack(
        rx.box(
            rx.icon(tag=icon, size=14, color=color),
            padding="6px",
            background=bg,
            border_radius="8px",
        ),
        rx.text(tipo.replace("_", " ").title(), size="2",
                weight="medium", color="white"),
        spacing="2", align="center",
    )


def tx_row(tx: dict) -> rx.Component:
    return rx.table.row(
        rx.table.cell(tipo_badge(tx["tipo"])),
        rx.table.cell(
            rx.text(
                f"${tx['monto']}",
                weight="bold", size="3",
                color=rx.cond(
                    (tx["tipo"] == "recarga") | (tx["tipo"] == "cashback"),
                    "#00E676",
                    "#FF4757",
                ),
            ),
        ),
        rx.table.cell(
            rx.box(
                rx.text(tx["estado"], size="1", weight="medium"),
                padding="3px 8px",
                border_radius="20px",
                background=rx.cond(
                    tx["estado"] == "completado",
                    "rgba(0,230,118,0.1)",
                    rx.cond(
                        tx["estado"] == "retenido",
                        "rgba(255,215,0,0.1)",
                        "rgba(255,71,87,0.1)",
                    ),
                ),
                color=rx.cond(
                    tx["estado"] == "completado", "#00E676",
                    rx.cond(tx["estado"] == "retenido", "#FFD700", "#FF4757"),
                ),
                display="inline-flex",
                align_items="center",
            ),
        ),
        rx.table.cell(
            rx.text(tx["created_at"][:10], size="1", color="#5A5A6E"),
        ),
        class_name="table-row",
        style={"border-bottom": "1px solid rgba(255,255,255,0.04)"},
    )


def wallet_view() -> rx.Component:
    return rx.box(
        navbar(),
        rx.box(
            rx.vstack(
                # Header
                rx.vstack(
                    rx.hstack(
                        rx.icon(tag="wallet", size=26, color=ACCENT),
                        rx.text("Mi Wallet", weight="bold",
                                font_size="1.6rem", color="white"),
                        spacing="3", align="center",
                    ),
                    rx.text("Gestiona tu saldo y revisa el historial de movimientos.",
                            color="#A0A0B0", size="3"),
                    spacing="1", align_items="start", width="100%",
                ),

                # Cards de saldo
                rx.hstack(
                    rx.box(
                        rx.vstack(
                            rx.hstack(
                                rx.icon(tag="dollar-sign", size=20,
                                        color=ACCENT),
                                rx.text("Saldo Real", size="2",
                                        weight="medium", color="#A0A0B0"),
                                spacing="2", align="center",
                            ),
                            rx.text(
                                f"${WalletState.saldo_real:.2f}",
                                weight="bold",
                                font_size="2.4rem",
                                style={"background": GRADIENT,
                                       "-webkit-background-clip": "text",
                                       "-webkit-text-fill-color": "transparent"},
                                class_name="fade-in-up",
                            ),
                            rx.text("Disponible para envíos",
                                    size="1", color="#3A3A4E"),
                            spacing="2", align_items="start",
                        ),
                        padding="28px",
                        background=SURFACE,
                        border="1px solid rgba(255,107,0,0.2)",
                        border_radius="20px",
                        flex="1",
                        min_width="240px",
                        box_shadow="0 0 30px rgba(255,107,0,0.08)",
                    ),
                    rx.box(
                        rx.vstack(
                            rx.hstack(
                                rx.text("🪙", font_size="20px"),
                                rx.text("MandaloCoins", size="2",
                                        weight="medium", color="#A0A0B0"),
                                spacing="2", align="center",
                            ),
                            rx.text(
                                f"{WalletState.saldo_coins:.2f}",
                                weight="bold",
                                font_size="2.4rem",
                                style={"background": "linear-gradient(135deg, #BE6BD8, #9B59B6)",
                                       "-webkit-background-clip": "text",
                                       "-webkit-text-fill-color": "transparent"},
                                class_name="fade-in-up",
                            ),
                            rx.text("Ganados por calificaciones 4★+",
                                    size="1", color="#3A3A4E"),
                            spacing="2", align_items="start",
                        ),
                        padding="28px",
                        background=SURFACE,
                        border="1px solid rgba(190,107,216,0.2)",
                        border_radius="20px",
                        flex="1",
                        min_width="240px",
                        box_shadow="0 0 30px rgba(190,107,216,0.06)",
                    ),
                    spacing="4",
                    width="100%",
                    flex_wrap="wrap",
                ),

                # Historial de transacciones
                rx.box(
                    rx.vstack(
                        rx.hstack(
                            rx.hstack(
                                rx.icon(tag="list", size=18, color=ACCENT),
                                rx.text("Historial de Movimientos",
                                        weight="bold", size="4", color="white"),
                                spacing="2", align="center",
                            ),
                            rx.spacer(),
                            rx.button(
                                rx.hstack(
                                    rx.icon(tag="refresh-cw", size=14),
                                    rx.text("Actualizar", size="2"),
                                    spacing="1",
                                ),
                                on_click=WalletState.on_mount,
                                size="2", variant="ghost", color_scheme="gray",
                            ),
                            width="100%", align="center",
                        ),
                        rx.cond(
                            WalletState.is_loading,
                            rx.center(
                                rx.box(class_name="spinner"),
                                padding="48px",
                            ),
                            rx.cond(
                                WalletState.transacciones.length() > 0,
                                rx.table.root(
                                    rx.table.header(
                                        rx.table.row(
                                            *[rx.table.column_header_cell(
                                                rx.text(h, size="1", weight="medium",
                                                        color="#5A5A6E",
                                                        text_transform="uppercase",
                                                        letter_spacing="0.05em"),
                                            ) for h in ["Tipo", "Monto", "Estado", "Fecha"]],
                                        ),
                                    ),
                                    rx.table.body(
                                        rx.foreach(WalletState.transacciones, tx_row),
                                    ),
                                    width="100%",
                                ),
                                rx.center(
                                    rx.vstack(
                                        rx.text("💸", font_size="48px"),
                                        rx.text("Sin movimientos aún",
                                                color="#5A5A6E", size="3", weight="medium"),
                                        rx.text("Las transacciones aparecerán aquí",
                                                color="#3A3A4E", size="2"),
                                        spacing="2", align="center",
                                    ),
                                    padding="56px",
                                ),
                            ),
                        ),
                        width="100%", spacing="4",
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
            max_width="1000px",
            margin="0 auto",
            padding="2rem",
            on_mount=WalletState.on_mount,
        ),
        background="#0A0A0F",
        min_height="100vh",
    )
