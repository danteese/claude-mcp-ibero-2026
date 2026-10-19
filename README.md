# Datos abiertos over MCP: Claude que consulta fuentes reales

Taller práctico de 40 minutos · Claude for AI Engineering · CDMX · Ibero.

Construyes un servidor MCP en Python con [FastMCP](https://gofastmcp.com) y lo conectas a Claude Code.
Con él, Claude consulta datos abiertos reales de la Ciudad de México: el catálogo de datos.cdmx.gob.mx,
la afluencia del Metro mes por mes y la disponibilidad de Ecobici en vivo. También registra un reporte
ciudadano con controles: aprobación humana, validación, idempotencia y un tope por hora.

## Qué necesitas

- **[uv](https://docs.astral.sh/uv/getting-started/installation/)**. Instala Python 3.11+ y las
  dependencias correctas; no instalas nada más.
  - macOS y Linux: `curl -LsSf https://astral.sh/uv/install.sh | sh`
  - Windows: `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`
- **Claude Code** (`claude` en la terminal) con tu sesión iniciada. También funciona con Claude Desktop
  (ver más abajo).
- **git**, o descarga el ZIP del repo.

Los datos del Metro vienen en el repo: preparar la base no necesita internet. Solo las tools en vivo
(el catálogo de datos.cdmx.gob.mx y Ecobici) usan la red.

## Empezar

```sh
git clone https://github.com/danteese/claude-mcp-ibero-2026
cd claude-mcp-ibero-2026
uv run preparar.py      # datos → SQLite, sin internet
uv run verificar.py     # ¿todo listo?
```

`verificar.py` revisa Python, los datos, la red y Claude Code. Si algo falla, te dice qué hacer.

## Cómo se corre: dos terminales

| Terminal | Comando | Qué hace |
| --- | --- | --- |
| 1 | `uv run servidor.py` | Levanta tu servidor MCP en `http://127.0.0.1:8765/mcp`. Solo tu máquina puede conectarse. Déjala abierta. |
| 2 | `claude` | Abre Claude Code en la carpeta del repo. El archivo `.mcp.json` ya lo conecta al servidor `cdmx`. |

- **La primera vez**, Claude Code hace dos preguntas y en las dos viene marcada la opción que no
  sirve. Muévete con las flechas antes de presionar Enter:
  1. «Is this a project you created or one you trust?» → **Yes, I trust this folder**.
  2. «New MCP server found in this project: cdmx» → **Use this MCP server**.

  Con `/mcp` ves si está conectado y qué tools expone. Si lo saltaste, aprúebalo desde ahí.
- **Cada vez que cambies `servidor.py`**, reinícialo en la terminal 1 (`Ctrl-C` y otra vez
  `uv run servidor.py`). Si Claude no ve las tools nuevas, reconéctalo desde `/mcp`.
- **Para ver tus tools sin Claude**, tal como las verá el modelo:

  ```sh
  uv run fastmcp list http://127.0.0.1:8765/mcp
  ```

## Los cuatro pasos

Trabajas sobre `servidor.py`, que empieza igual que el paso 1. Cada paso tiene una comprobación y un
punto de control en `pasos/` con la solución.

| Paso | Qué agregas | Comprueba | Punto de control |
| --- | --- | --- | --- |
| 1 · Una tool | `buscar_datasets_cdmx`: busca en el catálogo de datos.cdmx.gob.mx | `uv run verificar.py 1` | `pasos/01_hola.py` |
| 2 · Diseño | `buscar_estacion_metro`, `afluencia_metro`, `ranking_estaciones_metro` y el resource `fuentes`: tools por intención, errores que corrigen, respuestas cortas | `uv run verificar.py 2` | `pasos/02_consulta.py` |
| 3 · Una acción | `registrar_reporte` (escribe, con aprobación humana en cada llamada), `consultar_reportes` y el prompt `informe_estacion` | `uv run verificar.py 3` | `pasos/03_accion.py` |
| 4 · Medir | `ecobici_cerca_de_metro` (en vivo), `actualizar_mapa_ecobici` (escribe `mapa/ecobici.js` para el mapa) y la evaluación con `uv run evaluar.py` | `uv run verificar.py 4` | `pasos/04_final.py` |

**¿Te atrasaste?** Copia el punto de control y reinicia la terminal 1:

```sh
cp pasos/02_consulta.py servidor.py
```

### Preguntas para probar en Claude Code

- Paso 1: «¿Qué datos abiertos hay sobre bicicletas?»
- Paso 2: «¿Cuánta gente entró a Pantitlán en julio de 2026?» · «¿Cuándo estuvo cerrada la Línea 12?»
- Paso 3: «Levanta un reporte: el elevador de Pantitlán, Línea A, no funciona». Claude Code te pide
  aprobarlo antes de escribir.
- Paso 4: «¿Hay Ecobici cerca del Metro Insurgentes?»

### Medir si Claude elige bien

Con el servidor corriendo en la terminal 1:

```sh
uv run evaluar.py
```

Corre las 10 preguntas de `evals/casos.json`, cada una en una sesión de `claude -p` que solo ve tu
servidor, y cuenta si Claude llamó la tool correcta con los argumentos correctos. **Gasta tu cuota de
Claude**: unas pocas llamadas por caso. Si un caso falla, mejora la descripción o el schema de la
tool, no el prompt.

## El mapa

`uv run preparar.py` también genera los datos del mapa. Abre `mapa/index.html` en tu navegador y
mueve el slider de meses: cada círculo es una estación, y su tamaño, las entradas diarias promedio.

Debajo del mapa está la sección «Ecobici en vivo cerca del Metro». Se llena con el paso 4: pídele a
Claude «Actualiza el mapa de Ecobici para el Metro Insurgentes». La tool `actualizar_mapa_ecobici`
consulta Ecobici, escribe `mapa/ecobici.js` y a Claude sólo le devuelve un resumen. Recarga la página.
Es una foto del momento de la consulta: para actualizarla, se lo vuelves a pedir. Sin Claude:

```sh
uv run fastmcp call pasos/04_final.py actualizar_mapa_ecobici estacion=Insurgentes
```

Reto de cierre, en Claude Code:

> Usa el servidor cdmx para saber cuándo estuvo en cero la Línea 12 y agrega a mapa/index.html un
> aviso que aparezca solo en esos meses.

Luego lee lo que agregó: ¿qué dice el dato y qué añadió el modelo?

## Claude Desktop (opcional)

En lugar de las dos terminales, Claude Desktop puede lanzar tu servidor por stdio:

```sh
uv run fastmcp install claude-desktop servidor.py --project .
```

Reinicia Claude Desktop. Si después cambias `servidor.py`, vuelve a reiniciar Claude Desktop.

Si Claude Desktop dice que no encuentra `uv`, abre su configuración (Settings → Developer → Edit Config)
y cambia `"command": "uv"` por la ruta completa que te da `which uv` (por ejemplo,
`/opt/homebrew/bin/uv`). Las apps de macOS no siempre ven el mismo PATH que tu terminal.

## Para seguir

- **Califica tus definiciones con TDQS.** `evaluar.py` mide si Claude elige la tool correcta; el
  [Tool Definition Quality Score](https://github.com/glama-ai/tool-definition-quality-score) de Glama
  califica cada definición por separado en seis dimensiones (claridad del propósito, cuándo usarla y
  cuándo no, comportamiento, significado de los parámetros, concisión y completitud), con una nota de
  1 a 5 y un nivel de A a F. Su rúbrica sirve como lista de revisión aunque no lo corras.
- **Empaqueta una skill con tu servidor.** Un `SKILL.md` le dice al agente en qué orden usar tus tools
  y qué revisar. FastMCP puede servirla desde el propio servidor (`SkillsDirectoryProvider`, extensión de
  Skills de MCP, SEP-2640).

## ¿Atorado?

Abre `claude` en la carpeta del repo y pídele: **«guíame paso a paso»**. `CLAUDE.md` le dice cómo
revisar en qué paso vas y qué sigue.

| Síntoma | Qué hacer |
| --- | --- |
| `address already in use` al levantar el servidor | Ya hay otro servidor en el puerto 8765. Ciérralo (`Ctrl-C` en su terminal) o búscalo con `lsof -i :8765`. |
| Claude no ve las tools | ¿Está corriendo la terminal 1? Revisa `/mcp` en Claude Code y reconecta. |
| Falla `buscar_datasets_cdmx`, `ecobici_cerca_de_metro` o `actualizar_mapa_ecobici` | Necesitan internet. Las tools del Metro funcionan sin red. |
| `falta datos/cdmx.sqlite` | Corre `uv run preparar.py`. |

## De dónde sale cada dato

El servidor corre en tu máquina. La mayoría de las tools lee una copia local; sólo tres salen a internet.

```
Claude Code ──► tu servidor MCP (127.0.0.1:8765)
                  ├─ datos/cdmx.sqlite ............ Metro: copia local, sin internet
                  ├─ datos/reportes.sqlite ........ reportes del paso 3 (local)
                  ├─ API CKAN de datos.cdmx.gob.mx  catálogo (internet)
                  └─ feed GBFS de Ecobici ......... bicis en vivo (internet)
```

- **El histórico del Metro es local** porque no cambia: la consulta es instantánea y el taller funciona
  sin Wi-Fi. `preparar.py` lo arma con los CSV del repo.
- **Lo que cambia se consulta en vivo**: el catálogo de datos y las bicis disponibles.
- **CKAN** (*Comprehensive Knowledge Archive Network*) es el software de código abierto con el que
  muchos gobiernos publican datos abiertos; datos.cdmx.gob.mx es un portal CKAN. `buscar_datasets_cdmx`
  usa su API (`/api/3/action/package_search`), que devuelve qué conjuntos existen (título, dependencia,
  formatos, enlace), no los datos. Cualquier otro portal CKAN responde igual.
- **GBFS** (*General Bikeshare Feed Specification*) es el formato abierto en el que los sistemas de
  bicis compartidas publican sus estaciones y su disponibilidad.
- El modelo no corre en tu máquina: lo que devuelve cada tool viaja a Claude como parte de la
  conversación. Por eso las tools devuelven resúmenes y no tablas completas.

## Los datos

| Conjunto | Fuente | Licencia |
| --- | --- | --- |
| Afluencia diaria del Metro | [datos.cdmx.gob.mx](https://datos.cdmx.gob.mx/dataset/afluencia-diaria-del-metro-cdmx) | CC-BY-4.0 |
| Líneas y estaciones del Metro | [datos.cdmx.gob.mx](https://datos.cdmx.gob.mx/dataset/lineas-y-estaciones-del-metro) | CC-BY-4.0 |
| Disponibilidad de Ecobici (en vivo) | Feed GBFS público de Ecobici | Ver los términos de Ecobici |

- Los CSV de `datos/` son la copia cruda de la fuente; `preparar.py` los limpia al construir
  `datos/cdmx.sqlite`. Para volver a bajarlos: `uv run preparar.py --descargar`.
- La afluencia cuenta **entradas**, no la ocupación de los trenes.
- La Línea 12 está en cero de junio de 2021 a diciembre de 2022.
- Más detalle en [`docs/datos.md`](docs/datos.md).

## Qué hay en el repo

| Ruta | Qué es |
| --- | --- |
| `servidor.py` | Tu servidor; empieza igual que el paso 1 |
| `pasos/` | Puntos de control de los pasos 1 a 4 |
| `preparar.py` | Construye `datos/cdmx.sqlite` y los datos del mapa |
| `verificar.py` | Revisa tu entorno y que tu servidor cumpla el contrato de cada paso |
| `evaluar.py`, `evals/casos.json` | La evaluación: 10 preguntas reales |
| `.mcp.json` | Conecta Claude Code al servidor en `http://127.0.0.1:8765/mcp` |
| `mapa/index.html` | Mapa de afluencia del Metro por mes |
| `presentacion/construir.py` | Genera la presentación del taller |
| `docs/` | Bitácora: decisiones, fuentes, verificaciones y la agenda de la presentación |
