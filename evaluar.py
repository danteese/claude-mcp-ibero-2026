"""Evalúa si Claude elige la tool correcta, con los argumentos correctos, para preguntas reales.

    uv run evaluar.py                  # evalúa el servidor que está corriendo en el puerto 8765
    uv run evaluar.py --modelo haiku

Primero levanta el servidor en otra terminal (`uv run servidor.py`). Cada caso de evals/casos.json abre una sesión de `claude -p` que sólo ve el servidor
del taller (--strict-mcp-config) y no puede usar otras herramientas (dontAsk). Un caso
pasa si Claude llama la tool esperada con los argumentos esperados; puede consultar otras
antes (p. ej. confirmar una estación). Las tools que exigen aprobación se bloquean en
dontAsk, así que el intento cuenta y no se escribe nada. No mide si la respuesta final
es correcta: eso es otra evaluación. Los casos cuya tool no existe en el servidor se omiten.
Consume tu cuota de Claude: unas pocas llamadas por caso.
"""

import argparse
import asyncio
import json
import shutil
import subprocess
import unicodedata
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

import httpx
from fastmcp import Client

RAIZ = Path(__file__).parent
PREFIJO = "mcp__cdmx__"


def normalizar(valor) -> str:
    texto = unicodedata.normalize("NFKD", str(valor).lower())
    return "".join(c for c in texto if not unicodedata.combining(c))


def correr_caso(caso: dict, configuracion: str, modelo: str | None) -> dict:
    comando = [
        shutil.which("claude"), "-p", caso["pregunta"],
        "--mcp-config", configuracion, "--strict-mcp-config",
        "--allowedTools", f"{PREFIJO}*", "--permission-mode", "dontAsk",
        "--output-format", "stream-json", "--verbose", "--no-session-persistence",
    ]  # fmt: skip
    if modelo:
        comando += ["--model", modelo]
    salida = subprocess.run(comando, capture_output=True, text=True, timeout=300, cwd=RAIZ, check=False)

    llamadas, respuesta = [], ""
    for linea in salida.stdout.splitlines():
        try:
            evento = json.loads(linea)
        except json.JSONDecodeError:
            continue
        if evento.get("type") == "assistant":
            for bloque in evento["message"].get("content", []):
                if bloque.get("type") == "tool_use":
                    llamadas.append((bloque["name"], bloque.get("input", {})))
        elif evento.get("type") == "result":
            respuesta = evento.get("result") or ""

    del_servidor = [(n.removeprefix(PREFIJO), a) for n, a in llamadas if n.startswith(PREFIJO)]
    esperada = next(((n, a) for n, a in del_servidor if n == caso["tool"]), None)
    elegida, argumentos = esperada or (del_servidor[0] if del_servidor else (None, {}))
    fallas = []
    if elegida != caso["tool"]:
        fallas.append(f"eligió {elegida}")
    elif caso.get("argumentos"):
        for clave, esperado in caso["argumentos"].items():
            if normalizar(esperado) not in normalizar(argumentos.get(clave, "")):
                fallas.append(f"{clave}={argumentos.get(clave)!r}")
    return {
        **caso,
        "elegida": elegida,
        "argumentos_usados": argumentos,
        "secuencia": [n for n, _ in llamadas],
        "aprobado": not fallas,
        "fallas": fallas,
        "respuesta": respuesta[:400],
        "error": salida.stderr[-400:] if salida.returncode else "",
    }


async def tools_del_servidor(url: str) -> set[str]:
    async with Client(url) as cliente:
        return {t.name for t in await cliente.list_tools()}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--url", default="http://127.0.0.1:8765/mcp", help="servidor MCP ya levantado")
    parser.add_argument("--casos", type=Path, default=RAIZ / "evals" / "casos.json")
    parser.add_argument("--modelo", help="alias o nombre de modelo para `claude --model`")
    parser.add_argument("--paralelo", type=int, default=4)
    args = parser.parse_args()
    if not shutil.which("claude"):
        raise SystemExit("No encontré `claude` en el PATH: este script usa Claude Code en modo no interactivo.")

    try:
        disponibles = asyncio.run(tools_del_servidor(args.url))
    except (httpx.HTTPError, OSError, RuntimeError) as error:
        raise SystemExit(
            f"No pude conectar con {args.url} ({type(error).__name__}). ¿Está corriendo `uv run servidor.py`?"
        )
    casos = json.loads(args.casos.read_text(encoding="utf-8"))
    aplicables = [c for c in casos if c["tool"] is None or c["tool"] in disponibles]
    print(f"{args.url}: {len(disponibles)} tools · {len(aplicables)} de {len(casos)} casos aplican\n")

    configuracion = json.dumps({"mcpServers": {"cdmx": {"type": "http", "url": args.url}}})
    with ThreadPoolExecutor(max_workers=args.paralelo) as grupo:
        resultados = list(grupo.map(lambda c: correr_caso(c, configuracion, args.modelo), aplicables))

    for r in resultados:
        marca = "✓" if r["aprobado"] else "✗"
        detalle = "" if r["aprobado"] else f"  ← {', '.join(r['fallas'])}"
        print(f"{marca} {r['pregunta'][:70]:<70} {r['elegida'] or '(ninguna)'}{detalle}")
        if r["error"]:
            print(f"    error: {r['error'].strip()[:200]}")
    aprobados = sum(r["aprobado"] for r in resultados)
    print(f"\n{aprobados}/{len(resultados)} casos con la tool y los argumentos esperados.")

    destino = RAIZ / "evals" / "resultados" / f"{datetime.now():%Y%m%d-%H%M%S}.json"
    destino.parent.mkdir(exist_ok=True)
    destino.write_text(json.dumps(resultados, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Detalle: {destino.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
