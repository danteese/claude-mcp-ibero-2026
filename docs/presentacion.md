# Presentación

**Dónde está:** Google Slides en el Drive de dante@spot2.mx, carpeta "Taller MCP · Claude CDMX".
Es privada: solo la persona dueña tiene permiso. El enlace y los IDs están en
`presentacion/.ids.json` (no se versiona).

**Versión actual:** 9. Son 28 láminas: 27 se presentan en 40 minutos y la última es un glosario de consulta. Historial en `storytelling.md`.

**Reglas:** todas las láminas son claras (no sabemos cómo proyecta el foro una oscura); sin sombras ni líneas decorativas, así que solo hay flechas y líneas con significado (el diagrama M×N); cada concepto lleva su tarjeta de «Definición». La lámina 7 (Spot2) se armó con lo que respondió Devin sobre los repositorios de Spot2 (D17); falta el número de personas (`PERSONAS_MCP`).

**Cómo se construye:** `uv run presentacion/construir.py`.
1. Genera `presentacion/salida/taller-mcp.pptx` con `python-pptx`. El script declara sus
   dependencias en su encabezado (PEP 723), así que no ensucia las dependencias del taller.
2. Lo sube con `gws drive files update` sobre la misma presentación. Drive lo convierte a
   Google Slides y el enlace no cambia.
3. Exporta `presentacion/salida/taller-mcp.pdf` para revisarlo.

`--local` solo genera el `.pptx`.

**Recursos** (en `presentacion/recursos/`, no se versionan):
- `foto-dante.png`: la foto que compartió Dante; el script la recorta en círculo.
- `mapa-portada.png`: captura a 2× de `mapa/index.html` en julio de 2026, sin la capa de Ecobici, con el fondo del SVG igualado al papel (`#F7F7F3`), recortada al contenido y con el fondo transparente para que no se note un rectángulo en la portada.
- `mapa-oct-2022.png`: captura a 2× de `mapa/index.html` en octubre de 2022, sin la capa de
  Ecobici para no mezclar un dato de hoy con uno de 2022.

## Agenda (40 minutos)

Generada a partir de las notas del orador del `.pptx`.

| # | Minuto | Lámina | Definiciones |
| --- | --- | --- | --- |
| 1 | 0–0.5 | Datos abiertos over MCP · Claude que consulta fuentes reales (portada con el mapa de julio de 2026) | — |
| 2 | 0.5–1.5 | ¿Cuánta gente entró a Pantitlán en julio de 2026? (al centro de una lluvia de 16 preguntas con dato público) | — |
| 3 | 1.5–2 | **La respuesta: 4,623,233** (desglose por línea y las 5 estaciones con más entradas) | — |
| 4 | 2–2.5 | Sin herramientas, Claude estima. Con tu servidor MCP, responde con el dato. | — |
| 5 | 2.5–3.5 | **Al terminar tendrás un servidor MCP tuyo, conectado** (qué te llevas) | — |
| 6 | 3.5–4 | Quién soy: foto, rol y trayectoria | — |
| 7 | 4–5 | En Spot2, cada capacidad nace con su API y su MCP | — (callback del diagrama M×N; API/MCP first) |
| 8 | 5–6 | Un modelo convierte texto en texto: saber y actuar hay que dárselo | LLM |
| 9 | 6–7.5 | Una tool es una función que el modelo pide y tu código ejecuta | Tool, function calling, agente |
| 10 | 7.5–9 | MCP es el estándar para conectar la IA con tus sistemas | MCP (y el diagrama M×N contra M+N) |
| 11 | 9–10.5 | La IA puede usar API, CLI o MCP: elige según la situación | — |
| 12 | 10.5–12 | MCP te da control y alcance; lo pagas en contexto y riesgo | — |
| 13 | 12–13 | En MCP participan tres actores: host, client y server | Host, client, server, transporte |
| 14 | 13–14.5 | MCP tiene tres capas obligatorias; el resto es opcional | Componentes de la spec 2026-07-28 |
| 15 | 14.5–15.5 | Tres piezas, una pregunta: ¿quién decide cuándo ocurre? | Tool, resource, prompt (y sus campos) |
| 16 | 15.5–16.5 | **Un MCP da acceso; una skill le enseña a usarlo** | Skill (Agent Skill), plugin |
| 17 | 16.5–17.5 | **Construimos un servidor MCP por HTTP con FastMCP** | Transportes (stdio, HTTP local, HTTP remoto), FastMCP, FastAPI |
| 18 | 17.5–19.5 | Construyamos (instalación) | Datos abiertos, uv |
| 19 | 19.5–23.5 | Paso 1 · Una función con docstring ya es una tool | FastMCP, docstring, schema |
| 20 | 23.5–27.5 | Paso 2 · Diseña para quien lee el contrato: el modelo | Contexto |
| 21 | 27.5–32 | Paso 3 · Si la tool escribe, los controles van en el código | Idempotente |
| 22 | 32–35 | Paso 4 · Mide si Claude elige bien | Evaluación (eval) |
| 23 | 35–36 | El mismo dato, ahora en un mapa para personas | — |
| 24 | 36–37.5 | Claude extiende el mapa; tú lees lo que añade | — |
| 25 | 37.5–39 | **Recap: tienes un servidor MCP y sabes cuándo usarlo** | — |
| 26 | 39–39.5 | Ahora te toca | — |
| 27 | 39.5–40 | Si el agente falla, arregla la descripción, no el modelo. | — |
| 28 | — | Glosario del taller (apéndice, no se presenta) | 25 términos |

Las notas del orador de cada lámina tienen el guion, el tiempo y las marcas [EN VIVO]. Las de la lámina 14 explican elicitation (qué es, ejemplo, modos, qué no es y por qué no la usamos hoy), por si sale en preguntas.

## Ediciones de Dante en Google Slides

Regenerar sobrescribe lo que se edite directo en Slides. Antes de regenerar: exportar la presentación actual
como `.pptx` (`gws drive files export`, con `mimeType` de PowerPoint), compararla con la última generada
(texto, posición y tamaño de letra de cada forma) y pasar las diferencias a `construir.py`.

El 19-oct-2026 se incorporaron así: «Álvaro Obregón» en la lluvia; «(Solo repaso, ya se vio antes)» en
«Qué te llevas»; la bio de «Quién soy» (CMS del CERN, microbioma en UC San Diego, spot2.mx al pie); en
Spot2, «Algunos servidores MCP», «Otros Agentes», «Toda la plataforma disponible para agentes» y sin el
número; en LLM, «dado un token» y el titular a 21 pt en y=52. Segunda tanda: en Spot2, la tarjeta dice «En
Spot2 todos los sistemas deben de poder ser accesibles por agentes (first-class citizens)»; en LLM se quitó
«Claude es uno»; el titular de la tool, a 22 pt en y=54. Tercera tanda: la lámina 10 completa subió 22 pt
(titular en y=36 con alto 32), incluidas flechas y tarjeta.

## Lluvia de preguntas (lámina 2)

Cada pregunta tiene detrás un conjunto de datos.cdmx.gob.mx, revisado el 19-oct-2026 con la API de CKAN
(`package_search` y `package_show`). Sirve para responder «¿de dónde sale esa?» y como lista de ideas para
la lámina 26.

| Pregunta | Conjunto (slug en datos.cdmx.gob.mx) |
| --- | --- |
| ¿Cuánta gente entró a Pantitlán en julio de 2026? | `afluencia-diaria-del-metro-cdmx` (la del taller) |
| ¿Cuántos meses estuvo cerrada la Línea 12? | `afluencia-diaria-del-metro-cdmx` (la contesta el servidor del taller) |
| ¿Qué estación del Metro perdió más gente desde 2019? | `afluencia-diaria-del-metro-cdmx` (la contesta el servidor del taller) |
| ¿Hay Ecobici libre cerca de mi Metro ahorita? | Feed GBFS de Ecobici (la contesta el paso 4); en el catálogo: `cicloestaciones-ecobici-nuevo-sistema` |
| ¿Las mujeres usan más Ecobici que antes? | `afluencia-diaria-del-sistema-ecobici` (viajes por género) |
| ¿Cuánta gente sube al Cablebús un domingo? | `afluencia-diaria-servicio-de-transportes-electricos` |
| ¿Qué alcaldía reporta más falta de agua? | `reportes-de-agua` (Sacmex) |
| ¿A qué hora se llama más al 911? | `llamadas-numero-de-atencion-a-emergencias-911` (C5) |
| ¿Dónde hay más choques los viernes? | `incidentes-viales-c5` |
| ¿En qué colonia hay más robos a transeúnte? | `victimas-en-carpetas-de-investigacion-fgj` |
| ¿Cuántas denuncias por ruido hay en mi colonia? | `denuncias-realizadas-ante-la-paot` |
| ¿Qué mes tiene el peor aire? | `indice-de-calidad-del-aire` (Sedema) |
| ¿Cuánto presupuesto tiene mi alcaldía? | `presupuesto-de-egresos` (2024) |
| ¿Dónde hay WiFi gratis cerca de mí? | `puntos-de-acceso-wifi-en-la-cdmx` |
| ¿Qué es lo que más le piden al gobierno por *0311? | `0311` |
| ¿Qué nombre se registra más en Coyoacán? | `nombres-registrados-en-actas-del-registro-civil` |
| ¿Cuántas bodas hay cada 14 de febrero? | `matrimonios-registrados-en-la-ciudad-de-mexico` |

## Qué te llevas (láminas 5 y 25)

Las dos láminas tienen la misma composición. Al inicio: cuatro entregables con círculos vacíos y cinco
preguntas. En el recap (lámina 25): los mismos entregables con palomita y las respuestas.

| Pregunta (lámina 5) | Respuesta (lámina 25) |
| --- | --- |
| ¿Qué es una tool y qué agrega MCP? | El modelo solo pide; tu código ejecuta. MCP estandariza cómo se publican y descubren las tools. |
| ¿Cuándo conviene MCP y cuándo una CLI o una API? | MCP si el modelo decide en runtime, para varios usuarios o sin tu terminal. Si no, CLI o API. |
| ¿Cómo diseño tools que el modelo elija bien? | Por intención y con errores que corrigen: el modelo solo lee nombre, descripción y schema. |
| ¿Dónde van los controles si una tool escribe? | En el código: validación, idempotencia, tope y aprobación del host. Nunca solo en el prompt. |
| ¿Cómo sé si Claude elige bien? | Con preguntas reales. Si falla, arregla la descripción, y separa el dato de lo que añade el modelo. |

Entregables: un servidor MCP con 7 tools, un resource y un prompt; conectado a Claude Code por HTTP, con
una acción que pide aprobación; una evaluación de 10 preguntas (`evaluar.py`); el mapa del Metro que
Claude extiende.

## Hallazgos técnicos

- **Sombras:** python-pptx agrega a cada forma un `<p:style>` que apunta al estilo de efectos del tema, que trae sombra exterior. Google Slides la aplica al convertir aunque la forma tenga `<a:effectLst/>`. `sin_estilo_del_tema()` quita ese `<p:style>` de cada forma y cada línea; verificado: 0 en el `.pptx` y bordes limpios en el PDF a 300 dpi.
- **Imágenes:** la API de Slides solo inserta imágenes desde una URL pública. Para no publicar
  la foto ni por un momento, la versión 2 sube un `.pptx` con las imágenes incrustadas y deja
  que Drive lo convierta. Verificado: el archivo sigue siendo `application/vnd.google-apps.presentation`,
  conserva el enlace y queda con `shared: false`.
- **`gws` y argumentos largos:** el envoltorio de Node (`run.js`) muere con SIGKILL cuando
  `--json` pasa de ~980 bytes; el binario nativo del paquete no. `gws` no lee `--json @archivo`
  ni stdin. `construir.py` usa el binario nativo.

## Pendiente

- [x] URL real del repo en las láminas 18 y 26 (`REPO` en `construir.py`). La lámina 18 dice `cd claude-mcp-ibero-2026`.
- [x] `CLAUDE.md`: la lámina 18 promete «abre claude en el repo y pídele que te guíe».
- [ ] Ensayar en voz alta con cronómetro; los minutos son una estimación.
- [ ] Poner en la lámina 7 cuántas personas de Spot2 usan los MCP (`PERSONAS_MCP` en `construir.py`; hoy
  dice `‹N›`). El dato vive en la base de auditoría de Djinn (Postgres `wormhole`, `AUTH_DATABASE_URL`), que
  no está replicada en ClickHouse. También se ve en el panel de Djinn, en `/dashboard/tool-logs`:

  ```sql
  SELECT count(DISTINCT user_id) AS personas, count(*) AS llamadas
  FROM tool_invocations
  WHERE created_at >= now() - interval '30 days';
  ```

  `tool_invocations` no guarda qué cliente hizo la llamada (Claude, ChatGPT o Cursor), así que no se puede
  desglosar por conector. Colossu registra sus llamadas en su propio activity log, aparte.
- [ ] Confirmar que se pueden nombrar en público Djinn, Colossu, Argos y Pythia, y que «Grok · pronto» es
  el nombre correcto (Dante dijo «grokbot»).
