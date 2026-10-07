# Diseño de un asistente determinista, no conversacional y no invasivo (WINT)

## Resumen

1. WINT debería ser un workflow (rutas de código predefinidas) y no un agente: es la distinción de Anthropic en "Building effective agents" (19-dic-2024), y encaja con variables predecibles y reglas explícitas.
2. La IA cabe solo en el borde de entrada (extraer y clasificar el contenido de las páginas de los comercios) con salida validada por esquema; después, toda la lógica (oferta real o falsa, Sol, Luna, avisos) es código y reglas, sin IA.
3. `claude -p --output-format json --json-schema` devuelve el resultado en `structured_output`, pero el CLI acepta `format` solo como anotación (no lo valida) y el esquema debe ser draft-07: hay que revalidar localmente (Pydantic o jsonschema).
4. El determinismo no se consigue con temperature=0: en Claude Opus 4.7 y posteriores `temperature`, `top_p` y `top_k` dan error 400 si se cambian. Se consigue con caché por huella de datos, prompt/esquema/modelo versionados y registro de decisiones.
5. Hay riesgo de calendario: según la tabla oficial, Haiku 4.5 figura "no antes del 15-oct-2026" y Sonnet 4.5 se retira el 30-nov-2026 (aviso mínimo de 60 días). Fijá y registrá el ID de modelo en cada decisión.
6. Avisos: Android y Windows documentan lo que la tecnología calma pide (pocos avisos, niveles de importancia, agrupar, no avisar de lo que no requiere acción, pedir permisos en contexto). Se proponen 4 niveles de urgencia, presupuesto diario, horas de silencio, "por qué te avisé" y posponer.
7. En Android el permiso POST_NOTIFICATIONS (Android 13+) viene apagado, existe cooldown (Android 15) y auto-agrupación (Android 16), y las alarmas inexactas pueden desviarse hasta una hora en Android 12+: Sol y Luna en Android no pueden prometer el minuto exacto sin un permiso especial.
8. Para reglas declarativas el modelo disparador-condición-acción de Home Assistant (YAML, modos single/queued, trazas) es la mejor plantilla. Para un desarrollador solitario conviene YAML + Pydantic + un evaluador de expresiones cerrado (rule-engine o CEL), no Node-RED, n8n ni Huginn.
9. Sol y Luna se modelan bien como statecharts con python-statemachine 3.2.1 (o transitions 0.9.3 si alcanza lo simple); astral calcula sol y también luna (salida, puesta, fase).
10. YAML tiene trampas verificadas con PyYAML: `NO` pasa a False, `7:30` pasa a 450 y `22:30` a 1350 (probado en este entorno): entrecomillá horas, usá `safe_load` y validá con esquema.
11. Reproducibilidad: registro de eventos append-only, idempotencia por clave, modo simulado sin red (pytest-socket, time-machine), reglas versionadas y bitácora de decisiones al estilo de los decision logs de OPA.
12. Privacidad: local primero; lo único que sale es lo que se manda a la API (prompts y salidas). Retención: 30 días en API/comercial; 5 años en cuentas de consumo con entrenamiento activado. Usá `--no-session-persistence` y `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC`.
13. Limitación de esta investigación: la búsqueda web se agotó antes de empezar y varios sitios (calmtech.com, learn.microsoft.com, home-assistant.io, docs.ntfy.sh, jsonlogic.com, cel.dev, Wikipedia, entre otros) estaban bloqueados por el proxy; ver "Qué no se pudo verificar".

## Hallazgos

### H1 — Tecnología calma: periferia y mínimo de atención (no verificado en vivo)
- Afirmación: Hecho (de memoria, sin abrir la fuente): Mark Weiser y John Seely Brown formularon la "calm technology" como tecnología que informa sin exigir atención y que se desplaza entre el centro y la periferia de la atención ("Designing Calm Technology", 1995; ampliado en "The Coming Age of Calm Technology", 1996). Amber Case sistematizó ocho principios (calmtech.com y su libro "Calm Technology: Principles and Patterns for Non-Intrusive Design", O'Reilly, c. 2015): (1) requerir la mínima atención posible; (2) informar y crear calma; (3) usar la periferia; (4) amplificar lo mejor de la tecnología y de la humanidad; (5) poder comunicar sin necesidad de hablar; (6) funcionar incluso cuando falla; (7) la cantidad correcta de tecnología es la mínima necesaria para resolver el problema; (8) respetar las normas sociales. Opinión: (5) y (6) se traducen en "WINT no conversa" y "falla a salvo"; (7) en "pocas reglas y listas cerradas de acciones". El ícono del Detector que se pone naranja mientras trabaja ya es un ejemplo de comunicación periférica.
- Fuentes: https://calmtech.com/ (NO abierta: bloqueada por el proxy de salida), https://www.ubiq.com/hypertext/weiser/calmtech/calmtech.htm (NO abierta: el dominio no resolvió; URL canónica conocida por entrenamiento). Tampoco abrieron en.wikipedia.org ni link.springer.com.
- Confianza: baja
- Riesgo: alto
- Vigencia: textos de 1995/1996 y c. 2015; no consultados en vivo el 7 de octubre de 2026

### H2 — Android: cuándo NO notificar y niveles de importancia (guía de diseño)
- Afirmación: Hecho: la guía de diseño de Android describe las notificaciones como información breve, oportuna y relevante cuando la app no está en uso. Lista usos que no corresponden: promoción cruzada; si el usuario nunca abrió la app; como método principal de comunicación; para "volver a la app" sin valor directo; pedir calificaciones; operaciones que no requieren intervención del usuario "como sincronizar"; anunciar estados de error de los que la app puede recuperarse sin intervención; saludos de feriados o cumpleaños. Define cuatro niveles: HIGH (suena y aparece en pantalla; información crítica en el tiempo: mensajes, alarmas, llamadas), DEFAULT (suena; "earliest convenience": alertas de tráfico, recordatorios de tareas), LOW (sin sonido), MIN (sin sonido ni interrupción visual; información no esencial). Cita textual: "Importance should be chosen with consideration for the user's time and attention. When an unimportant notification is disguised as urgent, it can produce unnecessary alarm." Para varias notificaciones del mismo tipo, una madre resume y las hijas deben entenderse solas. Implicación (opinión): los escaneos rutinarios del Detector, los reintentos y los errores recuperables nunca generan aviso; van a la bitácora y al panel.
- Fuentes: https://developer.android.com/design/ui/mobile/guides/home-screen/notifications
- Confianza: alta
- Riesgo: bajo
- Vigencia: consultado 7 de octubre de 2026

### H3 — Android: canales de notificación y control del usuario
- Afirmación: Hecho: desde Android 8.0 (API 26) toda notificación debe asignarse a un canal; si la app apunta a API 26 o superior y publica sin canal, la notificación no aparece y el sistema registra un error. Importancia por canal: IMPORTANCE_HIGH (urgente: suena y aparece como heads-up), IMPORTANCE_DEFAULT (suena), IMPORTANCE_LOW (sin sonido), IMPORTANCE_MIN (sin sonido y no aparece en la barra de estado), IMPORTANCE_NONE (nada). Cita: "After you create a notification channel, you can't change the notification behaviors. The user has complete control at that point." La app solo puede cambiar nombre y descripción; no puede cambiar importancia, sonido/vibración/luces ni el grupo. Existen grupos de canales (NotificationChannelGroup). Implicación (opinión): crear desde el primer día un canal por nivel de urgencia de WINT (urgente, importante, digest) y empezar conservador, porque no se puede "subir" la importancia por código después.
- Fuentes: https://developer.android.com/develop/ui/views/notifications/channels
- Confianza: alta
- Riesgo: alto
- Vigencia: consultado 7 de octubre de 2026

### H4 — Android: moderación del sistema (agrupar, cooldown, actualizar, expirar, acciones)
- Afirmación: Hecho: (a) desde Android 7.0 (API 24) se agrupa con `setGroup()`; el resumen es obligatorio (`setGroupSummary(true)`, ID constante); "If your app sends four or more notifications and doesn't specify a group, the system automatically groups them"; `setGroupAlertBehavior()` admite GROUP_ALERT_SUMMARY, _ALL y _CHILDREN. (b) Android 15 introduce "notification cooldown": "reduces the appearance, sound volume and vibration intensity for repetitive notifications for up to two minutes"; las notificaciones críticas están exentas y el usuario puede desactivarlo. (c) Android 16: las notificaciones se auto-agrupan "on the app's behalf" cuando no hay resumen. (d) Para actualizar, `notify()` con el mismo ID (si el usuario la descartó se crea una nueva); `setOnlyAlertOnce()` interrumpe solo la primera vez; `setTimeoutAfter()` hace que expire; hasta tres botones de acción, por ejemplo "to snooze a reminder". Implicación (opinión): el digest es una única notificación con ID fijo que se actualiza dentro de un grupo; dos de los tres botones se reservan para "Posponer" y "Silenciar regla".
- Fuentes: https://developer.android.com/develop/ui/views/notifications/group, https://developer.android.com/develop/ui/compose/notifications, https://developer.android.com/develop/ui/views/notifications/build-notification
- Confianza: alta
- Riesgo: alto
- Vigencia: consultado 7 de octubre de 2026

### H5 — Android: No molestar (DND) y categorías
- Afirmación: Hecho: Do Not Disturb existe desde Android 5.0 (API 21) con tres niveles: silencio total, solo alarmas, solo prioritarias (el usuario elige categorías: alarmas, recordatorios, eventos, llamadas, mensajes). Desde Android 8.0 el usuario puede anular DND canal por canal. `setCategory()` y `addPerson()` indican al sistema cómo tratar la notificación en DND. Implicación (opinión): WINT no debe pedir ni intentar saltarse DND; sus "horas de silencio" propias se suman a las del sistema, y no hay que declarar categorías de alarma o mensaje para colarse.
- Fuentes: https://developer.android.com/develop/ui/compose/notifications, https://developer.android.com/develop/ui/views/notifications/build-notification
- Confianza: alta
- Riesgo: alto
- Vigencia: consultado 7 de octubre de 2026

### H6 — Android 13+: permiso POST_NOTIFICATIONS y cómo pedirlo
- Afirmación: Hecho: desde Android 13 (API 33) enviar notificaciones requiere el permiso de ejecución `POST_NOTIFICATIONS`; en instalaciones nuevas está apagado por defecto. Si la app apunta a Android 13 o superior, decide cuándo mostrar el diálogo; la guía recomienda pedirlo en contexto (por ejemplo, tras tocar un botón de "alerta") y no al abrir la app. Descartar el diálogo deslizándolo no cambia el estado; hay que verificar `areNotificationsEnabled()` antes de enviar. Están exentas las notificaciones de sesión de medios y las de tipo llamada (ConnectionService); las de foreground service también necesitan el permiso. La página indicaba última actualización 2026-10-01 UTC. Implicación (opinión): el shell Android de WINT pide el permiso recién cuando la persona activa su primera regla con aviso.
- Fuentes: https://developer.android.com/develop/ui/views/notifications/notification-permission
- Confianza: alta
- Riesgo: alto
- Vigencia: página con última actualización 2026-10-01; consultado 7 de octubre de 2026

### H7 — Android: alarmas exactas e inexactas (consecuencias para Sol y Luna)
- Afirmación: Hecho: las alarmas inexactas respetan Doze y el ahorro de batería; en Android 12+ el sistema las invoca "within one hour of the supplied trigger time" salvo restricciones. Las exactas solo se justifican si la función central depende de la hora precisa (despertador, calendario). `SCHEDULE_EXACT_ALARM` lo concede el usuario y puede revocarse (usuario o sistema); no viene preconcedido en instalaciones nuevas que apuntan a Android 13+; tras un backup-and-restore a Android 14 queda denegado. `USE_EXACT_ALARM` se concede automáticamente, no es revocable y está limitado a casos de uso acotados y a una política de Google Play. Hay que consultar `canScheduleExactAlarms()` y reprogramar al cambiar el permiso (broadcast `ACTION_SCHEDULE_EXACT_ALARM_PERMISSION_STATE_CHANGED`). En Doze las alarmas se difieren; alternativa `setAndAllowWhileIdle()`. La guía recomienda inexactas más WorkManager o JobScheduler. Implicación (opinión): en Android, Sol y Luna deben declarar una ventana de tolerancia (por ejemplo, 07:30 con hasta 60 min de desvío) o pedir explícitamente `SCHEDULE_EXACT_ALARM`; no prometer el minuto exacto.
- Fuentes: https://developer.android.com/develop/background-work/services/alarms
- Confianza: alta
- Riesgo: alto
- Vigencia: consultado 7 de octubre de 2026

### H8 — Windows: notificaciones de app (toasts) y Focus
- Afirmación: Hecho (documentos fuente del repositorio MicrosoftDocs/windows-dev-docs, rama docs; learn.microsoft.com estaba bloqueado): la guía UX dice "Too many interruptions leads to users turning off this critical communication channel for your app", pide intención clara y que las notificaciones no sean ruidosas; en Windows 11 los Focus Sessions suprimen avisos y se pueden detectar con la API `FocusSessionManager`. Escenarios: Reminder (queda en pantalla hasta que se descarte), Alarm (como Reminder más audio en bucle), IncomingCall y Urgent (alta prioridad que "can break through Focus Assist", bajo control del usuario sobre qué apps pueden enviarlas). Fuentes en tensión: la página de contenido lista Urgent; la página de esquema lista solo Default, Reminder, Alarm e IncomingCall. Las notificaciones programadas tienen una ventana de entrega de 5 minutos: si el equipo está apagado más de 5 minutos se descartan, y Microsoft recomienda una tarea en segundo plano con disparador de tiempo para entrega garantizada. "Apps running with administrator privileges (elevated) cannot send or receive app notifications." Tipos de app cubiertos: WinUI, WPF, WinForms, consola, UWP. Implicación (opinión): el Detector de la bandeja no debe correr elevado; Sol y Luna no deben depender de toasts programados; el digest puede ir como notificación silenciosa directa al Centro de notificaciones.
- Fuentes: https://raw.githubusercontent.com/MicrosoftDocs/windows-dev-docs/docs/hub/apps/develop/notifications/app-notifications/app-notifications-ux-guidance.md, https://raw.githubusercontent.com/MicrosoftDocs/windows-dev-docs/docs/hub/apps/develop/notifications/app-notifications/app-notifications-content.md, https://raw.githubusercontent.com/MicrosoftDocs/windows-dev-docs/docs/hub/apps/develop/notifications/app-notifications/app-notifications-scheduled.md, https://raw.githubusercontent.com/MicrosoftDocs/windows-dev-docs/docs/hub/apps/develop/notifications/app-notifications/index.md, https://raw.githubusercontent.com/MicrosoftDocs/windows-dev-docs/docs/hub/apps/develop/notifications/app-notifications/app-notifications-schema.md
- Confianza: media
- Riesgo: alto
- Vigencia: consultado 7 de octubre de 2026 (fecha de las páginas no disponible)

### H9 — Anthropic: workflows frente a agentes; por qué WINT es un workflow
- Afirmación: Hecho: en "Building effective agents" (Anthropic, 19 de diciembre de 2024) se traza "an important architectural distinction between workflows and agents": workflows son "systems where LLMs and tools are orchestrated through predefined code paths"; agentes son "systems where LLMs dynamically direct their own processes and tool usage, maintaining control over how they accomplish tasks". Citas adicionales: "we recommend finding the simplest solution possible, and only increasing complexity when needed"; "Workflows offer predictability and consistency for well-defined tasks, whereas agents are the better option when flexibility and model-driven decision-making are needed at scale"; "The autonomous nature of agents means higher costs, and the potential for compounding errors. We recommend extensive testing in sandboxed environments, along with the appropriate guardrails." Implicación (opinión): WINT tiene variables predecibles y reglas explícitas, por lo que cae del lado workflow; un agente contradiría el requisito de "sin pensar ni evaluar". Ni siquiera hace falta un workflow con LLM en cada paso: el modelo aparece solo en un paso de extracción (ver H10 y H17).
- Fuentes: https://www.anthropic.com/engineering/building-effective-agents, https://www.anthropic.com/research/building-effective-agents
- Confianza: alta
- Riesgo: bajo
- Vigencia: publicado el 19 de diciembre de 2024; consultado 7 de octubre de 2026

### H10 — Patrones de workflow con LLM: cuáles sirven a WINT
- Afirmación: Hecho: el artículo enumera cinco patrones de workflow: prompt chaining, routing, parallelization, orchestrator-workers y evaluator-optimizer. "Prompt chaining decomposes a task into a sequence of steps, where each LLM call processes the output of the previous one." "Routing classifies an input and directs it to a specialized followup task." Sobre frameworks advierte que "often create extra layers of abstraction that can obscure the underlying prompts and responses, making them harder to debug" y que pueden tentar a "add complexity when a simpler setup would suffice". Implicación (opinión): para WINT sirven solo routing (clasificar un producto o una página y enviarlo a una rama de código fija) y, a lo sumo, chaining (extraer, validar por esquema, aplicar regla). Orchestrator-workers y evaluator-optimizer introducen decisiones dinámicas del modelo y se descartan; tampoco conviene un framework de agentes.
- Fuentes: https://www.anthropic.com/research/building-effective-agents
- Confianza: alta
- Riesgo: bajo
- Vigencia: consultado 7 de octubre de 2026

### H11 — Home Assistant: el modelo disparador-condición-acción como plantilla
- Afirmación: Hecho: la documentación de automatizaciones de Home Assistant define tres bloques: el trigger ("When the trigger part is verified, the automation starts"), la condición opcional ("If the condition is verified, the action part takes place") y la acción, que se ejecuta solo si se cumplen trigger y condiciones. Elementos reutilizables del vocabulario: trigger `sun` con `offset: "-00:45:00"` (antes o después del evento solar); `id` opcional por trigger; `trigger_variables`; condición `time` con `after`/`before` que "can span across the midnight threshold" (ejemplo 15:00 a 02:00) y `weekday`; condición `state` con `for` (solo estados fijos del estado principal, no atributos ni listas); `numeric_state` con `above`/`below` (ambos deben cumplirse); lógica `and` (por defecto), `or`, `not`. Home Assistant Core es Apache-2.0 y se presenta como "local control and privacy first"; la página de releases mostraba 2026.9.4 como estable (27-sep-2026) y 2026.10.0 en beta (b4, 7-oct-2026). Implicación (opinión): copiar el vocabulario (disparador, condición, acción, id de disparador, ventana que cruza medianoche, `for` como confirmación sostenida) para el YAML de WINT, sin instalar Home Assistant (está pensado para domótica).
- Fuentes: https://raw.githubusercontent.com/home-assistant/home-assistant.io/current/source/_docs/automation/basics.markdown, https://raw.githubusercontent.com/home-assistant/home-assistant.io/current/source/_docs/automation/trigger.markdown, https://raw.githubusercontent.com/home-assistant/home-assistant.io/current/source/_docs/scripts/conditions.markdown, https://github.com/home-assistant/core, https://github.com/home-assistant/core/releases
- Confianza: media
- Riesgo: alto
- Vigencia: consultado 7 de octubre de 2026; versiones: 2026.9.4 (27-sep-2026), 2026.10.0b4 (7-oct-2026)

### H12 — Home Assistant: modos de ejecución y trazas (concurrencia y auditoría)
- Afirmación: Hecho: los modos son `single` (por defecto: "Doesn't start a new run while the automation is running, and logs a warning"), `restart`, `queued` y `parallel`; `max` (por defecto 10, mínimo 2) aplica a queued y parallel; `max_exceeded` fija el nivel de log o `silent`. Para pruebas: "Every time an automation runs, Home Assistant records a step-by-step timeline of what was triggered, which conditions were checked, and what each action did", con "the last 5 traces of each automation"; el editor permite "Run action" sin disparador ni condiciones y las herramientas de desarrollador simulan estados y eventos. Implicación (opinión): WINT debe usar `modo: single` por defecto (evita avisos duplicados si una regla se re-ejecuta); su traza debe ser permanente (no solo 5) y tener una acción de "simular" que ejecute la regla sin efectos.
- Fuentes: https://raw.githubusercontent.com/home-assistant/home-assistant.io/current/source/_docs/automation/modes.markdown, https://raw.githubusercontent.com/home-assistant/home-assistant.io/current/source/_docs/automation/testing.markdown
- Confianza: alta
- Riesgo: bajo
- Vigencia: consultado 7 de octubre de 2026

### H13 — Plataformas de automatización existentes: Node-RED, n8n, Huginn, Easer, Tasker
- Afirmación: Hecho: Node-RED se define como "low-code programming for event-driven applications", licencia Apache-2.0, bajo la OpenJS Foundation; la página de releases mostraba la serie 5.0.x (5.0.7 "Maintenance Release"; el año de la fecha extraída, 2024, es inconsistente con una versión 5.0, así que la fecha no es fiable). n8n es "fair-code" bajo Sustainable Use License y n8n Enterprise License, con "1500+ integrations"; la licencia permite usar, copiar, distribuir y hacer derivados para "internal business purposes" y para uso "non-commercial or personal", y prohíbe venderlo u ofrecerlo como servicio alojado; la página de releases mostraba n8n@2.42.4 como último estable el 7-oct-2026. Huginn es MIT, "Agents create and consume events, propagating them along a directed graph", autoalojado y presentado como alternativa a IFTTT/Zapier; sus commits más recientes figuraban a comienzos de octubre (el año fue inferido). En Android, Easer (GPLv3+, disponible en F-Droid) usa un modelo de eventos, condiciones y operaciones; su autor avisó en 2020 que el ritmo de mantenimiento bajaría. Tasker no se pudo verificar (sitio bloqueado). Opinión: para un desarrollador solitario con Python y SQLite, sumar Node.js o Ruby agrega un segundo runtime y estado fuera de SQLite; sirven como referencia o como capa visual opcional. La licencia de n8n no es OSI: si WINT se vende o se ofrece como servicio, n8n queda excluido.
- Fuentes: https://github.com/node-red/node-red, https://github.com/node-red/node-red/releases, https://github.com/n8n-io/n8n, https://github.com/n8n-io/n8n/blob/master/LICENSE.md, https://github.com/n8n-io/n8n/releases, https://github.com/huginn/huginn, https://github.com/huginn/huginn/commits/master, https://github.com/renyuneyun/Easer
- Confianza: media
- Riesgo: alto
- Vigencia: consultado 7 de octubre de 2026

### H14 — Motores de reglas en Python y JSON: rule-engine, business-rules, durable_rules, JsonLogic, CEL
- Afirmación: Hecho: rule-engine es "a lightweight, optionally typed expression language with a custom grammar for matching arbitrary Python objects" (BSD-3-Clause, Python 3.10 o superior, versión 5.0.2 del 8-jul-2026); soporta tipado opcional, regex (`=~`), datetime nativo, tipos compuestos y es thread-safe; ejemplo: `first_name == "Luke" and email =~ ".*@rebels.org$"`. business-rules (MIT) define reglas como JSON de condiciones y acciones con variables y acciones como clases Python; última versión 1.1.1 del 18-mar-2022 y último commit ese mismo día. durable_rules (MIT) es un motor Rete de encadenamiento hacia adelante; la v2 eliminó la dependencia de Redis; PyPI muestra 2.0.28 del 7-jun-2020 y el último commit en GitHub figuraba en julio de 2025. JsonLogic ("Build complex rules, serialize them as JSON, and execute them in JavaScript") ejecuta reglas sin efectos secundarios ni ejecución de código; el repositorio JS tuvo su último commit el 9-jul-2024; los portes Python en PyPI están viejos (json-logic 0.6.3 del 4-dic-2015; json_logic_qubit 0.9.1 del 15-ago-2018). CEL (Common Expression Language) "evaluates in linear time, is mutation free, and not Turing-complete"; sus principios: sin acceso a memoria ajena, "a CEL program only computes an output from its inputs", "CEL programs cannot loop forever", tipado fuerte; cel-python 0.5.0 (31-ene-2026, Apache-2.0, Python 3.10 o superior). Opinión para un desarrollador solitario: YAML con esquema Pydantic y un evaluador de expresiones cerrado; empezar con rule-engine (Python puro, mantenido en 2026, tipado) y dejar CEL como estándar si más adelante el mismo reglamento debe correr en Kotlin o Go; evitar business-rules (abandonado) y durable_rules (inferencia Rete innecesaria para umbrales).
- Fuentes: https://github.com/zeroSteiner/rule-engine, https://pypi.org/project/rule-engine/, https://github.com/venmo/business-rules, https://pypi.org/pypi/business-rules/json, https://github.com/jruizgit/rules, https://pypi.org/pypi/durable-rules/json, https://github.com/jruizgit/rules/commits/master, https://github.com/jwadhams/json-logic-js, https://github.com/jwadhams/json-logic-js/commits/master, https://pypi.org/pypi/json-logic/json, https://pypi.org/pypi/json-logic-qubit/json, https://github.com/google/cel-spec, https://raw.githubusercontent.com/google/cel-spec/master/doc/langdef.md, https://pypi.org/pypi/cel-python/json
- Confianza: media
- Riesgo: alto
- Vigencia: consultado 7 de octubre de 2026; rule-engine 5.0.2 (8-jul-2026), cel-python 0.5.0 (31-ene-2026), business-rules 1.1.1 (18-mar-2022), durable-rules 2.0.28 (7-jun-2020)

### H15 — Máquinas de estado y statecharts: transitions, python-statemachine, XState
- Afirmación: Hecho: transitions (MIT) es "a lightweight, object-oriented state machine implementation in Python"; soporta estados jerárquicos, transiciones condicionales, callbacks, diagramas (Graphviz o Mermaid), AsyncMachine y LockedMachine; última versión 0.9.3 del 2-jul-2025 y commits recientes del 9-sep-2025. python-statemachine (MIT, Python 3.10 o superior) ofrece statecharts completos: estados compuestos, regiones paralelas, historia, guardas, soporte async, diagramas Mermaid y compatibilidad con SCXML; versiones 3.2.1 (1-ago-2026), 3.2.0 (17-jun-2026) y 3.1.2 (19-may-2026). XState (MIT, JS/TS) es gestión de estado basada en actores, máquinas de estado y statecharts (v5; la página de releases mostraba además una línea 6.0.0-alpha; el año de esas fechas no fue verificable). Opinión: Sol y Luna son statecharts pequeños (por ejemplo, despierto, activo, cerrando, dormido, con guardas como "escaneo en curso") y el estado debe persistirse en SQLite; elegir python-statemachine por statecharts y diagramas automáticos, o transitions si se prefiere una API más simple y estable.
- Fuentes: https://github.com/pytransitions/transitions, https://pypi.org/project/transitions/, https://github.com/pytransitions/transitions/commits/master, https://github.com/fgmacedo/python-statemachine, https://pypi.org/project/python-statemachine/, https://pypi.org/pypi/python-statemachine/json, https://github.com/statelyai/xstate, https://github.com/statelyai/xstate/releases
- Confianza: media
- Riesgo: alto
- Vigencia: consultado 7 de octubre de 2026; python-statemachine 3.2.1 (1-ago-2026), transitions 0.9.3 (2-jul-2025)

### H16 — Trampas de YAML para reglas (verificado con el código de PyYAML y una prueba local)
- Afirmación: Hecho verificado en el código de PyYAML (`lib/yaml/resolver.py`, rama main): el resolver booleano es `^(?:yes|Yes|YES|no|No|NO|true|True|TRUE|false|False|FALSE|on|On|ON|off|Off|OFF)$` y el entero incluye base 60: `[-+]?[1-9][0-9_]*(?::[0-5]?[0-9])+`. Prueba propia en este entorno (PyYAML 6.0.1, `yaml.safe_load`): `pais: NO` da `False`; `hora: 7:30` da `450` (int); `22:30` da `1350`; `07:30` da el texto '07:30'; `"07:30"` entrecomillado da texto; `[NO, SI]` da `[False, 'SI']`. `yaml.load` sin Loader "has been unsafe since the first release in May 2006" (puede ejecutar código arbitrario); la alternativa es `yaml.safe_load`. StrictYAML se presenta como "Refusing to parse the ugly, hard to read and insecure features of YAML": rechaza el tipado implícito (el "problema de Noruega"), el estilo flow, anclas y tags, y exige esquema. Implicación (opinión): WINT tiene catálogo de países (código NO = Noruega) y horas de rutina; entrecomillar siempre, usar `safe_load` y validar con Pydantic, o usar StrictYAML.
- Fuentes: https://raw.githubusercontent.com/yaml/pyyaml/main/lib/yaml/resolver.py, https://github.com/yaml/pyyaml/wiki/PyYAML-yaml.load(input)-Deprecation, https://raw.githubusercontent.com/crdoconnor/strictyaml/master/README.md
- Confianza: alta
- Riesgo: bajo
- Vigencia: consultado y probado el 7 de octubre de 2026 (PyYAML 6.0.1 en el entorno de prueba)

### H17 — `claude -p --json-schema`: qué garantiza y qué no (CLI y Agent SDK)
- Afirmación: Hecho: `-p`/`--print` ejecuta sin interacción; `--output-format json` devuelve resultado y metadatos (incluye `total_cost_usd` y desglose por modelo, estimaciones del cliente); `--json-schema` (solo modo print) devuelve JSON validado y la salida estructurada va en el campo `structured_output`. El SDK valida con JSON Schema draft-07 y "re-prompt[s] on mismatch"; si no valida dentro del límite el resultado es un error (`error_max_structured_output_retries`); un resultado con subtipo `success` pero sin `structured_output` debe tratarse como fallo. La palabra clave `format` (por ejemplo `"format": "email"`) se acepta "as an annotation" y no se valida. Banderas útiles para un uso scripteado y reproducible: `--bare` ("recommended mode for scripted and SDK calls"; omite hooks, skills, plugins, MCP, memoria automática y CLAUDE.md, y no usa el login de suscripción: requiere `ANTHROPIC_API_KEY`); `--tools ""` (desactiva todas las herramientas integradas); `--no-session-persistence` (no guarda sesiones en disco); `--max-turns`; `--max-budget-usd` (estimación del cliente); `--model` con alias o ID completo; `--fallback-model` activa un modelo alternativo cuando el principal está sobrecargado o retirado. Opinión: no usar `--fallback-model` en WINT (rompe la reproducibilidad) y registrar en cada decisión el modelo realmente usado. Combinación no probada aquí: `--tools ""` y `--max-turns` bajos con `--json-schema` (la salida estructurada podría requerir un turno extra).
- Fuentes: https://code.claude.com/docs/en/headless, https://code.claude.com/docs/en/cli-reference, https://code.claude.com/docs/en/agent-sdk/structured-outputs
- Confianza: alta
- Riesgo: alto
- Vigencia: documentación consultada el 7 de octubre de 2026 (menciona versiones de Claude Code hasta v2.1.290)

### H18 — API de Claude: salidas estructuradas por decodificación restringida y sus límites
- Afirmación: Hecho: la API ofrece JSON outputs (`output_config.format` con `type: json_schema`) y strict tool use (`strict: true`) con "constrained decoding": "Always valid ... Type safe ... Reliable: No retries needed for schema violations". Salvedades documentadas: si Claude se niega por seguridad (`stop_reason: "refusal"`, estado 200, se factura) "the output may not match your schema"; si se alcanza el límite de tokens la salida puede quedar incompleta. No se admiten: esquemas recursivos, `$ref` externos, restricciones numéricas (`minimum`, `maximum`, `multipleOf`), de strings (`minLength`, `maxLength`), `minItems` distinto de 0 o 1, ni `additionalProperties` distinto de `false`; los helpers de los SDK pueden mover esas restricciones a las descripciones y validarlas localmente. Latencia: la primera vez con un esquema compila la gramática; la caché dura 24 horas desde el último uso. Límites por petición: 20 herramientas estrictas, 24 parámetros opcionales, 16 parámetros con uniones; si se exceden da 400 ("Schema is too complex for compilation"). Modelos con soporte incluyen claude-sonnet-5-5, claude-opus-5-5 y claude-haiku-4-5-20251001. La guía de consistencia de Anthropic indica usar salidas estructurales en lugar de ingeniería de prompts cuando se necesita conformidad garantizada con un esquema. Implicación (opinión): validar siempre del lado de WINT (umbrales numéricos, longitudes, rangos) aunque la API garantice la forma.
- Fuentes: https://platform.claude.com/docs/en/build-with-claude/structured-outputs, https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/increase-consistency
- Confianza: alta
- Riesgo: alto
- Vigencia: consultado 7 de octubre de 2026 (se leyeron los primeros 100000 de 103014 caracteres de la página)

### H19 — Determinismo del modelo: sin temperature, y ciclo de vida de los modelos
- Afirmación: Hecho: la tabla de deprecaciones de parámetros indica que `temperature`, `top_p` y `top_k` están deprecados para Claude Opus 4.7 y posteriores: "Returns a 400 error when set to a non-default value on Claude 4.7 and later models"; la recomendación es omitirlos y guiar con prompts. Por lo tanto no se puede fijar `temperature=0` como mecanismo de reproducibilidad en los modelos nuevos. Ciclo de vida: Anthropic da "at least 60 days' notice before model retirement for publicly released models". Estado en la tabla oficial: claude-haiku-4-5-20251001 "Active", retiro tentativo "Not sooner than October 15, 2026"; claude-sonnet-4-5-20250929 "Deprecated" el 30-sep-2026 con retiro el 30-nov-2026 y reemplazo recomendado claude-sonnet-5-5; claude-sonnet-5-5 "Active" y no se retira antes del 28-sep-2027; claude-opus-4-1-20250805 ya se retiró el 5-ago-2026. "Not sooner than" no es una fecha de retiro anunciada. Implicación (opinión): la reproducibilidad se obtiene por (i) caché por huella de los datos de entrada, (ii) versiones de prompt, esquema y ID de modelo guardadas con cada decisión, (iii) validación local y (iv) reglas deterministas aguas abajo; y hay que revisar la tabla de deprecaciones cada cierto tiempo, con un modo "solo reglas" si el modelo fijado deja de existir.
- Fuentes: https://platform.claude.com/docs/en/about-claude/model-deprecations
- Confianza: alta
- Riesgo: alto
- Vigencia: tabla consultada el 7 de octubre de 2026

### H20 — Registro de eventos liviano, idempotencia y bitácora de decisiones
- Afirmación: Hecho: el patrón Event Sourcing de la guía de arquitectura de Microsoft reemplaza el estado mutable por un registro append-only; el estado se reconstruye ("rehydration") repitiendo los eventos; existen vistas materializadas y snapshots para no repetir todo; trae consideraciones de consistencia eventual y de versionado de eventos (tolerant deserialization, upcasting, migración); "Event handlers must be idempotent so processing a duplicate event doesn't change the outcome". Es útil cuando se necesita "capture intent, purpose, or reason in the data" y auditoría, y no lo es para CRUD simple. El borrador del IETF HTTPAPI "The Idempotency-Key HTTP Header Field" (en desarrollo, no es RFC) formaliza claves de idempotencia para que repetir una petición no duplique efectos. Los decision logs de Open Policy Agent registran por decisión: ID de decisión, input, result, revisión del bundle de políticas y timestamp, con enmascarado de campos sensibles. Opinión (diseño propio, sin fuente primaria para SQLite): en WINT, tabla `eventos` append-only (id, ts, tipo, payload, huella de la fuente) y tabla `decisiones` (decision_id, regla@versión, huella de entrada, resultado, modelo, versión de prompt); clave de idempotencia por regla y producto y día (como en los ejemplos YAML) con restricción UNIQUE para que reprocesar no duplique avisos.
- Fuentes: https://raw.githubusercontent.com/MicrosoftDocs/architecture-center/main/docs/patterns/event-sourcing.md, https://github.com/ietf-wg-httpapi/idempotency, https://raw.githubusercontent.com/open-policy-agent/opa/main/docs/docs/management-decision-logs.md
- Confianza: media
- Riesgo: bajo
- Vigencia: consultado 7 de octubre de 2026 (el borrador del IETF sigue activo; número de versión no visible)

### H21 — Pruebas de reglas y modo simulado sin red
- Afirmación: Hecho: pytest-socket es "A plugin to use with Pytest to disable or restrict `socket` calls during tests"; `--disable-socket` bloquea toda llamada de red incluida la resolución DNS (falla con `SocketBlockedError`), `--allow-hosts` admite una lista blanca (hosts, IP o CIDR), con marcadores `enable_socket` y `allow_hosts`; versión 0.8.1, MIT, Python 3.10 o superior (fecha de PyPI no confiable). time-machine ("Travel through time in your tests"; MIT) fija la hora con `@time_machine.travel(...)`; PyPI mostraba 3.5.1 del 8-sep-2026. Hypothesis (pruebas basadas en propiedades; MPL-2.0; el JSON de PyPI mostró 6.168.5, sin fecha confiable) y syrupy (snapshots para pytest; MIT; 6.1.1) completan el set. Home Assistant muestra el equivalente conceptual: ejecutar acciones sin disparador y simular eventos (H12). Opinión: casos fijos tipo tabla para oferta real, oferta falsa, Sol y Luna con reloj inyectado; propiedades como "bajar el precio nunca desclasifica una oferta real", "procesar dos veces el mismo evento produce un único aviso" y "mismas entradas, misma decisión"; reglas nuevas con `estado: simulada`; todo el pipeline corre con red bloqueada y con respuestas del modelo tomadas de la caché o de archivos fijos.
- Fuentes: https://github.com/miketheman/pytest-socket, https://pypi.org/pypi/pytest-socket/json, https://github.com/adamchainz/time-machine, https://pypi.org/project/time-machine/, https://pypi.org/pypi/hypothesis/json, https://pypi.org/pypi/syrupy/json
- Confianza: media
- Riesgo: alto
- Vigencia: consultado 7 de octubre de 2026; fechas de PyPI contradictorias entre el JSON y la página HTML en varios paquetes (ver "Qué no se pudo verificar")

### H22 — Privacidad: qué sale cuando WINT usa `claude -p`, retención y telemetría
- Afirmación: Hecho (documentación de Claude Code, "Data usage"): "Claude Code runs locally. To interact with the LLM, Claude Code sends data over the network. This data includes all user prompts and model outputs, encrypted in transit via TLS 1.2+." Retención: cuentas de consumo (Free, Pro, Max) 5 años si se permite el uso para mejorar modelos y 30 días si no; comerciales (Team, Enterprise, API) 30 días estándar y sin entrenamiento con código ni prompts salvo programas a los que la organización se suscriba; Zero Data Retention para cuentas elegibles. Localmente, los transcriptos de sesión se guardan en texto plano en `~/.claude/projects/` por 30 días por defecto (`cleanupPeriodDays`); `--no-session-persistence` evita guardarlos en modo print. Telemetría: métricas ("never include your code, prompts, or file paths") con `DISABLE_TELEMETRY=1`; reportes de errores con `DISABLE_ERROR_REPORTING=1` (activos solo con login Pro/Max, v2.1.198 o superior, conexión directa a la API y sin ZDR/HIPAA); `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC` apaga el tráfico no esencial (actualizaciones, telemetría, reportes, /feedback, encuestas). Detalle: en estas variables cualquier valor no vacío activa el comportamiento, incluso `0` o `false`. Opinión: WINT local primero: lo único que sale es el texto de la página que se manda al modelo (precios y descripciones públicas, nunca datos personales ni compras de la persona), documentado en un archivo de "qué sale de tu máquina"; el paso de IA debe ser opcional, con un modo "solo reglas".
- Fuentes: https://code.claude.com/docs/en/data-usage, https://code.claude.com/docs/en/env-vars, https://code.claude.com/docs/en/cli-reference
- Confianza: alta
- Riesgo: alto
- Vigencia: consultado 7 de octubre de 2026 (de la página de variables se leyeron 100000 de 165607 caracteres)

### H23 — Permisos mínimos: guía de Android
- Afirmación: Hecho: la guía de buenas prácticas de permisos de Android dice que "Permission requests protect sensitive information available from a device and should only be used when access to information is necessary for the functioning of your app", que hay que pedir el permiso solo cuando una función concreta lo requiere ("Don't overburden the user by requesting every permission at app startup"), que cada permiso extra "increases the probability that at least one of the requests will be denied", que conviene buscar alternativas que no requieran el permiso y explicar siempre por qué se pide. Implicación (opinión): el shell Android de WINT declara solo `POST_NOTIFICATIONS` y, si hace falta, un permiso de alarma exacta; nada de lectura de notificaciones de otras apps, contactos, ubicación ni accesibilidad; y la lista de acciones permitidas de cada regla (`no_hace` y acciones cerradas) funciona como equivalente de "permisos mínimos" a nivel de la propia aplicación.
- Fuentes: https://developer.android.com/training/permissions/usage-notes, https://developer.android.com/develop/ui/views/notifications/notification-permission
- Confianza: alta
- Riesgo: bajo
- Vigencia: consultado 7 de octubre de 2026

### H24 — Transportes de aviso: ntfy, Apprise y bibliotecas de toasts en Windows
- Afirmación: Hecho: ntfy es un sistema pub-sub HTTP ("send notifications to your phone or desktop via scripts from any computer, without having to sign up or pay any fees"), doble licencia Apache-2.0 y GPLv2, autoalojable, con apps Android (Google Play y F-Droid) e iOS; hay servicio público gratuito en ntfy.sh y planes pagos desde 5 USD por mes. Publicar es un PUT o POST HTTP; prioridades 1 a 5 (min, low, default, high, max) con comportamiento definido (1 sin sonido ni vibración y bajo "Other notifications"; 3 sonido por defecto; 4 y 5 vibración larga y pop-over); entrega diferida con `X-Delay` (mínimo 10 segundos, máximo 3 días); hasta tres acciones por notificación (view, broadcast, http, copy). Apprise (BSD-2-Clause, `pip install apprise`) envía a "almost all of the most popular notification services" (README: más de 200; la descripción de PyPI dice más de 300) e incluye notificaciones de escritorio para Windows, macOS y Linux; PyPI mostraba 2.0.1 (fecha en conflicto entre fuentes). En Windows desde Python: win11toast 0.36.3 (MIT, 17-ene-2026) y windows-toasts 1.3.1 (6-may-2025; licencia no declarada en los metadatos); BurntToast (módulo de PowerShell, MIT) aparece archivado y de solo lectura desde el 25-sep-2026. Implicación (opinión): ntfy autoalojado entrega el digest al celular sin construir una app Android propia y sin que los precios pasen por un tercero; con el servicio público, los mensajes pasan por un servidor ajeno.
- Fuentes: https://github.com/binwiederhier/ntfy, https://raw.githubusercontent.com/binwiederhier/ntfy/main/docs/publish.md, https://github.com/caronc/apprise, https://pypi.org/project/apprise/, https://pypi.org/pypi/win11toast/json, https://pypi.org/pypi/windows-toasts/json, https://github.com/Windos/BurntToast
- Confianza: media
- Riesgo: alto
- Vigencia: consultado 7 de octubre de 2026 (el documento de publicación de ntfy se leyó parcialmente: 100000 de 231744 caracteres)

### H25 — Sol y Luna con datos astronómicos y planificador: astral y APScheduler
- Afirmación: Hecho: astral calcula "Times for various positions of the sun: dawn, sunrise, solar noon, sunset, dusk" y también salida y puesta de la luna, azimut, cenit y fase lunar; versión 3.2 publicada el 5-nov-2022, licencia Apache-2.0, Python 3.7 a menos de 4.0 (estable pero sin lanzamientos recientes). APScheduler es un planificador en proceso "with Cron-like capabilities" (una vez, intervalo o cron; almacenes en memoria o SQL); la versión estable 3.11.3 es del 28-jun-2026 (MIT, Python 3.8 o superior) y la rama 4.x figuraba como pre-release (4.0.0a6 al 27-abr-2025). Home Assistant tiene el equivalente del trigger solar (`sun` con offset, H11). Implicación (opinión): el cambio de nombre a Sol y Luna admite una versión literal opcional: Sol arranca a una hora fija o a "amanecer más offset", y Luna a una hora fija o a "puesta de sol más offset"; las horas fijas son lo determinista por defecto, y la variante astronómica es una opción de la regla; para el calendario usar APScheduler 3.x o el Programador de tareas de Windows (este último fuera de esta investigación).
- Fuentes: https://pypi.org/project/astral/, https://pypi.org/project/APScheduler/
- Confianza: media
- Riesgo: alto
- Vigencia: consultado 7 de octubre de 2026; astral 3.2 (5-nov-2022), APScheduler 3.11.3 (28-jun-2026)

## Herramientas y software

| Nombre | Qué hace | Plataforma | Licencia o precio | Estado a octubre 2026 (última versión/fecha si se puede) | URL oficial | Encaje con WINT (alto/medio/bajo) | Salvedad |
|---|---|---|---|---|---|---|---|
| Home Assistant (automatizaciones) | Motor de automatizaciones declarativas: disparador, condición, acción en YAML; modos single/restart/queued/parallel; trazas | Python, servidor local | Apache-2.0 | 2026.9.4 estable (27-sep-2026); 2026.10.0 en beta (b4, 7-oct-2026) | https://github.com/home-assistant/core | medio | Pensado para domótica; copiar el modelo, no instalarlo. Sitio oficial home-assistant.io bloqueado en esta sesión |
| Node-RED | Programación visual basada en flujos para aplicaciones orientadas a eventos | Node.js | Apache-2.0 | Serie 5.0.x (5.0.7 "Maintenance Release"; fecha no fiable) | https://github.com/node-red/node-red | medio | Segundo runtime (Node.js); sitio nodered.org bloqueado |
| n8n | Automatización de flujos con IA e integraciones (1500+) | Node.js, autoalojado o nube | Sustainable Use License (fair-code, no OSI); Enterprise aparte | 2.42.4 último estable en la página de releases (7-oct-2026) | https://github.com/n8n-io/n8n | bajo | Prohíbe venderlo u ofrecerlo como servicio; uso personal o interno permitido |
| Huginn | Agentes que crean y consumen eventos en un grafo dirigido (alternativa a IFTTT/Zapier) | Ruby, autoalojado | MIT | Commits recientes (oct-2026, año inferido); sin versión verificada | https://github.com/huginn/huginn | bajo | Segundo runtime (Ruby); pensado para vigilancia web genérica |
| Tasker | Automatización en Android por perfiles, contextos y tareas | Android | De pago (precio no verificado) | No verificado | https://tasker.joaoapps.com/ (bloqueada) | medio | Información de memoria, no verificada en esta sesión |
| Easer | Automatización en Android con eventos, condiciones y operaciones | Android | GPLv3 o posterior (gratis) | Mantenimiento más lento desde 2020 según el autor; disponible en F-Droid | https://github.com/renyuneyun/Easer | bajo | Fecha de última versión no verificada |
| rule-engine | Lenguaje de expresiones tipado para evaluar reglas sobre objetos Python sin ejecutar código arbitrario | Python 3.10+ | BSD-3-Clause | 5.0.2 (8-jul-2026) | https://github.com/zeroSteiner/rule-engine | alto | Gramática propia, no es estándar interoperable |
| business-rules | Reglas como JSON de condiciones y acciones con variables y acciones en clases Python | Python | MIT | 1.1.1 (18-mar-2022); último commit el mismo día | https://github.com/venmo/business-rules | bajo | Sin mantenimiento aparente desde 2022 |
| durable_rules | Motor Rete de encadenamiento hacia adelante para coordinar eventos | Python, Node.js, Ruby | MIT | PyPI 2.0.28 (7-jun-2020); último commit en GitHub jul-2025 | https://github.com/jruizgit/rules | bajo | Inferencia innecesaria para umbrales; mantenimiento irregular |
| JsonLogic (json-logic-js y portes) | Reglas serializadas como JSON, sin efectos secundarios | JavaScript; portes a Python y otros | MIT (porte Python en PyPI) | JS: último commit 9-jul-2024; portes Python en PyPI de 2015 y 2018 | https://github.com/jwadhams/json-logic-js | medio | Portes Python viejos; jsonlogic.com bloqueado |
| CEL (Common Expression Language) y cel-python | Lenguaje de expresiones seguro, sin bucles ni mutación, tiempo lineal | Multi-lenguaje; cel-python en Python 3.10+ | Apache-2.0 | cel-python 0.5.0 (31-ene-2026) | https://github.com/google/cel-spec | medio | Más pesado que rule-engine; cel.dev bloqueado |
| transitions | Máquinas de estado en Python con jerarquías, callbacks y diagramas | Python | MIT | 0.9.3 (2-jul-2025) | https://github.com/pytransitions/transitions | medio | Sin statecharts completos |
| python-statemachine | Statecharts y FSM declarativos, sync y async, diagramas Mermaid | Python 3.10+ | MIT | 3.2.1 (1-ago-2026) | https://github.com/fgmacedo/python-statemachine | alto | Comunidad más chica que transitions (1.3k estrellas contra 6.6k en GitHub) |
| XState | Máquinas de estado, statecharts y actores | JavaScript/TypeScript | MIT | v5 vigente; línea 6.0.0-alpha en releases (fechas no verificadas) | https://github.com/statelyai/xstate | bajo | Solo si WINT se escribe en TypeScript |
| Pydantic | Validación de datos y generación de JSON Schema desde modelos Python | Python | MIT (no reconfirmado en esta sesión) | 2.13.5 (28-ago-2026) | https://pypi.org/project/pydantic/ | alto | Para el CLI de Claude generar el esquema compatible con draft-07 |
| jsonschema | Validación contra JSON Schema (drafts 3 a 2020-12) | Python 3.10+ | MIT | 4.26.0 (7-ene-2026) | https://pypi.org/project/jsonschema/ | medio | Validar `format` es opcional |
| PyYAML | Lectura de YAML (usar `safe_load`) | Python | No verificada en esta sesión | 6.0.1 en el entorno de prueba | https://github.com/yaml/pyyaml | alto | YAML 1.1: `NO`, `7:30` y similares cambian de tipo (H16) |
| StrictYAML | Subconjunto estricto de YAML con esquema y errores legibles | Python | Basada en ruamel.yaml (licencia no verificada) | Versión no verificada | https://github.com/crdoconnor/strictyaml | medio | No admite estilo flow, anclas ni tags |
| Claude Code CLI (`claude -p`) | Ejecución no interactiva con `--json-schema` y salida JSON | Windows, macOS, Linux | Comercial (términos de Anthropic) | Documentación cita versiones hasta v2.1.290 | https://code.claude.com/docs/en/headless | alto | Con `--bare` exige `ANTHROPIC_API_KEY`; los datos viajan a la API |
| Claude Agent SDK para Python | Biblioteca para integrar Claude Code con salidas estructuradas | Python 3.10+ | MIT | 0.2.164 (fecha en conflicto: 6-oct-2026 en HTML de PyPI, 13-feb-2026 en JSON) | https://pypi.org/project/claude-agent-sdk/ | medio | Para WINT basta el CLI o la API |
| Claude API con salidas estructuradas | JSON con esquema por decodificación restringida | API HTTP | De pago por uso | GA (Claude API, Bedrock, Google Cloud, Foundry) | https://platform.claude.com/docs/en/build-with-claude/structured-outputs | alto | No admite varias restricciones (min, max, longitudes); rechazos y límite de tokens rompen el esquema |
| ntfy | Notificaciones push por HTTP al celular y escritorio | Servidor Go; apps Android (Play, F-Droid) e iOS | Apache-2.0 y GPLv2; servicio público gratis, planes desde 5 USD por mes | Última versión no verificada | https://github.com/binwiederhier/ntfy | alto | Autoalojar para que los datos no pasen por un tercero; docs.ntfy.sh bloqueado |
| Apprise | Biblioteca y CLI para enviar a 200+ servicios, incluidas notificaciones de escritorio | Python 3.9+ | BSD-2-Clause | 2.0.1 (3-oct-2026 en HTML de PyPI; conflicto con el JSON) | https://github.com/caronc/apprise | medio | Cantidad de servicios en conflicto entre README y PyPI |
| Notificaciones de app de Windows (Windows App SDK) | API de toasts: escenarios, programadas, Focus Session | Windows 10 y 11; WinUI, WPF, WinForms, consola, UWP | Parte de Windows App SDK | Documentación en el repo MicrosoftDocs/windows-dev-docs | https://github.com/MicrosoftDocs/windows-dev-docs/tree/docs/hub/apps/develop/notifications/app-notifications | medio | Apps elevadas no pueden enviar ni recibir; programadas se pierden tras 5 min |
| win11toast | Toasts de Windows 10 y 11 desde Python | Windows, Python | MIT | 0.36.3 (17-ene-2026) | https://pypi.org/project/win11toast/ | alto | Fecha de PyPI no contrastada |
| windows-toasts | Toasts de Windows desde Python | Windows, Python 3.9+ | No declarada en los metadatos | 1.3.1 (6-may-2025) | https://pypi.org/project/windows-toasts/ | medio | Licencia a confirmar |
| BurntToast | Toasts desde PowerShell | Windows 10 y Server 2019+ | MIT | Repositorio archivado el 25-sep-2026 (solo lectura) | https://github.com/Windos/BurntToast | bajo | Sin mantenimiento |
| APIs de notificaciones de Android (NotificationChannel, NotificationCompat, AlarmManager, WorkManager) | Canales, grupos, DND, alarmas exactas e inexactas, trabajo en segundo plano | Android 8.0+ (varias funciones 12 a 16) | Parte del SDK de Android | Documentación actualizada hasta 2026-10-01 | https://developer.android.com/develop/ui/views/notifications/channels | alto | Muchas restricciones dependen de la versión de Android y del `targetSdk` |
| astral | Hora de amanecer, atardecer, salida y puesta de luna y fase lunar | Python 3.7+ | Apache-2.0 | 3.2 (5-nov-2022) | https://pypi.org/project/astral/ | medio | Sin lanzamientos recientes |
| APScheduler | Planificador en proceso (cron, intervalo, una vez) con almacenes SQL | Python 3.8+ | MIT | 3.11.3 estable (28-jun-2026); 4.x en pre-release | https://pypi.org/project/APScheduler/ | medio | El proceso debe estar corriendo; no reemplaza al Programador de tareas |
| pytest-socket | Bloquea red en pruebas | Python 3.10+, pytest | MIT | 0.8.1 (fecha no confiable) | https://github.com/miketheman/pytest-socket | alto | Pensado para pytest |
| time-machine | Fija el reloj en pruebas | Python 3.10+ | MIT | 3.5.1 (8-sep-2026 en HTML de PyPI) | https://github.com/adamchainz/time-machine | alto | Fechas de PyPI discordantes entre fuentes |
| Hypothesis | Pruebas basadas en propiedades | Python 3.10+ | MPL-2.0 | 6.168.5 (fecha no verificada) | https://github.com/HypothesisWorks/hypothesis | medio | Útil para propiedades de las reglas |
| syrupy | Pruebas de snapshot para pytest | Python 3.10+ | MIT | 6.1.1 (fecha no verificada) | https://pypi.org/project/syrupy/ | medio | Los snapshots deben revisarse a mano |
| Open Policy Agent (decision logs) | Motor de políticas con bitácora de decisiones (ID, input, result, revisión, timestamp) | Go; servidor o biblioteca | Licencia no verificada | No verificado | https://github.com/open-policy-agent/opa | bajo | Sobredimensionado; sirve como modelo de la bitácora |

## Esquema para cuadro sinóptico

- WINT: asistente determinista
  - Calma y avisos
    - Silencio por defecto
    - Digest y presupuesto diario
    - Cuatro niveles de urgencia
    - Por qué, posponer, silenciar
  - Workflow, no agente
    - Rutas de código predefinidas
    - Sin conversar ni preguntar
    - El modelo nunca decide
  - Reglas declarativas
    - YAML validado por esquema
    - Expresiones cerradas
    - Sol y Luna como statecharts
  - IA en el borde
    - Extraer y clasificar
    - Esquema más validación local
    - Caché por huella
    - Prompt y modelo versionados
  - Reproducibilidad y auditoría
    - Registro de eventos
    - Idempotencia por clave
    - Modo simulado sin red
    - Reglas versionadas
  - Privacidad y control
    - Local primero
    - Sin telemetría
    - Permisos mínimos
    - Lista blanca de acciones

## Recomendaciones para WINT

1. Fijá la arquitectura como workflow de etapas fijas: ingesta (el Detector) -> extracción (IA opcional) -> validación por esquema -> reglas -> acciones y avisos. Por qué: es la definición de workflow de Anthropic (H9) y deja el comportamiento predecible; el modelo nunca decide qué hacer a continuación.
2. Definí las reglas como datos YAML con vocabulario copiado de Home Assistant (disparador, condiciones `todas`/`cualquiera`, acciones, `modo: single`, `id`, ventanas que cruzan medianoche, `for` como confirmación sostenida) y validalas con Pydantic al cargar. Por qué: el modelo está probado y es legible (H11, H12).
3. Para un desarrollador solitario, la combinación recomendada es: Python + SQLite + YAML con `safe_load` + Pydantic + rule-engine para expresiones + python-statemachine para Sol y Luna + APScheduler 3.x para el reloj. Dejá CEL como estándar de reserva si las reglas deben correr algún día en Kotlin o Go. Evitá Node-RED, n8n y Huginn salvo como capa visual opcional (segundo runtime, estado fuera de SQLite; n8n con licencia no OSI), y evitá business-rules y durable_rules (H13, H14, H15).
4. Entrecomillá todas las horas y códigos en YAML ("07:30", "NO"), usá siempre `safe_load` y rechazá archivos que no validen el esquema. Por qué: verificado que `7:30` pasa a 450 y `NO` a False (H16).
5. Limitá la IA a un único paso de extracción y clasificación. Invocación de referencia (combinación de banderas no probada en conjunto, ver H17): `claude --bare -p --model <ID_FIJO> --tools "" --no-session-persistence --output-format json --json-schema "$(cat esquema_producto.json)" --max-budget-usd 0.05 "<instrucción v12> <texto de la página>"`. Después validá localmente (rangos, longitudes, precio mayor que cero), porque `format` no se valida y los límites numéricos no se aplican por decodificación (H17, H18). Cualquier resultado sin `structured_output` o fuera de rango va a una cola de "revisar" en el panel; no genera pregunta ni aviso inmediato.
6. Guardá la reproducibilidad en datos: caché con clave sha256 de (ID de modelo + versión de prompt + versión de esquema + entrada normalizada) y bitácora por decisión con modelo realmente usado, versión de prompt, huella de entrada, resultado y regla@versión. No uses temperature como mecanismo (da 400 en los modelos nuevos) ni `--fallback-model` (H19, H17).
7. Revisá el calendario de modelos: Haiku 4.5 puede retirarse a partir del 15-oct-2026 y Sonnet 4.5 se retira el 30-nov-2026 (H19). Mantené un modo "solo reglas" que siga funcionando con la última caché si el modelo fijado desaparece.
8. Usá registro de eventos append-only y claves de idempotencia por regla, producto y día (o semana) con restricción UNIQUE en SQLite, para que reprocesar un día no duplique avisos (H20). Verificá la técnica exacta de SQLite en su documentación, que no se pudo abrir aquí.
9. Toda regla nueva nace con `estado: simulada` y pasa a `activa` por decisión de la persona editando el archivo; el pipeline completo debe correr en pruebas con red bloqueada (pytest-socket), reloj inyectado (time-machine) y casos fijos tabulados, más propiedades con Hypothesis (H21).
10. Implementá la política de avisos de abajo: cuatro niveles, presupuesto diario, horas de silencio, digest en Sol y Luna, "por qué" en cada aviso, y posponer y silenciar como botones. Por qué: coincide con las guías de Android y Windows (H2 a H8) y con la tecnología calma (H1).
11. Android: un canal por nivel desde el inicio (no se puede subir la importancia por código), permiso POST_NOTIFICATIONS pedido recién al activar la primera regla con aviso, un único ID de digest actualizado dentro de un grupo, y Sol y Luna con ventana de tolerancia en lugar de alarma exacta, salvo que la persona otorgue `SCHEDULE_EXACT_ALARM` (H3 a H7).
12. Windows: que el Detector no corra elevado; digest como notificación silenciosa; no depender de toasts programados (ventana de 5 minutos); detectar Focus Session con `FocusSessionManager` y bajar un nivel mientras dure (H8). Para Python elegí win11toast; BurntToast quedó archivado (H24).
13. Transporte hacia el celular: ntfy autoalojado (o Apprise si se quiere más de un destino) en vez de construir primero una app Android propia; si usás el servidor público ntfy.sh, tené presente que el mensaje pasa por un tercero (H24).
14. Privacidad: documentá en un archivo "qué sale de tu máquina" (solo el texto enviado al modelo); definí `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC`, `DISABLE_TELEMETRY` y `DISABLE_ERROR_REPORTING` (cualquier valor no vacío los activa); usá `--no-session-persistence`; evitá mandar datos personales; sabé que en cuentas de consumo la retención puede ser de 5 años si el entrenamiento está permitido (H22, H23).
15. Gobernanza de acciones sin preguntar: cada regla declara una lista cerrada de acciones y un campo `no_hace`; las acciones del sistema (suspender, apagar, cerrar programas) requieren habilitación expresa en el archivo y nunca se piden por diálogo. Si algo falla, la regla no actúa y lo registra (fallar a salvo, H1).
16. Nombre: Sol y Luna funcionan como rutinas de arranque y cierre; opcionalmente anclables a amanecer y atardecer con astral, que además calcula la luna (H25).

### Decálogo de principios de diseño de WINT

1. Workflow, no agente: el código decide; el modelo nunca elige acciones ni herramientas.
2. Reglas explícitas en datos: YAML validado por esquema y versionado; cada decisión cita regla@versión.
3. Silencio por defecto: nada avisa si la persona no lo habilitó; hay horas de silencio, presupuesto diario y digest.
4. Cero conversación: WINT no pregunta, no sugiere, no evalúa a la persona; se configura abriendo un archivo o un panel (modelo "pull", nunca "push").
5. IA solo en el borde: extraer y clasificar con salida validada por esquema; después, lógica 100 % determinista.
6. Misma entrada, misma salida: reloj inyectado, sin aleatoriedad, caché por huella, modelo y prompt fijados y registrados.
7. Todo es un evento: bitácora append-only, claves de idempotencia, decisiones reproducibles, también sin red.
8. Explicable: cada aviso dice por qué (regla, valores y umbral) y cómo silenciarlo, posponerlo o deshacer.
9. Local primero y permisos mínimos: sin telemetría propia; lo único que sale es lo documentado y habilitado.
10. Fallar a salvo: ante la duda no actúa, registra y espera; las reglas nuevas nacen simuladas; solo existen las acciones de la lista blanca.

### Política de notificaciones (tabla)

Niveles propuestos (diseño propio, sin fuente primaria; el mapeo de importancia sale de las guías de Android y Windows citadas en H2, H3 y H8): N0 Registro (sin aviso, solo bitácora y panel), N1 Digest (agrupado, sin sonido), N2 Importante (aviso individual con sonido), N3 Urgente (rompe el silencio, solo alertas definidas por la persona). Valores por defecto editables. Ningún aviso se descarta en silencio: lo que supera el presupuesto baja de nivel y entra al próximo digest con la etiqueta "retenido".

| Tipo de aviso | Nivel | Cuándo | Cuánto (tope por defecto) | Cómo |
|---|---|---|---|---|
| Oferta real confirmada en producto seguido, 30 % o más bajo la mediana de 30 días y 2 lecturas seguidas | N2 | Inmediato, fuera de horas de silencio | N2 total: 3 por día; 1 por producto cada 24 h | Android: canal importante (IMPORTANCE_DEFAULT); Windows: toast normal; botones Posponer 1 día y Silenciar regla; texto con regla, valores y umbral |
| Oferta real entre 15 % y 30 % bajo la mediana | N1 | En el próximo digest (Sol por la mañana) | Hasta 10 ítems por digest | Android: canal digest (IMPORTANCE_LOW), una sola notificación con ID fijo; Windows: toast silencioso al Centro de notificaciones |
| Alerta de precio objetivo definido por la persona | N3 | Inmediato; rompe el silencio solo si la persona lo habilitó en esa alerta | 2 por día; 1 por producto cada 24 h | Android: canal urgente (IMPORTANCE_HIGH); Windows: toast con escenario urgent o reminder según permisos; ntfy prioridad 4 o 5 si se usa |
| Comparación con la competencia (otro comercio más barato) | N1 | Digest diario | Hasta 5 ítems por digest | Dentro del digest, con la tabla de precios por comercio |
| Oferta falsa o sospechosa (descuento anunciado sin respaldo en el historial) | N0 y resumen | Registro inmediato con la evidencia; resumen semanal en Luna | 1 resumen por semana | Panel y digest semanal sin sonido; nunca aviso individual |
| Resumen Sol (arranque del día) | N1 | A la hora configurada o en el primer inicio de sesión del día; en Android con ventana de tolerancia | 1 por día | Canal digest; incluye avisos retenidos por presupuesto |
| Resumen Luna (cierre del día) | N1 | Al cierre configurado; dentro de las horas de silencio queda para Sol | 1 por día | Silencioso; sin sonido ni heads-up |
| Fallo del Detector (sitio cambió, sin datos) | N1 | Reintentos silenciosos; entra al digest; escala a N2 solo si falla más de 48 h en un producto seguido | 1 por incidente | Ícono de la bandeja con color distinto al naranja de "trabajando" (propuesta); sin toast |
| Recordatorio posponido por la persona | N2 | A la hora que ella eligió | 1 por posposición | Canal importante |
| Cambios de configuración y de reglas | N0 | Siempre al registrarse | Sin tope | Solo bitácora, con versión y fecha |
| Presupuesto agotado o aviso retenido | N1 | En el próximo digest | 1 línea por digest ("N avisos retenidos") | Dentro del digest; nunca un aviso aparte |

Parámetros globales propuestos: horas de silencio 23:30 a 07:30 (editable; se suman a No molestar del sistema y nunca lo contradicen); digest de 2 a 3 por día (Sol, opcional mediodía, Luna); explicación en cada aviso: "por qué te avisé" con regla@versión, valores observados y umbral; posponer 1 día o 1 semana; silenciar la regla; deshacer del silenciado en el panel. El sistema no ajusta umbrales por sí mismo: solo la persona los cambia (determinismo).

### Cuatro reglas de ejemplo en YAML

Esquema ilustrativo propio de WINT (no pertenece a ninguna biblioteca); las expresiones entre comillas serían evaluadas por un evaluador cerrado (por ejemplo rule-engine). Probado: los cuatro documentos cargan con `yaml.safe_load` (PyYAML 6.0.1) y las horas quedan como texto porque están entrecomilladas.

```yaml
---
# Regla 1: oferta real
regla: oferta_real
version: 3
estado: activa            # activa | simulada | pausada
modo: single              # una ejecución por producto a la vez
disparador:
  evento: precio.observado
condiciones:
  todas:
    - { dato: producto.en_seguimiento, es: true }
    - { dato: historial.dias, minimo: 14 }
    - { dato: precio.actual, menor_o_igual_que: "0.85 * historial.mediana_30d" }
    - { dato: precio.lecturas_consecutivas_bajas, minimo: 2 }
    - { dato: precio.actual, menor_o_igual_que: competencia.minimo }
    - { dato: aviso.ultimo_para_producto_horas, minimo: 24 }
acciones:
  - si: { dato: precio.actual, menor_o_igual_que: "0.70 * historial.mediana_30d" }
    entonces: { avisar: { nivel: importante, canal: telefono_y_pc } }
    si_no:    { avisar: { nivel: digest, ventana: matutina } }
  - registrar: { evento: oferta.confirmada, guardar: [precio.actual, historial.mediana_30d, competencia.minimo] }
explicacion: "{producto.nombre}: {precio.actual} es {pct_bajo_mediana}% menor que la mediana de 30 días ({historial.mediana_30d}); regla {regla}@v{version}"
clave_idempotencia: "{regla}:{producto.id}:{fecha_local}"
---
# Regla 2: oferta falsa
regla: oferta_falsa
version: 2
estado: activa
modo: single
disparador:
  evento: precio.observado
condiciones:
  todas:
    - { dato: oferta.descuento_anunciado_pct, minimo: 20 }
    - { dato: historial.dias, minimo: 30 }
    - { dato: precio.actual, mayor_o_igual_que: "0.95 * historial.mediana_30d" }
    - { dato: oferta.precio_lista_anunciado, mayor_que: "1.10 * historial.maximo_30d" }
acciones:
  - registrar: { evento: oferta.sospechosa, guardar: [oferta.precio_lista_anunciado, historial.maximo_30d, historial.mediana_30d, precio.actual, captura_html_hash] }
  - avisar: { nivel: registro, incluir_en: resumen_semanal }
explicacion: "Anuncia {oferta.descuento_anunciado_pct}% de descuento sobre {oferta.precio_lista_anunciado}, pero en 30 días el máximo observado fue {historial.maximo_30d} y la mediana {historial.mediana_30d}; regla {regla}@v{version}"
clave_idempotencia: "{regla}:{producto.id}:{semana_iso}"
---
# Regla 3: Sol (arranque del día)
regla: sol_arranque
version: 1
estado: activa
modo: single
disparador:
  cualquiera:
    - { hora: "07:30", dias: [lun, mar, mie, jue, vie] }
    - { evento: sesion.iniciada, primera_del_dia: true }
condiciones:
  todas:
    - { dato: sol.ejecutada_hoy, es: false }
acciones:                      # lista cerrada y ordenada; nada fuera de ella
  - detector: reanudar
  - silencio: terminar
  - digest: { tipo: matutino, incluir: [ofertas_reales, bajas_competencia, fallos_detector], maximo_items: 10 }
  - registrar: { evento: sol.completada }
no_hace: [abrir_ventanas, hacer_preguntas, instalar_nada]
clave_idempotencia: "sol:{fecha_local}"
---
# Regla 4: Luna (cierre del día)
regla: luna_cierre
version: 1
estado: simulada               # se prueba sin ejecutar acciones reales
modo: single
disparador:
  cualquiera:
    - { hora: "23:30" }
    - { evento: luna.pedida_por_usuario }
condiciones:
  todas:
    - { dato: detector.escaneo_en_curso, es: false, esperar_maximo_min: 10 }
acciones:
  - detector: pausar
  - base_datos: { checkpoint: true, copia_local: { conservar: 7 } }
  - digest: { tipo: cierre, incluir: [resumen_dia], maximo_items: 5 }
  - silencio: { iniciar: "23:30", terminar: "07:30" }
  - sistema: { accion: suspender, requiere_habilitacion_expresa: true }
no_hace: [apagar_sin_orden, cerrar_programas_ajenos, hacer_preguntas]
clave_idempotencia: "luna:{fecha_local}"
```

Notas de diseño de los ejemplos (opinión): la regla 1 usa mediana de 30 días, historial mínimo de 14 días y dos lecturas seguidas para evitar falsos positivos por errores de lectura; la regla 2 compara contra el máximo y la mediana observados (si el "precio de lista" anunciado supera en más de 10 % al máximo real de 30 días y el precio actual no es menor que el 95 % de la mediana, se registra evidencia sin avisar); Sol y Luna son listas cerradas; en Luna la acción de sistema requiere habilitación expresa y no se pregunta nada. Las opciones de energía de Windows más allá de las tres del menú de inicio quedan fuera de este frente.

## Qué no se pudo verificar

- Búsqueda web: el cupo de WebSearch estaba agotado desde el primer intento, así que no se hizo descubrimiento por buscador; todas las URL de este documento salen de lecturas directas con WebFetch.
- Tecnología calma (H1): calmtech.com bloqueado por el proxy de salida; www.ubiq.com no resolvió; en.wikipedia.org, es.wikipedia.org y link.springer.com bloqueados. Los años (1995, 1996), los ocho principios de Amber Case y el año del libro (c. 2015) están escritos de memoria y con confianza baja.
- Estudio sobre agrupar notificaciones (Fitz et al., 2019, "Batching smartphone notifications can improve well-being", Computers in Human Behavior): doi.org bloqueado; no se abrió. De memoria: agrupar notificaciones en lotes de tres por día mejoró el bienestar; no se citan cifras. No se encontró en esta sesión una fuente primaria para el presupuesto diario ni las horas de silencio propias (son diseño propio).
- Dominios bloqueados por el proxy: www.home-assistant.io (se usó el repositorio de documentación en GitHub), nodered.org, docs.n8n.io, learn.microsoft.com (se usó el repositorio MicrosoftDocs en GitHub), tasker.joaoapps.com, jsonlogic.com, cel.dev, docs.ntfy.sh, www.inkandswitch.com (local-first), martinfowler.com, docs.stripe.com, datatracker.ietf.org, www.sqlite.org, arxiv.org, www.w3.org, www.johnseelybrown.com y python-statemachine.readthedocs.io. api.github.com devolvió 403.
- Apple Human Interface Guidelines (niveles de interrupción): la página no entregó contenido útil; no se usa en este informe.
- Tasker: precio, versión y funciones no verificados (sitio bloqueado); la fila de la tabla es de memoria. Easer: fecha de la última versión no verificada.
- Node-RED: la fecha mostrada para 5.0.7 (8 de septiembre, año extraído 2024) es inconsistente con una versión 5.0; tomar como no fiable. XState: el año de las fechas de la línea 6.0.0-alpha no fue verificable. Huginn: el año de los commits de octubre fue inferido.
- Fechas de PyPI en conflicto entre el JSON y la página HTML en varios paquetes (claude-agent-sdk: 13-feb-2026 contra 6-oct-2026; Apprise: 19-dic-2024 contra 3-oct-2026; time-machine: ene-2025 contra 8-sep-2026); en los listados se prefirió la página HTML y se marcó el conflicto. Hypothesis, syrupy, pytest-socket y jsonschema (en JSON) no dieron fecha confiable. Licencias de Pydantic y PyYAML no reconfirmadas; la de StrictYAML y la de OPA no verificadas.
- Apprise: cantidad de servicios en conflicto (más de 200 en el README; más de 300 en la descripción de PyPI).
- Windows: la página de esquema y la de contenido se contradicen sobre el escenario Urgent (H8); no se leyó la documentación de Task Scheduler ni de opciones de energía (fuera de este frente); el texto "Focus Assist" frente a "Focus Sessions" no se contrastó en Windows 11 versión por versión.
- Android: no se verificó la función de posponer notificaciones del sistema (solo la API de acciones y de timeout), ni los detalles de Android 16 más allá de la auto-agrupación; no se leyó la referencia completa de `AutomaticZenRule` (la página se truncó).
- SQLite: la técnica de idempotencia con UNIQUE y UPSERT, WAL y checkpoints no se contrastó con su documentación oficial (www.sqlite.org bloqueado); el semántico de Idempotency-Key de Stripe tampoco.
- `claude -p` en conjunto: no se ejecutó el CLI aquí; la combinación `--bare --tools "" --max-turns` con `--json-schema` no está probada, ni cómo interactúa `--fallback-model` con el resultado estructurado más allá de lo que dice la documentación.
- Todas las lecturas pasaron por un modelo resumidor intermedio (WebFetch): las citas textuales provienen de ese resumen y pueden estar parafraseadas; las páginas largas se leyeron solo en parte cuando la herramienta lo indicó (structured-outputs: 100000 de 103014 caracteres; env-vars: 100000 de 165607; ntfy publish.md: 100000 de 231744).
- Ley argentina de protección de datos personales (Ley 25.326) y su aplicación a un uso personal: no investigada; no se espera que aplique a un uso local con datos públicos de precios, pero no está verificado.
