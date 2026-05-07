# INSTRUCCIÓN DE SISTEMA: REVISIÓN DE ARQUITECTURA Y DIAGRAMA DE FLUJO

## ROL
Actúa como Arquitecto de Software Principal de la plataforma MANDALO.

## TAREA
Antes de avanzar a la Fase 3, necesito validar la lógica de las fases anteriores (Fase 1: KYC y Fase 2: Tracking en Tiempo Real). 
Genera diagramas de flujo visuales utilizando la sintaxis de **Mermaid.js** para mapear exactamente cómo interactúan los componentes bajo los estándares de TECNIMAS. 

Debes generar 3 diagramas distintos con su respectiva explicación técnica breve:

### 1. Flujo de Arquitectura General (System Architecture)
Muestra cómo interactúa el cliente (PWA Reflex) con el Backend (FastAPI) y la Base de Datos (Supabase + PostGIS). Debe reflejar el uso de llamadas REST para operaciones estándar y WebSockets para el tiempo real.

### 2. Flujo de Verificación Progresiva (KYC User Journey)
Mapea el recorrido de un Operador desde que descarga la app (Nivel 1) hasta que es autorizado para multientregas (Nivel 3). Incluye los pasos de validación OTP, subida de documentos (cédula/vehículo) y aprobación del administrador.

### 3. Flujo de Datos en Tiempo Real (Real-Time Tracking)
Crea un diagrama de secuencia (Sequence Diagram) que ilustre el viaje de la coordenada GPS:
- El móvil del operador capta la coordenada.
- Se envía mediante FastAPI con debounce (throttle).
- Supabase actualiza PostGIS.
- Supabase Realtime emite el evento vía WebSocket.
- El Frontend (Reflex) del usuario actualiza el pin en el mapa (Mapbox/Google Maps).

## REGLAS DE FORMATO
- Escribe el código de los diagramas dentro de bloques de código específicos de `mermaid` para que puedan ser renderizados visualmente.
- Asegúrate de que la lógica sea coherente con un entorno asíncrono y de alta escalabilidad.
- Detecta y menciona si existe algún posible "cuello de botella" en el flujo actual antes de pasar a la Fase 3.