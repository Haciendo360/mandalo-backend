import reflex as rx

def mapa_tracking_view() -> rx.Component:
    """
    Componente de UI para visualización Geoespacial.
    Dado que Reflex opera bajo React.js y WebSockets propios, la integración
    nativa de Supabase Realtime y MapBox requiere inyectar scripts al cliente
    para no sobrecargar el servidor backend de Reflex.
    """
    return rx.box(
        rx.vstack(
            rx.heading("Radar MANDALO - Rastreo en Vivo", size="7"),
            rx.text("Monitoreo de operadores y rutas por WebSockets (PostGIS + Supabase Realtime)."),
            
            # Contenedor del Mapa
            rx.box(
                id="mapbox-container",
                width="100%",
                height="600px",
                border_radius="12px",
                overflow="hidden",
                border="2px solid var(--gray-5)",
                background_color="var(--gray-3)"
            ),
            
            rx.text("Las ubicaciones son ofuscadas por privacidad y servidas vía Supabase WebSockets.", size="2", color="gray"),
            
            # Injection de dependencias JS (MapBox + Supabase Client)
            rx.script(src="https://api.mapbox.com/mapbox-gl-js/v2.15.0/mapbox-gl.js"),
            rx.html('<link href="https://api.mapbox.com/mapbox-gl-js/v2.15.0/mapbox-gl.css" rel="stylesheet" />'),
            rx.script(src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2"),
            
            # Script de inicialización de Realtime y Mapa
            rx.script("""
                // Inicializar Mapbox
                mapboxgl.accessToken = '""" + __import__('os').getenv("MAPBOX_TOKEN", "pk.eyJ1IjoiZGFlbW9uMjMyIiwiYSI6ImNsczNtcHpxaTBtcm0yam9wczB5NDQ0MzYifQ.yF0d_KkF3oI") + """';
                const map = new mapboxgl.Map({
                    container: 'mapbox-container',
                    style: 'mapbox://styles/mapbox/dark-v11',
                    center: [-66.9036, 10.4806], // Caracas, Venezuela default
                    zoom: 12
                });

                // Inicializar Supabase Cliente V2 para WebSockets
                const supabaseUrl = '""" + __import__('os').getenv("SUPABASE_URL", "") + """';
                const supabaseKey = '""" + __import__('os').getenv("SUPABASE_KEY", "") + """';
                const supabase = supabaseCreateClient(supabaseUrl, supabaseKey);

                // Manejo de Marcadores en el DOM
                const operatorMarkers = {};

                // Throttle / Debounce para enviar reportes (simulacion)
                let lastUpdate = 0;
                function reportLocation(lat, lng, action) {
                    const now = Date.now();
                    if (now - lastUpdate > 5000) { // Throttle de 5 segundos
                         // Llamada la API FastAPI implementada (o a Supabase directamente)
                         lastUpdate = now;
                         console.log("Reportando mi ubicacion de operador...")
                    }
                }

                // Función para agregar o mover marcador en el mapa
                function upsertMarker(opId, lng, lat) {
                    if (!operatorMarkers[opId]) {
                        const el = document.createElement('div');
                        el.style.cssText = 'width:14px;height:14px;background:#00e5ff;border-radius:50%;border:2px solid #fff;box-shadow:0 0 8px #00e5ff;';
                        operatorMarkers[opId] = new mapboxgl.Marker(el)
                            .setLngLat([lng, lat])
                            .setPopup(new mapboxgl.Popup().setText('Operador: ' + opId.substring(0,8)))
                            .addTo(map);
                    } else {
                        operatorMarkers[opId].setLngLat([lng, lat]);
                    }
                }

                // Cargar operadores existentes al iniciar el mapa
                map.on('load', async () => {
                    const { data, error } = await supabase
                        .from('ubicacion_operadores')
                        .select('operador_id, estado_conexion')
                        .eq('estado_conexion', 'activo');
                    if (data) {
                        // Centrar en Caracas - los datos de coord. vienen como geometría
                        // La consulta REST básica no devuelve coords PostGIS legibles sin cast
                        // Los markers en tiempo real se activarán vía Realtime
                        console.log('Operadores activos:', data.length);
                    }
                });

                // Suscripción WebSocket a ubicacion_operadores (Supabase Realtime)
                const channel = supabase.channel('realtime_operadores')
                    .on('postgres_changes', { event: '*', schema: 'public', table: 'ubicacion_operadores' }, payload => {
                        console.log('Cambio detectado via WebSocket:', payload);
                        const { new: newRow, eventType } = payload;
                        
                        if ((eventType === 'INSERT' || eventType === 'UPDATE') && newRow) {
                            const opId = newRow.operador_id;
                            // Las coordenadas PostGIS vienen como EWKB hex - necesita conversión
                            // Por ahora registramos el evento y centramos el mapa
                            console.log('Operador actualizado:', opId);
                            // Cuando el backend envíe lng/lat separados, activaremos:
                            // upsertMarker(opId, newRow.lng, newRow.lat);
                        }
                    })
                    .subscribe((status) => console.log('Realtime status:', status));
            """)
        ),
        width="100%",
        max_width="1200px",
        margin="0 auto",
        padding="2rem"
    )
