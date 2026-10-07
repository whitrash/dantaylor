# Cómo demostrar que una oferta es falsa: método, estadística y particularidades de la inflación argentina

## Resumen

1. Límite de esta investigación: el buscador web quedó sin cupo (límite de 200 por turno, compartido) y la red de salida bloqueó casi todos los sitios oficiales (EUR-Lex, INDEC, BCRA, datos.gob.ar, Which?, FTC, arXiv). Solo se pudo abrir GitHub, raw.githubusercontent.com y PyPI; las normas y estudios quedan, por eso, en espejos secundarios o en la sección "Qué no se pudo verificar".
2. Definición propuesta: una oferta es real cuando (a) la referencia declarada existió, (b) el precio actual es menor, en pesos constantes, que una base robusta de 90 días y (c) no hubo una suba previa. Son tres preguntas independientes, no una sola.
3. Europa: el art. 6a de la Directiva 98/6/CE (insertado por la Directiva 2019/2161, aplicable desde el 28 de mayo de 2022) exige que el "precio anterior" sea el mínimo de los 30 días previos; cuatro implementaciones de software independientes repiten la regla (fuente secundaria).
4. Argentina: en los textos leídos (espejos de la Ley 24.240 y del DNU 274/2019) no aparece una regla numérica de "precio de referencia"; sí hay vigencia obligatoria de la oferta (art. 7), precio al contado en crédito (art. 36) y prohibición de inducir a error sobre el precio (DNU art. 11).
5. Estadística: el precio publicado es una función escalón; la mediana debe ponderarse por tiempo (1 día = 1 peso), con MAD robusto (scipy, scale="normal" = 1/0,67449) y percentiles; detección de puntos de cambio con ruptures (Pelt, costo l1, jump=1) como segunda etapa, no como base.
6. Inflación: comparar pesos nominales engaña en las dos direcciones. Ejemplo ejecutado: con 4% mensual y una baja nominal de 10%, el mínimo nominal de 120 días (851) queda por debajo del precio de hoy (900) y un detector nominal calla; deflactado, la baja es 10% real y la oferta se detecta.
7. Series: IPC nacional por la API de series de tiempo (id 148.3_INIVELNAL_DICI_M_26, hasta 40 ids por consulta, limit máx. 1000, 60 pedidos/s por IP) y cotización oficial por la API del BCRA (Estadísticas Cambiarias v1.0); MEP/CCL solo por APIs comunitarias sin garantías.
8. Regla de dos numerarios: acusar (suba previa, tachado ficticio) exige que la falla aparezca en pesos deflactados por IPC y en dólares; acreditar usa el numerario configurado por categoría. Evita falsos positivos por saltos cambiarios.
9. Datos de supermercados: SEPA (siete ZIP semanales, id_producto = EAN, precio de lista, precio de referencia por unidad) y scrapers de Precios Claros; un proyecto local ya marca "inflado" con una regla transversal ingenua (lista mayor a 2 veces la mediana entre comercios).
10. Emparejamiento: GTIN validado primero (python-stdnum: 8, 12, 13 y 14 dígitos); difuso (RapidFuzz), probabilístico (Splink) y embeddings solo para generar candidatos, con guardas duras de tamaño, pack y variante y revisión humana.
11. Algoritmo especificado y ejecutado: 6 reglas, puntaje 0 a 100, banderas duras, etiquetas y explicación en frases ("20% menos que la mediana de 90 dias (pesos constantes); es el minimo de 396 dias (toda la historia disponible)"); código de Python estándar probado en 11 escenarios sintéticos e invariancias (escala, inflación pura, faltantes).
12. Cifras de esa prueba de humo no son validación: los umbrales son heurísticos y no están calibrados; el plan de validación (suite sintética, hypothesis, muestra humana de 139 a 385 casos, Brier, kappa) está en H24.
13. Cuotas "sin interés": con lista 1200 y contado 1000 en 6 cuotas, la tasa implícita es 5,47% mensual (89,5% efectiva anual); con inflación alta, "sin interés" sin recargo es además un descuento real. Hay que auditar la serie de contado, no la de lista.

## Hallazgos

### H1 — Definición operativa de oferta real vs. engañosa
- Afirmación: Propuesta de diseño (opinión fundamentada en las normas de H2 a H5): conviene separar tres preguntas independientes porque una oferta puede fallar una y aprobar otra.
  - Veracidad de la referencia: ¿el precio tachado o "antes" existió y rigió? Se mide con S(L), la fracción de los últimos 90 días en que el precio real fue mayor o igual a 0,98·L (L = precio tachado declarado hoy).
  - Magnitud real: nd = 1 − P0/B, con P0 el precio actual en pesos constantes y B la mediana ponderada por tiempo del precio real en la ventana [r−111, r−22], donde r es el primer día del precio actual (90 días de base, excluida una zona de "rampa" de 21 días previa al cambio).
  - Oportunidad: k = días desde la última vez que hubo un precio real menor ("es el mínimo de k días") y comparación con la mediana de otros comercios.
  - Clasificación: "engañosa" si hay al menos una bandera dura (tachado ficticio, suba previa confirmada en dos numerarios, oferta perpetua); "oferta real" si no hay bandera y el puntaje es mayor o igual a 75; "dudosa" de 50 a 74; "sin valor real" si es menor a 50 sin banderas; "datos insuficientes" si hay menos de 45 días observados en la base.
  - Hay que distinguir incumplimiento legal (depende de la jurisdicción: la UE define el precio anterior como el mínimo de 30 días; en los textos argentinos leídos no hay definición numérica) de engaño económico (depende de los datos). El Detector puede probar lo segundo con historial propio sin necesidad de que lo primero esté definido.
- Fuentes: https://raw.githubusercontent.com/open-mercato/open-mercato/fefc71d09efe2aa8c732dc6fafaa084a0e0dae3c/.ai/specs/2026-06-30-omnibus-price-tracking.md, https://raw.githubusercontent.com/clarius/normas/main/ley/LNS0003875.md, https://raw.githubusercontent.com/clarius/normas/main/decreto/DN20190000274.md
- Confianza: media
- Riesgo: bajo
- Vigencia: consultado 7 de octubre de 2026 (definición propia; las normas citadas están en H2 a H5)

### H2 — Regla de la UE: precio anterior = mínimo de los 30 días previos
- Afirmación: La Directiva (UE) 2019/2161 ("Omnibus"), con aplicación desde el 28 de mayo de 2022, modificó la Directiva 98/6/CE insertando el art. 6a: todo anuncio de reducción de precio debe indicar el "precio anterior", y ese precio es el más bajo aplicado por el comerciante durante un período no inferior a 30 días antes de la reducción. Cuatro proyectos de software independientes (open-mercato, Hostilian/eushop, nopCommerce-Docs y Spree) formulan la regla de modo coincidente; ninguno es fuente oficial y el texto de EUR-Lex no se pudo abrir. Consecuencia directa para el Detector: calcular siempre min30 = mínimo del precio nominal en los 30 días anteriores al inicio de la reducción y comparar contra el precio tachado declarado L; si L > 1,02·min30, informar que "la referencia no cumpliría la regla europea de 30 días" (aclarando que es una regla de la UE, no argentina). La especificación de open-mercato propone para cumplirla una capa de historial de precios inmutable (solo-anexar) con consulta del mínimo en la ventana, y señala que los complementos de WooCommerce y de Magento 2 registran cada cambio y consultan el MIN en un rango de fechas; es el mismo diseño que se recomienda abajo.
- Fuentes: https://raw.githubusercontent.com/open-mercato/open-mercato/fefc71d09efe2aa8c732dc6fafaa084a0e0dae3c/.ai/specs/2026-06-30-omnibus-price-tracking.md, https://raw.githubusercontent.com/Hostilian/eushop/95478217fffd6c7de8802d35a39ee9cc2adcbed6/.agents/knowledge/eu-omnibus-directive-2019-2161.md, https://api.github.com/repositories/192514862/contents/en/running-your-store/catalog/eu-omnibus-directive/index.md?ref=b428a1dfc94b72c6a45e3267360efd7e662c2853, https://api.github.com/repositories/3314/contents/docs/developer/core-concepts/data-privacy.mdx?ref=a44267ddc5273bc7231d8229b56200c066f6aba9
- Confianza: media
- Riesgo: alto
- Vigencia: especificaciones de 2026 (open-mercato: 18/02/2026 y 30/06/2026 según el nombre de archivo); consultado 7 de octubre de 2026

### H3 — Alcance y límites de la regla de 30 días (y por qué no alcanza)
- Afirmación: Según la paráfrasis de open-mercato (que además atribuye el alcance al Aviso de la Comisión 2021/C 526/02, documento que no se pudo abrir), el art. 6a: (a) se aplica solo a reducciones anunciadas, no a cambios de precio silenciosos; (b) se refiere al precio propio anterior del comerciante, no al precio recomendado por el fabricante; (c) permite a los Estados miembros fijar reglas distintas para bienes perecederos (apartado 6a.3 según la paráfrasis) y un período más corto para productos que llevan menos de 30 días en el mercado (6a.4); (d) permite que, cuando la reducción se profundiza progresivamente, el precio anterior sea el previo a la primera reducción (6a.5). La numeración de los apartados no se contrastó con el texto oficial. Implicancias de diseño: (1) 30 días es un piso legal, no una definición económica: un comercio puede subir el precio 31 días antes y cumplir la regla; por eso el algoritmo usa base de 90 días con zona de rampa de 21 días y exige confirmación; (2) el Detector debe evaluar también bajas sin anuncio (la regla no las cubre); (3) hay que agrupar bajadas sucesivas con huecos de hasta 7 días en una sola "campaña" y tomar como precio previo el anterior a la primera; (4) para productos con menos de 30 días de historia, no calificar: solo comparar contra otros comercios.
- Fuentes: https://raw.githubusercontent.com/open-mercato/open-mercato/fefc71d09efe2aa8c732dc6fafaa084a0e0dae3c/.ai/specs/2026-06-30-omnibus-price-tracking.md, https://raw.githubusercontent.com/Hostilian/eushop/95478217fffd6c7de8802d35a39ee9cc2adcbed6/.agents/knowledge/eu-omnibus-directive-2019-2161.md
- Confianza: baja
- Riesgo: alto
- Vigencia: consultado 7 de octubre de 2026 (paráfrasis secundaria; el Aviso 2021/C 526/02 no se verificó)

### H4 — Argentina: Ley 24.240 (oferta con vigencia, precio al contado, sanciones)
- Afirmación: Según un espejo en Markdown del texto de la Ley 24.240 de Defensa del Consumidor (el espejo la marca "vigente"; no se contrastó con InfoLEG): art. 4, el proveedor debe dar información "cierta, clara y detallada" sobre las características esenciales y las condiciones de comercialización; art. 7, la oferta dirigida a consumidores indeterminados obliga a quien la emite durante el tiempo en que se realice y debe contener "la fecha precisa de comienzo y de finalización", además de modalidades, condiciones o limitaciones; art. 10 bis, el incumplimiento de la oferta faculta al consumidor a exigir el cumplimiento, aceptar un producto equivalente o rescindir; art. 36, en las operaciones de crédito para el consumo debe consignarse el precio al contado (solo en operaciones de crédito para adquirir bienes o servicios), la tasa de interés efectiva anual y el total de intereses o el costo financiero total; art. 47, multas expresadas en canastas básicas totales del hogar (el resumen leído dio 0,5 a 2.100; la cifra necesita confirmación). Consecuencias para el Detector: (1) guardar siempre el texto de vigencia de la oferta (fecha de inicio y fin); una "oferta" sin fecha visible es una bandera de cumplimiento distinta de las de precio; (2) en cuotas, capturar y comparar el precio de contado; (3) este es el único piso legal argentino verificado sobre precios "de oferta".
- Fuentes: https://raw.githubusercontent.com/clarius/normas/main/ley/LNS0003875.md, https://raw.githubusercontent.com/KairumAI/landing/f8d3b9d9854734ed2c525d873a1ba7b2d076b756/public/informes/credicuotas/evidence/D-011.html
- Confianza: media
- Riesgo: alto
- Vigencia: espejo consultado 7 de octubre de 2026; no se verificaron modificaciones posteriores (p. ej., decretos de 2023 en adelante)

### H5 — Argentina: DNU 274/2019 (publicidad engañosa sobre precio) y ausencia de regla numérica de precio de referencia
- Afirmación: Según un espejo del texto del DNU 274/2019 (Lealtad Comercial): art. 10 a) considera acto desleal "inducir a error sobre la existencia o naturaleza, modo de fabricación o distribución, características principales, pureza, mezcla, aptitud para el uso, calidad, cantidad, precio, condiciones de venta o compra, disponibilidad, resultados"; art. 11 prohíbe toda presentación, publicidad o propaganda que mediante inexactitudes u ocultamientos pueda inducir a error, engaño o confusión respecto de, entre otros, el precio y las condiciones de comercialización; art. 26 j) encarga a la autoridad verificar "el cumplimiento de la obligación de exhibición o publicidad de precios"; art. 57 b) fija multa de 1 a 10.000.000 de Unidades Móviles; art. 72 deroga la Ley 22.802. En el texto leído no aparece una definición cuantitativa de "precio de referencia" ni de "precio anterior" (a diferencia del art. 6a europeo); la herramienta de lectura devolvió un resumen, así que no se descarta que alguna parte del decreto no haya sido revisada. Implicancia: en Argentina la demostración de una oferta engañosa descansa en el criterio general de "inducir a error"; un expediente de historial de precios (con fecha, captura y método reproducible) es la forma práctica de documentarlo. No se verificó si existen resoluciones de la autoridad de aplicación que definan precio de referencia o precio por unidad de medida (ver "Qué no se pudo verificar").
- Fuentes: https://raw.githubusercontent.com/clarius/normas/main/decreto/DN20190000274.md
- Confianza: media
- Riesgo: alto
- Vigencia: espejo consultado 7 de octubre de 2026; vigencia actual del decreto y sus modificaciones no verificadas

### H6 — Tipología de engaños con firma estadística (propuesta)
- Afirmación: Catálogo de nueve engaños con la señal observable y la regla del algoritmo (H21). Es una taxonomía de diseño propia; el respaldo externo disponible es parcial: la base abierta Open Prices modela tipos de descuento QUANTITY, SALE, SEASONAL, LOYALTY_PROGRAM y EXPIRES_SOON (lista parcial vista) y valida que price_without_discount sea mayor o igual a price; el proyecto PriceDive declara apuntar al patrón "primero sube y luego baja" (先涨后降) pero no publica umbrales ni algoritmo; los informes de organizaciones de consumidores (Which? y otros) no se pudieron abrir.
  - Precio ancla inflado: el tachado L existió pero rigió poco (0,10 ≤ S(L) < 0,30 o L/B > 1,15). Regla R3 con puntos parciales. Falso positivo típico: lanzamiento de un producto a precio alto durante pocas semanas.
  - Suba previa a la oferta: el precio real sube 8% o más en la zona de rampa (21 días antes del nuevo nivel) y el descuento real es menos de la mitad del aparente. Regla R4; la bandera exige que la suba aparezca en pesos deflactados por IPC y en dólares. Falso positivo típico: ajuste legítimo por costo o por salto cambiario (cubierto por el segundo numerario).
  - Precio tachado ficticio: S(L) < 0,10, es decir, el precio tachado casi nunca fue el precio vigente en los últimos 90 días. Bandera tachado_ficticio (−25). Falso positivo típico: el tachado es el precio recomendado o de otro canal (la UE excluye el recomendado del art. 6a) o el scraper no capturó el período.
  - Oferta perpetua: el descuento anunciado (tachado mayor a 1,1 veces el precio) aparece en 60% o más de los últimos 180 días. Bandera oferta_perpetua (−15).
  - Falsa urgencia o escasez: temporizadores que se reinician, "quedan pocas unidades" generado al azar. No entra al puntaje de precio; se guarda como evidencia (ver H7).
  - Reduflación: baja el contenido neto con precio igual o mayor (ver H9). Evento propio, no se mezcla con el puntaje de oferta.
  - Cuotas "sin interés" con precio de lista inflado: el precio de lista en cuotas supera al de contado o transferencia (ver H8).
  - Descuento sobre precio de lista vs. precio de contado: el "X% off" se calcula sobre un lista que ya incluye el financiamiento; se audita la serie de contado.
  - Descuento bancario o de fidelidad: precio condicionado; se audita aparte y se verifica que el precio de lista no haya subido en los días de la promoción bancaria.
- Fuentes: https://api.github.com/repositories/708093187/contents/open_prices/prices/constants.py?ref=4b84b556320a1bd865b9015e82a5b3a220fbcac7, https://raw.githubusercontent.com/openfoodfacts/open-prices/4b84b556320a1bd865b9015e82a5b3a220fbcac7/open_prices/prices/validators.py, https://github.com/DAILtech/PriceDive, https://api.github.com/repositories/1215547918/contents/literature/text/extracted_Foreign_writer_1907.07032v2_copy.pdf.txt?ref=efa1e2dcb8c97fc7f8e0e20aafb8fe9aaf15d63a
- Confianza: media
- Riesgo: bajo
- Vigencia: consultado 7 de octubre de 2026 (taxonomía de diseño; evidencia de organizaciones de consumidores no verificada)

### H7 — Falsa urgencia y escasez: qué proporción es demostrablemente falsa
- Afirmación: El estudio "Dark Patterns at Scale" (Mathur et al., ACM CSCW 2019, Princeton) rastreó unos 11.000 sitios de compras y halló 1.818 instancias de patrones oscuros en 1.254 sitios (aprox. 11,1%). Urgencia: 393 temporizadores de cuenta regresiva en 361 sitios, de los cuales 157 instancias en 140 sitios eran engañosas (se reiniciaban o seguían tras vencer, 40% de los temporizadores), y 88 mensajes de tiempo limitado en 84 sitios. Escasez: 632 mensajes de "poco stock" en 581 sitios, con 17 instancias en 17 sitios engañosas (valores aleatorios o deterministas, 2,7%), y 47 mensajes de alta demanda en 43 sitios. Prueba social: 313 notificaciones de actividad en 264 sitios, 29 engañosas en 20 sitios (9,3%). Implicancias: (1) desde afuera, la mayoría de los mensajes de urgencia y escasez no se puede probar falsa con una sola visita; se necesitan visitas repetidas (recargar, sesión nueva) y comparar el valor del contador; (2) el Detector debe guardar el texto y el valor del elemento y marcar urgencia_refutada o urgencia_no_verificable, sin afectar el puntaje de precio; (3) son cifras de un rastreo anterior a 2019: la prevalencia actual puede ser distinta. Los totales (1.818/1.254/11,1%) aparecen textuales en un resultado de búsqueda; el resto proviene de un resumen de la copia del artículo.
- Fuentes: https://raw.githubusercontent.com/Sumi2058/thesis-mba-it/efa1e2dcb8c97fc7f8e0e20aafb8fe9aaf15d63a/literature/text/extracted_Foreign_writer_1907.07032v2_copy.pdf.txt, https://github.com/aruneshmathur/dark-patterns
- Confianza: media
- Riesgo: alto
- Vigencia: estudio de 2019; copia del texto consultada 7 de octubre de 2026 (el original en arXiv no se pudo abrir)

### H8 — Cuotas "sin interés", precio de lista vs. contado y descuentos bancarios
- Afirmación: El art. 36 de la Ley 24.240 obliga, en crédito para consumo, a informar precio al contado, tasa efectiva anual y costo financiero total (H4), y un informe de septiembre de 2026 sobre crédito al consumo advierte que "las cuotas sin interés pueden ocultar financiación incorporada en el precio" y recomienda comparar el total con el precio de contado. Prueba determinista propuesta: con lista L pagada en n cuotas iguales y precio de contado o transferencia C, el spread s = L/C − 1 revela financiación oculta. La tasa mensual implícita r resuelve C = (L/n)·(1 − (1+r)^−n)/r (anualidad vencida; sin forma cerrada, se resuelve por bisección; si la primera cuota vence a 30 o 60 días por el ciclo de la tarjeta, hay que desplazar el flujo). Ejemplos calculados: L=1200, C=1000, n=6 da r = 5,47% mensual (89,5% efectiva anual); L=1200, C=1000, n=12 da 2,92% mensual (41,3% anual); L=1100, C=1000, n=3 da 4,92% mensual. Contraste con la inflación: con IPC de 3% mensual y pagos vencidos mensuales, 12 cuotas sin recargo valen en términos reales 82,95% del precio (17% de descuento real), por lo que "sin interés" sin spread es una oferta real en sí misma, y una lista inflada que lleve r por encima de la inflación mensual es financiación cara disfrazada. Regla: todos los tests de oferta se aplican a la serie de contado (C), no a la de lista. Descuentos bancarios y de fidelidad: se modelan como precio condicionado (price_kind distinto, como el tipo LOYALTY_PROGRAM de Open Prices); se auditan sobre la serie sin condición y se compara la serie de precio de lista en ventanas con y sin promoción bancaria (descontada la inflación) para detectar subas de lista sincronizadas con la promoción. SEPA trae además precio promocional y leyenda de promoción por producto y sucursal.
- Fuentes: https://raw.githubusercontent.com/KairumAI/landing/f8d3b9d9854734ed2c525d873a1ba7b2d076b756/public/informes/credicuotas/evidence/D-011.html, https://raw.githubusercontent.com/clarius/normas/main/ley/LNS0003875.md, https://api.github.com/repositories/708093187/contents/open_prices/prices/constants.py?ref=4b84b556320a1bd865b9015e82a5b3a220fbcac7, https://raw.githubusercontent.com/AlanMundler/SUPERBARATO/f779c898b31178ba84b8e6f57f99ce98fd8e3e2c/scripts/update_precios.py
- Confianza: media
- Riesgo: alto
- Vigencia: informe de terceros del 9 de septiembre de 2026; cálculos propios; consultado 7 de octubre de 2026 (si la normativa de cuotas o de recargos por tarjeta cambió no se verificó)

### H9 — Reduflación (shrinkflation): detectar por precio unitario
- Afirmación: Se define como una baja del contenido neto con precio igual o mayor, es decir, una suba del precio por unidad sin cambio en el precio de góndola. Regla propuesta: registrar (cantidad, unidad, pack) por GTIN y por la tupla (marca, línea, variante); cuando el contenido canónico cae 2% o más y el precio por unidad sube 2% o más en pesos constantes, emitir el evento reduflación con la frase "contenido −10% (500 g a 450 g), precio por kg +11%". El proyecto shrinkflation-detective (MIT) usa la misma definición: mide semanalmente el peso o volumen normalizado, convierte a gramos y mililitros y marca aumentos del precio por gramo o mililitro sin cambio del precio listado, y agrega un índice mensual por categoría; su limitación declarada es que depende de interpretar bien el tamaño en los títulos. Open Prices tiene el campo price_per; SEPA entrega precio de referencia y unidad de medida de referencia, lo que permite validar el cálculo propio. No se verificó incidencia ni regulación de la reduflación en Argentina.
- Fuentes: https://github.com/aansensei/shrinkflation-detective, https://raw.githubusercontent.com/neaserisgod/Nodo-Sur-Pos/060ba8b767b23ea5b593b7ee6a856d57e2666371/lib/servicios/comparador_precios.dart, https://github.com/openfoodfacts/open-prices
- Confianza: media
- Riesgo: bajo
- Vigencia: consultado 7 de octubre de 2026 (shrinkflation-detective actualizado el 9/6/2026 según la búsqueda de repositorios)

### H10 — Estadística de base: mediana ponderada por tiempo, percentiles y MAD
- Afirmación: El precio publicado es una función escalón. Calcular medianas sobre las observaciones (cada scrape) o sobre los cambios de precio sesga el resultado (un precio que duró 80 días pesa igual que otro que duró 2). La mediana correcta pesa cada precio por el tiempo que rigió; en una grilla diaria con arrastre de la última observación, 1 día = 1 peso y coincide con la mediana de los valores diarios. Para intervalos irregulares: ordenar por valor y acumular duraciones hasta cubrir la mitad. Percentiles: statistics.quantiles(data, n=100, method="inclusive") de la biblioteca estándar (por defecto "exclusive"; "inclusive" trata el mínimo y el máximo como percentiles 0 y 100; con un solo dato devuelve data·(n−1); vacío levanta StatisticsError). MAD: scipy.stats.median_abs_deviation(x, scale="normal") divide por 0,67449 (inversa del cuantil 0,75 de la normal) para ser consistente con la desviación estándar; el docstring muestra 1,3487 sin escala y 1,9996 con escala en una muestra normal de sigma=2. Se debe aplicar sobre log-precios (los cambios son multiplicativos). Trampa: en series escalón la MAD es 0 si más de la mitad de los valores son iguales; usar un piso sigma_min = max(1,4826·MAD, 0,005). Puntaje robusto para errores de precio: M = 0,6745·(x − mediana)/MAD con umbral 3,5 (criterio de Iglewicz y Hoaglin, de memoria, no verificado en esta sesión). La "regla de N días" (mínimo de 30 días de la UE) es un caso particular; el algoritmo reporta k = días desde la última vez que hubo un precio real menor, que generaliza esa regla a cualquier ventana.
  ```python
  def tw_quantile(intervals, q):   # intervals: [(valor, dias)]
      total, acc = sum(w for _, w in intervals), 0.0
      for v, w in sorted(intervals):
          acc += w
          if acc >= q * total:
              return v
  ```
- Fuentes: https://raw.githubusercontent.com/python/cpython/2639fd65ff8e0c1949c480a8e670fe9c2467a1f8/Lib/statistics.py, https://raw.githubusercontent.com/scipy/scipy/main/scipy/stats/_stats_py.py
- Confianza: alta
- Riesgo: bajo
- Vigencia: código fuente de las bibliotecas consultado 7 de octubre de 2026 (SciPy 1.18.1, subida el 21/08/2026)

### H11 — Detección de puntos de cambio: ruptures (PELT) y BOCPD
- Afirmación: ruptures 1.1.10 (BSD-2-Clause, subida el 10/09/2025; PyPI exige Python mayor o igual a 3.9 y menor a 3.14, mientras el README de GitHub dice "3.10-3.14": dos fuentes que se contradicen, conviene fijar Python 3.12 o 3.13) implementa Pelt, Binseg, BottomUp, Window, Dynp y KernelCPD. En Pelt: model puede ser "l1", "l2" o "rbf"; min_size=2 y jump=5 por defecto (jump=5 submuestrea los candidatos a un cambio cada 5 puntos: con precios diarios y escalones cortos usar jump=1); pen>0 penaliza cada punto de cambio (minimiza error de aproximación + número de cambios × pen). El costo L1 usa la desviación absoluta respecto de la mediana del segmento, por lo que es robusto a valores atípicos y es el natural para escalones con errores de precio. Uso propuesto: serie diaria de log-precio real, algo = rpt.Pelt(model="l1", min_size=3, jump=1).fit(x); bkps = algo.predict(pen=beta·sigma·log(n)) con beta en {1, 2, 3} elegido por validación (la fórmula de pen es una propuesta propia, no de la biblioteca). Para qué sirve: (1) separar régimen normal de régimen promocional; (2) distinguir una caída transitoria (segmento corto que vuelve al nivel previo) de un reprecio permanente; (3) detectar la rampa previa. BOCPD (Adams y MacKay, 2007): detección bayesiana online que mantiene la distribución posterior del "run length"; gwgundersen/bocd (BSD-3-Clause, 111 estrellas, 12 commits) la implementa en un solo archivo con modelo gaussiano de media desconocida y varianza conocida y riesgo (hazard) constante de ejemplo 1/100; el paquete bayesian-changepoint-detection de PyPI está en 0.2.dev1 (12/08/2019), sin licencia declarada, y no conviene como dependencia. Honestidad metodológica: los cambios de precio en una web son eventos explícitos, así que CPD no hace falta para saber "que cambió"; sirve para fuentes ruidosas (varios precios por sucursal), para agrupar escalones en regímenes y para tendencias. Para la primera versión bastan las reglas de H21; CPD queda como segunda etapa. La cita original de PELT (Killick, Fearnhead y Eckley, 2012) no apareció en el código leído.
- Fuentes: https://pypi.org/pypi/ruptures/1.1.10/json, https://github.com/deepcharles/ruptures, https://raw.githubusercontent.com/deepcharles/ruptures/master/src/ruptures/detection/pelt.py, https://raw.githubusercontent.com/deepcharles/ruptures/master/src/ruptures/costs/costl1.py, https://github.com/gwgundersen/bocd, https://raw.githubusercontent.com/gwgundersen/bocd/master/bocd.py, https://pypi.org/pypi/bayesian-changepoint-detection/json
- Confianza: alta
- Riesgo: alto
- Vigencia: consultado 7 de octubre de 2026 (ruptures 1.1.10 del 10/09/2025)

### H12 — Datos faltantes, errores de precio y quiebres de stock
- Afirmación: Convenciones observadas en proyectos reales: el cliente de Keepa representa "sin oferta o sin stock" con el valor −1 (no con 0) y usa tiempos en minutos; Open Prices valida que el precio exista, que price_is_discounted esté definido si hay price_without_discount, que price_without_discount sea mayor o igual a price y que la fecha no sea futura; SUPERBARATO descarta filas con precio de lista menor o igual a 0. Política propuesta (diseño propio): (a) sin stock o sin precio es "desconocido" (None), nunca 0, y queda fuera de las ponderaciones; (b) arrastre de la última observación hasta 3 días y después "desconocido"; (c) cobertura = días con dato / días de la ventana; con menos de 45 de 90 días la salida es "datos insuficientes"; (d) outliers: se pone en cuarentena 48 horas un precio con |M| mayor a 3,5 en log-precio que además revierta en 2 observaciones o menos, y se exige una segunda captura independiente; si persiste, se informa "posible error de precio" (mensaje distinto) y no entra en la base B; (e) "reaparece tras un quiebre a un precio mayor" es un evento propio; (f) con varias capturas por día se toma la última del día local (America/Argentina/Buenos_Aires) y se guardan todas; (g) el precio puede variar por sucursal o zona: la clave es (comercio, sucursal, producto). En la prueba de humo, descartar 1 de cada 3 observaciones no cambió el veredicto gracias al arrastre de 3 días.
- Fuentes: https://github.com/akaszynski/keepa, https://raw.githubusercontent.com/openfoodfacts/open-prices/4b84b556320a1bd865b9015e82a5b3a220fbcac7/open_prices/prices/validators.py, https://raw.githubusercontent.com/AlanMundler/SUPERBARATO/f779c898b31178ba84b8e6f57f99ce98fd8e3e2c/scripts/update_precios.py
- Confianza: media
- Riesgo: bajo
- Vigencia: consultado 7 de octubre de 2026 (convenciones de terceros; política propia)

### H13 — Estacionalidad por eventos (Hot Sale, CyberMonday, Black Friday)
- Afirmación: Una guía de un sitio argentino de comparación de precios (PrecioRadar) afirma que el Hot Sale (mayo) y el CyberMonday (noviembre) son momentos de buenos precios y advierte "verificar siempre que no estén inflados", y que el Día del Padre (junio) también baja precios en celulares; no se verificaron las fechas de 2026 ni su vigencia (confianza baja). Método propuesto: (1) mantener una tabla manual de eventos con fuente y fechas por año, y etiquetar cada día con su evento; (2) excluir las ventanas de evento de la base B para no contaminarla con promociones previas; (3) comparar el precio de evento contra la base fuera de evento del mismo año (±45 días), contra el mismo evento del año anterior en pesos constantes (exige 12 a 13 meses de historia propia) y contra otros comercios el mismo día; (4) si no hay un año de historia, no afirmar estacionalidad y limitarse a las comparaciones (i) y (iii). statsmodels (0.15.0, subida el 27/08/2026) ofrece descomposición estacional, pero necesita al menos dos ciclos completos por serie, algo raro a nivel de producto: es preferible la tabla de eventos.
- Fuentes: https://api.github.com/repositories/1239312722/contents/src/content/guides/index.ts?ref=89489c632f85bc3323274df2f6b01707fa542cf6, https://pypi.org/pypi/statsmodels/0.15.0/json
- Confianza: baja
- Riesgo: alto
- Vigencia: consultado 7 de octubre de 2026 (fechas de eventos 2026 no verificadas)

### H14 — Inflación argentina: por qué los precios nominales engañan y cómo deflactar
- Afirmación: Con inflación mensual π, un precio nominal que no cambia durante m meses cae en términos reales 1 − (1+π)^−m; con π = 3% y m = 6, cae 16,25%. El engaño ocurre en los dos sentidos: (i) un detector nominal "mínimo de N días" calla ante una baja real porque los precios viejos eran nominalmente más bajos (ejemplo ejecutado: inflación 4% mensual, precio que sigue al IPC y baja 10% nominal hoy; el mínimo nominal de los 120 días previos es 851 y el precio de hoy es 900, luego no alerta; deflactado, la baja es 10% y el mínimo es de 396 días, es decir, de toda la historia disponible); (ii) un precio que no se mueve parece "estable" mientras en realidad se abarata. Deflactor propuesto: p_real(d) = p(d)·IPC(t_ref)/IPC(d). El IPC mide el promedio del mes: se ancla cada nivel mensual en el día 15 y se interpola geométricamente por día; para meses todavía no publicados se extrapola con la última tasa y se marca "estimado" (se recalcula al publicarse); en cada decisión se guarda la versión (vintage) de la serie usada para poder reproducirla. Riesgos de la referencia: el IPC nivel general no es la inflación de cada producto (hay series por región y divisiones; en un proyecto se ven ids regionales como 103.1_I2N_2016_M_19 junto al nacional); hay rezago de publicación; puede haber cambios de base o canasta (una nota periodística copiada en un repositorio dice que el IPC usa ponderadores de la ENGHo 2004/05 y que la ENGHo 2017/18 no fue implementada; el estado a octubre de 2026 no se verificó y un cambio de base exigiría empalmar series). El proyecto reporte_variaciones replica la metodología del INDEC para armar un índice propio con datos de supermercados (Jevons dentro de categorías elementales, Laspeyres hacia arriba, encadenamiento), útil como modelo si se construye un índice propio.
- Fuentes: https://api.github.com/repositories/1188379008/contents/src/app/application/skills/registry.py?ref=c26cb1d940c998f7b50cd3a128de27c2d54669f0, https://api.github.com/repositories/1188379008/contents/src/app/prompts/planner.txt?ref=c26cb1d940c998f7b50cd3a128de27c2d54669f0, https://raw.githubusercontent.com/joacoabraldes/reporte_variaciones/52d7ba7c55e2dd010a288f683eae6b2ad9023808/README.md, https://api.github.com/repositories/1045880170/contents/1-Scraping/clarin/outputs/clarin_pag_130.csv?ref=d2211dda52083bb4e4ed2982f58da437425f6d8c
- Confianza: media
- Riesgo: alto
- Vigencia: consultado 7 de octubre de 2026 (cálculos propios; estado actual del IPC y de su base no verificado)

### H15 — API de series de tiempo de datos.gob.ar: parámetros, límites e ids
- Afirmación: La API (aplicación Django y ElasticSearch, licencia MIT del software, estado "beta" sin garantías formales, producción en https://apis.datos.gob.ar/series) acepta ids (hasta 40 series separadas por coma), representation_mode (value, change, change_since_beginning_of_year, percent_change, percent_change_a_year_ago, percent_change_since_beginning_of_year), collapse (year, semester, quarter, month, week, day), collapse_aggregation (avg por defecto, sum, end_of_period, min, max), limit (por defecto 100, máximo 1000), start, start_date y end_date (ISO 8601: año, año-mes o fecha completa), format (json por defecto, csv), header (titles, ids, descriptions), sort (asc, desc), metadata (none, simple, full, only), decimal, sep, flatten y last. Se pueden combinar agregación y transformación con la sintaxis serie:agregación:transformación y siempre se aplica primero la agregación. Límites por IP: 60 pedidos por segundo, 2.000 por minuto, 40.000 por hora y 200.000 por día; cada serie tiene la licencia de su publicador (visible con metadata=full). Ids vistos en la documentación y en proyectos: IPC nacional nivel general 148.3_INIVELNAL_DICI_M_26 (aparece en la documentación oficial como ejemplo de identificador y con :percent_change y :percent_change_a_year_ago, lo que implica que es un nivel de índice; otro proyecto lo rotula "variación % mensual", así que hay que confirmarlo con metadata=full); tipo de cambio 168.1_T_CAMBIOR_D_0_0_26 (ejemplo de "tipo de cambio" en la guía de inicio) y 92.2_TIPO_CAMBIION_0_0_21_24 (visto en otro proyecto). No se verificó la última fecha disponible de ninguna serie ni qué tipo de cambio mide cada id: consultar metadata=full antes de usarlas. Ejemplo de URL visto en la documentación de componentes: https://apis.datos.gob.ar/series/api/series/?ids=148.3_INIVELNAL_DICI_M_26:percent_change&last=12. En esta sesión el dominio apis.datos.gob.ar estaba bloqueado, de modo que no se hizo ninguna llamada real.
- Fuentes: https://github.com/datosgobar/series-tiempo-ar-api, https://raw.githubusercontent.com/datosgobar/series-tiempo-ar-api/master/README.md, https://raw.githubusercontent.com/datosgobar/series-tiempo-ar-api/master/docs/reference/api-reference.md, https://raw.githubusercontent.com/datosgobar/series-tiempo-ar-api/master/docs/additional-parameters.md, https://raw.githubusercontent.com/datosgobar/series-tiempo-ar-api/master/docs/terms.md, https://raw.githubusercontent.com/datosgobar/series-tiempo-ar-api/master/docs/quick-start.md, https://api.github.com/repositories/97857863/contents/docs/publishers/identifiers.md?ref=82a7b2a388a297841cb5f8d9263a26a05bad07e5, https://api.github.com/repositories/132630306/contents/docs/components/graphic.html?ref=368bffa424f6b2596ba50e45c508933ea9c746df
- Confianza: alta
- Riesgo: alto
- Vigencia: documentación del repositorio consultada 7 de octubre de 2026 (puede haber cambiado en el servicio en producción)

### H16 — API del BCRA: Estadísticas Cambiarias v1.0 y Principales Variables v3.0
- Afirmación: Según un espejo del OpenAPI oficial, "Estadísticas Cambiarias" v1.0 tiene servidor https://api.bcra.gob.ar y tres endpoints: GET /estadisticascambiarias/v1.0/Maestros/Divisas (catálogo de monedas: código de hasta 3 caracteres y denominación de hasta 50), GET /estadisticascambiarias/v1.0/Cotizaciones con el parámetro opcional fecha (cotizaciones de una fecha: detalle con codigoMoneda, descripcion, tipoPase y tipoCotizacion) y GET /estadisticascambiarias/v1.0/Cotizaciones/{codMoneda} con fechaDesde, fechaHasta, limit y offset (historial, con metadatos de cantidad, offset y limit); contacto api@bcra.gob.ar. Un adaptador de Frankfurter comenta que el endpoint general "solo acepta una fecha por pedido" y recorre día por día saltando fines de semana. Otros proyectos consumen /estadisticas/v3.0/Monetarias (lista de variables) y /Monetarias/{idVariable}; un script referencia la documentación en https://www.bcra.gob.ar/Catalogo/Content/files/pdf/principales-variables-v3.pdf (no abierta). No se verificaron términos de uso, límites de pedidos, qué cotización exacta devuelve tipoCotizacion para USD (probablemente la de referencia oficial) ni si existen versiones posteriores a v1.0 y v3.0.
- Fuentes: https://raw.githubusercontent.com/opusoffline/dolarshift/ade37e7b1fdebfe7e7dc733e3480da0b321b978f/estadisticascambiarias-v1.json, https://api.github.com/repositories/124404569/contents/lib/provider/adapters/bcra.rb?ref=71334f73e9e67d4ceb2d54a03f9f4a66399327f4, https://api.github.com/repositories/985008031/contents/src/bcra.js?ref=822ace3571acb2c7d934b509e6761d816eea6bc1, https://api.github.com/repositories/738672609/contents/scripts/utils/bcra_estadisticas_monetarias_api.R?ref=82d8a7eefe6bc22376404ddc8f4d2e58108a8bde, https://api.github.com/repositories/304836585/contents/pkg/exchangerates/central_bank_of_argentina_datasource.go?ref=499f27b6b7cfef8f78aa098e961f4c949351f543
- Confianza: media
- Riesgo: alto
- Vigencia: espejo y código de terceros consultados 7 de octubre de 2026 (los dominios del BCRA estaban bloqueados)

### H17 — Dólar como segunda referencia y regla de dos numerarios
- Afirmación: La API del BCRA devuelve cotizaciones oficiales; en el OpenAPI leído no hay MEP, CCL ni dólar paralelo. Proyectos de terceros obtienen esas cotizaciones de APIs comunitarias: https://dolarapi.com/v1/dolares (actual) y https://api.argentinadatos.com/v1/cotizaciones/dolares (histórico; también /oficial y /contadoconliqui); no se verificó su licencia, disponibilidad ni definiciones, y no tienen garantía de servicio conocida. Riesgos por referencia: IPC (rezago, base, no es el precio del producto, H14); dólar oficial (puede divergir del costo real de reposición según el régimen cambiario, cuyo estado a octubre de 2026 no se verificó); MEP o CCL (depende de la fuente y de la definición del título y plazo, no verificado); índices propios de supermercado (sesgo de cobertura: el pan suelto no se mide por falta de presentación normalizada). Regla de dos numerarios, diseño propio probado en la prueba de humo: acusar (suba previa y tachado ficticio) solo si la falla aparece en pesos deflactados por IPC y en dólares constantes; acreditar (profundidad y mínimo) en el numerario configurado por categoría (alimentos y limpieza en IPC; electro, tecnología e importados en dólar). Resultado ejecutado: salto del dólar de 20% con precio en pesos que lo sigue y "descuento" de 15% posterior; numerario IPC da 27 puntos y "sin valor real" sin acusar de suba previa; numerario dólar da 90 puntos y "oferta real" (la baja es real en dólares).
- Fuentes: https://api.github.com/repositories/1106058349/contents/dolares.py?ref=0a590cac5c7548b8910f5fb31ab0b8db114e981e, https://api.github.com/repositories/1361205912/contents/src/fuentes/dolar.js?ref=a939b408915c88d47516027ca0a34cc43f45de31, https://api.github.com/repositories/1340533585/contents/scripts/download_argentinadatos_api_cotizaciones-ccl.py?ref=0d590070fc3baae533b7e0d23ade9157329db942, https://raw.githubusercontent.com/opusoffline/dolarshift/ade37e7b1fdebfe7e7dc733e3480da0b321b978f/estadisticascambiarias-v1.json
- Confianza: media
- Riesgo: alto
- Vigencia: consultado 7 de octubre de 2026 (las APIs comunitarias solo se vieron en código de terceros; no se llamaron)

### H18 — Datos de precios de supermercados argentinos: SEPA y Precios Claros
- Afirmación: El dataset abierto SEPA se publica en datos.produccion.gob.ar (id de dataset 6f47ec76-d1ce-4e34-a7e1-621fe9b1d0b5) como siete ZIP, uno por día de la semana (sepa_lunes.zip a sepa_domingo.zip) con URLs de recurso estables; cada ZIP contiene ZIP por comercio con comercio.csv, sucursales.csv y productos.csv separados por barra vertical, UTF-8 con BOM. En productos.csv, id_producto es el EAN real y productos_ean es un indicador 0/1 de si ese código es válido (sin el 1, el producto debe cruzarse por descripción); hay descripción, precio de lista, precio de referencia (por unidad de medida), unidad de medida de referencia, marca, cantidad y unidad de presentación, precio promocional y leyenda de promoción (identificados por posición de columna en un script de terceros). No se verificaron la licencia (un comentario de un script dice CC-BY), la retención histórica ni el esquema vigente: conviene archivar cada día los ZIP propios. Un proyecto que arma un índice con SEPA menciona un "TTL de 12 meses" (ambiguo: puede ser retención propia) y que el pan suelto no se mide. Precios Claros (portal): OpenDataCordoba/precios_claros es un crawler Scrapy (27 estrellas, actualizado el 12/06/2026) que descarga productos, precios y sucursales con id de producto (EAN), precio de lista, mínimo, máximo, presentación y marca; martjanz/precios-claros (2018) avisa que cualquier cambio de la API lo rompe. Línea de base local ya existente: SUPERBARATO (creado el 10/09/2026, Córdoba Capital) calcula por EAN la mediana entre comercios (con al menos 2 precios), dto_honesto = (mediana − precio)/mediana, y marca inflado si precio_lista > 2 × mediana; es una regla transversal, sin dimensión temporal y con umbral arbitrario, útil como comparación en la validación (H24).
- Fuentes: https://raw.githubusercontent.com/neaserisgod/Nodo-Sur-Pos/060ba8b767b23ea5b593b7ee6a856d57e2666371/lib/servicios/comparador_precios.dart, https://raw.githubusercontent.com/AlanMundler/SUPERBARATO/f779c898b31178ba84b8e6f57f99ce98fd8e3e2c/scripts/update_precios.py, https://raw.githubusercontent.com/joacoabraldes/reporte_variaciones/52d7ba7c55e2dd010a288f683eae6b2ad9023808/README.md, https://github.com/OpenDataCordoba/precios_claros, https://github.com/martjanz/precios-claros
- Confianza: media
- Riesgo: alto
- Vigencia: código de terceros consultado 7 de octubre de 2026 (el portal oficial y el dataset estaban bloqueados; no se descargó ningún ZIP)

### H19 — Normalización de unidades y de precios
- Afirmación: Unidades canónicas propuestas: masa en gramos, volumen en mililitros, longitud en metros, conteo en unidades; precio por 100 g o 100 ml y por kg o litro (SEPA ya trae precio de referencia y unidad de referencia: usarlos para validar el cálculo propio, tolerancia 2%). Precios: el formato argentino "1.234,56" exige un parser robusto; price-parser 0.5.1 (BSD-3-Clause, subida el 19/03/2026, Python mayor o igual a 3.9) extrae importe y símbolo de moneda manejando separadores de miles y decimales (probar con casos argentinos antes de adoptarlo). Cantidades: regex propios con diccionario (kg, g, gr, grs, l, lt, lts, ml, cc, cm3, un, u, docena, "x6", "pack x 4", "x 2 x 500 ml"); contenido total = pack × cantidad; Pint 0.26.1 (BSD, Python mayor o igual a 3.12, subida el 10/09/2026) sirve si se quiere conversión dimensional formal. Promociones por cantidad: precio efectivo por unidad 2x1 = P/2; 3x2 = 2P/3; "70% en la segunda" = 0,65·P por unidad; se registran con price_kind=QUANTITY y mínimo de compra. GTIN: python-stdnum 2.2 (LGPL, 04/01/2026) valida EAN-8, UPC-A de 12, EAN-13 y GTIN-14 con el dígito de control (pesos alternados 3 y 1 desde la derecha; dígito = (10 − suma) mod 10); normalizar a GTIN-14 con ceros a la izquierda antes de comparar.
- Fuentes: https://pypi.org/pypi/price-parser/0.5.1/json, https://pypi.org/pypi/pint/0.26.1/json, https://raw.githubusercontent.com/arthurdejong/python-stdnum/master/stdnum/ean.py, https://pypi.org/pypi/python-stdnum/2.2/json, https://raw.githubusercontent.com/neaserisgod/Nodo-Sur-Pos/060ba8b767b23ea5b593b7ee6a856d57e2666371/lib/servicios/comparador_precios.dart
- Confianza: media
- Riesgo: alto
- Vigencia: consultado 7 de octubre de 2026 (versiones de PyPI; reglas de promoción y parser son diseño propio no probado)

### H20 — Emparejamiento entre comercios y cómo evitar falsos emparejamientos
- Afirmación: Pipeline por etapas con confianza decreciente. E0: igualdad exacta de GTIN-14 validado (en SEPA, solo si productos_ean = 1): aceptar automáticamente. E1: bloqueo por marca normalizada + contenido neto canónico + cantidad de unidades por pack para generar candidatos. E2: similitud de texto con RapidFuzz 3.14.6 (MIT, Python mayor o igual a 3.11, subida el 30/08/2026), por ejemplo token_set_ratio mayor o igual a 90, siempre sujeta a las guardas. E3: modelo probabilístico con Splink 5.0.0 (MIT, Python mayor o igual a 3.10, motores DuckDB, Spark y PostgreSQL, subida el 28/09/2026), recordlinkage 0.16 (BSD-3-Clause, última versión del 20/07/2023: poco mantenida) o dedupe 3.0.3 (MIT, aprendizaje activo). E4: embeddings con sentence-transformers 6.1.0 (Apache-2.0, subida el 18/09/2026) solo para generar candidatos, nunca para aceptar. Todo lo que no sea E0 va a una cola de revisión humana; las decisiones se guardan en una tabla dorada con pares positivos y negativos. Guardas duras antes de aceptar cualquier match sin GTIN: (1) contenido neto canónico igual dentro de ±1%, si no, el par se marca "misma línea, otro tamaño" y solo se compara el precio unitario; (2) igual cantidad por pack; (3) coincidencia de las palabras de variante críticas (sabor, color, capacidad GB o TB, talle, "light", "zero", "sin azúcar", modelo o año); (4) misma marca, salvo marca propia declarada; (5) asignación 1 a 1 por comercio, resuelta con un algoritmo de asignación y no con "el mejor candidato" voraz; (6) no usar el precio como evidencia de identidad (circularidad con lo que se quiere medir). Errores típicos: mismo nombre con distinto tamaño, kits y combos, mismo producto con GTIN nuevo (historial roto: guardar una tabla de sucesores).
- Fuentes: https://pypi.org/pypi/rapidfuzz/3.14.6/json, https://pypi.org/pypi/splink/5.0.0/json, https://pypi.org/pypi/recordlinkage/json, https://pypi.org/pypi/dedupe/json, https://pypi.org/pypi/sentence-transformers/6.1.0/json, https://raw.githubusercontent.com/arthurdejong/python-stdnum/master/stdnum/ean.py, https://raw.githubusercontent.com/neaserisgod/Nodo-Sur-Pos/060ba8b767b23ea5b593b7ee6a856d57e2666371/lib/servicios/comparador_precios.dart
- Confianza: media
- Riesgo: alto
- Vigencia: consultado 7 de octubre de 2026 (versiones y fechas de PyPI; el pipeline y las guardas son diseño propio)

### H21 — Especificación del algoritmo: entradas, pasos, reglas, umbrales y puntaje
- Afirmación: Entradas: observaciones (día, precio o None, precio tachado o None), índice de IPC y de dólar como funciones del día, numerario por categoría (cpi o usd), precios actuales de otros comercios ya emparejados (opcional) y configuración. Pasos: (1) grilla diaria con arrastre máximo de 3 días; (2) deflactar a pesos de hoy por IPC y a dólares constantes; (3) hallar r, inicio del nivel de precio actual (±1%); (4) si el nivel dura 60 días o más no hay "evento": solo se auditan reclamos (tachado y oferta perpetua); (5) base B = mediana por tiempo del precio real en [r−111, r−22], con al menos 45 días observados; (6) reglas con puntos; (7) puntaje = 100 × ganado / disponible + penalidades de banderas, acotado a [0, 100]; (8) etiqueta; (9) explicación por plantillas. Reglas: R1 profundidad 35·clip(nd/0,20) con nd = 1 − P0/B; R2 mínimo 20·clip(k/180), k = días desde el último precio real menor (tope: historia disponible); R3 ancla (solo si hay tachado hoy) 15·clip(S/0,30), bandera tachado_ficticio (−25) si S < 0,10, donde S es el mayor entre los dos numerarios; R4 suba previa 15 puntos, 7 si la suba es de 4% o más, 0 con bandera suba_previa (−25) si la suba es de 8% o más en ambos numerarios y nd < 0,5 × descuento aparente (1 − P0/H, con H la mediana de la última semana antes de r); R5 mercado 15·clip(((m − P0)/m)/0,10) con al menos 3 comparables (m = su mediana); R6 oferta perpetua, bandera (−15) si el descuento anunciado (tachado mayor a 1,1 veces el precio) aparece en 60% o más de los últimos 180 días. Etiquetas: engañosa (hay bandera), oferta real (75 o más), dudosa (50 a 74), sin valor real (menos de 50), datos insuficientes, sin evento. Umbrales y justificación (todos heurísticos y no calibrados con datos reales, salvo el de 30 días que viene de la norma europea): 30 días para el "precio anterior" legal (H2); base de 90 días (un trimestre, suficiente para un régimen estable; calibrar en {60, 90, 120}); zona de rampa de 21 días (acumulación previa de campañas; calibrar en {14, 21, 28}); mismo nivel ±1% (ruido de redondeo); suba previa de 8% (por encima del ruido semanal; calibrar en {5, 8, 10}); saturación de profundidad en 20% y de mínimo en 180 días (medio año cubre un ciclo de eventos grandes); anclas 10% y 30%; oferta perpetua 60% de 180 días; cobertura mínima 45 de 90 días; arrastre de 3 días. Notificación sugerida al usuario: puntaje 75 o más y nd de 10% o más, configurable.
- Fuentes: https://raw.githubusercontent.com/open-mercato/open-mercato/fefc71d09efe2aa8c732dc6fafaa084a0e0dae3c/.ai/specs/2026-06-30-omnibus-price-tracking.md, https://raw.githubusercontent.com/scipy/scipy/main/scipy/stats/_stats_py.py
- Confianza: media
- Riesgo: bajo
- Vigencia: diseño propio ejecutado el 7 de octubre de 2026 (umbrales no calibrados)

### H22 — Seudocódigo ejecutable y corrida de humo en escenarios sintéticos
- Afirmación: Implementación de referencia, solo biblioteca estándar de Python 3.10 o superior (probada con Python 3.13.16), que aplica H21 y devuelve un diccionario explicable.
  ```python
  """Credibilidad de ofertas: nucleo determinista (solo biblioteca estandar, Python >= 3.10)."""
  from __future__ import annotations
  from dataclasses import dataclass
  from datetime import date, timedelta
  from statistics import median
  from typing import Callable

  DAY = timedelta(days=1)


  @dataclass(frozen=True)
  class Obs:
      day: date
      price: float | None              # None = sin stock / sin precio (nunca 0)
      list_price: float | None = None  # precio "tachado" declarado en la pagina ese dia


  @dataclass(frozen=True)
  class Cfg:
      max_gap: int = 3         # dias maximos de arrastre (LOCF) sin observacion
      base_win: int = 90       # ventana de base (dias) previa a la rampa
      ramp_win: int = 21       # ventana previa al inicio del precio actual (zona de "rampa")
      level_tol: float = 0.01  # dos precios dentro de +-1% son el "mismo nivel"
      hike: float = 0.08       # suba previa minima para sospechar
      min_days: int = 45       # dias observados minimos en la ventana de base
      long_run: int = 60       # precio sin cambios >= N dias: no hay "evento", solo se auditan reclamos
      anchor_fict: float = 0.10
      anchor_ok: float = 0.30
      perpetual: float = 0.60


  def daily_grid(obs, start: date, end: date, max_gap: int):
      """Funcion escalon diaria: arrastra la ultima observacion hasta max_gap dias; despues, None."""
      seen = {o.day: o for o in obs}
      grid, last_day, last = {}, None, None
      d = start
      while d <= end:
          if d in seen:
              last_day, last = d, seen[d]
          grid[d] = last.price if last_day is not None and (d - last_day).days <= max_gap else None
          d += DAY
      return grid


  def make_index(points: dict[date, float]) -> Callable[[date], float]:
      """Nivel de un indice (IPC o dolar) en cualquier dia: interpolacion geometrica entre puntos."""
      pts = sorted(points.items())

      def at(d: date) -> float:
          i = 0
          while i < len(pts) - 2 and d > pts[i + 1][0]:
              i += 1
          (d1, v1), (d2, v2) = pts[i], pts[i + 1]
          return v1 * (v2 / v1) ** ((d - d1).days / (d2 - d1).days)  # extrapola con la tasa del tramo

      return at


  def to_real(grid, index_at, ref: date):
      """Pesos de la fecha `ref` equivalentes: p * indice(ref) / indice(d)."""
      k = index_at(ref)
      return {d: (None if p is None else p * k / index_at(d)) for d, p in grid.items()}


  def vals(g, a: date, b: date):
      return [p for d, p in g.items() if a <= d <= b and p is not None]


  def clip(x, lo=0.0, hi=1.0):
      return max(lo, min(hi, x))


  def claim_flags(obs, real_cpi, real_usd, t0, lo_day, hi_day, cfg, expl):
      """Audita el precio tachado de hoy y la persistencia del descuento anunciado."""
      flags, pts = [], None
      L = next((o.list_price for o in obs if o.day == t0 and o.list_price), None)
      if L:
          def share(g):
              w = vals(g, lo_day, hi_day)
              return sum(1 for p in w if p >= 0.98 * L) / max(len(w), 1)
          S = max(share(real_cpi), share(real_usd))   # acusar exige que fallen AMBOS numerarios
          pts = 15 * clip(S / cfg.anchor_ok)
          if S < cfg.anchor_fict:
              flags.append(("tachado_ficticio", -25))
              expl.append(f"el precio tachado ${L:,.0f} solo rigio el {S:.0%} de los ultimos 90 dias")
      since = t0 - timedelta(days=180)
      seen = [o for o in obs if o.day >= since and o.price]
      anun = [o for o in seen if o.list_price and o.list_price > 1.1 * o.price]
      if seen and len(anun) / len(seen) >= cfg.perpetual:
          flags.append(("oferta_perpetua", -15))
          expl.append(f"anuncia descuento el {len(anun) / len(seen):.0%} de los ultimos 180 dias")
      return flags, pts


  def evaluate(obs, t0: date, cpi, fx, numeraire="cpi", comps=None, cfg: Cfg = Cfg()):
      """Devuelve un dict explicable. `comps`: precios actuales de otros comercios (mismo producto, en pesos de t0)."""
      first = min((o.day for o in obs if o.price), default=None)
      if first is None:
          return {"estado": "sin_datos"}
      start = max(first, t0 - timedelta(days=365 + cfg.base_win))
      nom = daily_grid(obs, start, t0, cfg.max_gap)
      r_cpi, r_usd = to_real(nom, cpi, t0), to_real(nom, fx, t0)
      real, alt = (r_cpi, r_usd) if numeraire == "cpi" else (r_usd, r_cpi)
      P0n = nom[t0]
      if P0n is None:
          return {"estado": "sin_precio_hoy"}
      r = t0                                           # inicio del nivel de precio actual
      while nom.get(r - DAY) is not None and abs(nom[r - DAY] / P0n - 1) <= cfg.level_tol:
          r -= DAY
      base_a = r - timedelta(days=cfg.ramp_win + cfg.base_win)
      base_b = r - timedelta(days=cfg.ramp_win + 1)
      base = vals(real, base_a, base_b)
      expl = []
      if len(base) < cfg.min_days:
          if (t0 - r).days >= cfg.long_run:            # sin evento de precio: solo auditar reclamos
              flags, _ = claim_flags(obs, r_cpi, r_usd, t0, t0 - timedelta(days=90), t0, cfg, expl)
              return {"estado": "sin_evento", "flags": [f for f, _ in flags], "porque": "; ".join(expl)}
          return {"estado": "datos_insuficientes", "dias_base": len(base)}

      P0, B = real[t0], median(base)                   # mediana por tiempo: 1 dia = 1 peso
      nd = 1 - P0 / B                                  # descuento neto vs. la base, en pesos constantes
      rules = [("profundidad", 35 * clip(nd / 0.20), 35)]
      expl.append(f"{abs(nd):.0%} {'menos' if nd >= 0 else 'mas'} que la mediana de {len(base)} dias (pesos constantes)")

      lower = [d for d, p in real.items() if d < r and p is not None and p < P0]
      k = (r - max(lower)).days if lower else (r - first).days
      rules.append(("minimo", 20 * clip(k / 180), 20))
      expl.append(f"es el minimo de {k} dias" + ("" if lower else " (toda la historia disponible)"))

      flags, anchor_pts = claim_flags(obs, r_cpi, r_usd, t0, t0 - timedelta(days=90), r - DAY, cfg, expl)
      if anchor_pts is not None:
          rules.append(("ancla", anchor_pts, 15))

      ramp = vals(real, r - timedelta(days=7), r - DAY)
      ramp_alt, base_alt = vals(alt, r - timedelta(days=7), r - DAY), vals(alt, base_a, base_b)
      if ramp and ramp_alt and base_alt:
          H = median(ramp)
          hk, hk_alt = H / B - 1, median(ramp_alt) / median(base_alt) - 1
          aparente = 1 - P0 / H                        # lo que ve quien solo mira el precio de ayer
          pts = 15.0
          if hk >= cfg.hike and hk_alt >= cfg.hike and nd < 0.5 * aparente:
              pts = 0.0
              flags.append(("suba_previa", -25))
              expl.append(f"antes de bajar subio {hk:.0%}; descuento real {nd:.0%} vs {aparente:.0%} aparente")
          elif hk >= cfg.hike / 2:
              pts = 7.0
          rules.append(("suba_previa", pts, 15))

      if comps and len(comps) >= 3:
          m = median(comps)
          rules.append(("mercado", 15 * clip((m - P0) / m / 0.10), 15))
          expl.append(f"{(m - P0) / m:+.0%} vs mediana de {len(comps)} comercios")

      earned, avail = sum(e for _, e, _ in rules), sum(a for _, _, a in rules)
      score = round(clip(100 * earned / avail + sum(p for _, p in flags), 0, 100))
      label = ("enganosa" if flags else "oferta real" if score >= 75
               else "dudosa" if score >= 50 else "sin valor real")
      return {"estado": "ok", "score": score, "label": label, "flags": [f for f, _ in flags],
              "reglas": {n: round(e, 1) for n, e, _ in rules}, "porque": "; ".join(expl)}
  ```
  Corrida de humo del autor (precios con ruido de ±0,2%, 400 días de historia, evaluación el 7/10/2026; no es validación): A oferta real (−20% por 5 días) da 100 y "oferta real"; A2 igual con tachado verdadero da 100; B suba previa (rampa de 1000 a 1250 en 21 días y luego baja a 1000 con tachado 1250) da 0, "engañosa" con banderas tachado_ficticio y suba_previa ("antes de bajar subió 21%; descuento real 0% vs 18% aparente"); C tachado 1500 sobre un precio constante de 1000 da "sin evento" con bandera tachado_ficticio; D tachado de 1300 todos los días da "sin evento" con banderas tachado_ficticio y oferta_perpetua; E producto de 20 días da "datos insuficientes"; F inflación de 4% mensual con baja nominal de 10% da 75 "oferta real" (el detector nominal no alerta: mínimo nominal de 120 días 851 contra precio 900); F2 precio nominal plano bajo inflación da "sin evento" sin banderas (se abarata por inflación, no por oferta); G salto del dólar de 20% y baja de 15% con numerario IPC da 27 "sin valor real" y con numerario dólar da 90 "oferta real"; H baja de 15% con 3 comparables entre 1100 y 1150 (precio de hoy 850) da 90. Invariancias verificadas en A y B: multiplicar todos los precios por 7,3 no cambia el resultado; precios que siguen un IPC de 3% mensual y se deflactan dan el mismo resultado; perder 1 de cada 3 observaciones no cambia el resultado (arrastre de 3 días).
- Fuentes: https://raw.githubusercontent.com/python/cpython/2639fd65ff8e0c1949c480a8e670fe9c2467a1f8/Lib/statistics.py
- Confianza: media
- Riesgo: bajo
- Vigencia: código y corrida ejecutados el 7 de octubre de 2026 con Python 3.13.16 (la única fuente externa es la documentación de statistics.median; el resto es creación propia)

### H23 — Salidas explicables, falsos positivos y negativos, casos límite
- Afirmación: Salida propuesta: {estado, score, label, flags, reglas (puntos por regla), porque, algo_version, cfg_hash, series_vintage}. La frase al usuario se arma con plantillas a partir de las reglas activadas y de la contraprueba, por ejemplo: "Te aviso porque: bajó 18% respecto de la mediana de 90 días (en pesos constantes) y es el mínimo de 120 días; 12% por debajo de la mediana de 4 comercios. Puntaje 84/100". El código de H22 genera textos de esa forma ("20% menos que la mediana de 90 dias (pesos constantes); es el minimo de 396 dias"). Política de errores (el costo de acusar sin razón es mayor que el de no acusar): (i) "engañosa" exige una bandera dura, y las de suba previa y tachado ficticio exigen confirmación en los dos numerarios; (ii) abstenerse ("datos insuficientes") con cobertura menor a 50%; (iii) banda "dudosa" entre 50 y 74; (iv) ajustar umbrales para precisión mayor o igual a 0,90 en "engañosa" y tratar el recall como secundario; (v) guardar entradas y versión de cada decisión para auditar o disputar; (vi) un único botón "discrepo" para capturar etiquetas sin conversación. Casos límite a cubrir: producto nuevo con menos de 30 días (la UE permite un período menor; sin puntaje, solo mercado); cambio de GTIN o de packaging; páginas con variantes y "desde $"; 2x1, 3x2 y descuentos por cantidad (precio efectivo por unidad); cupones y membresías; costo de envío; precios por sucursal o por zona; productos atados al dólar; liquidaciones progresivas (agrupar en una campaña); obsolescencia tecnológica (baja legítima de tendencia: medir desvío respecto de una pendiente robusta, por ejemplo Theil-Sen; scipy.stats.theilslopes, no verificada en esta sesión); reposición con suba tras un quiebre; error de precio de un día; ofertas relámpago de menos de 24 horas entre dos capturas (capturar al menos 2 veces por día); personalización por usuario o ubicación (capturar con sesión limpia); días sin captura; cambio de moneda o de redondeo.
- Fuentes: https://raw.githubusercontent.com/open-mercato/open-mercato/fefc71d09efe2aa8c732dc6fafaa084a0e0dae3c/.ai/specs/2026-06-30-omnibus-price-tracking.md, https://raw.githubusercontent.com/Hostilian/eushop/95478217fffd6c7de8802d35a39ee9cc2adcbed6/.agents/knowledge/eu-omnibus-directive-2019-2161.md
- Confianza: media
- Riesgo: bajo
- Vigencia: diseño propio, 7 de octubre de 2026

### H24 — Cómo validar: casos sintéticos y reales, métricas y revisión humana
- Afirmación: (1) Suite sintética con etiqueta de verdad: los 11 escenarios de H22 más quiebre con reposición, error de precio de un día, liquidación progresiva y obsolescencia tecnológica, con variaciones paramétricas (ruido 0 a 2%, inflación 0 a 10% mensual, faltantes 0 a 50%, longitud 30 a 400 días) y semilla fija: al menos 1.000 series, cada una con etiqueta y banderas esperadas. (2) Pruebas por propiedades con Hypothesis 6.168.5 (MPL-2.0, subida el 05/10/2026): invariancia de escala, invariancia ante inflación pura tras deflactar, orden de los comercios en comps, faltantes dentro del arrastre, monotonicidad (bajar P0 nunca baja el puntaje) y determinismo. (3) Métricas: matriz de confusión, precisión y recall por clase, F1 macro y, como métrica principal, la tasa de falsas acusaciones sobre ofertas reales; calibración del puntaje con el índice de Brier = media((p − y)²) y curva de confiabilidad; tasa de abstención. (4) Muestra humana: tamaño n = z²·p(1−p)/e²: para estimar la precisión con ±5 puntos y 95% de confianza, n = 385 (p desconocido = 0,5) o 139 (p cercano a 0,9); estratificar por categoría, comercio, bandera y banda de puntaje (sobremuestrear 40 a 60); doble revisión independiente de al menos 20% con kappa de Cohen = (po − pe)/(1 − pe), objetivo mayor o igual a 0,6, y un tercer revisor para desempates. Criterios de aceptación propuestos (no calibrados): precisión de "engañosa" mayor o igual a 0,90 con límite inferior del IC 95% mayor o igual a 0,85, falsas acusaciones sobre "oferta real" menores o iguales a 5%, determinismo 100%. (5) Datos reales: historial propio del Detector (la mejor fuente); archivo diario propio de SEPA; Open Prices (código AGPL-3.0; licencia de los datos no verificada) para productos con GTIN; el dataset de REWE (repositorio Apache-2.0, datos diarios con EAN y gramaje, ahora en almacenamiento externo; condiciones del sitio no verificadas) como banco de pruebas de escalones y reduflación fuera de Argentina; Keepa (suscripción paga) para historial de Amazon. (6) Un "oráculo normativo": la regla europea min30 etiqueta automáticamente las referencias que no la cumplen, útil para regresión pero no como verdad económica. (7) Líneas de base para comparar: detector nominal de "mínimo de N días", la regla "inflado" de SUPERBARATO (lista mayor a 2 veces la mediana) y la regla europea; el algoritmo debe mejorar sobre las tres en casos con inflación. (8) Revalidar cada trimestre y ante cualquier cambio de configuración, registrando algo_version.
- Fuentes: https://pypi.org/pypi/hypothesis/6.168.5/json, https://pypi.org/pypi/scikit-learn/1.9.1/json, https://github.com/openfoodfacts/open-prices, https://github.com/L480/rewe-price-data, https://github.com/akaszynski/keepa, https://raw.githubusercontent.com/AlanMundler/SUPERBARATO/f779c898b31178ba84b8e6f57f99ce98fd8e3e2c/scripts/update_precios.py
- Confianza: media
- Riesgo: bajo
- Vigencia: consultado 7 de octubre de 2026 (fórmulas estándar de estadística; criterios de aceptación propuestos)

## Herramientas y software

| Nombre | Qué hace | Plataforma | Licencia o precio | Estado a octubre 2026 (última versión/fecha) | URL oficial | Encaje con WINT (alto/medio/bajo) | Salvedad |
|---|---|---|---|---|---|---|---|
| ruptures | Detección de puntos de cambio offline (Pelt, Binseg, BottomUp, Window, Dynp, KernelCPD) | Python (Windows, Linux, macOS); PyPI exige >=3.9 y <3.14 | BSD-2-Clause, gratis | 1.1.10 (10/09/2025) | https://github.com/deepcharles/ruptures | medio | jump=5 por defecto; README y PyPI discrepan en la versión de Python |
| bocd (gwgundersen) | BOCPD de Adams y MacKay con modelo gaussiano de media desconocida | Python, archivo único | BSD-3-Clause | 111 estrellas, 12 commits (fecha de última actividad no vista) | https://github.com/gwgundersen/bocd | bajo | Didáctico, no es un paquete |
| bayesian_changepoint_detection (hildensia) | BOCPD con varios modelos | Python | Sin licencia declarada en PyPI | 0.2.dev1 (12/08/2019) | https://pypi.org/pypi/bayesian-changepoint-detection/json | bajo | Abandonado; no usar como dependencia |
| SciPy | MAD robusta (median_abs_deviation), estadística y pendientes robustas | Python >=3.12 | BSD-3-Clause | 1.18.1 (21/08/2026) | https://pypi.org/pypi/scipy/json | alto | Exige Python 3.12 o superior |
| statsmodels | Descomposición estacional y modelos de series | Python >=3.10 | BSD-3-Clause | 0.15.0 (27/08/2026) | https://pypi.org/pypi/statsmodels/json | bajo | Necesita al menos dos ciclos por serie |
| pandas | Series temporales, rolling y resample | Python >=3.11 | BSD-3-Clause | 3.0.6 (17/09/2026) | https://pypi.org/pypi/pandas/json | medio | El núcleo propuesto no lo necesita (solo biblioteca estándar) |
| RapidFuzz | Similitud de cadenas rápida | Python >=3.11 | MIT | 3.14.6 (30/08/2026) | https://pypi.org/pypi/rapidfuzz/json | alto | Solo candidatos; requiere guardas de tamaño y variante |
| Splink | Enlace probabilístico de registros a escala | Python >=3.10; DuckDB, Spark, PostgreSQL | MIT | 5.0.0 (28/09/2026) | https://pypi.org/pypi/splink/json | medio | Curva de aprendizaje; la página principal de PyPI dio una fecha inconsistente (dic. 2024) y se usó la del JSON por versión |
| recordlinkage | Enlace y deduplicación de registros | Python >=3.8 | BSD-3-Clause | 0.16 (20/07/2023) | https://pypi.org/pypi/recordlinkage/json | bajo | Poco mantenido |
| dedupe | Deduplicación con aprendizaje activo | Python >=3.8 | MIT | 3.0.3 (fecha no verificada) | https://pypi.org/pypi/dedupe/json | medio | Requiere etiquetar pares |
| sentence-transformers | Embeddings para generar candidatos de emparejamiento | Python >=3.10 | Apache-2.0 | 6.1.0 (18/09/2026) | https://pypi.org/pypi/sentence-transformers/json | medio | Pesado para una app de bandeja; solo para proponer, nunca para aceptar |
| python-stdnum | Validación de EAN y GTIN y otros números | Python >=3.8 | LGPL | 2.2 (04/01/2026) | https://pypi.org/pypi/python-stdnum/json | alto | Licencia LGPL; verificar compatibilidad |
| price-parser | Extrae importe y moneda de texto con separadores | Python >=3.9 | BSD-3-Clause | 0.5.1 (19/03/2026) | https://pypi.org/pypi/price-parser/json | alto | Probar con formato argentino 1.234,56 |
| Pint | Unidades físicas y conversiones | Python >=3.12 | BSD | 0.26.1 (10/09/2026) | https://pypi.org/pypi/pint/json | medio | Alternativa: diccionario propio de unidades |
| Hypothesis | Pruebas basadas en propiedades | Python >=3.10 | MPL-2.0 | 6.168.5 (05/10/2026) | https://pypi.org/pypi/hypothesis/json | alto (desarrollo) | Solo para pruebas |
| scikit-learn | Métricas de validación (precisión, recall, Brier, kappa) | Python >=3.11 | BSD-3-Clause | 1.9.1 (10/09/2026) | https://pypi.org/pypi/scikit-learn/json | medio (validación) | Las funciones de métricas se recuerdan, no se verificaron en esta sesión |
| API de Series de Tiempo (datos.gob.ar) | IPC, tipo de cambio y otras series públicas por REST | Web (REST, JSON o CSV) | Software MIT; datos con la licencia de cada publicador | Beta, sin garantía formal; no se pudo llamar | https://github.com/datosgobar/series-tiempo-ar-api | alto | 40 ids por consulta, limit máx. 1000, 60 pedidos/s por IP; verificar fecha del último dato |
| API BCRA Estadísticas Cambiarias | Cotizaciones oficiales por fecha o por moneda | Web (REST) | Gratuita; términos no verificados | v1.0 | https://api.bcra.gob.ar/estadisticascambiarias/v1.0/Cotizaciones | alto | Solo oficial; la URL se vio en código de terceros y estaba bloqueada |
| API BCRA Principales Variables | Variables monetarias y de mercado | Web (REST) | Gratuita; términos no verificados | v3.0 | https://api.bcra.gob.ar/estadisticas/v3.0/Monetarias | bajo | Existencia de versiones nuevas no verificada |
| ArgentinaDatos API | Cotizaciones históricas del dólar (oficial, CCL y otras) | Web (REST) | No verificada | No verificado | https://api.argentinadatos.com/v1/cotizaciones/dolares | medio | Comunitaria, sin garantía de servicio conocida |
| dolarapi.com | Cotizaciones actuales del dólar | Web (REST) | No verificada | No verificado | https://dolarapi.com/v1/dolares | medio | Comunitaria, sin garantía de servicio conocida |
| SEPA (datos abiertos de precios) | Precios diarios de supermercados con EAN, lista, referencia y promoción | ZIP y CSV (7 archivos semanales) | CC-BY según un comentario de un script (no verificado) | Actualización diaria según un script de terceros | https://datos.produccion.gob.ar/dataset/6f47ec76-d1ce-4e34-a7e1-621fe9b1d0b5/resource/0a9069a9-06e8-4f98-874d-da5578693290/download/sepa_lunes.zip | alto | Dominio bloqueado: no se descargó; archivar propio |
| Scrapers de Precios Claros | Descargan productos, precios y sucursales del portal oficial | Python (Scrapy, SQLite) | Sin licencia declarada (martjanz); no verificada (OpenDataCordoba) | OpenDataCordoba/precios_claros: 27 estrellas, actualizado el 12/06/2026 | https://github.com/OpenDataCordoba/precios_claros | medio | Frágiles ante cambios de la API; revisar términos de uso |
| Open Prices (Open Food Facts) | Base abierta y colaborativa de precios con código de barras y tipos de descuento | Django y Python; API web | AGPL-3.0 (código) | Activo, 1.166 commits | https://github.com/openfoodfacts/open-prices | medio | Cobertura argentina desconocida; licencia de datos no verificada |
| SDK openfoodfacts | Acceso a productos de Open Food Facts | Python >=3.10 | MIT | 5.3.0 | https://pypi.org/pypi/openfoodfacts/json | bajo | Útil para enriquecer GTIN de alimentos |
| Keepa (API y paquete keepa) | Historial de precios de Amazon | Python >=3.10; suscripción mensual | Cliente Apache-2.0; servicio de pago | 1.6.0 (05/10/2026) | https://github.com/akaszynski/keepa | bajo | Solo Amazon; cobertura argentina no verificada |
| changedetection.io | Monitorea cambios de páginas, precio y stock con avisos | Docker, pip, Windows; SaaS de pago | Apache-2.0; SaaS cerca de USD 8,99 por mes | 0.60.8 (28/09/2026) | https://github.com/dgtlmoon/changedetection.io | medio | No juzga la credibilidad de la oferta |
| Discount Bandit | Seguidor de precios autoalojado y multiusuario | Laravel (PHP), Docker | No especificada en lo leído | 746 estrellas; actualizado el 06/10/2026 | https://github.com/Cybrarist/Discount-Bandit | bajo | Tiendas no argentinas |
| PriceDive | Seguidor que apunta al patrón "sube y luego baja" | Python y SQLite | No verificada | 83 estrellas; creado el 08/10/2025 | https://github.com/DAILtech/PriceDive | bajo | Sin umbrales publicados; tiendas chinas; datos simulados por defecto |
| SUPERBARATO | Comparador de ofertas con SEPA; marca "inflado" y "descuento honesto" | Python y GitHub Pages | No verificada | Creado el 10/09/2026; 0 estrellas | https://github.com/AlanMundler/SUPERBARATO | medio (línea de base) | Regla transversal ingenua (2 veces la mediana) |
| shrinkflation-detective | Detección de reduflación por precio unitario con Kroger API | Python y PostgreSQL | MIT | 2 estrellas; actualizado el 09/06/2026 | https://github.com/aansensei/shrinkflation-detective | bajo | Solo datos de Kroger (EE. UU.) |
| rewe-price-data | Precios diarios de REWE con EAN y gramaje | CSV | Apache-2.0 (repositorio) | Actualizado el 24/08/2026 | https://github.com/L480/rewe-price-data | bajo (banco de pruebas) | Datos movidos a almacenamiento externo; condiciones del sitio no verificadas |
| dark-patterns (Mathur et al.) | Código y datos del estudio de 11.000 sitios | Python | GPL-3.0 | 2019 | https://github.com/aruneshmathur/dark-patterns | bajo | Solo referencia metodológica |
| clarius/normas | Espejo en Markdown de leyes y decretos argentinos | GitHub | No verificada | Activo | https://github.com/clarius/normas | medio | Espejo no oficial: contrastar con InfoLEG antes de citar |

## Esquema para cuadro sinóptico

- Detectar ofertas falsas
  - Definir oferta real
    - Referencia veraz
    - Descuento neto real
    - Mínimo histórico
  - Tipos de engaño
    - Ancla inflada
    - Suba previa
    - Tachado ficticio
    - Oferta perpetua
    - Falsa urgencia
    - Reduflación
    - Cuotas y contado
  - Estadística robusta
    - Mediana por tiempo
    - MAD y percentiles
    - Puntos de cambio
    - Faltantes y errores
  - Inflación argentina
    - Deflactar con IPC
    - Dólar como contraste
    - Regla de dos numerarios
  - Datos y emparejamiento
    - GTIN validado
    - Unidades normalizadas
    - Revisión humana
  - Algoritmo y validación
    - Puntaje de 0 a 100
    - Explicación por reglas
    - Casos sintéticos
    - Muestra humana

## Recomendaciones para WINT

1. Hacer del algoritmo una biblioteca pura y determinista (sin red, sin base de datos y sin modelos de lenguaje) que el Detector invoque y WINT solo muestre. Por qué: el mismo historial debe dar siempre el mismo veredicto y la misma explicación, que es lo que se espera de un bot que no conversa ni interpreta.
2. Guardar el historial en SQLite con tablas solo-anexar: observaciones (marca de tiempo UTC, día local, comercio, sucursal, clave de producto, GTIN-14, precio, precio tachado, tipo de precio, disponibilidad, cantidad, unidad, pack, hash del HTML), reclamos (textos de tachado, porcentaje, vigencia, cuotas, banco, temporizador, stock), decisiones (entradas, versión del algoritmo, hash de configuración) y versión de las series macro usadas. Por qué: es el patrón de "historial inmutable" que usan los proyectos que cumplen la regla europea de 30 días (H2) y permite reproducir o disputar cualquier alerta.
3. Capturar el reclamo y no solo el precio: precio tachado, "% OFF", fechas de vigencia (exigidas por el art. 7 de la Ley 24.240), cuotas y precio de contado, condiciones bancarias, temporizadores y mensajes de stock. Sin esos campos no se pueden probar la mayoría de los engaños de H6 a H8.
4. Capturar al menos 2 veces por día los productos vigilados y archivar todos los días los ZIP de SEPA propios. Por qué: una oferta relámpago entre dos capturas no se ve, y la retención histórica de la fuente no está verificada.
5. Descargar IPC y dólar una vez por día con caché local (la API de series permite 40 ids por consulta y 60 pedidos por segundo por IP) y guardar la versión usada en cada decisión. Si la descarga falla, degradar a "sin deflactar" mostrándolo en pantalla, nunca en silencio.
6. Configurar el numerario por categoría (IPC para alimentos y limpieza, dólar para electro y tecnología) y aplicar la regla de dos numerarios para acusar. Por qué: evita falsos positivos cuando un salto cambiario mueve los precios en pesos (H17).
7. Lanzar con los umbrales de H21 marcados como "no calibrados" y mostrar al usuario solo "oferta real", "dudosa" y "datos insuficientes" hasta tener 3 o 4 semanas de datos propios y una muestra humana de al menos 139 casos (idealmente 385). Recién entonces habilitar la etiqueta "engañosa". Por qué: acusar sin razón cuesta más que callar.
8. Emparejar por GTIN primero; para el resto usar RapidFuzz con las guardas de H20 y una cola de revisión humana. Si se usa Claude u otro modelo, que sea fuera del camino de decisión y solo para proponer candidatos que una persona aprueba (tabla dorada). Por qué: preserva el carácter determinista del bot.
9. Fijar Python 3.13 en Windows y versiones mínimas de dependencias (ruptures exige Python menor a 3.14 en PyPI; SciPy y Pint exigen 3.12 o más). Mantener el núcleo con biblioteca estándar y dejar ruptures como extra opcional para la segunda etapa.
10. Usar Luna para el lote nocturno (bajar SEPA del día, IPC y dólar, recalcular y archivar) y Sol para mostrar al arrancar un resumen fijo de "ofertas confirmadas y banderas de las últimas 24 horas", sin preguntas; el ícono naranja del Detector indica que el lote está corriendo. Es una propuesta de integración que respeta el carácter no conversacional de WINT.
11. Mostrar la evidencia, no solo el veredicto: gráfico escalón del precio real con la base B, el inicio r del nivel actual, la zona de rampa, el tachado declarado y las comparaciones, más las líneas "por qué sí" y "por qué no". Un único botón "discrepo" que guarde una etiqueta para la validación.
12. Mantener a mano una tabla de eventos (Hot Sale, CyberMonday, Black Friday y otros) con fuente y fechas de cada año, y excluir esas ventanas de la base B. Las fechas de 2026 no se verificaron.
13. Construir la suite de pruebas de H24 desde el primer día (escenarios sintéticos, propiedades con Hypothesis y la regla europea min30 como oráculo de regresión) y compararla contra las tres líneas de base (mínimo nominal de N días, "inflado" de SUPERBARATO, regla europea).
14. Antes de publicar cualquier acusación contra un comercio, contrastar el texto de la norma contra la fuente oficial (InfoLEG y EUR-Lex), conservar capturas y método reproducible, y respetar los términos de uso de cada sitio (no verificados aquí). El Detector es evidencia personal, no una sentencia.
15. Cuando se levante el bloqueo de red, completar la lista de verificación pendiente de la última sección (normas oficiales, estudios, IPC vigente y cambio de base, régimen cambiario, licencias de SEPA y de las APIs comunitarias) y recalibrar los umbrales con datos propios.

## Qué no se pudo verificar

Contexto de la sesión: las primeras cinco consultas de WebSearch devolvieron "límite de 200 búsquedas por turno agotado" (ninguna búsqueda se ejecutó). La red de salida bloqueó (EGRESS_BLOCKED) eur-lex.europa.eu, apis.datos.gob.ar, datosgobar.github.io, series-tiempo-ar-api.readthedocs.io, www.bcra.gob.ar, api.bcra.gob.ar, api.argentinadatos.com, www.ecfr.gov, www.ftc.gov, www.law.cornell.edu, commission.europa.eu, arxiv.org, www.which.co.uk, www.indec.gob.ar, en.wikipedia.org, docs.python.org, datos.gob.ar, www.preciosclaros.gob.ar, www.legislation.gov.uk, www.nber.org, doi.org y www.argentina.gob.ar; www.consumidor.gob.ar no resolvió. Se pudo abrir github.com, raw.githubusercontent.com, pypi.org y la búsqueda de repositorios y de código de GitHub. Un intento de leer documentación del proxy fue denegado por el sistema de permisos y no se insistió. Por eso las normas y los estudios dependen de espejos y paráfrasis de terceros.

1. Texto oficial de la Directiva (UE) 2019/2161 y de la Directiva 98/6/CE (EUR-Lex): numeración exacta de los apartados del art. 6a, sanciones (se recuerda un piso de multa de 4% de la facturación en infracciones coordinadas, sin fuente abierta) y el Aviso de la Comisión 2021/C 526/02 sobre el alcance de la regla.
2. Estudios de organizaciones de consumidores sobre Black Friday y precios de referencia (Which? en Reino Unido, CHOICE en Australia, Verbraucherzentrale en Alemania, barridos de la red CPC de la UE, BEUC): no se pudo abrir ninguno; no se cita ninguna cifra de ellos. Tampoco se encontraron estudios argentinos (Defensa del Consumidor, Cámara Argentina de Comercio, asociaciones de consumidores) sobre ofertas infladas en Hot Sale o CyberMonday.
3. Normas comparadas: 16 CFR Parte 233 de la FTC ("precio anterior" genuino), guías del Reino Unido (CMA y Trading Standards, regla de 28 días) y la ley DMCC de 2024: no abiertas.
4. Académicos: el original de Mathur et al. en arXiv (solo se vio una copia del texto en un repositorio de terceros), Cavallo (2013) sobre precios en línea frente al IPC oficial argentino, la literatura de precios de referencia, Iglewicz y Hoaglin (umbral 3,5), Killick et al. (PELT) y el artículo original de Adams y MacKay: no abiertos.
5. Argentina, normas: resoluciones de la Secretaría de Comercio sobre precio de referencia, precio por unidad de medida, exhibición de precios y descuentos por medio de pago; la Ley de Góndolas; la situación de Ahora 12 y de los programas de cuotas; las fechas de Hot Sale y CyberMonday 2026; si la Ley 24.240 (en particular los montos del art. 47) y el DNU 274/2019 fueron modificados después de las versiones de los espejos.
6. INDEC: último IPC publicado a octubre de 2026, calendario de publicación, cualquier cambio de base o de canasta y vigencia del id 148.3_INIVELNAL_DICI_M_26; qué mide cada id de tipo de cambio visto (168.1_T_CAMBIOR_D_0_0_26 y 92.2_TIPO_CAMBIION_0_0_21_24).
7. BCRA: términos de uso y límites, qué cotización exacta es tipoCotizacion para USD, existencia de versiones posteriores (v4 u otras) y régimen cambiario vigente a octubre de 2026.
8. APIs comunitarias del dólar (dolarapi.com y ArgentinaDatos): disponibilidad, licencia y definiciones de MEP y CCL; solo se vieron en código de terceros.
9. SEPA y Precios Claros: licencia real, retención histórica, esquema vigente de los ZIP y de las columnas, y estado actual de la API del portal; no se descargó ningún archivo.
10. Herramientas comerciales de seguimiento de precios (CamelCamelCamel, Idealo, PriceSpy, Google Shopping, extensiones de navegador): no se evaluaron por bloqueo; solo se relevaron Keepa, changedetection.io y proyectos abiertos.
11. GS1 y GTIN: reglas de asignación y de cambio de código, prefijo de país de Argentina (se recuerda 779, sin fuente abierta).
12. Reduflación: regulaciones (por ejemplo, de Francia o de la UE) y casos documentados en Argentina.
13. Todos los umbrales de H21 son heurísticos y no están calibrados con datos reales; la corrida de humo de H22 usa series sintéticas del autor y no demuestra desempeño en producción.
14. Las fechas de subida de PyPI provienen de resúmenes automáticos de la página JSON de cada versión; las de la página principal resultaron inconsistentes para pandas, sentence-transformers, Splink y changedetection.io y se reemplazaron por las del JSON por versión; para dedupe, SDK openfoodfacts, DuckDB y Scrapy no se verificó la fecha.
15. Los espejos de normas (clarius/normas) y las paráfrasis de software sobre la Directiva pueden contener errores o estar desactualizados; las cifras del art. 47 de la Ley 24.240 y las atribuciones al Aviso 2021/C 526/02 son las más frágiles.
