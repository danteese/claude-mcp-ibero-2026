"""Paso 2 · Consultar datos abiertos con tools bien diseñadas.

Sobre la copia local (datos/cdmx.sqlite, generada con `uv run preparar.py`):
- tools por intención, no un `ejecutar_sql(query)` genérico;
- parámetros con enums, rangos y formatos que el modelo no tiene que adivinar;
- errores que le dicen al modelo cómo corregirse;
- salidas acotadas, con unidad, alcance y fuente;
- conexión de solo lectura: estas tools no pueden escribir aunque quisieran;
- un resource (`cdmx://fuentes`) que la aplicación decide cuándo leer.

    uv run fastmcp list pasos/02_consulta.py
    uv run fastmcp call pasos/02_consulta.py afluencia_metro estacion=pantitlan agrupar_por=anio
"""

import difflib
import json
import re
import sqlite3
import unicodedata
from contextlib import contextmanager
from pathlib import Path
from typing import Annotated, Literal

import httpx
from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from pydantic import Field

# De dónde sale cada dato. El servidor corre en tu máquina; sólo una tool sale a internet.
# - Metro (afluencia y estaciones): copia local en datos/cdmx.sqlite, que arma `uv run preparar.py`
#   con los CSV del repo. El histórico no cambia, la consulta es instantánea y funciona sin red.
# - Catálogo de datos.cdmx.gob.mx (CKAN): en vivo, porque cambia.
RAIZ = Path(__file__).resolve().parent
DATOS = RAIZ / "datos" if (RAIZ / "datos").is_dir() else RAIZ.parent / "datos"
BASE = DATOS / "cdmx.sqlite"
# CKAN (Comprehensive Knowledge Archive Network): software abierto para portales de datos; datos.cdmx.gob.mx
# es uno. package_search busca conjuntos y sólo trae metadatos (título, formatos, enlace), no los datos.
CKAN = "https://datos.cdmx.gob.mx/api/3/action"
FUENTE_AFLUENCIA = "Afluencia diaria del Metro CDMX · datos.cdmx.gob.mx · CC-BY-4.0"

Linea = Literal["1", "2", "3", "4", "5", "6", "7", "8", "9", "12", "A", "B"]
Mes = Annotated[str, Field(pattern=r"^\d{4}-(0[1-9]|1[0-2])$", description="Mes en formato AAAA-MM, p. ej. 2024-03.")]
SOLO_LECTURA = {"readOnlyHint": True, "openWorldHint": False}

mcp = FastMCP(
    "cdmx",
    instructions=(
        "Datos abiertos de la Ciudad de México: afluencia mensual del Metro por estación y línea "
        "(copia local desde 2010), ubicación de estaciones y catálogo de datos.cdmx.gob.mx. "
        "Úsalo para preguntas sobre el Metro de la CDMX o para descubrir datos públicos. "
        "Si el nombre de una estación es ambiguo, llama primero a buscar_estacion_metro."
    ),
)


# --- Utilidades -----------------------------------------------------------------


@contextmanager
def conectar():
    if not BASE.exists():
        raise ToolError("Falta datos/cdmx.sqlite. Pide a la persona usuaria ejecutar `uv run preparar.py` y reintenta.")
    db = sqlite3.connect(f"{BASE.as_uri()}?mode=ro", uri=True)
    db.row_factory = sqlite3.Row
    try:
        yield db
    finally:
        db.close()


def clave_busqueda(texto: str) -> str:
    sin_acentos = "".join(c for c in unicodedata.normalize("NFKD", texto) if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", " ", sin_acentos.lower()).strip()


def sumar_meses(mes: str, n: int) -> str:
    anio, m = map(int, mes.split("-"))
    total = anio * 12 + m - 1 + n
    return f"{total // 12}-{total % 12 + 1:02d}"


def agrupar_meses(meses: list[str]) -> list[str]:
    """['2021-06', '2021-07', '2021-09'] -> ['2021-06 a 2021-07', '2021-09']"""
    rangos = []
    for mes in meses:
        if rangos and rangos[-1][1] == sumar_meses(mes, -1):
            rangos[-1][1] = mes
        else:
            rangos.append([mes, mes])
    return [inicio if inicio == fin else f"{inicio} a {fin}" for inicio, fin in rangos]


def validar_periodo(db: sqlite3.Connection, desde: str | None, hasta: str | None) -> tuple[str, str]:
    inicio, fin = db.execute("SELECT MIN(mes), MAX(mes) FROM afluencia_mensual").fetchone()
    hasta = hasta or fin
    desde = desde or sumar_meses(hasta, -11)
    if desde > hasta:
        raise ToolError(f"desde ({desde}) es posterior a hasta ({hasta}).")
    if hasta < inicio or desde > fin:
        raise ToolError(f"El periodo {desde} a {hasta} está fuera de la cobertura disponible: {inicio} a {fin}.")
    return max(desde, inicio), min(hasta, fin)


def resolver_estacion(db: sqlite3.Connection, texto: str, linea: str | None) -> list[sqlite3.Row]:
    """Filas (estación, línea) de UNA estación, o un ToolError que explica cómo corregir."""
    clave = clave_busqueda(texto)
    filtro, extra = (" AND linea = ?", [f"Línea {linea}"]) if linea else ("", [])
    filas = db.execute(f"SELECT * FROM estaciones WHERE busqueda = ?{filtro}", [clave, *extra]).fetchall()
    if not filas:
        filas = db.execute(f"SELECT * FROM estaciones WHERE busqueda LIKE ?{filtro}", [f"%{clave}%", *extra]).fetchall()
    if len({f["estacion"] for f in filas}) == 1:
        return filas
    if filas:
        opciones = sorted({f"{f['estacion']} ({f['linea']})" for f in filas})
        raise ToolError(
            f"'{texto}' coincide con varias estaciones: {', '.join(opciones)}. Repite con el nombre exacto."
        )

    if linea and (otras := db.execute("SELECT linea FROM estaciones WHERE busqueda = ?", [clave]).fetchall()):
        lineas = ", ".join(f["linea"] for f in otras)
        raise ToolError(f"'{texto}' no está en la Línea {linea}; está en: {lineas}. Corrige `linea`.")
    nombres = {f["busqueda"]: f["estacion"] for f in db.execute("SELECT busqueda, estacion FROM estaciones")}
    parecidas = [nombres[c] for c in difflib.get_close_matches(clave, nombres, n=4, cutoff=0.6)]
    sugerencia = f" ¿Quisiste decir: {', '.join(parecidas)}?" if parecidas else ""
    donde = f" en la Línea {linea}" if linea else ""
    raise ToolError(
        f"No encontré la estación '{texto}'{donde}.{sugerencia} Usa buscar_estacion_metro para ver opciones."
    )


# --- Tools ----------------------------------------------------------------------


@mcp.tool(annotations={"readOnlyHint": True, "openWorldHint": True})
async def buscar_datasets_cdmx(
    texto: Annotated[
        str, Field(min_length=2, description="Tema a buscar, en español. Ej.: 'metro', 'calidad del aire'.")
    ],
    limite: Annotated[int, Field(ge=1, le=10)] = 5,
) -> dict:
    """Busca conjuntos de datos en el catálogo oficial datos.cdmx.gob.mx.

    Devuelve título, dependencia responsable, formatos disponibles y enlace de cada conjunto.
    Úsala para descubrir qué datos públicos existen sobre un tema; no devuelve los datos en sí.
    """
    try:
        async with httpx.AsyncClient(timeout=15) as cliente:
            respuesta = await cliente.get(f"{CKAN}/package_search", params={"q": texto, "rows": limite})
            respuesta.raise_for_status()
    except httpx.HTTPError as error:
        raise ToolError(f"No pude consultar datos.cdmx.gob.mx ({type(error).__name__}). Revisa la conexión a internet.")

    resultado = respuesta.json()["result"]
    return {
        "total_encontrados": resultado["count"],
        "mostrados": len(resultado["results"]),
        "conjuntos": [
            {
                "titulo": conjunto["title"],
                "dependencia": (conjunto.get("organization") or {}).get("title"),
                "formatos": sorted({r["format"] for r in conjunto["resources"] if r.get("format")}),
                "actualizado": conjunto["metadata_modified"][:10],
                "url": f"https://datos.cdmx.gob.mx/dataset/{conjunto['name']}",
            }
            for conjunto in resultado["results"]
        ],
    }


@mcp.tool(annotations=SOLO_LECTURA)
def buscar_estacion_metro(
    texto: Annotated[str, Field(min_length=2, description="Nombre o parte del nombre; acentos opcionales.")],
    linea: Annotated[Linea | None, Field(description="Filtra por línea si se conoce.")] = None,
) -> dict:
    """Encuentra estaciones del Metro CDMX por nombre y devuelve su nombre oficial, líneas,
    alcaldía, tipo y año de apertura. Úsala antes de consultar afluencia si el nombre es
    ambiguo o informal (p. ej. 'insurgentes' existe en Línea 1 e 'Insurgentes Sur' en Línea 12).
    """
    clave = clave_busqueda(texto)
    filtro, extra = (" AND linea = ?", [f"Línea {linea}"]) if linea else ("", [])
    aproximadas = False
    with conectar() as db:
        filas = db.execute(
            f"SELECT * FROM estaciones WHERE busqueda LIKE ?{filtro} ORDER BY estacion, linea LIMIT 20",
            [f"%{clave}%", *extra],
        ).fetchall()
        if not filas:
            aproximadas = True
            todas = [f[0] for f in db.execute(f"SELECT DISTINCT busqueda FROM estaciones WHERE 1{filtro}", extra)]
            for parecida in difflib.get_close_matches(clave, todas, n=3, cutoff=0.6):
                filas += db.execute(
                    f"SELECT * FROM estaciones WHERE busqueda = ?{filtro}", [parecida, *extra]
                ).fetchall()

    return {
        "coincidencias": [{k: f[k] for k in ("estacion", "linea", "alcaldia", "tipo", "anio_apertura")} for f in filas],
        "nota": "Sin coincidencias directas; se muestran nombres parecidos." if aproximadas else None,
    }


@mcp.tool(annotations=SOLO_LECTURA)
def afluencia_metro(
    estacion: Annotated[
        str | None, Field(description="Nombre de la estación. Omítelo para consultar una línea completa.")
    ] = None,
    linea: Annotated[Linea | None, Field(description="Código de línea. Obligatorio si no hay estación.")] = None,
    desde: Mes | None = None,
    hasta: Mes | None = None,
    agrupar_por: Literal["mes", "anio"] = "mes",
) -> dict:
    """Afluencia del Metro CDMX (personas que entran) por mes o por año, para una estación o una
    línea completa. Si se omiten fechas, devuelve los últimos 12 meses disponibles. En estaciones
    de transbordo sin línea indicada, suma todas sus líneas. Incluye avisos de calidad de datos:
    meses en cero (cierres) y duplicados de la fuente.
    """
    if estacion is None and linea is None:
        raise ToolError("Indica `estacion`, `linea` o ambas. Ej.: linea='12' o estacion='Pantitlán'.")

    with conectar() as db:
        desde, hasta = validar_periodo(db, desde, hasta)
        if estacion:
            filas_estacion = resolver_estacion(db, estacion, linea)
            lineas = sorted({f["linea"] for f in filas_estacion})
            alcance = f"{filas_estacion[0]['estacion']} ({', '.join(lineas)})"
            filtro, parametros = "estacion = ?", [filas_estacion[0]["estacion"]]
        else:
            lineas, alcance = [f"Línea {linea}"], f"Línea {linea} completa"
            filtro, parametros = "1", []
        meses = db.execute(
            f"""SELECT mes, SUM(afluencia) AS afluencia, MAX(dias) AS dias, MAX(registros > dias) AS duplicado
                FROM afluencia_mensual
                WHERE mes BETWEEN ? AND ? AND {filtro} AND linea IN ({", ".join("?" * len(lineas))})
                GROUP BY mes ORDER BY mes""",
            [desde, hasta, *parametros, *lineas],
        ).fetchall()

    serie: dict[str, dict] = {}
    for fila in meses:
        periodo = fila["mes"] if agrupar_por == "mes" else fila["mes"][:4]
        punto = serie.setdefault(periodo, {"periodo": periodo, "afluencia": 0, "dias_con_dato": 0})
        punto["afluencia"] += fila["afluencia"]
        punto["dias_con_dato"] += fila["dias"]

    con_servicio = [f for f in meses if f["afluencia"] > 0]
    dias_con_servicio = sum(f["dias"] for f in con_servicio)
    total = sum(f["afluencia"] for f in meses)
    notas = []
    if en_cero := [f["mes"] for f in meses if f["afluencia"] == 0]:
        notas.append(f"Afluencia 0 (sin servicio o cerrada): {'; '.join(agrupar_meses(en_cero))}.")
    if any(f["duplicado"] for f in meses):
        notas.append("La fuente trae registros duplicados en algún mes; detalles en el resource cdmx://fuentes.")
    return {
        "alcance": f"{alcance} · {desde} a {hasta} · por {agrupar_por}",
        "unidad": "personas que entran al Metro (afluencia)",
        "serie": list(serie.values()),
        "total": total,
        "promedio_diario_con_servicio": round(total / dias_con_servicio) if dias_con_servicio else None,
        "notas": notas,
        "fuente": FUENTE_AFLUENCIA,
    }


@mcp.tool(annotations=SOLO_LECTURA)
def ranking_estaciones_metro(
    desde: Mes | None = None,
    hasta: Mes | None = None,
    linea: Annotated[Linea | None, Field(description="Limita el ranking a una línea.")] = None,
    orden: Literal["mas_concurridas", "menos_concurridas"] = "mas_concurridas",
    limite: Annotated[int, Field(ge=1, le=20)] = 10,
) -> dict:
    """Ordena estaciones del Metro CDMX por afluencia total en un periodo (por defecto, los
    últimos 12 meses). Las estaciones de transbordo suman todas sus líneas salvo que se filtre
    una. Excluye estaciones sin servicio en todo el periodo (afluencia 0).
    """
    filtro, extra = (" AND linea = ?", [f"Línea {linea}"]) if linea else ("", [])
    with conectar() as db:
        desde, hasta = validar_periodo(db, desde, hasta)
        filas = db.execute(
            f"""SELECT estacion, GROUP_CONCAT(DISTINCT linea) AS lineas, SUM(afluencia) AS afluencia
                FROM afluencia_mensual WHERE mes BETWEEN ? AND ?{filtro}
                GROUP BY estacion HAVING SUM(afluencia) > 0
                ORDER BY afluencia {"DESC" if orden == "mas_concurridas" else "ASC"} LIMIT ?""",
            [desde, hasta, *extra, limite],
        ).fetchall()
        en_alcance = db.execute(
            f"SELECT COUNT(DISTINCT estacion) FROM afluencia_mensual WHERE mes BETWEEN ? AND ?{filtro}",
            [desde, hasta, *extra],
        ).fetchone()[0]

    return {
        "alcance": f"{'Línea ' + linea if linea else 'Toda la red'} · {desde} a {hasta}",
        "unidad": "personas que entran al Metro (afluencia)",
        "ranking": [
            {
                "posicion": i,
                "estacion": f["estacion"],
                "lineas": sorted(f["lineas"].split(",")),
                "afluencia": f["afluencia"],
            }
            for i, f in enumerate(filas, start=1)
        ],
        "estaciones_en_alcance": en_alcance,
        "fuente": FUENTE_AFLUENCIA,
    }


# --- Resource -------------------------------------------------------------------


@mcp.resource("cdmx://fuentes", mime_type="application/json")
def fuentes() -> str:
    """Procedencia, licencia, cobertura y limpieza aplicada a los datos locales."""
    with conectar() as db:
        contenido = {
            "fuentes": {f["clave"]: f["valor"] for f in db.execute("SELECT * FROM fuentes")},
            "limpieza": [dict(f) for f in db.execute("SELECT * FROM limpieza")],
        }
    return json.dumps(contenido, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    # 127.0.0.1: sólo tu máquina puede conectarse (no el Wi-Fi del evento).
    # host_origin_protection: rechaza peticiones de páginas web que apunten a localhost (DNS rebinding).
    mcp.run(transport="http", host="127.0.0.1", port=8765, host_origin_protection=True)
