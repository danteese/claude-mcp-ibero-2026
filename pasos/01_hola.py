"""Paso 1 · Hola, datos abiertos.

Un servidor MCP con una sola tool: buscar conjuntos de datos en el portal
de datos abiertos de la CDMX (CKAN). Lo que Claude lee para decidir usarla:
el nombre de la función, el docstring y los tipos de los parámetros.

    uv run fastmcp list pasos/01_hola.py
    uv run fastmcp call pasos/01_hola.py buscar_datasets_cdmx texto=metro
"""

from typing import Annotated

import httpx
from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from pydantic import Field

CKAN = "https://datos.cdmx.gob.mx/api/3/action"

mcp = FastMCP(
    "cdmx",
    instructions="Datos abiertos de la Ciudad de México. Usa estas tools para buscar conjuntos de datos públicos de la CDMX.",
)


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


if __name__ == "__main__":
    # 127.0.0.1: sólo tu máquina puede conectarse (no el Wi-Fi del evento).
    # host_origin_protection: rechaza peticiones de páginas web que apunten a localhost (DNS rebinding).
    mcp.run(transport="http", host="127.0.0.1", port=8765, host_origin_protection=True)
