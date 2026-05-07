import asyncio
from mandalo_app.utils.supabase_client import get_supabase_client

async def calcular_desvio_ruta(supabase, op_id: str, origin_lat: float, origin_lng: float) -> bool:
    """
    Simula la complejidad del cálculo geoespacial de una desviación en Puntos de Parada.
    Llamaría a Mapbox u otra API para comparar la Ruta Original en minutos vs Nueva Ruta.
    Retorna True si la desviación es menor al 15% que pide el negocio.
    """
    await asyncio.sleep(0.1) # Simulamos el API request
    # Falsa aprobación para Nivel 3 elite
    return True 

async def motor_asignacion_pedidos(pedido_id: str, origin_lat: float, origin_lng: float):
    """
    Algoritmo the 'Cerebro' que funciona como un worker en BackgroundTasks de FastAPI.
    Busca, filtra, aplica multientrega y notifica.
    """
    await asyncio.sleep(1) # Delay opcional permitiendo estabilización del DB
    supabase = get_supabase_client()
    radio_busqueda_km = 8.0 # Ampliado a 8km
    
    try:
        candidatos_rpc = supabase.rpc("obtener_operadores_candidatos", {
            "p_lat": origin_lat,
            "p_lng": origin_lng,
            "p_radio_km": radio_busqueda_km
        }).execute()
        
        if not candidatos_rpc.data:
            print(f"[MOTOR-ALGORITMO] No se encontraron operadores cerca de {pedido_id}")
            return
            
        candidatos = candidatos_rpc.data
        operador_elegido = None
        
        for op in candidatos:
            # Multi-Entrega (Viajes Dobles/Apilados)
            if op['estado_conexion'] == 'en_ruta':
                if op['nivel_verificacion'] >= 3:
                    factible = await calcular_desvio_ruta(supabase, op['operador_id'], origin_lat, origin_lng)
                    if factible:
                        print(f"[{pedido_id}] Match Multientrega con Elite Ops: {op['operador_id']}")
                        operador_elegido = op['operador_id']
                        break
            # Operador Estandar Buscando Trabajo
            else:
                print(f"[{pedido_id}] Match Estandar con Operador: {op['operador_id']} (ZonaScore: {op['score_zona']})")
                operador_elegido = op['operador_id']
                break
                
        if operador_elegido:
            # Push WebSocket al Operador sobre el viaje pre-asignado
            supabase.table("notificaciones_push").insert({
                "operador_id": operador_elegido,
                "pedido_id": pedido_id,
                "mensaje": "¡Nuevo paquete cerca en tu Zona Prioritaria!"
            }).execute()
        else:
            print(f"[MOTOR] Candidatos descartados por desviación agresiva. Queda sin asignar.")
    except Exception as e:
        print(f"[ALGORITMO-ERROR] {str(e)}")
