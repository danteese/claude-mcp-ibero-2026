# Taller «Datos abiertos over MCP»

Quien te habla está en un taller de 40 minutos: construye un servidor MCP con FastMCP que expone datos
abiertos de la CDMX. Puede ser su primera vez con Python o con MCP. Responde en español, en pasos
cortos, y explica el porqué en una o dos frases.

## Si te pide «guíame paso a paso»

1. Corre `uv run verificar.py` y explica el resultado. Si falta `datos/cdmx.sqlite`, corre
   `uv run preparar.py`.
2. Averigua en qué paso va: compara las tools de `servidor.py` con las de `pasos/` y corre
   `uv run verificar.py N` con el último paso que debería cumplir.
3. Explica el siguiente paso y muestra lo que cambia respecto al punto de control (`pasos/0N_*.py`).
   Deja que lo escriba; si va atrasado o te lo pide, ofrece copiar el punto de control a `servidor.py`.
4. Después de cada cambio: pídele que reinicie el servidor en su terminal (`Ctrl-C` y
   `uv run servidor.py`), que lo compruebe con `uv run verificar.py N` y que pruebe una pregunta en
   Claude Code. Si no aparecen las tools nuevas, que reconecte desde `/mcp`.

| Paso | Agrega | Comprueba |
| --- | --- | --- |
| 1 | `buscar_datasets_cdmx` | `uv run verificar.py 1` |
| 2 | `buscar_estacion_metro`, `afluencia_metro`, `ranking_estaciones_metro`, resource `fuentes` | `uv run verificar.py 2` |
| 3 | `registrar_reporte` (aprobación humana), `consultar_reportes`, prompt `informe_estacion` | `uv run verificar.py 3` |
| 4 | `ecobici_cerca_de_metro`; evaluación con `uv run evaluar.py` | `uv run verificar.py 4` |

## Cómo está armado

- El servidor corre por HTTP en `http://127.0.0.1:8765/mcp`; la persona lo levanta en otra terminal con
  `uv run servidor.py`. `.mcp.json` conecta Claude Code a ese servidor con el nombre `cdmx`.
- `servidor.py` es su copia de trabajo. `pasos/` son las soluciones de referencia.
- `datos/cdmx.sqlite` es de solo lectura y se reconstruye con `uv run preparar.py`. Los reportes se
  escriben aparte, en `datos/reportes.sqlite`.
- Para ver las tools como las ve el modelo: `uv run fastmcp list http://127.0.0.1:8765/mcp`.

## Reglas

- Edita solo `servidor.py` (y `mapa/index.html` en el reto del mapa). No modifiques `pasos/`,
  `evals/casos.json` ni los CSV de `datos/`.
- Conserva `host="127.0.0.1"` y `host_origin_protection=True` en `mcp.run`: el servidor no debe quedar
  expuesto al Wi-Fi del evento.
- Usa `registrar_reporte` solo si la persona pide explícitamente levantar un reporte.
- `uv run evaluar.py` gasta su cuota de Claude: avísale antes de correrlo.
- Cuando respondas con datos del servidor `cdmx`, di de qué fuente salen y separa lo que dice el dato
  de lo que agregas tú.
- Si una tool elige mal o recibe argumentos equivocados, propón mejorar su descripción o su schema,
  no el prompt.
