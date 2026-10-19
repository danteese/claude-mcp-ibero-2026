# Verificación

Lo que se ejecutó de verdad, en esta máquina (macOS, uv 0.7.20, Python 3.12.9, FastMCP 4.1.0,
Claude Code 2.1.281), el 17-oct-2026.

## Datos

| Comprobación | Comando | Resultado |
| --- | --- | --- |
| Descarga desde las fuentes | `preparar.py` (descarga) | 195 estaciones del KMZ; afluencia de 2010 a 2026 en 17 consultas, una por año |
| Construcción de la base | `uv run preparar.py` | 38,804 filas mensuales (2010-01 a 2026-07); 195 estaciones con coordenadas; 6 reglas de limpieza registradas |

## Servidor (sin gastar cuota de Claude)

`verificar.py` usa un cliente MCP en memoria, así que no depende del transporte.

| Paso | Comando | Resultado |
| --- | --- | --- |
| 1 | `uv run verificar.py 1 --archivo pasos/01_hola.py` | 6 ✓, 0 ✗ |
| 2 | `uv run verificar.py 2 --archivo pasos/02_consulta.py` | 9 ✓, 0 ✗ |
| 3 | `uv run verificar.py 3 --archivo pasos/03_accion.py` | 12 ✓, 0 ✗ |
| 4 | `uv run verificar.py 4 --archivo pasos/04_final.py` | 13 ✓, 0 ✗ |

Los conteos incluyen las comprobaciones del entorno: Python, base, red hacia datos.cdmx.gob.mx
y GBFS, y Claude Code.

## HTTP

Servidor `pasos/04_final.py` en la sesión de tmux `taller-mcp`, en `http://127.0.0.1:8765/mcp`.

| Comprobación | Resultado |
| --- | --- |
| `uv run fastmcp list http://127.0.0.1:8765/mcp` | 7 tools listadas |
| `uv run fastmcp call … ranking_estaciones_metro limite=2 desde=2025-01 hasta=2025-12` | Pantitlán 55,622,303; Cuatro Caminos 35,149,370 |
| POST con `Host: evil.example.com` | **421**: rechazado por `host_origin_protection` |
| POST con `Origin: https://evil.example.com` | **403** "Forbidden Origin" |
| POST con `Origin: http://127.0.0.1:8765` | Pasa el guard. El 400 que devuelve es del protocolo ("Missing session ID", porque el `curl` manual no abre sesión) |

## Evaluación con Claude (gasta cuota)

`uv run evaluar.py`: 10 casos de `evals/casos.json`, cada uno con
`claude -p --strict-mcp-config --permission-mode dontAsk`, contra el servidor HTTP.

| Corrida | Resultado | Nota |
| --- | --- | --- |
| `evals/resultados/20261017-161139.json` | 9/10 | El caso de Tacubaya "falló": Claude confirmó la estación antes de intentar `registrar_reporte`. Fallaba la métrica, no el modelo (ver decisión D10) |
| `evals/resultados/20261017-161319.json` | 10/10 | Con la métrica corregida. `datos/reportes.sqlite` no se creó: el modo `dontAsk` bloqueó la escritura |

Costo observado: un solo caso medido aparte reportó `total_cost_usd` = 0.168. No es un
promedio. Las dos corridas usaron el modelo por defecto de Claude Code.

## Mapa

| Comprobación | Resultado |
| --- | --- |
| `uv run preparar.py` genera `mapa/datos.js` | 195 estaciones-línea × 199 meses, 238 KB |
| Orden por clave = recorrido de la línea | El salto más largo entre estaciones consecutivas es de 2,355 m (Guelatao → Peñón Viejo); las terminales son correctas en las 12 líneas |
| Cifras del mapa contra SQLite (consulta independiente) | abr-2020: 1,371,313 contra 1,371,315; jun-2021: 2,113,695 contra 2,113,701, con 20 en 0; oct-2022: 3,067,562, con 32 en 0; jul-2026: 3,346,186, con 0 en 0. La diferencia es de redondeo (Python y SQLite redondean distinto el .5) |
| Navegador (agent-browser, Chrome) | 195 círculos y 12 líneas; sin errores de consola; sin scroll horizontal a 390 px |
| Cabe en pantalla | Título, slider y mapa completo caben sin scroll a 1280×720 (el mapa termina en y=688) y a 1440×1000 |
| Ensayo en vivo: `claude -p` sobre una copia en `/tmp`, con Read, Edit y las tools `cdmx` | **42 s, US$0.33, 9 turnos.** Llamó `afluencia_metro` (Línea 12, 2010–2026) e hizo 3 ediciones pequeñas. El aviso aparece en jun-2021 y se oculta en jul-2026; sin errores de consola |
| Contrato de coordenadas de Ecobici | `verificar.py 4` pasa con el paso 4; con una copia sin `lat`/`lon`/`metro` falla con "no trae coordenadas" |
| Ensayo de la capa de Ecobici con `claude -p` | 31 s, US$0.20, 4 turnos; `mapa/ecobici.js` de 2,245 bytes; el panel dibuja 10 cuadros y 10 elementos en la lista; sin errores de consola, con y sin el archivo |

## Presentación

| Comprobación | Resultado |
| --- | --- |
| `uv run presentacion/construir.py --validar` | 24 láminas, unas 1,750 peticiones, 40 min |
| Construcción en Drive (cuenta dante@spot2.mx) | 24 láminas con las 24 notas del orador; carpeta "Taller MCP · Claude CDMX"; `shared: false`; un solo permiso (owner) |
| Revisión visual del PDF exportado (24 páginas) | Primera pasada: etiquetas encimadas en 6 láminas, títulos de dos líneas en 5, leyenda tapando una caja, texto partido. Corregido y revisado en hojas de contacto |
| Versión 2: gancho con `claude -p` (misma pregunta, mismo modelo) | Sin herramientas: «No puedo darte la cifra… unos 4 a 5 millones… es una estimación» (US$0.17). Con el servidor: «4,623,233 personas» (US$0.16). SQLite confirma 4,623,233 en 31 días |
| Versión 2: conversión del `.pptx` en Drive | `files update` sobre la misma presentación: sigue siendo Google Slides, 17 láminas, mismo enlace, `shared: false` |
| Versión 2: revisión visual del PDF exportado | Primera pasada: credenciales cortadas (lámina 4), titular encimado (6), texto al borde (7), titular pegado a la imagen (14). Corregido y revisado de nuevo |
| Versión 3: revisión visual del PDF exportado | 20 páginas. Primera pasada: chip partido (4), definiciones al borde (5 y 7), etiqueta invadiendo la caja del host (8), texto encimado (13), titulares de dos líneas pegados al contenido (7, 14 y 17). Corregido y revisado de nuevo |
| Versión 4: sombras y líneas | 0 `<p:style>` en el `.pptx` (antes, todas las formas apuntaban a un estilo con sombra exterior); acercamiento del PDF a 300 dpi con bordes limpios; revisión de las 21 láminas |
| Versión 5: láminas nuevas (9, 10, 12, 13) y glosario | 23 páginas, 40 min; 0 `<p:style>`. Primera pasada: dos puntos de la lámina 10 ocupaban tres líneas y se pegaban al siguiente; se recortaron. Revisión completa en hojas de contacto |
| Versión 5: afirmaciones contra la spec 2026-07-28 | Componentes y obligatoriedad (basic), sampling y roots obsoletos (client/sampling, client/roots), cambios (changelog), campos de tool, resource y prompt (server/*), anotaciones no confiables (server/tools), OAuth 2.1 (basic/authorization): leídos en las páginas oficiales con Parallel |
| Versión 6: apertura y recap | 25 páginas, 40 min (sumados desde las notas del `.pptx`); 0 `<p:style>`. Primera pasada: los dos titulares ocupaban dos líneas y chocaban con los encabezados; se acortaron a una línea |
| Versión 7: lámina de transporte y FastMCP; notas de elicitation | 26 páginas, 40 min (sumados desde las notas); 0 `<p:style>`; las notas de la lámina 13 contienen la explicación de elicitation. Primera pasada: titular en dos líneas y texto pegado al bloque de código; corregido |
| Lámina 6 (Spot2) con datos de Devin | Cuatro preguntas a DeepWiki sobre 10 repos; tools contadas en las conexiones de producción (Djinn 44, Colossu 65). La auditoría de Djinn no está en ClickHouse (sin tablas `tool_invocations` ni base `wormhole`). Primera pasada: negrita partida en «Una sola acción» y texto de la tarjeta en tres líneas; corregido |
| Clon limpio (19-oct-2026): `git clone` local → `uv run preparar.py` → `uv run verificar.py` | 38,804 filas (2010-01 a 2026-07), 195 estaciones, `mapa/datos.js`; entorno «Todo en orden» |
| Clon limpio: `uv run verificar.py N --archivo pasos/0N_*.py` (N = 1 a 4) y `cp pasos/04_final.py servidor.py` + `verificar.py 4` | Los cuatro contratos pasan; el punto de control copiado a `servidor.py` encuentra `datos/` |
| Clon limpio: `uv run servidor.py` + `uv run fastmcp list http://127.0.0.1:8765/mcp` | 7 tools por HTTP |
| `claude mcp list` en el clon | `cdmx` en «Pending approval» hasta abrir `claude` |
| `claude` interactivo en el clon (tmux) | Dos pantallas: confianza en la carpeta y «New MCP server found: cdmx»; en las dos viene marcada la opción que no sirve (se documentó en el README). `registrar_reporte` pidió aprobación aunque Claude Code estaba en modo auto; aprobado → folio CDMX-00001 en `datos/reportes.sqlite` |
| `claude -p` con las 4 preguntas del README (`--allowedTools mcp__cdmx__*`) | Bicicletas → `buscar_datasets_cdmx`; Pantitlán jul-2026 → 4,623,233; reporte → bloqueado («requires permission»), sin escribir; Ecobici → 12 cicloestaciones a 500 m de Insurgentes |
| `claude -p "guíame paso a paso"` con `servidor.py` en el paso 1 | Corrió `verificar.py`, detectó el paso 1 completo y explicó el paso 2 con sus comprobaciones |
| `uv run evaluar.py` en el clon | 10/10 |
| `fastmcp install claude-desktop servidor.py --project . --config-path <temporal>` | Genera la configuración con `"command": "uv"`; un cliente stdio con esa configuración lista y llama la tool. `uv` no está en el PATH mínimo de macOS (nota en el README) |
| `mapa/index.html` en el clon (agent-browser) | 199 meses, 195 círculos, julio de 2026 con Pantitlán primero (149,137) |
| `uv run presentacion/construir.py --local` en el clon | Sin `recursos/`: mensaje claro con las tres imágenes que faltan. Con ellas: 26 láminas, 40 min |
| Lámina 2: lluvia de preguntas | 16 preguntas, cada una con un conjunto encontrado con `package_search` y leído con `package_show` en datos.cdmx.gob.mx (19-oct-2026). PDF de Google revisado: sin encimados; primera pasada con «2019?» huérfano, corregido. 26 láminas, 40 min |
| `gws` con `--json` largo | El envoltorio de Node muere (exit 137 / -9) a partir de ~980 bytes; el binario nativo acepta 10 KB |

## Estilo

`uvx ruff check .` y `uvx ruff format --check` pasan, con `line-length = 120`.

## No verificado

- Claude Desktop con el servidor HTTP.
- Que Claude Code se reconecte solo al reiniciar el servidor.
- El flujo interactivo completo en Claude Code: aprobar `registrar_reporte` desde el
  diálogo, `/mcp__cdmx__informe_estacion` y `@cdmx:cdmx://fuentes`.
- Windows y Linux.
- Una máquina limpia, sin uv instalado ni caché.
