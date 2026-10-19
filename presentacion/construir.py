# /// script
# requires-python = ">=3.11"
# dependencies = ["python-pptx>=1.0", "pillow>=10"]
# ///
"""Construye la presentación del taller y la sube a Google Slides con `gws`.

    uv run presentacion/construir.py          # genera el .pptx, lo sube a Drive (convertido a Slides) y exporta un PDF
    uv run presentacion/construir.py --local  # solo genera presentacion/salida/taller-mcp.pptx

Narrativa (ver docs/storytelling.md): una pregunta como gancho, el contraste real entre Claude
sin herramientas y con MCP, quién soy, el porqué, los conceptos con su definición, la
construcción en cuatro pasos (el código se escribe en vivo; las láminas orientan), el mapa y el
llamado a crear. Cada lámina: un titular que afirma algo y una sola evidencia. Todas las láminas
son claras (el foro no garantiza que una lámina oscura se vea bien). Los tiempos van en las notas.
La última lámina es un glosario de consulta y no cuenta en los 40 minutos.

Se genera como .pptx porque la API de Slides solo inserta imágenes desde URLs públicas; al
subir el .pptx, Drive lo convierte con la foto y la captura incluidas, sin compartir nada.
Necesita presentacion/recursos/foto-dante.png y mapa-oct-2022.png (no se versionan).
"""

import argparse
import json
import re
import shutil
import subprocess
import time
from pathlib import Path

from PIL import Image, ImageDraw
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, MSO_AUTO_SIZE, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Emu, Pt

RAIZ = Path(__file__).parent
RECURSOS = RAIZ / "recursos"
SALIDA = RAIZ / "salida"
IDS = RAIZ / ".ids.json"
TITULO = "Datos abiertos over MCP · Taller Claude CDMX"
PPTX_MIME = "application/vnd.openxmlformats-officedocument.presentationml.presentation"
REPO = "https://github.com/danteese/claude-mcp-ibero-2026"
PUNTOS_DE_CONTROL = {2: "pasos/02_consulta.py", 3: "pasos/03_accion.py", 4: "pasos/04_final.py"}
PERSONAS_MCP = "‹N›"  # pendiente: personas distintas en tool_invocations de Djinn (ver docs/presentacion.md)

PAPEL, TINTA, GRIS, BORDE, BLANCO = "F7F7F3", "1F2A28", "5B6661", "D9DED7", "FFFFFF"
VERDE, VERDE_FONDO = "206449", "E6F0E6"
AZUL, AZUL_FONDO = "305B80", "E8EFF6"
OCRE, OCRE_FONDO = "8A5A2B", "F4EBDD"
ROJO, ROJO_FONDO = "A3412A", "F8E9E4"
SERIF, SANS, MONO = "Georgia", "Inter", "Roboto Mono"
MARCAS = re.compile(r"(\*\*.+?\*\*|==.+?==)")


def color(hexa: str) -> RGBColor:
    return RGBColor.from_string(hexa)


def sin_estilo_del_tema(forma) -> None:
    """Quita el <p:style> que python-pptx agrega: apunta al estilo de efectos del tema (con sombra
    exterior) y Google Slides lo aplica al convertir, aunque la forma pida no tener sombra."""
    estilo = forma._element.find(qn("p:style"))
    if estilo is not None:
        forma._element.remove(estilo)


class Deck:
    def __init__(self):
        self.prs = Presentation()
        self.prs.slide_width, self.prs.slide_height = Emu(9144000), Emu(5143500)  # 720 × 405 pt
        self.minutos = 0.0

    def lamina(self, notas: str, minutos: float, seccion="", paso=0, oculta=False):
        s = self.prs.slides.add_slide(self.prs.slide_layouts[6])
        if oculta:
            s._element.set("show", "0")
        s.background.fill.solid()
        s.background.fill.fore_color.rgb = color(PAPEL)
        s.notes_slide.notes_text_frame.text = f"[{minutos:g} min]\n{notas}" if minutos else notas
        self.minutos += minutos
        if seccion:
            self.texto(s, 40, 20, 420, 16, seccion.upper(), 9, GRIS, MONO)
        if paso:
            self.progreso(s, paso)
            recordatorio = "servidor.py ya es el paso 1" if paso == 1 else f"cp {PUNTOS_DE_CONTROL[paso]} servidor.py"
            self.texto(s, 250, 21, 340, 14, recordatorio, 8.5, GRIS, MONO, alinear="der")
        return s

    def texto(self, s, x, y, w, h, contenido, tam=15, tinta=TINTA, fuente=SANS, negrita=False,
              alinear="izq", vertical="arriba", interlineado=1.12, acento=VERDE, espacio=0):  # fmt: skip
        """Texto con marcas: **negrita** y ==acento==. Cada línea es un párrafo."""
        caja = s.shapes.add_textbox(Pt(x), Pt(y), Pt(w), Pt(h))
        tf = caja.text_frame
        tf.word_wrap, tf.auto_size = True, MSO_AUTO_SIZE.NONE
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = Pt(0)
        anclas = {"arriba": MSO_ANCHOR.TOP, "medio": MSO_ANCHOR.MIDDLE, "abajo": MSO_ANCHOR.BOTTOM}
        tf.vertical_anchor = anclas[vertical]
        self._parrafos(tf, contenido, tam, tinta, fuente, negrita, alinear, interlineado, acento, espacio)
        return caja

    def _parrafos(self, tf, contenido, tam, tinta, fuente, negrita, alinear, interlineado, acento, espacio):
        for n, linea in enumerate(contenido.split("\n")):
            p = tf.paragraphs[0] if n == 0 else tf.add_paragraph()
            p.alignment = {"izq": PP_ALIGN.LEFT, "centro": PP_ALIGN.CENTER, "der": PP_ALIGN.RIGHT}[alinear]
            p.line_spacing = interlineado
            p.space_after = Pt(espacio)
            for k, segmento in enumerate(linea.split("\v")):
                if k:
                    p.add_line_break()
                for trozo in MARCAS.split(segmento) or [""]:
                    if trozo == "" and segmento:
                        continue
                    es_negrita, es_acento = trozo.startswith("**"), trozo.startswith("==")
                    r = p.add_run()
                    r.text = trozo[2:-2] if es_negrita or es_acento else trozo
                    r.font.name, r.font.size = fuente, Pt(tam)
                    r.font.bold = negrita or es_negrita or es_acento
                    r.font.color.rgb = color(acento if es_acento else tinta)

    def caja(self, s, x, y, w, h, relleno=BLANCO, borde=None, radio=0.08, forma=MSO_SHAPE.ROUNDED_RECTANGLE,
             contenido="", tam=13, tinta=TINTA, alinear="centro", vertical="medio", margen=10, negrita=False):  # fmt: skip
        sh = s.shapes.add_shape(forma, Pt(x), Pt(y), Pt(w), Pt(h))
        if forma == MSO_SHAPE.ROUNDED_RECTANGLE:
            sh.adjustments[0] = radio
        sin_estilo_del_tema(sh)
        sh.fill.solid()
        sh.fill.fore_color.rgb = color(relleno)
        if borde:
            sh.line.color.rgb, sh.line.width = color(borde), Pt(1)
        else:
            sh.line.fill.background()
        tf = sh.text_frame
        tf.word_wrap, tf.auto_size = True, MSO_AUTO_SIZE.NONE
        tf.margin_left = tf.margin_right = Pt(margen)
        tf.margin_top = tf.margin_bottom = Pt(margen * 0.6)
        tf.vertical_anchor = {"arriba": MSO_ANCHOR.TOP, "medio": MSO_ANCHOR.MIDDLE}[vertical]
        if contenido:
            self._parrafos(tf, contenido, tam, tinta, SANS, negrita, alinear, 1.15, VERDE, 0)
        return sh

    def definicion(self, s, x, y, w, h, termino, texto, tam=11.5):
        """Tarjeta de definición: siempre igual, para que la sala aprenda a reconocerla."""
        self.caja(s, x, y, w, h, BLANCO, BORDE, radio=0.06)
        self.texto(s, x + 14, y + 8, w - 24, 12, "DEFINICIÓN", 7.5, VERDE, MONO, negrita=True)
        self.texto(s, x + 14, y + 22, w - 24, h - 28, f"**{termino}**: {texto}", tam, TINTA, interlineado=1.2)

    def linea(self, s, x1, y1, x2, y2, tinta=GRIS, grosor=1.5, flecha=False):
        c = s.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Pt(x1), Pt(y1), Pt(x2), Pt(y2))
        sin_estilo_del_tema(c)
        c.line.color.rgb, c.line.width = color(tinta), Pt(grosor)
        if flecha:
            ln = c.line._get_or_add_ln()
            ln.append(ln.makeelement(qn("a:tailEnd"), {"type": "triangle", "w": "med", "len": "med"}))
        return c

    def codigo(self, s, x, y, w, h, texto, tam=12.5, resaltar=()):
        """Bloque de código; `resaltar` pinta en verde lo que lee el modelo."""
        self.caja(s, x, y, w, h, BLANCO, BORDE, radio=0.04)
        caja = s.shapes.add_textbox(Pt(x + 14), Pt(y + 12), Pt(w - 28), Pt(h - 24))
        tf = caja.text_frame
        tf.word_wrap, tf.auto_size = False, MSO_AUTO_SIZE.NONE
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = Pt(0)
        patron = re.compile("(" + "|".join(re.escape(r) for r in resaltar) + ")") if resaltar else None
        for n, linea in enumerate(texto.split("\n")):
            p = tf.paragraphs[0] if n == 0 else tf.add_paragraph()
            p.line_spacing = 1.05
            for trozo in patron.split(linea) if patron else [linea]:
                r = p.add_run()
                r.text = trozo
                r.font.name, r.font.size = MONO, Pt(tam)
                es_resaltado = bool(patron and trozo in resaltar)
                r.font.bold = es_resaltado
                r.font.color.rgb = color(VERDE if es_resaltado else TINTA)

    def titular(self, s, texto, y=40, h=66, tam=25, w=640):
        if len(texto) > 80:
            raise ValueError(f"Titular de más de dos líneas: {texto!r}")
        self.texto(s, 40, y, w, h, texto, tam, TINTA, SERIF, interlineado=1.05)

    def progreso(self, s, actual):
        for n in range(1, 5):
            x = 600 + (n - 1) * 22
            relleno, tinta = (VERDE, BLANCO) if n == actual else ((VERDE_FONDO, VERDE) if n < actual else (PAPEL, GRIS))
            self.caja(s, x, 18, 16, 16, relleno, None if n <= actual else BORDE, forma=MSO_SHAPE.OVAL,
                      contenido=str(n), tam=8, tinta=tinta, margen=0, negrita=True)  # fmt: skip

    def chip(self, s, x, y, texto, relleno=VERDE, tinta=BLANCO, tam=11, ancho=None):
        ancho = ancho or len(texto) * tam * 0.58 + 24
        self.caja(s, x, y, ancho, 24, relleno, contenido=texto, tam=tam, tinta=tinta, margen=6, radio=0.5)
        return ancho

    def imagen(self, s, ruta, x, y, w=None, h=None):
        return s.shapes.add_picture(str(ruta), Pt(x), Pt(y), Pt(w) if w else None, Pt(h) if h else None)


def foto_circular() -> Path:
    destino = SALIDA / "foto-circular.png"
    foto = Image.open(RECURSOS / "foto-dante.png").convert("RGBA")
    lado = min(foto.size)
    izquierda, arriba = (foto.width - lado) // 2, (foto.height - lado) // 2
    foto = foto.crop((izquierda, arriba, izquierda + lado, arriba + lado)).resize((720, 720), Image.LANCZOS)
    mascara = Image.new("L", foto.size, 0)
    ImageDraw.Draw(mascara).ellipse((0, 0, 719, 719), fill=255)
    foto.putalpha(mascara)
    foto.save(destino)
    return destino


# --- Contenido ------------------------------------------------------------------


def tablero(d: Deck, s, entregables: list[str], ideas: list[str], hecho: bool) -> None:
    """Apertura y recap usan la misma composición: la sala reconoce la lámina y ve lo que cambió."""
    d.texto(s, 40, 98, 280, 20, "Lo que construiste" if hecho else "Lo que vas a tener", 15, AZUL, negrita=True)
    for n, texto in enumerate(entregables):
        y = 130 + n * 54
        d.caja(
            s, 40, y + 2, 18, 18, VERDE if hecho else BLANCO, None if hecho else BORDE, forma=MSO_SHAPE.OVAL,
            contenido="✓" if hecho else "", tam=10, tinta=BLANCO, margen=0, negrita=True,
        )  # fmt: skip
        d.texto(s, 68, y, 252, 48, texto, 11.5, TINTA, interlineado=1.2)
    titulo = "Lo que te llevas" if hecho else "Lo que vas a poder responder"
    d.texto(s, 352, 98, 328, 20, titulo, 15, VERDE, negrita=True)
    for n, texto in enumerate(ideas):
        y = 130 + n * 46
        d.texto(s, 352, y, 20, 18, str(n + 1), 12, VERDE, SERIF, negrita=True)
        d.texto(s, 374, y, 306, 42, texto, 11 if hecho else 12, TINTA, interlineado=1.2)


def construir_deck() -> Deck:
    faltan = [
        n
        for n in (
            "foto-dante.png",
            "mapa-portada.png",
            "mapa-oct-2022.png",
            "meme-mcp.png",
            "piezas-mcp.png",
            "qr-repo.png",
        )
        if not (RECURSOS / n).exists()
    ]
    if faltan:
        raise SystemExit(
            f"Faltan imágenes en {RECURSOS} (no se versionan; ver docs/presentacion.md): {', '.join(faltan)}"
        )
    d = Deck()
    foto = foto_circular()

    # 1 · Portada
    s = d.lamina(
        "Bienvenida. Al terminar, cada quien tendrá un servidor MCP propio conectado a Claude Code, "
        "que consulta datos abiertos reales de la CDMX y ejecuta una acción con controles. No hay que instalar "
        "nada más que uv. La imagen es el dato con el que vamos a trabajar: la afluencia del Metro en julio de 2026, "
        "cada círculo es una estación y su tamaño, la gente que entra al día. El más grande es Pantitlán: guárdenlo, "
        "porque es la pregunta que viene.",
        0.5,
    )
    d.texto(s, 48, 44, 320, 16, "CLAUDE FOR AI ENGINEERING · CDMX · IBERO", 9, VERDE, MONO, negrita=True)
    d.texto(s, 48, 96, 320, 110, "Datos abiertos\nover MCP", 44, TINTA, SERIF, interlineado=1.0)
    d.texto(s, 48, 212, 320, 52, "Claude que consulta fuentes reales", 19, VERDE, SERIF, interlineado=1.1)
    d.texto(s, 48, 254, 320, 18, "Taller práctico · Python + FastMCP · 40 min", 12, GRIS)
    d.imagen(s, foto, 48, 318, 46, 46)
    d.texto(s, 106, 321, 260, 18, "Dante Bazaldua", 13, TINTA, negrita=True)
    d.texto(s, 106, 340, 260, 18, "Cofundador y CTO de Spot2.mx", 11.5, GRIS)
    d.imagen(s, RECURSOS / "mapa-portada.png", 380, 30, h=332)
    d.texto(s, 380, 372, 300, 12, "Afluencia del Metro, julio de 2026 · datos.cdmx.gob.mx", 8, GRIS, MONO)

    # 2 · Meme de apertura (lo agregó Dante en Google Slides)
    s = d.lamina(
        "Meme de apertura, unos segundos: Claude Code solo y Claude Code con servidores MCP. Fuente: Nikolay "
        "Miroshnychenko, «Rapid UI prototyping with Figma + Android MCP servers» (Medium).",
        0,
    )
    s.background.fill.fore_color.rgb = color(BLANCO)
    d.imagen(s, RECURSOS / "meme-mcp.png", 61, 29, 587, 346)
    d.texto(
        s, 61, 372, 517, 27,
        "https://nikolaymiroshnychenko.medium.com/rapid-ui-prototyping-with-figma-android-mcp-servers-2f42fd7184cb",
        8, GRIS, MONO,
    )  # fmt: skip

    # 3 · La pregunta, dentro de una lluvia de preguntas con dato público
    s = d.lamina(
        "Antes de la pregunta, deja que la sala lea la lluvia unos segundos. Son preguntas que cualquiera le haría a "
        "su ciudad, y todas tienen detrás un conjunto de datos público en datos.cdmx.gob.mx: reportes de agua "
        "(Sacmex), llamadas al 911 e incidentes viales (C5), afluencia del Cablebús (Transportes Eléctricos), "
        "víctimas en carpetas de investigación (FGJ), denuncias por ruido (PAOT), presupuesto de egresos 2024, WiFi "
        "gratuito, solicitudes al *0311, nombres y matrimonios del Registro Civil, índice de calidad del aire "
        "(Sedema) y viajes de Ecobici. Lee dos o tres en voz alta. Luego la de en medio: ¿cuánta gente entró a "
        "Pantitlán en julio de 2026? Pide que levanten la mano: primero quién cree que más de 3 millones, luego "
        "quién cree que menos. Casi nadie sabe el número, y Claude tampoco. No digas la respuesta: está en la "
        "siguiente lámina.",
        1,
    )
    CLARO = "8E9792"
    lluvia = [
        (40, 30, 250, "¿Qué alcaldía reporta más falta de agua?", 12.5, GRIS),
        (318, 34, 190, "¿A qué hora se llama más al 911?", 10.5, CLARO),
        (530, 28, 150, "¿Cuánta gente sube al Cablebús un domingo?", 11, GRIS),
        (70, 80, 220, "¿Dónde hay más choques los viernes?", 10.5, CLARO),
        (300, 76, 284, "¿Cuántos meses estuvo cerrada la Línea 12?", 13, GRIS),
        (596, 74, 104, "¿Qué nombre se registra más en Álvaro Obregón?", 10, CLARO),
        (34, 140, 100, "¿Dónde hay WiFi gratis cerca de mí?", 11, GRIS),
        (34, 200, 100, "¿Qué mes tiene el peor aire?", 10, CLARO),
        (592, 136, 108, "¿Las mujeres usan más Ecobici que antes?", 11, GRIS),
        (592, 196, 108, "¿Cuántas denuncias por ruido hay en mi colonia?", 10, CLARO),
        (40, 254, 350, "¿Qué estación del Metro perdió más gente desde 2019?", 12.5, GRIS),
        (404, 258, 276, "¿Qué es lo que más le piden al gobierno por *0311?", 11, CLARO),
        (90, 294, 240, "¿Cuánto presupuesto tiene mi alcaldía?", 11, CLARO),
        (360, 290, 320, "¿Hay Ecobici libre cerca de mi Metro ahorita?", 12.5, GRIS),
        (40, 330, 280, "¿En qué colonia hay más robos a transeúnte?", 11, GRIS),
        (420, 332, 260, "¿Cuántas bodas hay cada 14 de febrero?", 10.5, CLARO),
    ]
    for x, y, w, pregunta, tam, tinta in lluvia:
        d.texto(s, x, y, w, 50, pregunta, tam, tinta)
    d.texto(
        s, 140, 126, 440, 66, "¿Cuánta gente entró a la estación\nPantitlán en julio de 2026?", 27, TINTA, SERIF,
        alinear="centro", interlineado=1.05,
    )  # fmt: skip
    d.texto(
        s, 140, 200, 440, 20, "Levanten la mano: ¿más o menos de 3 millones?", 14, VERDE, negrita=True, alinear="centro"
    )
    d.texto(
        s,
        40,
        382,
        640,
        12,
        "Cada pregunta tiene detrás un conjunto de datos público · datos.cdmx.gob.mx",
        8.5,
        GRIS,
        MONO,
    )

    # 4 · La respuesta (se revela después de que la sala vota)
    s = d.lamina(
        "Revela. 4,623,233 personas entraron a Pantitlán en julio de 2026: unas 149 mil al día. ¿Quién dijo más de "
        "3 millones? Acertaron. Dos precisiones: es la suma de sus cuatro líneas (1, 5, 9 y A), y la afluencia cuenta "
        "entradas, no a la gente dentro de los trenes. Es la estación más concurrida de la red: 1.6 veces la segunda, "
        "Constitución de 1917. Todo salió de las tools que van a escribir hoy. Pregunta puente: ¿y Claude lo sabía?",
        0.5,
        seccion="La respuesta",
    )
    # Salida de afluencia_metro y ranking_estaciones_metro (pasos/04_final.py) para julio de 2026.
    total, por_dia = 4623233, 149137
    lineas = [("1", 1062637), ("5", 1245423), ("9", 1405456), ("A", 909717)]
    ranking = [
        ("Pantitlán", 4623233),
        ("Constitución de 1917", 2845476),
        ("Cuatro Caminos", 2679667),
        ("Indios Verdes", 2417589),
        ("Tacubaya", 2162892),
    ]
    if sum(n for _, n in lineas) != total or ranking[0][1] != total:
        raise ValueError("Las cifras de Pantitlán no cuadran")
    d.texto(s, 40, 58, 300, 18, "Pantitlán · julio de 2026", 13, GRIS)
    d.texto(s, 40, 78, 320, 70, f"{total:,}", 58, VERDE, SERIF)
    d.texto(s, 40, 150, 300, 44, f"personas entraron en 31 días\n**≈{por_dia:,} al día**", 16, TINTA, interlineado=1.2)
    d.texto(s, 40, 206, 300, 20, "Quienes dijeron «más de 3 millones», acertaron.", 12.5, VERDE, negrita=True)
    d.texto(s, 40, 244, 300, 16, "Suma sus cuatro líneas", 11, TINTA, negrita=True)
    x = 40.0
    for linea, entradas in lineas:
        ancho = entradas / total * 290
        d.caja(
            s, x, 266, ancho - 2, 26, VERDE, radio=0.12, contenido=f"{linea} · {entradas / 1e6:.2f} M",
            tam=9, tinta=BLANCO, margen=2, negrita=True,
        )  # fmt: skip
        x += ancho
    d.texto(s, 40, 296, 300, 14, "línea · millones de entradas en el mes", 9, GRIS)
    d.texto(s, 380, 58, 300, 18, "Las 5 estaciones con más entradas", 12, TINTA, negrita=True)
    d.texto(s, 380, 76, 300, 14, "julio de 2026 · entradas en el mes", 9.5, GRIS)
    for n, (estacion, entradas) in enumerate(ranking):
        y, ancho, primera = 104 + n * 36, entradas / total * 110, n == 0
        d.texto(s, 380, y + 1, 118, 16, estacion, 10, TINTA, negrita=primera)
        d.caja(s, 500, y, ancho, 18, VERDE if primera else "C9CFCB", radio=0.12)
        d.texto(s, 506 + ancho, y + 2, 80, 16, f"{entradas:,}", 10, TINTA if primera else GRIS, negrita=primera)
    segunda = ranking[0][1] / ranking[1][1]
    d.texto(s, 380, 290, 300, 30, f"Pantitlán recibe {segunda:.1f} veces lo que la segunda.", 11, GRIS)
    d.texto(s, 40, 336, 640, 22, "**¿Y Claude lo sabía?** Veamos qué contesta con y sin herramientas.", 14, TINTA)
    d.texto(
        s, 40, 384, 640, 12,
        "Afluencia diaria del Metro CDMX · datos.cdmx.gob.mx · CC-BY-4.0 · afluencia = entradas, no ocupación de trenes",
        8.5, GRIS, MONO,
    )  # fmt: skip

    # 5 · El contraste
    s = d.lamina(
        "Ya saben el número. ¿Y Claude? Misma pregunta, mismo modelo, dos sesiones de claude -p del 17 de octubre. "
        "Sin herramientas, dice honestamente que no sabe y estima, sin fuente: no la podemos verificar. Con el "
        "servidor que van a construir hoy, da el número exacto con su fuente. Esa diferencia es todo el taller: "
        "pasar de «estimo» a «aquí está el dato y de dónde sale».",
        0.5,
        seccion="El problema",
    )
    d.titular(s, "Sin herramientas, Claude estima. Con tu servidor MCP, responde con el dato.")
    d.caja(s, 40, 120, 310, 214, BLANCO, BORDE, radio=0.05)
    d.texto(s, 58, 136, 280, 16, "Claude sin herramientas", 11, GRIS, negrita=True)
    d.texto(
        s, 58, 160, 276, 130,
        "«No puedo darte la cifra: julio de 2026 es posterior a lo que sé. Como referencia aproximada, unos "
        "4 a 5 millones de entradas al mes… pero eso es una estimación.»",
        14.5, GRIS, interlineado=1.2,
    )  # fmt: skip
    d.chip(s, 58, 298, "estimación", ROJO_FONDO, ROJO, 10)
    d.caja(s, 370, 120, 310, 214, VERDE_FONDO, VERDE, radio=0.05)
    d.texto(s, 388, 136, 280, 16, "Claude + tu servidor MCP", 11, VERDE, negrita=True)
    d.texto(
        s, 388, 160, 276, 130,
        "«En julio de 2026 entraron ==4,623,233 personas== a Pantitlán, contando sus cuatro líneas. Unas "
        "149,137 al día. La fuente es datos.cdmx.gob.mx.»",
        14.5, TINTA, interlineado=1.2,
    )  # fmt: skip
    d.chip(s, 388, 298, "dato con fuente", VERDE, BLANCO, 10)
    d.texto(
        s,
        40,
        352,
        640,
        30,
        "Misma pregunta y mismo modelo, dos sesiones de claude -p (17-oct-2026). La cifra coincide con la base del taller.",
        9.5,
        GRIS,
    )

    # 6 · Qué te llevas (apertura; se refleja en el recap)
    s = d.lamina(
        "Antes de entrar, el contrato del taller. A la izquierda, lo que van a tener en su laptop al terminar: un "
        "servidor MCP propio con ocho tools, un resource y un prompt sobre el Metro; conectado a Claude Code; con "
        "una acción que escribe y pide aprobación; una evaluación de diez preguntas y un mapa que Claude extiende. "
        "A la derecha, las cinco preguntas que van a poder responder. Al final volvemos a esta misma lámina, ya con "
        "las respuestas. Si en algún momento se pierden, esta es la brújula.",
        1,
        seccion="Qué te llevas",
    )
    d.titular(s, "Al terminar tendrás un servidor MCP conectado a CC")
    tablero(
        d, s,
        [
            "Un servidor MCP en tu laptop: 8 tools, un resource y un prompt sobre el Metro",
            "Conectado a Claude Code por HTTP, con una acción que escribe y pide tu aprobación",
            "Una evaluación de 10 preguntas que mide si Claude elige bien",
            "Un mapa de 16 años del Metro que Claude extiende con tus tools",
        ],
        [
            "¿Qué es una tool y qué agrega MCP?\n(Solo repaso, ya se vio antes)",
            "¿Cuándo conviene MCP y cuándo una CLI o una API?",
            "¿Cómo diseño tools que el modelo elija bien?",
            "¿Dónde van los controles si una tool escribe?",
            "¿Cómo sé si Claude elige bien?",
        ],
        hecho=False,
    )  # fmt: skip
    d.texto(
        s,
        40,
        362,
        640,
        18,
        "Todo queda en el repo y lo repites en casa con uv. Al final volvemos a esta lámina.",
        11.5,
        GRIS,
    )

    # 7 · Quién soy (solo lo personal; Spot2 va aparte)
    s = d.lamina(
        "Me presento en medio minuto: quién soy y de dónde vengo. Lo que hemos hecho en Spot2 viene después de la lámina del LLM.",
        0.5,
        seccion="Quién soy",
    )
    d.imagen(s, foto, 40, 100, 170, 170)
    d.texto(s, 240, 100, 440, 40, "Dante Bazaldua", 32, TINTA, SERIF)
    d.texto(s, 240, 146, 440, 24, "Cofundador y CTO de **Spot2.mx**", 17, TINTA)
    d.texto(
        s, 240, 190, 429, 120,
        "Ingeniería en Tecnologías de Cómputo y Telecomunicaciones y Maestría en Gestión de la Innovación "
        "Tecnológica · Ibero\nSoftware para el experimento CMS del CERN\vMicrobioma en UC San Diego\n"
        "Profesor en la Ibero: algoritmos, ciberseguridad y sistemas de comunicaciones",
        13, GRIS, interlineado=1.25, espacio=8,
    )  # fmt: skip
    d.texto(s, 40, 376, 640, 14, "spot2.mx · stdout.mx · linkedin.com/in/dantebh", 9, GRIS, MONO)

    # 8 · Qué es un LLM y por qué necesita herramientas
    s = d.lamina(
        "Primera definición: un LLM, modelo de lenguaje grande, como Claude, recibe texto y predice el texto que "
        "sigue. Eso es todo. Por sí solo no consulta internet, ni bases de datos, ni ejecuta nada. De ahí salen "
        "dos huecos: no sabe lo que pasó después de su entrenamiento ni lo que vive en tus sistemas (saber), y no "
        "puede escribir, enviar ni calcular con garantía (hacer). Una herramienta es una forma de dárselo.",
        1,
        seccion="El porqué",
    )
    d.titular(s, "Un modelo convierte texto en texto: saber y actuar hay que dárselo", y=52, h=40, tam=21)
    d.definicion(
        s, 40, 108, 640, 60, "LLM (modelo de lenguaje grande)",
        "un modelo que, dado un token, predice el token que sigue. Por sí solo no consulta ni ejecuta nada.",
    )  # fmt: skip
    d.caja(s, 160, 184, 110, 40, OCRE_FONDO, contenido="texto", tam=14, tinta=OCRE)
    d.caja(s, 300, 178, 120, 52, TINTA, contenido="**LLM**", tam=17, tinta=PAPEL)
    d.caja(s, 450, 184, 110, 40, OCRE_FONDO, contenido="texto", tam=14, tinta=OCRE)
    d.linea(s, 272, 204, 298, 204, GRIS, 2, True)
    d.linea(s, 422, 204, 448, 204, GRIS, 2, True)
    for x, etiqueta, texto in [
        (
            40,
            "Le falta SABER",
            "lo que pasó después de su entrenamiento · lo que vive en tus sistemas · de dónde sale cada cifra",
        ),
        (370, "Le falta HACER", "escribir, enviar, registrar · calcular con garantía · consultar en el momento"),
    ]:
        d.caja(s, x, 244, 310, 94, BLANCO, BORDE, radio=0.05)
        d.texto(s, x + 18, 255, 274, 18, etiqueta, 13, ROJO, negrita=True)
        d.texto(s, x + 18, 278, 274, 56, texto, 12, TINTA, interlineado=1.2)
    d.texto(s, 42, 358, 640, 22, "La forma de dárselo es una herramienta: una ==tool==.", 16, TINTA)

    # 9 · Spot2: lo que hemos implementado con MCP
    s = d.lamina(
        "En Spot2 esto no es teoría; es como trabajamos. Tenemos cuatro servidores MCP en producción. Djinn es la "
        "puerta del equipo a los datos: 44 tools de solo lectura sobre siete fuentes, Metabase y un glosario de "
        "negocio; cada consulta queda auditada (quién, qué tool, cuánto tardó). Colossu es la operación "
        "inmobiliaria: contratos, CRM, pipeline, formularios y tareas, 65 tools, ya en la spec 2026-07-28. Spot2.mx "
        "vive dentro de ChatGPT para buscar inmuebles comerciales. Argos guarda archivos, anotaciones y skills. "
        f"Hoy {PERSONAS_MCP} personas de Spot2 trabajan con ellos: te conectas con tu cuenta de Google de Spot2 desde "
        "Claude o ChatGPT, y Grok viene pronto. Pythia, nuestro agente en Google Chat, también es cliente MCP. Se "
        "volvió fundamental porque cualquiera pregunta por leads, búsquedas o contratos en lenguaje natural, sin "
        "esperar a que alguien escriba el SQL. Y cambió cómo diseñamos: API/MCP first. Una capacidad nueva nace con "
        "su endpoint y su tool encima de la misma acción; por ejemplo, la carga masiva de contratos es la misma "
        "acción desde la web y desde Claude. Lo que construyen hoy es una versión chiquita de esto, con datos públicos.",
        1,
        seccion="Quién soy · Spot2",
    )
    d.titular(s, "En Spot2, cada capacidad nace con su API y su MCP")
    d.texto(s, 40, 102, 180, 16, "Dónde lo usamos", 12, VERDE, negrita=True)
    d.texto(s, 248, 102, 200, 16, "Algunos servidores MCP", 12, AZUL, negrita=True)
    centros = [148 + n * 50 for n in range(4)]
    clientes = [("Claude", True), ("ChatGPT", True), ("Pythia", True), ("Otros Agentes", False)]
    for cy, (nombre, activo) in zip(centros, clientes):
        d.linea(s, 140, cy, 176, 223, VERDE if activo else "C9CFCB", 1.75 if activo else 1)
        d.caja(
            s, 40, cy - 12, 100, 24, VERDE_FONDO if activo else BLANCO, None if activo else BORDE, radio=0.5,
            contenido=nombre, tam=10.5, tinta=VERDE if activo else GRIS, margen=4,
        )  # fmt: skip
    d.caja(s, 176, 208, 50, 30, TINTA, contenido="**MCP**", tam=12, tinta=PAPEL, margen=2, radio=0.5)
    servidores = [
        ("**Djinn** · datos", "44 tools: 7 fuentes y Metabase"),
        ("**Colossu** · operación", "65 tools: contratos, CRM y más"),
        ("**Spot2.mx** · en ChatGPT", "Toda la plataforma disponible para agentes"),
        ("**Argos** · archivos", "archivos, anotaciones y skills"),
    ]
    for cy, (nombre, texto) in zip(centros, servidores):
        d.linea(s, 226, 223, 248, cy, AZUL, 1.75)
        d.caja(s, 248, cy - 21, 188, 42, AZUL_FONDO, radio=0.12)
        d.texto(s, 260, cy - 16, 170, 16, nombre, 11, AZUL)
        d.texto(s, 260, cy + 1, 170, 14, texto, 9.5, TINTA)
    d.texto(s, 40, 326, 400, 12, "Pythia: nuestro agente en Google Chat, también cliente MCP", 8.5, GRIS)
    d.caja(s, 464, 100, 216, 90, BLANCO, BORDE, radio=0.06)
    d.texto(
        s, 476, 113, 192, 40,
        "En Spot2 todos los sistemas deben de poder ser accesibles por agentes (first-class citizens)",
        12, TINTA, interlineado=1.2,
    )  # fmt: skip
    d.texto(s, 464, 204, 216, 18, "Diseñamos API/MCP first", 12, TINTA, negrita=True)
    d.caja(s, 464, 230, 104, 24, AZUL_FONDO, radio=0.5, contenido="Endpoint REST", tam=10, tinta=AZUL, margen=4)
    d.caja(s, 464, 266, 104, 24, VERDE_FONDO, radio=0.5, contenido="Tool MCP", tam=10, tinta=VERDE, margen=4)
    d.linea(s, 568, 242, 598, 254, GRIS, 1.5, True)
    d.linea(s, 568, 278, 598, 266, GRIS, 1.5, True)
    d.caja(s, 600, 236, 80, 48, TINTA, contenido="Una sola\nacción", tam=10.5, tinta=PAPEL, margen=4, negrita=True)
    d.texto(
        s, 464, 300, 216, 30,
        "Cada capacidad nueva nace con su endpoint y su tool, sobre la misma lógica.",
        10, GRIS, interlineado=1.2,
    )  # fmt: skip
    d.texto(
        s, 40, 352, 640, 34,
        "**Conectores** para Claude y ChatGPT; Grok, próximamente. Hoy construyes una versión chiquita de esto, "
        "con datos públicos.",
        12, TINTA, interlineado=1.2,
    )  # fmt: skip

    # 10 · Clonemos el repo (lo agregó Dante en Google Slides)
    s = d.lamina(
        "Pide que clonen el repo ahora, con el QR o la URL, y que corran uv run preparar.py y uv run verificar.py "
        "mientras sigues con los conceptos: así llegan a «Construyamos» con todo listo. Quien no tenga laptop o no "
        "programe, sigue en pantalla y en la práctica hace equipo con alguien.",
        0.5,
    )
    d.texto(s, 40, 169, 640, 38, "Clonemos repo para empezar", 25, TINTA, SERIF)
    d.texto(s, 47, 211, 432, 32, REPO, 14, TINTA)
    d.imagen(s, RECURSOS / "qr-repo.png", 429, 77, 251, 251)

    # 11 · Qué es una tool (function calling)
    s = d.lamina(
        "Este es el concepto más importante del taller. Una tool es una función que el modelo puede pedir que se "
        "ejecute. Ojo: el modelo NO la ejecuta; emite una petición estructurada (eso es function calling: el "
        "nombre de la tool y los argumentos en JSON), tu código la ejecuta y le devuelve el resultado, y el modelo "
        "responde con eso. Recorre los cuatro pasos de la derecha con la pregunta de Pantitlán. Cuando el modelo "
        "repite ese ciclo varias veces para resolver algo, le llamamos agente.",
        1.5,
        seccion="El concepto",
    )
    d.titular(s, "Una tool es una función que el modelo pide y tu código ejecuta", y=54, h=40, tam=22, w=620)
    definiciones = [
        (
            "Tool (herramienta)",
            "una función con nombre, descripción y parámetros que el modelo puede pedir que se ejecute.",
        ),
        ("Function calling", "la petición que emite el modelo: el nombre de la tool y los argumentos en JSON."),
        (
            "Agente",
            "un modelo que repite el ciclo (pedir una tool, leer el resultado, decidir) hasta resolver la tarea.",
        ),
    ]
    for n, (termino, texto) in enumerate(definiciones):
        d.definicion(s, 40, 112 + n * 82, 280, 72, termino, texto, 11)
    pasos = [
        (OCRE, "Tú preguntas", "«¿Cuánta gente entró a Pantitlán?»", SANS),
        (VERDE, "Claude pide la tool", 'afluencia_metro(estacion="Pantitlán")', MONO),
        (AZUL, "Tu código la ejecuta", '{"total": 4623233, "fuente": "datos.cdmx…"}', MONO),
        (VERDE, "Claude responde con el dato", "«Entraron 4,623,233 personas…»", SANS),
    ]
    for n, (tinta, etiqueta, ejemplo, fuente) in enumerate(pasos):
        y = 114 + n * 64
        d.caja(
            s,
            345,
            y + 6,
            24,
            24,
            tinta,
            forma=MSO_SHAPE.OVAL,
            contenido=str(n + 1),
            tam=10,
            tinta=BLANCO,
            margen=0,
            negrita=True,
        )
        d.texto(s, 384, y + 4, 296, 16, etiqueta, 13, tinta, negrita=True)
        d.texto(s, 384, y + 24, 296, 30, ejemplo, 11, TINTA, fuente)
    d.texto(s, 345, 372, 335, 18, "El modelo nunca ejecuta nada: solo pide.", 12.5, VERDE, negrita=True)

    # 12 · Qué es MCP
    s = d.lamina(
        "Si una tool es una función, ¿quién la define? Antes, cada aplicación definía sus tools en su propio "
        "código. MCP es el estándar abierto que permite que las tools vivan en un servidor aparte y que cualquier "
        "aplicación compatible las descubra al conectarse. La analogía oficial: un puerto USB-C para aplicaciones de "
        "IA. Este es el diagrama de la documentación oficial, adaptado: a la izquierda, las aplicaciones de IA "
        "(chat, editores de código, otros agentes); a la derecha, los datos y las herramientas; en medio, el "
        "protocolo, con datos que van y vienen. Ojo: el cuadro de en medio es un idioma, no un servidor "
        "intermediario. Cada app implementa el cliente una vez (lo hacen Anthropic, OpenAI, Cursor) y cada sistema "
        "expone su propio servidor (lo escribe su dueño): con 3 apps y 4 sistemas son 7 implementaciones, no 12 "
        "integraciones a la medida. Un gateway que agrupe servidores existe, pero es opcional. Y la ventaja sólo "
        "aparece con más de una app: con una sola, MCP cuesta casi lo mismo que una integración directa. Eso lo "
        "vemos en la siguiente lámina.",
        1.5,
        seccion="El concepto",
    )
    d.titular(s, "MCP es el estándar para conectar la IA con tus sistemas", y=36, h=32)
    d.definicion(
        s, 40, 78, 640, 60, "MCP (Model Context Protocol)",
        "un estándar abierto para conectar aplicaciones de IA con sistemas externos. «Como un puerto USB-C para aplicaciones de IA» (modelcontextprotocol.io).",
        11,
    )  # fmt: skip
    # Diagrama de modelcontextprotocol.io («What is MCP?», docs 2026-07-28), adaptado. En medio va el
    # protocolo, no un servidor: cada app trae su cliente y cada sistema expone su servidor.
    aplicaciones = [
        "**Interfaces de chat**\nClaude, ChatGPT",
        "**IDEs y editores de código**\nClaude Code, Cursor",
        "**Otras apps de IA**\nagentes propios, Goose",
    ]
    fuentes = [
        "**Datos y archivos**\nSQLite, PostgreSQL, Drive",
        "**Herramientas de desarrollo**\nGit, GitHub, Sentry",
        "**Productividad**\nSlack, Google Maps",
    ]
    centros = [173, 229, 285]
    for cy, izquierda, derecha in zip(centros, aplicaciones, fuentes):
        d.caja(s, 40, cy - 23, 196, 46, BLANCO, TINTA, radio=0.1, contenido=izquierda, tam=10.5, margen=6)
        d.caja(s, 484, cy - 23, 196, 46, BLANCO, TINTA, radio=0.1, contenido=derecha, tam=10.5, margen=6)
    d.caja(s, 300, 183, 120, 92, AZUL_FONDO, AZUL, radio=0.06, contenido="**MCP**\nprotocolo estándar", tam=12)
    # Flujo de datos en los dos sentidos: flecha hacia la caja de cada lado y hacia el protocolo.
    for cy, py in zip(centros, [201, 229, 257]):
        d.linea(s, 268, cy, 236, cy, GRIS, 1.25, True)
        d.linea(s, 268, py, 300, py, GRIS, 1.25, True)
        d.linea(s, 452, cy, 484, cy, GRIS, 1.25, True)
        d.linea(s, 452, py, 420, py, GRIS, 1.25, True)
        if cy != py:
            d.linea(s, 268, cy, 268, py, GRIS, 1.25)
            d.linea(s, 452, cy, 452, py, GRIS, 1.25)
    d.texto(s, 300, 280, 120, 24, "datos en los dos sentidos", 8.5, GRIS, alinear="centro")
    d.texto(s, 40, 314, 196, 14, "Aplicaciones de IA · cliente MCP", 9.5, GRIS, alinear="centro")
    d.texto(s, 484, 314, 196, 14, "Datos y herramientas · servidor MCP", 9.5, GRIS, alinear="centro")
    d.texto(
        s, 40, 336, 640, 28,
        "MCP es el idioma común, no un intermediario: cada app implementa el cliente una vez y cada sistema su "
        "servidor. Con 3 apps y 4 sistemas son 3 + 4 = **7 implementaciones**, no 3 × 4 = 12 integraciones.",
        10.5, GRIS, interlineado=1.2,
    )  # fmt: skip
    d.texto(
        s, 40, 370, 640, 10, "Adaptado de modelcontextprotocol.io · «What is MCP?» (docs 2026-07-28)", 7.5, GRIS, MONO
    )

    # 13 · ¿Cuál conviene? API, CLI o MCP
    s = d.lamina(
        "Primero la objeción honesta: la IA puede usar las tres. Puede leer la documentación de una API y armar la "
        "llamada, puede escribir comandos de terminal (git, gh o kubectl los conoce de su entrenamiento) y puede usar "
        "un servidor MCP. Los benchmarks dicen que, con tools bien diseñadas, CLI y MCP empatan en éxito, pero MCP "
        "gasta más contexto: en el de Scalekit, de 1.3 a 80 veces más tokens en cinco tareas de GitHub; Zechner lo "
        "resume como un empate en el que importa más el diseño de la tool que el protocolo. Así que la pregunta no es "
        "cuál es mejor, sino cuál conviene. Los tres carriles hacen lo mismo, listar los issues de GitHub; cambia el "
        "camino. Con la API, el modelo escribe código que arma la llamada con la credencial que le diste: conviene "
        "si el flujo es fijo y no lo decide un modelo. Con la CLI, escribe gh issue list en tu terminal y corre con "
        "todos tus permisos: conviene si eres tú, en tu máquina, con una herramienta que ya conoce. Con MCP, el host "
        "pide la tool por nombre al servidor: ve cada llamada, puede pedir aprobación y registrarla, y cada persona "
        "entra con su cuenta; conviene si el modelo elige en el momento, para varias personas, o si la persona está "
        "en Claude.ai o ChatGPT, donde no hay terminal. Y si son muchos pasos sobre muchos datos, que el modelo "
        "escriba código que llame tus tools (Anthropic, «code execution with MCP»).",
        1.5,
        seccion="¿Por qué MCP?",
    )
    d.titular(s, "La IA puede usar API, CLI o MCP: elige según la situación")
    # Mismo pedido en los tres carriles («lista los issues de GitHub»): sólo cambia el camino.
    carriles = [
        ("API", AZUL, BLANCO, BORDE,
         [("Claude", TINTA, PAPEL), ("código: GET /issues + API key", BLANCO, TINTA), ("API REST", AZUL_FONDO, AZUL)],
         "Cada servicio documenta distinto; la credencial se la das tú al agente.",
         "el flujo es siempre el mismo y no lo decide un modelo: un script o un pipeline"),
        ("CLI", OCRE, BLANCO, BORDE,
         [("Claude", TINTA, PAPEL), ("tu terminal: gh issue list", BLANCO, TINTA), ("GitHub", AZUL_FONDO, AZUL)],
         "Corre en tu máquina con todos tus permisos. Sin tu terminal, no hay CLI.",
         "trabajas en tu máquina con una herramienta que el modelo ya conoce: git, gh, kubectl"),
        ("MCP", VERDE, VERDE_FONDO, VERDE,
         [("Claude", TINTA, PAPEL), ("host: list_issues", BLANCO, TINTA), ("servidor MCP", BLANCO, VERDE),
          ("GitHub", AZUL_FONDO, AZUL)],
         "El host ve cada tool: pide aprobación y registra cada llamada; OAuth por persona.",
         "el modelo elige en el momento, para varias personas y con auditoría; también sin terminal (Claude.ai, ChatGPT)"),
    ]  # fmt: skip
    for n, (nombre, tinta, relleno, borde, pasos, control, conviene) in enumerate(carriles):
        y = 96 + n * 82
        d.caja(s, 40, y, 640, 74, relleno, borde, radio=0.06)
        d.texto(s, 54, y + 12, 50, 22, nombre, 17, tinta, negrita=True)
        x = 104.0
        for k, (texto, fondo, letra) in enumerate(pasos):
            ancho = len(texto) * 9 * 0.56 + 18
            d.caja(
                s, x, y + 11, ancho, 24, fondo, None if fondo != BLANCO else BORDE, radio=0.5,
                contenido=texto, tam=9, tinta=letra, margen=3, negrita=k == 0,
            )  # fmt: skip
            x += ancho
            if k < len(pasos) - 1:
                d.linea(s, x + 2, y + 23, x + 12, y + 23, GRIS, 1.25, True)
                x += 14
        d.texto(s, 104, y + 44, 352, 24, control, 9.5, GRIS, interlineado=1.15)
        d.caja(s, 470, y + 8, 200, 58, BLANCO, BORDE, radio=0.08)
        d.texto(s, 480, y + 13, 184, 10, "CONVIENE SI", 7, tinta, MONO, negrita=True)
        d.texto(s, 480, y + 25, 184, 40, conviene, 9, TINTA, interlineado=1.15)
    d.texto(
        s, 40, 344, 640, 30,
        "Con tools bien diseñadas, CLI y MCP empatan en éxito; MCP gasta más contexto (de 1.3× a 80× más tokens en "
        "cinco tareas de GitHub). ¿Muchos pasos sobre muchos datos? Que el modelo escriba código que llame las tools.",
        10, GRIS, interlineado=1.2,
    )  # fmt: skip
    d.texto(
        s, 40, 384, 640, 12,
        "Zechner (ago-2025) · Scalekit, MCP vs CLI benchmark (2026) · Osmani, MCP deep dive · Anthropic (nov-2025)",
        8, GRIS, MONO,
    )  # fmt: skip

    # 14 · Lo que MCP te da y lo que te cuesta
    s = d.lamina(
        "Si las tres funcionan, ¿por qué tener un servidor MCP? Lo que te da: 1) funciona donde no hay una terminal "
        "tuya: Claude.ai, ChatGPT o un agente en la nube no pueden correr tus CLIs, pero sí conectarse a un MCP "
        "remoto (Zechner: es la única opción para clientes sin shell). 2) La autorización viene en el estándar: OAuth "
        "2.1 sobre HTTP, con scopes mínimos; cada persona entra con su cuenta y el agente no guarda tu API key. 3) El "
        "host ve cada tool por nombre: puede pedir aprobación por tool y registrar cada llamada, en vez de heredar "
        "todos tus permisos como una CLI. 4) Tú decides qué exponer y cómo describirlo. 5) Es neutral: desde "
        "diciembre de 2025 lo gobierna la Agentic AI Foundation de la Linux Foundation, y lo usan Claude, ChatGPT, "
        "Gemini, Copilot y VS Code. Lo que cuesta: contexto (el MCP de GitHub declara 93 tools, unos 55,000 tokens; "
        "Claude Code mitiga con tool search), composición (cada paso pasa por inferencia; Anthropic propone que el "
        "modelo escriba código que llame las tools: de 150,000 a 2,000 tokens en su ejemplo), seguridad (la spec "
        "documenta confused deputy, token passthrough y SSRF; OWASP, tool poisoning y prompt injection en los "
        "resultados; y la spec pide tratar las anotaciones como no confiables) y operación. Conclusión: conviene "
        "cuando lo que te da pesa más. Aquí sí: queremos que cualquier host lo use y controlar la acción que escribe.",
        1.5,
        seccion="¿Por qué MCP?",
    )
    d.titular(s, "MCP te da control y alcance; lo pagas en contexto y riesgo")
    columnas = [
        (40, "Lo que te da", VERDE, [
            ("Funciona sin tu terminal", "Claude.ai, ChatGPT o un agente en la nube no corren tus CLIs; sí se conectan a un MCP remoto."),
            ("Autorización por usuario", "OAuth 2.1 viene en el estándar; cada persona entra con su cuenta."),
            ("El host ve cada tool", "puede pedir aprobación y registrar cada llamada; una CLI corre con todos tus permisos."),
            ("Tú defines la superficie", "expones intenciones, no 40 endpoints, con un contrato escrito para el modelo."),
            ("Lo escribes una vez", "estándar neutral en la Linux Foundation; lo usan Claude, ChatGPT, Gemini, Copilot y VS Code."),
        ]),
        (370, "Lo que te cuesta", ROJO, [
            ("Contexto", "cada definición ocupa tokens; el MCP de GitHub: 93 tools, unos 55,000 tokens."),
            ("Composición", "cada paso pasa por el modelo; para muchos pasos, conviene que escriba código que llame tus tools."),
            ("Seguridad", "tool poisoning, prompt injection en los resultados, token passthrough. Las anotaciones son pistas, no garantías."),
            ("Operación", "otro servicio que desplegar, versionar y probar con cada host."),
        ]),
    ]  # fmt: skip
    for x, encabezado, tinta, puntos in columnas:
        d.texto(s, x, 98, 310, 20, encabezado, 15, tinta, negrita=True)
        for n, (titulo, texto) in enumerate(puntos):
            d.texto(s, x, 126 + n * 48, 310, 44, f"**{titulo}**: {texto}", 10.5, TINTA, interlineado=1.2)
    d.texto(
        s, 40, 384, 640, 12,
        "MCP spec 2026-07-28 (autorización, seguridad, tools) · Anthropic (dic-2025, nov-2025) · Huntley vía Willison (ago-2025) · OWASP",
        8, GRIS, MONO,
    )  # fmt: skip

    # 15 · Host, client y server
    s = d.lamina(
        "Vocabulario que van a escuchar todo el día. El host es la aplicación donde conversas: hoy, Claude Code. "
        "Dentro, el host crea un client por cada servidor al que se conecta. El server es el programa que van a "
        "escribir: expone capacidades. Entre client y server viajan mensajes JSON-RPC; los dos que importan hoy: "
        "tools/list (¿qué sabes hacer?) y tools/call (hazlo). El transporte es por dónde viajan: hoy HTTP, en su "
        "propia máquina; también existe stdio, donde el host lanza el servidor como proceso.",
        1,
        seccion="El concepto",
    )
    d.titular(s, "En MCP participan tres actores: host, client y server")
    d.caja(s, 40, 112, 270, 120, VERDE_FONDO, VERDE, radio=0.06)
    d.texto(s, 56, 122, 240, 18, "Host · Claude Code", 13, VERDE, negrita=True)
    d.caja(s, 150, 160, 140, 54, BLANCO, VERDE, radio=0.08, contenido="**Client**\nuno por servidor", tam=11.5)
    d.caja(s, 430, 112, 250, 120, AZUL_FONDO, AZUL, radio=0.06)
    d.texto(s, 446, 122, 220, 18, "Server · cdmx (tu código)", 13, AZUL, negrita=True)
    d.texto(
        s, 446, 148, 220, 80,
        "Python + FastMCP\nexpone tools, resources y prompts\nlee SQLite y datos.cdmx.gob.mx",
        11.5, TINTA, interlineado=1.3,
    )  # fmt: skip
    d.linea(s, 292, 180, 428, 180, GRIS, 2, True)
    d.linea(s, 428, 200, 292, 200, GRIS, 2, True)
    d.texto(s, 316, 146, 108, 30, "tools/list\ntools/call", 9.5, GRIS, MONO, alinear="centro", vertical="abajo")
    d.texto(s, 300, 206, 120, 16, "resultado", 10, GRIS, alinear="centro")
    defs = [
        ("Host", "la aplicación de IA donde conversas: Claude Code, Claude Desktop."),
        ("Client", "el conector que el host crea para hablar con un servidor."),
        ("Server", "el programa que expone capacidades. Hoy escribes uno."),
    ]
    for n, (termino, texto) in enumerate(defs):
        d.definicion(s, 40 + n * 216, 248, 208, 76, termino, texto, 11)
    d.texto(
        s, 40, 338, 640, 40,
        "**Transporte**: por dónde viajan los mensajes. Hoy, HTTP en tu propia máquina (127.0.0.1:8765). "
        "También existe stdio: el host lanza el servidor como un proceso.",
        11.5, GRIS, interlineado=1.25,
    )  # fmt: skip

    # 16 · De qué se compone MCP (spec 2026-07-28)
    s = d.lamina(
        "Así está armada la especificación vigente, la 2026-07-28. Solo tres capas son obligatorias: los mensajes "
        "(JSON-RPC 2.0), el versionado y los patrones de mensaje (petición y respuesta, multi round-trip y "
        "suscripción). Desde esta versión el protocolo no tiene estado: ya no hay handshake initialize ni "
        "Mcp-Session-Id; cada petición lleva su versión y las capacidades del cliente, y el servidor responde "
        "server/discover. Todo lo demás es opcional: la autorización (OAuth 2.1, solo en HTTP), las utilidades, "
        "lo que ofrece el servidor (tools, resources y prompts) y lo que ofrece el cliente. Del lado del cliente "
        "queda elicitation, para pedirle un dato a la persona; sampling y roots quedaron obsoletos en esta versión "
        "(SEP-2577): siguen al menos doce meses, pero no se deben adoptar. Las extensiones, como Tasks y MCP Apps, "
        "se negocian aparte. El transporte se elige: stdio o Streamable HTTP. Lo que usamos hoy lleva una palomita: "
        "FastMCP resuelve las capas obligatorias por nosotros; nosotros escribimos tools, resources y prompts.\n\n"
        "ELICITATION, por si preguntan: es cuando el servidor le pide un dato a la persona a mitad de una operación; "
        "no lo pide el modelo. Ejemplo con nuestro servidor: alguien pide un reporte en «Insurgentes», que existe en "
        "las líneas 1 y 12. En vez de adivinar, la tool responde que le falta un dato (resultType input_required) con "
        "un formulario «¿en qué línea?»; Claude Code lo muestra, la persona elige y el cliente repite la llamada con "
        "la respuesta. Hay dos modos: formulario, para datos normales (nunca contraseñas ni credenciales), y URL, que "
        "abre el navegador para datos sensibles o para conectar una cuenta de terceros sin que el secreto pase por el "
        "modelo. La persona puede aceptar, rechazar o cancelar. No es la aprobación de una tool (esa la decide el host "
        "antes de ejecutarla) ni la autorización OAuth al servidor. En 2026-07-28 viaja como multi round-trip; en la "
        "versión anterior el servidor la pedía por un canal abierto (ctx.elicit() en FastMCP). Hoy no la usamos: para "
        "la acción que escribe usamos la aprobación del host (paso 3).",
        1.5,
        seccion="El concepto",
    )
    d.titular(s, "MCP tiene tres capas obligatorias; el resto es opcional")
    capas = [  # (y, alto, cajas, estado); cada caja: (x, ancho, contenido, relleno, borde)
        (98, 36, [(40, 520, "**Extensiones**: Tasks (trabajos largos) · MCP Apps (UI en la conversación) · auth empresarial", BLANCO, BORDE)], "opt-in"),
        (140, 40, [(40, 256, "**El servidor ofrece**: Tools ✓ · Resources ✓ · Prompts ✓", AZUL_FONDO, AZUL),
                   (304, 256, "**El cliente ofrece**: Elicitation", VERDE_FONDO, VERDE)], "opcional"),
        (186, 32, [(40, 520, "**Utilidades**: progreso · cancelación · logging · autocompletado · paginación", BLANCO, BORDE)], "opcional"),
        (224, 32, [(40, 520, "**Autorización**: OAuth 2.1, solo en HTTP; cada persona entra con su cuenta", BLANCO, BORDE)], "opcional"),
        (262, 54, [(40, 168, "**Mensajes**\nJSON-RPC 2.0, sin estado", BLANCO, TINTA),
                   (216, 168, "**Versionado**\nversión y capacidades en cada petición", BLANCO, TINTA),
                   (392, 168, "**Patrones**\npetición · multi round-trip · suscripción", BLANCO, TINTA)], "obligatorio"),
        (322, 32, [(40, 520, "**Transporte**: stdio, el host lanza el proceso · Streamable HTTP ✓", BLANCO, BORDE)], "elige uno"),
    ]  # fmt: skip
    for y, alto, cajas, estado in capas:
        for x, ancho, contenido, relleno, borde in cajas:
            d.caja(
                s,
                x,
                y,
                ancho,
                alto,
                relleno,
                borde,
                radio=0.12,
                contenido=contenido,
                tam=10.5,
                alinear="izq",
                margen=10,
            )
        obligatorio = estado == "obligatorio"
        d.caja(
            s, 576, y + (alto - 22) / 2, 104, 22, TINTA if obligatorio else BLANCO, None if obligatorio else BORDE,
            radio=0.5, contenido=estado, tam=9.5, tinta=PAPEL if obligatorio else GRIS, margen=4, negrita=obligatorio,
        )  # fmt: skip
    d.texto(
        s,
        40,
        362,
        640,
        14,
        "✓ = lo usamos hoy. Obsoleto = sigue en la spec al menos 12 meses, pero no se debe adoptar.",
        10,
        GRIS,
    )
    d.texto(
        s, 40, 384, 640, 12,
        "modelcontextprotocol.io/specification/2026-07-28 · basic · changelog · client/sampling · client/roots · extensions",
        8, GRIS, MONO,
    )  # fmt: skip

    # 17 · Tool, resource y prompt
    s = d.lamina(
        "Las tres cosas que puede ofrecer un servidor. Se declaran parecido, por eso se confunden; lo que las separa "
        "es quién decide cuándo ocurren. Tool: una función que el modelo invoca cuando la necesita. Resource: un dato "
        "de solo lectura con una dirección (URI) que la aplicación decide incluir como contexto. Prompt: una plantilla "
        "de instrucciones que tú eliges ejecutar (en Claude Code aparece como comando con /). Abajo, los campos con "
        "los que se define cada una según la spec: de esos campos, nombre y descripción son lo que lee el modelo. La "
        "mayoría expone todo como tools; el prompt es la pieza menos usada y la de mejor esfuerzo/impacto.",
        0,
        seccion="El concepto",
        oculta=True,  # Dante la ocultó a propósito: se presenta la versión con diagrama
    )
    d.titular(s, "Tres piezas, una pregunta: ¿quién decide cuándo ocurre?")
    piezas = [
        ("Tool", VERDE, "decide **el modelo**", "Una función que el modelo invoca cuando la necesita.",
         "afluencia_metro(...)", "name · description · inputSchema"),
        ("Resource", AZUL, "decide **la aplicación**", "Un dato de solo lectura, con dirección (URI), que la app incluye como contexto.",
         "cdmx://fuentes", "uri · name · mimeType"),
        ("Prompt", OCRE, "decides **tú**", "Una plantilla de instrucciones que eliges ejecutar; en Claude Code, un comando /.",
         "/informe_estacion", "name · description · arguments"),
    ]  # fmt: skip
    for n, (nombre, tinta, quien, definicion, ejemplo, campos) in enumerate(piezas):
        x = 40 + n * 220
        d.texto(s, x, 120, 200, 40, nombre, 30, tinta, SERIF)
        d.texto(s, x, 166, 200, 22, quien, 15, TINTA)
        d.texto(s, x, 196, 196, 56, definicion, 12, GRIS, interlineado=1.25)
        d.texto(s, x, 258, 200, 18, ejemplo, 12, tinta, MONO)
        d.texto(s, x, 290, 200, 12, "SE DEFINE CON", 8, GRIS, MONO)
        d.texto(s, x, 304, 200, 16, campos, 10, TINTA, MONO)
    d.texto(s, 40, 344, 640, 20, "Nuestro servidor tiene las tres. La mayoría expone todo como tools.", 12.5, GRIS)

    # 18 · Las tres piezas en un diagrama (lo agregó Dante en Google Slides; va con la lámina anterior)
    s = d.lamina(
        "Las tres cosas que puede ofrecer un servidor. Arriba: el cliente invoca tools, consulta resources e "
        "interpola prompts; el servidor los expone. Abajo, lo que las separa: quién decide cuándo ocurren. Tool: una "
        "función que el modelo invoca cuando la necesita (en nuestro servidor, afluencia_metro). Resource: un dato de "
        "solo lectura con dirección (URI) que la aplicación incluye como contexto (cdmx://fuentes). Prompt: una "
        "plantilla que tú eliges ejecutar; en Claude Code, un comando / (/informe_estacion). La mayoría expone todo "
        "como tools; el prompt es la pieza menos usada y la de mejor esfuerzo/impacto.",
        1,
        seccion="El concepto",
    )
    d.titular(s, "Tres piezas, una pregunta: ¿quién decide cuándo ocurre?")
    d.imagen(s, RECURSOS / "piezas-mcp.png", 69, 99, 583, 261)

    # 19 · Qué servidor construimos: transporte y FastMCP
    s = d.lamina(
        "Antes de escribir código: qué tipo de servidor vamos a hacer. Un servidor MCP se distingue por su transporte. "
        "Con stdio, Claude Code lanza tu servidor como un proceso y le habla por la entrada y salida estándar: no hay "
        "red; es lo que esperan Claude Desktop y la mayoría de los servidores locales. Con HTTP local, tu servidor "
        "corre aparte, en 127.0.0.1:8765, y Claude Code se conecta por URL: lo ves en su propia terminal, lo reinicias "
        "sin tocar a Claude y funciona igual que en producción. Ese es el que hacemos hoy. Con HTTP remoto, el mismo "
        "servidor se despliega en internet con OAuth 2.1; así lo usan Claude.ai o ChatGPT. Existe un transporte "
        "anterior, SSE, que solo se mantiene por compatibilidad. Con FastMCP las tools no cambian: el transporte es "
        "un argumento de mcp.run(). Y una confusión común: FastMCP no es FastAPI. FastMCP es el framework de Python "
        "para servidores MCP; su primera versión se incorporó al SDK oficial en 2024 (en el SDK v2 su sucesor se "
        "llama MCPServer) y hoy es un proyecto aparte que agrega autenticación, middleware, cliente y pruebas. "
        "FastAPI es un framework para APIs web (REST) que llama código. Se combinan porque los dos son apps ASGI "
        "(Starlette): puedes montar tu MCP dentro de FastAPI con app.mount, o generarlo desde una API con "
        "FastMCP.from_fastapi. La propia documentación de FastMCP advierte que los modelos rinden significativamente "
        "mejor con servidores curados que con APIs convertidas: úsalo para prototipar.",
        1,
        seccion="Qué vamos a construir",
    )
    d.titular(s, "Construimos un servidor MCP por HTTP con FastMCP")
    d.texto(s, 40, 98, 320, 18, "Tipos de servidor según el transporte", 13, TINTA, negrita=True)
    tipos = [
        ("stdio · local", "Claude Code lanza tu servidor como proceso y le habla por stdin/stdout. Sin red.", False),
        ("HTTP local ✓", "Hoy: tu servidor corre aparte en 127.0.0.1:8765 y Claude Code se conecta por URL.", True),
        ("HTTP remoto", "Desplegado en internet con OAuth 2.1; así lo usan Claude.ai o ChatGPT.", False),
    ]
    for n, (nombre, texto, hoy) in enumerate(tipos):
        y = 126 + n * 56
        d.caja(
            s, 40, y, 104, 22, VERDE if hoy else BLANCO, None if hoy else BORDE, radio=0.5,
            contenido=nombre, tam=9.5, tinta=BLANCO if hoy else TINTA, margen=4, negrita=hoy,
        )  # fmt: skip
        d.texto(s, 156, y + 1, 204, 50, texto, 10.5, TINTA, interlineado=1.2)
    d.texto(s, 40, 294, 320, 16, "Las tools no cambian; el transporte es un argumento:", 10.5, GRIS)
    d.codigo(s, 40, 314, 320, 46, 'mcp.run()                    # stdio\nmcp.run(transport="http")    # HTTP', 10)
    d.texto(s, 384, 98, 296, 18, "FastMCP", 13, TINTA, negrita=True)
    d.definicion(
        s, 384, 122, 296, 70, "FastMCP",
        "framework de Python para servidores MCP: de tu función saca el schema y habla el protocolo por stdio o HTTP.",
        10.5,
    )  # fmt: skip
    d.codigo(s, 384, 314, 296, 46, 'app.mount("/mcp", mcp.http_app())\nFastMCP.from_fastapi(app)', 10)
    d.texto(
        s, 40, 384, 640, 12,
        "gofastmcp.com (running-server, integrations/fastapi) · fastapi.tiangolo.com · MCP spec 2026-07-28 (transports)",
        8, GRIS, MONO,
    )  # fmt: skip

    # 20 · Construyamos
    s = d.lamina(
        "Ahora construimos. Primero, de qué datos hablamos: la afluencia diaria del Metro que publica el gobierno "
        "de la CDMX como datos abiertos (licencia CC-BY-4.0: se pueden usar citando la fuente). Ya clonaron en la "
        "lámina 10; quien no, que lo haga ahora: uv instala Python y las dependencias, y preparar.py arma la base "
        "sin internet. Pide manos: ¿a quién le dio «Todo en orden» verificar.py? Camina por la sala. Son cuatro pasos y cada uno termina con una comprobación; si alguien "
        "se atora, copia el punto de control del paso (pasos/0N_*.py) o abre claude en el repo y le pide que lo guíe.",
        1,
    )
    d.texto(s, 48, 40, 600, 50, "Construyamos", 40, TINTA, SERIF)
    d.texto(s, 48, 92, 600, 22, "Cuatro pasos. Cada uno termina con una comprobación.", 15, GRIS)
    for n, nombre in enumerate(["Una tool", "Diseño", "Una acción", "Medir"]):
        x = 48 + n * 156
        d.caja(
            s,
            x,
            128,
            28,
            28,
            PAPEL,
            VERDE,
            forma=MSO_SHAPE.OVAL,
            contenido=str(n + 1),
            tam=12,
            tinta=VERDE,
            margen=0,
            negrita=True,
        )
        d.texto(s, x + 38, 133, 110, 22, nombre, 14, TINTA)
    d.codigo(
        s, 48, 172, 624, 98,
        f"git clone {REPO}\ncd {REPO.rsplit('/', 1)[-1]}\nuv run preparar.py      # datos → SQLite, sin internet\nuv run verificar.py     # ¿todo listo?",
        13, resaltar=["uv run preparar.py", "uv run verificar.py"],
    )  # fmt: skip
    d.definicion(
        s, 48, 280, 306, 72, "Datos abiertos",
        "datos que publica una institución con una licencia que permite reusarlos. Aquí: afluencia del Metro, CC-BY-4.0.",
        11,
    )  # fmt: skip
    d.definicion(
        s, 366, 280, 306, 72, "uv",
        "herramienta que instala la versión de Python y las dependencias correctas, y corre el script. No instalas nada más.",
        11,
    )  # fmt: skip
    d.texto(
        s,
        48,
        362,
        624,
        20,
        "¿Atorado? Abre claude en el repo y pídele: «guíame paso a paso».",
        12.5,
        VERDE,
        negrita=True,
    )

    # 21 · En cada paso: copia, reinicia, reconecta y comprueba
    s = d.lamina(
        "Antes del paso 1, el ciclo que van a repetir en cada paso, para que nadie se pierda. Su servidor.py empieza "
        "en el paso 1; las tools nuevas llegan copiando el punto de control del paso: por eso afluencia_metro aparece "
        "hasta el paso 2. Cuatro movimientos: 1) copiar el punto de control sobre servidor.py; 2) en la terminal 1, "
        "Ctrl-C (no Cmd-C), flecha arriba y Enter para reiniciar el servidor; 3) en Claude Code, /mcp y reconectar "
        "cdmx; 4) comprobar con uv run verificar.py y el número del paso, y hacer la pregunta del paso. Quien quiera "
        "escribir el código puede ver qué cambia con git diff --no-index servidor.py pasos/02_consulta.py. En "
        "Windows (cmd), copy en lugar de cp. Copien solo el comando, sin comentarios.",
        0.5,
        seccion="Construyamos",
    )
    d.titular(s, "En cada paso: copia, reinicia, reconecta y comprueba", h=36)
    ciclo = [
        ("1 · Copia", "cp pasos/0N_*.py\n   servidor.py", "el punto de control"),
        ("2 · Reinicia", "Ctrl-C · ↑ · Enter", "en la terminal 1"),
        ("3 · Reconecta", "/mcp → cdmx", "en Claude Code"),
        ("4 · Comprueba", "uv run verificar.py N", "y haz la pregunta del paso"),
    ]
    for n, (titulo, comando, donde) in enumerate(ciclo):
        x = 40 + n * 164
        d.caja(s, x, 92, 148, 74, BLANCO, BORDE, radio=0.06)
        d.texto(s, x + 10, 100, 128, 14, titulo, 11, VERDE, negrita=True)
        d.texto(s, x + 10, 119, 132, 26, comando, 8.5, TINTA, MONO, interlineado=1.1)
        d.texto(s, x + 10, 148, 132, 14, donde, 8.5, GRIS)
        if n < 3:
            d.linea(s, x + 150, 129, x + 162, 129, GRIS, 1.5, True)
    # Después de comprobar se copia el punto de control del siguiente paso.
    d.linea(s, 606, 166, 606, 178, VERDE, 1.25)
    d.linea(s, 606, 178, 114, 178, VERDE, 1.25)
    d.linea(s, 114, 178, 114, 168, VERDE, 1.25, True)
    d.texto(s, 260, 181, 200, 12, "siguiente paso", 8.5, VERDE, alinear="centro")
    d.texto(s, 40, 204, 640, 16, "Qué tiene tu servidor en cada paso", 11, TINTA, negrita=True)
    filas = [
        ("Paso 1", "servidor.py (ya lo trae)", "buscar_datasets_cdmx"),
        ("Paso 2", "pasos/02_consulta.py", "+ buscar_estacion_metro · ==afluencia_metro== · ranking_estaciones_metro"),
        ("Paso 3", "pasos/03_accion.py", "+ registrar_reporte · consultar_reportes"),
        ("Paso 4", "pasos/04_final.py", "+ ecobici_cerca_de_metro · actualizar_mapa_ecobici"),
    ]
    for n, (paso, archivo, herramientas) in enumerate(filas):
        y = 226 + n * 28
        d.caja(s, 40, y, 56, 20, VERDE_FONDO, radio=0.5, contenido=paso, tam=9, tinta=VERDE, margen=2, negrita=True)
        d.texto(s, 106, y + 4, 170, 14, archivo, 9, TINTA, MONO)
        d.texto(s, 282, y + 4, 398, 14, herramientas, 8.5, GRIS, MONO)
    d.texto(
        s, 40, 344, 640, 30,
        "Windows (cmd): copy pasos\\02_consulta.py servidor.py · copia solo el comando, sin comentarios · "
        "¿Te perdiste? En Claude Code: «guíame paso a paso».",
        9.5, GRIS, interlineado=1.2,
    )  # fmt: skip

    # 22 · Paso 1
    s = d.lamina(
        "[EN VIVO] Escribe esta tool en servidor.py desde cero, explicando cada línea. FastMCP es la librería que "
        "convierte la función en tool: el decorador @mcp.tool la registra, el docstring se vuelve la descripción y "
        "los type hints se vuelven el schema. Lo verde es lo único que el modelo lee para decidir. Levanta el "
        "servidor (terminal 1), abre claude (terminal 2; el .mcp.json del repo ya lo conecta por HTTP) y pregunta "
        "por bicicletas. Comprobación: fastmcp list muestra la tool tal como la verá Claude.",
        4,
        seccion="Paso 1 · Una tool",
        paso=1,
    )
    d.titular(s, "Una función con docstring ya es una tool", y=58, h=40)
    d.codigo(
        s, 40, 110, 430, 178,
        '@mcp.tool(annotations={"readOnlyHint": True})\n'
        "async def buscar_datasets_cdmx(\n"
        "    texto: Annotated[str, Field(\n"
        '        description="Tema a buscar, en español.")],\n'
        "    limite: Annotated[int, Field(ge=1, le=10)] = 5,\n"
        ") -> dict:\n"
        '    """Busca conjuntos de datos en datos.cdmx.gob.mx.\n'
        '    Úsala para descubrir qué datos existen."""',
        11.5,
        resaltar=["buscar_datasets_cdmx", '"Tema a buscar, en español."', "ge=1, le=10",
                  "Busca conjuntos de datos en datos.cdmx.gob.mx.", "Úsala para descubrir qué datos existen."],
    )  # fmt: skip
    mini = [
        ("FastMCP", "librería de Python: un decorador convierte tu función en tool."),
        ("Docstring", "el texto entre triples comillas: es la descripción que lee el modelo."),
        ("Schema", "tipos y límites de los parámetros; sale de tus type hints."),
    ]
    for n, (termino, texto) in enumerate(mini):
        d.definicion(s, 40 + n * 146, 300, 138, 88, termino, texto, 10)
    for n, (etiqueta, texto, tinta) in enumerate(
        [
            ("Terminal 1", "uv run servidor.py", TINTA),
            ("Terminal 2", "claude", TINTA),
            ("Comprueba", "uv run fastmcp list\nhttp://127.0.0.1:8765/mcp", TINTA),
            ("Pruébalo", "«¿Qué datos abiertos hay\nsobre bicicletas?»", OCRE),
        ]
    ):
        y = 112 + n * 64
        d.texto(s, 494, y, 186, 14, etiqueta.upper(), 9, GRIS, MONO)
        d.texto(s, 494, y + 16, 186, 40, texto, 12, tinta, SANS if n == 3 else MONO, interlineado=1.15)

    # 23 · Paso 2
    s = d.lamina(
        "[EN VIVO] Tres reglas, una por columna. 1) Por intención: una tool genérica ejecutar_sql traslada el "
        "diseño al modelo; afluencia_metro con enums y formato AAAA-MM deja el dominio en el schema. 2) El error es "
        "una instrucción: muestra el error real de 'insurgente'; Claude se corrige en un turno. 3) La respuesta "
        "gasta contexto (la memoria de trabajo del modelo en una conversación): devuelve el agregado, con alcance, "
        "unidad, notas de calidad y fuente. Reto mientras copian el punto de control: ¿cómo diseñarían "
        "comparar_estaciones(a, b)?",
        4,
        seccion="Paso 2 · Diseño",
        paso=2,
    )
    d.titular(s, "Diseña para quien lee el contrato: el modelo")
    d.texto(s, 40, 116, 200, 20, "1 · Por intención", 14, TINTA, negrita=True)
    d.texto(s, 40, 146, 200, 18, "✗ ejecutar_sql(query)", 12, ROJO, MONO)
    d.codigo(
        s, 40, 172, 200, 76, "afluencia_metro(\n  estacion, linea,\n  desde, hasta)", 12, resaltar=["afluencia_metro("]
    )
    d.texto(s, 40, 260, 196, 40, "No por endpoint: el dominio vive en el schema.", 12, GRIS, interlineado=1.25)
    d.texto(s, 260, 116, 200, 20, "2 · Errores que corrigen", 14, TINTA, negrita=True)
    d.caja(
        s, 260, 146, 200, 118, VERDE_FONDO, VERDE, radio=0.05,
        contenido="'insurgente' coincide con varias estaciones: Insurgentes (Línea 1), Insurgentes Sur (Línea 12). Repite con el nombre exacto.",
        tam=11.5, alinear="izq", vertical="arriba", margen=12,
    )  # fmt: skip
    d.texto(s, 260, 276, 196, 30, "Claude se corrige en un turno.", 12, GRIS)
    d.texto(s, 480, 116, 200, 20, "3 · Respuestas cortas", 14, TINTA, negrita=True)
    d.texto(s, 480, 144, 196, 34, "alcance · unidad\nnotas · fuente", 12, VERDE, MONO)
    d.definicion(
        s, 480, 184, 200, 88, "Contexto",
        "lo que el modelo tiene presente en la conversación. Es finito: Claude Code avisa a los 10k tokens.",
        10.5,
    )  # fmt: skip
    d.texto(s, 480, 280, 196, 30, "Devuelve la serie agregada, no 38,804 filas.", 12, GRIS)
    d.chip(s, 40, 330, "✓ uv run verificar.py 2", ancho=200)
    d.texto(s, 256, 334, 424, 20, "Reto: ¿qué parámetros le darías a comparar_estaciones(a, b)?", 12.5, OCRE)

    # 24 · Paso 3
    s = d.lamina(
        "[EN VIVO] registrar_reporte escribe. Los controles, de afuera hacia adentro: el host pide aprobación en "
        "cada llamada (anthropic/requiresUserInteraction; en modo dontAsk la niega), el schema limita tipo y "
        "longitud, el código valida que la estación exista en esa línea, es idempotente y tiene un tope de 20 por "
        "hora, y escribe en una base separada (la de consulta es de solo lectura). Ese metadato es de Claude Code: "
        "otros hosts lo pueden ignorar, por eso el resto vive en el código. Y lo que regresa también es entrada: "
        "el texto ciudadano vuelve marcado como no confiable.",
        4.5,
        seccion="Paso 3 · Una acción",
        paso=3,
    )
    d.titular(s, "Si la tool escribe, los controles van en el código")
    capas = [
        (40, 112, 380, 236, OCRE_FONDO, OCRE, "Aprobación humana en cada llamada · el host"),
        (60, 142, 340, 196, BLANCO, AZUL, "Schema · tipo cerrado, de 10 a 500 caracteres"),
        (80, 172, 300, 156, AZUL_FONDO, AZUL, "Validación · idempotencia · tope de 20 por hora"),
    ]
    for x, y, w, h, relleno, tinta, etiqueta in capas:
        d.caja(s, x, y, w, h, relleno, tinta, radio=0.06)
        d.texto(s, x + 14, y + 9, w - 28, 16, etiqueta, 11, tinta, negrita=True)
    d.caja(
        s,
        100,
        206,
        260,
        106,
        AZUL,
        radio=0.06,
        contenido="Escribe en\n**reportes.sqlite**\n(base separada)",
        tam=13,
        tinta=BLANCO,
    )
    d.texto(s, 444, 112, 236, 46, "Claude propone;\nel código decide.", 19, TINTA, SERIF, interlineado=1.1)
    d.codigo(
        s, 444, 166, 236, 86,
        '@mcp.tool(meta={\n  "anthropic/\n   requiresUserInteraction":\n   True})',
        10.5, resaltar=["requiresUserInteraction"],
    )  # fmt: skip
    d.definicion(s, 444, 262, 236, 58, "Idempotente", "repetir la llamada no duplica el efecto: mismo folio.", 10.5)
    d.caja(
        s, 444, 328, 236, 40, ROJO_FONDO,
        contenido="Lo que regresa también es entrada: el texto ciudadano vuelve como dato no confiable.",
        tam=9.5, tinta=ROJO, alinear="izq", margen=8,
    )  # fmt: skip
    d.chip(s, 40, 360, "✓ uv run verificar.py 3", ancho=200)

    # 25 · Skills: cómo se empaqueta un MCP con su guía de uso
    s = d.lamina(
        "Un servidor MCP da acceso: tools, datos y acciones. Lo que no da es el método: en qué orden llamarlas, qué "
        "revisar, cómo presentar el resultado. Eso es una skill: una carpeta con un SKILL.md que lleva nombre, "
        "descripción e instrucciones, y puede traer scripts y referencias. Es un estándar abierto (agentskills.io) "
        "que leen Claude, Codex, Gemini CLI y Copilot. La clave es cómo se carga: al iniciar, el agente sólo ve el "
        "nombre y la descripción, unos 50 a 100 tokens; si la tarea coincide, lee el cuerpo, y si hace falta, sus "
        "scripts. Hoy hicimos algo parecido a mano con el CLAUDE.md del repo, pero ese archivo se carga siempre; una "
        "skill sólo cuando sirve, y viaja con el servidor. Por eso se empaquetan juntos: un plugin de Claude Code "
        "trae su .mcp.json y su carpeta skills/. OpenAI lo dice así en su documentación de plugins: el servidor da "
        "información en vivo y acciones controladas; la skill da el flujo alrededor: cuándo llamarlas, en qué orden, "
        "cómo manejar resultados incompletos y qué debe contener la respuesta. Desde septiembre, la extensión de "
        "Skills de MCP (SEP-2640, ya Final) deja que el propio servidor las sirva como recursos skill://, y FastMCP "
        "ya lo trae. En Spot2, Argos publica e instala skills por MCP. Anthropic lo resume: MCP conecta a Claude con "
        "los datos; las skills le enseñan qué hacer con ellos.",
        1,
        seccion="El concepto",
    )
    d.titular(s, "Un MCP da acceso; una skill le enseña a usarlo", h=36)
    d.caja(s, 40, 86, 640, 62, BLANCO, BORDE, radio=0.06)
    d.texto(s, 54, 96, 616, 12, "DEFINICIÓN", 7.5, VERDE, MONO, negrita=True)
    d.texto(
        s, 54, 110, 616, 24,
        "**Skill (Agent Skill)**: una carpeta con un SKILL.md (nombre, descripción e instrucciones) que el agente "
        "carga sólo cuando la tarea lo pide. Estándar abierto: agentskills.io.",
        11, TINTA, interlineado=1.2,
    )  # fmt: skip
    d.caja(s, 40, 160, 300, 140, BLANCO, BORDE, radio=0.05)
    d.texto(s, 54, 168, 276, 16, "Un plugin junta las dos cosas", 11.5, TINTA, negrita=True)
    partes = [
        ("Servidor MCP", AZUL_FONDO, None, AZUL, "qué puede hacer: tools, datos y acciones"),
        ("Skill", VERDE_FONDO, None, VERDE, "cómo usarlo: cuándo, en qué orden y qué revisar"),
        ("Opcional", BLANCO, BORDE, GRIS, "hooks, comandos y subagentes"),
    ]
    for n, (nombre, relleno, borde, tinta, texto) in enumerate(partes):
        y = 192 + n * 34
        d.caja(s, 54, y + 2, 98, 24, relleno, borde, radio=0.5, contenido=nombre, tam=10, tinta=tinta, margen=4)
        d.texto(s, 162, y + 1, 170, 30, texto, 10.5, TINTA, interlineado=1.15)
    d.codigo(
        s, 356, 160, 324, 140,
        "skills/metro-cdmx/SKILL.md\n---\nname: metro-cdmx\ndescription: Preguntas de afluencia del\n"
        "  Metro y Ecobici con el servidor cdmx.\n---\n1. Confirma la estación con buscar_estacion_metro.\n"
        "2. Afluencia = entradas, no ocupación.\n3. Cita la fuente; separa dato y opinión.\n"
        "4. ¿Mapa? actualizar_mapa_ecobici.",
        9.5,
        resaltar=["name: metro-cdmx", "description: Preguntas de afluencia del", "  Metro y Ecobici con el servidor cdmx."],
    )  # fmt: skip
    carga = [
        ("**Al iniciar**: sólo name y description (~100 tokens)", VERDE_FONDO, VERDE),
        ("**Si la tarea coincide**: lee el SKILL.md completo", BLANCO, BORDE),
        ("**Si hace falta**: abre sus scripts y referencias", BLANCO, BORDE),
    ]
    for n, (texto, relleno, borde) in enumerate(carga):
        x = 40 + n * 220
        d.caja(s, x, 312, 200, 34, relleno, borde, radio=0.12, contenido=texto, tam=9.5, alinear="izq", margen=8)
        if n:
            d.linea(s, x - 18, 329, x - 2, 329, GRIS, 1.5, True)
    d.texto(
        s, 40, 356, 640, 36,
        "Se distribuyen juntos en el formato de cada host, no del estándar MCP: plugins de Claude Code (.mcp.json + "
        "skills/), de ChatGPT y Codex, y extensiones de Gemini CLI. Lo estándar: el servidor MCP puede servir sus "
        "skills (extensión SEP-2640; en FastMCP, SkillsDirectoryProvider).",
        9.5, GRIS, interlineado=1.2,
    )  # fmt: skip

    # 26 · Paso 4
    s = d.lamina(
        "[EN VIVO] ¿Claude elige bien? Una evaluación es un conjunto de casos con la respuesta esperada. Diez "
        "preguntas reales, cada una en una sesión de claude -p que solo ve nuestro servidor; se cuenta si llamó la "
        "tool correcta con los argumentos correctos. La primera corrida dio 9 de 10, y el error era de la métrica: "
        "Claude confirmó la estación antes de levantar el reporte, que es lo que pide la descripción. Incluye un "
        "caso que no debe usar tools («¿capital de Francia?»). El paso 4 también agrega Ecobici en vivo, en dos tools: ecobici_cerca_de_metro responde en el chat y actualizar_mapa_ecobici escribe mapa/ecobici.js para el mapa y sólo devuelve un resumen, así el detalle no gasta contexto. Reto: "
        "escriban la pregunta que haga fallar a su servidor y arreglen la descripción, no el prompt. Trabajo a "
        "futuro: la evaluación mide si Claude elige bien; TDQS de Glama "
        "(github.com/glama-ai/tool-definition-quality-score) califica cada definición por separado en seis "
        "dimensiones (propósito, cuándo usarla, comportamiento, parámetros, concisión y completitud) y da una "
        "nota de 1 a 5.",
        3,
        seccion="Paso 4 · Medir",
        paso=4,
    )
    d.titular(s, "Mide si Claude elige bien: 10 preguntas reales, 10 sesiones")
    d.texto(s, 40, 108, 270, 110, "10/10", 90, VERDE, SERIF)
    d.texto(s, 40, 218, 270, 36, "tool y argumentos correctos\nmedido el 17-oct-2026", 11.5, GRIS, interlineado=1.25)
    d.definicion(
        s,
        40,
        260,
        270,
        56,
        "Evaluación (eval)",
        "casos reales con la tool esperada, para medir si Claude elige bien.",
        10.5,
    )
    d.caja(
        s, 330, 116, 350, 92, ROJO_FONDO,
        contenido="**La primera corrida dio 9/10.** Claude confirmó la estación antes de levantar el reporte: fallaba la métrica, no el modelo.",
        tam=13, alinear="izq", margen=14,
    )  # fmt: skip
    d.caja(
        s, 330, 220, 350, 70, VERDE_FONDO,
        contenido="**Si falla de verdad,** itera la descripción y el schema, no el system prompt.",
        tam=13, alinear="izq", margen=14,
    )  # fmt: skip
    d.chip(s, 40, 334, "✓ uv run evaluar.py", ancho=200)
    d.texto(s, 256, 338, 424, 20, "Reto: escribe la pregunta que haga fallar a tu servidor.", 12.5, OCRE)

    # 27 · El mapa
    s = d.lamina(
        "El mismo dato que consulta Claude, ahora para personas: preparar.py exporta la afluencia mensual y "
        "mapa/index.html la dibuja, sin servidor. Abre el mapa y mueve el slider en vivo: abril de 2020 (COVID: "
        "1.37 millones de entradas diarias en toda la red), junio de 2021 (Línea 12 en cero) y octubre de 2022 (la "
        "captura: Línea 12 y la mitad oriente de la Línea 1 en cero). Ojo: afluencia son entradas, no ocupación de "
        "trenes; no le llamen congestión.",
        1,
        seccion="El cierre",
    )
    d.titular(s, "El mismo dato, ahora en un mapa para personas")
    d.imagen(s, RECURSOS / "mapa-oct-2022.png", 40, 96, h=284)
    momentos = [
        ("abr-2020", "COVID: 1.37 millones de entradas diarias en toda la red"),
        ("jun-2021", "Línea 12 en cero hasta dic-2022"),
        ("oct-2022", "Línea 12 y la mitad oriente de la Línea 1 en cero (esta captura)"),
    ]
    for n, (mes, texto) in enumerate(momentos):
        y = 110 + n * 74
        d.texto(s, 420, y, 260, 18, mes, 13, VERDE, MONO, negrita=True)
        d.texto(s, 420, y + 20, 260, 44, texto, 13, TINTA, interlineado=1.2)
    d.texto(
        s,
        420,
        332,
        260,
        40,
        "Círculo = entradas diarias promedio. Anillo vacío = cero. Entradas, no ocupación.",
        10.5,
        GRIS,
        interlineado=1.2,
    )
    d.texto(
        s,
        40,
        388,
        640,
        12,
        "datos.cdmx.gob.mx · Afluencia diaria del Metro CDMX y ubicación de estaciones · CC-BY-4.0",
        8.5,
        GRIS,
        MONO,
    )

    # 28 · En vivo: Claude extiende el mapa
    s = d.lamina(
        "[EN VIVO] Pide esto a Claude en la terminal. Usa afluencia_metro, edita mapa/index.html y en el ensayo "
        "tardó 42 segundos. Recarga el mapa y ve a junio de 2021. Luego lee el aviso con la sala: dice «cerrada tras "
        "el colapso del 3 de mayo de 2021». Ese motivo no viene de la tool, que solo dice 0 entradas: lo añadió el "
        "modelo. Puede ser cierto, pero no es el dato. Separar lo que dice la fuente de lo que añade el modelo es la "
        "última lección.",
        1.5,
        seccion="El cierre",
    )
    d.titular(s, "Claude extiende el mapa; tú lees lo que añade")
    d.codigo(
        s,
        40,
        112,
        640,
        58,
        "«Usa el servidor cdmx para saber cuándo estuvo en cero la Línea 12 y agrega a\n mapa/index.html un aviso que aparezca solo en esos meses.»",
        12,
    )
    for n, etiqueta in enumerate(["afluencia_metro", "edita mapa/index.html", "aviso en el mapa"]):
        x = 40 + n * 176
        d.chip(s, x, 188, etiqueta, [AZUL_FONDO, VERDE_FONDO, OCRE_FONDO][n], [AZUL, VERDE, OCRE][n], 11, ancho=150)
        if n:
            d.linea(s, x - 24, 200, x - 4, 200, GRIS, 1.75, True)
    d.texto(s, 572, 193, 108, 16, "42 s en el ensayo", 10.5, GRIS)
    d.caja(
        s,
        40,
        234,
        310,
        106,
        AZUL_FONDO,
        AZUL,
        radio=0.05,
        contenido="**Lo dice el dato**\nLínea 12: 0 entradas\nde jun-2021 a dic-2022",
        tam=15,
        alinear="izq",
        margen=18,
    )
    d.caja(
        s,
        370,
        234,
        310,
        106,
        ROJO_FONDO,
        ROJO,
        radio=0.05,
        contenido="**Lo añadió el modelo**\n«cerrada tras el colapso del 3 de mayo de 2021»: no viene de la tool",
        tam=15,
        alinear="izq",
        margen=18,
    )

    # 29 · Recap (refleja la lámina «Qué te llevas»)
    s = d.lamina(
        "Volvemos a la lámina del inicio. A la izquierda, lo que construyeron; pide manos: ¿quién llegó al paso 4? "
        "Quien no, tiene los puntos de control en pasos/. A la derecha, las respuestas a las cinco preguntas del "
        "inicio; léelas en voz alta, una por una: 1) el modelo solo pide y tu código ejecuta; MCP estandariza cómo se "
        "publican y descubren las tools. 2) MCP conviene si el modelo decide en runtime, para varios usuarios o sin tu "
        "terminal; si no, CLI o API. 3) Tools por intención y errores que corrigen: el modelo solo lee nombre, "
        "descripción y schema. 4) Si la tool escribe, los controles van en el código. 5) Se mide con preguntas "
        "reales, y hay que separar el dato de lo que añade el modelo.",
        1.5,
        seccion="Recap",
    )
    d.titular(s, "Recap: tienes un servidor MCP y sabes cuándo usarlo")
    tablero(
        d, s,
        [
            "Un servidor MCP con 8 tools, un resource y un prompt (tu servidor.py)",
            "Conectado a Claude Code por HTTP, con una acción que pide tu aprobación",
            "Una evaluación de 10 preguntas (evaluar.py)",
            "Un mapa de 16 años del Metro que Claude extendió con tus tools",
        ],
        [
            "El modelo solo pide; tu código ejecuta. MCP estandariza cómo se publican y descubren las tools.",
            "MCP si el modelo decide en runtime, para varios usuarios o sin tu terminal. Si no, CLI o API.",
            "Por intención y con errores que corrigen: el modelo solo lee nombre, descripción y schema.",
            "En el código: validación, idempotencia, tope y aprobación del host. Nunca solo en el prompt.",
            "Con preguntas reales. Si falla, arregla la descripción, y separa el dato de lo que añade el modelo.",
        ],
        hecho=True,
    )  # fmt: skip
    d.texto(
        s,
        40,
        362,
        640,
        18,
        "Es la lámina del inicio, ahora con respuestas. Repasa en el repo: pasos/01 a 04 y docs/.",
        11.5,
        GRIS,
    )

    # 30 · Ahora te toca
    s = d.lamina(
        "El repo es suyo: cambien el dato, inventen la tool, rompan el mapa. Las ideas son solo puntos de partida. "
        "La última es la que más me importa: lo que hicimos con el Metro es lo mismo que hicimos en Spot2 con "
        "inmuebles, y es lo que pueden hacer mañana con su inventario, su CRM o sus tickets. Pidan que compartan lo "
        "que construyan. Las preguntas de la lluvia del inicio son buenos puntos de partida.",
        0.5,
    )
    d.texto(s, 48, 50, 600, 56, "Ahora te toca", 44, TINTA, SERIF)
    d.texto(s, 48, 110, 600, 24, "Clona, cambia el dato, inventa la tool, rompe el mapa.", 17, GRIS)
    ideas = [
        ("Otro dato", "calidad del aire, *0311, GTFS: 475 conjuntos en datos.cdmx.gob.mx"),
        ("Otra tool", "comparar_estaciones, alerta de cierre, tendencia anual"),
        ("Otra vista", "etiquetas, filtro por línea, cambio contra el año anterior"),
        ("Tu sistema", "tu inventario, tu CRM, tus tickets: como hicimos en Spot2"),
    ]
    for n, (titulo, texto) in enumerate(ideas):
        x = 48 + n * 158
        d.texto(s, x, 186, 144, 22, titulo, 16, TINTA, negrita=True)
        d.texto(s, x, 214, 140, 90, texto, 12.5, GRIS, interlineado=1.3)
    d.texto(
        s, 48, 340, 624, 20, f"Comparte lo que construyas · {REPO.removeprefix('https://')}", 13, VERDE, negrita=True
    )

    # 31 · Cierre: lo que ya se puede conectar hoy (queda en pantalla durante las preguntas)
    s = d.lamina(
        "Gracias. Abro preguntas. Mientras preguntan, esto ya existe y lo pueden conectar hoy. Blender: Claude arma "
        "escenas y modelos 3D (blender-mcp, más de 22 mil estrellas en GitHub). Y se encadena: otro servidor manda "
        "el modelo a una impresora 3D con OctoPrint, Bambu o Prusa; es el ejemplo de la documentación oficial de "
        "MCP. Ableton Live: compone una canción completa, con intro, build-up y drop. Figma: su servidor remoto "
        "oficial lee el diseño para generar código y también escribe en el lienzo. Home Assistant: la integración "
        "oficial deja que Claude o ChatGPT vean y controlen los dispositivos de tu casa. ROS: conecta un modelo con "
        "un robot. Chrome DevTools, de Google: el agente graba un trace y te dice por qué tu página carga lento. Y "
        "dos que uso a diario: Context7, de Upstash, le da al agente la documentación actual y por versión de cada "
        "librería, para que no programe con APIs viejas; Parallel hace búsqueda web para agentes con fuentes, y tiene "
        "otro servidor para investigación profunda. Los dos sirvieron para preparar este taller. Y "
        "cerca de casa: Mercado Pago tiene un servidor oficial para desarrolladores (busca en su documentación, "
        "genera el código del checkout, crea usuarios de prueba y califica tu integración); Mercado Libre también "
        "tiene uno. Los que dicen «remoto» se conectan pegando una URL en Claude o ChatGPT; los locales se instalan "
        "en tu máquina. Ojo: un MCP que mueve tu casa, tu impresora o un robot merece los mismos controles del paso "
        "3. MCP Toplist cuenta 142,221 servidores activos al 15 de octubre de 2026. (La siguiente lámina es un "
        "glosario para consulta; no se presenta.)",
        0.5,
    )
    d.titular(s, "Esto ya lo puedes conectar hoy", y=30, h=34)
    d.texto(
        s, 40, 70, 640, 16,
        "Hay 142,221 servidores MCP activos (MCP Toplist, 15-oct-2026). Algunos que vale la pena probar:", 10.5, GRIS,
    )  # fmt: skip
    casos = [
        ("CREAR EN 3D", "Blender", "«Arma una escena low-poly de una playa con palmeras»", "local · lo instalas"),
        ("FABRICAR", "Impresoras 3D", "«Rebana el modelo de Blender y mándalo a imprimir»", "local · lo instalas"),
        ("MÚSICA", "Ableton Live", "«Haz una canción de house con intro, build-up y drop»", "local · lo instalas"),
        ("DISEÑO", "Figma", "«Convierte este frame en un componente de React»", "remoto · pegas la URL"),
        ("TU CASA", "Home Assistant", "«Apaga todas las luces de la casa»", "URL de tu Home Assistant"),
        ("ROBÓTICA", "Robots con ROS", "«Mueve el brazo a la posición inicial»", "local · lo instalas"),
        ("WEB", "Chrome DevTools", "«¿Por qué carga lento mi página?»", "local · lo instalas"),
        ("DOCS AL DÍA", "Context7", "«¿Cómo monto FastMCP en FastAPI? Usa la doc actual»", "remoto · pegas la URL"),
        ("BÚSQUEDA WEB", "Parallel", "«Investiga quién soporta Agent Skills y cita fuentes»", "remoto · pegas la URL"),
        ("MÉXICO Y LATAM", "Mercado Pago", "«Genera el código de Checkout Pro y crea usuarios de prueba»",
         "remoto · pegas la URL"),
    ]  # fmt: skip
    for n, (categoria, nombre, pedido, conexion) in enumerate(casos):
        x, y = 40 + (n % 5) * 130, 92 + (n // 5) * 120
        remoto = not conexion.startswith("local")
        d.caja(s, x, y, 120, 112, BLANCO, BORDE, radio=0.06)
        d.texto(s, x + 8, y + 9, 104, 10, categoria, 6.5, VERDE, MONO, negrita=True)
        d.texto(s, x + 8, y + 20, 106, 18, nombre, 11.5, TINTA, negrita=True)
        d.texto(s, x + 8, y + 40, 106, 46, pedido, 8.5, OCRE, interlineado=1.15)
        d.caja(
            s, x + 8, y + 88, 104, 16, VERDE_FONDO if remoto else BLANCO, None if remoto else BORDE, radio=0.5,
            contenido=conexion, tam=7, tinta=VERDE if remoto else GRIS, margen=2,
        )  # fmt: skip
    d.imagen(s, foto, 40, 334, 56, 56)
    d.texto(s, 108, 338, 300, 24, "Gracias", 20, VERDE, negrita=True)
    d.texto(s, 108, 366, 440, 20, "Dante Bazaldua · stdout.mx · linkedin.com/in/dantebh", 12.5, GRIS)

    # 32 · Apéndice: buenas prácticas para que las tools se entiendan (no se presenta)
    s = d.lamina(
        "Apéndice para consulta; no se presenta. Cómo saber si un servidor MCP se entiende, en tres pasos. 1) "
        "Diseña para el agente (Phil Schmid, «MCP is not the problem, it's your server», ene-2026; Anthropic, "
        "«Writing effective tools for agents»): resultados y no endpoints (track_order en vez de tres llamadas), "
        "argumentos planos con enums y valores por defecto, entre 5 y 15 tools por servidor, respuestas cortas "
        "y paginadas (limit, has_more) con nombres en vez de IDs, y errores que enseñan: la spec 2026-07-28 "
        "distingue los errores de protocolo de los de ejecución, que van en el resultado con isError para que el "
        "modelo se corrija. La spec también pide nombres de tool de 1 a 128 caracteres (A-Z, a-z, 0-9, _, - y .), "
        "únicos en el servidor, y advierte que las anotaciones (readOnlyHint, destructiveHint…) son pistas: el "
        "cliente debe tratarlas como no confiables. 2) ¿Se entiende? TDQS de Glama califica cada definición en "
        "seis dimensiones con su peso: propósito 25 %, cuándo usarla 20 %, transparencia del comportamiento 20 %, "
        "significado de los parámetros 15 %, concisión 10 % y completitud 10 %; nota de 1 a 5 y nivel de A a F. "
        "OpenAI recomienda que la descripción empiece con «Úsala cuando…» y diga los casos en que no. 3) Mide y "
        "corrige: un golden set con pedidos directos (nombran tu producto), indirectos (describen el resultado) y "
        "negativos (otra tool debería contestar), cada uno con lo esperado (OpenAI, «Optimize metadata»). Anthropic "
        "recomienda medir además del acierto el número de llamadas, los tokens, el tiempo y los errores; leer las "
        "transcripciones, dejar que Claude proponga mejores descripciones y validar con casos que no se usaron para "
        "ajustar. Si falla, se corrige la descripción, no el prompt. En el taller: paso 2 y evaluar.py, con un caso "
        "negativo (¿capital de Francia?).",
        0,
        seccion="Apéndice · Buenas prácticas",
    )
    d.titular(s, "¿Tu tool se entiende? Diseña, describe y mide", h=36)
    columnas = [
        (40, "1 · Diseña para el agente", AZUL),
        (258, "2 · ¿Se entiende? Criterios TDQS", VERDE),
        (476, "3 · Mide y corrige", OCRE),
    ]
    for x, titulo, tinta in columnas:
        d.caja(s, x, 88, 204, 238, BLANCO, BORDE, radio=0.05)
        d.texto(s, x + 12, 98, 184, 18, titulo, 11, tinta, negrita=True)
    d.linea(s, 246, 107, 256, 107, GRIS, 1.5, True)
    d.linea(s, 464, 107, 474, 107, GRIS, 1.5, True)
    listas = [
        (40, [
            "**Resultados, no endpoints**: una tool por intención, no una por endpoint.",
            "**Argumentos planos**: tipos simples, enums y valores por defecto.",
            "**Respuestas cortas**: agrega, pagina y devuelve nombres, no IDs.",
            "**Errores que enseñan**: isError con el siguiente paso; el modelo se corrige.",
        ], "Schmid (ene-2026) · Anthropic · spec MCP 2026-07-28"),
        (476, [
            "**Golden set**: pedidos directos, indirectos y negativos, con lo esperado.",
            "**Mide**: tool y argumentos correctos, llamadas, tokens y errores.",
            "**Lee las transcripciones**: Claude puede proponer mejores descripciones.",
            "**Valida aparte**: con casos que no usaste para ajustar.",
        ], "OpenAI, Optimize metadata · Anthropic, Writing tools for agents"),
    ]  # fmt: skip
    for x, puntos, fuente in listas:
        for n, punto in enumerate(puntos):
            d.texto(s, x + 12, 122 + n * 44, 182, 42, punto, 9.5, TINTA, interlineado=1.15)
        d.texto(s, x + 12, 302, 182, 20, fuente, 7, GRIS, MONO, interlineado=1.1)
    criterios = [
        ("Propósito", "¿qué hace y en qué difiere?", 25),
        ("Cuándo usarla", "«úsala cuando…»", 20),
        ("Comportamiento", "¿qué efectos tiene?", 20),
        ("Parámetros", "¿formato y ejemplos?", 15),
        ("Concisión", "¿lo importante primero?", 10),
        ("Completitud", "¿alcanza para lo que hace?", 10),
    ]
    for n, (nombre, pregunta, peso) in enumerate(criterios):
        y = 122 + n * 29
        d.texto(s, 270, y, 188, 12, f"**{nombre}** · {pregunta}", 8.5, TINTA)
        d.caja(s, 270, y + 14, 150, 6, "E3E7E1", radio=0.5)
        d.caja(s, 270, y + 14, peso / 25 * 150, 6, VERDE, radio=0.5)
        d.texto(s, 426, y + 10, 30, 12, f"{peso} %", 8.5, VERDE, negrita=True)
    d.texto(s, 270, 302, 182, 20, "Nota de 1 a 5 y nivel de A a F (Glama)", 7, GRIS, MONO)
    # Si la medición falla, se vuelve a la descripción.
    d.linea(s, 578, 326, 578, 338, OCRE, 1.25)
    d.linea(s, 578, 338, 360, 338, OCRE, 1.25)
    d.linea(s, 360, 338, 360, 328, OCRE, 1.25, True)
    d.texto(s, 380, 341, 180, 12, "si falla: corrige la descripción, no el prompt", 8.5, OCRE, alinear="centro")
    d.texto(
        s, 40, 360, 414, 24,
        "En el taller: tools por intención y errores que corrigen (paso 2) y evaluar.py con 10 casos, uno negativo "
        "(paso 4). Siguiente: califica tus 8 tools con TDQS.",
        9.5, GRIS, interlineado=1.2,
    )  # fmt: skip

    # 33 · Glosario (apéndice, no se presenta)
    s = d.lamina(
        "Apéndice para consulta: no se presenta. Está aquí para quien revise las láminas después.",
        0,
        seccion="Apéndice · Glosario",
    )
    d.titular(s, "Glosario del taller")
    terminos = [
        ("LLM", "predice el texto que sigue a un texto"),
        ("Tool", "el modelo la pide; tu código la ejecuta"),
        ("Function calling", "la petición: tool + argumentos JSON"),
        ("Agente", "repite pedir tool → leer → decidir"),
        ("MCP", "estándar abierto: apps de IA ↔ sistemas"),
        ("Host", "app donde conversas: Claude Code, Desktop"),
        ("Client", "conector del host a un solo servidor"),
        ("Server", "expone tools, resources y prompts"),
        ("Transporte", "por dónde viajan: stdio o HTTP"),
        ("JSON-RPC", "formato de los mensajes de MCP"),
        ("OAuth 2.1", "autorización por usuario en HTTP"),
        ("Elicitation", "el servidor pide un dato a la persona"),
        ("Resource", "dato de solo lectura con URI"),
        ("Prompt", "plantilla que tú ejecutas (comando /)"),
        ("Skill", "guía SKILL.md; el agente la carga si aplica"),
        ("API", "interfaz para que un programa use a otro"),
        ("CLI", "programa de terminal: git, gh, kubectl"),
        ("FastMCP", "librería de Python para servidores MCP"),
        ("uv", "instala Python y dependencias, y ejecuta"),
        ("Schema", "tipos y límites de los parámetros"),
        ("Docstring", "descripción de la tool que lee el modelo"),
        ("Contexto", "lo que el modelo tiene presente; finito"),
        ("Idempotente", "repetirla no duplica el efecto"),
        ("Eval", "casos con respuesta esperada para medir"),
        ("Prompt injection", "instrucciones ocultas en datos o tools"),
    ]
    for n, (termino, texto) in enumerate(terminos):
        x, y = 40 + (n // 13) * 330, 100 + (n % 13) * 23
        d.texto(s, x, y, 104, 18, termino, 10.5, VERDE, negrita=True)
        d.texto(s, x + 104, y, 222, 18, texto, 10, TINTA)

    # 34 · Para aprender más: referencias y enlaces (no se presenta)
    s = d.lamina(
        "Apéndice para consulta; no se presenta. Las referencias para seguir aprendiendo, agrupadas. Todos los "
        "enlaces se comprobaron el 19-oct-2026 y son clicables en Slides y en el PDF. Las demás fuentes del taller "
        "(benchmarks, casos, datos) están en docs/fuentes-mcp-api-cli.md del repo.",
        0,
        seccion="Apéndice · Para aprender más",
    )
    d.titular(s, "Para aprender más", h=36)
    grupos = [
        ("MCP, la fuente", VERDE, [
            ("Qué es MCP", "https://modelcontextprotocol.io/docs/2026-07-28/getting-started/intro"),
            ("Especificación 2026-07-28", "https://modelcontextprotocol.io/specification/2026-07-28"),
            ("Registry oficial de servidores", "https://registry.modelcontextprotocol.io"),
        ]),
        ("Construir", AZUL, [
            ("FastMCP", "https://gofastmcp.com"),
            ("Claude Code y MCP", "https://code.claude.com/docs/en/mcp"),
            ("uv", "https://docs.astral.sh/uv/"),
        ]),
        ("Diseñar tools", OCRE, [
            ("Writing effective tools for agents · Anthropic", "https://www.anthropic.com/engineering/writing-tools-for-agents"),
            ("MCP best practices · Phil Schmid", "https://www.philschmid.de/mcp-best-practices"),
            ("Code execution with MCP · Anthropic", "https://www.anthropic.com/engineering/code-execution-with-mcp"),
        ]),
        ("Medir", OCRE, [
            ("Demystifying evals for AI agents · Anthropic", "https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents"),
            ("Optimize metadata · OpenAI", "https://developers.openai.com/plugins/guides/optimize-metadata"),
            ("Tool Definition Quality Score · Glama", "https://github.com/glama-ai/tool-definition-quality-score"),
        ]),
        ("Skills y empaquetado", VERDE, [
            ("Agent Skills", "https://agentskills.io"),
            ("Skills sobre MCP · SEP-2640", "https://modelcontextprotocol.io/seps/2640-skills-extension"),
            ("MCP Bundles (.mcpb)", "https://github.com/modelcontextprotocol/mcpb"),
        ]),
        ("Descubrir servidores", AZUL, [
            ("Conectores de Claude", "https://claude.com/connectors"),
            ("Glama", "https://glama.ai/mcp/servers"),
            ("MCP Toplist", "https://mcptoplist.com"),
        ]),
    ]  # fmt: skip
    for n, (titulo, tinta, enlaces) in enumerate(grupos):
        x, y = 40 + (n % 2) * 330, 80 + (n // 2) * 89
        d.texto(s, x, y, 310, 14, titulo, 10.5, tinta, negrita=True)
        for k, (etiqueta, url) in enumerate(enlaces):
            yy = y + 18 + k * 21
            d.texto(s, x, yy, 310, 11, etiqueta, 8.5, TINTA)
            caja = d.texto(s, x, yy + 10, 310, 10, url.removeprefix("https://").removeprefix("www."), 6.5, GRIS, MONO)
            for corrida in caja.text_frame.paragraphs[0].runs:
                corrida.hyperlink.address = url
    d.texto(
        s, 40, 348, 640, 30,
        f"**Este taller**: {REPO.removeprefix('https://')} · todas las fuentes, decisiones y pruebas, en docs/ · "
        "datos: datos.cdmx.gob.mx",
        10, TINTA, interlineado=1.2,
    )  # fmt: skip
    d.texto(s, 40, 384, 640, 10, "Enlaces comprobados el 19-oct-2026", 7.5, GRIS, MONO)

    if d.minutos != 40:
        raise ValueError(f"Los tiempos suman {d.minutos:g} min, no 40")
    return d


# --- Drive ----------------------------------------------------------------------


def binario_gws() -> str:
    """En esta máquina, el envoltorio de Node de `gws` muere (SIGKILL) con un --json de más de ~1 KB.
    El binario nativo que trae el paquete npm no tiene ese problema."""
    ruta = Path(shutil.which("gws") or "gws").resolve()
    nativo = ruta.parent / "bin" / "gws"
    return str(nativo if nativo.exists() else ruta)


def gws(*argumentos: str) -> dict:
    resultado = subprocess.run([binario_gws(), *argumentos], capture_output=True, text=True, check=False)
    if resultado.returncode:
        raise SystemExit(
            f"gws {' '.join(argumentos[:3])} falló:\n{resultado.stdout[-1500:]}\n{resultado.stderr[-1500:]}"
        )
    return json.loads(resultado.stdout) if resultado.stdout.strip() else {}


def subir(pptx: Path) -> str:
    """Reemplaza el contenido de la presentación existente con el .pptx (Drive lo convierte)."""
    ids = json.loads(IDS.read_text()) if IDS.exists() else {}
    if "presentacion" in ids:
        gws(
            "drive", "files", "update", "--params", json.dumps({"fileId": ids["presentacion"]}),
            "--json", "{}", "--upload", str(pptx), "--upload-content-type", PPTX_MIME,
        )  # fmt: skip
        return ids["presentacion"]
    if "carpeta" not in ids:
        ids["carpeta"] = gws(
            "drive", "files", "create", "--json",
            json.dumps({"name": "Taller MCP · Claude CDMX", "mimeType": "application/vnd.google-apps.folder"}),
        )["id"]  # fmt: skip
    metadatos = {"name": TITULO, "mimeType": "application/vnd.google-apps.presentation", "parents": [ids["carpeta"]]}
    ids["presentacion"] = gws(
        "drive",
        "files",
        "create",
        "--json",
        json.dumps(metadatos),
        "--upload",
        str(pptx),
        "--upload-content-type",
        PPTX_MIME,
    )["id"]
    IDS.write_text(json.dumps(ids, indent=2))
    return ids["presentacion"]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--local", action="store_true", help="solo genera el .pptx, sin subirlo")
    args = parser.parse_args()

    SALIDA.mkdir(exist_ok=True)
    deck = construir_deck()
    pptx = SALIDA / "taller-mcp.pptx"
    deck.prs.save(pptx)
    print(f"{len(deck.prs.slides)} láminas · {deck.minutos:g} min · {pptx.relative_to(RAIZ.parent)}")
    if args.local:
        return

    pid = subir(pptx)
    pdf = SALIDA / "taller-mcp.pdf"
    time.sleep(20)  # recién subido, Drive puede exportar todavía la versión anterior
    gws(
        "drive",
        "files",
        "export",
        "--params",
        json.dumps({"fileId": pid, "mimeType": "application/pdf"}),
        "--output",
        str(pdf),
    )
    print(f"Listo: https://docs.google.com/presentation/d/{pid}/edit")
    print(f"PDF para revisar: {pdf.relative_to(RAIZ.parent)}")


if __name__ == "__main__":
    main()
