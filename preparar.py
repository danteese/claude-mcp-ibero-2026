"""Prepara los datos del taller.

    uv run preparar.py              # construye datos/cdmx.sqlite y mapa/datos.js con los CSV del repo (sin red)
    uv run preparar.py --descargar  # vuelve a bajar los CSV de datos.cdmx.gob.mx y luego construye

Los CSV de `datos/` son la copia cruda de la fuente: se guardan tal cual llegan,
con sus errores de codificación. La limpieza ocurre aquí, al construir SQLite,
para que se pueda auditar qué cambió y por qué.

Fuentes (licencia CC-BY-4.0, Gobierno de la Ciudad de México):
  https://datos.cdmx.gob.mx/dataset/afluencia-diaria-del-metro-cdmx
  https://datos.cdmx.gob.mx/dataset/lineas-y-estaciones-del-metro
"""

import argparse
import csv
import io
import json
import re
import sqlite3
import unicodedata
import zipfile
from collections import Counter, defaultdict
from datetime import UTC, date, datetime
from pathlib import Path
from xml.etree import ElementTree

import httpx

RAIZ = Path(__file__).parent
DATOS = RAIZ / "datos"
CSV_AFLUENCIA = DATOS / "metro_afluencia_mensual_crudo.csv"
CSV_ESTACIONES = DATOS / "metro_estaciones_crudo.csv"
BASE = DATOS / "cdmx.sqlite"
DATOS_MAPA = RAIZ / "mapa" / "datos.js"

CKAN = "https://datos.cdmx.gob.mx/api/3/action"
RECURSO_AFLUENCIA = "0e8ffe58-28bb-4dde-afcd-e5f5b4de4ccb"
URL_KMZ_ESTACIONES = (
    "https://datos.cdmx.gob.mx/dataset/1b014317-ddb1-46c7-ac79-7330c652abe3/resource/"
    "b9b61c06-8325-4df1-85c6-10c3aa7af1ac/download/b9b61c06-8325-4df1-85c6-10c3aa7af1ac.zip"
)
PRIMER_ANIO = 2010


# --- Descarga -----------------------------------------------------------------


def descargar_afluencia(cliente: httpx.Client) -> list[dict]:
    """Agrega la afluencia diaria por mes dentro de CKAN, un año a la vez.

    La columna `afluencia` llega como texto: hay que convertirla en la consulta.
    CKAN limita cada respuesta a 32 000 filas; por eso se pide año por año.
    El firewall del portal rechaza (403) algunas construcciones SQL, como `''`.
    """
    filas = []
    for anio in range(PRIMER_ANIO, date.today().year + 1):
        sql = (
            "SELECT substring(fecha, 1, 7) AS mes, linea, estacion, "
            "SUM(afluencia::bigint) AS afluencia, "
            "COUNT(DISTINCT fecha) AS dias, COUNT(*) AS registros "
            f'FROM "{RECURSO_AFLUENCIA}" '
            f"WHERE fecha >= '{anio}-01-01' AND fecha < '{anio + 1}-01-01' "
            "GROUP BY 1, 2, 3 ORDER BY 1, 2, 3"
        )
        respuesta = cliente.get(f"{CKAN}/datastore_search_sql", params={"sql": sql})
        respuesta.raise_for_status()
        registros = respuesta.json()["result"]["records"]
        print(f"  afluencia {anio}: {len(registros)} filas")
        filas.extend(registros)
    return filas


def descargar_estaciones(cliente: httpx.Client) -> list[dict]:
    """Lee el KMZ oficial (un zip con otro zip adentro) y extrae cada estación."""
    respuesta = cliente.get(URL_KMZ_ESTACIONES)
    respuesta.raise_for_status()
    with zipfile.ZipFile(io.BytesIO(respuesta.content)) as externo:
        nombre_kmz = next(n for n in externo.namelist() if n.endswith("estaciones.kmz"))
        with zipfile.ZipFile(io.BytesIO(externo.read(nombre_kmz))) as kmz:
            kml = kmz.read("doc.kml")

    ns = {"kml": "http://www.opengis.net/kml/2.2"}
    filas = []
    for marca in ElementTree.fromstring(kml).iterfind(".//kml:Placemark", ns):
        tabla = marca.findtext("kml:description", default="", namespaces=ns)
        campos = dict(re.findall(r"<td>([^<]+)</td>\s*<td>([^<]*)</td>", tabla))
        lon, lat, _ = marca.findtext(".//kml:coordinates", namespaces=ns).strip().split(",")
        filas.append(
            {
                "nombre": campos["NOMBRE"],
                "linea": campos["LINEA"],
                "clave": campos["CVE_EST"],
                "tipo": campos["TIPO"],
                "alcaldia": campos["ALCALDIAS"],
                "anio_apertura": campos["AÑO"],
                "lat": lat,
                "lon": lon,
            }
        )
    print(f"  estaciones: {len(filas)} filas")
    return filas


def guardar_csv(ruta: Path, filas: list[dict]) -> None:
    ruta.parent.mkdir(exist_ok=True)
    with ruta.open("w", newline="", encoding="utf-8") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=list(filas[0]))
        escritor.writeheader()
        escritor.writerows(filas)


def leer_csv(ruta: Path) -> list[dict]:
    with ruta.open(newline="", encoding="utf-8") as archivo:
        return list(csv.DictReader(archivo))


# --- Limpieza -----------------------------------------------------------------

# El KMZ y la tabla de afluencia no escriben igual dos estaciones.
ALIAS_KMZ = {
    "mixhiuca": "mixiuhca",  # errata en el KMZ
    "ninos heroes poder judicial cdmx": "ninos heroes",
}


def arreglar_codificacion(texto: str) -> str:
    """Revierte UTF-8 leído como Latin-1: 'LÃ­nea' -> 'Línea'. Si no aplica, no toca el texto."""
    try:
        return texto.encode("latin-1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return texto


def clave_busqueda(texto: str) -> str:
    """Minúsculas, sin acentos ni signos: 'Etiopía/Plaza' -> 'etiopia plaza'."""
    sin_acentos = unicodedata.normalize("NFKD", texto)
    sin_acentos = "".join(c for c in sin_acentos if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", " ", sin_acentos.lower()).strip()


def normalizar_linea(texto: str) -> str:
    """'Linea 1', 'LÃ­nea 1' y '01' -> 'Línea 1'."""
    codigo = re.search(r"(\d+|[AB])\s*$", arreglar_codificacion(texto).strip()).group(1)
    return f"Línea {codigo.lstrip('0') or '0'}"


def limpiar_afluencia(crudas: list[dict]) -> tuple[list[tuple], dict[tuple, str], list[tuple]]:
    bitacora = Counter()
    variantes = defaultdict(Counter)
    for fila in crudas:
        nombre = arreglar_codificacion(fila["estacion"])
        if nombre != fila["estacion"] or arreglar_codificacion(fila["linea"]) != fila["linea"]:
            bitacora["codificacion"] += 1
        if fila["linea"].startswith("Linea"):
            bitacora["linea_sin_acento"] += 1
        variantes[(normalizar_linea(fila["linea"]), clave_busqueda(nombre))][nombre] += 1

    # Una estación puede aparecer escrita de varias formas ('Gómez Farias' / 'Gómez Farías').
    # Se queda la grafía más frecuente; en empate, la que conserva más acentos.
    canonico = {
        llave: max(conteo, key=lambda n: (conteo[n], sum(not c.isascii() for c in n)))
        for llave, conteo in variantes.items()
    }
    bitacora["grafias_unificadas"] = sum(len(c) - 1 for c in variantes.values())

    meses = defaultdict(lambda: [0, 0, 0])
    for fila in crudas:
        linea = normalizar_linea(fila["linea"])
        estacion = canonico[(linea, clave_busqueda(arreglar_codificacion(fila["estacion"])))]
        acumulado = meses[(fila["mes"], linea, estacion)]
        acumulado[0] += int(fila["afluencia"])
        acumulado[1] = max(acumulado[1], int(fila["dias"]))
        acumulado[2] += int(fila["registros"])

    filas = [(mes, linea, est, a, d, r) for (mes, linea, est), (a, d, r) in sorted(meses.items())]
    duplicados = [f for f in filas if f[5] > f[4]]
    todos_los_meses = {f[0] for f in filas}
    presentes = defaultdict(set)
    for mes, linea, estacion, *_ in filas:
        presentes[(linea, estacion)].add(mes)
    faltantes = [
        f"{estacion} ({linea}): {', '.join(sorted(todos_los_meses - meses_estacion))}"
        for (linea, estacion), meses_estacion in sorted(presentes.items())
        if meses_estacion != todos_los_meses
    ]
    reglas = [
        ("codificacion", bitacora["codificacion"], "'LÃ­nea 1' -> 'Línea 1'"),
        ("linea_sin_acento", bitacora["linea_sin_acento"], "'Linea 1' -> 'Línea 1'"),
        ("grafias_unificadas", bitacora["grafias_unificadas"], "'Gómez Farias' -> 'Gómez Farías'"),
        (
            "meses_con_registros_duplicados",
            len(duplicados),
            "; ".join(f"{f[0]} {f[2]} ({f[1]}): {f[5]} registros en {f[4]} días" for f in duplicados),
        ),
        ("meses_faltantes", len(faltantes), "; ".join(faltantes) or "ninguno"),
    ]
    return filas, canonico, reglas


def limpiar_estaciones(crudas: list[dict], canonico: dict[tuple, str]) -> tuple[list[tuple], list[tuple]]:
    filas, sin_par = [], []
    for fila in crudas:
        linea = normalizar_linea(fila["linea"])
        clave = clave_busqueda(fila["nombre"])
        clave = ALIAS_KMZ.get(clave, clave)
        nombre = canonico.get((linea, clave))
        if nombre is None:
            sin_par.append(f"{fila['nombre']} ({linea})")
            continue
        filas.append(
            (
                nombre,
                linea,
                fila["clave"],
                fila["tipo"],
                fila["alcaldia"],
                int(fila["anio_apertura"]),
                float(fila["lat"]),
                float(fila["lon"]),
                clave_busqueda(nombre),
            )
        )
    reglas = [("alias_kmz", len(ALIAS_KMZ), "; ".join(f"{a} -> {b}" for a, b in ALIAS_KMZ.items()))]
    if sin_par:
        reglas.append(("estaciones_kmz_sin_afluencia", len(sin_par), "; ".join(sin_par)))
    return filas, reglas


# --- Construcción -------------------------------------------------------------

ESQUEMA = """
CREATE TABLE estaciones (
    estacion TEXT NOT NULL, linea TEXT NOT NULL, clave TEXT, tipo TEXT, alcaldia TEXT,
    anio_apertura INTEGER, lat REAL, lon REAL, busqueda TEXT NOT NULL,
    PRIMARY KEY (estacion, linea)
);
CREATE TABLE afluencia_mensual (
    mes TEXT NOT NULL, linea TEXT NOT NULL, estacion TEXT NOT NULL,
    afluencia INTEGER NOT NULL, dias INTEGER NOT NULL, registros INTEGER NOT NULL,
    PRIMARY KEY (mes, linea, estacion)
);
CREATE TABLE fuentes (clave TEXT PRIMARY KEY, valor TEXT NOT NULL);
CREATE TABLE limpieza (regla TEXT PRIMARY KEY, filas_afectadas INTEGER NOT NULL, detalle TEXT NOT NULL);
"""


def construir() -> None:
    afluencia, canonico, reglas_afluencia = limpiar_afluencia(leer_csv(CSV_AFLUENCIA))
    estaciones, reglas_estaciones = limpiar_estaciones(leer_csv(CSV_ESTACIONES), canonico)

    temporal = BASE.with_suffix(".tmp")
    temporal.unlink(missing_ok=True)
    with sqlite3.connect(temporal) as db:
        db.executescript(ESQUEMA)
        db.executemany("INSERT INTO afluencia_mensual VALUES (?, ?, ?, ?, ?, ?)", afluencia)
        db.executemany("INSERT INTO estaciones VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", estaciones)
        db.executemany("INSERT INTO limpieza VALUES (?, ?, ?)", reglas_afluencia + reglas_estaciones)
        meses = [fila[0] for fila in afluencia]
        db.executemany(
            "INSERT INTO fuentes VALUES (?, ?)",
            [
                ("afluencia", "https://datos.cdmx.gob.mx/dataset/afluencia-diaria-del-metro-cdmx"),
                ("estaciones", "https://datos.cdmx.gob.mx/dataset/lineas-y-estaciones-del-metro"),
                ("ecobici_gbfs", "https://gbfs.mex.lyftbikes.com/gbfs/gbfs.json"),
                ("licencia", "CC-BY-4.0 · Gobierno de la Ciudad de México"),
                ("cobertura_desde", min(meses)),
                ("cobertura_hasta", max(meses)),
                ("construido_en", datetime.now(UTC).isoformat(timespec="seconds")),
            ],
        )
    temporal.replace(BASE)

    print(f"Listo: {BASE.relative_to(RAIZ)}")
    print(f"  {len(afluencia):,} filas de afluencia mensual ({min(meses)} a {max(meses)})")
    print(f"  {len(estaciones)} estaciones con coordenadas")
    print("  Limpieza aplicada:")
    for regla, n, detalle in reglas_afluencia + reglas_estaciones:
        print(f"    - {regla}: {n} · {detalle}")


def exportar_mapa() -> None:
    """Escribe mapa/datos.js: entradas diarias promedio por estación-línea y mes.

    Se carga con <script> y no con fetch, para que mapa/index.html abra con doble clic, sin servidor.
    """
    with sqlite3.connect(f"{BASE.as_uri()}?mode=ro", uri=True) as db:
        meses = [mes for (mes,) in db.execute("SELECT DISTINCT mes FROM afluencia_mensual ORDER BY mes")]
        posicion = {mes: i for i, mes in enumerate(meses)}
        puntos = {
            (estacion, linea): {
                "estacion": estacion,
                "linea": linea,
                "lat": lat,
                "lon": lon,
                "diario": [None] * len(meses),
            }
            for estacion, linea, lat, lon in db.execute(
                "SELECT estacion, linea, lat, lon FROM estaciones ORDER BY linea, clave"
            )
        }
        for mes, linea, estacion, afluencia, dias in db.execute(
            "SELECT mes, linea, estacion, afluencia, dias FROM afluencia_mensual"
        ):
            if punto := puntos.get((estacion, linea)):
                punto["diario"][posicion[mes]] = round(afluencia / dias)

    datos = {
        "meses": meses,
        "unidad": "entradas diarias promedio",
        "fuente": "Afluencia diaria del Metro CDMX y Ubicación de estaciones · datos.cdmx.gob.mx · CC-BY-4.0",
        "estaciones": list(puntos.values()),
    }
    DATOS_MAPA.write_text(
        f"window.DATOS_MAPA = {json.dumps(datos, ensure_ascii=False, separators=(',', ':'))};\n", encoding="utf-8"
    )
    print(f"Listo: {DATOS_MAPA.relative_to(RAIZ)} ({len(puntos)} estaciones-línea × {len(meses)} meses)")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--descargar", action="store_true", help="volver a bajar los CSV desde las fuentes")
    args = parser.parse_args()

    if args.descargar:
        print("Descargando de datos.cdmx.gob.mx ...")
        with httpx.Client(timeout=120, follow_redirects=True) as cliente:
            guardar_csv(CSV_ESTACIONES, descargar_estaciones(cliente))
            guardar_csv(CSV_AFLUENCIA, descargar_afluencia(cliente))
    elif not CSV_AFLUENCIA.exists():
        raise SystemExit("Faltan los CSV de datos/. Ejecuta: uv run preparar.py --descargar")

    construir()
    exportar_mapa()


if __name__ == "__main__":
    main()
