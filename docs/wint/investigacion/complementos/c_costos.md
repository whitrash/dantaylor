# c_costos: Costos, planes gratuitos y cuentas de desarrollador (segunda ronda, 7 de octubre de 2026)

Método y límites. Se usaron 18 llamadas a WebSearch (modo standard; la de Cloudflare devolvió dos tandas de resultados) y un intento de WebFetch sobre tailscale.com/pricing, que dio EGRESS_BLOCKED (no se insistió). Los límites de ntfy.sh se leyeron en los documentos oficiales del repositorio de GitHub (raw.githubusercontent.com, rama main), que no consume cupo de búsqueda. Los precios de Anthropic salen del extracto de la página oficial (docs.anthropic.com, visto vía WebSearch) y de la referencia de la API incluida en Claude Code (skill claude-api, tabla en caché del 25-sep-2026). Cuando una cifra viene solo de un extracto de búsqueda se dice. Escala de confianza: alta = fuente oficial/primaria o dos independientes coherentes; media = una fuente secundaria razonable; baja = indicio o foro.

Resumen de estado: Q1 resuelta, Q2 parcial, Q3 resuelta, Q4 parcial, Q5 resuelta, Q6 parcial.

---

## Q1. Tailscale: plan Personal vigente a octubre de 2026

Respuesta. El plan Personal es gratuito y permite hasta 6 usuarios en una misma tailnet, con dispositivos propios sin tope por usuario; incluye hasta 3 grupos de ACL y hasta 50 "recursos etiquetados" (servidores, nodos con etiqueta). Es solo para uso no comercial. Funnel está disponible en todos los planes, incluido el Personal, con límites de ancho de banda no configurables; para usarlo hay que tener HTTPS habilitado y certificados válidos en la tailnet. Serve no aparece restringido por plan en ninguno de los extractos (no hay una frase explícita que lo confirme, pero tampoco ningún indicio de que esté limitado).

Evidencia.
- Extracto de la búsqueda sobre tailscale.com/pricing: "The Personal plan is free and supports unlimited user devices with up to 6 users" y "up to 3 ACL groups and up to 50 tagged resources to start". El mismo extracto menciona también "up to 100 devices", cifra que coincide con el esquema anterior y queda en conflicto interno (ver abajo). URLs: https://tailscale.com/pricing , https://tailscale.com/docs/account/manage-plans/free-plans-discounts , https://tailscale.com/blog/pricing-v4 (fecha de la entrada no visible en el extracto; la primera ronda ya había fechado el cambio en el 08/04/2026).
- Extracto de la búsqueda sobre Funnel (docs de Tailscale): "Tailscale Funnel is available for all plans"; "Traffic sent over a Funnel is subject to non-configurable bandwidth limits"; "The Personal plan permits 6 free users in a single Tailscale network ... only suitable for non-commercial use". URLs: https://tailscale.com/docs/features/tailscale-funnel , https://tailscale.com/docs/account/manage-plans/free-plans-discounts .
- La primera ronda ya tenía, de la lectura del código del cliente en GitHub, que Funnel solo funciona en los puertos 443, 8443 y 10000 (integracion_modulos.verificado.md).

Confianza. Media-alta para los 6 usuarios y para Funnel en todos los planes (dos extractos coherentes de tailscale.com y coincidencia con la primera ronda para los 6 usuarios). Media-baja para la cifra de dispositivos: el extracto dice a la vez "ilimitados por usuario" y "hasta 100"; la lectura más consistente con "pricing v4" es dispositivos personales sin tope y un tope de 50 en recursos etiquetados, pero no se pudo leer la tabla de precios completa. Recomendación: en el informe no citar un número de dispositivos; decir "sin límite práctico para un uso personal".

Contradice o corrige a la primera ronda.
- CORRIGE integracion_modulos.md (fila de Tailscale, y la sección de H21): decía "plan Personal gratis para 3 usuarios y 100 dispositivos según agregadores; no verificado". Esa cifra es del esquema anterior; la vigente es 6 usuarios.
- CORRIGE la "contradicción sobre Funnel" de integracion_modulos.md: la fuente que decía que Funnel estaba solo en el plan Premium (18 USD por usuario por mes) estaba equivocada o desactualizada; la documentación de Tailscale dice que está en todos los planes.
- CONFIRMA shells_windows_android.md y su .verificado (6 usuarios, dispositivos propios ilimitados desde el 08/04/2026), que antes dependía de una fuente secundaria débil (costbench).

---

## Q2. ntfy, Pushover, Telegram y Cloudflare Tunnel/Access

### ntfy.sh (servicio público gratuito)

Respuesta. Límites del servicio gratuito en ntfy.sh, según la documentación oficial del proyecto: 250 mensajes por día por visitante; 5 correos por día; adjuntos de 2 MB y 20 MB en total por visitante; 200 MB de ancho de banda diario; 30 conexiones de suscripción abiertas; mensajes de hasta 4.096 bytes (los más largos se convierten en adjuntos); ráfaga de 60 pedidos y luego 1 pedido cada 5 segundos. Para uso personal con un puñado de avisos por día alcanza de sobra; para un Detector que avise muchas ofertas, 250 por día puede quedar justo.

Evidencia. Tabla "Limitations" de la documentación oficial: "On ntfy.sh, the daily message limit is 250", "On ntfy.sh, the daily limit is 5" (correos), "On ntfy.sh, the attachment size limit is 2 MB, and the per-visitor total is 20 MB", "On ntfy.sh, the daily bandwidth limit is 200 MB", "the server allows each visitor to keep 30 connections to the server open". URL: https://raw.githubusercontent.com/binwiederhier/ntfy/main/docs/publish.md (sección Limitations; lectura del 7-oct-2026). Texto del README (https://raw.githubusercontent.com/binwiederhier/ntfy/main/README.md): "You can buy a plan for as low as $5/month". Las pruebas de la primera ronda sobre el límite de 250 salían de un issue de usuario; ahora hay fuente oficial.

Precio de ntfy Pro (planes pagos de ntfy.sh). El README oficial dice "desde 5 USD al mes". Un agregador (toolradar.com/tools/ntfy/pricing, fecha no visible) lista tres escalones: Supporter 6 USD/mes (2.500 mensajes diarios, 3 temas reservados, 3 llamadas, 50 correos diarios, adjuntos de 25 MB), Pro 12 USD/mes (20.000 mensajes diarios, 10 temas reservados, 20 llamadas, 250 correos, 250 MB) y Business 25 USD/mes (50.000 mensajes diarios, 50 temas reservados, 500 correos, 1 GB). La diferencia entre 5 y 6 USD no se pudo resolver (puede ser facturación anual frente a mensual); la página oficial ntfy.sh/#pricing está bloqueada. Para el informe: "desde unos 5 a 6 USD al mes, según facturación".

Autoalojar. Gratis y de código abierto (Apache-2.0 y GPLv2). En una instancia propia los límites por defecto son más amplios (adjuntos de 15 MB, 100 MB por visitante, 500 MB de tráfico diario) y el tope de mensajes diarios no se aplica salvo que se configure (la documentación dice que "por defecto" el número de mensajes se rige por los límites de pedidos). El servidor funciona en Windows (primera ronda, v2.28.0 del 27-ago-2026). URL: https://raw.githubusercontent.com/binwiederhier/ntfy/main/docs/publish.md .

Confianza. Alta para los límites gratuitos (documentación oficial); media para los precios de los escalones (agregador) y alta para "desde 5 USD" (README oficial).

Contradice o corrige a la primera ronda.
- CONFIRMA y MEJORA android_plataforma.verificado.md (T10), que marcaba los 250 mensajes diarios como "fuente débil (issue de usuario)": ahora es fuente primaria. Se puede quitar el "(verificar)" de la recomendación 2.
- CONFIRMA "desde USD 5 al mes" (bot_determinista.verificado.md, integracion_modulos.verificado.md), con la salvedad de que un agregador muestra 6 USD al mes para el escalón de entrada.
- Matiz: la primera ronda decía "250 por día por IP"; la documentación habla de "por visitante" (en la práctica, la IP). Es equivalente para el informe.

### Pushover

Respuesta. 4,99 USD de pago único por plataforma (Android, iPhone/iPad y escritorio), con 30 días de prueba gratis; un solo pago cubre todos los dispositivos de la misma plataforma; sin suscripción para individuos. Si WINT envía a un Android y a un escritorio, son dos compras (9,98 USD en total).

Evidencia. Extracto: "Pushover costs $4.99 USD as a one-time purchase on each platform ... Users can try it free for 30 days ... multiple devices of the same platform are covered under the same one-time purchase" y "no subscription fees for individuals". URLs: https://pushover.net/pricing , https://support.pushover.net/i8-how-much-does-pushover-cost-is-there-a-subscription .

Confianza. Alta para el precio. SIN RESOLVER: el tope mensual de la API gratuita. La primera ronda dijo 10.000 mensajes por mes (con cambios del 1 de mayo de 2026 sin leer); esta ronda no encontró texto sobre ese límite (el extracto incluso dijo que no halló ninguno, lo que no lo refuta). Se intentó una búsqueda dirigida al dominio pushover.net. Para el informe: "10.000 mensajes al mes según la primera ronda, sin reverificar".

Contradice o corrige. CONFIRMA android_plataforma.md (precio de 4,99 USD por plataforma). No se pudo cerrar T13 (límite) de android_plataforma.verificado.md.

### Telegram Bot API

Respuesta. La Bot API es gratuita. Límites de envío: en un mismo chat, no más de unos 1 mensaje por segundo (ráfagas cortas permitidas; después llegan errores 429); en un grupo, no más de 20 mensajes por minuto; en difusión masiva, unos 30 mensajes por segundo gratis. Se pueden activar difusiones pagas en @BotFather (hasta 1.000 mensajes por segundo; cada mensaje por encima de los 30 gratis cuesta 0,1 Stars). Para avisos personales a un solo chat no hay problema.

Evidencia. "bots should avoid sending more than one message per second ... In a group, bots are not able to send more than 20 messages per minute ... not able to broadcast more than about 30 messages per second, unless they enable paid broadcasts ... 1000 messages per second ... 0.1 Stars per message". URL: https://core.telegram.org/bots/faq (extracto de búsqueda, 7-oct-2026).

Confianza. Alta (página oficial vía extracto). CONFIRMA lo que android_plataforma.md daba como débil; no contradice nada.

### Cloudflare Tunnel y Access

Respuesta. Sí, ambos están incluidos en el plan gratuito. Cloudflare Tunnel (cloudflared, conexiones salientes) es gratis para cualquier cuenta. Zero Trust (que incluye Access) es gratis hasta 50 usuarios; en el plan gratuito cada cuenta tiene un tope de 1.000 túneles y 500 aplicaciones de Access; pasados los 50 usuarios cuesta 7 USD por usuario al mes. Para una persona, Access con inicio de sesión por correo o GitHub frente a un túnel es suficiente y gratuito.

Evidencia. "Cloudflare Zero Trust is free for up to 50 users", "Any organization can use the secure, outbound-only connection feature of Cloudflare Tunnel at no cost", "in the free zero trust plan, each account has a limit of 1000 tunnels and 500 access applications", "paid plan costs $7/seat/month". URLs: https://blog.cloudflare.com/tunnel-for-everyone/ (fecha no visible en el extracto), https://blog.cloudflare.com/teams-plans/ , https://community.cloudflare.com/t/zero-trust-paid-plan-for-tunnels-and-access/646799 .

Confianza. Media-alta: las entradas oficiales del blog de Cloudflare son de años anteriores y la página vigente de precios (cloudflare.com/plans/zero-trust-services) no se vio; el tope de 1.000 túneles y 500 aplicaciones viene de un hilo de la comunidad. Recomendación: decir "gratuito hasta 50 usuarios según Cloudflare (verificar antes de depender de ello)". Un túnel con nombre, para usar Access con una política, necesita un dominio en Cloudflare (primera ronda); los "Quick Tunnels" (try.cloudflare.com) no necesitan dominio pero son temporales y sin garantías.

Contradice o corrige. RESUELVE el "plan gratuito de Access sin verificar" de integracion_modulos.verificado.md (fila de Cloudflare Tunnel + Access).

---

## Q3. Precios de la API de Anthropic y cálculo para 1.000 fichas

Respuesta (precios por millón de tokens, MTok).

| Modelo | Entrada | Salida | Lectura de caché | Entrada por lotes | Salida por lotes |
|---|---|---|---|---|---|
| Claude Haiku 4.5 (`claude-haiku-4-5`) | 1,00 USD | 5,00 USD | 0,10 USD (0,1x) | 0,50 USD | 2,50 USD |
| Claude Sonnet 5.5 (`claude-sonnet-5-5`) | 2,00 USD | 10,00 USD | 0,20 USD | 1,00 USD | 5,00 USD |

Reglas: Message Batches da 50 % de descuento sobre todos los tokens (entrada, salida y también lecturas y escrituras de caché, y los descuentos se acumulan); los resultados llegan de forma asíncrona dentro de las 24 horas. Caché de prompts: la escritura cuesta 1,25x la entrada (TTL de 5 minutos) o 2x (TTL de 1 hora); la lectura cuesta 0,1x (0,05x en Sonnet 5.5 según su ficha: 0,20 USD frente a 2,00 USD, es decir 0,1x del precio de entrada; ojo, el cociente exacto en Sonnet 5.5 es 0,20/2,00 = 0,1x). El prefijo mínimo cacheable en Haiku 4.5 es de 4.096 tokens: un prompt más corto no se cachea (sin error, simplemente no hay acierto).

Evidencia.
- Haiku 4.5: extracto de https://docs.anthropic.com/en/docs/about-claude/pricing (y secundarias coherentes): "Claude Haiku 4.5 costs $1 / $5 per million tokens", "Batch API ... 50% discount ... Haiku 4.5 via Batch API costs $0.50 per million input tokens and $2.50 per million output tokens", "Cache reads are charged at roughly 10% of the standard input rate".
- Sonnet 5.5: tabla "Current Models (cached: 2026-09-25)" de la referencia de la API de Claude Code (skill claude-api): "Claude Sonnet 5.5 ... $2.00 / $10.00 ... cache reads $0.20"; el extracto de la web de precios que devolvió la búsqueda solo trajo Sonnet 4.6 (3 y 15 USD), por lo que Sonnet 5.5 no se contrastó contra la página web. Misma referencia: "50% off every token in the request, including cache reads and writes", "Cache writes cost 1.25x for 5-minute TTL, 2x for 1-hour TTL", mínimo cacheable de Haiku 4.5: 4096 tokens.

Cálculo explícito para 1.000 fichas de unos 1.500 tokens de entrada y 400 de salida con Haiku 4.5.
- Entrada total: 1.000 x 1.500 = 1.500.000 tokens = 1,5 MTok. Salida total: 1.000 x 400 = 400.000 tokens = 0,4 MTok.
- Tarifa estándar: entrada 1,5 x 1,00 = 1,50 USD; salida 0,4 x 5,00 = 2,00 USD; total 3,50 USD (0,0035 USD por ficha).
- Por lotes (50 %): entrada 1,5 x 0,50 = 0,75 USD; salida 0,4 x 2,50 = 1,00 USD; total 1,75 USD (0,00175 USD por ficha).
- Con caché: si las 1.500 tokens ya incluyen las instrucciones, no hay prefijo de 4.096 tokens y la caché no ahorra nada en Haiku 4.5. Ejemplo hipotético (supuesto, no dato): si cada pedido llevara además un prefijo fijo de 5.000 tokens (instrucciones, esquema y ejemplos), sin caché la entrada sería 1.000 x 6.500 = 6,5 MTok = 6,50 USD (total 8,50 USD con la salida); con caché: una escritura de 5.000 x 1,25 = 0,00625 USD, más 999 lecturas de 5.000 tokens a 0,10 USD/MTok = 4.995.000 tokens x 0,10 / 1.000.000 = 0,4995 USD, más 1,5 MTok variables a 1,00 USD = 1,50 USD; entrada total = 2,006 USD; con la salida (2,00 USD) el total es 4,006 USD, y por lotes con caché unos 2,00 USD (la caché en lotes es de mejor esfuerzo; no se verificó en esta ronda).
- Comparación: con Sonnet 5.5 las mismas fichas cuestan 1,5 x 2,00 + 0,4 x 10,00 = 3,00 + 4,00 = 7,00 USD (3,50 USD por lotes), siempre que la salida no crezca; Sonnet 5.5 corre con razonamiento adaptativo por defecto (los tokens de razonamiento se facturan como salida), y para apagarlo hay que enviar `thinking: {type: "between_tools"}` (el valor `disabled` da error 400 en ese modelo), de modo que el costo real puede ser mayor si no se configura. Haiku 4.5 no razona por defecto.
- Con impuestos argentinos (ver Q5), pagando con tarjeta en dólares: multiplicar por 1,30 como mínimo (solo percepción) y hasta unos 1,57 si además se aplicara IVA. Eso lleva 3,50 USD a 4,55 a 5,50 USD, y 1,75 USD por lotes a 2,28 a 2,75 USD.
- Contraste con `claude -p`: la primera ronda midió unos 0,012 USD por una llamada trivial con Haiku 4.5 (unos 5.000 tokens de contexto base). Mil llamadas serían al menos 12 USD, 3,4 veces la tarifa estándar directa de la API (3,50 USD) y 6,9 veces la tarifa por lotes (1,75 USD), sin contar los 1.500 tokens de la ficha.

Confianza. Alta para Haiku 4.5 (extracto de la página oficial y de secundarias; coincide con la referencia de Claude Code); media-alta para Sonnet 5.5 (referencia oficial de Claude Code en caché del 25-sep-2026, no contrastada en la web). Los cálculos son aritmética propia sobre esas tarifas.

Contradice o corrige a la primera ronda.
- CONFIRMA y CUANTIFICA bot_determinista.verificado.md (corrección 2d): la recomendación de agrupar productos o usar la API directa se sostiene; la API directa con lotes es unas 7 veces más barata que `claude -p` por ficha.
- CONFIRMA que Haiku 4.5 sigue "Activo" (bot_determinista.verificado.md, corrección 1: "no antes del 15-oct-2026", con 60 días de preaviso); como plan B, Sonnet 5.5 duplica el precio de Haiku 4.5 (1,5 USD el lote más barato por 1.000 fichas frente a 1,75 USD no, ver arriba: 3,50 USD por lotes frente a 1,75 USD).
- AGREGA algo que la primera ronda no tenía: el mínimo de 4.096 tokens para cachear en Haiku 4.5.

---

## Q4. Cuentas de desarrollador y firma de código

### Google Play Console

Respuesta. Cuota única de 25 USD (sin cuota anual, apps ilimitadas), pagada con tarjeta de crédito o débito. Las cuentas personales creadas después del 13 de noviembre de 2023 deben hacer una prueba cerrada con al menos 12 testers durante 14 días seguidos antes de poder publicar en producción. La verificación de identidad de una cuenta personal pide un documento nacional, un nombre público de desarrollador, un correo de soporte y el país.

Evidencia. Extractos: "US$25 one-time registration fee ... no annual fee and no per-app charge", "closed test with at least 12 testers for 14 continuous days". URLs de resultados: https://support.google.com/googleplay/android-developer/answer/6112435 y https://support.google.com/googleplay/android-developer/answer/6008841 (aparecen en la búsqueda, pero solo se vio el texto de las secundarias: https://afkarsoftware.com/en/blog-detail/google-play-console-account-2026-one-time-25-fee/ , https://www.testerscommunity.com/blog/how-much-does-it-cost-to-publish-an-app-on-google-play ).

Confianza. Media (varias secundarias coherentes; las páginas oficiales no se leyeron). SIN RESOLVER: si una persona residente en Argentina puede registrarse y qué trámite fiscal pide Play para apps pagas (AUDITORIA M2); se intentó con una búsqueda general y no devolvió nada específico. Al pagar los 25 USD con tarjeta argentina rige la percepción de Q5 (costo de bolsillo de unos 32,5 USD como mínimo, más IVA si correspondiera; inferencia).

Contradice o corrige. COMPLETA android_plataforma.md y c_android.md (no traían la cuota). No contradice nada. Para un Android sin Play, la primera ronda y c_android.md hablan de la "cuenta de distribución limitada" de la Android Developer Console (sin tarifa); no se reverificó aquí.

### Microsoft Store (cuenta individual)

Respuesta. El registro de desarrollador individual es gratuito, sin tarjeta de crédito, en casi 200 mercados, desde el anuncio del 10-sep-2025 (flujo en storedeveloper.microsoft.com: cuenta Microsoft, verificación de identidad con escaneo de documento y acceso casi inmediato a Partner Center). Antes costaba 19 USD (fuente secundaria). Argentina figura como país admitido para el registro de desarrollador en la página de Microsoft Learn "Account types, locations, and fees" (su tabla de tarifas, con 106 ARS para individuos, es anterior al cambio y quedó obsoleta; hoy es gratis).

Evidencia. "Individual developers can now publish apps to the Microsoft Store without paying any onboarding fees ... nearly 200 markets ... no longer need a credit card"; "Argentina is listed as a supported country ... individual registration fee of 106 ARS". URLs: https://blogs.windows.com/windowsdeveloper/2025/09/10/free-developer-registration-for-individual-developers-on-microsoft-store/ , https://learn.microsoft.com/windows/uwp/publish/account-types-locations-and-fees , https://learn.microsoft.com/en-us/windows/apps/publish/faq/get-started-with-the-microsoft-store .

Confianza. Alta para "gratis" (blog oficial de Microsoft, más la guía del 17-sep-2025 que leyó la primera ronda) y media-alta para Argentina (tabla oficial vista en un extracto, de fecha anterior; dado que la nueva oferta es "casi 200 mercados", conviene confirmar en el alta). La cuenta individual es para actividad fuera del oficio; si WINT se distribuye con fines comerciales, la guía de la primera ronda indica una cuenta de empresa (también gratuita).

Contradice o corrige. CONFIRMA shells_windows_android.md (afirmación sobre la guía del 9/17/2025) y CIERRA lo que AUDITORIA.md (M2) dejó sin verificar: "elegibilidad de Argentina para Store".

### Opciones de firma de código para individuos

- Microsoft Artifact Signing (antes Trusted Signing). Plan Basic: 9,99 USD al mes por hasta 5.000 firmas (0,005 USD por firma adicional); Premium: 99,99 USD al mes por hasta 100.000 firmas. Disponibilidad: para individuos, solo Estados Unidos y Canadá; para organizaciones, Estados Unidos, Canadá, UE y Reino Unido en el extracto de la página del producto (la primera ronda, leyendo Microsoft Learn, tenía una lista más larga de organizaciones: también Australia, Nueva Zelanda, Japón, Corea del Sur, Singapur, Suiza, Noruega e Israel). Argentina no está en ninguna de las dos listas, por lo que una persona en Argentina no puede usarlo. Evidencia: "For individuals, Artifact Signing is available in USA and Canada only". URLs: https://azure.microsoft.com/products/artifact-signing , https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/code-signing-options , https://www.devclass.com/security/2026/01/14/code-signing-windows-apps-may-be-easier-and-more-secure-with-new-azure-artifact-service/4079554 . Confianza: alta para "individuos solo EE. UU. y Canadá" (dos lecturas independientes: Learn en la primera ronda y esta). CONFIRMA shells_windows_android.md (H5) y su cifra de 9,99 USD; la lista de organizaciones varía entre páginas, citar la de Learn con su fecha.
- SignPath Foundation (gratis, solo código abierto). Exige licencia aprobada por la OSI sin doble licencia comercial, sin componentes propietarios, proyecto con mantenimiento activo y compilación totalmente automatizada y trazable al repositorio; la clave privada queda en un HSM de SignPath, no pide identificación personal (SignPath verifica que el binario sale del repositorio y lo avala con su nombre). WINT solo calificaría si se publica como software libre; si es personal o cerrado, no. URLs: https://signpath.org/ , https://about.signpath.io/product/open-source , https://signpath.org/terms . Confianza: alta (páginas del proveedor vía extracto).
- Certum (certificado "Open Source Code Signing"). Según una fuente secundaria: unos 69 euros en la primera compra (incluye lector y tarjeta inteligente) y 25 euros por año en renovaciones, con firma que exige ingresar un PIN en cada operación, por lo que no se puede automatizar en integración continua; el certificado gratuito de prueba se discontinuó en 2016. No se vio la página de Certum ni si acepta residentes en Argentina. Confianza: baja-media (fuente secundaria sin fecha clara; precios y requisitos a verificar con Certum). URLs de resultados: https://dev.to/jozefizso/digital-signatures-in-open-source-projects-17f5 , https://en.delphipraxis.net/topic/15454-cheapest-codesign-149-anyone-used-this/ .
- Alternativa sin comprar certificado: publicar en Microsoft Store con MSIX (la Store firma el paquete; primera ronda).

Contradice o corrige. Completa la nota de shells_windows_android.md ("certificado comercial: no investigado aquí") con las opciones concretas. No se investigaron certificados comerciales (OV/EV) ni la reputación en SmartScreen.

---

## Q5. Impuestos argentinos a pagos en dólares con tarjeta por servicios digitales del exterior

Respuesta. Los pagos en moneda extranjera con tarjeta (consumos en el exterior y suscripciones a plataformas digitales como Netflix o Spotify) llevan una percepción del 30 % a cuenta de Impuesto a las Ganancias o Bienes Personales, regulada por la Resolución General ARCA 5617, tal como la modificó la RG 5672/2025 (publicada el 14-abr-2025: eliminó la percepción sobre la compra de billetes y divisas para atesoramiento por personas humanas, pero la mantuvo para compras de bienes y servicios en el exterior). Notas de prensa de iProfesional del 20-jun-2026 ("ARCA mantuvo 30 % percepción ganancias") y del 23-jul-2026 ("paso a paso para no pagar la percepción del 30 %") indican que sigue en vigencia a mediados de 2026. Además, las suscripciones a servicios digitales del exterior llevan IVA del 21 % que cobra el banco emisor de la tarjeta, y en algunos casos percepciones provinciales (Ingresos Brutos).

Costo real de una suscripción. Es una estimación propia, no un dato de las fuentes: la percepción es un anticipo y no un costo definitivo si hay Ganancias o Bienes Personales que computar; para consumidores finales, monotributistas y empleados sin Ganancias no es computable y, según el extracto, se puede pedir la devolución desde el sitio de ARCA (con demora y verificación). El IVA no es computable para consumidores finales ni para monotributistas, así que es costo. Multiplicador sobre el precio en dólares, convertido al dólar oficial de la tarjeta: 1,30 (solo percepción) hasta unos 1,51 a 1,57 si además hay IVA del 21 % (1,21 + 0,30 si la percepción se calcula sobre el precio sin IVA; 1,21 x 1,30 = 1,573 si se calcula sobre el precio con IVA; el extracto no aclaró la base), antes de percepciones provinciales y comisiones bancarias. Ejemplo: una suscripción de 10 USD equivale a entre 13,00 y 15,70 USD al tipo de cambio oficial. Si el proveedor (por ejemplo Anthropic, ntfy, Pushover) cobra IVA depende de si figura como prestador de servicios digitales del exterior: no se verificó para ninguno; la percepción del 30 % sí aplica a cualquier pago en moneda extranjera con tarjeta.

Evidencia. "The 30% withholding is applied by ... ARCA under Resolution General 5617 ... advance payment on account of Income Tax or Personal Property Tax"; "Through Resolution General 5672/2025, published ... on April 14, 2025 ... elimination of the perception regime ... on the purchase of bills and foreign currency for hoarding ... purchases of goods and services abroad will continue to be subject"; "se aplican el 21% de IVA sobre servicios digitales, más la percepción del 30%"; "For those not registered in these taxes, such as monotax contributors or employees without withholdings, there is the possibility of requesting the return". URLs: https://blogdelcontador.com.ar/arca-percepcion-ganancias-operaciones-en-moneda-extranjera , https://eleconomista.com.ar/economia/alerta-turismo-pagos-exterior-modificaron-percepciones-ganancias-bienes-personales-n83869 , https://bruchoufunes.com/arca-modifico-el-regimen-de-percepcion-aplicable-a-operaciones-en-moneda-extranjera-cambios-en-la-resolucion-general-5617 , https://www.iprofesional.com/impuestos/419311-dolar-arca-ex-afip-mantuvo-30-por-ciento-percepcion-ganancias , https://www.iprofesional.com/impuestos/445594-dolar-tarjeta-paso-a-paso-para-no-pagar-la-percepcion-del-30-por-ciento-de-arca-ex-afip , https://www.global66.com/blog/?p=21186 .

Confianza. Media-alta para el 30 % y la RG 5617 (varios medios y estudios contables coherentes, con fechas hasta julio de 2026; no se vio la norma en el Boletín Oficial en texto completo). Media para el IVA del 21 % (una fuente secundaria). Baja para el multiplicador total y las percepciones provinciales (inferencia, no cálculo oficial). No se verificó si pagar con saldo en dólares propio (débito en cuenta en dólares) evita la percepción; hay notas de prensa sobre "cómo evitar el recargo" (noticiasnqn.com.ar, 27-ene-2026; iProfesional 23-jul-2026) que no se leyeron. El Impuesto PAIS (30 %), que antes se sumaba, dejó de aplicarse a fines de 2024: es conocimiento propio y esta ronda no lo reverificó (baja-media).

Contradice o corrige. La primera ronda no cubrió esto (AUDITORIA.md A10); es información nueva para el capítulo de costos. No hay contradicción con ningún archivo.

---

## Q6. Hardware siempre encendido y alternativas en la nube

### Raspberry Pi 5

Respuesta. Precio en Estados Unidos en 2026: unos 110 USD el modelo de 4 GB y unos 175 USD el de 8 GB (hasta unos 205 USD el de mayor memoria) tras tres subas entre noviembre de 2025 y abril de 2026, atribuidas a la escasez de memoria (70 a 90 % de aumento, según prensa). Se suman fuente de alimentación, disipador o caja y almacenamiento (microSD o SSD). En Argentina, la Raspberry Pi 5 de 4 GB se cotizaba en 277.340 pesos en Mercado Libre en junio de 2026 (mínimo histórico del seguimiento: 220.088 pesos). Consumo: unos 2,7 a 3,0 W en reposo; 3 a 5 W con una pila de servidor básica; hasta 12 a 25 W a plena carga. A 0,30 USD por kWh, un Pi 5 encendido todo el año cuesta unos 7 a 8 USD.

Evidencia. https://www.gigazine.net/gsc_news/en/20260402-raspberry-pi-price-increases , https://www.techspot.com/news/111165-raspberry-pi-prices-soar-amid-ai-memory-shortage.html , https://www.notebookcheck.net/Raspberry-Pi-5-now-costs-up-to-205-due-to-RAM-crisis.1218209.0.html (URL tal como aparece abreviada en los resultados; ver el listado original en la búsqueda), https://raspberry.tips/en/faq/raspberry-pi-power-consumption-update-2026-all-models-compared , https://mejorescompras.com.ar/precio/MLA34101441--raspberry-pi-5-4gb-ram-made-in-uk , https://ecosistemastartup.com/?p=77350 . Cuidado: los extractos mezclan "110 USD" y "105 USD" para el modelo de 4 GB; la cifra exacta de la lista oficial de raspberrypi.com no se leyó.
Confianza. Media (prensa y seguidores de precios; no la página del fabricante).

### Mini PC con Intel N100

Respuesta. Consumo típico en reposo: 5,5 a 6,5 W medidos en equipos genéricos; 6 a 12 W en equipos con ventilador; hay unidades con 14 W en reposo y unos 29 W a plena carga. Precio: en el exterior, un N100 con 8 GB de memoria LPDDR5 desde unos 156 USD (nota antigua de CNX Software, anterior a las subas de memoria de 2026, así que hoy sería más) y un Minisforum UN100L de 16 GB y 512 GB en preventa a 206 USD (Notebookcheck, antigua). En Argentina, un MeLE Quieter 4C (N100, 16 GB, 512 GB) figura en Frávega a 1.699.099 pesos con impuestos (fecha de captura no visible). Un mini PC x86 permite correr Windows o Linux con todo el software de WINT; un Raspberry Pi (ARM, Linux) sirve para el Detector, ntfy y el panel, pero no para los módulos que actúan sobre Windows (Sol y Luna), que deben vivir en la PC.
Evidencia. https://www.linuxlinks.com/dreamquest-n100-mini-pc-running-linux-power-consumption/ , https://selfhosting.sh/hardware/intel-n100-mini-pc/ , https://minipclab.com/blog/mini-pc-power-consumption-guide , https://cnx-software.com/?p=110543 , https://www.notebookcheck.org/El-Minisforum-UN100L-debuta-como-mini-PC-rentable.783924.0.html , https://www.fravega.com/p/mini-pc-mele-quieter-4c-intel-n100-16gb-ram-512gb-22941566/ . Confianza: media-baja (reseñas y comercio; las fechas de precio no son comparables).

### Frente a dejar la PC principal encendida

SIN RESOLVER con fuente: no se buscó el consumo en reposo de una PC de escritorio ni la tarifa eléctrica residencial argentina de 2026. Se deja la fórmula para el informe: kWh por año = vatios x 8,76 (por ejemplo 3 W son unos 26 kWh por año; 10 W, unos 88; 60 W, unos 526; los 60 W son un supuesto ilustrativo, no un dato). La comparación honesta es medir la PC con un medidor de enchufe y multiplicar por la tarifa del propio contrato. La primera ronda tiene un capítulo sobre energía en Windows (energia_windows.md), donde puede ir ese perfil.

### Oracle Cloud "Always Free" y VPS económicos

Respuesta. El plan sigue existiendo, pero se recortó en 2026: el cupo de cómputo Ampere A1 pasó de 4 OCPU y 24 GB de RAM a 2 OCPU y 12 GB (1.500 horas de OCPU y 9.000 horas de GB al mes), con efecto desde el 15-jun-2026, según dos notas (braindetox.kr e InfoQ de julio de 2026); Oracle habría actualizado la documentación sin anuncio. Además, Oracle puede reclamar instancias Always Free "inactivas": se considera inactiva una instancia si durante 7 días el percentil 95 de CPU y de red está por debajo del 20 % y, en las formas A1, también la memoria está por debajo del 20 %. Un rastreador de precios que despierta de a ratos probablemente quede por debajo de ese umbral, con riesgo de que se la reclamen (se mitiga pasando a "pago por uso", que conserva los recursos Always Free, dato no verificado aquí). No se verificó si Argentina puede registrarse ni los precios de VPS de pago (SIN RESOLVER; no se buscaron).
Evidencia. https://docs.oracle.com/en-us/iaas/Content/FreeTier/resourceref.htm (política de instancias inactivas), https://braindetox.kr/en/posts/oracle_always_free_tier_reduced_2026.html , https://infoq.com/news/2026/07/oracle-cloud-free-tier-limits/ , https://docs.oracle.com/iaas/Content/FreeTier/freetier.htm .
Confianza. Alta para la política de instancias inactivas (documentación de Oracle vía extracto); media para el recorte a 2 OCPU y 12 GB (notas periodísticas; el extracto no mostró la tabla de la documentación).

Contradice o corrige. Es información nueva: la primera ronda no cubrió hardware ni nube de bajo costo.

---

## Cambios que esto impone al informe

1. Tailscale: reemplazar "plan Personal gratis para 3 usuarios y 100 dispositivos" por "plan Personal gratuito para hasta 6 usuarios, con dispositivos propios sin tope práctico, solo para uso no comercial" (confianza media-alta; esquema vigente desde abril de 2026).
2. Tailscale Funnel: eliminar la "contradicción" y decir que, según la documentación de Tailscale, Funnel está disponible en todos los planes, incluido el gratuito, con ancho de banda limitado; para el teléfono sigue bastando Serve (solo tailnet).
3. ntfy.sh: el límite de 250 mensajes diarios por visitante y los demás topes (5 correos diarios, adjuntos de 2 MB, 20 MB por visitante, 200 MB diarios de tráfico, 30 suscripciones) ya son de fuente oficial y se citan sin "verificar"; ntfy Pro es "desde 5 USD al mes" según el README, y un agregador muestra 6, 12 y 25 USD por escalón.
4. Pushover: 4,99 USD de pago único por plataforma, con 30 días de prueba y sin suscripción para individuos; el tope mensual de la API (10.000 según la primera ronda) queda sin reverificar.
5. Telegram: la Bot API es gratuita, con unos 1 mensaje por segundo por chat, 20 por minuto en grupos y unos 30 por segundo en difusión, límites que no afectan a un uso personal.
6. Cloudflare: Tunnel es gratuito y Zero Trust (con Access) es gratis hasta 50 usuarios, según Cloudflare (confianza media-alta; verificar la página vigente antes de depender de ello).
7. API de Anthropic: Haiku 4.5 cuesta 1 USD por millón de tokens de entrada y 5 USD de salida, y Sonnet 5.5 cuesta 2 y 10 USD; los lotes dan 50 % de descuento y las lecturas de caché cuestan 0,1x la entrada.
8. Costo de 1.000 fichas (1.500 tokens de entrada, 400 de salida) con Haiku 4.5: 1,5 MTok x 1 USD + 0,4 MTok x 5 USD = 3,50 USD (0,0035 USD por ficha), y 1,75 USD por lotes; con Sonnet 5.5, 7,00 USD (3,50 USD por lotes).
9. Caché de prompts: en Haiku 4.5 solo se cachean prefijos de 4.096 tokens o más, así que con fichas de 1.500 tokens y un prompt corto la caché no ahorra nada; solo conviene si hay un prefijo fijo largo (con 5.000 tokens fijos, el ejemplo baja de 8,50 a 4,01 USD).
10. `claude -p`: una llamada trivial costó unos 0,012 USD (primera ronda), es decir, 1.000 llamadas son al menos 12 USD, unas 3,4 veces la API directa (3,50 USD) y unas 6,9 veces la API por lotes (1,75 USD); para analizar fichas en volumen conviene la API directa con lotes.
11. Impuestos argentinos: el pago en dólares con tarjeta por servicios del exterior lleva una percepción del 30 % a cuenta de Ganancias o Bienes Personales (RG ARCA 5617, modificada por la RG 5672/2025 del 14-abr-2025, vigente a mediados de 2026 según la prensa) y, para servicios digitales, además IVA del 21 %; el costo real queda entre 1,30 y unas 1,57 veces el precio en dólares (estimación), con devolución posible de la percepción para quienes no tienen Ganancias ni Bienes Personales.
12. Microsoft Store: el registro individual es gratuito desde el 10-sep-2025 en casi 200 mercados y Argentina figura como país admitido; queda cerrado el pendiente de elegibilidad de Argentina de la auditoría.
13. Firma de código: Microsoft Artifact Signing (9,99 USD al mes) está disponible para individuos solo en Estados Unidos y Canadá, por lo que no sirve para una persona en Argentina; SignPath Foundation es gratis pero solo para proyectos de código abierto con licencia OSI; Certum Open Source cuesta unos 69 euros la primera vez y 25 euros por año (fuente secundaria, a verificar) y exige PIN en cada firma.
14. Google Play: la cuota de registro es única de 25 USD, y las cuentas personales nuevas deben completar una prueba cerrada de 12 testers durante 14 días antes de publicar en producción; si se paga con tarjeta argentina rige la percepción del 30 %; la elegibilidad de Argentina no se verificó.
15. Hardware siempre encendido: una Raspberry Pi 5 cuesta en 2026 unos 110 USD (4 GB) o 175 USD (8 GB) por la escasez de memoria (277.340 pesos el modelo de 4 GB en Mercado Libre en junio de 2026), consume unos 3 W en reposo y sirve para el Detector, ntfy y el panel; un mini PC N100 consume unos 6 a 12 W y permite correr todo el software, pero los módulos Sol y Luna deben seguir en la PC de Windows.
16. Oracle Cloud Always Free: en 2026 el cupo ARM se recortó de 4 OCPU y 24 GB a 2 OCPU y 12 GB (desde el 15-jun-2026, según dos notas periodísticas) y Oracle puede reclamar instancias inactivas (percentil 95 de CPU y red por debajo del 20 % durante 7 días), de modo que no conviene presentarlo como alternativa confiable para un proceso de poca carga.
17. No se pudo cerrar con fuente: el consumo en reposo de la PC principal, la tarifa eléctrica argentina, los precios de VPS de pago, el tope mensual gratuito de Pushover y la elegibilidad de Argentina en Google Play; el informe debe marcarlos como "a verificar".
