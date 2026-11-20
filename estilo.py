"""
estilo.py — Identidad visual de la interfaz (CSS sobre el tema de .streamlit/config.toml).

Estilo técnico tipo CAD/CAE: fondo blanco, bordes finos de 1 px y esquinas de
4 px, azul acero y cian como acento, y fuente monoespaciada en los valores
numéricos (KPIs y tablas de datos). Los colores salen de graficas.py para que
la interfaz y las gráficas usen la misma paleta.
"""

from string import Template

import streamlit as st

from graficas import AZUL, BORDE, EJES, FONDO_TARJETA, REJILLA, TINTA, TINTA_2

MONO = '"JetBrains Mono", Consolas, "SF Mono", Menlo, monospace'
GRIS_PANEL = "#F1F5F9"  # igual que secondaryBackgroundColor

CSS = Template("""
.stApp { background: #FFFFFF; }
[data-testid="stHeader"] { background: #FFFFFF; border-bottom: 1px solid $borde; }
.block-container { padding-top: 3.5rem; }

h1 {
  color: #0F172A; font-weight: 600; letter-spacing: -0.01em;
  padding-bottom: 0.4rem; border-bottom: 2px solid $azul; margin-bottom: 0.8rem;
}
h2, h3, h4 { color: #0F172A; font-weight: 600; }
hr { border-color: $borde; }
[data-testid="stCaptionContainer"] { color: $tinta2; }

/* Tarjetas de métricas (KPIs) */
[data-testid="stMetric"] {
  background: $fondo; border: 1px solid $borde; border-radius: 4px;
  padding: 0.65rem 0.9rem;
}
[data-testid="stMetricLabel"], [data-testid="stMetricLabel"] p {
  color: $tinta2; font-size: 0.74rem; text-transform: uppercase; letter-spacing: 0.04em;
}
[data-testid="stMetricValue"], [data-testid="stMetricValue"] * {
  font-family: $mono !important; font-weight: 600; color: #0F172A;
}
[data-testid="stMetricValue"] { font-size: 1.35rem; }

/* Campos de entrada */
div[data-baseweb="input"], div[data-baseweb="select"] > div, div[data-baseweb="textarea"] {
  border: 1px solid $borde !important; border-radius: 4px !important;
  background-color: $panel !important;
}
div[data-baseweb="input"]:focus-within, div[data-baseweb="select"] > div:focus-within {
  border-color: $azul !important; box-shadow: 0 0 0 1px $azul;
}
[data-testid="stWidgetLabel"] p { color: $tinta; font-size: 0.85rem; font-weight: 500; }

/* Pestañas */
[data-baseweb="tab-list"] { gap: 2px; border-bottom: 1px solid $borde; }
button[data-baseweb="tab"] {
  background: $panel; border: 1px solid $borde; border-bottom: none;
  border-radius: 4px 4px 0 0; padding: 0.45rem 1.2rem; height: auto;
}
button[data-baseweb="tab"] p { color: $tinta2; font-weight: 500; }
button[data-baseweb="tab"][aria-selected="true"] { background: #FFFFFF; }
button[data-baseweb="tab"][aria-selected="true"] p { color: $azul; font-weight: 600; }
[data-baseweb="tab-highlight"] { background-color: $azul; height: 2px; }
[data-baseweb="tab-border"] { background-color: $borde; }

/* Botones */
.stButton > button, .stDownloadButton > button {
  border: 1px solid $borde; border-radius: 4px; font-weight: 500;
}
.stButton > button:hover, .stDownloadButton > button:hover {
  border-color: $azul; color: $azul;
}
.stButton > button[kind="primary"] { border-color: $azul; }
.stButton > button[kind="primary"]:hover { color: #FFFFFF; filter: brightness(1.08); }

/* Desplegables, cargadores de archivos y avisos */
[data-testid="stExpander"] details {
  border: 1px solid $borde; border-radius: 4px; background: #FFFFFF;
}
[data-testid="stExpander"] summary { background: $fondo; border-radius: 4px; }
[data-testid="stFileUploaderDropzone"] {
  border: 1px dashed $ejes; border-radius: 4px; background: $fondo;
}
[data-testid="stAlert"] { border: 1px solid $borde; border-radius: 4px; }

/* Tablas de datos */
.tabla-datos { overflow-x: auto; margin-bottom: 1rem; }
.tabla-datos table {
  width: 100%; border-collapse: separate; border-spacing: 0;
  border: 1px solid $borde; border-radius: 4px; overflow: hidden;
}
.tabla-datos th {
  background: $panel; color: #0F172A; font-size: 0.78rem; font-weight: 600;
  padding: 0.45rem 0.7rem; border-bottom: 1px solid $borde; white-space: nowrap;
}
.tabla-datos td {
  font-size: 0.88rem; color: $tinta; padding: 0.4rem 0.7rem;
  border-bottom: 1px solid $rejilla;
}
.tabla-datos .txt { text-align: left; }
.tabla-datos .num { text-align: right; }
.tabla-datos td.num { font-family: $mono; font-size: 0.84rem; }
.tabla-datos tbody tr:last-child td { border-bottom: none; }
.tabla-datos tbody tr:nth-child(even) td { background: $fondo; }

/* Gráficas y fotografías en contenedores limpios */
[data-testid="stPlotlyChart"] {
  border: 1px solid $borde; border-radius: 4px; padding: 0.25rem; background: #FFFFFF;
}
[data-testid="stImage"] {
  background: $fondo; border: 1px solid $borde; border-radius: 4px; padding: 0.5rem;
  width: 100%;
}
[data-testid="stImage"] img { border-radius: 2px; }
[data-testid="stImageCaption"], [data-testid="stImage"] figcaption {
  color: $tinta2; font-size: 0.72rem; line-height: 1.3;
}
""").safe_substitute(
    borde=BORDE, azul=AZUL, tinta=TINTA, tinta2=TINTA_2, fondo=FONDO_TARJETA,
    panel=GRIS_PANEL, ejes=EJES, rejilla=REJILLA, mono=MONO,
)


def aplicar():
    """Inyecta el CSS en la página (llamar una vez por ejecución, al inicio)."""
    st.markdown(f"<style>{CSS}</style>", unsafe_allow_html=True)
