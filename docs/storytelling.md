# Storytelling y diseño de la presentación

Investigación del 17-oct-2026 con Parallel, después de que Dante calificó la versión 1 (24
láminas) como monótona, larga, sin introducción, sin el porqué, sin conceptos y con diagramas
pobres. Aquí van los principios, sus fuentes y cómo se aplicaron en la versión 2.

## Principios y fuentes

| Principio | Fuente | Qué dice |
| --- | --- | --- |
| Contraste entre «lo que es» y «lo que podría ser» | Nancy Duarte, [The secret structure of great talks](https://www.ted.com/talks/nancy_duarte_the_secret_structure_of_great_talks) (TEDx, 2011); [Duarte: storytelling framework](https://www.duarte.com/resources/storytelling-framework/) | Las charlas que mueven a la gente alternan la realidad actual con la posible y terminan en la «new bliss» con un llamado a la acción. La audiencia es la protagonista: «¿quién es cuando entra y quién quiero que sea cuando salga?» |
| Afirmación + evidencia | Michael Alley, Penn State, [assertion-evidence.com](https://www.assertion-evidence.com/) y [checklist](http://www.writing.engr.psu.edu/AE_checklist.pdf); Garner y Alley, *International Journal of Engineering Education* 29(6), 2013 | Cada lámina abre con una oración que afirma algo (máximo dos líneas) y la respalda una evidencia visual, no una lista de viñetas. El estudio midió mejor comprensión que con títulos de frase y viñetas |
| Coherencia, señalización, redundancia, segmentación | Principios de Mayer ([resumen](https://www.digitallearninginstitute.com/blog/mayers-principles-multimedia-learning)) | Quitar lo que sobra; resaltar lo que importa; no poner en pantalla lo que se dice en voz alta; partir en bloques |
| El código se enseña en vivo, no en láminas | The Carpentries, [Live coding is a skill](https://carpentries.github.io/instructor-training/instructor/17-live.html) y [teaching tips](https://carpentries.org/blog/2015/03/teaching-tips) | Escribir el código frente a la gente, explicando cada línea; los errores enseñan; planear tiempo para la instalación; empezar desde un archivo vacío |
| Presentarse sin CV, después del gancho | [Six Minutes: how to introduce a speaker](https://sixminutes.dlugan.com/how-to-introduce-a-speaker/); [Marianna Swallow](https://www.mariannaswallow.com/voice-memos/pro-tips-introduce-speaker-bio) | Responder qué tema, por qué le importa a esta audiencia y por qué el ponente lo cuenta. «Your intro is not your résumé» |

## Cómo se aplicó en la versión 2

- **De 24 a 17 láminas.** Los minutos salieron de la pantalla y pasaron a las notas.
- **Gancho con evidencia real:** la misma pregunta («¿cuánta gente entró a Pantitlán en julio de
  2026?») en dos sesiones de `claude -p`. Sin herramientas: «No puedo darte la cifra… unos 4 a 5
  millones… es una estimación». Con el servidor: «4,623,233 personas», que coincide con la base.
- **Arco de Duarte:**
  - lo que es: la pregunta, «Claude estima», el modelo como función de texto a texto;
  - lo que podría ser: el dato con fuente, MCP como estándar, el mapa;
  - new bliss: «Ahora te toca», con el mismo patrón aplicado a su sistema, como Spot2.
- **Quién soy en la lámina 4**, después del gancho: foto, rol y la historia de Spot2 («¿esperamos
  a que lleguen al portal o vamos a donde ya preguntan?»), con las credenciales como chips.
- **Conceptos en tres láminas** (qué es MCP, en qué se diferencia, las tres piezas), cada una
  con un titular que afirma algo.
- **La construcción como señalización:** cada paso tiene un indicador 1·2·3·4, una idea, el
  código mínimo, una comprobación (✓) y un reto. El código se escribe en vivo, como piden
  las notas.
- **Ritmo visual:** láminas oscuras para portada, pregunta, sección, llamado y cierre; claras
  para contenido. Cifras grandes (10/10), foto, captura real del mapa.
- **Diagramas solo donde explican una estructura:** M×N contra M+N (lámina 6), capas de control
  (lámina 12) y el flujo de la lámina 15. El resto es tipografía, citas reales, código o imagen.
- **Una sola frase para recordar** al final: «Si el agente falla, arregla la descripción, no el modelo».

## Versión 3 (comentarios de Dante)

- «Falta explicar, dar definiciones»: se agregaron dos láminas de concepto (qué es una tool, con
  el ciclo de function calling, y quiénes participan en MCP) y una tarjeta de «Definición» con el
  mismo formato en cada lámina que introduce un término (LLM, tool, function calling, agente, MCP,
  host, client, server, API, CLI, resource, prompt, datos abiertos, uv, FastMCP, docstring, schema,
  contexto, idempotente, eval). Al final va un glosario de consulta que no cuenta en el tiempo.
  Que la definición se vea siempre igual aplica el principio de señalización de Mayer.
- «No pongas diapositivas negras, no sé si se vean bien»: todas las láminas son claras. El énfasis
  de portada, pregunta, sección y cierre ahora es una franja verde a la izquierda.
- Para no volver a alargarla, los conceptos ganaron 3 minutos y los pasos 2, 3 y 4 cedieron medio
  minuto cada uno.

## Versión 4 (comentarios de Dante)

- «No quiero sombras ni líneas raras»: se quitó la sombra que Google aplicaba a todas las formas
  (venía del tema) y se eliminaron las líneas decorativas: la franja verde, la raya bajo el título,
  las rayas sobre las columnas, el tachado de `ejecutar_sql` (ahora es «✗ ejecutar_sql(query)»), la
  línea vertical de la secuencia y la barra de las tarjetas de definición. Solo quedan las flechas y
  las líneas del diagrama M×N, que significan algo.
- «Separa lo que yo soy y lo que hemos implementado en Spot2; eso lo pongo yo»: la lámina 4 es solo
  personal (foto, rol, formación, CERN, UC San Diego, docencia) y la lámina 5 es un espacio para Dante.

## Versión 5 (comentarios de Dante)

- «Todas las puede leer la IA; ¿cuál es el incentivo de tener un MCP? ¿Qué problemas puede tener?»: la
  sección «¿Por qué MCP?» ahora empieza por la objeción honesta (la IA puede usar API, CLI o MCP; con
  buenas tools, CLI y MCP empatan en éxito) y responde con una tabla de situaciones y una lámina de lo
  que MCP da contra lo que cuesta. Es el contraste de Duarte aplicado al propio argumento: no vender MCP
  como si no tuviera costo.
- «Falta poner de qué se compone; revisa bien el estándar»: lámina con las capas de la spec 2026-07-28,
  marcando lo obligatorio, lo opcional, lo obsoleto y lo que usamos hoy. Es uno de los pocos lugares
  donde un diagrama explica una estructura.

## Versión 6 (comentarios de Dante)

- «No me queda claro cuál es el output o los takeaways; debería venir un recap»: se agregaron dos
  láminas espejo. La 4, «Al terminar tendrás un servidor MCP tuyo, conectado», va justo después del
  contraste: cuatro entregables y cinco preguntas. La 22, «Recap», es la misma lámina con los entregables
  marcados y las respuestas, antes de «Ahora te toca».
- Fuente: The Carpentries, [Launches and Landings](https://carpentries.github.io/instructor-training/23-introductions.html)
  (actualizado 25-ago-2025). La introducción debe «clarify learning objectives and expectations»; una buena
  conclusión «helps learners to solidify what they have learned and plan their next steps». El reflejo
  entre las dos láminas aplica la señalización de Mayer: la misma composición hace evidente qué cambió.
- Tiempo: apertura 1 min y recap 1.5 min. Ceden medio minuto el contraste, los pasos 2 y 4, el mapa y la
  demo en vivo.

## Portada (comentario de Dante: «tampoco me gusta la portada»)

- Antes: solo texto sobre fondo vacío y un título inventado («Que Claude consulte el mundo real») que no era
  el nombre del taller.
- Ahora: el título real («Datos abiertos over MCP», con «Claude que consulta fuentes reales» como subtítulo),
  formato y duración, foto y rol del ponente, y como imagen el propio dato: la afluencia del Metro de julio de
  2026. El círculo más grande es Pantitlán, que es la pregunta de la lámina 2; la nota del orador lo usa como
  puente. Sin líneas decorativas ni sombras.

## Lámina 6: Spot2 (pedido de Dante: «pregúntale a Devin qué hemos implementado de MCP»)

- Titular: «En Spot2, cada capacidad nace con su API y su MCP».
- Repite el diagrama «Con MCP» de la lámina 9 con los clientes y servidores reales de Spot2: la sala ve que
  el diagrama abstracto ya existe en una empresa mexicana.
- Abre el puente al taller: «hoy construyes una versión chiquita de esto, con datos públicos».
- Falta el número de personas (`PERSONAS_MCP`).

## Lámina 2: lluvia de preguntas (pedido de Dante)

- La pregunta de Pantitlán queda al centro, en serif y tinta; alrededor, 16 preguntas reales en dos tonos de
  gris y tamaños distintos. Todas tienen un conjunto público detrás (tabla en `presentacion.md`).
- El mensaje: los datos públicos ya contestan muchas preguntas; hoy contestamos una y al final cada quien elige
  otra. Por eso la lámina 24 («Ahora te toca») baja a medio minuto: la lluvia ya sembró las ideas.
- Tiempo: la lámina 2 pasa de 0.5 a 1 minuto; el total sigue en 40.

## Versión 8: pregunta y respuesta en dos láminas (pedido de Dante: «sino no me van a seguir»)

- Lámina 2: la lluvia y la pregunta, con «Levanten la mano: ¿más o menos de 3 millones?» (antes decía «Una
  mano arriba», que no se entendía). La respuesta no aparece.
- Lámina 3 (nueva): la revelación. 4,623,233 en grande, ≈149,137 al día, «Quienes dijeron «más de 3
  millones», acertaron», la suma de sus cuatro líneas en una barra y las 5 estaciones con más entradas. Cierra
  con la pregunta puente: «¿Y Claude lo sabía?», que abre el contraste de la lámina 4.
- Cifras: salida de `afluencia_metro` y `ranking_estaciones_metro` del paso 4; el generador revisa que las
  cuatro líneas sumen el total.
- Tiempo: la respuesta dura medio minuto y el contraste baja de 1 a 0.5, porque el número ya se reveló.

## Versión 9: skills (pedido de Dante)

- Lámina 16, «Un MCP da acceso; una skill le enseña a usarlo», entre «Tres piezas» y el transporte: cierra el
  bloque conceptual con la pieza que guía al agente y conecta con el `CLAUDE.md` que usa el taller.
- Mismo lenguaje visual: tarjeta de definición, chips azul (servidor) y verde (skill), código con lo que lee
  el modelo en verde y una secuencia con flechas para la carga progresiva.

## Lámina 10 con el diagrama oficial (pedido de Dante)

- Cajas con borde a los lados, protocolo en azul al centro y flechas de ida y vuelta, como en
  modelcontextprotocol.io; los pies de columna dicen qué trae cada lado (cliente o servidor MCP).
