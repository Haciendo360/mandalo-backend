import reflex as rx
from mandalo_app.utils.supabase_client import get_supabase_client
from mandalo_app.components.navbar import navbar

GRADIENT  = "linear-gradient(135deg, #FF6B00 0%, #FFB347 100%)"
SURFACE   = "#13131A"
ELEVATED  = "#1C1C27"
ACCENT    = "#FF6B00"


class DashboardState(rx.State):
    pedidos: list[dict] = []
    is_loading: bool = False
    origen: str = ""
    destino: str = ""
    cotizacion: dict = {}
    cotizando: bool = False
    error: str = ""

    def set_origen(self, v: str):  self.origen = v
    def set_destino(self, v: str): self.destino = v

    async def on_mount(self):
        """Carga el historial de pedidos del usuario al entrar al dashboard."""
        self.is_loading = True
        try:
            client = get_supabase_client()
            res = client.table("pedidos").select(
                "id, estado, precio_calculado, distancia_km, created_at"
            ).order("created_at", desc=True).limit(10).execute()
            self.pedidos = res.data or []
        except Exception as e:
            self.error = str(e)
        self.is_loading = False

    async def cotizar(self):
        if not self.origen or not self.destino:
            self.error = "Ingresa origen y destino para cotizar"
            return
        self.cotizando = True
        self.error = ""
        # Simulación de cotización (coordenadas ficticias de Caracas)
        try:
            client = get_supabase_client()
            res = client.rpc("distancia_entre_puntos", {
                "lat1": 10.4806, "lng1": -66.9036,
                "lat2": 10.4950, "lng2": -66.8800,
            }).execute()
            distancia = float(res.data) if res.data else 3.5
            precio = 2.0 + (distancia * 1.2 * 1.15)
            self.cotizacion = {
                "distancia_km": round(distancia, 2),
                "precio": round(precio, 2),
                "tiempo_estimado": f"{int(distancia * 4 + 5)} min",
            }
        except Exception:
            self.cotizacion = {
                "distancia_km": 3.5,
                "precio": 6.83,
                "tiempo_estimado": "19 min",
            }
        self.cotizando = False


def estado_badge(estado: str) -> rx.Component:
    colores = {
        "creado": ("badge-activo", "Creado"),
        "buscando_operador": ("badge-pendiente", "Buscando"),
        "asignado": ("badge-en-transito", "Asignado"),
        "recogido": ("badge-en-transito", "Recogido"),
        "en_transito": ("badge-en-transito", "En Tránsito"),
        "entregado": ("badge-entregado", "Entregado"),
        "cancelado": ("badge-cancelado", "Cancelado"),
    }
    return rx.box(
        rx.text(estado, size="1", weight="600"),
        class_name=f"badge-{estado.replace('_', '-')}",
        padding="4px 10px",
        border_radius="20px",
        font_size="11px",
    )


def metric_card(icon: str, title: str, value: str, subtitle: str,
                color: str = ACCENT) -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.box(
                    rx.icon(tag=icon, size=20, color=color),
                    padding="10px",
                    background=f"rgba(255,107,0,0.1)",
                    border_radius="10px",
                ),
                rx.spacer(),
                rx.icon(tag="trending-up", size=16, color="#00E676"),
                align="center",
            ),
            rx.box(height="8px"),
            rx.text(value, weight="800", font_size="1.8rem", color="white"),
            rx.text(title, weight="600", size="2", color="white"),
            rx.text(subtitle, size="1", color="#5A5A6E"),
            spacing="1",
            align_items="start",
        ),
        class_name="metric-card fade-in-up",
        flex="1",
        min_width="160px",
    )


def pedido_row(pedido: dict) -> rx.Component:
    return rx.table.row(
        rx.table.cell(
            rx.text(pedido["id"][:8] + "...", size="2",
                    color="#A0A0B0", font_family="monospace"),
        ),
        rx.table.cell(
            rx.text(f"${pedido['precio_calculado']}", size="2",
                    weight="600", color="white"),
        ),
        rx.table.cell(
            rx.text(f"{pedido['distancia_km']} km", size="2", color="#A0A0B0"),
        ),
        rx.table.cell(
            rx.box(
                rx.text(pedido["estado"], size="1", weight="600"),
                padding="3px 10px",
                border_radius="20px",
                background="rgba(255,107,0,0.1)",
                display="inline-block",
                color=ACCENT,
            ),
        ),
        class_name="table-row",
        style={"border-bottom": "1px solid rgba(255,255,255,0.04)"},
    )


def cotizador_card() -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.icon(tag="package", size=20, color=ACCENT),
                rx.text("Nuevo Envío", weight="700", size="4", color="white"),
                spacing="3", align="center",
            ),
            rx.box(height="4px"),
            rx.hstack(
                rx.vstack(
                    rx.text("Origen", size="2", weight="500", color="#A0A0B0"),
                    rx.el.input(
                        placeholder="Dirección de recogida...",
                        on_change=DashboardState.set_origen,
                        style={"width": "100%", "padding": "10px 14px",
                               "background": "rgba(255,255,255,0.05)",
                               "border": "1px solid rgba(255,255,255,0.1)",
                               "border-radius": "8px", "color": "white",
                               "font-size": "13px", "outline": "none"},
                    ),
                    flex="1", spacing="2",
                ),
                rx.vstack(
                    rx.text("Destino", size="2", weight="500", color="#A0A0B0"),
                    rx.el.input(
                        placeholder="Dirección de entrega...",
                        on_change=DashboardState.set_destino,
                        style={"width": "100%", "padding": "10px 14px",
                               "background": "rgba(255,255,255,0.05)",
                               "border": "1px solid rgba(255,255,255,0.1)",
                               "border-radius": "8px", "color": "white",
                               "font-size": "13px", "outline": "none"},
                    ),
                    flex="1", spacing="2",
                ),
                rx.el.button(
                    rx.cond(
                        DashboardState.cotizando,
                        rx.box(class_name="spinner"),
                        rx.text("Cotizar", weight="700", color="white"),
                    ),
                    on_click=DashboardState.cotizar,
                    class_name="glow-button",
                    style={"padding": "10px 24px", "white-space": "nowrap",
                           "margin-top": "22px"},
                ),
                spacing="4", width="100%", align="end",
                flex_wrap="wrap",
            ),
            rx.cond(
                DashboardState.cotizacion != {},
                rx.hstack(
                    rx.hstack(
                        rx.icon(tag="map-pin", size=16, color=ACCENT),
                        rx.text(f"{DashboardState.cotizacion['distancia_km']} km",
                                weight="600", color="white", size="3"),
                        spacing="1",
                    ),
                    rx.hstack(
                        rx.icon(tag="clock", size=16, color="#A0A0B0"),
                        rx.text(DashboardState.cotizacion["tiempo_estimado"],
                                color="#A0A0B0", size="3"),
                        spacing="1",
                    ),
                    rx.spacer(),
                    rx.text("Precio estimado:", color="#A0A0B0", size="3"),
                    rx.text(
                        f"${DashboardState.cotizacion['precio']}",
                        weight="800", font_size="1.4rem",
                        style={"background": GRADIENT,
                               "-webkit-background-clip": "text",
                               "-webkit-text-fill-color": "transparent"},
                    ),
                    spacing="4",
                    padding="16px",
                    background="rgba(255,107,0,0.07)",
                    border="1px solid rgba(255,107,0,0.2)",
                    border_radius="10px",
                    width="100%",
                    align="center",
                    flex_wrap="wrap",
                    class_name="fade-in",
                ),
            ),
            width="100%", spacing="4",
        ),
        padding="24px",
        background=SURFACE,
        border="1px solid rgba(255,255,255,0.06)",
        border_radius="16px",
        width="100%",
    )


def dashboard_view() -> rx.Component:
    return rx.box(
        rx.script(""),
        navbar(),
        rx.box(
            rx.vstack(
                # Saludo
                rx.vstack(
                    rx.text("¡Bienvenido de vuelta! 👋",
                            weight="800", font_size="1.6rem", color="white",
                            class_name="fade-in-up"),
                    rx.text("Aquí está el resumen de tus operaciones de hoy.",
                            color="#A0A0B0", size="3"),
                    spacing="1", align_items="start", width="100%",
                ),

                # Métricas
                rx.flex(
                    metric_card("package",   "Pedidos Activos",  "3",      "2 en tránsito"),
                    metric_card("wallet",    "Saldo Wallet",     "$128.50","MandaloCoins: 42"),
                    metric_card("shield-check", "Nivel KYC",     "Nivel 2","Docs verificados"),
                    metric_card("star",      "Calificación",     "4.8 ★",  "Últimos 30 días"),
                    gap="16px",
                    width="100%",
                    flex_wrap="wrap",
                ),

                # Cotizador
                cotizador_card(),

                # Historial de pedidos
                rx.box(
                    rx.vstack(
                        rx.hstack(
                            rx.hstack(
                                rx.icon(tag="history", size=18, color=ACCENT),
                                rx.text("Historial de Pedidos", weight="700",
                                        size="4", color="white"),
                                spacing="2", align="center",
                            ),
                            rx.spacer(),
                            rx.button(
                                rx.hstack(
                                    rx.icon(tag="refresh-cw", size=14),
                                    rx.text("Actualizar", size="2"),
                                    spacing="1",
                                ),
                                on_click=DashboardState.on_mount,
                                size="2", variant="ghost", color_scheme="gray",
                            ),
                            width="100%", align="center",
                        ),
                        rx.cond(
                            DashboardState.is_loading,
                            rx.center(
                                rx.box(class_name="spinner"),
                                padding="40px",
                            ),
                            rx.cond(
                                DashboardState.pedidos.length() > 0,
                                rx.table.root(
                                    rx.table.header(
                                        rx.table.row(
                                            *[rx.table.column_header_cell(
                                                rx.text(h, size="1", weight="600",
                                                        color="#5A5A6E",
                                                        text_transform="uppercase",
                                                        letter_spacing="0.05em"),
                                            ) for h in ["ID", "Precio", "Distancia", "Estado"]],
                                        ),
                                    ),
                                    rx.table.body(
                                        rx.foreach(DashboardState.pedidos, pedido_row)
                                    ),
                                    width="100%",
                                    style={"border-collapse": "collapse"},
                                ),
                                rx.center(
                                    rx.vstack(
                                        rx.icon(tag="inbox", size=40,
                                                color="#3A3A4E"),
                                        rx.text("No hay pedidos aún",
                                                color="#5A5A6E", size="3"),
                                        rx.text("¡Crea tu primer envío arriba!",
                                                color="#3A3A4E", size="2"),
                                        spacing="2", align="center",
                                    ),
                                    padding="48px",
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
                ),

                width="100%",
                spacing="6",
                padding_bottom="48px",
            ),
            max_width="1200px",
            margin="0 auto",
            padding="2rem",
            on_mount=DashboardState.on_mount,
        ),
        background="#0A0A0F",
        min_height="100vh",
    )
