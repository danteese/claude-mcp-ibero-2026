# MCP: conceptos, primitives y diseño de tools

**Evento:** Claude for AI Engineering · CDMX · Universidad Iberoamericana
**Duración:** 55 min de contenido + 5 min de colchón
**Hilo conductor:** un LLM es una función de texto a texto. Todo lo demás — saber, actuar, verificar — hay que dárselo. La charla recorre cómo se le da, hasta llegar a MCP, y luego cómo diseñarlo bien.

---

## 0. Apertura (1 min)

> Escribir un MCP server es fácil. Que el modelo elija la tool correcta, con los parámetros correctos, no lo es. Vamos a llegar ahí, pero empezando por una pregunta anterior: por qué un modelo necesita herramientas.

---

## 1. Por qué un LLM necesita herramientas (8 min)

### 1.1 Qué no puede hacer un modelo por sí solo

Un LLM recibe texto y produce texto. Eso es todo. De ahí salen cinco límites concretos:

| Límite | Qué significa |
|---|---|
| **Conocimiento congelado** | Sabe hasta su fecha de corte. No sabe qué pasó ayer |
| **Sin acceso a lo privado** | Tu inventario, tu CRM, tus tickets nunca estuvieron en el entrenamiento |
| **Sin efectos en el mundo** | Genera texto. No manda correos, no escribe en una base de datos, no cobra |
| **Cómputo no determinista** | Aritmética, fechas, agregaciones: puede acertar, pero no garantiza |
| **No puede verificar** | No sabe si lo que dijo es cierto. Necesita una fuente externa |

Los primeros dos son problemas de **saber**. Los siguientes tres son problemas de **hacer**.

### 1.2 Cómo se han ido resolviendo

Capacidades que se acumulan, no generaciones que se reemplazan. Cada una sigue siendo la respuesta correcta para algo.

**a) Meter todo en el prompt.**
Funciona a escala pequeña. Choca con el contexto finito, y los datos quedan viejos en cuanto los pegas.

**b) Recuperación (RAG).**
Resuelve el problema de *saber*: traer el fragmento correcto en el momento correcto. No resuelve el de *hacer* — el modelo sigue sin poder actuar.

**c) Llamadas a tools (function calling).**
El modelo emite una petición estructurada, tu código la ejecuta y le devuelve el resultado. Aquí aparece por primera vez la capacidad de actuar. Límite: las tools están definidas en tu aplicación, en tiempo de build.

**d) Acceso a una VM o shell.**
Máxima generalidad: el modelo compone CLIs que ya conoce por entrenamiento, encadena con pipes, hace cosas que nadie previó. Límites: es local, hereda todos los permisos del usuario, y la salida es texto sin estructura que alguien tiene que parsear.

**e) Tools dinámicas, descubiertas en runtime.**
El conjunto de capacidades deja de estar fijado en el código del agente. El usuario conecta servers y la superficie del agente cambia sin redesplegarlo.

### 1.3 El cambio conceptual del último peldaño

Con tools estáticas, quien construye el agente tiene que anticipar en tiempo de build todo lo que el agente podría necesitar.

Con tools dinámicas, las capacidades se **componen en runtime**. Pasas de una aplicación con features a un agente con capacidades componibles, y quien aporta cada capacidad es el dueño del sistema, no el dueño del agente.

Eso es lo que MCP estandariza.

### 1.4 Y aquí entra MCP

- **El problema que resuelve:** M clientes × N sistemas = integraciones que nadie mantiene. Un protocolo lo convierte en M+N.
- **Analogía:** MCP es a los agentes lo que HTTP es a las aplicaciones. No es una librería, es un contrato.
- **Arquitectura:** Host → Client → Server, en un diagrama.
- **Qué no resuelve:** no arregla un prompt malo, no arregla datos sucios, no reemplaza tu capa de autorización, no hace que el modelo entienda tu dominio.

### 1.5 El problema nuevo que crea

Si el conjunto de tools se compone en runtime, el modelo se enfrenta a herramientas que nadie diseñó juntas. Elegir bien entre 5 tools es fácil; entre 60 de seis servers distintos, no.

Ese es el tema del bloque 5.

---

## 2. Diferencias de ejecución: CLI, API REST, function calling y MCP (6 min)

Habiendo visto de dónde sale cada opción, la comparación directa:

| | **CLI** | **API REST** | **Function calling nativo** | **MCP** |
|---|---|---|---|---|
| **Quién decide invocar** | El humano (o el modelo generando texto) | Tu código | El modelo | El modelo (Tools), la app (Resources), el usuario (Prompts) |
| **Dónde vive el contrato** | `--help`, en prosa | OpenAPI, para developers | Schema JSON en tu código | Schema + descripción, para el modelo |
| **Descubrimiento** | El usuario lee la doc | Fuera de banda, en build time | Hardcodeado en tu app | En runtime, vía `tools/list` |
| **Entrada** | String sin validar | Validada por el server | Validada por schema | Validada por schema |
| **Salida** | Texto sin estructura | JSON estructurado | JSON estructurado | Estructurada + con hints de caché |
| **Errores** | Exit code + stderr | HTTP status | Lo que tú devuelvas | Lo que tú devuelvas, leído como instrucción |
| **Permisos** | Los del usuario, todo o nada | API key por aplicación | Los de tu backend | Por tool, con auth por request |
| **Portabilidad** | Solo esa máquina | Cualquier cliente que codifiques | Atada a tu app y a tu proveedor | Cualquier host que hable MCP |
| **Quién escribe la integración** | El usuario | El dueño del agente | El dueño del agente | **El dueño del sistema** |

### 2.1 MCP vs function calling

La confusión más común. No son competidores, son capas distintas:

- **Function calling** es el mecanismo: cómo un modelo emite una llamada estructurada. Vive en tu aplicación, con un proveedor.
- **MCP** es el protocolo: cómo esas capacidades se publican, se descubren y se consumen entre procesos distintos.

Un MCP server termina alimentando function calling. La diferencia es quién es dueño de la definición y quién la puede reutilizar.

### 2.2 La crítica de "esto es REST otra vez"

Va a salir. Es parcialmente cierta a nivel de transporte y no lo es a nivel de diseño: el contrato está escrito para un lector que infiere, no para uno que lee documentación. Ese cambio de lector es todo lo que sigue.

**Regla práctica:** Si tu server se ve como un `swagger.json` traducido, tienes una API con otro nombre.

### Slide de respaldo (para Q&A): CLI vs MCP

Hay quien argumenta que darle al modelo shell y buenos CLIs supera a escribir MCP servers. Tener la respuesta lista:

- **A favor del CLI:** el modelo ya conoce `git`, `curl`, `psql` por entrenamiento (cero tokens de definición); composición real vía pipes; no pagas definiciones en contexto hasta usarlas
- **A favor de MCP:** contrato estructurado en vez de parseo de texto; funciona contra sistemas remotos sin dar shell; permisos por capacidad; el host puede mostrar, aprobar y auditar; sirve para hosts que no son terminal
- **Conclusión:** para tooling local de developers el CLI compite de verdad. Para exponer un sistema interno a varios agentes y equipos, con permisos y auditoría, MCP es la respuesta

---

## 3. Las tres primitives y el modelo de control (8 min)

Tools, Resources y Prompts se declaran igual y se listan por el mismo protocolo, por eso se confunden. La propiedad que los separa es quién decide cuándo ocurre la acción.

| Primitive | Controlado por | Qué es | Cuándo elegirlo |
|---|---|---|---|
| **Tools** | El **modelo** | Funciones que ejecutan algo | El modelo debe poder actuar solo. Todo lo que tiene efecto: escribir, borrar, enviar, publicar |
| **Resources** | La **aplicación** | Datos read-only direccionables por URI | El host decide qué contexto inyectar: schemas, configuración, documentación |
| **Prompts** | El **usuario** | Plantillas de interacción reutilizables | El usuario elige explícitamente, típicamente vía slash commands |

**La pregunta de diseño, para cada capacidad que vas a exponer:**

> ¿Quién debería decidir cuándo esto ocurre — el modelo, la aplicación, o el usuario?

Esa pregunta determina la primitive. No hay una segunda regla.

### Consecuencias prácticas

La mayoría expone todo como Tools, porque es el camino de menor resistencia.

**Lo que se pierde sin Resources:**
- Control del usuario sobre qué datos entran al contexto (esto es compliance, no comodidad)
- Material de referencia grande disponible bajo demanda en vez de cargado siempre
- Datos sensibles con opt-in explícito antes de exponerse

**Lo que se pierde sin Prompts:**
- Workflows empaquetados: en vez de que cada usuario redescubra cómo encadenar tus 8 tools, entregas el camino correcto ya armado
- Es la primitive menos usada y la de mejor relación esfuerzo/impacto

**Un mismo dominio, las tres primitives:**

| Necesidad | Primitive | Por qué |
|---|---|---|
| Consultar el stock de un SKU | Tool | El modelo debe decidirlo a media conversación |
| El catálogo de categorías y su jerarquía | Resource | Contexto estable que la aplicación inyecta |
| "Auditar inventario del mes" | Prompt | El usuario lo dispara; empaqueta 5 pasos en un comando |

**Regla práctica:** Si el modelo decide, es una Tool. Si la aplicación decide, es un Resource. Si el usuario decide, es un Prompt.

---

## 4. Cómo se escribe un server (8 min) — hands-on

Una sola demo en vivo. El objetivo es ver dónde aterriza cada concepto del bloque anterior.

- Server mínimo con Python + FastMCP
- Un **tool** con type hints + docstring → el SDK genera el schema. Señalar que ese docstring es lo único que el modelo lee para decidir
- Un **resource** con su URI
- Un **prompt**, porque rara vez se muestran y toma 90 segundos
- Probarlo con el **MCP Inspector**
- Conectarlo a Claude Code y observar la selección de tools

```
escribir función → decorador → schema automático → Inspector → Claude lo ve
```

**Entregable:** salen sabiendo escribir las tres primitives, no solo tools.

**Nota de producción:** repo clonado, venv armado, terminal de respaldo con el server ya corriendo.

---

## 5. Diseño de tools (13 min)

Retoma el problema abierto en 1.5: el modelo elige entre tools que nadie diseñó juntas.

### 5.1 Qué lee el modelo

El modelo no lee tu código ni tu README. Lee **nombre + descripción + schema**. Todo el trabajo de diseño ocurre en esos tres campos.

### 5.2 Agrupar por intención, no por endpoints

Tu API tiene 40 endpoints porque así se construyó. Tus tools deben corresponder a las intenciones que un humano expresaría. No son el mismo conjunto.

- Regla práctica: 5-15 tools por server
- Tools genéricas (`query_db(sql)`) trasladan el trabajo de diseño al modelo
- Tools que se solapan compiten entre sí y la elección se vuelve inconsistente

### 5.3 Ejemplos mal → bien

Tres pares, de un dominio reconocible (inventario, facturación/CFDI, CRM):

| Mal | Bien | Por qué |
|---|---|---|
| `query_db(sql: str)` | `buscar_pedidos(cliente_id, estatus, desde, hasta)` | El dominio vive en el schema |
| `get_data` / `fetch_info` / `retrieve` | nombres por intención, sin solapamiento | Tres tools vagas compiten entre sí |
| Devolver 400 filas | 10 filas + `total: 4823` + cómo pedir más | El contexto es finito y caro |

### 5.4 Schemas estrictos y side-effects explícitos

- Enums, límites, `additionalProperties: false`
- El modelo no puede inferir qué es reversible: dilo en la descripción. "Esto escribe", "esto borra permanentemente", "esto tiene costo", "esto envía correo a un cliente real"

### 5.5 El diseño de errores

Lo que devuelves cuando falla funciona como instrucción para el modelo:

```python
# mal: reintenta en ciclo
{"error": "invalid input"}

# bien: se corrige en un turno
{"error": "fecha debe ser YYYY-MM-DD, recibí '15 de marzo'"}
```

### 5.6 El contexto como presupuesto

Cada definición de tool vive en el contexto de cada request. 40 tools son tokens en cada llamada, en cada conversación. Conecta con el bloque de context engineering del evento.

### 5.7 Composición entre servers

Consecuencia directa de las tools dinámicas: el usuario va a conectar tu server junto con otros cinco.

- Los nombres genéricos colisionan a nivel ecosistema (`search`, `create`, `list`)
- Un prefijo de dominio evita ambigüedad
- Tu descripción compite por atención con tools que nunca viste

### 5.8 Cómo validar el diseño

Evaluación corta, sin framework:

1. Escribe 10 prompts realistas de usuario
2. Córrelos contra tu server
3. Cuenta cuántas veces eligió la tool correcta, con los parámetros correctos
4. Itera **descripción y schema**, no el system prompt
5. Repite hasta que deje de fallar

Enlaza con el bloque de evals del evento.

**Regla práctica:** Si el agente llama la tool incorrecta o con parámetros malos, el problema casi siempre está en la descripción o en el schema, no en el modelo.

---

## 6. Dónde vive el estado (4 min)

- El protocolo es stateless: cada request es autosuficiente y puede atenderse en cualquier instancia
- Contexto: en el spec `2026-07-28` se retiraron el handshake `initialize` y el header `Mcp-Session-Id`
- El estado no desapareció, se volvió explícito. Emites un `handle` desde una tool y el modelo lo pasa de vuelta como argumento
- Ventaja de diseño, no solo de infraestructura: el modelo ve el handle y puede hilarlo entre tools. El estado en el transporte era invisible para el actor que tenía que razonar sobre él
- Si necesitas intervención del usuario a media llamada (confirmar algo costoso o destructivo), existe un mecanismo estándar

**Regla práctica:** Diseña cada tool para que se ejecute de forma independiente. Si hay continuidad, hazla visible como parámetro.

---

## 7. Seguridad al conectar sistemas internos (5 min)

- **Least privilege por tool, no por server.** Un server con credencial de administrador y 12 tools tiene 12 caminos de escalación
- **Validar siempre los inputs**, aunque el schema ya los declare
- **Prompt injection vía resultados de tools:** lo que devuelve tu sistema interno entra al contexto del modelo. Un ticket de soporte con instrucciones adentro es un vector
- **Tool poisoning:** la descripción que aprobaste puede no ser la que corre después
- **Confirmación del usuario** para acciones destructivas o costosas
- **Sandboxing** cuando el server toca datos reales

**Checklist:**

- [ ] ¿Cada tool tiene el permiso mínimo, o comparten credencial?
- [ ] ¿Valido cada input aunque el schema ya lo declare?
- [ ] ¿Las acciones destructivas piden confirmación?
- [ ] ¿Trato el output de sistemas internos como texto no confiable?
- [ ] ¿Sé qué tool se llamó, por quién y con qué parámetros?
- [ ] ¿Qué pasa si el server se cae a la mitad de una operación?

---

## 8. Cierre (2 min)

1. Escribe un server con las tres primitives, no solo tools
2. Pruébalo con el Inspector
3. Conéctalo a Claude Code / Claude Desktop
4. Corre la evaluación de 10 prompts
5. Itera descripciones y schemas hasta que deje de fallar

**Starter** (repo o gist) orientado a conectar un sistema interno simple. QR en el último slide.

---

## Presupuesto de tiempo

| Bloque | Min |
|---|---|
| 0. Apertura | 1 |
| 1. Por qué un LLM necesita herramientas | 8 |
| 2. Diferencias de ejecución | 6 |
| 3. Las tres primitives y el modelo de control | 8 |
| 4. Cómo se escribe un server | 8 |
| 5. Diseño de tools | 13 |
| 6. Dónde vive el estado | 4 |
| 7. Seguridad | 5 |
| 8. Cierre | 2 |
| **Total contenido** | **55** |
| Colchón | 5 |

El colchón está ajustado. Recortes disponibles, en orden de cuál duele menos:

1. Bloque 1.2 → dejar la escalera en un solo slide narrado, sin desglosar cada peldaño: **−3 min**
2. Bloque 4 → mostrar solo tool y prompt, omitir el resource: **−2 min**
3. Bloque 6 → fusionarlo como cierre del bloque 5: **−2 min**

---

## Notas de diseño

- **El bloque 1 es el nuevo hilo.** Arranca en la limitación del modelo, no en la premisa de que MCP es necesario. La audiencia llega a MCP por deducción, no por anuncio
- **1.2 no es una narrativa de progreso.** Cada capacidad sigue siendo la respuesta correcta para algo: RAG no muere porque existan tools, y una VM con CLIs sigue ganando en varios casos. Decirlo explícitamente evita que suene a pitch
- **1.5 abre el problema que cierra el bloque 5.** Las tools dinámicas resuelven la rigidez y crean el problema de selección. Ese arco sostiene la charla
- El bloque 3 determina las decisiones de los bloques 5 y 6
- Una sola demo en vivo (bloque 4), que aterriza el bloque 3
- Statelessness se presenta como consecuencia de diseño, en 4 minutos

### Pendientes

- Elegir el dominio de los ejemplos mal → bien. Un sistema interno real anonimizado funciona mejor que un ejemplo genérico
- Confirmar con Ricardo y Andrés qué cubren los otros speakers: el listing menciona sandboxing, permisos y rate limits en "del laptop a producción", que solapa con la sección 7
- Verificar estado del spec y de FastMCP la semana previa al evento
