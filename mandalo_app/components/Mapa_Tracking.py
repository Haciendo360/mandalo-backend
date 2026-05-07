import reflex as rx
from mandalo_app.utils.supabase_client import get_supabase_client
from mandalo_app.components.navbar import navbar
import os

GRADIENT = "linear-gradient(135deg, #FF6B00 0%, #FFB347 100%)"
SURFACE  = "#13131A"
ACCENT   = "#FF6B00"

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")


class MapState(rx.State):
    operadores_activos: list[dict[str, str]] = []
    total_activos: int = 0

    async def on_mount(self):
        try:
            client = get_supabase_client()
            res = client.table("ubicacion_operadores").select(
                "operador_id, estado_conexion, ultima_actualizacion"
            ).eq("estado_conexion", "activo").execute()
            self.operadores_activos = res.data or []
            self.total_activos = len(self.operadores_activos)
        except Exception:
            self.total_activos = 0


def operador_item(op: dict) -> rx.Component:
    return rx.hstack(
        rx.box(
            width="10px", height="10px",
            border_radius="50%",
            background="#00E676",
            box_shadow="0 0 6px #00E676",
            flex_shrink="0",
        ),
        rx.vstack(
            rx.text(
                op["operador_id"][:12] + "...",
                size="1", weight="medium", color="white",
                font_family="monospace",
            ),
            rx.text("En línea", size="1", color="#00E676"),
            spacing="0", align_items="start",
        ),
        spacing="3", align="center",
        padding="10px 14px",
        border_radius="10px",
        background="rgba(255,255,255,0.03)",
        border="1px solid rgba(255,255,255,0.05)",
        width="100%",
        _hover={"background": "rgba(255,107,0,0.05)"},
        transition="all 0.15s",
    )


def mapa_tracking_view() -> rx.Component:
    return rx.box(
        navbar(),

        # Inyección de Leaflet CSS
        rx.html(
            '<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>'
        ),

        rx.hstack(
            # ========== PANEL LATERAL ==========
            rx.box(
                rx.vstack(
                    rx.hstack(
                        rx.icon(tag="radio", size=18, color=ACCENT),
                        rx.text("Radar en Vivo", weight="bold",
                                size="4", color="white"),
                        spacing="2", align="center",
                    ),
                    rx.box(
                        rx.hstack(
                            rx.box(
                                rx.text(
                                    MapState.total_activos,
                                    weight="bold", font_size="2rem", color="white",
                                ),
                                rx.text("operadores activos",
                                        size="2", color="#A0A0B0"),
                                spacing="1",
                            ),
                            rx.spacer(),
                            rx.box(
                                width="12px", height="12px",
                                border_radius="50%",
                                background="#00E676",
                                box_shadow="0 0 8px #00E676",
                                style={"animation": "glow-pulse 2s ease infinite"},
                            ),
                            align="center", width="100%",
                        ),
                        padding="16px",
                        background="rgba(0,230,118,0.05)",
                        border="1px solid rgba(0,230,118,0.15)",
                        border_radius="12px",
                    ),
                    rx.text("Operadores", size="2", weight="medium",
                            color="#A0A0B0"),
                    rx.cond(
                        MapState.operadores_activos.length() > 0,
                        rx.vstack(
                            rx.foreach(MapState.operadores_activos, operador_item),
                            width="100%", spacing="2",
                        ),
                        rx.center(
                            rx.vstack(
                                rx.icon(tag="users", size=28, color="#2A2A3E"),
                                rx.text("Sin operadores activos",
                                        color="#3A3A4E", size="2"),
                                spacing="2", align="center",
                            ),
                            padding="32px",
                        ),
                    ),
                    rx.spacer(),
                    rx.box(
                        rx.vstack(
                            rx.text("Estadísticas", size="2",
                                    weight="medium", color="#A0A0B0"),
                            rx.hstack(
                                rx.vstack(
                                    rx.text("0", weight="bold", color="white", size="3"),
                                    rx.text("En tránsito", size="1", color="#5A5A6E"),
                                    spacing="0", align="center",
                                ),
                                rx.vstack(
                                    rx.text("0", weight="bold", color="white", size="3"),
                                    rx.text("Pedidos activos", size="1", color="#5A5A6E"),
                                    spacing="0", align="center",
                                ),
                                justify="between", width="100%",
                            ),
                            spacing="3",
                        ),
                        padding="16px",
                        background=SURFACE,
                        border="1px solid rgba(255,255,255,0.06)",
                        border_radius="12px",
                    ),
                    height="100%",
                    spacing="4",
                    padding="20px",
                    width="280px",
                    flex_shrink="0",
                ),
                background="#0D0D14",
                border_right="1px solid rgba(255,255,255,0.06)",
                height="calc(100vh - 60px)",
                overflow_y="auto",
            ),

            # ========== MAPA ==========
            rx.box(
                rx.box(
                    id="mandalo-map",
                    width="100%",
                    height="100%",
                ),
                flex="1",
                height="calc(100vh - 60px)",
                position="relative",
            ),

            spacing="0",
            width="100%",
            align_items="stretch",
        ),

        # Scripts: Leaflet + inicialización del mapa dark + WebSocket Supabase
        rx.script(src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"),
        rx.script(src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2"),
        rx.script(f"""
(function initMap() {{
    // Esperar que el DOM esté listo
    if (!document.getElementById('mandalo-map')) {{
        setTimeout(initMap, 300);
        return;
    }}

    // Inicializar mapa Leaflet centrado en Caracas
    const map = L.map('mandalo-map', {{ zoomControl: false }}).setView([10.4806, -66.9036], 13);

    L.tileLayer('https://{{s}}.basemaps.cartocdn.com/dark_all/{{z}}/{{x}}/{{y}}{{r}}.png', {{
        attribution: '&copy; CARTO',
        subdomains: 'abcd',
        maxZoom: 20
    }}).addTo(map);

    L.control.zoom({{ position: 'bottomright' }}).addTo(map);

    // Icono custom naranja para operadores
    function makeIcon(color) {{
        return L.divIcon({{
            className: '',
            html: '<div class="operator-marker"></div>',
            iconSize: [20, 20],
            iconAnchor: [10, 10],
        }});
    }}

    const markers = {{}};

    function upsertMarker(opId, lat, lng) {{
        if (!markers[opId]) {{
            markers[opId] = L.marker([lat, lng], {{ icon: makeIcon('#FF6B00') }})
                .bindPopup('<b style="color:#FF6B00">Operador</b><br>' + opId.substring(0, 12) + '...')
                .addTo(map);
        }} else {{
            markers[opId].setLatLng([lat, lng]);
        }}
    }}

    // Conectar Supabase Realtime si las credenciales están disponibles
    const supabaseUrl = '{SUPABASE_URL}';
    const supabaseKey = '{SUPABASE_KEY}';

    if (supabaseUrl && supabaseKey) {{
        const supabaseClient = supabase.createClient(supabaseUrl, supabaseKey);

        supabaseClient.channel('map_realtime')
            .on('postgres_changes', {{
                event: '*',
                schema: 'public',
                table: 'ubicacion_operadores'
            }}, payload => {{
                const row = payload.new;
                if (row && row.lat && row.lng) {{
                    upsertMarker(row.operador_id, parseFloat(row.lat), parseFloat(row.lng));
                }}
            }})
            .subscribe();
    }}

    // Marcadores de demo para visualización
    const demoOps = [
        [10.4850, -66.9100],
        [10.4780, -66.8950],
        [10.4920, -66.9200],
    ];
    demoOps.forEach((c, i) => upsertMarker('demo-op-' + i, c[0], c[1]));
}})();
"""),

        background="#0A0A0F",
        min_height="100vh",
        on_mount=MapState.on_mount,
    )

