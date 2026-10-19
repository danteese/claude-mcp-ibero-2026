# Demo de cierre: mapa de afluencia del Metro

**Estado:** implementado (`mapa/index.html` + `preparar.py`) y ensayado una vez con `claude -p`.
**Tiempo:** 5 minutos al final del taller.

## Decisión (17-oct-2026)

- **Un solo caso: Metro.** Dante pidió elegir el de mejor información. El histórico de viajes de
  Ecobici en el portal no tiene estación (solo mes, hora de arribo, género y edad), así que no
  sirve para un mapa. Los viajes con estación están en ecobici.cdmx.gob.mx y se bajan mes por
  mes. El feed en vivo (GBFS) no declara licencia. El Metro ya está en el repo, con estación,
  coordenadas oficiales, 16 años y licencia CC-BY-4.0.
- **Slider de mes, no de hora.** No hay datos por hora por estación ni datos del Metro en
  tiempo real (ver `datos.md`).
- **Los participantes clonan el repo y juegan.** El mapa ya viene hecho; en vivo, Claude lo
  modifica usando las tools MCP.
- **Menos es más.** Un solo HTML, sin dependencias, que abre con doble clic y no necesita servidor.

## Qué hay

```text
datos/cdmx.sqlite ──► preparar.py ──► mapa/datos.js ──► mapa/index.html   (lo ve la gente)
        │
        └──────────► servidor MCP (tools) ──► Claude ──► edita mapa/index.html
```

- `uv run preparar.py` genera `mapa/datos.js`: entradas diarias promedio por estación-línea
  y mes (195 × 199, unos 238 KB; está en `.gitignore`).
- `mapa/index.html` (156 líneas): proyecta lat/lon a SVG, une las estaciones en orden
  de clave (verificado que sigue el recorrido; el salto más largo es de 2.4 km), dibuja el
  área de cada círculo proporcional a la afluencia con la misma escala en todos los meses y
  un anillo vacío cuando el valor es 0. Junto al mapa: resumen de la red y top 5 del mes.
- Las historias que se ven solas:
  - abril de 2020: 1,371,313 entradas diarias en la red;
  - junio de 2021: 20 estaciones-línea en 0 (Línea 12);
  - octubre de 2022: 32 en 0 (Línea 12 y la mitad oriente de la Línea 1);
  - julio de 2026: 3,346,186 entradas diarias, ninguna estación en 0.

## Capa de Ecobici en vivo (agregada a petición de Dante)

**Regla: el navegador no consulta Ecobici.** El dato pasa por el MCP:

```text
GBFS en vivo ──► tool ecobici_cerca_de_metro ──► Claude ──► mapa/ecobici.js ──► panel "Ecobici en vivo"
```

- **Un momento de construcción del MCP:** la tool no devolvía coordenadas y el mapa las
  necesitaba. Se agregó `metro: {lat, lon}` y `lat`/`lon` por cicloestación. Un consumidor
  nuevo cambió el contrato de la tool, y `verificar.py 4` ahora protege ese contrato (falla
  con "no trae coordenadas" si se quitan).
- `mapa/ecobici.js` es la salida de la tool tal cual. Lo escribe Claude y no se versiona
  (está en `.gitignore`; además, el feed no declara licencia).
- Sin ese archivo, el panel muestra qué pedirle a Claude.
- Ensayo con `claude -p`: **31 s, US$0.20, 4 turnos.** Hizo `ToolSearch`, llamó
  `ecobici_cerca_de_metro` (Insurgentes, `limite=10`) y luego `Write`. El resultado fueron 12
  cicloestaciones a 500 m y 99 bicis.

## Guion de 5 minutos

1. **(1 min) Concepto:** el diagrama de arriba. Los mismos datos tienen dos consumidores:
   Claude, por MCP (preguntas), y las personas, por el HTML (vista).
2. **(1 min) El mapa:** `open mapa/index.html` y mover el slider a abril de 2020, junio de
   2021 y octubre de 2022.
3. **(3 min) En vivo, en Claude Code:**
   > Usa el servidor cdmx para averiguar en qué meses estuvo en cero la Línea 12. Luego agrega
   > a mapa/index.html un aviso visible que aparezca solo cuando el slider esté en esos meses,
   > con la cifra y la fuente. Cambia lo mínimo.

   Recargar el navegador y mover el slider a junio de 2021.

**Punto didáctico que salió en el ensayo:** el aviso que escribió Claude dice "cerrada tras el
colapso del 3 de mayo de 2021" e "inauguración: 30 de octubre de 2012". Esos motivos **no
vienen de la tool**: el dato solo dice "0 entradas". Claude los agregó de su conocimiento. Es
un buen ejemplo para separar lo que dice la fuente de lo que añade el modelo.

## Más ejercicios para jugar (participantes)

- Etiquetar en el mapa las 5 estaciones más concurridas del mes.
- Agregar un filtro por línea.
- Colorear por cambio contra el mismo mes del año anterior.
- Con `ranking_estaciones_metro`, marcar las 10 menos concurridas del último año.

## Pendiente

- [ ] Probar el ejercicio en Claude Code interactivo (el ensayo fue con `claude -p`).
- [ ] Captura o video de respaldo por si falla la red.
- [ ] Decidir si se conserva `ecobici_cerca_de_metro` en el paso 4, ahora que el cierre es solo Metro.
