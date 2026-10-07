# Complemento: Nombres (WINT, Osi, Sol y Luna), marcas INPI y dominios .ar

Fecha de la consulta: 7 de octubre de 2026. Presupuesto de WebSearch: 18 de 18 consultas usadas (todas en modo "standard"). WebFetch se probó una vez sobre una URL clave (https://www.argentina.gob.ar/normativa/nacional/norma-424092/texto, Resolución INPI 75/2026) y dio EGRESS_BLOCKED; no se insistió. Se usaron además: WebFetch de https://raw.githubusercontent.com/aunai-org/wint/master/README.md (funcionó) y consultas JSON a crates.io y PyPI (funcionaron).

Advertencia metodológica: el buscador devuelve resúmenes redactados, no el texto crudo de las páginas. Las "citas" de abajo son extractos de esos resúmenes, y las URLs son las que el buscador listó (a veces solo se vio el título). Donde la página oficial no se pudo abrir, se dice.

Estado por pregunta: Q1 RESUELTA, Q2 PARCIAL (Amazon Luna en Argentina sin resolver), Q3 RESUELTA, Q4 PARCIAL (valor de la UMAPI de octubre y URL exacta del buscador de marcas sin resolver), Q5 PARCIAL (dos escalas de tarifas en las fuentes; dominios solo por indicio).

---

## Q1. "Wint": wint.ai, crate `wint`, `aunai-org/wint`, `wintapp`, PyPI

### Respuesta
1. wint.ai es WINT Water Intelligence: empresa israelí de gestión de agua y detección de fugas (software con IA más hardware conectado que avisa de una fuga y, si se configura, corta el suministro). Sede en Tel Aviv. Es una empresa financiada, no un proyecto de aficionados: Serie B de USD 15 millones (Insight Partners y empresas inmobiliarias) y Serie C de USD 35 millones (agosto de 2023, con Insight Partners e Inven Capital). Clientes que la propia empresa declara: Microsoft, Google, Mastercard, HP y Dell.
2. Tamaño: unos 122 empleados según directorios de datos (bitscale.ai, startuphub.ai); dato de fuente débil. Año de fundación: un extracto dice 2011; no se pudo contrastar, no conviene publicarlo.
3. Otro software o empresa "Wint" en escritorio, automatización, precios o Android: una búsqueda específica (Wint app Windows Android price tracker automation) no devolvió ninguna aplicación llamada Wint; solo trackers de precios genéricos. Es un resultado negativo de una búsqueda, no una prueba de ausencia. Lo ya conocido de la primera ronda sigue vigente: un usuario de GitHub "Wint" (Winton Wint, China), el usuario de Docker Hub `wint`, y el nombre ocupado en PyPI, npm y crates.io.
4. Crate `wint` (crates.io): versión 0.1.0, creada el 2026-10-06T09:59:58Z, 7 descargas, descripción "Deterministic, explainable engine that finds the time windows when a job can run within the limits you set", repositorio https://github.com/aunai-org/wint (consulta directa a la API de crates.io hoy). El README (leído hoy en raw.githubusercontent.com) dice: "wint finds the time windows when a job can run, given the limits you set, and explains why the others cannot." Es un motor determinista en Rust, compilable a WebAssembly, que analiza datos con marca de tiempo ("forecasts, metrics, prices") contra un plan de restricciones y devuelve ventanas factibles ordenadas con evidencia. Usos que menciona: pronósticos del tiempo, ventanas de despliegue de servidores, carga de vehículos eléctricos, horneado de panadería. El README no identifica al autor. El crate tiene un día de vida: es cercano en concepto a una rutina Sol/Luna ("cuándo conviene correr algo"), pero no hay evidencia de que sea de la persona que encarga el informe.
5. PyPI `wint` 0.2.0: "Dependency injection with type hints", Stanislav Lobanov, hogar https://github.com/asyncee/wint (reconsultado hoy; coincide con la primera ronda).
6. `wintapp` en GitHub: usuario creado el 22/9/2026 con 0 repositorios (dato de la verificación de la primera ronda; no se reconsultó). Titular desconocido.
7. Riesgo de confusión para un software personal llamado WINT (valoración propia):
   - Uso personal o privado: bajo.
   - Búsquedas y tiendas de aplicaciones: alto. "WINT" a secas lleva primero a WINT Water Intelligence (misma escritura en mayúsculas, mismo nombre exacto, rubro de IA y monitoreo con aplicación móvil propia) y, en desarrolladores, a los paquetes homónimos.
   - Si se publica o comercializa software: medio a alto en las clases 9 y 42, porque hay una empresa financiada con el mismo signo exacto en software e IoT. No se pudo comprobar si WINT Water Intelligence tiene marca registrada en Argentina o en otra oficina; esa es la comprobación que decide.
   - Técnico: el crate `wint` instala un binario llamado `wint`; un comando propio `wint sol` / `wint luna` chocaría en el PATH si alguien instala ese crate.

### Evidencia
- Extracto del buscador sobre WINT Water Intelligence: "water intelligence company founded in Israel ... AI-enabled software and connected hardware that alerts users when there may be a leak, with the ability to configure the system to automatically shut down where the leak is detected"; "headquartered in Tel Aviv"; "$15 million Series B funding round from Insight Partners"; Serie C "$35 million ... Insight Partners has co-led ... alongside ... Inven Capital". Fuentes listadas: https://undergroundinfrastructure.com/news/2023/august/wint-raises-35-million-to-propel-ai-driven-leak-detection-solutions (agosto de 2023), https://www.aquatechtrade.com/water-stories/industrial-water/wint-has-secured-15-million-in-series-b-funding (Serie B), https://esgnews.com/?p=22043 (Serie C), https://bitscale.ai/directory/wint-water-intelligence y https://www.startuphub.ai/startups/wintwi.md (directorios; headcount), https://slimpages.startupim.com/neo_company_page/wint-water-intelligence. Consulta del 7/10/2026. wint.ai y los sitios oficiales siguen bloqueados.
- README de `aunai-org/wint`: https://raw.githubusercontent.com/aunai-org/wint/master/README.md (7/10/2026).
- Crate: https://crates.io/api/v1/crates/wint (7/10/2026): creado y actualizado el 2026-10-06T09:59:58Z, una sola versión, 7 descargas.
- PyPI: https://pypi.org/pypi/wint/json (7/10/2026).
- Búsqueda de otro "Wint" en software/Android/precios: sin resultado (consulta del 7/10/2026).

### Confianza
- Existencia, rubro, sede y financiamiento de WINT Water Intelligence: media a alta (varias notas de prensa especializada y directorios coherentes entre sí; sitio oficial no abierto).
- Headcount de 122 y año 2011: baja.
- Crate `wint` y PyPI `wint`: alta (APIs oficiales y README leídos hoy).
- Ausencia de otro "Wint" en escritorio/Android/precios: baja a media (una sola búsqueda).
- Valoración de riesgo: opinión del analista.

### Contradice o corrige
- CORRIGE el tono de `nombres_marca.verificado.md`, corrección clave 2(b), y de `nombres_marca.md` H1: allí el respaldo de Insight Partners se tenía por débil (perfil automático "stub" de API Evangelist). Ahora hay notas de prensa especializada independientes que lo confirman (Serie B y Serie C). Ya se puede afirmar el financiamiento, con la salvedad de que se lee en extractos de búsqueda y no en el sitio de la empresa.
- COMPLETA H1 con sede (Tel Aviv), tamaño aproximado y clientes declarados, que la primera ronda dio por no verificables.
- CONFIRMA H2 y H3 (crate y PyPI) sin cambios.

---

## Q2. "Sol" y "Luna": OpenAI, Amazon Luna, software con esos nombres

### Respuesta
1. REAL y mejor datado que en la primera ronda. OpenAI usa Sol, Terra y Luna como nombres de modelos:
   - Serie GPT-5.6 (Sol, Terra y Luna): anunciada con fecha de salida el 9 de julio (título del hilo oficial de OpenAI Developer Community: "Introducing GPT-5.6 series: Sol, Terra and Luna. Coming July 9 10am PT"); 9to5Mac informó de un lanzamiento limitado el 26/6/2026.
   - GPT-6 Astra (el modelo más grande), y GPT-6 Sol y GPT-6 Luna, lanzados el 22 de septiembre de 2026 (TechCrunch, 22/9/2026: "OpenAI launches GPT-6 Sol and Luna, boasting lower cost and fewer mistakes"; 9to5Mac, 22/9/2026).
   - GPT-6.1 Sol, lanzado el 29 de septiembre de 2026 en DevDay (TechCrunch, 29/9/2026: "OpenAI launches GPT-6.1 Sol, says it nearly matches GPT-6 Astra and costs less"). Es decir, "Sol" es el nivel de trabajo actual, no un nombre viejo.
   - Roles: Astra es el más capaz; Sol, el intermedio para programación compleja y flujos con agentes; Luna, el rápido y barato para tareas de alto volumen ("summarizing documents, extracting information, or answering quick questions"). Terra pertenece a la serie 5.6, no hay un GPT-6 Terra según el resumen de un blog. Precios por millón de tokens (fuentes secundarias): GPT-6 Sol 2 y 10 dólares, GPT-6 Luna 0,10 y 0,50, Astra 10 y 50.
   - Disponibilidad: ChatGPT Work, Codex y API; Luna también para usuarios gratuitos en la app de escritorio.
2. Amazon Luna (juegos en la nube): sigue operando en 2026 (nota de un medio argentino, "amazon luna nuevos videojuegos abril 2026", culturageek.com.ar). Países con disponibilidad oficial en 2025-2026 según un agregador de suscripciones (fuente débil): Estados Unidos, Reino Unido, Alemania y Canadá; hubo expansión previa a Francia, Italia y España (wccftech, sin fecha vista). Argentina: un medio argentino (nota de lanzamiento de 2020) dice que no está disponible oficialmente y que se accede con una cuenta de Amazon de EE. UU.; la verificación de la primera ronda halló un README de terceros con "currently US clients only". No se halló ninguna fuente oficial de 2026 sobre Argentina: SIN RESOLVER.
3. Software conocido con esos nombres en automatización, rutinas o escritorio:
   - Luna (adrianmteo/luna): "lightweight automatic theme changer for Windows 10", programa horarios para tema claro y oscuro y fondo de pantalla; proyecto descontinuado en 2020 según el extracto. Es lo más cercano a una rutina "Luna" y ya existe con ese nombre en Windows (Softpedia).
   - Sol (ospfranco/sol): lanzador de aplicaciones de código abierto, "focused on ease of use and speed", con comandos AppleScript, gestor de ventanas y portapapeles; es para macOS.
   - Resultados de baja calidad al buscar "Luna" más "download" (sitios de "Luna Executor"): señal de ruido de búsqueda en descargas de software con ese nombre.
   - No se encontró ningún producto de automatización o rutinas llamado "Sol" ni el par "Sol y Luna" (resultado negativo).
   - La primera ronda ya había documentado: PyPI `sol` (Carrom), PyPI `luna` (descubrimiento de fármacos), tokens SOL (Solana) y LUNA/LUNC (Terra), Pokémon Sol/Luna (nombres en español según PokéAPI).
4. Implicación: en el ámbito de IA y desarrollo, "Sol" y "Luna" evocan hoy modelos de OpenAI; si WINT usa modelos de lenguaje, un identificador `sol` o `luna` en configuración se confundiría con los modelos `gpt-6-sol` y `gpt-6-luna`. Conviene el prefijo: "WINT Sol" y "WINT Luna", con identificadores `wint.sol` y `wint.luna`.

### Evidencia
- OpenAI, título de la página oficial listada por el buscador: "Introducing GPT-6 Sol and Luna", https://openai.com/index/introducing-gpt-6-sol-and-luna/ (no se abrió; se vio el título y un resumen). Hilo oficial: https://community.openai.com/t/announcing-gpt-6-sol-and-gpt-6-luna-in-the-api-codex-and-chatgpt/1399925 . Hilo de la serie 5.6: https://community.openai.com/t/introducing-gpt-5-6-series-sol-terra-and-luna-coming-july-9-10am-pt/1384931 . Prensa: https://techcrunch.com/2026/09/22/openai-launches-gpt-6-sol-and-luna/ ; https://9to5mac.com/2026/09/22/openai-upgrading-chatgpt-and-codex-with-two-more-gpt-6-models/ ; https://techcrunch.com/2026/09/29/openai-launches-gpt-6-1-sol-says-it-nearly-matches-gpt-6-astra-and-costs-less/ ; https://9to5mac.com/2026/06/26/openai-upgrading-chatgpt-and-codex-with-new-gpt-5-6-models-in-limited-release/ ; https://computingforgeeks.com/gpt-6-sol-luna-released-features-benchmarks/ (precios) ; https://tecnoblog.net/noticias/openai-expande-gpt-6-com-modelos-sol-e-luna-vejas-as-diferencas/ . Consulta del 7/10/2026.
- Amazon Luna: https://culturageek.com.ar/amazon-luna-nuevos-videojuegos-abril-2026/ (título); https://culturageek.com.ar/amazon-luna-todo-lo-que-tenes-que-saber-del-servicio-de-streaming-de-videojuegos-de-amazon-que-ya-arranca-en-ee-uu/ (nota de 2020); https://subger.com/en/cloud-gaming (agregador); https://wccftech.com/amazon-luna-cloud-gaming-expands-to-italy-france-and-spain/amp/ .
- Software: https://www.softpedia.com/get/Desktop-Enhancements/Other-Desktop-Enhancements/Luna-Mateoaea.shtml ; https://awesome.ecosyste.ms/projects/github.com%2Fadrianmteo%2Fluna ; https://github.com/ospfranco/sol . Consulta del 7/10/2026.

### Confianza
- OpenAI: alta. Página oficial y hilos oficiales listados más dos medios independientes coherentes en fechas (22/9 y 29/9/2026). Solo se vieron títulos y resúmenes.
- Precios de los modelos: media (fuente secundaria).
- Amazon Luna sigue activo en 2026: media. Países: baja a media. Argentina: baja (sin fuente oficial).
- Software Luna/Sol: media (fichas de descarga y GitHub). Resultado negativo del par Sol/Luna: baja a media.

### Contradice o corrige
- CONFIRMA `nombres_marca.md` H12 y la corrección clave 1 de `nombres_marca.verificado.md`: "Sol" es vigente (GPT-6.1 Sol, 29/9/2026), no un nivel viejo; la primera ronda había basado todo en el repositorio `openai/codex` y ahora hay página oficial y prensa. La duda de esa verificación (que `latest-model.md` no listara Sol) queda como una discrepancia interna del repositorio, probablemente de desfase de documentación; la fuente oficial sí lista Sol.
- PRECISA: Terra existe solo en la serie 5.6 (extracto de un blog); en H12 se menciona "GPT-6-Astra ... Terra" sin separar series.
- No contradice H15 (Amazon Luna en Argentina sigue sin confirmar), pero añade que el servicio sigue vivo en 2026 y que un medio argentino lo describía como no oficial en el país.
- COMPLETA H10/H11: Luna ya era un cambiador automático de tema para Windows 10 (descontinuado en 2020) y Sol un lanzador de macOS.

---

## Q3. "Osi": Open Source Initiative, modelo OSI, otro software

### Respuesta
1. Open Source Initiative (OSI): "OSI", "Open Source Initiative", el logotipo y "OSI Approved Open Source License" son marcas que la organización protege. El logotipo "keyhole" y su marca denominativa están registrados en la USPTO para promoción pública de software no propietario (clase 35) y servicios educativos sobre software no propietario (clase 41). Su política exige aprobación escrita para usar marcas de OSI en nombres de dominio y para bienes que no sean software; prohíbe marcas "confusingly similar", traducir o alterar las marcas, y combinar nombres de empresa con nombres de OSI de modo que sugiera vínculo. Consecuencia: un producto de software llamado "Osi" (mismas cuatro letras sin distinguir mayúsculas, misma pronunciación) cae en el área de la política de marca de OSI, sobre todo si se distribuye bajo licencia de código abierto. Riesgo: medio a alto si se publica o comercializa; no es un problema para uso privado.
2. Modelo OSI (Open Systems Interconnection, siete capas): no se buscó en esta ronda. La primera ronda halló repositorios de GitHub que lo describen (H7, verificado). Conocimiento general: es un estándar ISO/IEC 7498-1, nombre muy establecido en redes. El efecto es de ruido de búsqueda, no de marca.
3. Software "Osi" conocido de automatización o asistente: una búsqueda dirigida (Osi AI assistant app automation) no devolvió ninguno. Devolvió nombres parecidos, como "Oi - AI Assistant" (iPhone), "OsmO - AI Phone Assistant", "Aisi Assistant" y "Omi AI". Resultado negativo de una sola búsqueda. Por su parte, la verificación de la primera ronda halló npm `osi` (14.4.12), crates.io `osi` (0.0.1, 8.072 descargas) y un usuario de GitHub `osi` (Peter Royal).

### Evidencia
- Política de marca de OSI (extracto del buscador): "The OSI 'Keyhole Logo' ... registered with the United States Patent and Trademark Office for public advocacy promoting non-proprietary software (Class 35) and educational services related to non-proprietary software (Class 41)"; usos que requieren aprobación escrita: "using OSI Trademarks in domain names"; usos prohibidos: "use confusingly similar marks". URLs listadas: https://opensource.org/about/brand-and-trademark-guidelines , https://opensource.org/wp-content/uploads/2009/08/TrademarkGuidelines.pdf (documento de 2009), https://wiki.opensource.org/bin/Operations/Trademarks/ . La página oficial no se abrió (bloqueada); la política vigente puede haber cambiado desde el PDF de 2009, pero la primera URL es la página actual de OSI. Consulta del 7/10/2026.
- Búsqueda de "Osi" asistente: https://apps.apple.com/us/app/id6462895560 (Oi), https://alternativeto.net/software/osmo--ai-phone-assistant/about/ , https://hunted.space/product/omi-ai (7/10/2026).

### Confianza
- Política y marcas de OSI: media a alta (sitio oficial listado y coherente en varios resultados; página no abierta).
- Ausencia de un "Osi" asistente conocido: baja a media.
- Valoración de riesgo: opinión del analista.

### Contradice o corrige
- CIERRA lo que `nombres_marca.md` H6 y `nombres_marca.verificado.md` (puntos "política de marca de OSI: no verificada") dejaron abierto: la política existe y menciona dominios y marcas confundibles.
- La inferencia de H6 ("un producto llamado Osi invita a confusión y a que la organización cuestione usos que sugieran aval") queda respaldada por la política.
- COMPLETA con el dato de las clases del registro de OSI en la USPTO (35 y 41, no 9 ni 42): el solapamiento formal de clases con software sería limitado, pero la política de OSI no depende de la clase.

---

## Q4. Registro de marcas en Argentina (INPI): búsqueda, tasa 2026, duración, clases

### Respuesta
1. Tasa 2026: la Resolución INPI 75/2026, publicada en el Boletín Oficial el 20 de marzo de 2026 (aviso 339726), creó la UMAPI (Unidad de Medida Arancelaria de la Propiedad Industrial) y actualizó los aranceles. La solicitud de una marca nueva en una clase, con hasta 20 productos o servicios, cuesta 100 UMAPI. Valor inicial de la UMAPI: $360, o sea $36.000 por clase. Cada indicación adicional por encima de 20 suma 4 UMAPI. La nueva estructura rige formalmente desde el 1 de mayo de 2026 (un resumen decía 1 de abril; hay que confirmarlo). La UMAPI se ajusta mensualmente por el IPC del INDEC y su valor debe publicarse en el portal de trámites del INPI. Según notas de mayo de 2026, 1 UMAPI = $372,24, es decir unos $37.224 por clase. El valor de octubre de 2026 no se obtuvo: SIN RESOLVER.
   - Cuenta orientativa para las tres clases (9, 35 y 42): 300 UMAPI, unos $108.000 con el valor inicial y unos $111.672 con $372,24 (valor de mayo; el de octubre será mayor por el ajuste mensual). No se confirmó si hay tasas posteriores (por ejemplo por oposición o renovación): SIN RESOLVER.
2. Duración del trámite: aproximadamente 20 meses (extracto de una página de Presidencia de la Nación sobre el trámite de marcas). Es el plazo típico, no una garantía; no se halló información sobre el plazo de oposición en esta ronda.
3. Cómo se busca: el INPI ofrece (a) un módulo gratuito de búsqueda por caracteres idénticos, (b) búsquedas aranceladas de antecedentes fonéticos en bases nacionales e internacionales, solicitadas al área de Información Tecnológica, y (c) TMview: desde 2017 el INPI participa en esta plataforma gratuita, disponible las 24 horas, con datos actualizados diariamente de las oficinas nacionales participantes. La URL exacta del módulo gratuito no apareció en los extractos: SIN RESOLVER (las pistas son el portal de trámites del INPI y TMview).
4. Clasificación de Niza: desde el 1 de enero de 2026 el INPI aplica la 13.ª edición de la Clasificación de Niza, de forma automática según la Resolución 233/2023. La edición traslada productos entre clases (por ejemplo, lentes y anteojos salen de la clase 9) y, según los extractos, no modifica clases de servicios (35 y 42).
   - Clases relevantes (conocimiento previo, no verificado en esta ronda; confirmar en la base oficial https://nclpub.wipo.int/esfr): 9 para software descargable y aplicaciones móviles; 42 para software como servicio y desarrollo de software; 35 para servicios comerciales, entre ellos la comparación de precios (Detector de precios). Una solicitud cubre una clase: tres clases son tres solicitudes de tasa.
   - Matiz: la vigencia de 10 años renovables (Ley 22.362, art. 5) viene de conocimiento previo de la primera ronda; no se reverificó.

### Evidencia
- Extracto del buscador: "La solicitud de registro de una marca nueva (hasta 20 productos/servicios) se fija en 100 UMAPI ($36.000)"; "El 20 de marzo de 2026 se publicó en el Boletín Oficial la Resolución 75/2026 del ... INPI"; "La implementación de la nueva estructura estará vigente formalmente desde el 1° de mayo de 2026"; "se tomará como referencia el ... IPC publicado mensualmente por el INDEC"; "El valor actualizado de la UMAPI deberá publicarse de forma obligatoria en el portal de trámites del INPI". URLs: texto oficial https://www.argentina.gob.ar/normativa/nacional/norma-424092/texto (título "Resolución 75 / 2026"; EGRESS_BLOCKED al abrirlo); https://www.boletinoficial.gob.ar/detalleAviso/primera/339726/20260320 ; notas de estudios: https://abogados.com.ar/resolucion-752026-creacion-de-la-umapi-y-actualizacion-de-aranceles-del-inpi/38776 , https://abogados.com.ar/la-unidad-de-medida-arancelaria-de-la-propiedad-industrial-umapi-resolucion-inpi-752026/38789 , https://abogados.com.ar/actualizacion-de-aranceles-del-inpi-y-creacion-de-la-unidad-de-medida-arancelaria-de-la-propiedad-industrial-umapi/38862 , https://beccarvarela.com/novedades/actualizacion-de-aranceles-del-inpi-y-creacion-de-la-unidad-de-medida-arancelaria-de-la-propiedad-industrial-umapi/ (6/4/2026). Costo y UMAPI de $372,24 (mayo de 2026): https://www.esderecho.com.ar/cuanto-cuesta-registrar-marca-argentina-2026/ , https://developargentina.com/blog/registrar-marca-argentina-inpi-2026 (25/3/2026), https://developargentina.com/blog/registrar-marca-inpi-argentina-costos-pasos-2026 (9/7/2026), https://www.iprofesional.com/legales/450317-cuanto-cuesta-registrar-una-marca-en-el-inpi-y-que-factores-influyen-en-el-precio (23/6/2026). Consulta del 7/10/2026.
- Búsqueda y duración: "La duración del trámite es de aproximadamente 20 meses"; "Desde el 2017 el INPI es parte de TMView ... uso gratuito y disponible las veinticuatro (24) horas": https://www.argentina.gob.ar/node/230501 ; guía de 12/6/2026: https://www.iprofesional.com/legales/450840-como-saber-si-una-marca-ya-esta-registrada-en-el-inpi-guia-practica-para-emprendedores ; material del INPI para cursos: https://utn.edu.ar/images/Secretarias/SCTYP/UGEPI1/vtpcua/Marcas_Modulo-2-Dr-Sosa-INPI.pdf (no leído).
- Niza 13: "Desde el 1.º de enero de 2026, el INPI aplica la 13.ª edición de la Clasificación de Niza ... Resolución 233/2023": https://www.marval.com/Publicacion/argentina-rige-la-13a-edicion-de-niza-17438 ; https://abogados.com.ar/novedades-nueva-clasificacion-niza-ed-13-a-partir-de-enero-de-2026/38287 (7/10/2026).

### Confianza
- 100 UMAPI por clase y UMAPI inicial de $360: alta (resolución oficial identificada por título y fecha, más cuatro notas de estudios jurídicos coherentes).
- Valor de $372,24 en mayo de 2026: media (notas de prensa y blogs; no es el valor de octubre).
- Fecha de vigencia: media (1 de mayo según varias notas; un resumen decía 1 de abril).
- Duración de 20 meses y descripción de la búsqueda: media (página oficial pero no abierta, más una guía de prensa).
- Niza 13 desde enero de 2026: alta (dos fuentes de estudios de PI coherentes).
- Asignación de productos a clases 9, 35, 42: baja a media (conocimiento previo).

### Contradice o corrige
- CORRIGE `nombres_marca.md` H22 y `nombres_marca.verificado.md` corrección clave 8 ("El informe no debe dar aranceles ni plazos"): ya hay fuente para ambos. El arancel por clase y el plazo aproximado pueden darse con las salvedades de arriba.
- COMPLETA la lista de verificación de H22: la edición de Niza aplicable es la 13.ª y el INPI ofrece búsqueda gratuita por caracteres idénticos, búsqueda fonética arancelada y TMview.
- No toca: adhesión de Argentina al Protocolo de Madrid (no se buscó, SIN RESOLVER) ni la existencia de marcas registradas con WINT, Osi, Sol o Luna.

---

## Q5. NIC Argentina (.ar y .com.ar): reglas, costo 2026, wint.com.ar / wint.ar

### Respuesta
1. Reglas: se necesita CUIT o CUIL y Clave Fiscal; los trámites de dominios requieren Clave Fiscal nivel 2 o superior, y se hacen en "Trámites a Distancia". Un dominio dura 1 año desde su registro y se renueva: la renovación procede desde 30 días corridos antes del vencimiento hasta el último día del período de gracia. Desde 2019 se pueden registrar dominios .ar con cualquier combinación de 4 letras o más. "wint" tiene 4 letras: wint.ar es una combinación permitida. "osi" tiene 3: no se verificó si osi.ar puede registrarse libremente.
2. Costo (en pesos, anual): $8.500 por alta, renovación y transferencia para .com.ar, .net.ar, .tur.ar y otras zonas del mismo grupo; $25.500 para .ar; $28.800 por disputa en las zonas del primer grupo; $64.000 para .bet.ar. Los resultados también mostraban una escala anterior mucho menor ($855 .com.ar y $1.710 .ar, disputa $7.200), que no sería la vigente. Cifra más probable para 2026: $8.500 (.com.ar) y $25.500 (.ar). Confirmar en https://nic.ar/es/dominios/aranceles antes de publicarla.
3. ¿wint.com.ar o wint.ar registrados? La búsqueda de "wint.com.ar dominio" no devolvió ninguna página sobre ese dominio: sin dato. Único indicio: la consulta DNS de la primera ronda (7/10/2026) mostró que ni wint.ar ni wint.com.ar tienen delegación (NXDOMAIN); eso no prueba que estén libres, porque un dominio puede estar registrado sin servidores de nombres. SIN RESOLVER; la prueba válida es la consulta en nic.ar con CUIT y Clave Fiscal.

### Evidencia
- Extracto del buscador sobre nic.ar: "Para registrar dominios en las zonas .ar y .com.ar se requiere CUIT y Clave Fiscal"; "Clave Fiscal Nivel 2 o superior"; "Un dominio tiene una validez de 1 (un) año"; "La zona .ar ... $25.500 para alta y renovación anual, mientras que .com.ar y .net.ar cuestan $8.500". URLs listadas: https://nic.ar/es/dominios/aranceles , https://nic.ar/es/ayuda/faq , https://nic.ar/es/ayuda/instructivos/renovacion-de-dominio , https://nic.ar/es/ayuda/instructivos/registro-de-dominio , https://nic.ar/es/dominios/normativa . Prensa: https://www.iprofesional.com/tecnologia/397387-cual-es-el-costo-de-registrar-un-dominio-en-internet-en-argentina (16/7/2026) y https://www.iprofesional.com/tecnologia/300187-ya-se-pueden-registrar-dominios-ar-con-cualquier-combinacion-de-4-letras-o-mas . Lanzamiento de .ar: https://NIC.ar/sites/default/files/2019-09/Lanzamiento-de-dominios-ar_0.pdf . Nota: la búsqueda más restringida a nic.ar mostró las dos escalas de precios en el mismo resumen; la mayor aparece en la búsqueda general y coincide con la mención a .bet.ar, que es una zona reciente. Consulta del 7/10/2026.
- Consulta DNS previa: `nombres_marca.md` H4 y `nombres_marca.verificado.md` H4.

### Confianza
- Reglas (CUIT, Clave Fiscal, 1 año, renovación): media a alta (sitio oficial listado; resumen del buscador).
- Costos: media (dos escalas en los extractos; se tomó la más reciente por coherencia con .bet.ar y con el listado de prensa de 2026; sin tabla oficial abierta).
- Estado de wint.ar y wint.com.ar: baja (solo DNS).

### Contradice o corrige
- CIERRA lo que `nombres_marca.md` (limitaciones y paso 6) dejó abierto: "precio y requisitos de registro de .ar no se consultaron". Ya hay precio y requisitos con fuente.
- CONFIRMA, sin pruebas nuevas, H4: wint.ar y wint.com.ar sin delegación; sigue sin ser disponibilidad confirmada.

---

## Cambios que esto impone al informe

1. WINT (wint.ai) es WINT Water Intelligence, empresa israelí con sede en Tel Aviv, de IA y hardware para detectar fugas de agua, con rondas de USD 15 millones (Serie B) y USD 35 millones (Serie C, agosto de 2023, con Insight Partners e Inven Capital) según prensa especializada; el financiamiento ya no debe presentarse como dato débil. El año de fundación (2011 en un extracto) y los 122 empleados son de fuente débil y conviene omitirlos o marcarlos.
2. El informe debe decir que el nombre WINT tiene colisión fuerte en búsquedas y tiendas con esa empresa financiada, que el riesgo de marca en clases 9 y 42 es medio a alto si el software se publica o comercializa, y que no se pudo comprobar si esa empresa tiene marca registrada en Argentina.
3. El crate `wint` de `aunai-org` (creado el 6/10/2026, README: "finds the time windows when a job can run, given the limits you set, and explains why the others cannot") sigue siendo de titular desconocido; la composición `wint sol` / `wint luna` chocaría con su binario `wint` en el PATH, y el paquete PyPI `wint` (inyección de dependencias, 2018) sigue ocupando ese nombre.
4. "Sol" y "Luna" son hoy nombres de modelos de OpenAI con página oficial: GPT-5.6 Sol/Terra/Luna (serie con salida anunciada el 9 de julio de 2026), GPT-6 Sol y GPT-6 Luna (22/9/2026) y GPT-6.1 Sol (29/9/2026, DevDay); "Sol" no es un nombre viejo y Terra solo existe en la serie 5.6. Se recomienda escribir siempre "WINT Sol" y "WINT Luna", con identificadores `wint.sol` y `wint.luna`, para no confundirse con los modelos `gpt-6-sol` y `gpt-6-luna`.
5. Amazon Luna sigue operativo en 2026, pero ninguna fuente de esta ronda lo da como oficial en Argentina (un medio argentino lo describía como accesible solo con cuenta de EE. UU.); el informe no debe afirmar ni negar su disponibilidad en el país.
6. Ya existía un programa "Luna" para Windows 10 que cambia automáticamente entre tema claro y oscuro por horario (descontinuado en 2020) y un lanzador "Sol" de código abierto para macOS; no se halló ningún producto de rutinas llamado "Sol" ni el par "Sol y Luna".
7. "Osi" tiene colisión directa con las marcas de la Open Source Initiative: la política de OSI protege "OSI", su logotipo y "OSI Approved", exige aprobación escrita para usar sus marcas en dominios y prohíbe marcas confundibles; sus registros en la USPTO son de clases 35 y 41. No se halló un asistente o producto de automatización llamado "Osi", pero sí nombres parecidos (Oi, OsmO, Aisi, Omi AI).
8. Marcas en Argentina: la Resolución INPI 75/2026 (Boletín Oficial del 20/3/2026) fija 100 UMAPI por clase para la solicitud de una marca nueva con hasta 20 productos o servicios (UMAPI inicial de $360, o $36.000 por clase; unos $37.224 con la UMAPI de $372,24 de mayo de 2026), con ajuste mensual por IPC; cada indicación adicional suma 4 UMAPI. Para las clases 9, 35 y 42 la cuenta orientativa ronda los $108.000 a $112.000 a valores de mayo de 2026, y el valor de octubre de 2026 no se obtuvo.
9. El trámite de una marca en el INPI dura aproximadamente 20 meses según una página oficial; la búsqueda previa puede hacerse gratis por caracteres idénticos, con búsqueda fonética arancelada, y en TMview (INPI participa desde 2017). Desde el 1 de enero de 2026 rige la 13.ª edición de la Clasificación de Niza. La asignación de software a las clases 9 y 42 y de la comparación de precios a la clase 35 es conocimiento previo y debe confirmarse en la base oficial de Niza.
10. Dominios: NIC Argentina exige CUIT o CUIL y Clave Fiscal nivel 2 o superior; el dominio dura un año; los .ar admiten cualquier combinación de 4 letras o más (wint.ar califica); la tarifa más probable es de $8.500 anuales para .com.ar y $25.500 para .ar, a confirmar en nic.ar. No hay confirmación de que wint.ar ni wint.com.ar estén libres: solo no tienen delegación DNS.
11. Sigue SIN RESOLVER: titularidad de `aunai-org` y de `wintapp`; marcas registradas con WINT, Osi, Sol o Luna en cualquier oficina; valor de la UMAPI de octubre de 2026; adhesión de Argentina al Protocolo de Madrid; disponibilidad de Amazon Luna en Argentina.
