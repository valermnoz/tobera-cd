"""
graficas_gui.py — Gráficas interactivas (Plotly) para la interfaz gráfica.

  figura_geometria():       media sección de la tobera con su pared
  figura_distribucion():    p(x) o M(x) para cada presión exterior
  figura_campo():           tobera coloreada con M(x) o p(x), tipo CFD
  figura_mapa_regimenes():  empuje contra presión exterior con los regímenes
  figura_animacion_choque(): M(x) animado al bajar la presión exterior
  figura_cf():              C_F contra pb/p0 (análisis dimensional)
  figura_comparar_perfiles(), figura_comparar_mach(): dos casos superpuestos
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

from tobera import distribucion, estado_salida

from geometria import contorno_exterior, muestrear
from graficas import NOMBRES_REGIMEN, _series

# ---------------------------------------------------------------------
# Paleta de la interfaz: grafito neutro con azul rey como único acento
# ---------------------------------------------------------------------

FONDO = "#0C0E13"        # fondo de la página
PANEL = "#13161D"        # tarjetas, gráficas y controles
PANEL_2 = "#1B1F28"      # encabezados de tabla, hover
BORDE = "#272C37"        # bordes finos
REJILLA = "#1D212A"      # rejilla de las gráficas
EJES = "#3B4251"         # ejes
TEXTO = "#E6E8EC"        # texto principal
TEXTO_2 = "#A2A8B4"      # texto secundario y líneas de referencia
TEXTO_3 = "#6F7684"      # notas
ACENTO = "#1F5BD6"       # azul profundo (sin tono morado): modelo 1D y elementos activos
ACENTO_CLARO = "#6FA3F2" # el mismo azul aclarado, para texto pequeño sobre fondo oscuro
TEAL = "#2BB3A3"         # diferencia / error
COLOR_SW = "#F2A93B"     # datos de SolidWorks (ámbar, contrasta con el azul)
COLOR_ERROR = "#EF6461"  # zona de error entre las dos curvas
PARED = "#272C37"        # pared de la tobera

# Paleta categórica (orden fijo); la primera es el azul del modelo y el
# ámbar se reserva para SolidWorks.
SERIES = [ACENTO, "#2BB3A3", "#E8C547", "#5FB3F0", "#A3E635", "#94A3B8", "#E6E8EC", "#F08A5D"]

# Un color por régimen (tabla de resultados y mapa de regímenes)
COLOR_REGIMEN = {
    "subsonico": "#A2A8B4",
    "estrangulado_subsonico": "#D4D7DD",
    "choque_interno": "#F08A5D",
    "choque_en_salida": "#E0604E",
    "sobreexpandida": "#F2C94C",
    "adaptada": "#4CC38A",
    "subexpandida": "#4FA3E8",
}

COLOR_CODIGO = ACENTO
FUENTE = dict(family="'IBM Plex Sans', 'Segoe UI', Helvetica, Arial, sans-serif", size=13,
              color=TEXTO)
ETIQUETA_X = "x [mm]  (garganta en x = 0)"

# Barra de herramientas de las gráficas: sin logo y exportación PNG en alta
# resolución (escala 3) para usar las figuras en el reporte.
CONFIG = {
    "displaylogo": False,
    "modeBarButtonsToRemove": ["lasso2d", "select2d", "autoScale2d"],
    "toImageButtonOptions": {"format": "png", "scale": 3, "filename": "tobera_cd"},
}


# Mapa de color tipo arcoíris, parecido al que usa SolidWorks Flow Simulation en
# sus gráficas de corte: empieza en azul marino (no en morado como "Turbo") y
# sigue con los tonos de Turbo hacia el rojo.
_TONOS_CFD = ["#0A2463", "#1F5BD6"] + sequential.Turbo[3:]
MAPA_CFD = [[i / (len(_TONOS_CFD) - 1), c] for i, c in enumerate(_TONOS_CFD)]


def rgba(color, alfa):
    """'#1F5BD6', 0.2 -> 'rgba(31,91,214,0.2)' (para rellenos transparentes)."""
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
    Media tobera coloreada con M(x) o p(x)/p0 (mapa de color arcoíris tipo CFD),
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
        x=x_mm, y=y_mm, z=campo, colorscale=MAPA_CFD, zmin=0, zmax=float(np.max(z)),
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


# ---------------------------------------------------------------------
# Animación del choque
# ---------------------------------------------------------------------

def figura_animacion_choque(x, r, A, p0, T0, g, criticas, n=36):
    """
    M(x) para presiones exteriores que bajan de p1 a p3/2: el choque nace en la
    garganta, recorre la divergente, sale por el plano de salida y el flujo
    queda supersónico. Botón ▶ y deslizador con p_b en kPa.
    """
    x_mm, r_mm = x * 1e3, r * 1e3
    # Dos tercios de los cuadros con el choque dentro (entre p1 y p2), el resto
    # con la tobera ya supersónica (de p2 a p3/2)
    n_choque = 2 * n // 3
    pbs = np.concatenate([np.linspace(0.999 * criticas["p1"], criticas["p2"], n_choque),
                          np.geomspace(0.97 * criticas["p2"], 0.5 * criticas["p3"],
                                       n - n_choque)])
    M_max = 1.15 * np.max(distribucion(x, A, pbs[-1], p0, T0, g)["M"])

    def trazas(pb):
        d = distribucion(x, A, pb, p0, T0, g)
        reg = estado_salida(pb, p0, T0, 1.0, A[-1] / A.min(), g)["regimen"]
        xs = [None, None] if d["x_choque"] is None else [d["x_choque"] * 1e3] * 2
        return [
            go.Scatter(x=x_mm, y=d["M"], mode="lines", line=dict(color=ACENTO, width=3),
                       fill="tozeroy", fillcolor=rgba(ACENTO, 0.10), name="M(x)",
                       hovertemplate="x = %{x:.2f} mm<br>M = %{y:.3f}<extra></extra>"),
            go.Scatter(x=xs, y=[0, M_max], mode="lines", name="choque",
                       line=dict(color=TEXTO, width=1.5, dash="dash"), hoverinfo="skip"),
        ], f"p_b = {pb/1e3:.1f} kPa · {NOMBRES_REGIMEN[reg]}"

    datos, titulo = trazas(pbs[0])
    # Silueta de la tobera al fondo, escalada al eje de Mach
    escala = 0.9 * M_max / r_mm.max()
    silueta = go.Scatter(x=np.concatenate([x_mm, x_mm[::-1]]),
                         y=np.concatenate([r_mm * escala, np.zeros_like(r_mm)]),
                         fill="toself", fillcolor=rgba(TEXTO, 0.03), mode="lines",
                         line=dict(color=EJES, width=1), hoverinfo="skip", name="tobera")
    fig = go.Figure(data=[silueta] + datos)
    marcos = []
    for pb in pbs:
        tr, tit = trazas(pb)
        marcos.append(go.Frame(data=tr, traces=[1, 2], name=f"{pb/1e3:.1f}",
                               layout=dict(title_text=f"<b>Animación del choque</b>  ·  {tit}")))
    fig.frames = marcos
    _estilo(fig, "Animación del choque", alto=460)
    fig.update_layout(title_text=f"<b>Animación del choque</b>  ·  {titulo}")
    fig.add_hline(y=1, line=dict(color=TEXTO_3, width=1, dash="dot"),
                  annotation_text="M = 1", annotation_position="bottom left",
                  annotation_font=dict(color=TEXTO_3, size=11))
    _linea_garganta(fig)
    boton = dict(type="buttons", direction="left", x=0, y=-0.19, xanchor="left", yanchor="top",
                 showactive=False, bgcolor=PANEL_2, bordercolor=BORDE, font=dict(color=TEXTO),
                 buttons=[
                     dict(label="▶  Reproducir", method="animate",
                          args=[None, dict(frame=dict(duration=140, redraw=True),
                                           transition=dict(duration=0), fromcurrent=True)]),
                     dict(label="❚❚  Pausa", method="animate",
                          args=[[None], dict(frame=dict(duration=0), mode="immediate")]),
                 ])
    deslizador = dict(active=0, x=0.26, y=-0.13, len=0.74, xanchor="left", yanchor="top",
                      bgcolor=PANEL_2, bordercolor=BORDE, activebgcolor=ACENTO,
                      tickcolor=EJES, font=dict(color=TEXTO_3, size=10),
                      currentvalue=dict(prefix="p_b = ", suffix=" kPa",
                                        font=dict(color=TEXTO, size=12)),
                      steps=[dict(label=m.name, method="animate",
                                  args=[[m.name], dict(frame=dict(duration=0, redraw=True),
                                                       mode="immediate")]) for m in marcos])
    fig.update_layout(updatemenus=[boton], sliders=[deslizador], showlegend=False,
                      hovermode="closest", margin=dict(b=150))
    fig.update_xaxes(title_text=ETIQUETA_X, showspikes=False)
    fig.update_yaxes(title_text="Número de Mach M [–]", range=[0, M_max], showspikes=False)
    return fig


# ---------------------------------------------------------------------
# Análisis dimensional
# ---------------------------------------------------------------------

def figura_cf(curvas, titulo, etiqueta, resaltar=None, pb_p0_diseno=None,
              sufijo="  (este caso)"):
    """
    C_F contra pb/p0 (eje logarítmico). 'curvas' = {parámetro: (pb/p0, C_F)};
    'etiqueta' da el nombre de cada curva y 'resaltar' es el parámetro del caso.
    """
    fig = go.Figure()
    for i, (clave, (eje, cf)) in enumerate(curvas.items()):
        propia = resaltar is not None and np.isclose(clave, resaltar)
        color = ACENTO if propia else SERIES[1:][i % (len(SERIES) - 1)]
        fig.add_trace(go.Scatter(
            x=eje, y=cf, mode="lines", name=etiqueta(clave) + (sufijo if propia else ""),
            line=dict(color=color, width=3.5 if propia else 1.8),
            hovertemplate="p_b/p₀ = %{x:.4f}<br>C_F = %{y:.4f}<extra>" + etiqueta(clave) +
                          "</extra>"))
    if pb_p0_diseno is not None:
        fig.add_vline(x=np.log10(pb_p0_diseno), line=dict(color=COLOR_REGIMEN["adaptada"],
                                                          width=1.2, dash="dot"),
                      annotation_text=f"diseño  pₐ/p₀ = {pb_p0_diseno:.4f}",
                      annotation_position="top right",
                      annotation_font=dict(color=COLOR_REGIMEN["adaptada"], size=11))
    _estilo(fig, titulo, alto=440)
    _leyenda_derecha(fig)
    fig.update_layout(margin=dict(r=220), hovermode="closest")
    # Rango explícito: en un eje log la línea vertical se ubica con log10 y sin
    # rango fijo Plotly lo extiende de más
    x_min = min(float(eje[0]) for eje, _ in curvas.values())
    fig.update_xaxes(type="log", range=[np.log10(x_min), 0],
                     title_text="Presión exterior adimensional p_b/p₀  (log)")
    fig.update_yaxes(title_text="Coeficiente de empuje C_F = F/(p₀A*)", rangemode="tozero")
    return fig


# ---------------------------------------------------------------------
# Comparación de casos
# ---------------------------------------------------------------------

COLORES_CASO = (ACENTO, "#E4E4E7")


def figura_comparar_perfiles(casos):
    """Perfil r(x) de dos o más toberas en la misma escala. casos = [(nombre, x, r)]."""
    fig = go.Figure()
    for (nombre, x, r), color in zip(casos, COLORES_CASO * 2):
        for signo, leyenda in ((1, True), (-1, False)):
            fig.add_trace(go.Scatter(x=x * 1e3, y=signo * r * 1e3, mode="lines", name=nombre,
                                     legendgroup=nombre, showlegend=leyenda,
                                     line=dict(color=color, width=2.5),
                                     hovertemplate="x = %{x:.2f} mm<br>r = %{y:.2f} mm"
                                                   f"<extra>{nombre}</extra>"))
    fig.add_hline(y=0, line=dict(color=TEXTO_3, width=1, dash="dashdot"))
    _linea_garganta(fig)
    _estilo(fig, "Perfiles a la misma escala", alto=400)
    fig.update_layout(hovermode="closest",
                      legend=dict(orientation="h", yanchor="bottom", y=1.04, xanchor="right", x=1))
    fig.update_xaxes(title_text=ETIQUETA_X)
    fig.update_yaxes(title_text="r [mm]", scaleanchor="x", scaleratio=1)
    return fig


def figura_comparar_mach(casos):
    """M contra x/L (posición adimensional) para comparar toberas de distinto tamaño."""
    fig = go.Figure()
    for (nombre, x, r, M), color in zip(casos, COLORES_CASO * 2):
        x_rel = (x - x.min()) / (x.max() - x.min())
        fig.add_trace(go.Scatter(x=x_rel, y=M, mode="lines", name=nombre,
                                 line=dict(color=color, width=2.5),
                                 hovertemplate="x/L = %{x:.3f}<br>M = %{y:.3f}"
                                               f"<extra>{nombre}</extra>"))
    fig.add_hline(y=1, line=dict(color=TEXTO_3, width=1, dash="dot"))
    _estilo(fig, "Número de Mach en la presión de diseño", alto=400)
    fig.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.04, xanchor="right", x=1))
    fig.update_xaxes(title_text="Posición adimensional x/L (0 = entrada, 1 = salida)")
    fig.update_yaxes(title_text="Número de Mach M [–]")
    return fig


# ---------------------------------------------------------------------
# Validación visual (código contra SolidWorks)
# ---------------------------------------------------------------------

def figura_empalme(comp, nombre, unidad, n_cuadros=40):
    """
    Las dos curvas empalmadas con la zona entre ellas sombreada (ese hueco es
    el error). Botón ▶: un cursor recorre la tobera y va marcando los dos
    valores y el error en cada punto.
    """
    x, cod, sw, err = comp["x"], comp["codigo"], comp["solidworks"], comp["error_pct"]
    fig = go.Figure()
    # Relleno entre curvas: primero SolidWorks, luego el código con fill="tonexty"
    fig.add_trace(go.Scatter(x=x, y=sw, mode="lines", line=dict(color=COLOR_SW, width=2.2,
                                                                 dash="dash"),
                             name="SolidWorks", hovertemplate="%{y:.4g}<extra>SolidWorks</extra>"))
    fig.add_trace(go.Scatter(x=x, y=cod, mode="lines", line=dict(color=ACENTO, width=2.8),
                             fill="tonexty", fillcolor=rgba(COLOR_ERROR, 0.22), name="Código 1D",
                             hovertemplate="%{y:.4g}<extra>Código 1D</extra>"))
    y_min, y_max = float(min(cod.min(), sw.min())), float(max(cod.max(), sw.max()))
    margen = 0.08 * (y_max - y_min or 1.0)

    def cursor(i):
        texto = (f"x = {x[i]:.2f} mm<br>Código: {cod[i]:.4g}<br>SolidWorks: {sw[i]:.4g}"
                 f"<br><b>Error: {err[i]:+.2f} %</b>")
        return [
            go.Scatter(x=[x[i], x[i]], y=[y_min - margen, y_max + margen], mode="lines",
                       line=dict(color=TEXTO_2, width=1), hoverinfo="skip", showlegend=False),
            go.Scatter(x=[x[i], x[i]], y=[cod[i], sw[i]], mode="markers+lines",
                       marker=dict(size=9, color=[ACENTO, COLOR_SW], line=dict(color=FONDO, width=2)),
                       line=dict(color=COLOR_ERROR, width=3), hoverinfo="skip",
                       showlegend=False),
        ], texto

    indices = np.linspace(0, len(x) - 1, n_cuadros).astype(int)
    trazas, texto = cursor(indices[0])
    for t in trazas:
        fig.add_trace(t)
    nota = dict(xref="paper", yref="paper", x=0.01, y=0.97, xanchor="left", yanchor="top",
                showarrow=False, align="left", bgcolor=PANEL_2, bordercolor=BORDE, borderpad=8,
                font=dict(color=TEXTO, size=12, family="'IBM Plex Mono', monospace"))
    fig.frames = [go.Frame(data=cursor(i)[0], traces=[2, 3], name=str(k),
                           layout=dict(annotations=[dict(nota, text=cursor(i)[1])]))
                  for k, i in enumerate(indices)]
    fig.add_annotation(**nota, text=texto)
    _estilo(fig, f"{nombre}: empalme código – SolidWorks", alto=460)
    boton = dict(type="buttons", direction="left", x=0, y=-0.2, xanchor="left", yanchor="top",
                 showactive=False, bgcolor=PANEL_2, bordercolor=BORDE, font=dict(color=TEXTO),
                 buttons=[dict(label="▶  Recorrer la tobera", method="animate",
                               args=[None, dict(frame=dict(duration=120, redraw=True),
                                                transition=dict(duration=0), fromcurrent=True)]),
                          dict(label="❚❚", method="animate",
                               args=[[None], dict(frame=dict(duration=0), mode="immediate")])])
    deslizador = dict(active=0, x=0.3, y=-0.14, len=0.7, xanchor="left", yanchor="top",
                      bgcolor=PANEL_2, bordercolor=BORDE, activebgcolor=ACENTO, tickcolor=EJES,
                      font=dict(color=TEXTO_3, size=9), currentvalue=dict(visible=False),
                      steps=[dict(label=f"{x[i]:.0f}", method="animate",
                                  args=[[str(k)], dict(frame=dict(duration=0, redraw=True),
                                                       mode="immediate")])
                             for k, i in enumerate(indices)])
    fig.update_layout(updatemenus=[boton], sliders=[deslizador], hovermode="x unified",
                      margin=dict(b=140, t=80),
                      legend=dict(orientation="h", yanchor="bottom", y=1.03, xanchor="right", x=1))
    _linea_garganta(fig)
    fig.update_xaxes(title_text=ETIQUETA_X)
    fig.update_yaxes(title_text=f"{nombre} [{unidad}]", range=[y_min - margen, y_max + margen])
    return fig


def figura_mapa_error(x_modelo_mm, r_modelo_mm, comp, nombre):
    """
    La tobera pintada con |error| en cada sección: blanco donde coinciden,
    rojo donde más se separan. Muestra de un vistazo DÓNDE está el error.
    """
    x = comp["x"]
    r = np.interp(x, x_modelo_mm, r_modelo_mm)
    err = np.abs(comp["error_pct"])
    tope = max(5.0, float(np.nanpercentile(err, 98)))
    y = np.linspace(-1.05 * r.max(), 1.05 * r.max(), 140)
    campo = np.where(np.abs(y)[:, None] <= r[None, :], err[None, :], np.nan)
    escala = [[0, "#0A2463"], [0.15, ACENTO], [0.45, "#F2C94C"], [1, COLOR_ERROR]]
    fig = go.Figure(go.Heatmap(
        x=x, y=y, z=campo, colorscale=escala, zmin=0, zmax=tope,
        colorbar=dict(title=dict(text="|error| %", font=dict(color=TEXTO_2)), thickness=12,
                      outlinewidth=0, tickfont=dict(color=TEXTO_3, size=11)),
        hovertemplate="x = %{x:.2f} mm<br>|error| = %{z:.2f} %<extra></extra>"))
    for signo in (1, -1):
        fig.add_trace(go.Scatter(x=x_modelo_mm, y=signo * r_modelo_mm, mode="lines",
                                 hoverinfo="skip", showlegend=False,
                                 line=dict(color=TEXTO_2, width=1.2)))
    i = int(np.nanargmax(err))
    fig.add_annotation(x=x[i], y=r[i], text=f"máx. {err[i]:.1f} %", showarrow=True,
                       arrowcolor=TEXTO_2, ay=-28, font=dict(color=TEXTO, size=11))
    _estilo(fig, f"{nombre}: dónde está el error", alto=340)
    fig.update_layout(hovermode="closest")
    fig.update_xaxes(title_text=ETIQUETA_X, showgrid=False, showspikes=False,
                     range=[x_modelo_mm[0], x_modelo_mm[-1]], constrain="domain")
    fig.update_yaxes(title_text="r [mm]", showgrid=False, showspikes=False, scaleanchor="x",
                     scaleratio=1, range=[y[0], y[-1]], constrain="domain")
    return fig


def figura_paridad(comp, nombre, unidad, banda_pct=5.0):
    """
    Gráfica de paridad: SolidWorks en x, código en y. Si coincidieran, todos
    los puntos caerían sobre la diagonal; la franja es ±banda_pct %.
    """
    sw, cod, x = comp["solidworks"], comp["codigo"], comp["x"]
    lim = [float(min(sw.min(), cod.min())), float(max(sw.max(), cod.max()))]
    linea = np.linspace(lim[0], lim[1], 50)
    f = banda_pct / 100
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=np.concatenate([linea, linea[::-1]]),
                             y=np.concatenate([linea * (1 + f), (linea * (1 - f))[::-1]]),
                             fill="toself", fillcolor=rgba(ACENTO, 0.10), line=dict(width=0),
                             hoverinfo="skip", name=f"±{banda_pct:g} %"))
    fig.add_trace(go.Scatter(x=linea, y=linea, mode="lines", name="coincidencia perfecta",
                             line=dict(color=TEXTO_2, width=1, dash="dash"), hoverinfo="skip"))
    fig.add_trace(go.Scatter(
        x=sw, y=cod, mode="markers", name="secciones",
        marker=dict(size=6, color=x, colorscale=MAPA_CFD, showscale=True,
                    colorbar=dict(title=dict(text="x [mm]", font=dict(color=TEXTO_2)),
                                  thickness=10, outlinewidth=0,
                                  tickfont=dict(color=TEXTO_3, size=10))),
        hovertemplate="SW = %{x:.4g}<br>código = %{y:.4g}<extra></extra>"))
    dentro = float(np.mean(np.abs(cod - sw) <= f * np.abs(sw)) * 100)
    _estilo(fig, f"{nombre}: paridad  ·  {dentro:.0f} % de las secciones dentro de "
                 f"±{banda_pct:g} %", alto=420)
    fig.update_layout(hovermode="closest", showlegend=False)
    # Mismo rango en los dos ejes: la diagonal queda a 45°
    holgura = 0.05 * (lim[1] - lim[0] or 1.0)
    rango = [lim[0] - holgura, lim[1] + holgura]
    fig.update_xaxes(title_text=f"SolidWorks [{unidad}]", showspikes=False, range=rango,
                     constrain="domain")
    fig.update_yaxes(title_text=f"Código 1D [{unidad}]", showspikes=False, range=rango,
                     scaleanchor="x", scaleratio=1, constrain="domain")
    return fig


def figura_globales(filas):
    """
    Barras horizontales con el error % de cada magnitud global (ṁ, Me, pe, F).
    Franjas: ±2 % excelente, ±5 % bueno. filas = [(nombre, error_pct)].
    """
    nombres = [n for n, _ in filas]
    errores = [e for _, e in filas]
    colores = [COLOR_REGIMEN["adaptada"] if abs(e) <= 2 else "#F2C94C" if abs(e) <= 5
               else COLOR_ERROR for e in errores]
    fig = go.Figure(go.Bar(x=errores, y=nombres, orientation="h", marker_color=colores,
                           text=[f"{e:+.2f} %" for e in errores], textposition="outside",
                           textfont=dict(color=TEXTO, family="'IBM Plex Mono', monospace"),
                           hovertemplate="%{y}: %{x:+.2f} %<extra></extra>"))
    tope = max(8.0, 1.3 * max(abs(e) for e in errores))
    for limite, alfa in ((5, 0.06), (2, 0.08)):
        fig.add_vrect(x0=-limite, x1=limite, fillcolor=COLOR_REGIMEN["adaptada"], opacity=alfa,
                      line_width=0, layer="below")
    fig.add_vline(x=0, line=dict(color=TEXTO_2, width=1))
    _estilo(fig, "Magnitudes globales: error del código respecto a SolidWorks",
            alto=120 + 55 * len(filas))
    fig.update_layout(hovermode="closest", showlegend=False, bargap=0.45)
    fig.update_xaxes(title_text="Error relativo [%]   (franjas: ±2 % y ±5 %)",
                     range=[-tope, tope], showspikes=False, zeroline=False)
    fig.update_yaxes(showspikes=False, autorange="reversed")
    return fig
