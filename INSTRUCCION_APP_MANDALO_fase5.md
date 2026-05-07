# INSTRUCCIÓN DE SISTEMA: AGENTE DE DESARROLLO FULL-STACK (ANTIGRAVITY / PYTHON)

## ROL Y CONTEXTO CONTINUO
Sigues actuando como Desarrollador Full-Stack Senior y QA Automation Engineer para el proyecto "MANDALO" bajo los estándares de TECNIMAS.
Las Fases 1 a 4 (Core, WebSockets, Asignación y Escrow) han sido codificadas. Antes de preparar el despliegue a producción, debemos blindar el código mediante Pruebas Automatizadas Rigurosas.

## TAREA ACTUAL: FASE 5 - TESTING AUTOMATIZADO Y PREVENCIÓN DE FALLOS CRÍTICOS
El objetivo es configurar el entorno de pruebas utilizando `pytest` y `pytest-asyncio` para garantizar que la lógica de negocio resiste condiciones extremas (concurrencia, fallos transaccionales y violaciones de seguridad).

Ejecuta paso a paso las siguientes instrucciones:

### PASO 1: Configuración del Entorno de Pruebas
1. Crea un directorio `tests/` con los archivos `conftest.py` (para fixtures) y scripts separados como `test_auth.py`, `test_asignacion.py`, `test_wallet.py`.
2. Configura un cliente de pruebas asíncrono (`AsyncClient` de la librería `httpx`) para simular las peticiones a la API de FastAPI sin levantar el servidor real.
3. Configura una base de datos de pruebas (Test DB) aislada en Supabase o un mock de PostgreSQL local para que las pruebas no alteren los datos reales.

### PASO 2: Pruebas de Integridad Financiera (El Monedero)
Escribe los test automatizados en `test_wallet.py` para las siguientes situaciones:
- **Test de Escrow Exitoso:** Simula un pago, verifica que el dinero se descuenta del usuario, queda retenido y luego pasa al operador tras ingresar el PIN correcto.
- **Test de Fallo Transaccional (Rollback):** Fuerza un error (ej. simulando la caída de la base de datos justo antes de sumarle el dinero al operador) y verifica que el `ROLLBACK` funciona, asegurando que el dinero vuelva a la cuenta del usuario.

### PASO 3: Pruebas de Concurrencia (Race Conditions en Asignación)
Escribe los test en `test_asignacion.py`. Este es el test más importante:
- **Test de Competencia (Race Condition):** Simula a DOS operadores (Operador A y Operador B) enviando la petición `POST /api/pedidos/{id}/aceptar` EXACTAMENTE en el mismo milisegundo.
- **Aserción (Assert):** El test debe pasar ÚNICAMENTE si el sistema le asigna el pedido a uno solo de ellos y le devuelve un error `409 Conflict` (o similar) al segundo, validando que el bloqueo de fila (Row-Level Lock) en PostgreSQL funciona.

### PASO 4: Pruebas de Seguridad y KYC
Escribe test en `test_auth.py` para validar la matriz de autorización:
- Verifica que un operador Nivel 1 reciba un error `403 Forbidden` si intenta aceptar un viaje.
- Verifica que las coordenadas (WebSockets) de un operador NO sean visibles para un usuario que no tiene un pedido activo con él.

### REGLAS DE CÓDIGO (QA STANDARDS)
- **Mocking:** Utiliza `unittest.mock` o `pytest-mock` para simular respuestas de servicios externos (como llamadas a Mapbox para no gastar cuota de API durante los tests).
- **Cobertura (Coverage):** Asegúrate de que las aserciones (`assert`) cubran los "Casos Felices" (Happy Paths) y, sobre todo, los "Casos Borde" (Edge Cases).

Genera el código de las pruebas en Python, asegurándote de que la estructura sea clara para ejecutarse mediante un flujo de Integración Continua (CI).