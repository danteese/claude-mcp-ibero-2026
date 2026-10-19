# Datos

## Fuentes que usa el servidor

| Fuente | Origen | Licencia | Cobertura | Uso |
| --- | --- | --- | --- | --- |
| Afluencia diaria del Metro CDMX (simple) | [datos.cdmx.gob.mx](https://datos.cdmx.gob.mx/dataset/afluencia-diaria-del-metro-cdmx), recurso `0e8ffe58-28bb-4dde-afcd-e5f5b4de4ccb` | CC-BY-4.0 | 2010-01-01 a 2026-07-31, por día, estación y línea (1,180,920 filas) | Agregada por mes: 38,804 filas en `afluencia_mensual` |
| Ubicación de líneas y estaciones del Metro | [datos.cdmx.gob.mx](https://datos.cdmx.gob.mx/dataset/lineas-y-estaciones-del-metro), KMZ `b9b61c06-8325-4df1-85c6-10c3aa7af1ac` | CC-BY-4.0 | 195 pares estación-línea con coordenadas, alcaldía, tipo y año de apertura | Tabla `estaciones` |
| Catálogo del portal | API CKAN `https://datos.cdmx.gob.mx/api/3/action` (CKAN 2.11.5) | Varía por conjunto | 475 conjuntos | En vivo: `buscar_datasets_cdmx` |
| Ecobici en vivo | Feed GBFS `https://gbfs.mex.lyftbikes.com/gbfs/gbfs.json` | **No declara licencia** (`license_url` vacío) | 677 cicloestaciones; se actualiza cada minuto | En vivo: `ecobici_cerca_de_metro` |

Las cifras de este cuadro se observaron al consultar las fuentes el 17-oct-2026.

## Lo que se encontró al limpiar (medido)

`uv run preparar.py` lo imprime y lo guarda en la tabla `limpieza`:

| Regla | Filas afectadas | Ejemplo |
| --- | --- | --- |
| `codificacion` | 16,289 | `LÃ­nea 1` → `Línea 1` (UTF-8 leído como Latin-1; ene-2021 a may-2023) |
| `linea_sin_acento` | 33,149 | `Linea 1` → `Línea 1` |
| `grafias_unificadas` | 2 | `Gómez Farias` → `Gómez Farías` |
| `meses_con_registros_duplicados` | 1 | dic-2020, Oceanía (Línea B): 62 registros en 31 días |
| `meses_faltantes` | 1 | Deportivo Oceanía (Línea B): dic-2020; sus datos vienen etiquetados como Oceanía |
| `alias_kmz` | 2 | `Mixhiuca` → `Mixiuhca`; `Niños Héroes/Poder Judicial CDMX` → `Niños Héroes` |

Por la codificación y el acento, el portal reporta 24 "líneas" distintas en lugar de 12.

## Peculiaridades de la fuente (sirven como ejemplos en la presentación)

- `afluencia` llega como texto: hay que convertirla (`afluencia::bigint`) para sumar.
- El diccionario de datos menciona las columnas `dia` y `ano`, que no existen en el recurso.
- El firewall del portal responde 403 a algunas construcciones SQL; por ejemplo, `NULLIF(afluencia, '')`.
- `datastore_search_sql` devuelve como máximo 32,000 filas; por eso la descarga se hace año por año.
- La fuente trae filas en cero para estaciones que todavía no existían: la Línea 12 aparece
  desde 2010-01, pero su primera afluencia es de 2012-11.
- La Línea 12 tiene afluencia 0 de jun-2021 a dic-2022. El dato es el cero; atribuirlo al
  cierre de la línea es contexto externo, no algo que diga la tabla.
- La Línea 1 tiene 12 de sus 20 estaciones en cero de ago-2022 a sep-2023, y después vuelven
  de forma escalonada (quedan 7 en cero a inicios de 2025). Son 335 filas estación-mes en cero.
- Las filas en cero no se borran: las tools las reportan en `notas` y el ranking de "menos
  concurridas" las excluye.

## Conjuntos que existen y no se usan (aún)

| Conjunto | Qué trae | Nota |
| --- | --- | --- |
| [Datos de Movilidad (histórico COVID-19)](https://datos.cdmx.gob.mx/dataset/movilidad-historico-covid-19) · "Índice de Afluencia en el Metro (promedio entre semana)", recurso `b4b6b8a9-5eba-432a-b7d4-1d48ddf82036` | Índice **por hora y por línea**: 44 semanas de 2020 (05-feb a 02-dic), 24 horas, 12 líneas, 14,112 filas | Es el único dato por hora que encontramos. Su descripción dice: "índice de afluencia promedio en el metro para los días martes, miércoles y jueves a partir de la semana 10 de 2020". **No documenta la unidad**. Hay valores `NaN` y semanas casi en cero (5-feb-2020, Línea 2). Una semana que sí se ve bien (22-abr-2020, Línea 2) tiene picos a las 08:00 (20.2) y a las 18:00 (27.1). Ver `demo-mapa.md` |
| Mismo conjunto · "promedio fines de semana" | Índice por hora, **sin línea** | 1,392 filas |
| Afluencia del Metro desglosada | Afluencia por medio de acceso (tarjeta, boleto, gratuidad) | 70 MB |
| [GTFS estático CDMX](https://datos.cdmx.gob.mx/dataset/gtfs) | Rutas, paradas, horarios y frecuencias | No explorado; podría dar el trazo y el orden de las estaciones |
| [Viajes del sistema Ecobici](https://datos.cdmx.gob.mx/dataset/afluencia-diaria-del-sistema-ecobici) | Viajes diarios (por género) y mensuales (por género, edad y hora de arribo); 115,773 filas en el mensual; CC-BY-4.0 | **No tiene estación**: no sirve para un mapa. Los viajes con estación están en ecobici.cdmx.gob.mx/datos-abiertos, en descargas mensuales |
| Índice de la calidad del aire (y otros 17) | SEDEMA | No explorado |
| Solicitudes *0311 | Reportes ciudadanos | No explorado |

**No encontramos datos abiertos del Metro en tiempo real** (afluencia ni ocupación). Lo único
en vivo es Ecobici (GBFS). La búsqueda "tiempo real transporte" en el portal no devolvió nada
del Metro.

## Esquema de `datos/cdmx.sqlite`

```text
estaciones(estacion, linea, clave, tipo, alcaldia, anio_apertura, lat, lon, busqueda)   PK (estacion, linea)
afluencia_mensual(mes, linea, estacion, afluencia, dias, registros)                      PK (mes, linea, estacion)
fuentes(clave, valor)          procedencia, licencia, cobertura, fecha de construcción
limpieza(regla, filas_afectadas, detalle)
```

Los reportes ciudadanos del paso 3 viven en otra base, `datos/reportes.sqlite`, que crea el
servidor. Las dos bases están en `.gitignore`.
