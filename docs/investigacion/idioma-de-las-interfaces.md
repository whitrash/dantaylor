# El idioma universal de las interfaces

Segunda parte de la investigación (12/10/2026). La primera, `canales-de-informacion.md`,
analizó **qué** llega por cada canal. Esta analiza **cómo se habla**: los símbolos, la
ubicación de los botones, por qué todas las apps terminan pareciéndose y por qué cambian
juntas (la barra que pasa de la izquierda a abajo, la fiebre de los reels).

Marcas: ✔ confirmado con búsqueda en esta pasada · el resto es historia de diseño
ampliamente documentada, sin re-verificar acá.

---

## 1. Por qué todas hablan el mismo idioma

No hay un comité que lo decida. Hay cinco fuerzas que empujan para el mismo lado:

1. **La gente aprende en otro lado.** La "ley de Jakob" (Jakob Nielsen, 2000): *los
   usuarios pasan la mayor parte del tiempo en otros sitios*, así que esperan que el tuyo
   funcione como esos. Cada app que rompe la costumbre le cobra al usuario un costo de
   aprendizaje. Resultado: copiar lo que ya aprendieron es lo más barato.
2. **Los dueños del sistema escriben el manual.** Apple (Human Interface Guidelines,
   desde 1987; para iPhone desde 2008) y Google (Material Design, 2014) publican cómo
   tiene que verse una app y regalan los componentes ya hechos. Si usás la barra estándar
   de iOS, obtenés gratis accesibilidad, gestos y el "look" nuevo cuando Apple lo cambia.
   **Cuando Apple o Google mueven un botón, se mueven millones de apps a la vez.**
3. **Los kits compartidos.** Bootstrap (2011), Material, después Tailwind y las librerías
   de componentes: miles de sitios construidos con las mismas piezas se parecen.
4. **Los tests A/B convergen.** Todas las grandes miden lo mismo (tiempo, retención,
   clics); si el mismo cambio sube la métrica en una, sube en otra.
5. **Copia competitiva.** Cuando un formato le saca usuarios al líder, el líder lo copia
   en meses (ver §4). Para el usuario parece un "acuerdo"; en realidad es miedo.

## 2. El diccionario de símbolos (de dónde viene cada uno)

| Símbolo | Significa | Origen |
|---|---|---|
| ☰ "hamburguesa" | menú escondido | Norm Cox, Xerox Star (1981); se masificó en móviles ~2010–2014 |
| ⋮ / ⋯ "kebab" / "meatball" | más opciones de *este* ítem | Android (⋮) e iOS (⋯) |
| 🔍 lupa | buscar | metáfora del detective, universal desde los 90 |
| ⚙ engranaje | configuración | la "máquina" por dentro |
| 💾 disquete | guardar | sobrevive aunque nadie lo haya usado (fósil) |
| 🏠 casa | inicio | el sitio como "hogar" |
| ♥ corazón | me gusta / guardar | Twitter cambió la estrella ★ por ♥ en nov. 2015; Instagram lo popularizó |
| 🔔 campana | notificaciones | |
| ✕ | cerrar | arriba a la derecha (Windows) o izquierda (Mac viejo) |
| ← | volver | en iOS arriba a la izquierda; en Android, gesto o botón del sistema |
| ＋ | crear | en el **centro** de la barra cuando la app quiere que publiques (TikTok, YouTube) |
| ▶ triángulo | reproducir | herencia de los grabadores de cinta |
| ⬆ con caja (iOS) / ◁ tres puntos unidos (Android) | compartir | cada sistema tiene el suyo |
| círculo con foto | tu perfil | casi siempre la última pestaña, a la derecha |
| anillo de color en un avatar | historia sin ver | Snapchat/Instagram 2016 |
| punto rojo / número | algo nuevo te espera | el símbolo más eficaz y más abusado |

Gestos que ya son "idioma": tirar para refrescar (Tweetie, 2008), deslizar para
descartar (Tinder, 2012), doble toque = me gusta (Instagram), mantener apretado = menú,
deslizar desde el borde = volver (iPhone X, 2017; Android 10, 2019), deslizar hacia
arriba = siguiente (TikTok).

## 3. Dónde van los botones y por qué se mueven

### La regla madre: el pulgar
Steven Hoober observó en 2013 a 1.333 personas usando el celular: de las que tocaban la
pantalla, el **49% usaba una sola mano**, 36% sostenía con una y tocaba con la otra, 15%
dos manos; el pulgar hace ~75% de las interacciones ✔. Con pantallas cada vez más
grandes, la parte de arriba quedó fuera del alcance. **Todo lo importante bajó.**

### Cronología de la navegación
- **Escritorio (1995–2010):** menú horizontal arriba + barra lateral izquierda (se lee de
  izquierda a derecha y de arriba abajo; el logo arriba a la izquierda lleva al inicio).
- **iPhone (2007):** barra de pestañas **abajo**, de 3 a 5 íconos con nombre. Apple la
  tuvo siempre.
- **Era hamburguesa (≈2010–2014):** para "limpiar" la pantalla, el menú se escondió en
  un cajón lateral (Facebook, Gmail, YouTube). Problema: lo que no se ve no se usa.
  Facebook pasó a barra de pestañas en iOS con iOS 7 (2013) y los relatos coinciden en que
  el uso subió, aunque Facebook nunca publicó cifras ✔.
- **Android adopta la barra de abajo:** Google la agregó a Material Design en marzo de
  2016 (3 a 5 destinos) ✔. Desde entonces es el estándar en los dos sistemas.
- **Gestos en vez de botones (2017–2019):** desaparece el botón físico de inicio; la
  pantalla entera es contenido y se navega deslizando.
- **La barra de direcciones baja (2021–2023):** Safari en iOS 15 la puso abajo; Chrome
  después lo ofreció como opción. Misma razón: el pulgar.
- **La barra que flota y se achica (2025):** iOS 26 ("Liquid Glass") hace que la barra de
  pestañas flote sobre el contenido y se encoja en una píldora al hacer scroll ✔. El
  contenido manda; los botones se apartan.

### La barra de pestañas es una declaración de prioridades
Lo que la empresa pone en la barra de abajo —y sobre todo en el **centro**— es lo que
quiere que hagas:
- **Instagram 2020:** Reels toma el centro (donde estaba "publicar") y la tienda reemplaza
  al corazón de actividad, que se va arriba; hubo quejas por empujar funciones nuevas ✔.
  En 2022–2023 la tienda se retira de la barra.
- **Instagram 2025:** prueba y lanza una barra con Inicio, **Reels y Mensajes**; "crear"
  se va arriba ✔. Reels y los mensajes privados eran lo que más crecía.
- **TikTok / YouTube:** "＋" en el centro porque necesitan creadores; YouTube puso Shorts
  como segunda pestaña.
- **X:** Grok y la búsqueda ganaron pestañas cuando la empresa los priorizó.

**Lección:** cuando una app "cambia la barra", casi nunca es estética; es un cambio de
negocio que se ve.

## 4. Las olas: por qué de golpe todos hacen lo mismo

| Ola | Quién la inventó | Quién la copió | Qué quedó |
|---|---|---|---|
| Diseño plano | Windows Phone (2010), iOS 7 (2013) | todos | sigue (con capas de vidrio en 2025) |
| Historias (24 h) | Snapchat 2013 | Instagram (ago. 2016), WhatsApp, Facebook, YouTube; LinkedIn y Twitter las cerraron en 2021 | quedó en las apps de amigos, murió en las de trabajo |
| Video corto vertical | Douyin/TikTok 2016–2018 | Reels (ago. 2020), Shorts (sep. 2020), Spotlight (nov. 2020), Netflix, Spotify, LinkedIn | se volvió el formato dominante |
| Salas de audio | Clubhouse 2020–2021 | Twitter Spaces, Facebook, Spotify | se desinfló en 2 años |
| Modo oscuro | iOS 13 y Android 10 (2019) | todos | quedó como opción estándar |
| Caja de IA | ChatGPT (nov. 2022) | buscadores, apps, sistemas | en curso |

**Por qué todos se obsesionaron con los reels:**
1. **Amenaza:** TikTok les sacaba tiempo de uso, sobre todo a los jóvenes. El tiempo es
   lo que venden (publicidad).
2. **Cambio de motor:** el reel no necesita que sigas a nadie; el algoritmo te muestra
   lo que más te retiene de *todo* el catálogo ("grafo de intereses" en vez de "grafo
   social"). Eso le da a la plataforma inventario infinito.
3. **Mide mejor:** una cosa por pantalla = cada segundo es una señal clara de gusto.
4. **Ocasión:** India prohibió TikTok en junio de 2020; Instagram lanzó Reels allí antes
   y Shorts nació en India en septiembre de 2020.
5. **Costo:** pelearse con los usuarios. En 2022 la campaña "Make Instagram Instagram
   again" (con las Kardashian) hizo retroceder a Instagram en algunos cambios, pero el
   formato se quedó.

**Patrón general de una ola:** alguien chico inventa → crece entre jóvenes → los grandes
copian en 3–12 meses y le dan un lugar en la barra → el formato sobrevive si sube el
tiempo de uso, o se retira en silencio si no (Fleets, Spaces, tiendas).

## 5. Qué accesos se le dan al usuario (y cuáles se le quitan)

- **Se dan:** lo que genera uso (crear, ver más, mensajes), siempre al alcance del pulgar.
- **Se esconden:** lo que corta el uso (el feed cronológico, desactivar autoplay, "ya
  estás al día", configuración de privacidad): detrás de un ⋯, un engranaje o dos menús.
- **Se reglamentan:** Europa (DSA, 2023) obliga a ofrecer un feed sin perfilado; Nueva
  York y California, avisos en los chatbots. Cuando la ley obliga, el botón aparece… lejos.

## 6. Qué significa para los catálogos

Los catálogos ya hablan este idioma (visor tipo Netflix, filas, "Mi lista", azar, buscar
arriba). Para no hacer pensar a nadie:

1. **Usar los símbolos estándar sin inventar:** 🔍 buscar, ♥ o ＋ "Mi lista", ✕ cerrar,
   ← volver, ⋯ más opciones, círculo de perfil.
2. **En el celular, barra de 3 a 5 pestañas abajo, con ícono y nombre** (Inicio, Explorar,
   Mi lista, Buscar). En escritorio, pestañas arriba. En TV, arriba y que se esconda al bajar.
3. **El centro de la barra = lo que queremos que hagan:** "La de hoy" o "Uno al azar",
   no "configuración".
4. **Gestos esperados:** deslizar entre fichas, tocar fuera para cerrar, Esc/Atrás cierra,
   flechas en TV.
5. **No esconder lo que da control** (ver todo, cronológico/orden, pausar el visor): es
   lo que las grandes esconden y lo que nos diferencia.
6. **Seguir las olas con criterio:** tomar el formato (una cosa por pantalla, la tarjeta
   del día) sin tomar el motor (infinito, retención a toda costa).
7. **Revisar una vez por año** las guías de Apple (WWDC, junio) y Google (I/O, mayo):
   ahí se anuncia el próximo cambio de idioma antes de que lo adopten todos.
