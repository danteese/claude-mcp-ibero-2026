"""Comprueba el entorno y, opcionalmente, que tu servidor cumple el contrato de un paso.

    uv run verificar.py                 # entorno: Python, datos, red, Claude Code
    uv run verificar.py 2               # entorno + servidor.py cumple el paso 2
    uv run verificar.py 3 --archivo pasos/03_accion.py

Usa un cliente MCP en memoria: llama a las tools igual que Claude, sin abrir procesos.
"""

import argparse
import asyncio
import importlib.util
import json
import logging
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

import httpx
from fastmcp import Client

RAIZ = Path(__file__).parent
fallas = 0


def ok(mensaje: str) -> None:
    print(f"  ✓ {mensaje}")


def falla(mensaje: str, ayuda: str) -> None:
    global fallas
    fallas += 1
    print(f"  ✗ {mensaje}\n      → {ayuda}")


def aviso(mensaje: str) -> None:
    print(f"  ! {mensaje}")


def revisar_entorno(paso: int) -> bool:
    print("Entorno")
    ok(f"Python {sys.version.split()[0]} (uv lo instaló si hacía falta)")

    base = RAIZ / "datos" / "cdmx.sqlite"
    if base.exists():
        with sqlite3.connect(f"{base.as_uri()}?mode=ro", uri=True) as db:
            filas, desde, hasta = db.execute("SELECT COUNT(*), MIN(mes), MAX(mes) FROM afluencia_mensual").fetchone()
        ok(f"datos/cdmx.sqlite: {filas:,} filas de afluencia, {desde} a {hasta}")
    elif paso >= 2:
        falla("falta datos/cdmx.sqlite", "ejecuta `uv run preparar.py`")
    else:
        aviso("datos/cdmx.sqlite aún no existe; se crea en el paso 2 con `uv run preparar.py`")

    en_linea = True
    for nombre, url in [
        ("datos.cdmx.gob.mx", "https://datos.cdmx.gob.mx/api/3/action/status_show"),
        ("Ecobici GBFS", "https://gbfs.mex.lyftbikes.com/gbfs/gbfs.json"),
    ]:
        try:
            httpx.get(url, timeout=8).raise_for_status()
            ok(f"red: {nombre} responde")
        except httpx.HTTPError as error:
            en_linea = False
            aviso(f"red: {nombre} no responde ({type(error).__name__}); las tools en vivo fallarán, las locales no")

    claude = shutil.which("claude")
    if claude:
        version = subprocess.run([claude, "--version"], check=False, capture_output=True, text=True).stdout.strip()
        ok(f"Claude Code {version}")
    else:
        aviso("no encontré `claude` en el PATH; puedes usar Claude Desktop (ver README)")
    return en_linea


def cargar_servidor(archivo: Path):
    especificacion = importlib.util.spec_from_file_location("servidor_del_taller", archivo)
    modulo = importlib.util.module_from_spec(especificacion)
    especificacion.loader.exec_module(modulo)
    return modulo


async def revisar_servidor(archivo: Path, paso: int, en_linea: bool) -> None:
    print(f"Servidor {archivo.relative_to(RAIZ)} · contrato del paso {paso}")
    modulo = cargar_servidor(archivo)
    temporal = tempfile.TemporaryDirectory()
    if hasattr(modulo, "BASE_REPORTES"):
        modulo.BASE_REPORTES = Path(temporal.name) / "reportes.sqlite"
    if hasattr(modulo, "MAPA_ECOBICI"):  # no reemplaza el mapa/ecobici.js de la persona
        modulo.MAPA_ECOBICI = Path(temporal.name) / "ecobici.js"

    async with Client(modulo.mcp) as cliente:
        tools = {t.name: t for t in await cliente.list_tools()}

        async def llamar(nombre: str, argumentos: dict):
            if nombre not in tools:
                falla(f"falta la tool {nombre}", f"compárala con pasos/0{paso}_*.py")
                return None
            return await cliente.call_tool(nombre, argumentos, raise_on_error=False)

        if en_linea:
            r = await llamar("buscar_datasets_cdmx", {"texto": "metro", "limite": 2})
            if r and not r.is_error and r.data["conjuntos"]:
                ok(f"buscar_datasets_cdmx encontró {r.data['total_encontrados']} conjuntos sobre 'metro'")
            elif r:
                falla("buscar_datasets_cdmx no devolvió conjuntos", f"{r.content[0].text if r.content else r}")
        else:
            aviso("sin red: omito buscar_datasets_cdmx")

        if paso >= 2:
            r = await llamar(
                "afluencia_metro", {"linea": "12", "desde": "2021-01", "hasta": "2021-12", "agrupar_por": "anio"}
            )
            if r and not r.is_error and r.data["total"] > 0 and any("0" in n for n in r.data["notas"]):
                ok("afluencia_metro suma la Línea 12 en 2021 y avisa de los meses en cero")
            elif r:
                falla(
                    "afluencia_metro no avisó del cierre de la Línea 12",
                    "revisa que devuelva `notas` con meses en cero",
                )

            r = await llamar("afluencia_metro", {"estacion": "insurgente"})
            texto = r.content[0].text if r and r.content else ""
            if r and r.is_error and "Insurgentes Sur" in texto:
                ok("un nombre ambiguo produce un error que ofrece las opciones")
            elif r:
                falla(
                    "'insurgente' no produjo un error con opciones",
                    "el error debe listar Insurgentes e Insurgentes Sur",
                )

            anotaciones = tools["buscar_estacion_metro"].annotations if "buscar_estacion_metro" in tools else None
            if anotaciones and anotaciones.read_only_hint:
                ok("las tools de consulta se declaran de solo lectura (readOnlyHint)")
            elif "buscar_estacion_metro" in tools:
                falla("buscar_estacion_metro no declara readOnlyHint", 'agrega annotations={"readOnlyHint": True}')

        if paso >= 3:
            registrar = tools.get("registrar_reporte")
            if registrar and (registrar.meta or {}).get("anthropic/requiresUserInteraction") is True:
                ok("registrar_reporte exige aprobación humana en cada llamada")
            elif registrar:
                falla(
                    "registrar_reporte no exige aprobación", 'agrega meta={"anthropic/requiresUserInteraction": True}'
                )

            argumentos = {
                "estacion": "Pantitlán",
                "linea": "A",
                "tipo": "limpieza",
                "descripcion": "Prueba de verificar.py",
            }
            primero = await llamar("registrar_reporte", argumentos)
            segundo = await llamar("registrar_reporte", argumentos)
            if primero and segundo and not primero.is_error and primero.data["folio"] == segundo.data["folio"]:
                ok("registrar_reporte es idempotente: el mismo reporte devuelve el mismo folio")
            elif primero:
                falla("registrar_reporte duplicó el reporte o falló", f"{(segundo or primero).content[0].text}")

            r = await llamar("registrar_reporte", {**argumentos, "linea": "2"})
            if r and r.is_error:
                ok("registrar_reporte rechaza una estación que no está en esa línea")
            elif r:
                falla("registrar_reporte aceptó Pantitlán en la Línea 2", "valida la estación con resolver_estacion")

        if paso >= 4:
            if en_linea:
                r = await llamar("ecobici_cerca_de_metro", {"estacion": "Insurgentes"})
                # mapa/index.html dibuja esta salida tal cual: sin coordenadas no hay capa de Ecobici.
                con_coordenadas = r and not r.is_error and "metro" in r.data
                con_coordenadas = con_coordenadas and all("lat" in c and "lon" in c for c in r.data["cicloestaciones"])
                if con_coordenadas:
                    ok(
                        f"ecobici_cerca_de_metro: {r.data['cicloestaciones_en_radio']} cicloestaciones a 500 m de "
                        "Insurgentes, con coordenadas para el mapa"
                    )
                elif r and not r.is_error:
                    falla("ecobici_cerca_de_metro no trae coordenadas", "agrega `metro` y lat/lon por cicloestación")
                elif r:
                    falla("ecobici_cerca_de_metro falló", r.content[0].text)

                r = await llamar("actualizar_mapa_ecobici", {"estacion": "Insurgentes"})
                archivo = Path(temporal.name) / "ecobici.js"
                if r and not r.is_error and archivo.exists():
                    contenido = archivo.read_text(encoding="utf-8").strip()
                    datos = json.loads(contenido.removeprefix("window.ECOBICI = ").removesuffix(";"))
                    ok(
                        f"actualizar_mapa_ecobici escribe mapa/ecobici.js ({len(datos['cicloestaciones'])} "
                        f"cicloestaciones) y le devuelve a Claude un resumen de {len(r.data)} campos"
                    )
                elif r and not r.is_error:
                    falla("actualizar_mapa_ecobici no escribió el archivo", "revisa que use MAPA_ECOBICI")
                elif r:
                    falla("actualizar_mapa_ecobici falló", r.content[0].text)
            else:
                aviso("sin red: omito ecobici_cerca_de_metro")
    temporal.cleanup()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("paso", nargs="?", type=int, choices=[1, 2, 3, 4], help="paso del taller a verificar")
    parser.add_argument("--archivo", type=Path, default=RAIZ / "servidor.py", help="servidor a revisar")
    args = parser.parse_args()

    en_linea = revisar_entorno(args.paso or 0)
    if args.paso:
        logging.getLogger("fastmcp").setLevel(logging.CRITICAL)  # los errores esperados ya se reportan arriba
        asyncio.run(revisar_servidor(args.archivo.resolve(), args.paso, en_linea))
    print("\nTodo en orden." if fallas == 0 else f"\n{fallas} comprobación(es) fallaron.")
    sys.exit(1 if fallas else 0)


if __name__ == "__main__":
    main()
