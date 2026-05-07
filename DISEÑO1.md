Plan: Rediseño Premium y Funcionalidad Completa — MANDALO PWA
Contexto
La app está en producción en Railway (mandalo-backend-production.up.railway.app) con Supabase como DB. Los 4 componentes Reflex actuales tienen estructura funcional básica pero carecen de:

Diseño premium (son grises/blancos sin identidad de marca)
Funcionalidad real (los estados son simulados con datos hardcodeados, no conectan al backend)
Páginas adicionales (falta dashboard de pedidos, wallet, perfil de usuario)
Sistema de Diseño MANDALO
Se aplicará un sistema de diseño unificado Dark Mode con acento naranja-ámbar:

Token	Valor
Fondo principal	#0A0A0F (negro profundo)
Superficie	#13131A (tarjetas)
Acento primario	#FF6B00 (naranja MANDALO)
Acento secundario	#FFB347 (ámbar cálido)
Texto primario	#FFFFFF
Texto secundario	#A0A0B0
Éxito	#00E676 (verde neón)
Error	#FF4757
Fuente	Inter (Google Fonts)
Propuesta de Cambios
Componente 1: Sistema de Diseño y Layout
[MODIFY] 
mandalo_app.py
Cambiar tema Reflex a appearance="dark" con accent_color="orange"
Agregar head_components con Google Fonts (Inter)
Registrar 2 nuevas páginas: /dashboard y /wallet
[NEW] 
components/navbar.py
Barra de navegación persistente con logo MANDALO
Links a: Dashboard, Mapa, KYC, Wallet
Indicador de nivel KYC del usuario activo
Botón de logout
Componente 2: LoginView — Rediseño Premium
[MODIFY] 
components/LoginView.py
Pantalla split: lado izquierdo con imagen/brandind MANDALO, lado derecho con el formulario
Logo animado con gradiente naranja
Input fields con bordes que brillan al focus (naranja)
Botón Ingresar con gradiente naranja → ámbar y efecto hover
Botón Google con ícono SVG real
Selector de rol: Usuario / Comercio / Operador (con íconos)
Funcionalidad real: 
on_login
 hace llamada HTTP real a POST /api/auth en el backend Railway usando rx.State con httpx
Componente 3: Dashboard de Pedidos (NUEVO)
[NEW] 
components/Dashboard.py
Pantalla principal post-login con:

Cards de métricas: Pedidos activos, Wallet balance, Nivel KYC, Rating promedio
Sección "Nuevo Envío": Formulario de cotizador (origen/destino → llama POST /api/pedidos/cotizar)
Historial de pedidos: Tabla con estado en tiempo real, badge de color por estado
Estado con funcionalidad real: Conectado a GET /api/pedidos del backend
Componente 4: KYC Dashboard — Rediseño + Funcionalidad Real
[MODIFY] 
components/KYC_Dashboard.py
Barra de progreso animada con 3 pasos visuales (estilo stepper)
Cada nivel tiene ícono, descripción de beneficios y estado (completado/pendiente/bloqueado)
Zona de drag-and-drop con preview del archivo seleccionado
Funcionalidad real: 
handle_upload
 sube el archivo a Supabase Storage vía el cliente de Supabase
Componente 5: Admin KYC — Rediseño + Funcionalidad Real
[MODIFY] 
components/AdminKYCView.py
Tabla premium con filas con hover efecto
Thumbnails del documento subido
Badges de color animados (verde pulsante si pendiente)
Funcionalidad real: on_mount hace GET real a Supabase para cargar documentos pendientes; Aprobar/Rechazar llaman a POST /api/kyc/review
Componente 6: Mapa Tracking — Rediseño + Fix WebSocket
[MODIFY] 
components/Mapa_Tracking.py
Panel lateral izquierdo: lista de operadores activos con distancia y estado
Mapa ocupa el resto de la pantalla (estilo fullscreen)
Marcadores con animación de pulso (CSS keyframes)
Fix WebSocket: Resolver la lectura de coordenadas PostGIS en formato EWKB → añadir lat y lng como columnas separadas en la tabla o usar RPC de conversión
Panel inferior con estadísticas en tiempo real (operadores activos, pedidos en curso)
Componente 7: Wallet (NUEVO)
[NEW] 
components/Wallet.py
Card grande con saldo real y saldo MandaloCoins (con ícono de moneda)
Historial de transacciones con tipo, monto y estado
Funcionalidad real: conectada a GET /api/finance/wallet (a crear en backend)
User Review Required
IMPORTANT

Decisiones que necesito que confirmes antes de ejecutar:

1. Páginas adicionales
¿Quieres que cree las páginas de Dashboard de Pedidos y Wallet además del rediseño de las 4 pantallas existentes? Esto suma 2 páginas nuevas.

2. Autenticación real
¿Los usuarios ya tienen cuentas en Supabase Auth? ¿O el login por ahora sigue siendo simulado (redirige directo al mapa)?

3. Mapbox Token
El mapa usa un token de Mapbox hardcodeado. ¿Tienes un token propio de Mapbox? Si no, puedo usar Leaflet.js (100% gratuito y open source) como alternativa.

4. Scope del trabajo
¿Prefieres que empiece por un componente específico (ej. solo el Login y el Dashboard) o quieres que ataque todos los componentes a la vez?

Verificación
Verificación Visual (Manual)
Con reflex run activo localmente, abrir http://localhost:3000/ y verificar:
Pantalla de login con diseño dark + naranja
Formulario funcional (campos, selector de rol, botones)
Navegar a http://localhost:3000/kyc → verificar stepper de 3 pasos visible
Navegar a http://localhost:3000/admin/kyc → verificar tabla con datos
Navegar a http://localhost:3000/map → verificar mapa Mapbox con fondo dark
Verificación Funcional (Test suite existente)
powershell
# Desde c:\Users\Jessi\Downloads\WEB_APP_2026\mandalo_app
venv\Scripts\activate; pytest tests/ -v
Los tests existentes en 
test_auth.py
, 
test_asignacion.py
 y 
test_wallet.py
 deben seguir pasando.

Verificación en Producción
Hacer commit y push a main → GitHub Actions ejecuta 
ci-tests.yml
 → si pasa, despliega automáticamente a Railway y Vercel.


Comment
Ctrl+Alt+M
