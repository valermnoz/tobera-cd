"""
estilo.py — Identidad visual de la interfaz (CSS sobre el tema de .streamlit/config.toml).

Estilo técnico tipo CAD/CAE en negro: paneles grafito con bordes finos de
1 px, naranja de escape como único acento y fuente monoespaciada en los
valores numéricos (KPIs y tablas de datos). También trae los estilos de la
pantalla de inicio (clases .hero, .cifras, .tarjetas, .pasos). Los colores salen de
graficas_gui.py para que la interfaz y las gráficas usen la misma paleta.
"""

from html import escape
from string import Template

import streamlit as st

from main import NOMBRES_REGIMEN

from graficas_gui import (ACENTO, ACENTO_CLARO, BORDE, COLOR_ERROR, COLOR_REGIMEN, EJES, FONDO, PANEL, PANEL_2, REJILLA,
                          TEXTO, TEXTO_2, TEXTO_3, rgba)

# Colores del veredicto de la validación (clases .insignia.veredicto-*)
COLOR_VEREDICTO = {"veredicto-excelente": COLOR_REGIMEN["adaptada"],
                   "veredicto-buena": ACENTO_CLARO, "veredicto-aceptable": "#F2C94C",
                   "veredicto-revisar": COLOR_ERROR}

MONO = '"IBM Plex Mono", "SF Mono", Menlo, Consolas, monospace'

CSS = Template("""
.stApp { background: $fondo; }
[data-testid="stHeader"] { background: transparent; }
.block-container { padding-top: 2.2rem; padding-bottom: 3rem; max-width: 1400px; }

h1, h2, h3, h4 { color: $texto; font-weight: 600; letter-spacing: -0.01em; }
h3 { font-size: 1.15rem; }
hr { border-color: $borde !important; }
[data-testid="stCaptionContainer"] { color: $texto2; }
a { color: $acentoclaro; }

/* Encabezado compacto */
.encabezado {
  display: flex; align-items: center; justify-content: space-between; gap: 1rem;
  flex-wrap: wrap; padding: 0.9rem 1.2rem; margin-bottom: 1rem;
  background: $panel;
  border: 1px solid $borde; border-radius: 4px;
}
.encabezado .marca { display: flex; align-items: center; gap: 0.9rem; }
.encabezado .logo {
  width: 42px; height: 42px; border-radius: 4px; flex: none;
  display: grid; place-items: center;
  background: $acento10; border: 1px solid $acento35;
}
.encabezado .titulo { font-size: 1.35rem; font-weight: 700; color: $texto; line-height: 1.15; }
.encabezado .titulo span { color: $acentoclaro; }
.encabezado .subtitulo { font-size: 0.85rem; color: $texto2; }
.encabezado .chips { display: flex; gap: 0.4rem; flex-wrap: wrap; }
.chip {
  font-size: 0.75rem; color: $texto2; padding: 0.2rem 0.6rem; border-radius: 999px;
  border: 1px solid $borde; background: $fondo; white-space: nowrap;
}
.chip b { color: $texto; font-weight: 600; font-family: $mono; }

/* Pantalla de inicio */
.hero {
  position: relative; overflow: hidden; border: 1px solid $borde; border-radius: 6px;
  padding: 4.2rem 3rem 3.6rem 3rem; margin-bottom: 1.2rem; min-height: 360px;
  background:
    linear-gradient(90deg, $fondo 0%, $fondo 38%, rgba(12,14,19,0.6) 70%, rgba(12,14,19,0.25) 100%),
    var(--foto) right center / cover no-repeat, $fondo;
}
.hero > * { position: relative; z-index: 1; max-width: 640px; }
.hero .antetitulo {
  font-size: 0.75rem; letter-spacing: 0.18em; text-transform: uppercase; color: $acentoclaro;
  font-weight: 600; margin-bottom: 0.9rem;
}
.hero .gran-titulo {
  font-size: 3.2rem; font-weight: 600; letter-spacing: -0.02em; line-height: 1.05;
  color: $texto; margin-bottom: 1rem;
}
.hero .gran-titulo span { color: $acentoclaro; }
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
.cifra { border: 1px solid $borde; border-radius: 4px; padding: 1rem 1.1rem; background: $panel; }
.cifra .valor { font-family: $mono; font-size: 1.7rem; font-weight: 600; color: $texto; }
.cifra .valor span { color: $acentoclaro; }
.cifra .etiqueta { font-size: 0.82rem; color: $texto2; margin-top: 0.2rem; }

.tarjetas { display: grid; grid-template-columns: repeat(3, 1fr); gap: 0.8rem; }
.tarjeta {
  border: 1px solid $borde; border-radius: 4px; padding: 1.2rem 1.2rem 1.1rem 1.2rem;
  background: $panel; transition: border-color 0.15s, transform 0.15s;
}
.tarjeta:hover { border-color: $ejes; }
.tarjeta .num { font-family: $mono; font-size: 0.75rem; color: $acentoclaro; margin-bottom: 0.6rem; }
.tarjeta .nombre { font-size: 1.02rem; font-weight: 600; color: $texto; margin-bottom: 0.35rem; }
.tarjeta .desc { font-size: 0.86rem; color: $texto2; line-height: 1.5; }

.pasos { display: grid; grid-template-columns: repeat(4, 1fr); gap: 0.8rem; }
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

/* Barra de navegación de la portada */
.nav {
  display: flex; justify-content: space-between; align-items: center; gap: 1rem;
  padding: 0 0 1rem 0; margin-bottom: 1rem; border-bottom: 1px solid $borde;
}
.nav .marca { display: flex; align-items: center; gap: 0.7rem; }
.nav .logo {
  width: 36px; height: 36px; border-radius: 4px; display: grid; place-items: center;
  background: $acento10; border: 1px solid $acento35;
}
.nav .titulo { font-size: 1.1rem; font-weight: 700; color: $texto; letter-spacing: 0.02em; }
.nav .titulo span { color: $acentoclaro; }
.nav-der { display: flex; gap: 1.4rem; flex-wrap: wrap; }
.nav-der span {
  font-family: $mono; font-size: 0.72rem; color: $texto3; text-transform: uppercase;
  letter-spacing: 0.1em;
}

/* Barra de estado del programa */
.barra-estado {
  display: flex; justify-content: space-between; gap: 1rem; flex-wrap: wrap;
  font-family: $mono; font-size: 0.68rem; letter-spacing: 0.12em; color: $texto3;
  text-transform: uppercase; padding: 0 0.2rem 0.55rem 0.2rem;
}
.estado { display: inline-flex; align-items: center; gap: 0.5rem; }
.estado::before {
  content: ""; width: 7px; height: 7px; border-radius: 50%; background: currentColor;
}
.estado.ok { color: #4ADE80; }
.estado.espera { color: #FACC15; }

/* Títulos de sección numerados */
.seccion {
  display: flex; align-items: baseline; gap: 0.8rem; margin: 2rem 0 0.35rem 0;
  padding-bottom: 0.5rem; border-bottom: 1px solid $borde;
}
.seccion-num { font-family: $mono; font-size: 0.78rem; color: $acentoclaro; font-weight: 600; }
.seccion-texto {
  font-size: 0.86rem; font-weight: 600; color: $texto; text-transform: uppercase;
  letter-spacing: 0.12em;
}
.seccion-nota { font-size: 0.84rem; color: $texto3; margin: 0.2rem 0 0.8rem 0; }

/* Lecturas tipo consola (telemetría) */
.telemetria {
  display: grid; grid-template-columns: repeat(auto-fit, minmax(118px, 1fr));
  border: 1px solid $borde; border-radius: 4px; background: $panel; margin: 0.6rem 0 0.8rem 0;
}
.lectura { padding: 0.8rem 1rem; border-right: 1px solid $borde; position: relative; }
.lectura:last-child { border-right: none; }
.lectura::before {
  content: ""; position: absolute; left: 0; top: 0; width: 10px; height: 1px;
  background: $acento;
}
.lectura-etq {
  font-family: $mono; font-size: 0.64rem; color: $texto3; text-transform: uppercase;
  letter-spacing: 0.12em; margin-bottom: 0.35rem;
}
.lectura-val { font-family: $mono; font-size: 1.25rem; font-weight: 600; color: $texto; }
.lectura-val span { font-size: 0.75rem; color: $texto2; font-weight: 400; }
.lectura-etq sub, .lectura-etq sup, .seccion-texto sub { font-size: 0.75em; text-transform: none; }

/* Hoja de especificaciones */
.especificaciones {
  display: grid; grid-template-columns: repeat(2, 1fr); border: 1px solid $borde;
  border-radius: 4px; background: $panel;
}
.espec { display: flex; gap: 1rem; padding: 0.75rem 1rem; border-bottom: 1px solid $rejilla; }
.espec:nth-child(odd) { border-right: 1px solid $rejilla; }
.espec:nth-last-child(-n+2) { border-bottom: none; }
.espec-etq {
  flex: 0 0 120px; font-family: $mono; font-size: 0.68rem; color: $texto3;
  text-transform: uppercase; letter-spacing: 0.1em; padding-top: 0.15rem;
}
.espec-val { font-size: 0.88rem; color: $texto; }
@media (max-width: 900px) {
  .especificaciones { grid-template-columns: 1fr; }
  .espec:nth-child(odd) { border-right: none; }
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
  background: $panel; border: 1px solid $borde; border-radius: 4px;
  padding: 0.75rem 1rem; border-top: 1px solid $acento;
}
[data-testid="stMetricLabel"], [data-testid="stMetricLabel"] p {
  color: $texto3; font-size: 0.66rem; text-transform: uppercase; letter-spacing: 0.12em;
  font-family: $mono;
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
  font-size: 0.72rem; font-weight: 600; color: $acentoclaro; text-transform: uppercase;
  letter-spacing: 0.08em; margin: 0.2rem 0 0.4rem 0; padding-bottom: 0.3rem;
  border-bottom: 1px solid $borde;
}

/* Pestañas */
[data-baseweb="tab-list"] { gap: 0.25rem; border-bottom: 1px solid $borde; }
button[data-baseweb="tab"] {
  background: transparent; border: none; border-radius: 3px 3px 0 0;
  padding: 0.55rem 1.1rem; height: auto;
}
button[data-baseweb="tab"]:hover { background: $panel; }
button[data-baseweb="tab"] p { color: $texto2; font-weight: 500; font-size: 0.92rem; }
button[data-baseweb="tab"][aria-selected="true"] { background: $panel; }
button[data-baseweb="tab"][aria-selected="true"] p { color: $acentoclaro; font-weight: 600; }
[data-baseweb="tab-highlight"] { background-color: $acento; height: 2px; }
[data-baseweb="tab-border"] { background-color: transparent; }

/* Botones */
[data-testid="stBaseButton-secondary"] { border-radius: 4px; font-weight: 500; background: $panel; }
[data-testid="stBaseButton-secondary"]:hover { border-color: $acentoclaro; color: $acentoclaro; }
[data-testid="stBaseButton-primary"] {
  border-radius: 4px; font-weight: 600; background: $acento; border-color: $acento; color: #FFFFFF;
}
[data-testid="stBaseButton-primary"]:hover { color: #FFFFFF; filter: brightness(1.12); }
[data-testid="stBaseButton-primary"] p { color: #FFFFFF; }

/* Desplegables, cargadores de archivos y avisos */
[data-testid="stExpander"] details {
  border: 1px solid $borde; border-radius: 4px; background: $panel;
}
[data-testid="stFileUploaderDropzone"] {
  border: 1px dashed $ejes; border-radius: 4px; background: $panel;
}
[data-testid="stAlert"] { border-radius: 4px; }

/* Tablas de datos */
.tabla-datos { overflow-x: auto; margin-bottom: 1rem; }
.tabla-datos table {
  width: 100%; border-collapse: separate; border-spacing: 0;
  border: 1px solid $borde; border-radius: 4px; overflow: hidden; background: $panel;
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
  border: 1px solid $borde; border-radius: 4px; padding: 0.3rem; background: $panel;
  overflow: hidden;
}
[data-testid="stImage"] img { border-radius: 6px; border: 1px solid $borde; }
[data-testid="stImageCaption"], [data-testid="stImage"] figcaption {
  color: $texto3; font-size: 0.72rem; line-height: 1.3;
}
""").safe_substitute(
    fondo=FONDO, panel=PANEL, panel2=PANEL_2, borde=BORDE, rejilla=REJILLA, ejes=EJES,
    texto=TEXTO, texto2=TEXTO_2, texto3=TEXTO_3, acento=ACENTO, mono=MONO,
    acento10=rgba(ACENTO, 0.12), acento35=rgba(ACENTO, 0.45), acentoclaro=ACENTO_CLARO,
    insignias="\n".join(f".insignia.{reg} {{ color: {color}; }}"
                        for reg, color in {**COLOR_REGIMEN, **COLOR_VEREDICTO}.items()),
)


def aplicar():
    """Inyecta el CSS en la página (llamar una vez por ejecución, al inicio)."""
    st.markdown(f"<style>{CSS}</style>", unsafe_allow_html=True)


def ocultar_barra_lateral():
    """En la pantalla de inicio no se muestra la barra lateral."""
    st.markdown("<style>[data-testid='stSidebar'], [data-testid='stSidebarCollapsedControl'],"
                "[data-testid='stExpandSidebarButton'] { display: none; }</style>",
                unsafe_allow_html=True)


def titulo_seccion(numero, texto, nota=None):
    """
    Encabezado de sección numerado, estilo hoja técnica: '01  ANÁLISIS ...'.
    'texto' admite <sub>/<sup> (son textos fijos del programa). La nota se
    escribe en Markdown, así que las fórmulas entre $...$ salen como ecuación.
    """
    st.markdown(f'<div class="seccion"><span class="seccion-num">{escape(numero)}</span>'
                f'<span class="seccion-texto">{texto}</span></div>', unsafe_allow_html=True)
    if nota:
        st.caption(nota)


def insignia(clave, texto):
    """Etiqueta de color para un régimen (clave de tobera.regimen)."""
    return f'<span class="insignia {escape(clave)}">{escape(texto)}</span>'


def telemetria(valores):
    """
    Fila de lecturas tipo consola: [(etiqueta, valor, unidad)]. La etiqueta
    admite <sub>/<sup> para los símbolos (C<sub>F</sub>, Re<sup>*</sup>).
    """
    celdas = "".join(f'<div class="lectura"><div class="lectura-etq">{e}</div>'
                     f'<div class="lectura-val">{v}<span>{escape(u)}</span></div></div>'
                     for e, v, u in valores)
    st.markdown(f'<div class="telemetria">{celdas}</div>', unsafe_allow_html=True)


# Texto del régimen (como sale en resumen.txt) -> clave, para colorear las insignias
_CLAVE_REGIMEN = {texto: clave for clave, texto in NOMBRES_REGIMEN.items()}


def mostrar_tabla(df, derecha=(), insignia=None):
    """
    Tabla de datos en HTML (clase tabla-datos, ver estilo.py). Las columnas de
    'derecha' son numéricas: van alineadas a la derecha y en fuente monoespaciada.
    La columna 'insignia' (el régimen) se dibuja como etiqueta de color.
    """
    def celda(etiqueta, valor, columna):
        clase = "num" if columna in derecha else "txt"
        texto = escape(str(valor))
        if etiqueta == "td" and columna == insignia:
            texto = f'<span class="insignia {_CLAVE_REGIMEN.get(valor, "")}">{texto}</span>'
        return f'<{etiqueta} class="{clase}">{texto}</{etiqueta}>'

    cabecera = "".join(celda("th", c, c) for c in df.columns)
    filas = "".join("<tr>" + "".join(celda("td", v, c) for c, v in fila.items()) + "</tr>"
                    for _, fila in df.iterrows())
    st.markdown(f'<div class="tabla-datos"><table><thead><tr>{cabecera}</tr></thead>'
                f"<tbody>{filas}</tbody></table></div>", unsafe_allow_html=True)
