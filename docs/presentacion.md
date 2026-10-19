# Presentación

**Dónde está:** Google Slides en el Drive de dante@spot2.mx, carpeta "Taller MCP · Claude CDMX".
Es privada: solo la persona dueña tiene permiso. El enlace y los IDs están en
`presentacion/.ids.json` (no se versiona).

**Versión actual:** 7. Son 26 láminas: 25 se presentan en 40 minutos y la última es un glosario de consulta. Historial en `storytelling.md`.

**Reglas:** todas las láminas son claras (no sabemos cómo proyecta el foro una oscura); sin sombras ni líneas decorativas, así que solo hay flechas y líneas con significado (el diagrama M×N); cada concepto lleva su tarjeta de «Definición». La lámina 6 (Spot2) se armó con lo que respondió Devin sobre los repositorios de Spot2 (D17); falta el número de personas (`PERSONAS_MCP`).

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
| 2 | 0.5–1 | ¿Cuánta gente entró a la estación Pantitlán en julio de 2026? | — |
| 3 | 1–2 | Sin herramientas, Claude estima. Con tu servidor MCP, responde con el dato. | — |
| 4 | 2–3 | **Al terminar tendrás un servidor MCP tuyo, conectado** (qué te llevas) | — |
| 5 | 3–3.5 | Quién soy: foto, rol y trayectoria | — |
| 6 | 3.5–4.5 | En Spot2, cada capacidad nace con su API y su MCP | — (callback del diagrama M×N; API/MCP first) |
| 7 | 4.5–5.5 | Un modelo convierte texto en texto: saber y actuar hay que dárselo | LLM |
| 8 | 5.5–7 | Una tool es una función que el modelo pide y tu código ejecuta | Tool, function calling, agente |
| 9 | 7–8.5 | MCP es el estándar para conectar la IA con tus sistemas | MCP (y el diagrama M×N contra M+N) |
| 10 | 8.5–10 | La IA puede usar API, CLI o MCP: elige según la situación | — |
| 11 | 10–12 | MCP te da control y alcance; lo pagas en contexto y riesgo | — |
| 12 | 12–13 | En MCP participan tres actores: host, client y server | Host, client, server, transporte |
| 13 | 13–15 | MCP tiene tres capas obligatorias; el resto es opcional | Componentes de la spec 2026-07-28 |
| 14 | 15–16 | Tres piezas, una pregunta: ¿quién decide cuándo ocurre? | Tool, resource, prompt (y sus campos) |
| 15 | 16–17 | **Construimos un servidor MCP por HTTP con FastMCP** | Transportes (stdio, HTTP local, HTTP remoto), FastMCP, FastAPI |
| 16 | 17–19 | Construyamos (instalación) | Datos abiertos, uv |
| 17 | 19–23 | Paso 1 · Una función con docstring ya es una tool | FastMCP, docstring, schema |
| 18 | 23–27 | Paso 2 · Diseña para quien lee el contrato: el modelo | Contexto |
| 19 | 27–31.5 | Paso 3 · Si la tool escribe, los controles van en el código | Idempotente |
| 20 | 31.5–34.5 | Paso 4 · Mide si Claude elige bien | Evaluación (eval) |
| 21 | 34.5–35.5 | El mismo dato, ahora en un mapa para personas | — |
| 22 | 35.5–37 | Claude extiende el mapa; tú lees lo que añade | — |
| 23 | 37–38.5 | **Recap: tienes un servidor MCP y sabes cuándo usarlo** | — |
| 24 | 38.5–39.5 | Ahora te toca | — |
| 25 | 39.5–40 | Si el agente falla, arregla la descripción, no el modelo. | — |
| 26 | — | Glosario del taller (apéndice, no se presenta) | 24 términos |

Las notas del orador de cada lámina tienen el guion, el tiempo y las marcas [EN VIVO]. Las de la lámina 13 explican elicitation (qué es, ejemplo, modos, qué no es y por qué no la usamos hoy), por si sale en preguntas.

## Qué te llevas (láminas 4 y 23)

Las dos láminas tienen la misma composición. Al inicio: cuatro entregables con círculos vacíos y cinco
preguntas. En el recap (lámina 23): los mismos entregables con palomita y las respuestas.

| Pregunta (lámina 4) | Respuesta (lámina 22) |
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

- [ ] Poner la URL real del repo en las láminas 16 y 24 (`REPO` en `construir.py`; hoy dice `URL-DEL-REPO`).
- [ ] Escribir el `CLAUDE.md`: la lámina 16 promete «abre claude en el repo y pídele que te guíe».
- [ ] Ensayar en voz alta con cronómetro; los minutos son una estimación.
- [ ] Poner en la lámina 6 cuántas personas de Spot2 usan los MCP (`PERSONAS_MCP` en `construir.py`; hoy
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
