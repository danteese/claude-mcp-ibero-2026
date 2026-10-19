# Decisiones

Formato: decisión · por qué · alternativas descartadas · consecuencias.

## D1. Dominio: Metro de la CDMX y Ecobici

- **Por qué:** cualquier persona en la sala conoce el Metro. Los datos cuentan historias sin
  mucha explicación: el cierre de la Línea 12, la caída por COVID en 2020 y Pantitlán como
  la estación más concurrida. Además, los datos vienen con errores reales que sirven para
  enseñar diseño de tools.
- **Descartado:** calidad del aire, solicitudes *0311 y afluencia desglosada por medio de
  pago. Siguen disponibles en el portal si se quiere cambiar (ver `datos.md`).

## D2. Copia local agregada por mes, en SQLite, generada con `uv run`

- **Por qué:** el CSV oficial pesa 60 MB (1,180,920 filas diarias) y el Wi-Fi de un evento
  no es confiable. Se agrega por mes dentro de la API de CKAN y queda una copia de 1.7 MB en
  el repo. SQLite viene con Python, así que no hay que instalar nada.
- **Cómo:** `uv run preparar.py` construye la base sin red. `uv run preparar.py --descargar`
  refresca los CSV desde el portal.
- **Consecuencia:** las tools de consulta funcionan sin internet. Solo `buscar_datasets_cdmx`
  y `ecobici_cerca_de_metro` necesitan red, y lo dicen en su descripción y en su error.

## D3. La limpieza vive en `preparar.py` y queda registrada en la base

- **Por qué:** los CSV `*_crudo.csv` se guardan tal cual llegan, para que se pueda auditar.
  Cada regla de limpieza escribe su conteo en la tabla `limpieza`, y el resource
  `cdmx://fuentes` la publica.
- **Consecuencia:** la presentación puede mostrar las reglas con números reales (ver `datos.md`).

## D4. Cuatro puntos de control y una copia de trabajo

- `pasos/01_hola.py`: una tool que busca en el catálogo de CKAN, en vivo.
- `pasos/02_consulta.py`: tools por intención sobre SQLite, más el resource `cdmx://fuentes`.
- `pasos/03_accion.py`: una acción controlada (`registrar_reporte`) y el prompt `informe_estacion`.
- `pasos/04_final.py`: añade Ecobici en vivo cruzado con la ubicación del Metro.
- `servidor.py` empieza como copia del paso 1; si alguien se atrasa, copia el siguiente punto de control.

## D5. Reglas de diseño de tools aplicadas en el código

- Tools por intención (`afluencia_metro`, `ranking_estaciones_metro`), no `ejecutar_sql(query)`.
- Parámetros cerrados: `Linea` es un `Literal` con las 12 líneas y `Mes` exige el formato `AAAA-MM`.
- Los errores explican cómo corregirse: con un nombre ambiguo, ofrecen las opciones; con una
  línea equivocada, dicen en qué línea está la estación.
- Cada salida trae unidad, alcance, fuente y avisos de calidad de datos (meses en cero, duplicados).
- La base de consulta se abre en solo lectura (`mode=ro`): esas tools no pueden escribir.

## D6. Acción controlada con `anthropic/requiresUserInteraction`, no con elicitation

- **Por qué:** en FastMCP 4, `ctx.elicit()` solo funciona en conexiones con handshake
  (protocolo 2025-11-25 o anterior), e `InputRequiredResult` solo funciona en 2026-07-28.
  Claude Code elige la versión del protocolo según el runtime, así que la confirmación por
  elicitation dependería de la versión negociada. En cambio, `requiresUserInteraction` lo
  hace cumplir el host: Claude Code pide aprobación en cada llamada y en modo `dontAsk` la
  niega.
- **Controles que no dependen del host:** base de reportes separada; validación de que la
  estación existe en esa línea; idempotencia mediante una huella diaria; tope de 20 reportes
  por hora; el texto ciudadano se devuelve marcado como no confiable.
- **Límite:** `anthropic/requiresUserInteraction` es un metadato propio de Claude Code; otros
  hosts pueden ignorarlo. Por eso los controles del código no se quitan.

## D7. Anotaciones como diccionario

`annotations={"readOnlyHint": True, ...}` en lugar de `ToolAnnotations(...)`: se serializa
igual, el código del participante tiene un import menos y se evita el aviso de deprecación
del SDK v2 al leer `.readOnlyHint`.

## D8. Transporte HTTP (Streamable HTTP), no stdio

- **Por qué:** preferencia de Dante. Además, refleja cómo se despliega un servidor real y
  evita que Claude Code lance el proceso.
- **Configuración:** `mcp.run(transport="http", host="127.0.0.1", port=8765, host_origin_protection=True)`.
  - `127.0.0.1`: solo la propia máquina puede conectarse, no la red del evento.
  - Puerto 8765: el 8000 estaba ocupado en esta máquina (otro proceso de `node`) y es común
    que lo esté en las de los participantes.
  - `host_origin_protection=True`: FastMCP la trae apagada por defecto. Con ella, una página
    web no puede usar el navegador para llamar al servidor local (DNS rebinding). Verificado:
    con un Host ajeno responde 421 y con un Origin ajeno responde 403.
- **Consecuencias:** el servidor tiene que estar corriendo antes de abrir Claude Code;
  `.mcp.json` usa `"type": "http"`; `evaluar.py` se conecta a la URL en lugar de lanzar el archivo.

## D9. tmux para la preparación, no para el taller

El servidor de desarrollo corre en la sesión `taller-mcp`. A los participantes no se les
pide tmux porque no viene instalado en todas las máquinas.

## D10. Métrica de la evaluación

- **Antes:** contaba solo la primera tool que llamaba Claude. En el caso "levanta un reporte
  en Tacubaya", Claude primero confirmó la estación con `buscar_estacion_metro` y luego llamó
  `registrar_reporte`. Eso es lo que pide la descripción de la tool, y aun así se contaba
  como fallo.
- **Ahora:** un caso pasa si Claude llama la tool esperada con los argumentos esperados,
  aunque antes haga otras consultas. En modo `dontAsk` la llamada que requiere aprobación se
  bloquea: el intento cuenta y no se escribe nada.
- **Lo que no mide:** si la respuesta final es correcta. Esa es otra evaluación.

## D11. Versiones y herramientas

- Python `>=3.11` (uv eligió 3.12.9 aquí). Dependencias: `fastmcp>=4.1,<5` y `httpx`.
- FastMCP 4.1.0 (8-oct-2026) sirve las dos eras del protocolo desde el mismo servidor.
- Claude Code 2.1.281 en esta máquina.
- `ruff` con `line-length = 120`; se ejecuta con `uvx ruff`, sin instalarlo.

## D12. Cierre con un mapa del Metro, por mes, en un solo HTML

- **Por qué:** Dante pidió concentrarse en un caso, el de mejor información, y que "menos es
  más". El Metro tiene estación, coordenadas y 16 años; Ecobici en el portal no tiene
  estación. Por hora o en tiempo real no hay datos del Metro.
- **Cómo:** `preparar.py` exporta `mapa/datos.js` y `mapa/index.html` lo dibuja en SVG. Sin
  dependencias ni servidor; abre con doble clic. En vivo, Claude lo modifica usando las tools MCP.
- **Descartado:** slider de hora estimado, MCP Apps y servir el mapa desde FastMCP con `custom_route`.
- **Revisión (mismo día):** Dante pidió agregar Ecobici "sin perder el objetivo: mostrar la
  construcción del MCP". Se agregó como panel, pero el dato llega **por la tool**, no por el
  navegador: la tool ahora devuelve coordenadas, Claude guarda su salida en `mapa/ecobici.js`
  y el mapa la dibuja.
- Detalle y guion en `demo-mapa.md`.

## D13. Presentación como Google Slides nativo, generada con `gws`

- **Por qué:** Dante pidió trabajarla con `gws` y subirla a su Drive de Spot2. Con formas
  nativas, los diagramas se pueden editar en Slides, no son imágenes pegadas.
- **Cómo:** `presentacion/construir.py` arma las peticiones de la API de Slides y las envía con
  el binario nativo de `gws` (el envoltorio de Node muere con argumentos de más de ~1 KB; ver
  `presentacion.md`). Vive en una carpeta privada y no se comparte.
- **Descartado:** HTML exportado a PDF (no se edita en Drive).
- **Revisión, versión 2 (mismo día):** Dante rechazó la versión 1 por monótona, larga, sin
  introducción ni porqué y con diagramas pobres. Se rehízo con la investigación de
  `storytelling.md` (17 láminas). El método cambió a `.pptx` convertido por Drive, porque la API
  de Slides solo inserta imágenes desde URLs públicas y había que incluir la foto y la captura
  sin compartir nada. Se sube con `files update` sobre la misma presentación, así que el enlace
  no cambia.
- **Revisión, versión 3 (mismo día):** se agregan definiciones (dos láminas nuevas, tarjetas de
  «Definición» y un glosario) y se eliminan las láminas oscuras por la proyección del foro. Son
  20 láminas: 19 se presentan en 40 minutos y el glosario es un apéndice.
- **Revisión, versión 4 (mismo día):** sin sombras (se quita el `<p:style>` del tema en cada forma) y
  sin líneas decorativas. «Quién soy» se separa en una lámina personal y una sobre Spot2 que escribe
  Dante. Son 21 láminas; el tiempo no cambia.

## D14. Por qué MCP, contado con honestidad, y la anatomía de la spec

- **Por qué:** Dante señaló que la lámina «MCP vs API vs CLI» no respondía lo importante: la IA puede usar
  las tres, así que ¿qué incentivo hay para tener un MCP y qué problemas trae? También pidió decir de qué
  se compone MCP, revisando el estándar.
- **Qué cambió (versión 5):** dos láminas de «¿Por qué MCP?» (cuál conviene según la situación, y lo que
  MCP te da contra lo que cuesta) y una lámina de «De qué se compone» basada en la spec 2026-07-28 (tres
  capas obligatorias y el resto opcional, con sampling y roots marcados como obsoletos). La lámina de tool,
  resource y prompt ahora dice con qué campos se define cada una. El glosario pasa a 24 términos.
- **Tiempo:** los conceptos ganan 2 minutos; Construyamos, los pasos 1 y 3 y «Ahora te toca» ceden medio
  minuto cada uno. Siguen siendo 40 minutos.
- Fuentes y tabla completa en `fuentes-mcp-api-cli.md`.

## D15. Objetivos al inicio y recap al final, en láminas espejo

- **Por qué:** Dante no veía claro el resultado ni las ideas que se lleva la sala. The Carpentries recomienda
  aclarar objetivos al inicio y consolidar al final.
- **Cómo:** una función `tablero()` en `construir.py` dibuja las dos láminas con la misma composición
  (entregables a la izquierda, preguntas o respuestas a la derecha). Las preguntas siguen el orden del
  taller, así que cada respuesta del recap apunta a una sección.
- **Tiempo:** +2.5 min, compensados con medio minuto de cinco láminas. Siguen siendo 40.

## D16. Decir qué tipo de servidor construimos y aclarar FastMCP frente a FastAPI

- **Por qué:** Dante pidió dejar claro que hoy se construye un servidor MCP por HTTP, que existen otros tipos
  y qué es FastMCP frente a FastAPI.
- **Qué:** lámina 15, antes de «Construyamos». A la izquierda, los tipos según el transporte: stdio local,
  HTTP local (el de hoy) y HTTP remoto con OAuth 2.1; las tools no cambian, el transporte es un argumento de
  `mcp.run()`. A la derecha, las definiciones de FastMCP y FastAPI y cómo se combinan (`app.mount` y
  `FastMCP.from_fastapi`), con la advertencia de la documentación de FastMCP: los servidores curados rinden
  mejor que las APIs convertidas, así que la conversión es para prototipar.
- **Elicitation:** no se agregó lámina; la explicación completa va en las notas de la lámina 13.
- **Tiempo:** +1 min; los pasos 1 y 2 ceden medio minuto cada uno (el paso 1 ya no presenta FastMCP ni el transporte).

## D17. Lámina 6: lo que Spot2 hace con MCP, según Devin

- **Por qué:** Dante pidió preguntarle a Devin qué se ha implementado de MCP en Spot2, quién lo usa, y
  contar que ahora se diseña API/MCP first, con conectores en Claude, ChatGPT y Grok (próximamente).
- **Qué:** la lámina repite el diagrama «Con MCP» de la lámina 9, ahora con lo real: clientes (Claude,
  ChatGPT, Pythia y Grok en gris, porque viene pronto) → MCP → cuatro servidores (Djinn, Colossu, Spot2.mx
  en ChatGPT y Argos). A la derecha, el número de personas (pendiente) y un diagrama de API/MCP first: el
  endpoint REST y la tool MCP llegan a una sola acción.
- **Cifras:** 44 tools en Djinn y 65 en Colossu, contadas en las conexiones MCP de producción el
  17-oct-2026 (Devin decía 43 para Djinn: su wiki va un poco atrás). El número de personas no está en el
  código; Devin no lo puede dar y se deja como `PERSONAS_MCP`.
- **Lo que no se dice:** URLs internas ni detalles de autenticación más allá de «te conectas con tu cuenta
  de Google de Spot2».
