"""
graficas.py — Gráficas de resultados (PNG).

  graficar_contorno():   media sección de la tobera con sus cotas principales
  graficar_presiones():  p/p0 a lo largo de la tobera para cada presión exterior
  graficar_mach():       M(x) para cada presión exterior

Cada presión exterior conserva su color en todas las gráficas.
"""

import matplotlib

matplotlib.use("Agg")  # genera archivos sin abrir ventanas
import matplotlib.pyplot as plt
import numpy as np

from geometria import contorno_exterior, muestrear

# Paleta categórica (orden fijo) y tintas para texto y ejes
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
TINTA = "#0b0b0b"
TINTA_2 = "#52514e"
REJILLA = "#e6e5e0"
PARED = "#c9c6bd"

NOMBRES_REGIMEN = {
    "subsonico": "subsónico",
    "estrangulado_subsonico": "estrangulado subsónico",
    "choque_interno": "choque interno",
    "choque_en_salida": "choque en la salida",
    "sobreexpandida": "sobreexpandida",
    "adaptada": "adaptada",
    "subexpandida": "subexpandida",
}


def _estilo_ejes(ax):
    ax.grid(True, color=REJILLA, linewidth=0.8)
    ax.set_axisbelow(True)
    for lado in ("top", "right"):
        ax.spines[lado].set_visible(False)
    for lado in ("left", "bottom"):
        ax.spines[lado].set_color(TINTA_2)
    ax.tick_params(colors=TINTA_2, labelsize=9)
    ax.xaxis.label.set_color(TINTA)
    ax.yaxis.label.set_color(TINTA)


def _dibujar_tobera(ax, tramos, espesor, pared, completa=True):
    """Pared de la tobera (relleno gris) en mm; completa = ambas mitades."""
    xi, ri = muestrear(tramos)
    xe, re = muestrear(contorno_exterior(tramos, espesor, pared))
    if pared == "cilindrica":
        re = np.interp(xi, xe, re)
        xe = xi
    re_i = np.interp(xi, xe, re)
    signos = (1, -1) if completa else (1,)
    for s in signos:
        ax.fill_between(xi * 1e3, s * ri * 1e3, s * re_i * 1e3, color=PARED, linewidth=0)
        ax.plot(xi * 1e3, s * ri * 1e3, color=TINTA, linewidth=1.2)
    ax.axhline(0, color=TINTA_2, linewidth=0.8, linestyle=(0, (6, 3, 1, 3)))


def _cota_vertical(ax, x, r, texto, lado="derecha"):
    ax.annotate("", xy=(x, r), xytext=(x, -r),
                arrowprops=dict(arrowstyle="<->", color=TINTA, linewidth=1))
    dx = 0.8 if lado == "derecha" else -0.8
    ax.text(x + dx, 0, texto, color=TINTA, fontsize=10, va="center",
            ha="left" if lado == "derecha" else "right",
            bbox=dict(facecolor="white", edgecolor="none", pad=1.5))


def graficar_contorno(tramos, diseno, geo, espesor, pared, ruta):
    """Media sección de la tobera con D*, De, D entrada y longitud total."""
    fig, ax = plt.subplots(figsize=(9, 5.2))
    _dibujar_tobera(ax, tramos, espesor, pared)

    x_ini, x_fin = geo["x_entrada"] * 1e3, geo["x_salida"] * 1e3
    r_in, r_t, r_e = geo["r_entrada"] * 1e3, geo["r_garganta"] * 1e3, geo["r_salida"] * 1e3
    _cota_vertical(ax, 0.0, r_t, f"D* = {2*r_t:.2f} mm", lado="izquierda")
    _cota_vertical(ax, x_fin, r_e, f"Dₑ = {2*r_e:.2f} mm")
    _cota_vertical(ax, x_ini + 2.0, r_in, f"D entrada = {2*r_in:.2f} mm")

    y_L = r_in + espesor * 1e3 + 3.0
    ax.annotate("", xy=(x_ini, y_L), xytext=(x_fin, y_L),
                arrowprops=dict(arrowstyle="<->", color=TINTA, linewidth=1))
    ax.text((x_ini + x_fin) / 2, y_L + 0.8, f"L = {geo['L_total']*1e3:.2f} mm",
            color=TINTA, fontsize=10, ha="center", va="bottom")

    ax.set_aspect("equal")
    ax.set_xlabel("x [mm]  (garganta en x = 0)")
    ax.set_ylabel("r [mm]")
    ax.set_title(f"Geometría de la tobera · Aₑ/A* = {diseno['Ae_At']:.3f}",
                 color=TINTA, fontsize=12, loc="left")
    _estilo_ejes(ax)
    ax.set_xlim(x_ini - 3, x_fin + 14)
    ax.set_ylim(-(r_in + espesor * 1e3) - 2, y_L + 5)
    fig.tight_layout()
    fig.savefig(ruta, dpi=200)
    plt.close(fig)


SUPERSONICOS = ("choque_en_salida", "sobreexpandida", "adaptada", "subexpandida")


def _series(distribuciones):
    """
    Curvas a dibujar. Si pb <= p2 el flujo dentro de la tobera es el mismo
    (supersónico e isentrópico hasta la salida) para cualquier pb: lo que
    cambia ocurre fuera. Esas presiones se agrupan en una sola curva.
    """
    series, grupo = [], []
    for d in distribuciones:
        if d["regimen"] in SUPERSONICOS:
            grupo.append(d)
        else:
            series.append((d, f"{d['pb']/1e3:.1f} kPa · {NOMBRES_REGIMEN[d['regimen']]}"))
    if grupo:
        pbs = ", ".join(f"{d['pb']/1e3:.1f}" for d in grupo)
        series.append((grupo[0], f"{pbs} kPa · supersónico en toda la tobera\n"
                                 f"(mismo flujo interior; difieren fuera)"))
    return series


def _grafica_distribucion(tramos, espesor, pared, x, distribuciones, clave, escala,
                          etiqueta_y, titulo, ruta, referencia=None):
    """Plantilla común: tobera arriba (contexto) y la variable abajo."""
    fig, (ax0, ax) = plt.subplots(2, 1, figsize=(10, 7), sharex=True,
                                  gridspec_kw={"height_ratios": [1, 3.2]})
    _dibujar_tobera(ax0, tramos, espesor, pared)
    r_max = max(contorno_exterior(tramos, espesor, pared)[0]["p0"][1],
                contorno_exterior(tramos, espesor, pared)[-1]["p1"][1]) * 1e3
    ax0.set_ylim(-1.1 * r_max, 1.1 * r_max)
    ax0.axis("off")

    for i, (d, etiqueta) in enumerate(_series(distribuciones)):
        color = SERIES[i % len(SERIES)]
        ax.plot(x * 1e3, d[clave] * escala, color=color, linewidth=2, label=etiqueta)
        if d["x_choque"] is not None:
            xs = d["x_choque"] * 1e3
            ax.axvline(xs, color=color, linewidth=1, linestyle=":")
            ax0.axvline(xs, color=color, linewidth=1.5, linestyle=":")

    if referencia is not None:
        valor, texto = referencia
        ax.axhline(valor, color=TINTA_2, linewidth=1, linestyle="--")
        ax.text(x[0] * 1e3, valor * 1.02, f" {texto}", color=TINTA_2, fontsize=9, va="bottom")

    ax.axvline(0, color=TINTA_2, linewidth=0.8, linestyle=(0, (6, 3, 1, 3)))
    ax.set_xlabel("x [mm]  (garganta en x = 0; líneas punteadas: posición del choque)")
    ax.set_ylabel(etiqueta_y)
    ax.set_title(titulo, color=TINTA, fontsize=12, loc="left")
    _estilo_ejes(ax)
    leyenda = ax.legend(title="Presión exterior p_b", fontsize=9, title_fontsize=9,
                        frameon=False, loc="center left", bbox_to_anchor=(1.01, 0.5))
    for texto in leyenda.get_texts():
        texto.set_color(TINTA)
    fig.tight_layout()
    fig.savefig(ruta, dpi=200, bbox_inches="tight")
    plt.close(fig)


def graficar_presiones(tramos, espesor, pared, x, distribuciones, p0, ruta):
    """p/p0 a lo largo de la tobera, una curva por presión exterior."""
    _grafica_distribucion(tramos, espesor, pared, x, distribuciones, "p", 1.0 / p0,
                          "p / p₀", "Presión estática a lo largo de la tobera", ruta)


def graficar_mach(tramos, espesor, pared, x, distribuciones, ruta):
    """Número de Mach a lo largo de la tobera, una curva por presión exterior."""
    _grafica_distribucion(tramos, espesor, pared, x, distribuciones, "M", 1.0,
                          "M", "Número de Mach a lo largo de la tobera", ruta,
                          referencia=(1.0, "M = 1"))
