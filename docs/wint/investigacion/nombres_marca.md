# Nombres: WINT, Osi, Sol/Luna y Sun/Moon — colisiones, registro y diseño

## Resumen

Consulta hecha el 7 de octubre de 2026. Limitación importante: el presupuesto de búsquedas web de la sesión se agotó antes de empezar y la red bloquea wikipedia, opensource.org, wipo.int, inpi.gob.ar, argentina.gob.ar, amazon.com, pokemon.com, solana.com, wint.ai y otros. Por eso la evidencia sale de registros de paquetes (JSON oficiales), GitHub, consultas DNS y documentación de Android/Apple. Marcas e INPI quedan SIN verificar.
- WINT ya existe como nombre de empresa: Wint (wint.ai), plataforma de IA para gestión de agua y detección de fugas en edificios comerciales e industriales, con app móvil "Wint Pulse". El dominio wint.ai está delegado y existe una organización GitHub `wint-ai` (Israel, según su perfil).
- Un día antes de esta consulta (6/10/2026) apareció en crates.io un crate `wint` ("motor determinista y explicable que encuentra las ventanas de tiempo en que un trabajo puede correr"), de la organización `aunai-org`. Es conceptualmente cercano a una rutina Sol/Luna. No hay evidencia de que sea de la persona que encarga el informe.
- En PyPI `wint` ya está tomado (inyección de dependencias, último release en 2018); en npm `wint` es un paquete vacío de 2017. Libres hoy: `wint-sol`, `wint-luna`, `wint-osi`, `wint-app`, `wint-platform` en PyPI y npm; `wint` en RubyGems y NuGet; `wint-app` y `getwint` en GitHub.
- Osi/OSI: Open Source Initiative (guardiana de la Open Source Definition) y el modelo OSI de redes (7 capas) dominan cualquier búsqueda. `osi` está libre en PyPI, RubyGems y NuGet, pero ocupado en npm, crates.io y GitHub.
- Sol/Luna/Sun/Moon: los cuatro nombres desnudos están ocupados en PyPI, npm, GitHub (usuario u organización), RubyGems/NuGet (sol, luna) y como dominios .com. Con prefijo `wint-` están libres.
- Hallazgo nuevo de 2026: el repositorio oficial openai/codex contiene los modelos "GPT-5.6 Sol", "GPT-5.6 Terra", "GPT-5.6 Luna" y "GPT-6 Luna". En el mundo de la IA, Sol y Luna ya son nombres de modelos de OpenAI; esto agrava la confusión de búsqueda justo en el terreno del "bot de IA".
- Otras colisiones de Sol/Luna: Solana (SOL, repositorio de 14.9k estrellas, hoy archivado y sucedido por Agave), Terra/LUNA (cripto), Amazon Luna (nube gamer) y la app Lunar (macOS, brillo de monitores). Para Sun/Moon: Sun Microsystems/Oracle y Pokémon Sun/Moon no se pudieron abrir (confianza baja).
- Diseño: el par día/noche es un patrón establecido (Android DayNight, Auto Dark Mode con amanecer/atardecer, Night Light, Home Assistant `sun.sun` con `above_horizon`/`below_horizon`). Íconos libres: Lucide (ISC) tiene `sun-moon`, `sunrise`, `moon-star`.
- Cálculo propio de contraste: ámbar #F5A524 sobre #14161C da 8.86:1 y azul lunar #9DB4E8 sobre #0E1424 da 8.85:1 (ambos superan 4.5:1). Cuidado: el naranja ya significa "trabajando" en el ícono del Detector.
- Recomendación (opinión): nombres de cara al usuario "Sol" y "Luna" siempre precedidos por WINT ("WINT Sol", "WINT Luna"), identificadores ASCII internos `sol`/`luna` dentro de un espacio de nombres `wint`, sin publicar nunca `wint`, `sol` ni `luna` desnudos. Antes de cualquier uso público o comercial, búsqueda de marcas en INPI, WIPO, TMview y USPTO (clases de Niza 9, 35, 42). Esto no es asesoramiento legal.

## Hallazgos

### H1 — WINT ya es una empresa: Wint (wint.ai), agua e IA
- Afirmación: Existe una empresa llamada WINT (también escrita Wint) con sitio wint.ai, descrita como plataforma de gestión de agua y detección de fugas con IA para instalaciones comerciales e industriales: sensores IoT de caudal, válvulas de corte automáticas y centro de monitoreo 24/7, con procesamiento de señales y detección de anomalías. Un perfil de terceros de API Evangelist la lista como empresa del portafolio de Insight Partners. La organización GitHub `wint-ai` figura como radicada en Israel, enlaza a wint.ai y publica la maqueta "Wint Pulse 2.0", una app móvil de monitoreo de fugas para administradores de edificios e inquilinos (repositorio actualizado en septiembre de 2026). Cercanía con el software de la persona: rubro distinto (hardware IoT B2B de agua), pero misma mecánica "monitorear, detectar anomalías y avisar" y mismo nombre de 4 letras con la palabra IA; en tiendas de apps y buscadores "Wint" devolverá primero a esta empresa. Variantes: "Wint", "WINT", "WINT.ai", "Wint Pulse". El nombre completo "Wint Water Intelligence" aparece en el encargo y en el tema `water-intelligence` del perfil de terceros, pero no pude abrir wint.ai para confirmar razón social, fundación, sede ni financiamiento.
- Fuentes: https://github.com/api-evangelist/wint, https://github.com/wint-ai, https://github.com/wint-ai/pulse2_mobile_product_mockup
- Confianza: media (fuentes secundarias y de GitHub; el sitio oficial está bloqueado)
- Riesgo: alto
- Vigencia: consultado 7 de octubre de 2026 (perfil de API Evangelist creado el 2 de agosto de 2026 y actualizado el 4 de octubre de 2026; repositorio de Wint Pulse actualizado en septiembre de 2026)

### H2 — Un crate `wint` publicado el 6 de octubre de 2026 propone ventanas de tiempo deterministas
- Afirmación: En crates.io existe `wint` 0.1.0, creado el 2026-10-06 (09:59 UTC) por la cuenta `aunailab` (cuenta creada una hora antes, 08:53 UTC). Descripción: "Deterministic, explainable engine that finds the time windows when a job can run within the limits you set". Licencia MIT; palabras clave: windows, scheduling, forecast, time-series, constraints; 7 descargas; repositorio https://github.com/aunai-org/wint (organización `aunai-org`, sitio aunai.org, 4 repositorios, incluido `wint-demo`, un demo en el navegador). El README dice que recibe lecturas con marca de tiempo (pronósticos, métricas, precios) y devuelve ventanas factibles ordenadas con evidencia; admite la restricción `is_day` ("== 1" / "== 0") y los indicadores `--between` y `--on`; se ofrece como biblioteca Rust, CLI y WebAssembly. Cercanía alta en concepto (determinista, explicable, ventanas de tiempo, día/noche, precios) y en el nombre exacto "wint". No hay evidencia de relación con la persona que encarga el informe; si el crate fuera suyo, este hallazgo se descarta. Hecho: el nombre ya está en uso en otro ecosistema. Opinión: conviene monitorear el repositorio, porque una colisión conceptual y de nombre puede crecer.
- Fuentes: https://crates.io/api/v1/crates/wint, https://crates.io/api/v1/crates/wint/owners, https://github.com/aunai-org/wint, https://github.com/aunai-org
- Confianza: alta (datos leídos del registro y del repositorio)
- Riesgo: alto
- Vigencia: consultado 7 de octubre de 2026 (crate creado el 6 de octubre de 2026)

### H3 — `wint` en los registros: PyPI, npm, Docker Hub y GitHub, más ruido de búsqueda
- Afirmación: PyPI `wint` existe: versión 0.2.0, "Dependency injection with type hints", autor Stanislav Lobanov, 2 versiones, última subida el 2018-07-18, hogar https://github.com/asyncee/wint (proyecto prácticamente abandonado, pero el nombre no está disponible). npm `wint` existe: versión 0.0.1, descripción "wint", creado el 2017-03-25, última modificación 2022-06-29, mantenedor `atwoz`, una sola versión (paquete placeholder). Docker Hub: existe el usuario `wint` (Kurnia D Win, desde el 2015-06-29). GitHub: `github.com/Wint` es un usuario individual (Winton Wint, China, 14 repositorios, 3 seguidores) y `github.com/wint-ai` es una organización (H1). RubyGems `wint` y NuGet `wint`: no existen (HTTP 404, libres). Ruido de búsqueda (hecho medido, con la salvedad de que es coincidencia por subcadena): en GitHub `wint in:login` devuelve 22,395 usuarios y `wint in:name language:python` devuelve 3,938 repositorios, encabezados por nombres como `winton-kafka-streams`, `winterpy`, `WinT3R`, es decir, "wint" queda sepultado bajo "winter" y "winton". Opinión: en español el nombre se leerá "güint" o "uint"; "Wint" no es palabra del español; puede evocar "Win NT" (Windows NT), asociación que podría confundir con Microsoft.
- Fuentes: https://pypi.org/pypi/wint/json, https://registry.npmjs.org/wint, https://hub.docker.com/v2/users/wint/, https://github.com/Wint, https://rubygems.org/api/v1/gems/wint.json, https://api.nuget.org/v3-flatcontainer/wint/index.json
- Confianza: alta
- Riesgo: alto
- Vigencia: consultado 7 de octubre de 2026 (PyPI última subida 18 de julio de 2018; npm modificado el 29 de junio de 2022)

### H4 — Dominios de "wint": casi todo registrado, salvo .ar, .com.ar y combinaciones con prefijo
- Afirmación: Método: consulta DNS directa de registros NS y A (resolver 8.8.8.8). Un dominio con NS delegados cuenta como registrado; NXDOMAIN en NS y A indica que no está delegado, lo que sugiere (sin garantizarlo) que está libre. Resultado al 2026-10-07. Registrados/delegados: wint.com, wint.ai (4 NS), wint.app, wint.dev, wint.io, wint.net, wint.org, wint.xyz, wint.lat, wint.cloud, wint.us, wintapp.com, wintos.com. Sin delegación (NXDOMAIN): wint.ar, wint.com.ar, wint.tech, wint.software, getwint.com, getwint.app, getwint.ar, wintapp.ar, wintapp.com.ar, wintapp.app, wintapp.ai, wint-app.com, wint-app.ar, wintsuite.com, wintplatform.com, wintplatform.ar, wintsol.com, wint-os.com. Advertencia: DNS no es WHOIS; un dominio puede estar registrado sin delegar, en trámite o reservado. La confirmación debe hacerse en el registro de dominios .ar (NIC Argentina) y en un registrador; no pude abrir nic.ar ni RDAP.
- Fuentes: método propio de consulta DNS (sin URL), a contrastar en https://nic.ar (no abierto por bloqueo de red)
- Confianza: media
- Riesgo: alto
- Vigencia: consultado 7 de octubre de 2026

### H5 — Identificadores libres hoy con prefijo `wint-` y hechos sobre `wintapp`
- Afirmación: Verificados como inexistentes (HTTP 404) el 2026-10-07: en PyPI y en npm a la vez: `wint-sol`, `wint-luna`, `wint-sun`, `wint-moon`, `wint-osi`, `wint-app`, `wint-ai`, `wint-platform`, `wintcore`, `pywint`, `wint-detector`, `sol-luna`, `solluna`, `sol-y-luna`; solo en PyPI (npm no comprobado): `wintai`. Ocupados: npm `wint-core` y npm `osi-app` (existen; PyPI `wint-core` y `osi-app` están libres). GitHub (consulta de perfil): `wint-app` y `getwint` devuelven 404 (libres); `wintos` existe (usuario en Tailandia); `wintapp` existe (cuenta creada el 22 de septiembre de 2026, sin repositorios; titular desconocido, posiblemente alguien que ya reservó el nombre). RubyGems y NuGet sin conflicto para `wint` (en Docker Hub, en cambio, el usuario `wint` ya existe, H3). Los ámbitos de npm (`@wint`, `@osi`, `@sol`, `@luna`) no se pudieron comprobar (la búsqueda por ámbito del registro no es confiable y npmjs.com devuelve 403). Opinión: reservar solo lo que se vaya a usar; reservar nombres cuesta atención y puede crear una expectativa de publicación.
- Fuentes: https://pypi.org/pypi/wint-sol/json, https://registry.npmjs.org/wint-sol, https://github.com/wintapp, https://github.com/wint-app
- Confianza: media (los 404 se verificaron una sola vez; cualquiera puede ocupar el nombre mañana)
- Riesgo: alto
- Vigencia: consultado 7 de octubre de 2026

### H6 — OSI es la Open Source Initiative; sus datos de licencias quedaron archivados en 2026
- Afirmación: La organización GitHub `OpenSourceOrg` se presenta como "Stewards of the Open Source Definition", con sitio https://opensource.org/ y contacto contact@opensource.org; tiene 17 repositorios públicos, casi todos archivados. El repositorio `OpenSourceOrg/licenses` ("UNMAINTAINED machine readable OSI license information") quedó archivado el 2026-06-09 y su README indica que existe una API de reemplazo basada en los metadatos del sitio de OSI. Implicación: "OSI" en el contexto de software de código abierto se asocia fuertemente con licencias aprobadas ("OSI-approved"); un producto llamado "Osi" (aunque no use la sigla en mayúsculas) invita a confusión y a que la organización cuestione usos que sugieran aval. No pude abrir opensource.org ni sus pautas de marca (bloqueado), de modo que su política de marca figura entre lo no verificado.
- Fuentes: https://github.com/OpenSourceOrg, https://github.com/OpenSourceOrg/licenses
- Confianza: media
- Riesgo: alto
- Vigencia: consultado 7 de octubre de 2026 (archivado el 9 de junio de 2026)

### H7 — OSI también es el modelo de redes (Open Systems Interconnection, 7 capas)
- Afirmación: Los repositorios de GitHub describen "OSI" como el modelo de interconexión de sistemas abiertos de siete capas (por ejemplo la descripción de `valentin00013/Layer-2`: "the second layer of the seven-layer OSI model of computer networking"; `Roboticela/OSI-Model-Simulator`: "shows how messages move through all seven layers"). La búsqueda `OSI model networking layers` devuelve 142 repositorios, y cualquier contenido educativo de redes usa esa sigla. Resultado práctico (opinión): una búsqueda por "Osi" o "OSI software" mezcla Open Source Initiative, modelo OSI, tutoriales de redes y la sigla de varias empresas; el posicionamiento de un software llamado "Osi" será muy difícil. No pude abrir la norma ISO/IEC 7498 (iso.org bloqueado).
- Fuentes: https://github.com/valentin00013/Layer-2, https://github.com/Roboticela/OSI-Model-Simulator, https://github.com/AzizBenIsmail/Switching_network
- Confianza: alta (para la existencia del modelo y la saturación); media (para el conteo, que depende del buscador de GitHub)
- Riesgo: bajo
- Vigencia: consultado 7 de octubre de 2026

### H8 — `osi` en registros: libre en PyPI, RubyGems, NuGet y Docker; ocupado en npm, crates.io y GitHub
- Afirmación: PyPI `osi`: no existe (404, libre). RubyGems `osi` y NuGet `osi`: 404 (libres). Docker Hub: no hay usuario `osi` (404). npm `osi`: existe, versión 14.4.12, descripción "OSI is a distributed P2P project, aiming at creating a censorship free, anonymous and open internet", creado el 2014-04-24, última modificación 2022-06-23, mantenedor `digihaven`. crates.io `osi`: versión 0.0.1, "Capability-based Standard Interfaces", repositorio https://github.com/bus1/sys, 8,072 descargas, actualizado el 2025-05-22. GitHub: `github.com/osi` es el usuario Peter Royal (Los Ángeles, trabaja en Netflix, 42 repositorios, 65 seguidores). `osi in:login` devuelve 15,122 usuarios. Opinión: aunque PyPI `osi` esté libre, publicarlo bajo ese nombre lo asociaría a OSI; si el módulo es interno, `wint-osi` es más seguro.
- Fuentes: https://pypi.org/pypi/osi/json, https://registry.npmjs.org/osi, https://crates.io/api/v1/crates/osi, https://github.com/osi, https://hub.docker.com/v2/users/osi/
- Confianza: alta
- Riesgo: alto
- Vigencia: consultado 7 de octubre de 2026

### H9 — Dominios de "osi": todos registrados, salvo osi.ar
- Afirmación: Con el mismo método DNS de H4: delegados o registrados: osi.com (3 NS, sin registro A), osi.app, osi.ai, osi.dev, osi.io, osi.net, osi.org, osi.com.ar. Sin delegación (NXDOMAIN): osi.ar. Conclusión: ningún dominio razonable de "osi" está disponible salvo posiblemente `osi.ar`, y aun así su uso no resuelve la confusión de H6 y H7. Confirmar en NIC Argentina (no abierto).
- Fuentes: método propio de consulta DNS (sin URL), a contrastar en https://nic.ar (no abierto)
- Confianza: media
- Riesgo: alto
- Vigencia: consultado 7 de octubre de 2026

### H10 — Sol, Luna, Sun y Moon desnudos están ocupados en todos los registros de paquetes y en GitHub
- Afirmación: PyPI: `sol` = SoL, "Carrom tournaments management" (versión 5.26, 164 versiones, última subida 2026-08-03); `luna` = LUNA, "drug discovery toolkit" (0.14.0, 2025-09-18); `sun` = "Tray notification applet for informing about package updates in Slackware" (2.5.3, 2026-06-04); `moon` = "Fetch moon phase visualizations from NASA's Dial-a-Moon API" (3.0.0, 2026-09-07). npm: `sol` (utilidad de hashes, 0.3.0), `luna` ("a reactive redux-like store", 1.6.3), `sun` (helper de VDOM para Preact, 1.1.4), `moon` ("The minimal & fast library for functional user interfaces", 1.0.0-beta.7); los cuatro con última modificación en 2022. RubyGems `sol` (0.0.1, 2014) y `luna` (0.0.1, servidor de archivos estáticos, 2026-08-13). NuGet `sol` y `luna` existen. crates.io `sol` (envoltorio de Embree, 0.1.5, 2019) y `luna` (0.2.1, 2025-08-24). Docker Hub: usuario `luna` existe (desde 2014); `sol` no existe. GitHub: `sol` (Simon Hengel, Singapur, 271 repositorios, 282 seguidores, proyectos Haskell: hspec, hpack), `luna` (usuario de modding de Call of Duty), `sun` (Daniel Kudwien, Alemania, 56 repositorios), `moon` (organización en Londres) están todos ocupados; también existe `solyluna` (usuario con 3 repositorios de prueba). Ruido de búsqueda en GitHub: `luna in:login` = 53,405 usuarios; `sol in:login` = 176,661 y `moon in:login` = 70,457 (resultados marcados como incompletos por GitHub). Con prefijo, `wint-sol`, `wint-luna`, `wint-sun`, `wint-moon` están libres en PyPI y npm (H5).
- Fuentes: https://pypi.org/pypi/sol/json, https://pypi.org/pypi/luna/json, https://pypi.org/pypi/sun/json, https://pypi.org/pypi/moon/json, https://registry.npmjs.org/luna, https://registry.npmjs.org/sol, https://registry.npmjs.org/sun, https://registry.npmjs.org/moon, https://crates.io/api/v1/crates/sol, https://rubygems.org/api/v1/gems/luna.json, https://github.com/sol, https://github.com/luna, https://github.com/sun, https://github.com/moon, https://github.com/solyluna
- Confianza: alta
- Riesgo: alto
- Vigencia: consultado 7 de octubre de 2026

### H11 — Dominios de sol, luna y "sol y luna": las palabras sueltas están todas tomadas
- Afirmación: Método DNS de H4. Registrados: sol.com, sol.app, sol.ai, sol.dev, sol.ar, sol.com.ar (3 NS); luna.com, luna.app, luna.ai, luna.ar, luna.com.ar (4 NS, sin registro A); sun.com (8 NS), moon.com, sunmoon.app, solyluna.com, solyluna.com.ar, solyluna.app, sol-luna.com, solluna.com. Sin delegación (NXDOMAIN): solyluna.ar, solluna.app. (`luna.dev` respondió SERVFAIL; indeterminado.) Opinión: para el par Sol/Luna no hay dominio propio razonable; la salida es colgar los módulos de un dominio de WINT (por ejemplo subdominios `sol.` y `luna.` o rutas) en lugar de comprar dominios sueltos. Confirmar los NXDOMAIN en NIC Argentina o un registrador.
- Fuentes: método propio de consulta DNS (sin URL), a contrastar en https://nic.ar (no abierto)
- Confianza: media
- Riesgo: alto
- Vigencia: consultado 7 de octubre de 2026

### H12 — Colisión nueva y fuerte: OpenAI usa "Sol", "Terra" y "Luna" como nombres de modelos
- Afirmación: En el repositorio oficial de OpenAI `openai/codex` (Apache-2.0, 128.1k estrellas) figuran como modelos: `gpt-5.6-sol`, `gpt-5.6-terra`, `gpt-5.6-luna`, `gpt-6-luna`, `gpt-6-sol`, `gpt-6.1-sol` y `gpt-6-astra`, con identificadores equivalentes en Amazon Bedrock (`openai.gpt-5.6-sol`, `openai.gpt-6-luna`). Una captura de la interfaz de selección de modelos muestra: "GPT-6-Luna: Fast and affordable model for easier tasks", "GPT-5.6-Sol: Older generation workhorse model", "GPT-5.6-Terra: Older balanced model for straightforward work", "GPT-5.6-Luna: Older fast and efficient model". Un documento de migración del propio repositorio indica: Astra = nivel insignia, Terra = equilibrado, Luna = "primary speed and cost option". Además aparecen repositorios de terceros de julio de 2026 que enrutan tareas entre "Sol, Terra y Luna" para Codex (por ejemplo `codyrobertson/codex-advisor`, `AlexAI-MCP/GPT5.6-SOLTELU-Model-Inverter`). Implicaciones (opinión): (a) en contextos de IA y programación asistida, "Luna" y "Sol" ya remiten a modelos de OpenAI; (b) un "WINT" descrito como "bot de IA" con módulos Sol y Luna se confundirá en búsquedas y en conversaciones; (c) no es una marca registrada para un producto de la persona, pero sí un riesgo de confusión y de percepción de afiliación. Cautela: los nombres de modelos cambian rápido (la lista ya marca algunos como "older"), y no pude abrir la documentación comercial de OpenAI (bloqueada); la evidencia es el código y los textos del repositorio oficial.
- Fuentes: https://github.com/openai/codex, https://github.com/openai/codex/blob/406eb53c074a29bd65aa7a8bd21d574234faf315/codex-rs/skills/src/assets/samples/openai-docs/references/latest-model.md, https://github.com/openai/codex/blob/406eb53c074a29bd65aa7a8bd21d574234faf315/codex-rs/skills/src/assets/samples/openai-docs/references/upgrading-to-gpt-6-astra.md, https://github.com/openai/codex/blob/406eb53c074a29bd65aa7a8bd21d574234faf315/codex-rs/tui/src/chatwidget/snapshots/codex_tui__chatwidget__tests__model_selection_popup.snap, https://github.com/openai/codex/blob/406eb53c074a29bd65aa7a8bd21d574234faf315/codex-rs/model-provider-info/src/lib.rs, https://github.com/codyrobertson/codex-advisor
- Confianza: media (es evidencia de código del repositorio oficial, no de un anuncio comercial)
- Riesgo: alto
- Vigencia: consultado 7 de octubre de 2026 (versión del código consultada: commit 406eb53; la página de releases de Codex mostraba versiones del 3 al 7 de octubre de 2026)

### H13 — Solana (SOL) y su sucesor Agave: "Sol" evoca criptomonedas
- Afirmación: El repositorio `solana-labs/solana` ("Web-Scale Blockchain for fast, secure, scalable, decentralized apps and marketplaces", Rust) tiene 14,942 estrellas y figura archivado. `anza-xyz/agave` está descrito con el mismo texto, "forked from solana-labs/solana", con licencia Apache-2.0 y sitio anza.xyz. Que el token se llame SOL no pude confirmarlo en una página abierta (solana.com bloqueado); el nombre del ticker queda como conocimiento general, confianza baja. Opinión: "Sol" a secas, sobre todo con mayúsculas ("SOL"), se lee en el ámbito financiero como criptomoneda; para una herramienta de ahorro y precios, esa asociación no ayuda.
- Fuentes: https://github.com/solana-labs/solana, https://github.com/anza-xyz/agave
- Confianza: media (repositorio); baja (ticker SOL, no abierto)
- Riesgo: alto
- Vigencia: consultado 7 de octubre de 2026

### H14 — Terra/LUNA: el nombre "Luna" quedó ligado a un colapso financiero
- Afirmación: El README de `terra-money/classic-core` (implementación en Go del protocolo Terra, sobre Cosmos SDK y Tendermint) dice: "Upon the implosion of Terra, a group of rebels seized control of the blockchain"; el código usa `uluna` como unidad mínima de Luna. La cadena clásica sigue viva con un token conocido como LUNC (la relación entre LUNA y LUNC no pude confirmarla en una fuente abierta). Opinión: para un producto cuyo propósito es "demostrar las mentiras de las ofertas" y ganar confianza, "Luna" evoca en buena parte del público (sobre todo el que sigue criptomonedas) un caso célebre de pérdida de dinero; es un riesgo de percepción, no legal.
- Fuentes: https://github.com/terra-money/classic-core
- Confianza: media (hecho del README); baja (percepción pública)
- Riesgo: alto
- Vigencia: consultado 7 de octubre de 2026

### H15 — Amazon Luna, Pokémon Sun/Moon y Sun Microsystems: solo evidencia indirecta
- Afirmación: Hecho verificado de forma indirecta: existen repositorios que presuponen Amazon Luna como servicio de juegos en la nube (`mistertest/luna-shield`: "Luna App Unofficial for the Nvidia Shield Android TV. Play your Amazon Luna games in the cloud", creado en 2021, actualizado el 2026-07-22; `decafCG/decaf`: herramienta que mide el rendimiento de plataformas como Google Stadia, Amazon Luna y NVIDIA GeForce Now). Existen repositorios de la comunidad de Pokémon Sun/Moon creados en noviembre de 2016 (`AnalogMan151/sumoCheatMenu` creado el 2016-11-22; `richi3f-zz/pokemon-team-planner` creado el 2016-10-24) y todavía hay actividad en 2026 (`its269/Battle-Tree-Vault`, 21 de septiembre de 2026). No pude abrir páginas de Amazon, Nintendo, Pokémon ni Oracle: fechas de lanzamiento, países donde está disponible Amazon Luna (incluida Argentina), que "Sol y Luna" sea el título en español de Pokémon Sun/Moon y los detalles de la adquisición de Sun Microsystems por Oracle quedan SIN verificar (ver sección final). Opinión: Luna (juegos en la nube) y Pokémon (videojuegos) viven en la clase 9/41 de software y juegos; el solapamiento con una herramienta de utilidad es parcial pero nada evidente.
- Fuentes: https://github.com/mistertest/luna-shield, https://github.com/decafCG/decaf, https://github.com/AnalogMan151/sumoCheatMenu, https://github.com/richi3f-zz/pokemon-team-planner
- Confianza: baja
- Riesgo: alto
- Vigencia: consultado 7 de octubre de 2026

### H16 — Nombres con luna en el terreno de pantallas y modo nocturno: Lunar, Redshift y Night Light
- Afirmación: Lunar (alin23/Lunar) es una app para macOS que controla brillo, volumen y entrada de monitores externos, con brillo adaptativo por sensores, luz ambiente o ubicación; licencia MIT, 5.7k estrellas, sitio lunar.fyi, instalación con `brew install --cask lunar`; el repositorio indica que el código de las funciones pagas está cifrado y no acepta contribuciones. Es un vecino temático directo de un módulo "Luna" (brillo y noche), aunque solo para macOS. Redshift (jonls/redshift, GPL-3.0, 6.1k estrellas) ajusta la temperatura de color según la hora; su repositorio fue archivado el 2026-04-01 y su README remite a alternativas integradas: GNOME Night Light, Plasma Night Color, Windows Night Light y macOS Night Shift. Conclusión: "Night Light", "Night Shift" y "Night Color" son los nombres de sistema de la función nocturna; "Lunar" ya ocupa el espacio de nombre "luna" en apps de pantalla.
- Fuentes: https://github.com/alin23/Lunar, https://github.com/jonls/redshift
- Confianza: alta
- Riesgo: alto
- Vigencia: consultado 7 de octubre de 2026 (Redshift archivado el 1 de abril de 2026)

### H17 — Sistemas operativos y plataformas ya modelan el par día/noche con nombres propios
- Afirmación: Android: temas `Theme.AppCompat.DayNight` y `Theme.MaterialComponents.DayNight`; constantes `AppCompatDelegate.MODE_NIGHT_NO`, `MODE_NIGHT_YES`, `MODE_NIGHT_FOLLOW_SYSTEM` (recomendada); desde API 31, `UiModeManager#setApplicationNightMode(int)`; detección con `Configuration.UI_MODE_NIGHT_MASK`, `UI_MODE_NIGHT_YES`, `UI_MODE_NIGHT_NO`; tema oscuro disponible desde Android 10 (API 29); "Force Dark" con `android:forceDarkAllowed`. Apple HIG (modo oscuro): usar colores semánticos (`systemBackground`, `label`, etc.), no valores fijos, y mantener contraste mínimo de 4.5:1 para texto normal y 3:1 para texto grande (criterio WCAG AA). Implicación: si WINT se piensa como "plataforma Android", un módulo Sol/Luna debe mapear a "modo diurno"/"modo nocturno" del sistema con el esquema `DayNight`; la dupla Sol/Luna se entiende de inmediato en esas APIs aunque los identificadores técnicos sigan siendo `day`/`night`.
- Fuentes: https://developer.android.com/develop/ui/views/theming/darktheme, https://developer.apple.com/design/human-interface-guidelines/dark-mode
- Confianza: alta (Android); media (Apple, resumen de la página)
- Riesgo: alto
- Vigencia: consultado 7 de octubre de 2026

### H18 — Auto Dark Mode es el precedente más cercano en Windows (amanecer y atardecer)
- Afirmación: Auto Dark Mode (AutoDarkMode/Windows-Auto-Night-Mode, GPL-3.0, 9.7k estrellas) alterna Windows entre tema claro y oscuro según amanecer y atardecer, sensor de luz ambiente, condiciones personalizadas y scripts; también cambia fondo de pantalla, cursor, color de énfasis y teclado táctil; no cambia mientras se juega; admite Windows 10 (22H2 o posterior) y Windows 11; se instala por Microsoft Store, `winget install autodarkmode`, Chocolatey, Scoop o descarga directa. Versiones: 11.1.1 (2026-08-16, corrección), 11.1.0 (2026-08-14, soporte de sensor de luz ambiente y rediseño de color de énfasis), 11.0.0 (2025-10-13, interfaz WinUI 3 con Windows App SDK). Ganó los Microsoft App Store Awards de 2022 según su README. Existen además scripts de PowerShell más pequeños que programan el cambio con el Programador de tareas (`thisis-romar/windows-auto-theme-switcher`, 1 estrella). Implicación: el caso de uso "Sol = amanecer" ya tiene una app madura; WINT puede integrarse con ella o competir en otra dimensión (rutinas que van más allá del tema).
- Fuentes: https://github.com/AutoDarkMode/Windows-Auto-Night-Mode, https://github.com/AutoDarkMode/Windows-Auto-Night-Mode/releases, https://github.com/thisis-romar/windows-auto-theme-switcher
- Confianza: alta
- Riesgo: alto
- Vigencia: consultado 7 de octubre de 2026 (última versión 11.1.1 del 16 de agosto de 2026)

### H19 — Home Assistant aporta un vocabulario de estados y disparadores solares reutilizable
- Afirmación: La integración Sun de Home Assistant mantiene la entidad `sun.sun` con dos estados, `above_horizon` y `below_horizon`; atributos de próximos eventos en UTC (`next_dawn`, `next_dusk`, `next_noon`, `next_midnight`, `next_rising`, `next_setting`), `elevation` (ángulo negativo cuando el sol está bajo el horizonte) y `azimuth`; un sensor binario "solar rising". Disparador `trigger: sun` con `event: sunrise` o `sunset` y un `offset` (por ejemplo "-01:00:00" dispara antes del evento), y, para el crepúsculo, el disparador de umbral de elevación. Implicación: es un patrón probado para modelar "Sol" y "Luna" en WINT como estados de un reloj solar con desplazamientos, no como botones.
- Fuentes: https://raw.githubusercontent.com/home-assistant/home-assistant.io/current/source/_integrations/sun.markdown
- Confianza: alta
- Riesgo: bajo
- Vigencia: consultado 7 de octubre de 2026

### H20 — Íconos libres para sol y luna: Lucide (ISC), Bootstrap Icons (MIT) y Tabler (MIT)
- Afirmación: Lucide: licencia ISC (los íconos heredados de Feather, MIT); versión 1.52.0 publicada el 2026-10-04; verificados en el repositorio `sun-moon.svg` (452 bytes), `sunrise` (etiquetas weather, time, morning, day) y `moon-star` (etiquetas dark, night, star; categorías accessibility, weather). `sun`, `moon` y `sunset` los doy por existentes pero no los abrí. Bootstrap Icons: MIT, versión 1.13.1 publicada el 2025-05-09, existe `moon-stars.svg` (media luna con estrellas, 16×16, `currentColor`). Tabler Icons: MIT, versión 3.49.0 publicada el 2026-10-05 (los íconos concretos de sol y luna no los abrí). Octicons (GitHub, MIT) tiene `sun-16.svg` y `moon-16.svg`, pero el resumen automático de su contenido fue inconsistente y no lo uso como evidencia. Opinión: Lucide es el candidato natural por tener el ícono combinado `sun-moon` para el nombre de la suite y los individuales para los módulos.
- Fuentes: https://github.com/lucide-icons/lucide/blob/main/icons/sun-moon.svg, https://raw.githubusercontent.com/lucide-icons/lucide/main/icons/sunrise.json, https://raw.githubusercontent.com/lucide-icons/lucide/main/icons/moon-star.json, https://raw.githubusercontent.com/lucide-icons/lucide/main/LICENSE, https://registry.npmjs.org/lucide, https://raw.githubusercontent.com/twbs/icons/main/icons/moon-stars.svg, https://registry.npmjs.org/bootstrap-icons, https://registry.npmjs.org/@tabler%2ficons
- Confianza: alta (Lucide: licencia, versión, `sun-moon`, `sunrise`, `moon-star`); media (el resto)
- Riesgo: alto
- Vigencia: consultado 7 de octubre de 2026 (Lucide 1.52.0 del 4 de octubre de 2026)

### H21 — Paleta ámbar dorado y azul lunar: contraste calculado y conflicto con el naranja del Detector
- Afirmación: Cálculo propio con la fórmula de luminancia relativa de WCAG 2.x (hecho matemático; los colores son propuestas, no estándares): #F5A524 sobre #14161C = 8.86:1; texto #1F1500 sobre ámbar #F5A524 = 8.83:1; ámbar oscuro #B45309 sobre crema #FFF8E7 = 4.74:1 (pasa AA para texto normal por poco); azul lunar #9DB4E8 sobre noche #0E1424 = 8.85:1; azul #3B5BDB sobre blanco = 5.67:1; texto #E8EEFF sobre azul noche #1B2A4E = 12.17:1; ámbar #F5A524 sobre azul noche #1B2A4E = 6.92:1. Todos superan 4.5:1. Conflicto de diseño (hecho del encargo): el ícono de bandeja del Detector se pone naranja mientras trabaja; un ámbar dorado cercano al naranja puede leerse como "estado: trabajando". Opinión: reservar el naranja exclusivamente para "trabajando", usar un dorado más amarillo para Sol y diferenciar por forma (sol con rayos, luna creciente) y no solo por color, y definir los colores como tokens de modo claro/oscuro en vez de valores fijos.
- Fuentes: cálculo propio (fórmula WCAG), umbrales 4.5:1 y 3:1 citados en https://developer.apple.com/design/human-interface-guidelines/dark-mode
- Confianza: alta (cálculos); media (umbrales según resumen de la página de Apple)
- Riesgo: bajo
- Vigencia: consultado 7 de octubre de 2026

### H22 — Búsqueda y registro de marcas: no pude abrir ninguna fuente oficial (lista de verificación)
- Afirmación: No se pudo abrir inpi.gob.ar, argentina.gob.ar, wipo.int/branddb, tmdn.org (TMview), euipo.europa.eu ni los buscadores del USPTO (todos bloqueados por la red de la sesión), de modo que costos, plazos y requisitos del registro de marca en Argentina quedan SIN verificar y no se dan cifras. Lo que se puede decir con confianza baja, de conocimiento general y a confirmar en la fuente oficial: la marca se registra por clase del Nomenclador de Niza ante el INPI; para software, las clases habituales son 9 (software descargable), 42 (software como servicio y desarrollo) y 35 (servicios comerciales, entre ellos comparación de precios); la vigencia es de varios años renovables; el régimen argentino se rige por la Ley 22.362. Lista de verificación mínima antes de usar un nombre en público o comercialmente: (1) buscar el nombre exacto y variantes fonéticas ("Wint", "Güint", "Uint") en la base del INPI Argentina; (2) repetir en WIPO Global Brand Database, TMview (EUIPO) y USPTO, filtrando clases 9, 35, 42; (3) buscar titulares conocidos: Wint (wint.ai) en 9/42, Amazon (Luna), OpenAI (Sol/Luna/Terra) y Open Source Initiative (OSI); (4) revisar bases por marcas mixtas (logotipos de sol/luna); (5) registrar el dominio y las cuentas antes de anunciar; (6) consultar a un agente de la propiedad industrial matriculado antes de invertir. Esto no es asesoramiento legal.
- Fuentes: ninguna abierta; sitios oficiales a consultar (no abiertos por bloqueo): https://www.inpi.gob.ar, https://branddb.wipo.int, https://www.tmdn.org/tmview, https://tmsearch.uspto.gov
- Confianza: baja
- Riesgo: alto
- Vigencia: consultado 7 de octubre de 2026 (sin fuente accesible)

### H23 — Estrategia de identificadores: nombre visible en español, ID interno en ASCII con prefijo
- Afirmación: Hecho: los nombres `sol`, `luna`, `sun` y `moon` están ocupados en PyPI, npm y GitHub (H10), `wint` está ocupado en PyPI y npm (H3), y los nombres con prefijo `wint-sol`, `wint-luna`, `wint-sun`, `wint-moon`, `wint-osi` están libres en PyPI y npm al 2026-10-07 (H5). Opinión de diseño: (a) nombre visible: "Sol" y "Luna" con tildes y mayúsculas normales; interfaces en español rioplatense; (b) identificadores en ASCII, minúsculas, sin tildes ni espacios (`wint`, `sol`, `luna`, `osi`) como módulos o subcomandos internos (`wint sol`, `wint luna`, `wint osi`); (c) si algún día se publica un paquete, usar el nombre con prefijo (`wint-sol`) y no el desnudo; (d) evitar que un módulo local llamado `sol.py` o `luna.py` sombree paquetes instalados con esos nombres (existen `sol` y `luna` en PyPI); (e) ASCII evita problemas de codificación en rutas, tareas programadas y APIs. Pronunciación (opinión): "Sol" se lee igual en español y se entiende en inglés como "sol/sun" aunque suene a "soul"; "Luna" funciona en ambos idiomas; "Sun/Moon" se pronuncian "san/mun" con acento español, comprensibles pero menos naturales para una interfaz en español; "Osi" se pronuncia "osi" en español pero en inglés se deletrea "O-S-I"; "WINT" en español suena "güint/uint" y en inglés "wint". Memorabilidad (opinión): Sol y Luna son palabras cortas, universales y simétricas; Good Morning/Good Night son frases largas y en inglés para una interfaz en español.
- Fuentes: https://pypi.org/pypi/sol/json, https://pypi.org/pypi/luna/json, https://pypi.org/pypi/wint-sol/json, https://registry.npmjs.org/wint-luna
- Confianza: media (hechos); baja (pronunciación y memorabilidad son juicio del analista)
- Riesgo: bajo
- Vigencia: consultado 7 de octubre de 2026

## Herramientas y software

| Nombre | Qué hace | Plataforma | Licencia o precio | Estado a octubre 2026 (última versión/fecha si se puede) | URL oficial | Encaje con WINT (alto/medio/bajo) | Salvedad |
|---|---|---|---|---|---|---|---|
| Auto Dark Mode | Cambia Windows entre tema claro y oscuro por amanecer/atardecer, sensor de luz, condiciones y scripts | Windows 10 (22H2+) y 11 | GPL-3.0, gratuito | 11.1.1 del 16/8/2026 (11.1.0 del 14/8/2026) | https://github.com/AutoDarkMode/Windows-Auto-Night-Mode | alto | GPL-3.0: no incorporar su código a software propietario sin evaluar; mejor integrarse o inspirarse |
| Windows Night Light (función integrada) | Filtro de luz azul programable del sistema | Windows 10/11 | Incluido en Windows | Citado por el README de Redshift; no abrí documentación de Microsoft | https://github.com/jonls/redshift (mención) | medio | Sin documentación oficial abierta; verificar en Configuración de Windows |
| Redshift | Ajusta temperatura de color de pantalla según la hora | Linux, macOS, Windows | GPL-3.0 | Archivado el 1/4/2026, sigue funcionando | https://github.com/jonls/redshift | bajo | Archivado; sin Wayland |
| f.lux | Ajusta la temperatura de color de pantalla al ciclo del día | Windows, macOS, Linux | No verificado | No verificado | https://justgetflux.com | medio | No se pudo abrir el sitio (bloqueado); datos no verificados |
| Lunar (alin23) | Control de brillo, volumen y entrada de monitores externos, con brillo adaptativo | macOS | MIT en el repositorio (funciones pagas cifradas) | 5.7k estrellas; versión no consultada | https://github.com/alin23/Lunar | bajo | Solo macOS; colisión conceptual con "Luna" |
| Home Assistant: integración Sun | Entidad `sun.sun` con estados `above_horizon`/`below_horizon`, eventos solares y disparadores con desplazamiento | Servidor propio (multiplataforma) | Código abierto (licencia no consultada) | Documentación vigente en `current` | https://raw.githubusercontent.com/home-assistant/home-assistant.io/current/source/_integrations/sun.markdown | medio | Es un sistema de domótica, útil como modelo de estados |
| astral (Python) | Cálculo de posiciones del sol y la luna: amanecer, atardecer, fases | Python >=3.7,<4.0 | Apache-2.0 | 3.2, última subida 5/11/2022 | https://pypi.org/project/astral/ | alto | Sin releases desde 2022; probar con Python reciente |
| skyfield (Python) | Astronomía de alta precisión: salidas y puestas, fases lunares | Python | MIT | 1.55, 7/8/2026 | https://pypi.org/project/skyfield/ | medio | Más pesado que astral; requiere archivos de efemérides (tamaño no verificado) |
| ephem (Python) | Cálculo de posiciones de planetas y estrellas | Python | MIT | 4.2.1, 28/2/2026 | https://pypi.org/project/ephem/ | medio | Extensión en C; API antigua |
| pysolar (Python) | Posición solar e irradiancia | Python | GPL | 0.13, 4/1/2025 | https://pypi.org/project/pysolar/ | bajo | Licencia GPL; sirve más para energía solar que para rutinas |
| suntime (Python) | Cálculo simple de amanecer y atardecer | Python | LGPLv3 | 1.4.0, 31/8/2026 | https://pypi.org/project/suntime/ | medio | LGPLv3 |
| suncalc (npm) | Posiciones y fases del sol y la luna en JavaScript | Node/navegador | No consta en los metadatos del registro | 2.1.1, modificado el 5/10/2026 | https://registry.npmjs.org/suncalc | medio | Licencia a confirmar |
| Lucide Icons | Íconos SVG, incluidos `sun-moon`, `sunrise`, `moon-star` | Web y apps | ISC (partes MIT) | 1.52.0, 4/10/2026 | https://github.com/lucide-icons/lucide | alto | Íconos `sun`, `moon`, `sunset` sin abrir |
| Bootstrap Icons | Íconos SVG, incluido `moon-stars` | Web | MIT | 1.13.1, 9/5/2025 | https://github.com/twbs/icons | medio | Sin releases desde 2025 |
| Tabler Icons | Íconos SVG | Web | MIT | 3.49.0, 5/10/2026 | https://registry.npmjs.org/@tabler%2ficons | medio | Íconos concretos de sol y luna sin abrir |
| Android DayNight y UiModeManager | API de modo claro/oscuro: `MODE_NIGHT_*`, `UiModeManager#setApplicationNightMode` (API 31+) | Android 10+ | Incluido en Android | Documentación vigente | https://developer.android.com/develop/ui/views/theming/darktheme | medio | Solo relevante si WINT apunta a Android |
| Apple HIG: modo oscuro | Guía de apariencia clara/oscura, colores semánticos, contraste | iOS/macOS | Gratuito | Documentación vigente | https://developer.apple.com/design/human-interface-guidelines/dark-mode | bajo | Contexto de diseño; no es la plataforma objetivo |
| API JSON de PyPI | Consulta si un nombre existe (`/pypi/<nombre>/json`) y sus versiones | Web | Gratuito | Operativa el 7/10/2026 | https://pypi.org/pypi/wint/json | alto | La página HTML no cargó en la herramienta; usar la API |
| Registro npm (API) | Consulta de paquetes (`registry.npmjs.org/<nombre>`) | Web | Gratuito | Operativa el 7/10/2026 | https://registry.npmjs.org/wint | alto | La búsqueda por ámbito (`scope:`) no fue confiable; npmjs.com devuelve 403 |
| API de crates.io | Consulta de crates (`/api/v1/crates/<nombre>`) | Web | Gratuito | Operativa el 7/10/2026 | https://crates.io/api/v1/crates/wint | medio | Requiere cabecera User-Agent |
| Consulta DNS (NS y A) | Prueba indirecta de dominio registrado o libre | Cualquiera | Gratuito | Usada el 7/10/2026 | (método, sin URL) | medio | No reemplaza a WHOIS/RDAP ni a NIC Argentina |
| NIC Argentina | Registro de dominios .ar | Web | No verificado | No verificado | https://nic.ar | alto | No se pudo abrir (bloqueado); confirmar disponibilidad y costos |
| WIPO Global Brand Database | Buscador internacional de marcas | Web | Gratuito | No verificado | https://branddb.wipo.int | alto | No se pudo abrir (bloqueado) |
| TMview (EUIPO/TMDN) | Buscador de marcas de la UE y oficinas asociadas | Web | Gratuito | No verificado | https://www.tmdn.org/tmview | alto | No se pudo abrir (bloqueado) |
| Búsqueda de marcas del USPTO | Buscador de marcas de Estados Unidos | Web | Gratuito | No verificado | https://tmsearch.uspto.gov | medio | No se pudo abrir (bloqueado) |
| INPI Argentina (buscador y registro) | Búsqueda y presentación de marcas en Argentina | Web | Arancel oficial a consultar | No verificado | https://www.inpi.gob.ar | alto | No se pudo abrir (bloqueado); sin cifras de costos ni plazos |
| Colisión: Wint (wint.ai) y Wint Pulse | Plataforma de IA para agua y fugas en edificios; app móvil de monitoreo | Web y móvil | Comercial (condiciones no consultadas) | Maqueta de Pulse 2.0 actualizada en septiembre de 2026 | https://github.com/wint-ai | bajo | Colisión directa de nombre; datos de empresa de fuentes secundarias |
| Colisión: crate `wint` (aunai) | Motor determinista de ventanas de tiempo con restricciones | Rust, CLI, WebAssembly | MIT | 0.1.0, 6/10/2026 | https://github.com/aunai-org/wint | bajo | Colisión de nombre y concepto; titular sin relación comprobada |
| Colisión: OpenAI GPT-5.6 Sol/Terra/Luna y GPT-6 Luna | Familias de modelos de OpenAI listadas en Codex | API y Codex | Comercial | Código consultado el 7/10/2026 (commit 406eb53) | https://github.com/openai/codex | bajo | Evidencia de código, sin anuncio oficial abierto |
| Colisión: Open Source Initiative (OSI) | Organización que custodia la Open Source Definition | Web | Organización sin fines de lucro | Repositorios de licencias archivados el 9/6/2026 | https://github.com/OpenSourceOrg | bajo | Sitio opensource.org bloqueado |
| Colisión: Solana (SOL) y Agave | Blockchain y cliente sucesor | Cadena de bloques | Apache-2.0 | solana-labs/solana archivado; Agave activo | https://github.com/anza-xyz/agave | bajo | Ticker SOL no verificado en página abierta |
| Colisión: Terra Classic (LUNA/LUNC) | Implementación de la cadena Terra tras el colapso | Cadena de bloques | Código abierto | Repositorio `classic-core` | https://github.com/terra-money/classic-core | bajo | Percepción pública y relación LUNA/LUNC no verificadas |
| Colisión: Amazon Luna | Servicio de juegos en la nube | Web, TV, móviles | No verificado | No verificado | (no abierto) | bajo | amazon.com bloqueado; evidencia solo indirecta |
| Colisión: Pokémon Sun/Moon | Videojuegos de Nintendo (títulos en español "Sol y Luna" sin verificar) | Nintendo 3DS | Comercial | Comunidad activa en 2026 (indirecto) | (no abierto) | bajo | Fechas y nombres oficiales no verificados |

## Esquema para cuadro sinóptico

- Nombres de WINT
  - WINT
    - Wint.ai (agua, IA)
    - Crate wint (aunai)
    - PyPI y npm ocupados
    - Dominios casi todos tomados
  - Osi
    - Open Source Initiative
    - Modelo OSI de redes
    - PyPI libre, npm ocupado
  - Sol y Luna
    - Modelos OpenAI Sol/Luna
    - Solana y Terra Luna
    - Amazon Luna, Lunar
    - Nombres desnudos ocupados
  - Sun y Moon
    - Palabras genéricas
    - Sun Microsystems y Pokémon (sin verificar)
    - Paquetes ocupados
- Identificadores técnicos
  - Libres hoy
    - Prefijo wint- (PyPI, npm)
    - GitHub wint-app, getwint
  - Ocupados
    - wint, sol, luna, sun, moon
    - Dominios .com, .app, .ai
- Marcas
  - Dónde buscar
    - INPI Argentina
    - WIPO y TMview
    - USPTO
  - Clases de Niza
    - 9 software
    - 35 comparación de precios
    - 42 software como servicio
  - Estado: sin verificar
- Diseño día/noche
  - Precedentes
    - Android DayNight
    - Auto Dark Mode
    - Home Assistant sun.sun
  - Paleta
    - Ámbar dorado (Sol)
    - Azul lunar (Luna)
    - Naranja reservado al Detector
  - Íconos
    - Lucide sun-moon
    - Bootstrap moon-stars
- Decisión
  - Visible: Sol y Luna
  - Interno: sol, luna (ASCII)
  - Siempre con prefijo WINT
  - Marca: búsqueda previa

## Recomendaciones para WINT

Tabla de decisión (puntajes de 1 a 5, donde 5 es lo mejor; son juicio del analista basado en los hallazgos, no una medición):

| Opción | Colisión (5 = pocas) | Pronunciación es/en | Memorabilidad | Coherencia temática | Identificadores libres | Veredicto |
|---|---|---|---|---|---|---|
| Sol / Luna (visibles en español) con IDs `wint-sol`, `wint-luna` | 2 (modelos de OpenAI, Amazon Luna, Solana, Terra; todo desnudo ocupado) | 5 / 4 | 5 | 5 (idioma de la persona, día/noche, WINT) | 4 (con prefijo) | Recomendada, siempre con prefijo WINT |
| Sun / Moon | 2 (palabras genéricas; paquetes ocupados; Sun Microsystems y Pokémon sin verificar) | 3 / 5 | 4 | 3 (interfaz en español con nombres en inglés) | 3 | Aceptable, menos coherente |
| Good Morning / Good Night (original) | 3 (frases comunes; no verificado) | 2 / 5 | 3 | 4 (descriptivo, pero largo) | 4 | Reemplazar |
| WINT como nombre de la suite | 2 (Wint.ai, crate wint, PyPI y npm ocupados) | 3 / 3 | 4 | 3 | 2 (desnudo) / 4 (con prefijo) | Usable en privado; revisar antes de publicar |
| Osi como nombre de módulo | 1 (Open Source Initiative, modelo OSI) | 4 / 2 | 3 | 2 | 3 | Mantener solo como módulo interno; considerar renombrar si se hace público |

1. Mantener "Sol" y "Luna" como nombres de cara al usuario (en lugar de Sun/Moon o Good Morning/Good Night), siempre precedidos por el nombre de la suite en títulos, menús y notificaciones ("WINT Sol", "WINT Luna"). Por qué: son coherentes con una persona hispanohablante y con el simbolismo día/noche, y el prefijo reduce la confusión con Amazon Luna, Solana, Terra y los modelos de OpenAI (H12 a H15, H23). Sun/Moon no ofrece ventaja real: las palabras sueltas también están ocupadas en todos los registros (H10) y suenan menos naturales en una interfaz rioplatense.
2. Usar identificadores internos en ASCII y en minúsculas: `wint`, `sol`, `luna`, `osi`, expuestos como subcomandos (`wint sol`, `wint luna`) o submódulos de un espacio de nombres `wint`; si un día se publica un paquete, usar `wint-sol`, `wint-luna`, `wint-osi` (libres hoy en PyPI y npm, H5) y nunca `sol`, `luna`, `sun`, `moon` ni `wint`. Por qué: los nombres desnudos están tomados (H3, H10) y el ASCII evita fallos de codificación en rutas, tareas programadas y APIs.
3. No publicar nada en PyPI, npm o crates.io con el nombre `wint` desnudo, y tratar "WINT" como nombre de trabajo para uso privado hasta hacer la búsqueda de marcas. Por qué: ya existen Wint (wint.ai, H1), el crate `wint` (H2), un paquete PyPI `wint` (H3) y un npm `wint`; el nombre es débil para posicionarse y arriesga confusión con una empresa con financiamiento. Si el software se hace público o comercial, evaluar un nombre más distintivo antes de invertir en identidad visual.
4. Ejecutar la lista de verificación de marcas (H22) antes de cualquier lanzamiento público o comercial: INPI Argentina, WIPO Global Brand Database, TMview y USPTO, clases 9, 35 y 42, buscando "WINT", "Osi", "Sol" y "Luna" con variantes fonéticas; hablar con un agente de la propiedad industrial. Por qué: no pude verificar ninguna fuente oficial, y hay titulares activos en el mismo rubro (Wint en 9/42, OpenAI, Amazon).
5. Reconsiderar el nombre "Osi" si el módulo va a ser visible: elegir un nombre que no sea una sigla de tres letras con significados dominantes (Open Source Initiative y modelo OSI de redes, H6 y H7), o presentarlo siempre como "WINT Osi" con descripción de función; nunca escribirlo en mayúsculas ni sugerir que es "OSI-approved". Por qué: el posicionamiento en buscadores será casi imposible y OSI podría objetar usos que sugieran aval (política de marca de OSI no verificada).
6. Reservar solo lo que se vaya a usar y verificarlo de nuevo el mismo día: en GitHub, `wint-app` y `getwint` figuran libres (H5; `wintapp` ya existe desde el 22/9/2026, titular desconocido); para dominios, `wint.com.ar`, `wint.ar` y las variantes con prefijo figuran sin delegación (H4), pero hay que confirmarlo en NIC Argentina antes de contar con ellos. Por qué: la disponibilidad cambia por día y el DNS no equivale a WHOIS.
7. Definir la paleta como tokens de modo claro y oscuro (por ejemplo ámbar dorado #F5A524 para Sol y azul lunar #9DB4E8 para Luna sobre fondos oscuros, ambos por encima de 8:1 de contraste) y reservar el naranja exclusivamente para el estado "trabajando" del Detector; distinguir Sol y Luna también por forma de ícono (sol con rayos, media luna) y no solo por color (H21). Por qué: evita ambigüedad de estados en la bandeja del sistema y cumple el contraste mínimo de 4.5:1.
8. Adoptar Lucide (`sun-moon` para la suite, `sunrise`, `moon-star` y compañía para los módulos) como set de íconos, con la licencia ISC incluida en el repositorio (H20). Por qué: licencia permisiva, versiones activas (1.52.0 el 4/10/2026) y cobertura del par día/noche.
9. Modelar Sol y Luna como estados de un reloj solar con desplazamientos, copiando el vocabulario probado de Home Assistant (`above_horizon`/`below_horizon`, eventos `sunrise`/`sunset` con `offset` tipo "-01:00:00") y calcular amanecer y atardecer con una biblioteca local como astral, skyfield o suntime (H19, herramientas). Por qué: mantiene el comportamiento determinista, explicable y sin conversación que se pide para WINT, y evita depender de un servicio externo.
10. Evaluar la integración con Auto Dark Mode antes de reimplementar el cambio de tema: es GPL-3.0, tiene versión 11.1.1 y soporta scripts (H18). Por qué: el caso "Sol = cambiar a modo día" ya está resuelto; WINT puede concentrarse en las rutinas que Windows no ofrece (cerrar apps, guardar sesiones, ejecutar al arrancar el Detector) en lugar de duplicar lo existente.
11. Registrar la decisión de nombres en una ficha de una página con fecha (nombres elegidos, IDs, resultados de H3 a H11) y repetir las consultas de registros y DNS antes de publicar. Por qué: casi todo lo verificado cambia con el tiempo (el crate `wint` apareció el 6/10/2026, un día antes de esta consulta) y la ficha sirve de prueba de buena fe ante un conflicto.
12. Mantener un vigilante del repositorio `aunai-org/wint` y de la organización `wint-ai` si se piensa publicar: son los dos lugares donde el nombre "wint" tiene actividad activa en 2026 (H1, H2). Por qué: una colisión conceptual (motor determinista de ventanas con `is_day`) podría crecer y conviene saberlo antes de anunciar.

## Qué no se pudo verificar

- Presupuesto de búsquedas web: la sesión alcanzó el límite de WebSearch (200 por turno, compartido) antes de la primera consulta; todo se hizo con registros de paquetes (PyPI, npm, crates.io, RubyGems, NuGet, Docker Hub), GitHub (WebFetch y herramientas MCP) y consultas DNS. No se usaron buscadores por otras vías.
- Bloqueos de red (política de la organización): opensource.org, en.wikipedia.org y es.wikipedia.org, www.wipo.int y branddb.wipo.int, www.inpi.gob.ar, www.argentina.gob.ar, nic.ar, tmdn.org, euipo.europa.eu, tmsearch.uspto.gov, www.amazon.com, www.pokemon.com, solana.com, learn.microsoft.com, support.microsoft.com, www.wint.ai y wint.ai, platform.openai.com, justgetflux.com, store.steampowered.com, play.google.com, peps.python.org, RDAP (rdap.org y rdap.verisign.com). La página de Oracle respondió 403. El sitio npmjs.com respondió 403 y las páginas HTML de PyPI no cargaron en la herramienta (se usó la API JSON).
- Marcas en Argentina (INPI): costos, plazos, vigencia, procedimiento de oposición, clases de Niza aplicables y adhesión de Argentina a sistemas internacionales (como el Protocolo de Madrid): sin fuente oficial abierta; lo anotado en H22 es conocimiento general con confianza baja. Tampoco se verificó que "WINT", "Osi", "Sol" o "Luna" estén registrados como marca de software en ninguna oficina.
- Wint (wint.ai): razón social ("Wint Water Intelligence"), año de fundación, sede, financiamiento y clases de marca: solo hay fuentes secundarias (perfil de API Evangelist y organización GitHub). La sede en Israel proviene del perfil de la organización GitHub.
- Titularidad de `github.com/wintapp` (cuenta del 22/9/2026) y de la cuenta `aunailab`/`aunai-org` (creadas en septiembre y octubre de 2026): se desconoce si pertenecen a la persona que encarga el informe o a terceros.
- Disponibilidad real de dominios: el DNS no equivale a WHOIS/RDAP. Los NXDOMAIN para `.ar` y `.com.ar` deben confirmarse en NIC Argentina; precio y requisitos de registro de `.ar` no se consultaron. Los ámbitos de npm (`@wint`, `@osi`, `@sol`, `@luna`), las organizaciones de PyPI y las organizaciones de Docker Hub no se pudieron comprobar.
- Amazon Luna (fecha de lanzamiento, disponibilidad por país incluida Argentina, estado actual), Pokémon Sun/Moon (fecha de lanzamiento, plataformas, título oficial en español "Sol y Luna"), Sun Microsystems/Oracle (fecha de adquisición, titularidad actual de la marca Sun), Moon+ Reader (app de lectura para Android) y el ticker SOL de Solana: no se pudieron abrir fuentes primarias; solo hay evidencia indirecta de GitHub o conocimiento general de confianza baja.
- Marcas o negocios argentinos y latinoamericanos llamados Sol o Luna en software (por ejemplo, empresas, bancos, aerolíneas, parques o apps locales): no se pudo investigar; "Sol" y "Luna" son palabras y nombres propios muy comunes en español, de modo que la saturación de marca es probable pero no está medida.
- OSI: política de marca y de uso de la sigla "OSI" y "Open Source" (opensource.org bloqueado); solo se verificó la existencia de la organización y de sus repositorios de GitHub. La definición formal del modelo OSI (ISO/IEC 7498) no se abrió.
- OpenAI: la documentación comercial y los anuncios de los modelos Sol/Terra/Luna no se abrieron; la evidencia es el código, las pruebas y los documentos del repositorio `openai/codex` (commit 406eb53). El estado de esos nombres puede haber cambiado.
- f.lux y la documentación oficial de Windows Night Light (versiones, funciones, API): no se abrieron; solo una mención en el README de Redshift.
- Íconos: no se abrieron `sun`, `moon` ni `sunset` de Lucide, ni los íconos de Tabler ni los de Octicons (el resumen automático de Octicons fue incoherente).
- Pronunciación y memorabilidad: son juicios del analista; no hay encuesta ni dato medido.
