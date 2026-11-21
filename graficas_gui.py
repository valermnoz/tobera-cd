"""
graficas_gui.py — Gráficas interactivas (Plotly) para la interfaz gráfica.

  figura_geometria():       media sección de la tobera con su pared
  figura_distribucion():    p(x) o M(x) para cada presión exterior
  figura_campo():           tobera coloreada con M(x) o p(x), tipo CFD
  figura_mapa_regimenes():  empuje contra presión exterior con los regímenes
  figura_superpuesta():     código contra SolidWorks para una variable
  figura_error():           diferencia absoluta o error porcentual contra x

Tema negro: los colores de este archivo son la paleta de toda la interfaz
(estilo.py los importa y .streamlit/config.toml repite los principales).
Los PNG de graficas.py se quedan con fondo blanco para el reporte.
Longitudes en mm.
"""

import numpy as np
import plotly.graph_objects as go
from plotly.colors import sequential

from geometria import contorno_exterior, muestrear
from graficas import NOMBRES_REGIMEN, _series

# ---------------------------------------------------------------------
# Paleta de la interfaz (tema negro)
# ---------------------------------------------------------------------

FONDO = "#09090B"        # fondo de la página
PANEL = "#111113"        # tarjetas, gráficas y controles
PANEL_2 = "#1A1A1E"      # encabezados de tabla, hover
BORDE = "#27272A"        # bordes finos
REJILLA = "#1E1E22"      # rejilla de las gráficas
EJES = "#3F3F46"         # ejes
TEXTO = "#F4F4F5"        # texto principal
TEXTO_2 = "#A1A1AA"      # texto secundario y líneas de referencia
TEXTO_3 = "#71717A"      # notas
ACENTO = "#FF6A1F"       # naranja de escape: modelo 1D y elementos activos
TEAL = "#2DD4BF"         # diferencia / error
COLOR_SW = "#E4E4E7"     # datos de SolidWorks (blanco, línea discontinua)
PARED = "#27272A"        # pared de la tobera

# Paleta categórica (orden fijo); la primera es el naranja del modelo.
SERIES = [ACENTO, "#FACC15", TEAL, "#A78BFA", "#F472B6", "#A3E635", "#60A5FA", "#A1A1AA"]

# Un color por régimen (tabla de resultados y mapa de regímenes)
COLOR_REGIMEN = {
    "subsonico": "#A1A1AA",
    "estrangulado_subsonico": "#D4D4D8",
    "choque_interno": "#F472B6",
    "choque_en_salida": "#E879F9",
    "sobreexpandida": "#FACC15",
    "adaptada": "#4ADE80",
    "subexpandida": "#A78BFA",
}

COLOR_CODIGO = ACENTO
FUENTE = dict(family="Inter, 'Segoe UI', Helvetica, Arial, sans-serif", size=13, color=TEXTO)
ETIQUETA_X = "x [mm]  (garganta en x = 0)"

# Barra de herramientas de las gráficas: sin logo y exportación PNG en alta
# resolución (escala 3) para usar las figuras en el reporte.
CONFIG = {
    "displaylogo": False,
    "modeBarButtonsToRemove": ["lasso2d", "select2d", "autoScale2d"],
    "toImageButtonOptions": {"format": "png", "scale": 3, "filename": "tobera_cd"},
}


# Mapa de color "Inferno" (negro -> naranja -> amarillo) para el campo de
# Mach. Streamlit cambia el color #000004 de la escala original por otro, así
# que el primer tono se sustituye por un negro equivalente.
_TONOS = ["#05050A"] + sequential.Inferno[1:]
INFERNO = [[i / (len(_TONOS) - 1), c] for i, c in enumerate(_TONOS)]


def rgba(color, alfa):
    """'#FF6A1F', 0.2 -> 'rgba(255,106,31,0.2)' (para rellenos transparentes)."""
    r, g, b = (int(color[i:i + 2], 16) for i in (1, 3, 5))
    return f"rgba({r},{g},{b},{alfa})"


def _estilo(fig, titulo, alto=420):
    fig.update_layout(
        title=dict(text=f"<b>{titulo}</b>", x=0.0, xanchor="left", y=0.97, yanchor="top",
                   font=dict(size=14, color=TEXTO)),
        font=FUENTE,
        template="plotly_dark",
        paper_bgcolor=PANEL,
        plot_bgcolor=PANEL,
        height=alto,
        margin=dict(l=70, r=24, t=64, b=56),
        hovermode="x unified",
        legend=dict(bgcolor="rgba(0,0,0,0)", borderwidth=0,
                    font=dict(color=TEXTO_2, size=12), title_font=dict(color=TEXTO_3, size=11)),
        hoverlabel=dict(bgcolor=PANEL_2, bordercolor=EJES, font=dict(color=TEXTO, size=12)),
    )
    eje = dict(showgrid=True, gridcolor=REJILLA, gridwidth=1, zeroline=False,
               showline=True, linecolor=EJES, linewidth=1, mirror=False,
               ticks="outside", ticklen=4, tickcolor=EJES,
               tickfont=dict(color=TEXTO_3, size=11), title_font=dict(color=TEXTO_2, size=12),
               showspikes=True, spikemode="across", spikesnap="cursor", spikecolor=EJES,
               spikethickness=1, spikedash="solid")
    fig.update_xaxes(**eje)
    fig.update_yaxes(**eje)
    return fig


def _leyenda_derecha(fig, titulo=None):
    """Leyenda vertical fuera del área de la gráfica, a la derecha (no tapa los ejes)."""
    fig.update_layout(legend=dict(title=titulo, orientation="v", yanchor="top", y=1,
                                  xanchor="left", x=1.02))
    fig.update_layout(margin=dict(r=290))


def _linea_garganta(fig):
    fig.add_vline(x=0, line=dict(color=TEXTO_3, width=1, dash="dashdot"),
                  annotation_text="garganta", annotation_position="top right",
                  annotation_font=dict(color=TEXTO_3, size=11))


def _lineas_criticas(fig, criticas, eje="y", log=False):
    """
    Marca p1, p2 y p3 (en kPa) como líneas de referencia horizontales o
    verticales. En un eje logarítmico Plotly ubica las líneas con log10(valor).
    """
    for nombre, clave in (("p₁", "p1"), ("p₂", "p2"), ("p₃", "p3")):
        valor = criticas[clave] / 1e3
        estilo = dict(line=dict(color=TEXTO_2, width=1, dash="dot"),
                      annotation_text=f"{nombre} = {valor:.1f} kPa",
                      annotation_font=dict(color=TEXTO_2, size=11))
        if eje == "y":
            fig.add_hline(y=valor, annotation_position="bottom left", **estilo)
        else:
            fig.add_vline(x=np.log10(valor) if log else valor, annotation_position="top",
                          **estilo)


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
            fill="toself", fillcolor=PARED, line=dict(width=1, color=EJES), hoverinfo="skip"))
        fig.add_trace(go.Scatter(
            x=x_mm, y=signo * ri_mm, mode="lines", line=dict(color=ACENTO, width=2.5),
            hovertemplate="x = %{x:.2f} mm<br>r = %{y:.3f} mm<extra></extra>"))
    # Núcleo del flujo con un tono tenue del acento
    fig.add_trace(go.Scatter(
        x=np.concatenate([x_mm, x_mm[::-1]]), y=np.concatenate([ri_mm, -ri_mm[::-1]]),
        fill="toself", fillcolor=rgba(ACENTO, 0.06), line=dict(width=0),
        hoverinfo="skip"))
    fig.add_hline(y=0, line=dict(color=TEXTO_3, width=1, dash="dashdot"))
    _linea_garganta(fig)

    for x, r, texto, pos in (
        (0.0, geo["r_garganta"], f"D* = {2e3*geo['r_garganta']:.2f} mm", "bottom center"),
        (geo["x_salida"] * 1e3, geo["r_salida"], f"Dₑ = {2e3*geo['r_salida']:.2f} mm",
         "middle right"),
        (geo["x_entrada"] * 1e3, geo["r_entrada"], f"D entrada = {2e3*geo['r_entrada']:.2f} mm",
         "bottom right"),
    ):
        fig.add_trace(go.Scatter(x=[x], y=[r * 1e3], mode="markers+text", text=[texto],
                                 textposition=pos, textfont=dict(color=TEXTO, size=12),
                                 marker=dict(color=TEXTO, size=7), hoverinfo="skip"))

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

def figura_distribucion(x, distribuciones, variable, criticas=None):
    """
    variable = "p" (presión estática en kPa) o "M" (Mach).
    Las presiones exteriores con el mismo flujo interior se agrupan en una
    curva (igual que en los PNG). Las líneas punteadas verticales marcan el
    choque. Si se pasan las presiones críticas, en la gráfica de presión se
    marcan p1, p2 y p3.
    """
    fig = go.Figure()
    for i, (d, etiqueta) in enumerate(_series(distribuciones)):
        color = SERIES[i % len(SERIES)]
        if variable == "p":
            y, formato = d["p"] / 1e3, "p = %{y:.2f} kPa"
        else:
            y, formato = d["M"], "M = %{y:.4f}"
        fig.add_trace(go.Scatter(x=x * 1e3, y=y, mode="lines",
                                 name=etiqueta.replace("\n", "<br>"),
                                 line=dict(color=color, width=2.5),
                                 hovertemplate=f"{formato}<extra></extra>"))
        if d["x_choque"] is not None:
            fig.add_vline(x=d["x_choque"] * 1e3, line=dict(color=color, width=1.5, dash="dot"))
    _linea_garganta(fig)

    if variable == "p":
        titulo, eje_y = "Presión estática a lo largo de la tobera", "Presión estática p [kPa]"
        if criticas is not None:
            _lineas_criticas(fig, criticas, eje="y")
    else:
        titulo, eje_y = "Número de Mach a lo largo de la tobera", "Número de Mach M [–]"
        fig.add_hline(y=1, line=dict(color=TEXTO_2, width=1, dash="dash"),
                      annotation_text="M = 1", annotation_position="bottom left",
                      annotation_font=dict(color=TEXTO_2, size=11))

    _estilo(fig, titulo, alto=440)
    _leyenda_derecha(fig, "Presión exterior p_b")
    fig.update_xaxes(title_text=ETIQUETA_X + "  ·  punteado: choque normal")
    fig.update_yaxes(title_text=eje_y)
    return fig


# ---------------------------------------------------------------------
# Campo de Mach (vista tipo CFD)
# ---------------------------------------------------------------------

def figura_campo(x, r, d, variable="M", p0=None):
    """
    Media tobera coloreada con M(x) o p(x)/p0 (mapa de color "Inferno"),
    parecido al resultado de Flow Simulation. Como el modelo es cuasi-1D el
    color solo cambia con x: es la misma información que las curvas, pero
    sobre la geometría real. La línea blanca discontinua marca el choque.
    """
    x_mm, r_mm = x * 1e3, r * 1e3
    if variable == "M":
        z, titulo, barra = d["M"], "Campo de Mach", "M"
    else:
        z, titulo, barra = d["p"] / p0, "Campo de presión", "p/p₀"
    y_mm = np.linspace(-1.05 * r_mm.max(), 1.05 * r_mm.max(), 160)
    # Solo se colorea dentro de la tobera (|y| <= r(x))
    campo = np.where(np.abs(y_mm)[:, None] <= r_mm[None, :], z[None, :], np.nan)

    fig = go.Figure(go.Heatmap(
        x=x_mm, y=y_mm, z=campo, colorscale=INFERNO, zmin=0, zmax=float(np.max(z)),
        colorbar=dict(title=dict(text=barra, font=dict(color=TEXTO_2)), thickness=12,
                      outlinewidth=0, tickfont=dict(color=TEXTO_3, size=11)),
        hovertemplate=f"x = %{{x:.2f}} mm<br>{barra} = %{{z:.3f}}<extra></extra>"))
    for signo in (1, -1):
        fig.add_trace(go.Scatter(x=x_mm, y=signo * r_mm, mode="lines", hoverinfo="skip",
                                 line=dict(color=TEXTO_2, width=1.5), showlegend=False))
    if d["x_choque"] is not None:
        xs = d["x_choque"] * 1e3
        rs = np.interp(xs, x_mm, r_mm)
        fig.add_trace(go.Scatter(x=[xs, xs], y=[-rs, rs], mode="lines", hoverinfo="skip",
                                 line=dict(color="white", width=2, dash="dash"),
                                 showlegend=False))
        fig.add_annotation(x=xs, y=rs, text=f"choque  x = {xs:.2f} mm", showarrow=False,
                           yshift=12, font=dict(color=TEXTO, size=11))
    _estilo(fig, f"{titulo}  ·  p_b = {d['pb']/1e3:.1f} kPa", alto=360)
    fig.update_layout(hovermode="closest", plot_bgcolor=PANEL)
    margen = 0.03 * (x_mm[-1] - x_mm[0])
    fig.update_xaxes(title_text=ETIQUETA_X, showgrid=False, showspikes=False,
                     range=[x_mm[0] - margen, x_mm[-1] + margen], constrain="domain")
    fig.update_yaxes(title_text="r [mm]", showgrid=False, showspikes=False,
                     scaleanchor="x", scaleratio=1, range=[y_mm[0], y_mm[-1]],
                     constrain="domain")
    return fig


# ---------------------------------------------------------------------
# Mapa de regímenes
# ---------------------------------------------------------------------

def figura_mapa_regimenes(curva, criticas, p0, pa, analisis):
    """
    Empuje F contra presión exterior pb (eje logarítmico). Cada régimen se
    sombrea con su color, se marcan p1, p2, p3 y la presión ambiente de
    diseño, y los puntos son las presiones analizadas en el caso.
    """
    pb = curva["pb"] / 1e3
    fig = go.Figure()

    # Bandas de régimen: (desde, hasta, régimen) en kPa. El eje x es
    # logarítmico, así que las bandas y líneas se ubican con log10.
    p1, p2, p3 = (criticas[k] / 1e3 for k in ("p1", "p2", "p3"))
    bandas = ((pb[0], p3, "subexpandida"), (p3, p2, "sobreexpandida"),
              (p2, p1, "choque_interno"), (p1, p0 / 1e3, "subsonico"))
    for desde, hasta, reg in bandas:
        fig.add_vrect(x0=np.log10(desde), x1=np.log10(hasta), fillcolor=COLOR_REGIMEN[reg],
                      opacity=0.14, line_width=0, layer="below",
                      annotation_text=NOMBRES_REGIMEN[reg], annotation_position="top",
                      annotation_font=dict(color=COLOR_REGIMEN[reg], size=11))
    _lineas_criticas(fig, criticas, eje="x", log=True)
    fig.add_vline(x=np.log10(pa / 1e3), line=dict(color=COLOR_REGIMEN["adaptada"], width=1.5),
                  annotation_text=f"diseño  pₐ = {pa/1e3:.1f} kPa",
                  annotation_position="bottom right",
                  annotation_font=dict(color=COLOR_REGIMEN["adaptada"], size=11))

    fig.add_trace(go.Scatter(
        x=pb, y=curva["F"], mode="lines", name="Empuje F", line=dict(color=TEXTO, width=2.5),
        customdata=np.column_stack([curva["pe"] / 1e3, curva["CF"],
                                    [NOMBRES_REGIMEN[r] for r in curva["regimen"]]]),
        hovertemplate=("p_b = %{x:.1f} kPa<br>F = %{y:.2f} N<br>p_e = %{customdata[0]:.1f} kPa"
                       "<br>C_F = %{customdata[1]:.3f}<br>%{customdata[2]}<extra></extra>")))
    fig.add_trace(go.Scatter(
        x=[a["pb_Pa"] / 1e3 for a in analisis], y=[a["F_N"] for a in analisis],
        mode="markers", name="Casos analizados",
        marker=dict(size=10, color=[COLOR_REGIMEN[a["regimen"]] for a in analisis],
                    line=dict(color=FONDO, width=2)),
        hovertemplate="p_b = %{x:.1f} kPa<br>F = %{y:.2f} N<extra>analizado</extra>"))

    _estilo(fig, "Mapa de regímenes: empuje contra presión exterior", alto=460)
    fig.update_layout(hovermode="closest", margin=dict(t=90),
                      legend=dict(orientation="h", yanchor="bottom", y=1.08, xanchor="right", x=1))
    fig.update_xaxes(type="log", range=[np.log10(pb[0]), np.log10(p0 / 1e3)], title_text="Presión exterior p_b [kPa]  (escala logarítmica)")
    fig.update_yaxes(title_text="Empuje F [N]")
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
                             line=dict(color=COLOR_SW, width=1.2, dash="dash"),
                             marker=dict(color=COLOR_SW, size=5, symbol="circle-open"),
                             hovertemplate="%{y:.4g}<extra>SolidWorks</extra>"))
    _linea_garganta(fig)
    _estilo(fig, f"{nombre}: código contra SolidWorks")
    fig.update_layout(margin=dict(t=85),
                      legend=dict(orientation="h", yanchor="bottom", y=1.04, xanchor="right", x=1))
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
                               fill="tozeroy", fillcolor=rgba(TEAL, 0.12),
                               hovertemplate=f"{formato}<extra></extra>"))
    fig.add_hline(y=0, line=dict(color=TEXTO_2, width=1))
    _linea_garganta(fig)
    _estilo(fig, titulo)
    fig.update_layout(showlegend=False)
    fig.update_xaxes(title_text=ETIQUETA_X)
    fig.update_yaxes(title_text=eje)
    return fig
