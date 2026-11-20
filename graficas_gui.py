"""
graficas_gui.py — Gráficas interactivas (Plotly) para la interfaz gráfica.

  figura_geometria():    media sección de la tobera con su pared
  figura_distribucion(): p(x) o M(x) para cada presión exterior
  figura_superpuesta():  código contra SolidWorks para una variable
  figura_error():        diferencia absoluta o error porcentual contra x

Misma paleta que graficas.py: azul para el modelo 1D, carmesí para los
datos de SolidWorks y verde azulado para la diferencia. Longitudes en mm.
"""

import numpy as np
import plotly.graph_objects as go

from geometria import contorno_exterior, muestrear
from graficas import AZUL, CARMESI, EJES, PARED, REJILLA, SERIES, TEAL, TINTA, TINTA_2, _series

COLOR_SW = CARMESI
COLOR_CODIGO = AZUL
FUENTE = dict(family="Inter, 'Segoe UI', Helvetica, Arial, sans-serif", size=13, color=TINTA)
ETIQUETA_X = "x [mm]  (garganta en x = 0)"


def _estilo(fig, titulo, alto=420):
    fig.update_layout(
        title=dict(text=titulo, x=0.0, xanchor="left", font=dict(size=15)),
        font=FUENTE,
        template="plotly_white",
        # Fondo y textos fijos: así se leen igual con el tema claro u oscuro de Streamlit
        paper_bgcolor="white",
        plot_bgcolor="white",
        height=alto,
        margin=dict(l=70, r=20, t=60, b=55),
        hovermode="x unified",
        legend=dict(bgcolor="white", bordercolor=REJILLA, borderwidth=1,
                    font=dict(color=TINTA, size=12), title_font=dict(color=TINTA, size=12)),
        hoverlabel=dict(bgcolor="white", font=dict(color=TINTA)),
    )
    eje = dict(showgrid=True, gridcolor=REJILLA, gridwidth=1, zeroline=False,
               minor=dict(showgrid=True, gridcolor=REJILLA, gridwidth=0.5, ticks="outside",
                          ticklen=3, tickcolor=EJES),
               showline=True, linecolor=EJES, linewidth=1, mirror=True,
               ticks="outside", tickcolor=EJES, tickfont=dict(color=TINTA, size=12),
               title_font=dict(color=TINTA, size=13))
    fig.update_xaxes(**eje)
    fig.update_yaxes(**eje)
    return fig


def _linea_garganta(fig):
    fig.add_vline(x=0, line=dict(color=TINTA_2, width=1, dash="dashdot"))


# ---------------------------------------------------------------------
# Geometría
# ---------------------------------------------------------------------

def figura_geometria(tramos, geo, diseno, espesor, pared):
    """Perfil 2D de la tobera: r contra x, con ambas mitades y la pared."""
    xi, ri = muestrear(tramos)
    xe, re = muestrear(contorno_exterior(tramos, espesor, pared))
    re_i = np.interp(xi, xe, re)
    x_mm, ri_mm, re_mm = xi * 1e3, ri * 1e3, re_i * 1e3

    fig = go.Figure()
    for signo in (1, -1):
        fig.add_trace(go.Scatter(
            x=np.concatenate([x_mm, x_mm[::-1]]),
            y=signo * np.concatenate([ri_mm, re_mm[::-1]]),
            fill="toself", fillcolor=PARED, line=dict(width=0), hoverinfo="skip"))
        fig.add_trace(go.Scatter(
            x=x_mm, y=signo * ri_mm, mode="lines", line=dict(color=AZUL, width=2.5),
            hovertemplate="x = %{x:.2f} mm<br>r = %{y:.3f} mm<extra></extra>"))
    fig.add_hline(y=0, line=dict(color=TINTA_2, width=1, dash="dashdot"))
    _linea_garganta(fig)

    for x, r, texto, pos in (
        (0.0, geo["r_garganta"], f"D* = {2e3*geo['r_garganta']:.2f} mm", "bottom center"),
        (geo["x_salida"] * 1e3, geo["r_salida"], f"D salida = {2e3*geo['r_salida']:.2f} mm",
         "middle right"),
        (geo["x_entrada"] * 1e3, geo["r_entrada"], f"D entrada = {2e3*geo['r_entrada']:.2f} mm",
         "bottom right"),
    ):
        fig.add_trace(go.Scatter(x=[x], y=[r * 1e3], mode="markers+text", text=[texto],
                                 textposition=pos, marker=dict(color=TINTA, size=7),
                                 hoverinfo="skip"))

    largo = x_mm[-1] - x_mm[0]
    r_max = 1.15 * re_mm.max()
    _estilo(fig, f"Perfil de la tobera  ·  Aₑ/A* = {diseno['Ae_At']:.3f}  ·  "
                 f"L = {geo['L_total']*1e3:.2f} mm", alto=420)
    fig.update_layout(hovermode="closest", showlegend=False)
    fig.update_xaxes(title_text=ETIQUETA_X, range=[x_mm[0] - 0.05 * largo, x_mm[-1] + 0.25 * largo])
    fig.update_yaxes(title_text="r [mm]", range=[-r_max, r_max])
    return fig


# ---------------------------------------------------------------------
# Distribuciones
# ---------------------------------------------------------------------

def figura_distribucion(x, distribuciones, variable):
    """
    variable = "p" (presión estática en kPa) o "M" (Mach).
    Las presiones exteriores con el mismo flujo interior se agrupan en una
    curva (igual que en los PNG). Las líneas punteadas marcan el choque.
    """
    fig = go.Figure()
    for i, (d, etiqueta) in enumerate(_series(distribuciones)):
        color = SERIES[i % len(SERIES)]
        if variable == "p":
            y, formato = d["p"] / 1e3, "p = %{y:.2f} kPa"
        else:
            y, formato = d["M"], "M = %{y:.4f}"
        fig.add_trace(go.Scatter(x=x * 1e3, y=y, mode="lines",
                                 name=etiqueta.replace("\n", " "),
                                 line=dict(color=color, width=2.5),
                                 hovertemplate=f"{formato}<extra></extra>"))
        if d["x_choque"] is not None:
            fig.add_vline(x=d["x_choque"] * 1e3, line=dict(color=color, width=1.5, dash="dot"))
    _linea_garganta(fig)

    if variable == "p":
        titulo, eje_y = "Presión estática a lo largo de la tobera", "Presión estática p [kPa]"
    else:
        titulo, eje_y = "Número de Mach a lo largo de la tobera", "Número de Mach M [–]"
        fig.add_hline(y=1, line=dict(color=TINTA_2, width=1, dash="dash"),
                      annotation_text="M = 1", annotation_position="bottom left")

    _estilo(fig, titulo, alto=440)
    fig.update_layout(legend=dict(title="Presión exterior p_b", orientation="h",
                                  yanchor="top", y=-0.22, xanchor="left", x=0))
    fig.update_layout(margin=dict(l=70, r=20, t=60, b=120))
    fig.update_xaxes(title_text=ETIQUETA_X + "; punteado: choque normal")
    fig.update_yaxes(title_text=eje_y)
    return fig


# ---------------------------------------------------------------------
# Comparación con SolidWorks
# ---------------------------------------------------------------------

def figura_superpuesta(x_modelo_mm, y_modelo, comp, nombre, unidad):
    """Curva del código y datos del CSV de SolidWorks."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x_modelo_mm, y=y_modelo, mode="lines", name="Código",
                             line=dict(color=COLOR_CODIGO, width=2.5),
                             hovertemplate="%{y:.4g}<extra>Código</extra>"))
    fig.add_trace(go.Scatter(x=comp["x_csv"], y=comp["y_csv"], mode="lines+markers",
                             name="SolidWorks",
                             line=dict(color=COLOR_SW, width=1.5, dash="dash"),
                             marker=dict(color=COLOR_SW, size=5, symbol="circle-open"),
                             hovertemplate="%{y:.4g}<extra>SolidWorks</extra>"))
    _linea_garganta(fig)
    _estilo(fig, f"{nombre}: código contra SolidWorks")
    fig.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    fig.update_xaxes(title_text=ETIQUETA_X)
    fig.update_yaxes(title_text=f"{nombre} [{unidad}]")
    return fig


def figura_error(comp, nombre, unidad, modo="porcentual"):
    """Error entre métodos contra x: 'porcentual' o 'absoluto' (código − SolidWorks)."""
    if modo == "porcentual":
        y, eje = comp["error_pct"], "Error relativo [%]"
        titulo = f"{nombre}: error relativo (código − SW) / |SW|"
        formato = "%{y:.2f} %"
    else:
        y, eje = comp["diferencia"], f"Diferencia código − SW [{unidad}]"
        titulo = f"{nombre}: diferencia absoluta (código − SW)"
        formato = f"%{{y:.4g}} {unidad}"
    fig = go.Figure(go.Scatter(x=comp["x"], y=y, mode="lines", line=dict(color=TEAL, width=2),
                               fill="tozeroy", fillcolor="rgba(13,148,136,0.12)",
                               hovertemplate=f"{formato}<extra></extra>"))
    fig.add_hline(y=0, line=dict(color=TINTA_2, width=1))
    _linea_garganta(fig)
    _estilo(fig, titulo)
    fig.update_layout(showlegend=False)
    fig.update_xaxes(title_text=ETIQUETA_X)
    fig.update_yaxes(title_text=eje)
    return fig
