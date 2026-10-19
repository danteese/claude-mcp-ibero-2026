# Fuentes: MCP vs API vs CLI

Investigación para la sección "Diferencias de ejecución" del temario. Consultado el
17-oct-2026 con Parallel, Exa y la documentación oficial.

**Lectura** indica qué tanto revisamos cada fuente: *completa* (leímos la página), *extracto*
(solo el fragmento del buscador) o *docs* (documentación consultada por tema).

## Fuentes primarias (oficiales)

| Fuente | Fecha | Lectura | Qué aporta |
| --- | --- | --- | --- |
| [MCP spec 2026-07-28 · Architecture](https://modelcontextprotocol.io/specification/2026-07-28/architecture) | 2026-07-28 | extracto | Arquitectura host → client → server (un client por server). "MCP is a stateless protocol: every request is self-contained". Principios de diseño: servers fáciles de construir y componibles; **un server no puede leer toda la conversación ni "ver" a otros servers**; el host impone los límites de seguridad |
| [Blog MCP · The 2026-07-28 Specification](https://blog.modelcontextprotocol.io/posts/2026-07-28/) | 2026-07-28 | extracto | Núcleo stateless, Multi Round-Trip Requests, headers `Mcp-Method`/`Mcp-Name` para enrutar, listas cacheables, autorización reforzada, marco de extensiones. Se retiran `initialize`/`initialized` y `Mcp-Session-Id` |
| [Blog MCP · Release Candidate](https://blog.modelcontextprotocol.io/posts/2026-07-28-release-candidate) | 2026-05-21 | extracto | "Stateless protocol, stateful applications": el estado entre llamadas va en handles explícitos que se pasan como argumentos |
| [MCP spec · Key Changes](https://modelcontextprotocol.io/specification/2026-07-28/changelog.md) | 2026-07-28 | extracto | SEP-2567 (sin sesiones), SEP-2575 (sin handshake), SEP-2322 (`resultType: input_required`) |
| [SEP-2575: Make MCP Stateless](https://modelcontextprotocol.io/seps/2575-stateless-mcp) | — | extracto | Motivación: el handshake obligaba a sticky sessions detrás de un balanceador |
| [MCP docs · Architecture overview](https://modelcontextprotocol.io/docs/learn/architecture) | — | extracto | Las tres primitives (tools, resources, prompts) y cómo el host intercepta y enruta la llamada |
| [Anthropic · Code execution with MCP](https://www.anthropic.com/engineering/code-execution-with-mcp) | 2025-11-04 | extracto | Cargar todas las definiciones y resultados gasta contexto. En su ejemplo, presentar las tools como código bajó de 150,000 a 2,000 tokens (98.7%). Costo: requiere sandbox, límites y monitoreo |
| [Claude Code docs · MCP](https://code.claude.com/docs/en/mcp) | consultado 17-oct-2026 | docs | Tool search difiere las definiciones (solo carga nombres e instrucciones). Las descripciones se cortan a 4,096 caracteres (16,384 si se cargan por búsqueda). Salida: aviso a los 10k tokens, tope de 25k, y más de 50k caracteres se guarda en archivo. `anthropic/requiresUserInteraction`, `anthropic/alwaysLoad`, `anthropic/maxResultSizeChars`. Los `.mcp.json` de proyecto piden aprobación |
| [FastMCP docs](https://gofastmcp.com) | v4.1.0 | docs | Una misma instancia sirve las dos eras del protocolo; `ctx.elicit()` vs `InputRequiredResult`; anotaciones; `host_origin_protection` viene apagado por defecto |

## Fuentes secundarias (explicaciones y opinión)

| Fuente | Fecha | Lectura | Postura | Qué usar |
| --- | --- | --- | --- | --- |
| [Design Gurus · MCP vs API](https://designgurus.substack.com/p/mcp-vs-api-what-they-are-how-they) (Arslan Ahmad) | 2026-09-18 | completa (primeros 12k caracteres) | Explicativa | El consumo de APIs está **mediado por developers**: alguien lee la doc y escribe el código en tiempo de build. MCP sirve cuando el consumidor es un modelo que decide en runtime. "Different layers, not competitors". REST, GraphQL y gRPC explicados de forma breve. **Ojo:** describe el handshake `initialize` y el sampling iniciado por el server; el primero se retiró en 2026-07-28 y el segundo no está en la API de servidor de FastMCP 4 |
| [Cloudflare · Code Mode MCP](https://blog.cloudflare.com/code-mode-mcp/) | feb-2026 | extracto (vía Firecrawl) | Fabricante | Exponer los 2,500+ endpoints de su API como tools costaría ~1.17 M tokens; con dos tools (`search`, `execute`) baja a ~1,000. Las cifras son suyas, no las medimos |
| [Cloudflare · The next generation of MCP](https://blog.cloudflare.com/mcp-v2) | ago-2026 | extracto | Fabricante | Por qué el diseño stateful heredado de stdio estorbaba en remoto; elicitation sin stream abierto |
| [AAIF · Are MCP and CLIs Competing?](https://aaif.io/blog/are-mcp-and-clis-competing) | — | extracto | Matizada | "Intent is what MCP actually adds". La salida del modelo cuesta más que la entrada; el modo código y el shell son la misma idea con distinta sintaxis |
| [Firecrawl · MCP vs CLI](https://www.firecrawl.dev/blog/mcp-vs-cli) | 2026-04-10 | extracto | Comparativa | Resume los números de Anthropic y Cloudflare |
| [MCPBundles · MCP vs CLI is the wrong debate](https://www.mcpbundles.com/blog/mcp-vs-cli-the-wrong-debate) | 2026-03-31 | extracto | Fabricante, pro-MCP | "CLI works fine when YOU are the orchestrator". MCP para acceso autenticado con schema; el código, para componer |
| [Jannik Reinhard · CLI tools vs MCP](https://jannikreinhard.com/why-cli-tools-are-beating-mcp-for-ai-agents/) | 2026-02-22 | extracto | Pro-CLI | "MCP is a context hog"; `--output json` y `--help` como documentación justo a tiempo |
| [AWS Builder Center · ditch the MCP overhead](https://builder.aws.com/content/3AXTTz6IRsrQPbzMamElxly8F0J/agent-skills-and-cli-tools-ditch-the-mcp-overhead) | 2026-03-10 | extracto | Pro-skills/CLI | Publicación de la comunidad de AWS (la autora trabaja en AWS); no es guía oficial |
| [Microsoft Tech Community · MCP vs mcp-cli](https://techcommunity.microsoft.com/blog/azuredevcommunityblog/mcp-vs-mcp-cli-dynamic-tool-discovery-for-token-efficient-ai-agents/4494272) | 2026-02-26 | extracto | Comunidad | Descubrimiento dinámico frente a cargar todo al inicio |
| [Mac Install Guide · MCP or Skills or CLI?](https://mac.install.guide/mcp/vs-skills) | 2026-10-10 | extracto | Práctica | Un server limita lo que puede hacer el agente; "MCP connects Claude to data, skills teach Claude what to do with it" (lo atribuye a Anthropic) |
| [DevOps Toolkit · MCP vs CLI (video)](https://www.youtube.com/watch?v=TuIZoFyBKIM) | 2026-04-27 | extracto | Pro-CLI | Demo con Claude Code y Kubernetes |
| [MCP vs API: Why traditional APIs are failing AI agents (video)](https://www.youtube.com/watch?v=185XGEMefgc) (Smitha Kolan) | 2026-07-01 | extracto | Pro-MCP | "MCP on top of APIs: the new middleware" |
| [Hacker News · When does MCP make sense vs CLI?](https://news.ycombinator.com/item?id=47208398) | — | extracto | Comunidad | "MCP makes sense for discovery and contextual tool selection. CLIs make sense when the human already knows which tool to use" |

## Segunda ronda (17-oct-2026, con Parallel): incentivos y problemas

Dante cuestionó la versión anterior («todas las puede leer la IA; ¿cuál es el incentivo de tener un MCP?»).
Tenía razón: la síntesis comparaba quién lee el contrato y no decía cuándo conviene cada opción ni qué
cuesta MCP.

| Fuente | Fecha | Lectura | Qué aporta |
| --- | --- | --- | --- |
| [Mario Zechner · MCP vs CLI: Benchmarking Tools for Coding Agents](https://mariozechner.at/posts/2025-08-15-mcp-vs-cli/) | 2025-08-15 | extracto | 120 corridas: «MCP vs CLI truly is a wash»; las dos versiones de su tool, 100% de éxito. Lo que importa es el diseño de la tool. «MCP servers are also the only option for LLM clients without a built-in shell tool» |
| [Scalekit · mcp-vs-cli-benchmark](https://github.com/scalekit-inc/mcp-vs-cli-benchmark) | 2026 | extracto | 5 tareas de GitHub con Claude Sonnet 4: 100% de éxito en ambos; MCP usó de 1.3× a 80× más tokens (por el schema en cada request), pero menos llamadas y menor latencia en datos estructurados. Una sola corrida publicada |
| [Armin Ronacher · Tools: Code Is All You Need](https://lucumr.pocoo.org/2025/7/3/tools/) | 2025-07-03 | extracto | Crítica: MCP «isn't truly composable» (la composición pasa por inferencia) y «demands too much context» |
| [Addy Osmani · MCP deep dive](https://addyosmani.com/agents/16-mcp-deep-dive) | — | extracto | Tabla de decisión: CLI para trabajo local y herramientas conocidas; MCP para multiusuario, permisos por usuario y auditoría |
| [CircleCI · MCP vs CLI](https://circleci.com/blog/mcp-vs-cli/) | 2026-03-11 | extracto | CLI en el *inner loop* (local, rápido); MCP en el *outer loop* (sistemas externos, auth, auditoría). Cargar todo el schema al conectar es una decisión de implementación, no del protocolo |
| [Simon Willison sobre «too many MCPs»](https://simonwillison.net/2025/Aug/22/too-many-mcps/) (citando a Geoffrey Huntley) | 2025-08-22 | extracto vía Outpost | El MCP de GitHub define 93 tools y ocupa unos 55,000 tokens |
| [Anthropic · Donating MCP to the Agentic AI Foundation](https://www.anthropic.com/news/donating-the-model-context-protocol-and-establishing-of-the-agentic-ai-foundation) | 2025-12-09 | extracto | MCP pasa a la AAIF (Linux Foundation), cofundada por Anthropic, Block y OpenAI, con Google, Microsoft, AWS, Cloudflare y Bloomberg. Más de 10,000 servidores públicos; adoptado por ChatGPT, Cursor, Gemini, Copilot y VS Code |
| [MCP spec 2026-07-28 · Security Best Practices](https://modelcontextprotocol.io/specification/2026-07-28/basic/security_best_practices) | 2026-07-28 | extracto | Ataques documentados: confused deputy, token passthrough (prohibido), SSRF, secuestro de handles, servidor local comprometido, scopes excesivos |
| [OWASP · MCP Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/MCP_Security_Cheat_Sheet.html) y [Microsoft · indirect prompt injection en MCP](https://developer.microsoft.com/blog/protecting-against-indirect-injection-attacks-mcp/) | 2025-04 / — | extracto | Tool poisoning (instrucciones ocultas en descripciones) y prompt injection por resultados de tools |
| [Anthropic · Writing effective tools for agents](https://www.anthropic.com/engineering/writing-tools-for-agents) | — | extracto | Diseñar tools para agentes, no como APIs para developers; consolidar, namespacing, respuestas eficientes en tokens, evaluar |

### Síntesis (versión 5 de la presentación, láminas 9 y 10)

**La IA puede usar las tres.** Con tools bien diseñadas, CLI y MCP empatan en éxito; MCP gasta más
contexto. La pregunta no es cuál es mejor, sino cuál conviene:

| Situación | Conviene |
| --- | --- |
| Trabajas en tu máquina con una herramienta que el modelo ya conoce (git, gh, kubectl) | CLI |
| Código que siempre hace lo mismo: no decide un modelo | API |
| El modelo decide en runtime, para varios usuarios, con permisos y auditoría | MCP |
| La persona está en Claude.ai, ChatGPT o un agente en la nube, sin tu terminal | MCP remoto |
| Muchos pasos encadenados sobre muchos datos | código que llama tus tools («code execution with MCP») |

**Lo que MCP te da:** funciona donde no hay una terminal tuya; la autorización por usuario (OAuth 2.1)
está en el estándar; el host ve cada tool por nombre y puede pedir aprobación y registrar llamadas; el
dueño del sistema define la superficie; es un estándar neutral con adopción amplia.

**Lo que cuesta:** contexto (definiciones en cada request); composición (cada paso pasa por inferencia);
seguridad (tool poisoning, prompt injection por resultados, token passthrough; la spec pide tratar las
anotaciones como no confiables); operación (otro servicio que desplegar y probar con cada host).

## De qué se compone MCP (spec 2026-07-28, lámina 12)

Fuentes: [basic](https://modelcontextprotocol.io/specification/2026-07-28/basic), [changelog](https://modelcontextprotocol.io/specification/2026-07-28/changelog),
[client/sampling](https://modelcontextprotocol.io/specification/2026-07-28/client/sampling), [client/roots](https://modelcontextprotocol.io/specification/2026-07-28/client/roots),
[extensions](https://modelcontextprotocol.io/docs/extensions/overview), [server/tools](https://modelcontextprotocol.io/specification/2026-07-28/server/tools). Lectura: extractos de las páginas oficiales.

| Componente | Qué es | Estado |
| --- | --- | --- |
| Protocolo base | Mensajes JSON-RPC 2.0; sin estado: cada petición lleva versión y capacidades en `_meta`; `resultType` en cada resultado | **Obligatorio** |
| Versionado y compatibilidad | Negociación de versión y de extensiones; `server/discover` (los servidores MUST implementarlo) | **Obligatorio** |
| Patrones de mensaje | Petición/respuesta, *multi round-trip requests* (MRTR, `input_required`), suscripción y notificación (`subscriptions/listen`) | **Obligatorio** |
| Transportes | stdio (el cliente lanza el proceso) y Streamable HTTP (un endpoint, POST) | Se elige uno |
| Autorización | OAuth 2.1 para transportes HTTP; Protected Resource Metadata (RFC 9728), CIMD | Opcional |
| Funciones del servidor | Tools, resources y prompts | Opcional |
| Funciones del cliente | Elicitation. **Sampling y roots quedaron obsoletos en 2026-07-28 (SEP-2577)**: siguen al menos 12 meses, no se deben adoptar | Opcional |
| Utilidades | Progreso, cancelación, logging (nivel por petición), autocompletado, paginación | Opcional |
| Extensiones | Tasks (trabajos largos), MCP Apps (UI en la conversación), autorización empresarial y client credentials | Opt-in, se negocian |

Cambios de 2026-07-28 que importan para el taller: sin `initialize` ni `Mcp-Session-Id`; sin `ping`
ni `logging/setLevel`; las peticiones del servidor al cliente (elicitation) viajan con MRTR; Tasks salió
del núcleo a una extensión.

Campos de cada pieza (lámina 13): una tool se define con `name`, `description` e `inputSchema`
(opcionales: `title`, `outputSchema`, `annotations`, `icons`); un resource con `uri` y `name`
(opcionales: `title`, `description`, `mimeType`); un prompt con `name` (opcionales: `title`,
`description`, `arguments`).

### Lo que la versión anterior decía mal

- «La diferencia no es el transporte: es quién lee el contrato»: cierto en parte, pero no respondía por
  qué conviene MCP si la IA puede leer la documentación de una API o usar una CLI.
- La fuente de Design Gurus describe el handshake `initialize` y el sampling iniciado por el servidor:
  el primero ya no existe en 2026-07-28 y el segundo es obsoleto. Ya no se cita en las láminas.

## Datos con fecha que conviene citar con cuidado

- "Close to half-a-billion downloads a month" de los SDK Tier 1: lo afirma el blog de MCP
  (jul-2026); no lo verificamos.
- 98.7% y 99.9% de ahorro de tokens: son casos de Anthropic y Cloudflare, no promedios.

## FastMCP, FastAPI y transportes (lámina 15)

Consultado el 17-oct-2026 con Context7 (documentación de FastMCP) y Parallel.

| Fuente | Qué aporta |
| --- | --- |
| [FastMCP · inicio](https://gofastmcp.com) | «FastMCP created the high-level Python API incorporated into the official MCP Python SDK in 2024»; el proyecto independiente se mantiene aparte |
| [FastMCP · Upgrading from MCP SDK v2](https://gofastmcp.com/getting-started/upgrading/from-mcp-sdk-v2) | `MCPServer` es el sucesor de FastMCP 1.0 dentro del SDK v2; FastMCP se construye sobre ese SDK y agrega composición, middleware, proxies, autenticación, cliente y pruebas |
| [FastMCP · Running your server](https://gofastmcp.com/deployment/running-server) | stdio para uso local (lo que esperan Claude Desktop y las herramientas de línea de comandos); HTTP para red, varios clientes o despliegue remoto; SSE solo por compatibilidad |
| [FastMCP · http_app](https://gofastmcp.com/python-sdk/fastmcp-server-mixins-transport) | `http_app()` crea una aplicación Starlette (ASGI) que se sirve con Uvicorn |
| [FastMCP · FastAPI integration](https://gofastmcp.com/integrations/fastapi) | `FastMCP.from_fastapi(app)` convierte endpoints en tools; `app.mount("/mcp", mcp.http_app())` monta el servidor en FastAPI. Advertencia: «LLMs achieve significantly better performance with well-designed and curated MCP servers than with auto-converted OpenAPI servers»; recomiendan la conversión para prototipar |
| [FastAPI](https://fastapi.tiangolo.com/) | «A modern, fast (high-performance), web framework for building APIs with Python based on standard Python type hints», sobre Starlette y Pydantic |
| [MCP spec 2026-07-28 · Transports](https://modelcontextprotocol.io/specification/2026-07-28/basic/transports) | Dos transportes estándar: stdio (subproceso que lanza el cliente) y Streamable HTTP (un endpoint, POST) |

## Skills y MCP (lámina 16)

Consultado el 19-oct-2026 con Parallel y Context7 (documentación de FastMCP).

| Fuente | Qué aporta |
| --- | --- |
| [Agent Skills · especificación](https://agentskills.io/specification) | Una skill es una carpeta con `SKILL.md` (frontmatter `name` y `description`, obligatorios) y opcionalmente `scripts/`, `references/`, `assets/`. Carga progresiva: al iniciar sólo nombre y descripción (~50-100 tokens por skill); el cuerpo, cuando la tarea coincide |
| [Anthropic · Equipping agents… with Agent Skills](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills) (16-oct-2025) | Skills como conocimiento procedimental; el 18-dic-2025 se publicaron como estándar abierto |
| [Claude · Skills explained](https://claude.com/blog/skills-explained) (5-mar-2026) | «MCP connects Claude to data; Skills teach Claude what to do with that data… Use both together» |
| [Claude Code · Plugins](https://code.claude.com/docs/en/plugins/overview) | Un plugin junta `.claude-plugin/plugin.json`, `skills/`, `agents/`, `hooks/hooks.json` y `.mcp.json`; «Plugins are the packaging layer» |
| [OpenAI · Plugins, Skills](https://developers.openai.com/plugins/concepts/skills) | «An MCP server provides live information and controlled actions. A skill provides the workflow around those tools: when to call them, in what order, how to handle incomplete results, and what the final output should contain» (ChatGPT y Codex) |
| [Gemini CLI · extensiones](https://github.com/google-gemini/gemini-cli/blob/main/docs/extensions/writing-extensions.md) | `gemini-extension.json` con `mcpServers`, archivo de contexto y skills; p. ej., la extensión oficial de MongoDB es «MCP Server + Skills» |
| [MCP · SEP-2640 Skills Extension](https://modelcontextprotocol.io/seps/2640-skills-extension) | Estado **Final**. Skills servidas como recursos (`skill://<skill>/<archivo>`), con `skills/list` y `skills/get`; escrita contra 2026-07-28 |
| [FastMCP · Skills provider](https://gofastmcp.com/servers/providers/skills) | `SkillsDirectoryProvider` expone carpetas de skills como recursos `skill://` (desde FastMCP 3.0) |

## Diagrama oficial y TDQS (19-oct-2026)

| Fuente | Qué aporta |
| --- | --- |
| [MCP · What is MCP? (docs 2026-07-28)](https://modelcontextprotocol.io/docs/2026-07-28/getting-started/intro) | «MCP is an open-source standard for connecting AI applications to external systems»; la analogía del USB-C; el diagrama aplicaciones de IA ↔ protocolo estándar ↔ fuentes de datos y herramientas, con flujo bidireccional |
| [Glama · Tool Definition Quality Score](https://github.com/glama-ai/tool-definition-quality-score) | Marco abierto para calificar qué tan bien comunica una tool MCP al agente. Seis dimensiones de 1 a 5: propósito (25 %), cuándo usarla (20 %), transparencia del comportamiento (20 %), semántica de parámetros (15 %), concisión (10 %), completitud (10 %). Nota 1.0-5.0 y nivel A-F; sólo la rúbrica usa un LLM, el resto es determinista. Glama lo aplica a todo su registro |

## Casos del cierre (lámina 27, 19-oct-2026)

| Caso | Fuente | Qué se verificó |
| --- | --- | --- |
| Conteo de servidores | [MCP Toplist](https://mcptoplist.com/) | 142,221 servidores MCP activos, actualizado el 15-oct-2026 (Official Registry, Glama, Smithery, mcp.so, PulseMCP) |
| Blender | [ahujasid/blender-mcp](https://github.com/ahujasid/blender-mcp) | 22,690 estrellas; complemento de Blender + servidor local; genera assets 3D (Hyper3D) |
| Blender → impresora 3D | [MCP · What is MCP?](https://modelcontextprotocol.io/docs/2026-07-28/getting-started/intro); [mcp-3D-printer-server](https://github.com/DMontgomery40/mcp-3D-printer-server) | «AI models can create 3D designs on Blender and print them out using a 3D printer»; OctoPrint, Klipper, Bambu Lab, Prusa, Creality, con puente opcional a Blender |
| Ableton Live | [ahujasid/ableton-mcp](https://github.com/ahujasid/ableton-mcp) | Crea pistas y clips y arma canciones completas (intro, buildup, drop) en Arrangement View |
| Figma | [Figma · remote server](https://developers.figma.com/docs/figma-mcp-server/remote-server-installation/) | Servidor remoto oficial (`mcp.figma.com/mcp`); lee contexto de diseño y escribe en el lienzo |
| Home Assistant | [Home Assistant · MCP Server](https://www.home-assistant.io/integrations/mcp_server/) | Integración oficial: ChatGPT o Claude controlan dispositivos y ven el estado de la casa |
| Robots | [robotmcp/ros-mcp-server](https://github.com/robotmcp/ros-mcp-server) | Conecta Claude o GPT con robots vía ROS |
| Chrome DevTools | [ChromeDevTools/chrome-devtools-mcp](https://github.com/ChromeDevTools/chrome-devtools-mcp) | De Google; traces de rendimiento, red, consola y automatización con Puppeteer |
| Mercado Pago | [Mercado Pago MCP Server](https://www.mercadopago.com.mx/developers/es/docs/mcp-server/overview) | Remoto oficial (`mcp.mercadopago.com`): `search-documentation`, generación de código de checkout, aplicaciones y credenciales (OAuth), webhooks, usuarios de prueba, `quality_evaluation` |
| Mercado Libre | [mercadolibre/mercadolibre-mcp-server](https://github.com/mercadolibre/mercadolibre-mcp-server) | Remoto oficial (`mcp.mercadolibre.com/mcp`) con token de la aplicación |

## Buenas prácticas para tools (lámina 29, 19-oct-2026)

Consultado con Parallel (búsqueda y lectura) y DeepWiki (`modelcontextprotocol/modelcontextprotocol`).

| Fuente | Qué aporta |
| --- | --- |
| [Anthropic · Writing effective tools for agents](https://www.anthropic.com/engineering/writing-tools-for-agents) | Elegir qué tools construir, namespacing, devolver contexto útil, eficiencia de tokens, prompt-engineering de descripciones. Evaluar con tareas reales; medir acierto, tiempo, llamadas, tokens y errores; leer transcripciones; dejar que Claude refactorice las tools; validar con un set aparte |
| [Anthropic · Demystifying evals for AI agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents) (9-ene-2026) | Calificadores por código (incluye verificar tools y parámetros llamados) y por modelo (rúbricas) |
| [Phil Schmid · MCP best practices](https://www.philschmid.de/mcp-best-practices) (21-ene-2026) | «MCP is a User Interface for Agents»: resultados, no operaciones; argumentos planos; instrucciones y errores son contexto; 5-15 tools por servidor; nombres `{servicio}_{acción}_{recurso}`; paginar |
| [OpenAI · Optimize metadata](https://developers.openai.com/apps-sdk/guides/optimize-metadata) | Golden prompt set (directos, indirectos, negativos) con el comportamiento esperado; descripción que empiece con «Use this when…» y diga los casos excluidos; documentar parámetros con ejemplos |
| [MCP spec 2026-07-28 · Tools](https://modelcontextprotocol.io/specification/2026-07-28/server/tools) | Nombres de 1 a 128 caracteres, `A-Z a-z 0-9 _ - .`, únicos en el servidor (la página de SEP-986 conserva la propuesta original de 64); anotaciones no confiables; errores de ejecución con `isError` para que el modelo se corrija |
| [Glama · TDQS](https://github.com/glama-ai/tool-definition-quality-score) | Seis criterios con peso; nota de 1 a 5 y nivel A-F (ver «Diagrama oficial y TDQS») |
