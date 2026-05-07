# INSTRUCCIÓN DE SISTEMA: AGENTE DE DESARROLLO FULL-STACK (ANTIGRAVITY / PYTHON)

## ROL Y CONTEXTO CONTINUO
Sigues actuando como Desarrollador Full-Stack Senior y Arquitecto de Software para el proyecto "MANDALO".
Las Fases 1 (KYC) y 2 (WebSockets/Mapas) están completas. Ahora, bajo los estándares de escalabilidad de TECNIMAS, implementaremos el motor logístico principal: La Fase 3.

## TAREA ACTUAL: FASE 3 - ALGORITMO DE ASIGNACIÓN, RUTEO Y MULTIENTREGA
El objetivo es crear la "Máquina de Estados" de los pedidos y el algoritmo asíncrono que decide qué operador recibe qué paquete, basándose en ubicación, nivel KYC y prioridad zonal.

Ejecuta paso a paso las siguientes instrucciones:

### PASO 1: Esquema de Base de Datos para Pedidos (Supabase)
Crea el código SQL para generar la tabla `Pedidos`:
1. Campos básicos: `id`, `usuario_id`, `comercio_id` (opcional), `estado` (creado, buscando_operador, asignado, recogido, en_transito, entregado, cancelado).
2. Datos espaciales: `origen_coordenadas`, `destino_coordenadas` (tipo POINT de PostGIS).
3. Datos de logística: `operador_id` (FK, nulo hasta asignación), `precio_calculado`, `distancia_km`, `tipo_vehiculo_requerido`.
4. Relación: Crea una tabla `Zonas_Fidelidad_Operador` para registrar en qué polígonos/zonas un operador tiene prioridad (Score de Zona).

### PASO 2: Motor de Tarificación y Ruteo (Backend - FastAPI)
Desarrolla el endpoint para cotizar el envío:
1. `POST /api/pedidos/cotizar`: Recibe origen y destino.
2. Utiliza la distancia lineal (PostGIS) o integración simulada con API de Mapbox Matrix para calcular los kilómetros.
3. Devuelve el `precio_calculado` basado en una fórmula base (Ej: Tarifa Base + (Tarifa x Km) + Factor de Alta Demanda).

### PASO 3: Algoritmo Inteligente de Asignación (El Cerebro)
Crea una tarea asíncrona en Python (puedes sugerir el uso de Celery, Redis Queue o `BackgroundTasks` de FastAPI) llamada `motor_asignacion_pedidos`:
1. Cuando un pedido pasa a estado `buscando_operador`, el algoritmo debe buscar en la tabla `Ubicacion_Operadores` (PostGIS) a los repartidores en un radio de X km.
2. **Filtros de Negocio Estrictos:** 
   - El operador DEBE estar activo.
   - El nivel de KYC del operador debe ser suficiente para el tipo de pedido.
   - **Prioridad Zonal:** Si hay empate en distancia, asigna primero al operador que tenga mayor puntuación en esa "Zona de Calor" (`Zonas_Fidelidad_Operador`).
3. Implementa la lógica de **Multientrega**: Si un operador Nivel 3 (Élite) está en ruta, el algoritmo puede asignarle un segundo pedido del mismo comercio si el destino final no desvía su ruta principal más de un 15%.

### PASO 4: Endpoints de la Máquina de Estados
Crea las rutas en FastAPI para que el Frontend (Reflex) actualice el pedido:
- `POST /api/pedidos/{id}/aceptar` (Operador acepta el viaje).
- `POST /api/pedidos/{id}/recoger` (Operador escanea/confirma que tiene el paquete).
- `POST /api/pedidos/{id}/entregar` (Finalización del viaje).

### REGLAS DE CÓDIGO (TRANSACCIONES SEGURAS)
- **Bloqueo Concurrente (Race Conditions):** Es vital que prevengas que dos operadores acepten el mismo pedido al mismo tiempo. Utiliza transacciones seguras (bloqueos a nivel de fila en PostgreSQL o *locks* en Redis) al momento de asignar `operador_id`.
- **Atomicidad:** Si falla la actualización del estado del pedido a `asignado`, todo el proceso debe revertirse para no dejar el sistema en un estado inconsistente.

Genera el código modularizado: SQL para el esquema, lógica asíncrona de FastAPI/Python para la asignación y las rutas REST para la máquina de estados.