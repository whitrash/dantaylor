# Lanzadores, tableros personales y puentes Windows–Android: dónde encaja WINT

## Resumen

- Alcance y método: todo se investigó el 7 de octubre de 2026 usando solo GitHub (github.com y raw.githubusercontent.com). El presupuesto de WebSearch estaba agotado y el proxy bloqueó learn.microsoft.com, raycast.com, home-assistant.io, tailscale.com, syncthing.net, kdeconnect.kde.org, play.google.com, f-droid.org y otros. Las fechas de versión salieron de los feeds Atom de GitHub (marcas de tiempo ISO), no de resúmenes de páginas.
- WINT no necesita ser una app propia en la PC: Flow Launcher (plugins en Python por JSON-RPC) y la Command Palette de PowerToys (extensiones en C#/WinRT) aceptan una extensión que consulte una API local de WINT. Raycast ya tiene versión para Windows (2.0.0, 25 de agosto de 2026) pero no pude verificar precio ni estado.
- La Command Palette es la dirección de Microsoft (sucesora de PowerToys Run); el roadmap v0.102 promete extensiones en JavaScript/TypeScript, aún sin confirmar como lanzado. Hoy solo se escriben en C#.
- Para el tablero, Glance es el mejor candidato para Windows: un binario único (menos de 20 MB), YAML y un widget custom-api que lee JSON con plantillas Go. Homepage hace algo parecido con Docker. Homarr acaba de pasar a v2.0.0 (2 de octubre de 2026), así que conviene esperar. CasaOS (último estable diciembre de 2024) y Keypirinha (último release noviembre de 2020) están estancados.
- Home Assistant, Umbrel, CasaOS y YunoHost son sistemas de servidor doméstico; para un usuario solo-Windows son excesivos, salvo que ya tenga un equipo siempre encendido.
- En Android, ser launcher implica declarar la categoría HOME y seguir cada versión del sistema; los datos muestran roturas por versión (widgets en Android 17 QPR2, crash en Android 16 QPR1). Se recomienda NO construir un launcher.
- Alternativa para Android sin launcher propio: Smartspacer (At a Glance con plugins), widgets de HTTP Shortcuts para disparar Sol/Luna, y el panel web vía Tailscale.
- Puentes: ntfy (avisos con curl, apps en Google Play y F-Droid), Tailscale (acceso remoto), Syncthing-Fork (la app Android oficial de Syncthing fue discontinuada en diciembre de 2024) y KDE Connect (misma red Wi-Fi, ejecuta comandos desde el teléfono). El estado 2026 de Enlace a Windows (Phone Link), Pushbullet, Join, Nova, Niagara y Smart Launcher NO pudo verificarse.
- "Google comprimido" se define aquí (opinión) como búsqueda unificada sobre fuentes propias (catálogos, precios, notas) más acciones. El motor recomendado es SQLite FTS5 (no verificado en fuente oficial); Meilisearch como opción; SearXNG solo cubre la web, no los datos propios.
- Tendencia a vigilar: Raycast 2.5.0, Wox, Umbrel 2.0 y Homarr 2.0 incorporan IA, MCP o agentes. WINT, determinista por diseño, puede usar estas herramientas ignorando esas funciones.
- Decisión central (detalle en Recomendaciones): construir solo el núcleo (API local, reglas, motor de búsqueda); reutilizar lanzador, tablero, notificaciones y puente móvil.

## Hallazgos

### H1 — Command Palette de PowerToys: sucesora de PowerToys Run
- Afirmación: PowerToys Command Palette (CmdPal) se activa con Win+Alt+Space y debe estar habilitada y corriendo en segundo plano desde la configuración de PowerToys. La documentación oficial (ms.date 10/04/2026, formato mm/dd) la describe como lanzador de aplicaciones, comandos, archivos, web, WinGet, Window Walker, portapapeles, servicios, perfiles de Terminal y más (16 capacidades listadas). La página de PowerToys Run (ms.date 20/08/2025) dice: "PowerToys Run is getting an upgrade to v2! Check out the Command Palette, PowerToys Run's evolution". PowerToys Run se abre con Alt+Space y tiene unos 15 plugins. Conflicto entre fuentes: el README del módulo (src/modules/cmdpal) aún dice que CmdPal "is currently in preview" y que puede haber cambios incompatibles antes de la 1.0.0, mientras la documentación de Microsoft que leí no repite esa advertencia. No pude confirmar si ya salió de preview.
- Fuentes: https://raw.githubusercontent.com/MicrosoftDocs/windows-dev-docs/docs/hub/powertoys/command-palette/overview.md, https://raw.githubusercontent.com/MicrosoftDocs/windows-dev-docs/docs/hub/powertoys/run.md, https://raw.githubusercontent.com/microsoft/PowerToys/main/src/modules/cmdpal/README.md
- Confianza: media
- Riesgo: alto
- Vigencia: docs ms.date 10/04/2026 (overview) y 20/08/2025 (run); consultado 7 de octubre de 2026

### H2 — Cómo se escribe una extensión de Command Palette
- Afirmación: las extensiones son aplicaciones .NET independientes (fuera de proceso, servidor COM) que hablan con CmdPal por una API WinRT. Se empaquetan como app de Windows (MSIX) y se declaran en el .appxmanifest con una extensión de aplicación `windows.appExtension` de nombre `com.microsoft.commandpalette`. Se usan dos paquetes NuGet: `Microsoft.CommandPalette.Extensions` (API WinRT, agnóstica de lenguaje según el README del módulo) y `Microsoft.CommandPalette.Extensions.Toolkit` (clases base en C#). Interfaces: `IExtension` (método `GetProvider`) y `ICommandProvider`; tipos de página: lista, detalle, formulario, markdown y cuadrícula. Código mínimo documentado: `ListPage.GetItems()` devuelve `IListItem[]`; `InvokableCommand.Invoke()` devuelve `CommandResult.KeepOpen()` o `CommandResult.CloseAfterInvoke()`; hay comandos incluidos `OpenUrlCommand` y `CopyTextCommand`. Requisitos de desarrollo (guía de creación): Visual Studio con las cargas "WinUI y Windows App SDK", Windows 11 con PowerToys instalado, modo desarrollador activado y fundamentos de C#. Flujo: ejecutar el comando "Create extension" dentro de la paleta (pide ExtensionName como nombre de clase C# válido, nombre para mostrar y ruta), compilar con "Deploy [ExtensionName]" en Visual Studio y ejecutar "Reload" en la paleta. La documentación solo muestra C# en los ejemplos.
- Fuentes: https://raw.githubusercontent.com/MicrosoftDocs/windows-dev-docs/docs/hub/powertoys/command-palette/extensibility-overview.md, https://raw.githubusercontent.com/MicrosoftDocs/windows-dev-docs/docs/hub/powertoys/command-palette/creating-an-extension.md, https://raw.githubusercontent.com/MicrosoftDocs/windows-dev-docs/docs/hub/powertoys/command-palette/adding-commands.md, https://raw.githubusercontent.com/MicrosoftDocs/windows-dev-docs/docs/hub/powertoys/command-palette/samples.md, https://raw.githubusercontent.com/MicrosoftDocs/windows-dev-docs/docs/hub/powertoys/command-palette/extension-development.md
- Confianza: alta
- Riesgo: alto
- Vigencia: ms.date 10/04/2026 (extensibility-overview y extension-development), 28/10/2025 (creating-an-extension, según el encabezado leído), 23/03/2025 (adding-commands), 7/2/2025 (samples); consultado 7 de octubre de 2026

### H3 — Distribución de extensiones de CmdPal: Microsoft Store, WinGet y galería
- Afirmación: la guía de publicación (ms.date 06/04/2026) ofrece dos vías con actualización automática. Microsoft Store es la "recomendada" (requiere cuenta de Partner Center y paquete MSIX; la guía dice que el registro no tiene costo para desarrolladores individuales). WinGet requiere un manifiesto con la etiqueta `windows-commandpalette-extension`, con lo que la extensión aparece con el comando "Search WinGet". La Extension Gallery es un directorio curado dentro de la paleta que no aloja extensiones: remite a WinGet o Store. Para entrar en la galería hay que publicar primero en Store o WinGet y luego abrir un pull request al repositorio microsoft/CmdPal-Extensions con un `extension.json` y un ícono (licencia MIT). Para uso estrictamente personal (WINT para una sola persona) basta con compilar y desplegar localmente, sin publicar.
- Fuentes: https://raw.githubusercontent.com/MicrosoftDocs/windows-dev-docs/docs/hub/powertoys/command-palette/publish-extension.md, https://raw.githubusercontent.com/MicrosoftDocs/windows-dev-docs/docs/hub/powertoys/command-palette/extension-gallery.md, https://github.com/microsoft/CmdPal-Extensions
- Confianza: alta
- Riesgo: alto
- Vigencia: ms.date 06/04/2026; consultado 7 de octubre de 2026

### H4 — CmdPal: versiones recientes, Dock y roadmap de JavaScript/TypeScript
- Afirmación: el feed de releases de PowerToys muestra previews v0.101.2781.0 (2026-10-07T03:07Z), v0.101.2712.0 (2026-09-30), v0.101.2684.0 (2026-09-26), v0.101.2652.0 (2026-09-23), v0.101.2632.0 (2026-09-21) y v0.101.2601.0 (2026-09-18). La publicación v0.101.2362.0 (25 de agosto; el año 2026 se infiere del feed) aparece como release estándar, no marcada "Latest" por problemas de despliegue de la actualización. Contenido relevante: modo compacto de CmdPal, Dock (barra persistente con auto-ocultar), toasts de extensiones con posición, íconos y botones de acción, "Quick Access Shelf" y búsqueda difusa (preview 0.101.2781.0). El README de PowerToys dice del roadmap v0.102: "expanding Command Palette with tabs and JavaScript/TypeScript extensions". Es un plan ("we're working on"), no una función confirmada como lanzada. No verifiqué si los toasts de extensión funcionan con la paleta cerrada.
- Fuentes: https://github.com/microsoft/PowerToys/releases.atom, https://github.com/microsoft/PowerToys/releases/tag/v0.101.2362.0, https://github.com/microsoft/PowerToys/releases/tag/v0.101.2781.0, https://raw.githubusercontent.com/microsoft/PowerToys/main/README.md, https://raw.githubusercontent.com/MicrosoftDocs/windows-dev-docs/docs/hub/powertoys/command-palette/dock.md
- Confianza: media
- Riesgo: alto
- Vigencia: feed consultado 7 de octubre de 2026 (última entrada 2026-10-07); dock.md ms.date 09/03/2026

### H5 — Flow Launcher: estado, lenguajes de plugin e integración con Everything
- Afirmación: Flow Launcher es un lanzador y buscador de archivos para Windows 10 en adelante, con licencia MIT y .NET 9; su README lo instala por winget, Scoop o Chocolatey. Último release: v2.1.4 (2026-09-20T23:07Z); antes v2.1.3 (2026-06-08), v2.1.2 (2026-05-10) y v2.1.1 (2026-03-09), es decir, un ritmo de un release cada uno a tres meses. Los plugins se escriben en C#, F#, Python, JavaScript o TypeScript, y hay una tienda de plugins integrada (instalables con el comando `pm install`). Busca archivos con Everything o con Windows Search (el plugin Explorer incluye la carpeta EverythingSDK). El README cita entre los plugins notables uno llamado "Home Assistant Commander", lo que muestra que enlazar un lanzador con un tablero doméstico ya es práctica común.
- Fuentes: https://github.com/Flow-Launcher/Flow.Launcher, https://raw.githubusercontent.com/Flow-Launcher/Flow.Launcher/dev/README.md, https://github.com/Flow-Launcher/Flow.Launcher/releases.atom, https://github.com/Flow-Launcher/Flow.Launcher/tree/dev/Plugins/Flow.Launcher.Plugin.Explorer
- Confianza: alta
- Riesgo: alto
- Vigencia: feed consultado 7 de octubre de 2026 (v2.1.4 del 2026-09-20)

### H6 — Anatomía de un plugin de Flow Launcher (JSON-RPC, Python)
- Afirmación: un plugin lleva un `plugin.json` en la raíz con los campos ID (UUID), ActionKeyword (el asterisco significa sin palabra clave), Name, Description, Author, Version (semántica), Language, Website, IcoPath y ExecuteFileName. Language admite seis valores: `csharp`, `fsharp`, `python`, `javascript`, `typescript`, `executable`. Flow está hecho en C# y los plugins .NET se integran de forma nativa; los demás lenguajes hablan con Flow por JSON-RPC local (llamada de procedimiento local). En Python se hereda de `FlowLauncher` y se implementa `query(self, query)`, que devuelve una lista de diccionarios con `title`, `subTitle`, `icoPath` y `jsonRPCAction` (método y parámetros a ejecutar al elegir el resultado); `context_menu(self, data)` se abre con Shift+Enter. La API de Flow expuesta a plugins incluye `ChangeQuery`, `ShowMsg`, `ShellRun`, `RestartApp`, `OpenSettingDialog` y otras (más de 15). El modelo es petición/respuesta: encaja con un bot determinista (no hay conversación).
- Fuentes: https://raw.githubusercontent.com/Flow-Launcher/docs/main/plugin.json.md, https://raw.githubusercontent.com/Flow-Launcher/docs/main/plugin-dev.md, https://raw.githubusercontent.com/Flow-Launcher/docs/main/json-rpc.md, https://raw.githubusercontent.com/Flow-Launcher/docs/main/py-write-code.md, https://github.com/Flow-Launcher/Flow.Launcher.Plugin.HelloWorldPython
- Confianza: alta
- Riesgo: bajo
- Vigencia: documentación en la rama main del repositorio de docs (sin fecha visible); consultado 7 de octubre de 2026

### H7 — Wox (activo) y Keypirinha (sin releases desde 2020)
- Afirmación: Wox es un lanzador multiplataforma (Windows, macOS, Linux) con licencia GPL-3.0, render nativo con GPU, unos 150 MB de memoria en uso típico, y plugins en Node.js, Python o scripts (SDK `wox-plugin` en npm y `wox_plugin` en pip; tienda de plugins propia). Releases del feed: v2.4.6 (2026-10-06), v2.4.5 (2026-09-23), v2.4.4 (2026-09-16), v2.4.3 (2026-09-09), es decir, cadencia semanal. Incluye búsqueda de archivos con indexado rápido opcional por servicio NTFS en Windows (v2.4.2) y "AI Chat" con configuración de servidor MCP. Keypirinha ("A fast keystroke launcher for Windows") tiene como último release v2.26 con fecha 2020-11-08, antes v2.25 (2020-05-25) y v2.24 (2019-08-18); el repositorio no está archivado, pero lleva casi seis años sin release. Evaluación (opinión): descartar Keypirinha como base.
- Fuentes: https://github.com/Wox-launcher/Wox, https://raw.githubusercontent.com/Wox-launcher/Wox/master/README.md, https://github.com/Wox-launcher/Wox/tree/master, https://github.com/Wox-launcher/Wox/releases.atom, https://github.com/Keypirinha/Keypirinha, https://github.com/Keypirinha/Keypirinha/releases.atom
- Confianza: alta (fechas por feed Atom); media en la descripción de funciones de Wox
- Riesgo: alto
- Vigencia: feeds consultados 7 de octubre de 2026

### H8 — Raycast llega a Windows (API de extensiones en TypeScript)
- Afirmación: el changelog oficial de la API de extensiones de Raycast dice: 1.103.0 (2025-09-15), primera apertura a Windows con un campo `platforms` en el manifiesto (por defecto `["macOS"]`; para Windows se pone `["macOS","Windows"]`), atajos por plataforma, `@raycast/utils` multiplataforma con `runPowerShellScript` y soporte para llamar funciones en Rust (se compilan a ejecutable de Windows con el atributo `#[raycast]`); 1.103.3 (2025-10-07), la publicación y contribución de extensiones funciona en Windows; 2.0.0 (2026-08-25): "Raycast 2.0 brings the extension API to the new Raycast desktop app on macOS and Windows" (CLI requiere Node.js 22.22.2 o superior); 2.5.0 (2026-09-24) permite que las extensiones aporten modelos de IA, declaren servidores MCP (`ai.mcp`) y empaqueten Agent Skills (`ai.skills`). Las extensiones son React y TypeScript (repo raycast/extensions, licencia MIT). No pude abrir raycast.com: precio, plan gratuito, y si Windows es beta o disponibilidad general quedan SIN VERIFICAR.
- Fuentes: https://raw.githubusercontent.com/raycast/extensions/main/docs/changelog.md, https://raw.githubusercontent.com/raycast/extensions/main/docs/information/manifest.md, https://github.com/raycast/extensions
- Confianza: alta en fechas y API; baja en el estado comercial de Windows
- Riesgo: alto
- Vigencia: changelog con entrada más reciente 2026-09-24; consultado 7 de octubre de 2026

### H9 — Everything (con ES) y Windows Search como buscadores locales de archivos
- Afirmación: ES es la interfaz de línea de comandos de Everything (MIT): requiere que el cliente Everything esté corriendo y le consulta por IPC; opciones `-n <num>`, `-csv`, `-json`, `-tsv`, `-txt`, `-export-csv`, `-export-json`, `-r` (regex), `-path`. voidtools publica además `everything_sdk3` (envoltorio C del IPC por canales con nombre), `http_server` y `etp_server`. Flow Launcher ya integra Everything. Windows Search (documentación oficial, última actualización 31/05/2018) es la plataforma de indexado de Windows: se consulta con proveedor OLE DB/SQL o `ISearchFolderItemFactory`; para indexar tipos propios hay que escribir protocol handlers y property handlers en código nativo (COM). Opinión: para WINT, estas herramientas sirven como fuente de archivos locales, no como lugar donde publicar catálogos o precios. Microsoft Search (búsqueda de Microsoft 365) y la versión, licencia y precio del propio Everything NO pudieron verificarse (sitios bloqueados).
- Fuentes: https://github.com/voidtools/ES, https://github.com/voidtools, https://raw.githubusercontent.com/MicrosoftDocs/win32/docs/desktop-src/search/-search-3x-wds-overview.md, https://github.com/MicrosoftDocs/win32/tree/docs/desktop-src/search
- Confianza: media
- Riesgo: alto
- Vigencia: ES sin fecha de release visible; documentación de Windows Search del 31/05/2018; consultado 7 de octubre de 2026

### H10 — Homepage (gethomepage): tablero por YAML con widget de API propia
- Afirmación: Homepage (GPL-3.0, unas 33 mil estrellas) se configura con archivos YAML o por etiquetas de Docker; tiene más de 100 integraciones y sus llamadas a servicios pasan por un proxy interno que oculta las claves. Instalación: Docker, Kubernetes (Helm), Unraid o desde el código fuente; la documentación leída no trata Windows. Desde v1.0 exige la variable `HOMEPAGE_ALLOWED_HOSTS` (lista separada por comas, sin espacios; `localhost:3000` y `127.0.0.1:3000` siempre permitidos); desde v2.0 trae autenticación por contraseña u OIDC (`HOMEPAGE_AUTH_ENABLED`, `HOMEPAGE_AUTH_SECRET`, `HOMEPAGE_EXTERNAL_URL`), aunque la documentación insiste en que los despliegues públicos deben estar detrás de proxy inverso o VPN. Widget Custom API: `url`, `mappings` con rutas por puntos (`origin.name`), `refreshInterval` en milisegundos (10 s por defecto), formatos text, number, float, percent, duration, bytes, bitrate, size, date y relativeDate, y tres modos de despliegue (block, list, dynamic-list). Releases: v2.4.0 (2026-09-17), v2.3.0 (2026-09-09), v2.2.0 (2026-09-02), o sea cadencia semanal.
- Fuentes: https://github.com/gethomepage/homepage, https://raw.githubusercontent.com/gethomepage/homepage/main/docs/installation/index.md, https://raw.githubusercontent.com/gethomepage/homepage/main/docs/widgets/services/customapi.md, https://github.com/gethomepage/homepage/releases.atom
- Confianza: alta
- Riesgo: alto
- Vigencia: feed consultado 7 de octubre de 2026 (v2.4.0 del 2026-09-17)

### H11 — Glance: binario único para Windows y widget custom-api con plantillas
- Afirmación: Glance (AGPL-3.0, unas 37,4 mil estrellas) es un tablero con configuración YAML. Se instala con Docker Compose o con binarios precompilados para Linux, Windows y macOS (el README declara "single <20mb binary"; carga de página de aproximadamente 1 s). Widgets: RSS, videos, Hacker News, Reddit, mercados, clima, calendario, Docker, estadísticas del servidor, monitor, marcadores, tareas, grupos y más. El widget `custom-api` muestra JSON propio: propiedades `url`, `template` (plantilla Go con `html/template`), `headers`, `cache`, `method`, `body`, `parameters`, `subrequests` (peticiones concurrentes), `options`; el JSON se recorre con gjson (`{{ .JSON.String "campo" }}`, `{{ range .JSON.Array "items" }}`). También hay widget `extension` (carga HTML de un endpoint propio, con la bandera `allow-potentially-dangerous-html` como riesgo declarado) y widget `html`. Releases: v0.8.6 (2026-09-03), v0.8.5 (2026-05-30), v0.8.4 (2025-06-10); sigue en 0.x y con cadencia lenta. La v0.8.6 agregó autenticación básica y opción de conexión insegura al custom-api y corrigió una falsificación de X-Forwarded-For que permitía eludir el límite de intentos de login. Opinión: es el mejor candidato para usar como pantalla de inicio de WINT en Windows, porque lee la API local de WINT sin Docker.
- Fuentes: https://github.com/glanceapp/glance, https://raw.githubusercontent.com/glanceapp/glance/main/docs/configuration.md, https://github.com/glanceapp/glance/releases.atom
- Confianza: alta en hechos; media en la recomendación (es opinión)
- Riesgo: alto
- Vigencia: feed consultado 7 de octubre de 2026

### H12 — Homarr: migración de repositorio y versión mayor recién lanzada
- Afirmación: el proyecto activo es homarr-labs/homarr (licencia Apache-2.0, instalación principal por Docker, soporte declarado para Windows, Linux, TrueNAS y Unraid, y Kubernetes/Helm; interfaz de arrastrar y soltar sin YAML; usuarios y permisos; inicio de sesión OIDC/LDAP; widgets en tiempo real con WebSockets y Redis). El repositorio original ajnart/homarr (MIT) aparece archivado y con aviso de migración; una lectura de esa página dio como fecha de archivo el 3 de junio de 2026 (una sola lectura). Releases del feed: v2.0.0 (2026-10-02), v2.1.1 (2026-10-03), v2.1.2 (2026-10-04), v2.2.0 (2026-10-05). La v2.0.0 introduce "Custom Widgets v2" (se escriben o se generan describiéndolos), "Workshop" (plataforma comunitaria de widgets y CSS), rediseño de tableros, "Integration Requests" (peticiones HTTP y MCP que reutilizan credenciales guardadas) y 31 integraciones nuevas. Hay discrepancia de cifras: el README leído habla de 80 o más integraciones y otra página de 100 o más. Opinión: con una versión mayor de cinco días y tres parches seguidos, conviene esperar.
- Fuentes: https://github.com/homarr-labs/homarr, https://github.com/ajnart/homarr, https://github.com/homarr-labs/homarr/releases.atom, https://github.com/homarr-labs/homarr/releases/latest
- Confianza: media
- Riesgo: alto
- Vigencia: feed consultado 7 de octubre de 2026 (v2.2.0 del 2026-10-05)

### H13 — Dashy, Homer y Heimdall: tableros más simples
- Afirmación: Dashy (MIT, Vue/Node; 26,6 mil estrellas): Docker (`docker run -p 4000:8080 lissy93/dashy`) o Node LTS (24.x recomendado), mínimo 1 GB de RAM y 1 GB de disco, corre en ARM; widgets incluyen "API Response" (JSON de un endpoint propio), iframe y HTML embed; autenticación opcional con SSO; releases v4.7.15 a v4.7.17 entre 2026-10-02 y 2026-10-03 (cambios muy frecuentes). Homer (Apache-2.0; 11,6 mil estrellas): sitio estático con un `config.yml`, PWA instalable, búsqueda difusa; advertencia oficial: el archivo `config.yml` queda expuesto en `/assets/config.yml` por HTTP, así que no debe llevar claves si no hay autenticación; las "smart cards" suelen requerir CORS o proxy; release v26.08.3 (2026-08-30). Heimdall (MIT; 9,3 mil estrellas): PHP 8.4+ con Laravel 11 y SQLite, "enhanced apps" con estadísticas en vivo; release v2.8.3 (2026-09-05). Opinión: Homer sirve como página de enlaces mínima, Dashy como alternativa a Glance si se quiere iframe o editor de interfaz, y Heimdall aporta poco para este caso.
- Fuentes: https://github.com/Lissy93/dashy, https://raw.githubusercontent.com/Lissy93/dashy/master/docs/widgets.md, https://github.com/Lissy93/dashy/releases.atom, https://github.com/bastienwirtz/homer, https://raw.githubusercontent.com/bastienwirtz/homer/main/docs/customservices.md, https://github.com/bastienwirtz/homer/releases.atom, https://github.com/linuxserver/Heimdall, https://github.com/linuxserver/Heimdall/releases.atom
- Confianza: alta
- Riesgo: alto
- Vigencia: feeds consultados 7 de octubre de 2026

### H14 — Home Assistant: API REST, app Android y notificaciones
- Afirmación: Home Assistant Core (Apache-2.0, Python, unas 91,3 mil estrellas) tiene versión 2026.9.4 (2026-09-27). La instalación recomendada es Home Assistant OS (en Raspberry Pi 4 o 5 con mínimo 2 GB de RAM, Odroid, x86-64, o la unidad Home Assistant Green); en contenedor Docker no hay "apps" (add-ons) ni actualización en un clic; en Windows solo se menciona como máquina virtual. Su API REST usa `/api/` en el puerto 8123 con encabezado `Authorization: Bearer <token de larga duración>`; endpoints `GET /api/states`, `POST /api/services/<dominio>/<servicio>` y `POST /api/states/<entity_id>` (crea o actualiza un estado representativo, sin hablar con dispositivos reales). La app Companion de Android (Kotlin con Jetpack Compose, Apache-2.0) ofrece widgets, notificaciones y ubicación, y recibe avisos con `notify.mobile_app_<dispositivo>` (campos `title`, `message` y, en Android, `channel`, `tag`, `importance`, `color`, `sticky`). Home Assistant también tiene integración oficial con ntfy. Opinión: para WINT solo vale la pena si ya se usa Home Assistant; no debería ser la base.
- Fuentes: https://github.com/home-assistant/core, https://github.com/home-assistant/core/releases/latest, https://raw.githubusercontent.com/home-assistant/home-assistant.io/current/source/installation/index.html, https://raw.githubusercontent.com/home-assistant/developers.home-assistant/master/docs/api/rest.md, https://github.com/home-assistant/android, https://raw.githubusercontent.com/home-assistant/companion.home-assistant/master/docs/notifications/basic.md, https://raw.githubusercontent.com/home-assistant/home-assistant.io/current/source/_integrations/ntfy.markdown
- Confianza: alta
- Riesgo: alto
- Vigencia: release 2026.9.4 del 27 de septiembre de 2026; consultado 7 de octubre de 2026

### H15 — Umbrel, CasaOS y YunoHost: sistemas operativos de servidor doméstico
- Afirmación: umbrelOS 2.0 se publicó el 2026-09-22 (betas 2026-09-02 y 2026-09-17); licencia PolyForm Noncommercial 1.0.0 (uso personal y sin fines de lucro; uso comercial requiere autorización); mínimo para x86: CPU de dos núcleos, 4 GB de RAM (se recomiendan 8 GB o más) y 32 GB de disco; más de 300 apps; la 2.0 incluye "Machines" (ejecutar Windows, Ubuntu y Android dentro de Umbrel), servidor MCP para agentes de IA, varios usuarios y HTTPS automático. CasaOS (Apache-2.0; 37,3 mil estrellas): último estable v0.4.15 (2024-12-19) y una alfa v0.4.17-alpha1 (2025-04-17); soporte oficial para Debian 12, Ubuntu Server 20.04 y Raspberry Pi OS; sin releases estables desde hace unos 22 meses. YunoHost (AGPL-3.0; sobre Debian; panel de administración y portal de inicio de sesión único): último release visible debian/12.1.41.2 (3 de septiembre; año no confirmado). Los tres necesitan un equipo Linux o una máquina virtual siempre encendida, ajeno al uso previsto solo-Windows de WINT. Opinión: descartarlos como pantalla de inicio.
- Fuentes: https://github.com/getumbrel/umbrel, https://github.com/getumbrel/umbrel/releases.atom, https://github.com/IceWhaleTech/CasaOS, https://github.com/IceWhaleTech/CasaOS/releases.atom, https://github.com/YunoHost/yunohost, https://github.com/YunoHost/yunohost/releases/latest
- Confianza: alta en Umbrel y CasaOS; media en YunoHost
- Riesgo: alto
- Vigencia: feeds consultados 7 de octubre de 2026

### H16 — Lawnchair: launcher para Android basado en Launcher3 (y el dato de Nova)
- Afirmación: el README de Lawnchair declara que "Lawnchair 16" está en desarrollo sobre el Launcher3 de Android 16, con tema Material 3, widget "At a Glance" e integración con Smartspacer, búsqueda global y QuickSwitch para Android 15–16 (requiere root). Feed de releases: Lawnchair Nightly (2026-10-06), Lawnchair 15 Beta 3 (2026-04-18), Beta 2.1 (2026-03-09) y Beta 2 (2025-12-25). La Beta 3 agrega importar copias de seguridad de Nova Launcher (restaura disposición de íconos, widgets, carpetas y paquetes de íconos). Distribución: Google Play, IzzyOnDroid, Obtainium y GitHub. Conflicto: la página "releases/latest" muestra como última versión 1.2.0.1884 (23 de julio, descrita como "final release for Lawnchair v1"), porque las versiones nuevas están marcadas como prelanzamiento; para un usuario, "lo más reciente" depende de dónde se mire. La licencia y el mínimo de Android no se confirmaron en la fuente leída. El estado de Nova Launcher en 2026 NO pudo verificarse; la función de importación de Lawnchair solo indica que hay migración desde Nova, no el estado de Nova.
- Fuentes: https://github.com/LawnchairLauncher/lawnchair, https://github.com/LawnchairLauncher/lawnchair/releases.atom, https://github.com/LawnchairLauncher/lawnchair/releases/latest
- Confianza: media
- Riesgo: alto
- Vigencia: feed consultado 7 de octubre de 2026 (nightly del 2026-10-06)

### H17 — Qué implica que WINT sea un launcher en Android (Olauncher como ejemplo)
- Afirmación: Olauncher (GPLv3, 3,9 mil estrellas; Google Play, F-Droid, IzzyOnDroid) es un launcher minimalista sin widgets por defecto; existe una versión paga "Pro Launcher" con widgets y clima. Su AndroidManifest declara la actividad principal con acción `android.intent.action.MAIN` y categorías `HOME`, `DEFAULT` y `LAUNCHER`, que es lo que lo habilita como pantalla de inicio. También pide permisos como `QUERY_ALL_PACKAGES` (enumerar apps), `PACKAGE_USAGE_STATS`, `SET_WALLPAPER`, `EXPAND_STATUS_BAR` e incluye servicio de accesibilidad y receptor de administrador de dispositivo. Evidencia de mantenimiento por versión de Android: Smartspacer 1.11.3 (2026-08-29) "Fixed widgets not loading on Android 17 QPR2"; Termux v0.118.3 corrigió un crash en Android 16 QPR1; Syncthing-Fork 2.1.6.0 subió a target SDK Android 17. Opinión: construir un launcher propio obliga a reexaminar cada versión trimestral del sistema (QPR) y a competir con launchers ya hechos; por eso se desaconseja. Lo que no verifiqué: las condiciones de Google Play para permisos como `QUERY_ALL_PACKAGES`.
- Fuentes: https://github.com/tanujnotes/Olauncher, https://raw.githubusercontent.com/tanujnotes/Olauncher/master/app/src/main/AndroidManifest.xml, https://github.com/kieronquinn/Smartspacer/releases.atom, https://github.com/termux/termux-app/releases.atom, https://github.com/researchxxl/syncthing-android/releases.atom
- Confianza: alta en los hechos del manifiesto; media en la conclusión (opinión)
- Riesgo: alto
- Vigencia: feeds consultados 7 de octubre de 2026

### H18 — Alternativas a ser launcher: Smartspacer, HTTP Shortcuts y Termux
- Afirmación: Smartspacer (app GPLv3, SDK Apache-2.0; 3,6 mil estrellas) reemplaza el "At a Glance" de Pixel sin root y funciona con cualquier launcher; terceros pueden crear plugins que aportan "targets" y complicaciones mediante su SDK; versión 1.11.4 (2026-10-02), 1.11.3 (2026-08-29), 1.11.2 (2026-07-23). HTTP Shortcuts (MIT; 1,8 mil estrellas; Google Play, F-Droid y APK): crea accesos y widgets que lanzan peticiones HTTP (GET, POST, PUT, DELETE y otros) con autenticación Basic, Digest, Bearer o certificado de cliente, variables, JavaScript antes y después de la petición, respuesta mostrada como toast, diálogo, HTML, imagen o página; también soporta MQTT y Wake-on-LAN; versión v4.8.1 (2026-10-05). Termux (62,1 mil estrellas): terminal y entorno Linux en Android 7 o superior; versión estable v0.118.3 (2025-05-22); complementos Termux:API, :Boot, :Widget, :Tasker; la versión de Google Play es experimental (Android 11+, funciones reducidas) y los APK de distintas fuentes no se pueden mezclar por las firmas. Opinión: Smartspacer más HTTP Shortcuts permiten mostrar datos de WINT y disparar rutinas desde Android sin construir ninguna app.
- Fuentes: https://github.com/kieronquinn/Smartspacer, https://github.com/kieronquinn/Smartspacer/releases.atom, https://github.com/Waboodoo/HTTP-Shortcuts, https://github.com/Waboodoo/HTTP-Shortcuts/releases.atom, https://github.com/termux/termux-app, https://github.com/termux/termux-app/releases.atom
- Confianza: alta
- Riesgo: alto
- Vigencia: feeds consultados 7 de octubre de 2026

### H19 — KDE Connect: puente en la misma red, con comandos remotos
- Afirmación: KDE Connect (GPLv2 y GPLv3) conecta teléfono y PC por Wi-Fi con cifrado TLS. Funciones del README: sincronizar portapapeles, ver notificaciones de Android en la PC, compartir archivos y enlaces, control de reproductores de medios, panel táctil virtual, control remoto de presentaciones, SMS/MMS desde el escritorio y ejecución de comandos de shell desde el teléfono. Plataformas: Linux (Qt 6), Android (Google Play y F-Droid), iPhone/iPad (App Store), Windows (Microsoft Store) y BSD sin soporte oficial. En Windows "most of the features have already been ported" pero con menos pruebas. Los repositorios de GitHub son espejos; el oficial es invent.kde.org. Opinión: el comando remoto es el único mecanismo de la lista que dispara un programa de la PC desde el teléfono sin servidor propio, pero depende de estar en la misma red. Versión mínima de Android y número de versión: no verificados.
- Fuentes: https://github.com/KDE/kdeconnect-kde, https://github.com/KDE/kdeconnect-android
- Confianza: media
- Riesgo: alto
- Vigencia: consultado 7 de octubre de 2026 (README sin fecha)

### H20 — Syncthing: la app oficial de Android fue discontinuada; el reemplazo es Syncthing-Fork
- Afirmación: Syncthing (MPL-2.0) publicó v2.1.6 el 2026-10-06 (novedades de 2.1: agrupar dispositivos y carpetas en la interfaz, proxy HTTP/HTTPS, desactivar el indexado de bloques por carpeta). El repositorio syncthing/syncthing-android está archivado y su aviso dice "This app is discontinued. The last release on Github and F-Droid will happen with the December 2024 Syncthing version" (archivado el 3 de diciembre de 2024 según la lectura; motivos citados: dificultad de publicar en Google Play y falta de mantenimiento). La continuación es Syncthing-Fork (mantenedor researchxxl, MPL-2.0; distribución GitHub, F-Droid y Obtainium; Google Play no figura): v2.1.6.0 (2026-10-06), con "target sdk is now Android 17". Opinión: sincronizar exportaciones (JSON o CSV) en lugar de archivos SQLite abiertos, por riesgo de corrupción al sincronizar una base en uso (no verificado en fuente).
- Fuentes: https://github.com/syncthing/syncthing, https://github.com/syncthing/syncthing/releases.atom, https://github.com/syncthing/syncthing-android, https://github.com/researchxxl/syncthing-android, https://github.com/researchxxl/syncthing-android/releases.atom
- Confianza: alta
- Riesgo: alto
- Vigencia: feeds consultados 7 de octubre de 2026

### H21 — Tailscale y Headscale: acceso remoto al panel sin abrir puertos
- Afirmación: el cliente de Tailscale es BSD-3-Clause; `tailscaled` corre en Linux, Windows, macOS, FreeBSD/OpenBSD, e iOS y Android (la interfaz móvil no está en ese repositorio). Versiones: la página "releases/latest" muestra v1.102.5 (29 de septiembre), pero el feed lista la etiqueta v1.104.0 (2026-09-30T19:06Z) y v1.105.0-pre; ambas cifras se registran porque no pude reconciliarlas. Headscale es una implementación libre y autoalojada del servidor de control de Tailscale (BSD-3-Clause; 44,4 mil estrellas), pensada para "una sola tailnet" (uso personal o una organización pequeña) y no afiliada a Tailscale Inc. Precio y límites del plan gratuito de Tailscale: NO verificados (sitio bloqueado). Homepage advierte que los despliegues públicos deben ir detrás de VPN o proxy inverso, y Homer expone su configuración por HTTP, lo que apoya acceder al panel solo por red privada.
- Fuentes: https://github.com/tailscale/tailscale, https://github.com/tailscale/tailscale/releases/latest, https://github.com/tailscale/tailscale/releases.atom, https://github.com/juanfont/headscale
- Confianza: media
- Riesgo: alto
- Vigencia: feed consultado 7 de octubre de 2026

### H22 — ntfy: avisos al celular con una línea de curl
- Afirmación: ntfy es un servicio de notificaciones por HTTP (publicar con PUT o POST, sin registro en el servicio público ntfy.sh; también autoalojable), con apps para Android (Google Play y F-Droid) e iOS, y soporte de UnifiedPush. Licencia doble Apache 2.0 y GPLv2; la versión alojada ofrece un plan "ntfy Pro" desde 5 dólares al mes. Ejemplo oficial: `curl -d "Backup successful" ntfy.sh/mytopic`. Prioridades de 1 (mínima) a 5 (urgente) con la cabecera `X-Priority`; etiquetas con `X-Tags`; abrir una URL al tocar con `X-Click`; hasta tres botones con `X-Actions` de tipo `view`, `broadcast` (intents de Android), `http` o `copy`; adjuntos hasta 15 MB (subidos por PUT, expiran a las 3 horas); mensajes de más de 4096 bytes se convierten en adjunto; autenticación Bearer o Basic. Releases: v2.28.0 (2026-08-27, límites de 1 KB al título y 512 bytes a las etiquetas, tope de 10 MB por tema al reenviar caché) y v2.27.0 (2026-08-04, inicio de sesión por correo y PostgreSQL ya sin marca experimental). Home Assistant tiene integración oficial con ntfy. Opinión: en el servicio público el nombre del tema funciona como contraseña, así que usar nombres largos e imposibles de adivinar o autoalojar con autenticación.
- Fuentes: https://github.com/binwiederhier/ntfy, https://raw.githubusercontent.com/binwiederhier/ntfy/main/docs/publish.md, https://github.com/binwiederhier/ntfy/releases.atom, https://raw.githubusercontent.com/home-assistant/home-assistant.io/current/source/_integrations/ntfy.markdown
- Confianza: alta
- Riesgo: alto
- Vigencia: feed consultado 7 de octubre de 2026 (v2.28.0 del 2026-08-27)

### H23 — Búsqueda unificada: SearXNG, Meilisearch y DocFetcher; qué es un "Google comprimido"
- Afirmación (hechos): SearXNG (AGPL-3.0, 38,1 mil estrellas) es un metabuscador que agrega resultados de otros servicios sin rastrear al usuario; se instala con Docker. Su API de búsqueda (`GET` o `POST` a `/search`) acepta `q`, `format` (`json`, `csv`, `rss`), `categories`, `language`, `pageno`, `time_range` y `safesearch`; los formatos admitidos se definen en `settings.yml` (sección `search`) y pedir uno no habilitado devuelve 403; en el `settings.yml` del repositorio el valor por defecto es `formats: - html`, `limiter: false`, `public_instance: false` y `secret_key: "ultrasecretkey"` (hay que cambiarla). Meilisearch (59,5 mil estrellas; edición comunitaria MIT, edición empresarial con licencia comercial o BUSL 1.1) ofrece búsqueda al escribir, tolerancia a errores de tipeo, búsqueda híbrida y binario único; está escrito en Rust. DocFetcher (Apache-2.0): el repositorio de GitHub leído muestra muy poca actividad (parece espejo); su estado real y el de Recoll NO pudieron verificarse. (Opinión): "Google comprimido" como producto = índice unificado sobre las fuentes del usuario (catálogos, historial de precios, notas) con operadores explícitos (por ejemplo precio, comercio, variación) y acciones sobre el resultado; SearXNG cubre solo la web externa, no esos datos. Como el usuario ya usa SQLite, el motor natural sería su extensión FTS5 (documentación oficial no abierta: sqlite.org bloqueado, confianza baja); Meilisearch queda como mejora si se necesitan tolerancia a typos y ranking.
- Fuentes: https://github.com/searxng/searxng, https://raw.githubusercontent.com/searxng/searxng/master/docs/dev/search_api.rst, https://raw.githubusercontent.com/searxng/searxng/master/searx/settings.yml, https://github.com/meilisearch/meilisearch, https://github.com/docfetcher/DocFetcher
- Confianza: alta en SearXNG y Meilisearch; baja en FTS5, DocFetcher y Recoll
- Riesgo: alto
- Vigencia: consultado 7 de octubre de 2026 (archivos de la rama principal, sin fecha)

### H24 — Windows Subsystem for Android (WSA) fue retirado
- Afirmación: el repositorio oficial microsoft/WSA anuncia que "Windows Subsystem for Android and the Amazon Appstore will no longer be available in the Microsoft Store after March 5, 2025"; el repositorio quedó archivado en modo solo lectura el 20 de mayo de 2025. Consecuencia: si "plataforma Android" se entendiera como correr apps de Android dentro de Windows, esa vía oficial ya no existe. Umbrel 2.0 ofrece "Machines" para ejecutar Android, pero dentro de un servidor Umbrel, no en Windows.
- Fuentes: https://github.com/microsoft/WSA, https://github.com/getumbrel/umbrel/releases/latest
- Confianza: alta
- Riesgo: alto
- Vigencia: soporte terminado el 5 de marzo de 2025; consultado 7 de octubre de 2026

### H25 — Los lanzadores incorporan IA y MCP; WINT puede conservar su diseño determinista
- Afirmación (hechos): Raycast 2.5.0 (2026-09-24) permite a las extensiones aportar modelos de IA, declarar servidores MCP y empaquetar Agent Skills; Wox 2.4.5 y 2.4.2 añadieron "AI Chat" y configuración de servidores MCP; umbrelOS 2.0 trae servidor MCP para agentes; Homarr 2.0.0 permite generar widgets describiéndolos y expone "Integration Requests" por HTTP y MCP; el protocolo JSON-RPC de Flow Launcher es una petición que recibe una lista de resultados, sin diálogo. (Opinión): el diferencial de WINT (reglas explícitas, sin preguntar ni evaluar) no choca con estas herramientas, porque sus funciones de IA son opcionales; conviene definir un contrato de comandos cerrado (gramática fija, respuestas con plantilla) y dejar la IA solo para construir el software, no para ejecutarlo.
- Fuentes: https://raw.githubusercontent.com/raycast/extensions/main/docs/changelog.md, https://github.com/Wox-launcher/Wox/releases, https://github.com/getumbrel/umbrel/releases/latest, https://github.com/homarr-labs/homarr/releases.atom, https://raw.githubusercontent.com/Flow-Launcher/docs/main/json-rpc.md
- Confianza: media
- Riesgo: bajo
- Vigencia: consultado 7 de octubre de 2026

## Herramientas y software

| Nombre | Qué hace | Plataforma | Licencia o precio | Estado a octubre 2026 (última versión/fecha) | URL oficial | Encaje con WINT (alto/medio/bajo) | Salvedad |
|---|---|---|---|---|---|---|---|
| Flow Launcher | Lanzador y buscador con plugins (C#, F#, Python, JS, TS) | Windows 10 o superior | MIT, gratis | v2.1.4 (2026-09-20) | https://github.com/Flow-Launcher/Flow.Launcher | alto | flowlauncher.com no se pudo abrir; la documentación se leyó en el repositorio de docs |
| PowerToys Command Palette | Paleta de comandos extensible (Win+Alt+Space), con Dock | Windows (desarrollo documentado en Windows 11) | MIT, gratis | Estable v0.101.2362.0 (25 ago 2026); preview v0.101.2781.0 (7 oct 2026) | https://github.com/microsoft/PowerToys | alto | README del módulo dice "preview" y cambios posibles antes de 1.0; extensiones solo en C# hoy |
| PowerToys Run | Lanzador previo (Alt+Space) con unos 15 plugins | Windows | MIT, gratis | En transición hacia Command Palette ("v2") | https://github.com/microsoft/PowerToys | bajo | Doc de ms.date 20/08/2025; no desarrollar plugins nuevos para él |
| Wox | Lanzador multiplataforma, plugins Node.js/Python/scripts | Windows, macOS, Linux | GPL-3.0, gratis | v2.4.6 (2026-10-06) | https://github.com/Wox-launcher/Wox | medio | Cadencia semanal; sitio woxlauncher.com no abierto |
| Keypirinha | Lanzador por teclado | Windows | Licencia no verificada | v2.26 (2020-11-08) | https://github.com/Keypirinha/Keypirinha | bajo | Sin releases desde 2020 |
| Everything y ES | Búsqueda instantánea de archivos y CLI con salida JSON/CSV | Windows | ES: MIT; Everything: no verificada | ES sin versión visible | https://github.com/voidtools/ES | medio | voidtools.com bloqueado; ES requiere Everything corriendo |
| Raycast | Lanzador con extensiones React/TypeScript | macOS y Windows | Precio no verificado; repo de extensiones MIT | App 2.0.0 (2026-08-25); API 2.5.0 (2026-09-24) | https://github.com/raycast/extensions | medio | raycast.com bloqueado: precio y si Windows es beta o general, sin verificar |
| Windows Search / Microsoft Search | Indexador de Windows (OLE DB y SQL) y búsqueda de Microsoft 365 | Windows | Incluido en Windows | Doc de Windows Search de 31/05/2018; Microsoft Search sin verificar | https://github.com/MicrosoftDocs/win32/tree/docs/desktop-src/search | bajo | Extender requiere código nativo (COM) |
| Home Assistant (Core y app Companion) | Domótica, tableros, API REST, notificaciones al celular | Linux o VM; app Android | Apache-2.0, gratis | 2026.9.4 (2026-09-27) | https://github.com/home-assistant/core | bajo | home-assistant.io bloqueado; en Windows solo por VM; mínimo de Android de la app no verificado |
| Homarr | Tablero con integraciones y widgets personalizados | Docker (Windows, Linux, Unraid, TrueNAS) | Apache-2.0, gratis | v2.2.0 (2026-10-05); v2.0.0 el 2026-10-02 | https://github.com/homarr-labs/homarr | medio | Versión mayor de cinco días; cifras de integraciones discrepantes |
| Dashy | Tablero con widgets (API Response, iframe, HTML) | Docker o Node LTS | MIT, gratis | v4.7.17 (2026-10-03) | https://github.com/Lissy93/dashy | medio | Releases casi diarios |
| Homepage (gethomepage) | Tablero YAML con widget Custom API | Docker, Kubernetes, código fuente | GPL-3.0, gratis | v2.4.0 (2026-09-17) | https://github.com/gethomepage/homepage | medio | Documentación leída no trata Windows; gethomepage.dev bloqueado |
| Glance | Tablero YAML de un binario, widget custom-api con plantillas Go | Binarios Windows, Linux, macOS; Docker | AGPL-3.0, gratis | v0.8.6 (2026-09-03) | https://github.com/glanceapp/glance | alto | Aún 0.x; cadencia lenta |
| Heimdall | Tablero de aplicaciones con estadísticas | PHP 8.4+ o Docker | MIT, gratis | v2.8.3 (2026-09-05) | https://github.com/linuxserver/Heimdall | bajo | Aporta poco al caso |
| Homer | Página estática de servicios (YAML, PWA) | Docker o archivos estáticos | Apache-2.0, gratis | v26.08.3 (2026-08-30) | https://github.com/bastienwirtz/homer | medio | config.yml queda expuesto por HTTP |
| Umbrel (umbrelOS) | SO de servidor doméstico con tienda de apps | x86, Raspberry Pi 5, VM | PolyForm Noncommercial 1.0.0 | 2.0 (2026-09-22) | https://github.com/getumbrel/umbrel | bajo | Requiere equipo dedicado; licencia no comercial |
| CasaOS | Nube personal con tienda de apps | Linux (Debian 12, Ubuntu Server 20.04) | Apache-2.0, gratis | v0.4.15 (2024-12-19); alfa v0.4.17-alpha1 (2025-04-17) | https://github.com/IceWhaleTech/CasaOS | bajo | Estancado |
| YunoHost | SO de servidor sobre Debian con portal SSO | Debian | AGPL-3.0, gratis | debian/12.1.41.2 (3 sep; año sin confirmar) | https://github.com/YunoHost/yunohost | bajo | Fecha con año no confirmado |
| Lawnchair | Launcher Android sobre Launcher3 | Android | Licencia no confirmada en fuente leída | 15 Beta 3 (2026-04-18); Nightly 2026-10-06 | https://github.com/LawnchairLauncher/lawnchair | medio | "releases/latest" muestra 1.2.0.1884 (v1 final) |
| Olauncher | Launcher minimalista sin widgets | Android | GPLv3; Pro Launcher de pago | Sin versión visible | https://github.com/tanujnotes/Olauncher | bajo | Útil sobre todo como ejemplo de manifiesto HOME |
| Smartspacer | Reemplazo de "At a Glance" con plugins y SDK | Android (con cualquier launcher) | App GPLv3; SDK Apache-2.0 | 1.11.4 (2026-10-02) | https://github.com/kieronquinn/Smartspacer | alto | Se corrige con cada versión de Android (17 QPR2) |
| HTTP Shortcuts | Accesos y widgets que lanzan peticiones HTTP, con JavaScript | Android | MIT, gratis | v4.8.1 (2026-10-05) | https://github.com/Waboodoo/HTTP-Shortcuts | alto | Sitio http-shortcuts.rmy.ch no abierto |
| Termux | Terminal y entorno Linux en Android | Android 7 o superior | Licencia no verificada | v0.118.3 (2025-05-22) | https://github.com/termux/termux-app | medio | Versión de Google Play experimental; no mezclar APK de distintas fuentes |
| Niagara Launcher | Launcher minimalista | Android | No verificado | No verificado | No verificada | bajo | Sin acceso a su sitio ni a la tienda |
| Nova Launcher | Launcher personalizable | Android | No verificado | No verificado | No verificada | bajo | Estado 2026 sin verificar; Lawnchair 15 Beta 3 importa sus copias |
| Smart Launcher | Launcher con categorías automáticas | Android | No verificado | No verificado | No verificada | bajo | Sin acceso a fuentes |
| Enlace a Windows (Phone Link) | Puente oficial de Microsoft para notificaciones, mensajes, fotos y apps | Windows y Android | No verificado | No verificado | No verificada | medio | No se pudo abrir ninguna fuente de Microsoft; no depender de él sin probar |
| KDE Connect | Puente en la misma red: notificaciones, portapapeles, archivos, comandos | Windows, Linux, Android, iOS | GPLv2 y GPLv3, gratis | Sin versión visible | https://github.com/KDE/kdeconnect-kde (espejo; oficial invent.kde.org) | medio | Solo misma red; Windows con menos pruebas |
| Syncthing | Sincronización de archivos entre equipos (P2P) | Windows, Linux, macOS | MPL-2.0, gratis | v2.1.6 (2026-10-06) | https://github.com/syncthing/syncthing | medio | App Android oficial discontinuada (dic 2024) |
| Syncthing-Fork | Continuación de la app de Android | Android | MPL-2.0, gratis | v2.1.6.0 (2026-10-06) | https://github.com/researchxxl/syncthing-android | medio | Distribución por GitHub, F-Droid y Obtainium; Google Play no figura |
| Tailscale | Red privada WireGuard entre PC y teléfono | Windows, Linux, macOS, Android, iOS | Cliente BSD-3-Clause; precio no verificado | Release marcado v1.102.5; feed v1.104.0 (2026-09-30) | https://github.com/tailscale/tailscale | alto | Dos versiones discrepantes; tailscale.com bloqueado |
| Headscale | Servidor de control autoalojado compatible con Tailscale | Linux (servidor) | BSD-3-Clause, gratis | Sin versión visible | https://github.com/juanfont/headscale | bajo | Una sola tailnet; más mantenimiento |
| Pushbullet | Puente de notificaciones y portapapeles | Windows, Android | No verificado | No verificado | No verificada | bajo | Estado 2026 sin verificar; el repo pushbullet/api dio 404 |
| Join | Puente (joaomgcd) de acciones y notificaciones | Android, Windows | No verificado | No verificado | No verificada | bajo | Repositorio joaomgcd/Join dio 404; estado sin verificar |
| ntfy | Notificaciones push por HTTP (PUT/POST) | Servidor Go; apps Android e iOS | Apache 2.0 y GPLv2; ntfy Pro desde 5 USD al mes | v2.28.0 (2026-08-27) | https://github.com/binwiederhier/ntfy | alto | Tema del servicio público equivale a contraseña; autoalojar con auth |
| SearXNG | Metabuscador web sin rastreo, API JSON | Docker o Python | AGPL-3.0, gratis | Sin versión visible | https://github.com/searxng/searxng | medio | Solo web; habilitar `json` en settings.yml; cambiar `secret_key` |
| Meilisearch | Motor de búsqueda local con tolerancia a typos y modo híbrido | Binario único (Rust) | Comunitaria MIT; empresarial comercial o BUSL 1.1 | Sin versión visible | https://github.com/meilisearch/meilisearch | medio | meilisearch.com/docs no abierto |
| DocFetcher | Buscador de documentos de escritorio | Windows, macOS, Linux | Apache-2.0 | Poca actividad visible | https://github.com/docfetcher/DocFetcher | bajo | Posible espejo; estado real sin verificar |
| Recoll | Buscador de documentos de escritorio | Windows, Linux | No verificado | No verificado | No verificada | bajo | Fuente no accesible |
| SQLite FTS5 | Búsqueda de texto completo dentro de SQLite | Cualquiera (SQLite) | Dominio público (no verificado en fuente) | No verificado | No verificada | alto | sqlite.org bloqueado; confianza baja |
| Windows Subsystem for Android | Apps de Android dentro de Windows | Windows 11 | Gratis | Discontinuado: fin de soporte 5 mar 2025 | https://github.com/microsoft/WSA | bajo | Repositorio archivado desde 20 may 2025 |

## Esquema para cuadro sinóptico

- Puerta única WINT
  - Lanzadores Windows
    - Flow Launcher (plugin Python)
    - Command Palette (extensión C#)
    - Raycast 2.0 (TypeScript)
    - Wox, Everything, ES
    - Keypirinha (abandonado)
  - Tableros autoalojados
    - Glance (binario Windows)
    - Homepage y Dashy
    - Homarr (esperar)
    - Homer, Heimdall
    - Home Assistant (solo si ya existe)
    - Umbrel, CasaOS, YunoHost (descartar)
  - Android
    - Lawnchair y Olauncher
    - Smartspacer (At a Glance)
    - HTTP Shortcuts (widgets)
    - Termux (scripts)
    - Launcher propio (no)
  - Puentes Windows–Android
    - Tailscale (acceso remoto)
    - ntfy (avisos)
    - Syncthing-Fork (archivos)
    - KDE Connect (misma red)
    - Enlace a Windows (sin verificar)
  - Búsqueda unificada
    - SQLite FTS5 (núcleo)
    - Meilisearch (opcional)
    - SearXNG (solo web)
  - Construir o reutilizar
    - Construir: API, reglas, índice
    - Reutilizar: lanzador, tablero, push

## Recomendaciones para WINT

1. Separar un núcleo de WINT de sus "puertas". El núcleo es un servicio local en 127.0.0.1 que expone una API JSON con rutas fijas (por ejemplo ofertas del día, comparación entre comercios, catálogo por tema, ejecutar Sol, ejecutar Luna, estado). Todo lo demás (lanzador, tablero, teléfono) es un adaptador que llama a esa API. Por qué: las herramientas relevadas (plugin de Flow por JSON-RPC, widget custom-api de Glance, Custom API de Homepage, REST de Home Assistant, HTTP Shortcuts en Android) consumen justamente JSON por HTTP; así se escribe la lógica una sola vez y cambiar de lanzador no cuesta nada.
2. Primer adaptador: un plugin de Flow Launcher en Python (H5, H6). Por qué: es un `plugin.json` más un `main.py` con `query()` y `context_menu()`, se instala con `pm install` o copiando la carpeta, hay documentación oficial por lenguaje, y la persona ya programa con ayuda de IA en Python. Palabras clave sugeridas: `sol`, `luna`, `oferta`, `precio`.
3. Segundo adaptador, a esperar: una extensión de Command Palette. Por qué: es la dirección de Microsoft (H1), pero hoy exige C#, MSIX, Visual Studio con cargas WinUI/Windows App SDK y Windows 11 (H2); el roadmap v0.102 promete JavaScript/TypeScript (H4) sin confirmación. Reevaluar cuando salga 0.102 estable. Para uso personal basta el despliegue local, sin Store.
4. Tablero: Glance en Windows con widgets `custom-api` que lean la API de WINT; si se prefiere Docker, Homepage con su widget Custom API (H10, H11). Por qué: Glance es un binario único con plantillas, sin Docker. Evitar por ahora Homarr (versión mayor del 2 de octubre de 2026, H12), CasaOS (estancado, H15), Umbrel y YunoHost (equipo dedicado, H15) y Keypirinha (H7). Mantener el panel de catálogos "estilo Netflix" propio como página enlazada o incrustada (Dashy permite iframe, H13): los tableros genéricos son de enlaces, estados y widgets de texto, no de carruseles de catálogo (opinión).
5. Notificaciones: ntfy (H22). Cada aviso se publica con un `curl` o una petición HTTP desde Python; priorizar con `X-Priority` (oferta real = 4, falla del detector = 3), abrir la página del producto con `X-Click` y usar `X-Actions` con tipo `http` para acciones de un toque (por ejemplo "silenciar este producto"). Usar un tema largo y no adivinable o autoalojar con autenticación; las plantillas de mensaje son fijas, lo que mantiene el comportamiento determinista. Si algún día se usa Home Assistant, ya tiene integración con ntfy.
6. Android: no construir un launcher (H17). Armar la pantalla de inicio con un launcher existente (Lawnchair u otro) más Smartspacer, para mostrar datos de WINT en "At a Glance" mediante un plugin (H18), y widgets de HTTP Shortcuts para disparar Sol, Luna y consultas (H18). Por qué: el costo de un launcher propio es seguir cada versión de Android (widgets rotos en Android 17 QPR2, crash en Android 16 QPR1) además de la política de permisos como `QUERY_ALL_PACKAGES`. Si más adelante se necesita app propia, preferir una PWA del panel antes que una app nativa.
7. Acceso desde el teléfono fuera de casa: Tailscale en PC y teléfono, con el panel escuchando solo en la red privada (H21). No abrir puertos del router. Headscale solo si se quiere evitar el servidor de control de Tailscale, a costa de mantener un servidor. Verificar el plan y límites vigentes de Tailscale antes de depender de él (no pude).
8. Puentes opcionales: KDE Connect para portapapeles, notificaciones y ejecutar un comando de la PC desde el teléfono en la misma red (H19); Enlace a Windows (Phone Link) solo si funciona bien en el equipo de la persona, y sin hacerlo dependencia de WINT, porque no pude verificar su estado 2026. Syncthing-Fork (H20) solo para copiar exportaciones (JSON o CSV) al teléfono, no el archivo SQLite en uso.
9. Búsqueda unificada ("Google comprimido", H23): empezar con una tabla FTS5 en la base SQLite existente con columnas del tipo fuente, título, cuerpo, precio, fecha, comercio, y una gramática fija de operadores (`precio<`, `comercio:`, `cambio>`); Meilisearch solo si hace falta tolerancia a errores de tipeo y ranking. SearXNG como pestaña "web" separada (habilitar `json`, cambiar `secret_key`); Everything o ES para archivos locales. Antes de decidir, confirmar la documentación oficial de FTS5 (no pude abrirla).
10. Conservar el diseño determinista (H25): sin LLM en tiempo de ejecución, comandos con gramática cerrada y respuestas por plantilla; desactivar o no usar las funciones de IA y MCP de Raycast, Wox o Homarr si se adoptan. La IA queda como ayuda para escribir el código, no como parte del producto.
11. Seguridad mínima en todo lo que se instale: token tipo Bearer en la API de WINT; `HOMEPAGE_ALLOWED_HOSTS` si se usa Homepage; no poner claves en el `config.yml` de Homer; cambiar `secret_key` en SearXNG; y no exponer ningún panel a internet sin VPN o proxy con autenticación (H10, H13, H21, H23).
12. Validar con una prueba de punta a punta de un día antes de invertir más: una oferta falsa generada en la API local, mostrada en Flow Launcher, Glance y ntfy en el teléfono. Si las tres puertas la muestran bien, el resto es repetición.

Cuadro de decisión: construir o reutilizar por capa (los costos de mantenimiento son estimaciones propias, en opinión, no datos de las fuentes)

| Capa | Construir | Reutilizar | Mantenimiento estimado | Por qué |
|---|---|---|---|---|
| Núcleo y reglas (API local, Sol/Luna, detector) | Sí | Nada equivalente | Medio, es el producto | Es lo que diferencia a WINT |
| Puerta de entrada en la PC | Solo un plugin pequeño | Flow Launcher (ahora); Command Palette (cuando haya JS/TS) | Bajo: un plugin; alto si fuese una app de interfaz propia | Los lanzadores ya resuelven teclado, ranking y ventana |
| Tablero o pantalla de inicio | Solo el panel "estilo Netflix" ya hecho | Glance u Homepage para estados y accesos | Bajo a medio | Los tableros genéricos no hacen catálogos visuales |
| Notificaciones | Solo las reglas de qué avisar | ntfy | Bajo | Una petición HTTP y apps ya existentes |
| Puente móvil (acceso y acciones) | Nada | Tailscale, HTTP Shortcuts, Smartspacer, KDE Connect opcional | Bajo | Evita escribir y mantener una app nativa |
| Launcher de Android | No | Lawnchair, Olauncher u otro | Alto si se construye | Cada versión de Android rompe cosas (H17) |
| Búsqueda unificada | Conectores de cada fuente al índice | SQLite FTS5 o Meilisearch; SearXNG para la web | Medio | El motor existe; los conectores son propios |
| Sincronización de archivos | No | Syncthing y Syncthing-Fork | Bajo | Solo para exportaciones, no para la base en uso |

## Qué no se pudo verificar

- Limitaciones de herramientas: el presupuesto de WebSearch del turno (200 búsquedas compartidas) estaba agotado, así que las cinco búsquedas intentadas no se ejecutaron y no hubo ninguna búsqueda web. El proxy de salida solo permitió github.com y raw.githubusercontent.com; bloqueó learn.microsoft.com, support.microsoft.com, blogs.windows.com, www.raycast.com, developers.raycast.com, www.flowlauncher.com, www.home-assistant.io, syncthing.net, kdeconnect.kde.org, tailscale.com, docs.ntfy.sh, gethomepage.dev, docs.searxng.org, www.sqlite.org, play.google.com, f-droid.org, novalauncher.com, www.pushbullet.com y en.wikipedia.org. No se intentó rodear estos bloqueos. Un intento de leer el README del proxy fue denegado por el sistema de permisos y no se insistió. El servidor MCP de GitHub solo admite el repositorio de la sesión.
- Enlace a Windows (Phone Link) y su estado en 2026: no se pudo abrir ninguna fuente de Microsoft ni Google Play. No hay hallazgo; la fila de la tabla queda "no verificado". Recomendado: probarlo en el equipo real.
- Nova Launcher (estado en 2026), Niagara Launcher y Smart Launcher: sin fuente accesible; solo consta que Lawnchair 15 Beta 3 importa copias de Nova (H16).
- Pushbullet y Join: los repositorios consultados (pushbullet/api y joaomgcd/Join) dieron 404 y los sitios están bloqueados; estado, precio y vigencia sin verificar.
- Recoll, DocFetcher (estado real), la versión y licencia del propio Everything, y la documentación oficial de SQLite FTS5: sin fuente primaria accesible. La afirmación sobre FTS5 es de conocimiento general y de confianza baja.
- Microsoft Search (Microsoft 365): el repositorio de documentación esperado devolvió 404 y learn.microsoft.com está bloqueado. Los requisitos mínimos de Windows de PowerToys (documentados en learn.microsoft.com) tampoco se leyeron.
- Raycast: precio, plan gratuito y si la versión de Windows es beta o disponibilidad general; solo consta lo que dice el changelog de la API (H8).
- Tailscale: precio y límites del plan gratuito. Además hay dos versiones discrepantes (v1.102.5 en la página "latest" y v1.104.0 en el feed Atom del 2026-09-30); no se pudo reconciliar.
- Command Palette: si ya salió de preview (el README del módulo dice preview; la documentación de Microsoft leída no lo menciona) y si la compatibilidad con JavaScript/TypeScript salió en 0.102 (solo consta como plan en el README de PowerToys).
- Calidad de los datos de fecha: WebFetch devuelve resúmenes hechos por un modelo pequeño que en varias páginas inventó el año (por ejemplo 2024 para releases de Flow Launcher, Wox, PowerToys, Homepage y Umbrel, que los feeds Atom fechan en 2026). Por eso todas las fechas de versión citadas salen de feeds Atom con marca de tiempo ISO, de changelogs con fecha ISO o de campos ms.date. Excepciones con año no confirmado: PowerToys v0.101.2362.0 (25 de agosto), YunoHost debian/12.1.41.2 (3 de septiembre) y Lawnchair 1.2.0.1884 (23 de julio).
- Homarr: la fecha de archivo del repositorio original (3 de junio de 2026) sale de una sola lectura; la cifra de integraciones (80 o más frente a 100 o más) quedó discrepante.
- Syncthing Android: la fecha de archivado (3 de diciembre de 2024) sale de una sola lectura del repositorio.
- Mínimos de Android de Lawnchair, KDE Connect y la app Companion de Home Assistant; licencias de Lawnchair y Termux: no figuraban en las páginas leídas.
- Los costos de mantenimiento del cuadro de decisión y varias evaluaciones (por ejemplo descartar CasaOS, esperar a Homarr, preferir Glance) son opinión propia, marcada como tal, no datos de las fuentes. No se evaluó rendimiento real ni se instaló ninguna herramienta.
