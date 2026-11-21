"""
estilo.py — Identidad visual de la interfaz (CSS sobre el tema de .streamlit/config.toml).

Estilo técnico tipo CAD/CAE en negro: paneles grafito con bordes finos de
1 px, naranja de escape como único acento y fuente monoespaciada en los
valores numéricos (KPIs y tablas de datos). También trae los estilos de la
pantalla de inicio (clases .hero, .cifras, .tarjetas, .pasos). Los colores salen de
graficas_gui.py para que la interfaz y las gráficas usen la misma paleta.
"""

from string import Template

import streamlit as st

from graficas_gui import (ACENTO, BORDE, COLOR_REGIMEN, EJES, FONDO, PANEL, PANEL_2, REJILLA,
                          TEXTO, TEXTO_2, TEXTO_3, rgba)

MONO = '"JetBrains Mono", "SF Mono", Menlo, Consolas, monospace'

CSS = Template("""
.stApp { background: $fondo; }
[data-testid="stHeader"] { background: transparent; }
.block-container { padding-top: 2.2rem; padding-bottom: 3rem; max-width: 1400px; }

h1, h2, h3, h4 { color: $texto; font-weight: 600; letter-spacing: -0.01em; }
h3 { font-size: 1.15rem; }
hr { border-color: $borde !important; }
[data-testid="stCaptionContainer"] { color: $texto2; }
a { color: $acento; }

/* Encabezado compacto */
.encabezado {
  display: flex; align-items: center; justify-content: space-between; gap: 1rem;
  flex-wrap: wrap; padding: 0.9rem 1.2rem; margin-bottom: 1rem;
  background: linear-gradient(110deg, $acento10, transparent 55%), $panel;
  border: 1px solid $borde; border-radius: 8px;
}
.encabezado .marca { display: flex; align-items: center; gap: 0.9rem; }
.encabezado .logo {
  width: 42px; height: 42px; border-radius: 8px; flex: none;
  display: grid; place-items: center;
  background: $acento10; border: 1px solid $acento35;
}
.encabezado .titulo { font-size: 1.35rem; font-weight: 700; color: $texto; line-height: 1.15; }
.encabezado .titulo span { color: $acento; }
.encabezado .subtitulo { font-size: 0.85rem; color: $texto2; }
.encabezado .chips { display: flex; gap: 0.4rem; flex-wrap: wrap; }
.chip {
  font-size: 0.75rem; color: $texto2; padding: 0.2rem 0.6rem; border-radius: 999px;
  border: 1px solid $borde; background: $fondo; white-space: nowrap;
}
.chip b { color: $texto; font-weight: 600; font-family: $mono; }

/* Pantalla de inicio */
.hero {
  position: relative; overflow: hidden; border: 1px solid $borde; border-radius: 14px;
  padding: 4.2rem 3rem 3.6rem 3rem; margin-bottom: 1.2rem; min-height: 360px;
  background:
    linear-gradient(90deg, $fondo 0%, $fondo 38%, rgba(9,9,11,0.55) 70%, rgba(9,9,11,0.2) 100%),
    var(--foto) right center / cover no-repeat, $fondo;
}
.hero::after {
  content: ""; position: absolute; inset: 0; pointer-events: none;
  background: radial-gradient(600px 260px at 12% 110%, $acento35, transparent 70%);
}
.hero > * { position: relative; z-index: 1; max-width: 640px; }
.hero .antetitulo {
  font-size: 0.75rem; letter-spacing: 0.18em; text-transform: uppercase; color: $acento;
  font-weight: 600; margin-bottom: 0.9rem;
}
.hero .gran-titulo {
  font-size: 4.2rem; font-weight: 800; letter-spacing: -0.04em; line-height: 0.95;
  color: $texto; margin-bottom: 1rem;
}
.hero .gran-titulo span { color: $acento; }
.hero .lema { font-size: 1.35rem; color: $texto; font-weight: 500; margin-bottom: 0.7rem; }
.hero .texto { font-size: 0.98rem; color: $texto2; line-height: 1.6; }
.hero .creditos-foto {
  position: absolute; right: 1rem; bottom: 0.7rem; font-size: 0.68rem; color: $texto3;
  max-width: none;
}

.seccion-inicio {
  font-size: 0.72rem; letter-spacing: 0.16em; text-transform: uppercase; color: $texto3;
  font-weight: 600; margin: 2.4rem 0 0.9rem 0;
}
.cifras { display: grid; grid-template-columns: repeat(4, 1fr); gap: 0.8rem; }
.cifra { border: 1px solid $borde; border-radius: 10px; padding: 1rem 1.1rem; background: $panel; }
.cifra .valor { font-family: $mono; font-size: 1.7rem; font-weight: 600; color: $texto; }
.cifra .valor span { color: $acento; }
.cifra .etiqueta { font-size: 0.82rem; color: $texto2; margin-top: 0.2rem; }

.tarjetas { display: grid; grid-template-columns: repeat(3, 1fr); gap: 0.8rem; }
.tarjeta {
  border: 1px solid $borde; border-radius: 10px; padding: 1.2rem 1.2rem 1.1rem 1.2rem;
  background: $panel; transition: border-color 0.15s, transform 0.15s;
}
.tarjeta:hover { border-color: $acento35; transform: translateY(-2px); }
.tarjeta .num { font-family: $mono; font-size: 0.75rem; color: $acento; margin-bottom: 0.6rem; }
.tarjeta .nombre { font-size: 1.02rem; font-weight: 600; color: $texto; margin-bottom: 0.35rem; }
.tarjeta .desc { font-size: 0.86rem; color: $texto2; line-height: 1.5; }

.pasos { display: grid; grid-template-columns: repeat(3, 1fr); gap: 0.8rem; }
.paso { border-left: 2px solid $acento; padding: 0.3rem 0 0.3rem 1rem; }
.paso .nombre { font-weight: 600; color: $texto; }
.paso .desc { font-size: 0.86rem; color: $texto2; }

.pie-inicio {
  margin-top: 2.6rem; padding-top: 1.1rem; border-top: 1px solid $borde;
  display: flex; justify-content: space-between; flex-wrap: wrap; gap: 0.6rem;
  font-size: 0.8rem; color: $texto3;
}
[data-testid="stLatex"] { color: $texto; }
@media (max-width: 900px) {
  .cifras, .tarjetas, .pasos { grid-template-columns: 1fr; }
  .hero { padding: 2.4rem 1.4rem; }
  .hero .gran-titulo { font-size: 2.8rem; }
}

/* Barra lateral */
[data-testid="stSidebar"] { border-right: 1px solid $borde; }
[data-testid="stSidebar"] h3 {
  font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.08em; color: $texto3;
  margin-top: 0.6rem;
}
[data-testid="stSidebar"] li, [data-testid="stSidebar"] p { font-size: 0.86rem; }

/* Tarjetas de métricas (KPIs) */
[data-testid="stMetric"] {
  background: $panel; border: 1px solid $borde; border-radius: 8px;
  padding: 0.75rem 1rem; border-top: 2px solid $acento;
}
[data-testid="stMetricLabel"], [data-testid="stMetricLabel"] p {
  color: $texto2; font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.06em;
}
[data-testid="stMetricValue"], [data-testid="stMetricValue"] * {
  font-family: $mono !important; font-weight: 600; color: $texto;
}
[data-testid="stMetricValue"] { font-size: 1.4rem; }

/* Campos de entrada */
div[data-baseweb="input"], div[data-baseweb="select"] > div, div[data-baseweb="textarea"] {
  border-radius: 6px !important; background-color: $fondo !important;
}
[data-testid="stNumberInput"] input { font-family: $mono; }
div[data-baseweb="input"]:focus-within, div[data-baseweb="select"] > div:focus-within {
  border-color: $acento !important; box-shadow: 0 0 0 1px $acento;
}
[data-testid="stWidgetLabel"] p { color: $texto2; font-size: 0.82rem; font-weight: 500; }

/* Bloques del formulario */
.grupo {
  font-size: 0.72rem; font-weight: 600; color: $acento; text-transform: uppercase;
  letter-spacing: 0.08em; margin: 0.2rem 0 0.4rem 0; padding-bottom: 0.3rem;
  border-bottom: 1px solid $borde;
}

/* Pestañas */
[data-baseweb="tab-list"] { gap: 0.25rem; border-bottom: 1px solid $borde; }
button[data-baseweb="tab"] {
  background: transparent; border: none; border-radius: 6px 6px 0 0;
  padding: 0.55rem 1.1rem; height: auto;
}
button[data-baseweb="tab"]:hover { background: $panel; }
button[data-baseweb="tab"] p { color: $texto2; font-weight: 500; font-size: 0.92rem; }
button[data-baseweb="tab"][aria-selected="true"] { background: $panel; }
button[data-baseweb="tab"][aria-selected="true"] p { color: $acento; font-weight: 600; }
[data-baseweb="tab-highlight"] { background-color: $acento; height: 2px; }
[data-baseweb="tab-border"] { background-color: transparent; }

/* Botones */
[data-testid="stBaseButton-secondary"] { border-radius: 6px; font-weight: 500; background: $panel; }
[data-testid="stBaseButton-secondary"]:hover { border-color: $acento; color: $acento; }
[data-testid="stBaseButton-primary"] {
  border-radius: 6px; font-weight: 600; background: $acento; border-color: $acento; color: $fondo;
}
[data-testid="stBaseButton-primary"]:hover { color: $fondo; filter: brightness(1.1); }
[data-testid="stBaseButton-primary"] p { color: $fondo; }

/* Desplegables, cargadores de archivos y avisos */
[data-testid="stExpander"] details {
  border: 1px solid $borde; border-radius: 8px; background: $panel;
}
[data-testid="stFileUploaderDropzone"] {
  border: 1px dashed $ejes; border-radius: 8px; background: $panel;
}
[data-testid="stAlert"] { border-radius: 8px; }

/* Tablas de datos */
.tabla-datos { overflow-x: auto; margin-bottom: 1rem; }
.tabla-datos table {
  width: 100%; border-collapse: separate; border-spacing: 0;
  border: 1px solid $borde; border-radius: 8px; overflow: hidden; background: $panel;
}
.tabla-datos th {
  background: $panel2; color: $texto2; font-size: 0.72rem; font-weight: 600;
  text-transform: uppercase; letter-spacing: 0.05em;
  padding: 0.55rem 0.8rem; border-bottom: 1px solid $borde; white-space: nowrap;
}
.tabla-datos td {
  font-size: 0.88rem; color: $texto; padding: 0.5rem 0.8rem;
  border-bottom: 1px solid $rejilla;
}
.tabla-datos .txt { text-align: left; }
.tabla-datos .num { text-align: right; }
.tabla-datos td.num { font-family: $mono; font-size: 0.84rem; }
.tabla-datos tbody tr:last-child td { border-bottom: none; }
.tabla-datos tbody tr:hover td { background: $panel2; }

/* Insignias de régimen */
.insignia {
  display: inline-flex; align-items: center; gap: 0.4rem; font-size: 0.78rem;
  padding: 0.12rem 0.55rem; border-radius: 999px; white-space: nowrap;
  border: 1px solid currentColor; background: rgba(255,255,255,0.03);
}
.insignia::before {
  content: ""; width: 6px; height: 6px; border-radius: 50%; background: currentColor;
}
$insignias

/* Gráficas y fotografías */
[data-testid="stPlotlyChart"] {
  border: 1px solid $borde; border-radius: 8px; padding: 0.3rem; background: $panel;
  overflow: hidden;
}
[data-testid="stImage"] img { border-radius: 6px; border: 1px solid $borde; }
[data-testid="stImageCaption"], [data-testid="stImage"] figcaption {
  color: $texto3; font-size: 0.72rem; line-height: 1.3;
}
""").safe_substitute(
    fondo=FONDO, panel=PANEL, panel2=PANEL_2, borde=BORDE, rejilla=REJILLA, ejes=EJES,
    texto=TEXTO, texto2=TEXTO_2, texto3=TEXTO_3, acento=ACENTO, mono=MONO,
    acento10=rgba(ACENTO, 0.10), acento35=rgba(ACENTO, 0.35),
    insignias="\n".join(f".insignia.{reg} {{ color: {color}; }}"
                        for reg, color in COLOR_REGIMEN.items()),
)


def aplicar():
    """Inyecta el CSS en la página (llamar una vez por ejecución, al inicio)."""
    st.markdown(f"<style>{CSS}</style>", unsafe_allow_html=True)


def ocultar_barra_lateral():
    """En la pantalla de inicio no se muestra la barra lateral."""
    st.markdown("<style>[data-testid='stSidebar'], [data-testid='stSidebarCollapsedControl'],"
                "[data-testid='stExpandSidebarButton'] { display: none; }</style>",
                unsafe_allow_html=True)
