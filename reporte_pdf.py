"""
reporte_pdf.py — Reporte técnico del caso en PDF (un clic desde la interfaz).

Usa solo matplotlib (ya es dependencia): una hoja de datos con el
dimensionamiento, las presiones críticas y el análisis por presión exterior,
seguida de las figuras que main.guardar() deja en salidas/<caso>/.
Fondo blanco para imprimir.
"""

import io
from datetime import date

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

from analisis_dimensional import reynolds_garganta
from main import NOMBRES_REGIMEN

TAMANO_CARTA = (8.5, 11)
NARANJA = "#E8590C"
GRIS = "#52525B"
TINTA = "#18181B"
FIGURAS = (("contorno.png", "Geometría de la tobera"),
           ("presiones.png", "Presión estática a lo largo de la tobera"),
           ("mach.png", "Número de Mach a lo largo de la tobera"))


def _encabezado(fig, titulo, pagina):
    fig.text(0.07, 0.955, "TOBERA-CD", fontsize=13, fontweight="bold", color=TINTA)
    fig.text(0.215, 0.955, "· Reporte técnico", fontsize=11, color=GRIS)
    fig.text(0.93, 0.955, f"Pág. {pagina}", fontsize=9, color=GRIS, ha="right")
    fig.add_artist(plt.Line2D([0.07, 0.93], [0.945, 0.945], color=NARANJA, linewidth=1.5))
    fig.text(0.07, 0.915, titulo, fontsize=15, fontweight="bold", color=TINTA)


def _pie(fig):
    fig.text(0.07, 0.03, "Modelo cuasi-1D isentrópico con choque normal · Mecánica de Fluidos, "
                         "ENES Juriquilla, UNAM", fontsize=7.5, color=GRIS)
    fig.text(0.93, 0.03, date.today().isoformat(), fontsize=7.5, color=GRIS, ha="right")


def _tabla(fig, y, titulo, filas, anchos, alto_fila=0.022):
    """Tabla simple con texto. filas[0] es la cabecera. Devuelve la y siguiente."""
    fig.text(0.07, y, titulo.upper(), fontsize=8.5, fontweight="bold", color=NARANJA)
    y -= 0.012
    x0 = 0.07
    for i, fila in enumerate(filas):
        y -= alto_fila
        x = x0
        for j, (valor, ancho) in enumerate(zip(fila, anchos)):
            derecha = j > 0  # valores y unidades alineados a la derecha
            fig.text(x + (ancho - 0.01 if derecha else 0), y, str(valor),
                     fontsize=8.5 if i else 7.5, ha="right" if derecha else "left",
                     color=TINTA if i else GRIS, fontweight="bold" if i == 0 else "normal",
                     family="monospace" if derecha and i > 0 else "sans-serif")
            x += ancho
        if i == 0:
            fig.add_artist(plt.Line2D([x0, x0 + sum(anchos)], [y - 0.007, y - 0.007],
                                      color="#D4D4D8", linewidth=0.8))
    return y - 0.04


def generar_pdf(caso, res, salida=None):
    """Devuelve el PDF como bytes. 'salida' es la carpeta con los PNG del caso."""
    d, c, geo = res["diseno"], res["criticas"], res["geometria"]
    p0, T0 = caso["camara"]["p0_Pa"], caso["camara"]["T0_K"]
    g, R = caso["gas"]["gamma"], caso["gas"]["R"]
    re = reynolds_garganta(p0, T0, d["Dt"], g, R)

    buffer = io.BytesIO()
    with PdfPages(buffer) as pdf:
        # Hoja 1: datos del caso
        fig = plt.figure(figsize=TAMANO_CARTA)
        _encabezado(fig, caso["nombre"], 1)
        fig.text(0.07, 0.89, caso.get("descripcion", ""), fontsize=9.5, color=GRIS)

        y = 0.85
        y = _tabla(fig, y, "Condiciones de diseño", [
            ("Parámetro", "Valor", "Unidad"),
            ("Relación de calores específicos γ", f"{g:.3f}", "–"),
            ("Constante del gas R", f"{R:.1f}", "J/(kg·K)"),
            ("Presión de cámara p0", f"{p0/1e6:.3f}", "MPa"),
            ("Temperatura de cámara T0", f"{T0:.1f}", "K"),
            ("Presión ambiente de diseño pa", f"{caso['pa_Pa']/1e3:.2f}", "kPa"),
            ("Empuje requerido F", f"{caso['empuje_requerido_N']:.2f}", "N"),
        ], (0.5, 0.2, 0.16))
        y = _tabla(fig, y, "Dimensionamiento (expansión ideal)", [
            ("Magnitud", "Valor", "Unidad"),
            ("Mach de salida Me", f"{d['Me']:.4f}", "–"),
            ("Relación de áreas Ae/A*", f"{d['Ae_At']:.4f}", "–"),
            ("Velocidad de salida Ve", f"{d['Ve']:.1f}", "m/s"),
            ("Gasto másico", f"{d['m']:.5f}", "kg/s"),
            ("Diámetro de garganta D*", f"{d['Dt']*1e3:.3f}", "mm"),
            ("Diámetro de salida De", f"{d['De']*1e3:.3f}", "mm"),
            ("Longitud total", f"{geo['L_total']*1e3:.3f}", "mm"),
            ("Coeficiente de empuje C_F", f"{d['CF']:.4f}", "–"),
            ("Reynolds en la garganta Re*", f"{re['Re']:.3e}", "–"),
        ], (0.5, 0.2, 0.16))
        y = _tabla(fig, y, "Presiones críticas", [
            ("Presión", "Valor", "Unidad"),
            ("p1 · subsónica con M = 1 en la garganta", f"{c['p1']/1e3:.2f}", "kPa"),
            ("p2 · choque normal en la salida", f"{c['p2']/1e3:.2f}", "kPa"),
            ("p3 · expansión ideal", f"{c['p3']/1e3:.2f}", "kPa"),
        ], (0.5, 0.2, 0.16))
        filas = [("p_b [kPa]", "Régimen", "Me", "ṁ [kg/s]", "F [N]", "x choque [mm]")]
        for a in res["analisis"]:
            x_ch = "–" if a["x_choque_mm"] is None else f"{a['x_choque_mm']:.2f}"
            filas.append((f"{a['pb_Pa']/1e3:.1f}", NOMBRES_REGIMEN[a["regimen"]],
                          f"{a['Me']:.3f}", f"{a['m_kg_s']:.4f}", f"{a['F_N']:.2f}", x_ch))
        # La columna de régimen es texto: se alinea a la izquierda
        _tabla_analisis(fig, y, filas)
        _pie(fig)
        pdf.savefig(fig)
        plt.close(fig)

        # Hojas siguientes: figuras del caso
        pagina = 2
        for archivo, titulo in FIGURAS:
            ruta = None if salida is None else salida / archivo
            if ruta is None or not ruta.exists():
                continue
            fig = plt.figure(figsize=TAMANO_CARTA)
            _encabezado(fig, titulo, pagina)
            ax = fig.add_axes([0.07, 0.12, 0.86, 0.76])
            ax.imshow(plt.imread(str(ruta)))
            ax.axis("off")
            _pie(fig)
            pdf.savefig(fig)
            plt.close(fig)
            pagina += 1

        info = pdf.infodict()
        info["Title"] = f"TOBERA-CD · {caso['nombre']}"
        info["Subject"] = "Reporte técnico de tobera convergente–divergente"
    return buffer.getvalue()


def _tabla_analisis(fig, y, filas):
    fig.text(0.07, y, "ANÁLISIS POR PRESIÓN EXTERIOR", fontsize=8.5, fontweight="bold",
             color=NARANJA)
    y -= 0.012
    anchos = (0.12, 0.3, 0.1, 0.12, 0.1, 0.12)
    for i, fila in enumerate(filas):
        y -= 0.022
        x = 0.07
        for j, (valor, ancho) in enumerate(zip(fila, anchos)):
            izquierda = j == 1
            fig.text(x if izquierda else x + ancho - 0.01, y, str(valor),
                     fontsize=8.5 if i else 7.5, ha="left" if izquierda else "right",
                     color=TINTA if i else GRIS, fontweight="bold" if i == 0 else "normal",
                     family="sans-serif" if izquierda or i == 0 else "monospace")
            x += ancho
        if i == 0:
            fig.add_artist(plt.Line2D([0.07, 0.07 + sum(anchos)], [y - 0.007, y - 0.007],
                                      color="#D4D4D8", linewidth=0.8))
