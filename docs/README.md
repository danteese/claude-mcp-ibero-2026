# Bitácora del taller

**Taller:** Datos abiertos over MCP: Claude que consulta fuentes reales
**Evento:** Claude for AI Engineering · CDMX · Universidad Iberoamericana
**Duración:** 40 minutos. El temario v6 (`../temario-mcp-v6.md`) está escrito para 55: hay que recortarlo.
**Última actualización:** 19-oct-2026

Esta carpeta guarda lo que decidimos, lo que investigamos y lo que verificamos, para no
reconstruirlo de memoria. Cada documento distingue entre **medido** (lo corrimos),
**documentado** (lo dice una fuente) y **propuesto** (idea sin implementar).

| Documento | Contenido |
| --- | --- |
| [decisiones.md](decisiones.md) | Qué decidimos y por qué, con las alternativas descartadas |
| [datos.md](datos.md) | Fuentes, limpieza, y qué permiten y qué no permiten los datos |
| [fuentes-mcp-api-cli.md](fuentes-mcp-api-cli.md) | Investigación para la sección MCP vs API vs CLI |
| [ponente.md](ponente.md) | Bio de Dante para la presentación, con fuentes y datos por confirmar |
| [demo-mapa.md](demo-mapa.md) | Idea del mapa de afluencia para cerrar la demo |
| [verificacion.md](verificacion.md) | Qué se ejecutó, con qué comando y qué resultado dio |
| [presentacion.md](presentacion.md) | Dónde está la presentación, cómo se reconstruye, agenda de 40 minutos y pendientes |
| [storytelling.md](storytelling.md) | Buenas prácticas investigadas (Duarte, Alley, Mayer, Carpentries) y cómo se aplicaron |

## Estado del repositorio

| Ruta | Qué es | Estado |
| --- | --- | --- |
| `preparar.py` | Construye `datos/cdmx.sqlite` desde los CSV del repo; `--descargar` los vuelve a bajar | Listo |
| `datos/*_crudo.csv` | Copia cruda de las fuentes (1.7 MB) para trabajar sin internet | Listo |
| `pasos/01_hola.py` … `04_final.py` | Puntos de control del servidor; cada uno corre por HTTP | Listos |
| `servidor.py` | Copia de trabajo del participante; empieza igual que el paso 1 | Listo |
| `verificar.py` | Revisa el entorno y que un servidor cumpla el contrato de un paso | Listo |
| `evaluar.py` + `evals/casos.json` | 10 preguntas reales: ¿Claude elige la tool y los argumentos correctos? | Listo |
| `.mcp.json` | Conecta Claude Code al servidor en `http://127.0.0.1:8765/mcp` | Listo |
| `mapa/index.html` | Mapa de afluencia del Metro con slider de mes; los datos los genera `preparar.py` | Listo |
| `presentacion/construir.py` | Genera la presentación (versión 12: 29 láminas presentadas en 40 min, una oculta y tres apéndices) y la sube a Google Slides con `gws` | Listo, en revisión de Dante |
| `README.md` (raíz) | Guía para participantes: requisitos, dos terminales, los cuatro pasos, evaluación, mapa, Claude Desktop y problemas comunes | Listo |
| `CLAUDE.md` | Instrucciones para que Claude Code guíe paso a paso (la lámina 20 lo promete) | Listo, probado con `claude -p "guíame paso a paso"` |

Repositorio: https://github.com/danteese/claude-mcp-ibero-2026 (privado por ahora).

## Entorno de desarrollo (tmux)

Durante la preparación, el servidor corre en la sesión de tmux `taller-mcp`:

```sh
uv run preparar.py                                        # una vez; sin red
tmux new-session -d -s taller-mcp "uv run pasos/04_final.py"
tmux attach -t taller-mcp                                 # ver logs; salir con Ctrl-b d
tmux kill-session -t taller-mcp                           # apagarlo

uv run verificar.py 4 --archivo pasos/04_final.py         # contrato del paso, sin gastar cuota
uv run evaluar.py                                         # 10 casos con claude -p; gasta cuota
```

El taller **no** requiere tmux: los participantes usan dos pestañas de terminal (una con
`uv run servidor.py` y otra con `claude`).

## Pendientes

- [x] Agenda de 40 minutos y presentación en Google Slides (`presentacion.md`).
- [x] `README.md` para participantes y `CLAUDE.md` para que Claude Code los guíe paso a paso.
- [x] Subir el repo y poner su URL en las láminas 10, 20, 29 y 33.
- [ ] Hacer público el repo antes del evento. Antes, revisar si `docs/` debe incluir las notas internas de Spot2 (`ponente.md`, D17).
- [ ] Lámina 9 (Spot2): Dante quitó el número en Slides; la tarjeta dice «personas de Spot2 los usan…» sin cifra.
- [ ] Ensayar la presentación con cronómetro.
- [x] Cierre decidido: mapa del Metro por mes, 5 minutos (`demo-mapa.md`, decisión D12).
- [ ] Probar el ejercicio del mapa en Claude Code interactivo y grabar un respaldo.
- [ ] Confirmar los datos marcados "por confirmar" en `ponente.md`.
- [ ] Probar Claude Desktop de punta a punta. Probado: `fastmcp install claude-desktop` genera la configuración y el servidor responde por stdio; falta abrirlo en la app.
- [ ] Probar si Claude Code se reconecta solo al reiniciar el servidor HTTP (no probado).
- [ ] Revisar la licencia del feed GBFS de Ecobici antes de presentarlo como dato abierto.
- [ ] Confirmar con Ricardo y Andrés qué cubren los demás speakers (pendiente del temario v6).
- [ ] La semana previa: revisar el estado del spec MCP, FastMCP y Claude Code.

## Trabajo a futuro

- [ ] Calificar las 8 tools con TDQS de Glama (github.com/glama-ai/tool-definition-quality-score) y comparar con
  `evaluar.py`: TDQS mide la definición; la evaluación, si Claude elige bien.
- [ ] Skill del servidor del Metro servida por MCP con `SkillsDirectoryProvider` (D20), como extensión opcional
  fuera de `.claude/skills/` para no alterar `evaluar.py`.
