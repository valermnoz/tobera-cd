"""
app.py — Interfaz gráfica de TOBERA-CD (Streamlit).

Uso:
    streamlit run app.py

Primero se muestra una pantalla de inicio; con "Comenzar" se entra al
programa, que tiene tres pestañas:
  Caso          abrir o crear el .json, ver el perfil y simular
  Resultados    resumen, presión estática y Mach (después de simular)
  Validación    comparar con el CSV de SolidWorks (después de simular y de
                correr Flow Simulation sobre el contorno generado)

Esta capa solo maneja la interfaz. Los cálculos están en configuracion.py,
main.py y los módulos de cálculo; el resumen se lee con resumen_txt.py, la
comparación está en comparacion.py y las figuras en graficas_gui.py.
"""

import base64
from html import escape
from pathlib import Path

import pandas as pd
import streamlit as st

import comparacion as cmp
import configuracion as cfg
import estilo
from geometria import GEOMETRIA_DEFECTO
from graficas_gui import (ACENTO, CONFIG, figura_campo, figura_distribucion, figura_error,
                          figura_geometria, figura_mapa_regimenes, figura_superpuesta)
from interactivo import DESCRIPCION_GEOMETRIA
from main import NOMBRES_REGIMEN
from resumen_txt import parsear_resumen
from tobera import curva_empuje

st.set_page_config(page_title="TOBERA-CD · Toberas convergente–divergentes", page_icon="🚀",
                   layout="wide", initial_sidebar_state="expanded")
estilo.aplicar()

DIR_ASSETS = Path(__file__).parent / "assets"
OPCION_NUEVO = "(caso nuevo)"
CAMPOS = ("nombre", "descripcion", "gamma", "R", "p0_MPa", "T0_K", "altitud_m", "pa_kPa",
          "F_N", "pb_kPa")

# Límites de los campos de geometría: (mínimo, máximo, paso)
LIMITES_GEOMETRIA = {
    "angulo_convergente_deg": (1.0, 89.0, 1.0),
    "angulo_divergente_deg": (1.0, 89.0, 0.5),
    "relacion_contraccion": (1.01, 100.0, 0.5),
    "longitud_recta_entrada_mm": (0.0, 1000.0, 1.0),
    "radio_arco_entrada_rt": (0.01, 20.0, 0.1),
    "radio_garganta_arriba_rt": (0.01, 20.0, 0.1),
    "radio_garganta_abajo_rt": (0.01, 20.0, 0.1),
    "espesor_pared_mm": (0.01, 100.0, 0.5),
}
PAREDES = {"constante": "Espesor constante", "cilindrica": "Tubo recto"}
# Texto del régimen (como sale en resumen.txt) -> clave, para colorear las insignias
CLAVE_REGIMEN = {texto: clave for clave, texto in NOMBRES_REGIMEN.items()}


def grupo(texto):
    """Pequeño título de sección dentro del formulario."""
    st.markdown(f'<div class="grupo">{escape(texto)}</div>', unsafe_allow_html=True)


# ---------------------------------------------------------------------
# Estado del formulario
# ---------------------------------------------------------------------

def cargar_en_formulario(caso, origen):
    """Pasa un caso a los widgets del formulario."""
    v = cfg.valores_formulario(caso)
    for campo in CAMPOS:
        st.session_state[f"f_{campo}"] = v[campo]
    st.session_state["f_ambiente"] = "Altitud" if v["por_altitud"] else "Presión"
    for clave, valor in v["geometria"].items():
        st.session_state[f"g_{clave}"] = valor
    st.session_state["origen_caso"] = origen
    st.session_state.pop("resultado", None)


def valores_actuales():
    v = {campo: st.session_state[f"f_{campo}"] for campo in CAMPOS}
    v["por_altitud"] = st.session_state["f_ambiente"] == "Altitud"
    v["geometria"] = {clave: st.session_state[f"g_{clave}"] for clave in GEOMETRIA_DEFECTO}
    return v


def _al_elegir_caso():
    sel = st.session_state["sel_caso"]
    try:
        if sel == OPCION_NUEVO:
            cargar_en_formulario(cfg.CASO_NUEVO, "caso nuevo")
        else:
            cargar_en_formulario(cfg.leer_json(Path(sel).read_text(encoding="utf-8")), sel)
    except (OSError, ValueError) as e:
        st.session_state["aviso"] = ("error", str(e))


def inicializar():
    if "f_nombre" in st.session_state:
        return
    preliminar = cfg.DIR_CASOS / "caso_preliminar.json"
    ruta = preliminar if preliminar.exists() else next(iter(cfg.listar_casos()), None)
    if ruta is not None:
        try:
            cargar_en_formulario(cfg.leer_json(ruta.read_text(encoding="utf-8")), str(ruta))
            st.session_state["sel_caso"] = str(ruta)
            return
        except (OSError, ValueError):
            pass
    cargar_en_formulario(cfg.CASO_NUEVO, "caso nuevo")


# ---------------------------------------------------------------------
# Pestaña: caso
# ---------------------------------------------------------------------

def _formulario():
    c1, c2 = st.columns([1, 2])
    c1.text_input("Nombre del caso", key="f_nombre")
    c2.text_input("Descripción", key="f_descripcion")

    gas, camara, ambiente, diseno = st.columns(4)
    with gas:
        grupo("Gas")
        st.number_input("gamma [–]", min_value=1.01, max_value=1.67, step=0.01,
                        format="%.3f", key="f_gamma")
        st.number_input("R [J/(kg·K)]", min_value=1.0, max_value=5000.0, step=1.0,
                        format="%.2f", key="f_R")
    with camara:
        grupo("Cámara")
        st.number_input("Presión de cámara p0 [MPa]", min_value=0.01, max_value=100.0,
                        step=0.1, format="%.4f", key="f_p0_MPa")
        st.number_input("Temperatura de cámara T0 [K]", min_value=1.0, max_value=5000.0,
                        step=10.0, format="%.1f", key="f_T0_K")
    with ambiente:
        grupo("Ambiente")
        por_altitud = st.radio("Ambiente definido por", ["Altitud", "Presión"],
                               horizontal=True, key="f_ambiente") == "Altitud"
        # Se dibujan los dos campos (uno deshabilitado) para que Streamlit
        # conserve el valor del que no se usa.
        st.number_input("Altitud [m]", min_value=-500.0, max_value=11000.0, step=100.0,
                        key="f_altitud_m", disabled=not por_altitud)
        st.number_input("Presión ambiente [kPa]", min_value=0.001, max_value=10000.0,
                        step=1.0, format="%.3f", key="f_pa_kPa", disabled=por_altitud)
    with diseno:
        grupo("Diseño")
        st.number_input("Empuje requerido [N]", min_value=0.001, max_value=1e7, step=10.0,
                        format="%.3f", key="f_F_N")
        st.text_input("Presiones exteriores [kPa]", key="f_pb_kPa",
                      help='Lista separada por comas, o "auto" para una por régimen. '
                           "La presión ambiente de diseño siempre se analiza.")

    with st.expander("Geometría de la tobera (valores por defecto si no se cambian)"):
        columnas = st.columns(4)
        for i, (clave, texto) in enumerate(DESCRIPCION_GEOMETRIA.items()):
            minimo, maximo, paso = LIMITES_GEOMETRIA[clave]
            columnas[i % 4].number_input(texto, min_value=minimo, max_value=maximo,
                                         step=paso, format="%.3f", key=f"g_{clave}")
        st.radio("Pared exterior", list(PAREDES), format_func=PAREDES.get, horizontal=True,
                 key="g_tipo_pared")


def _guardar_y_simular(caso, simular):
    try:
        ruta = cfg.guardar_caso(caso, sobrescribir=True)
        mensaje = f"Caso guardado en {ruta}."
        if simular:
            with st.spinner("Simulando..."):
                resultado = cfg.ejecutar(caso)
            resultado["id"] = st.session_state.get("n_corridas", 0) + 1
            st.session_state["n_corridas"] = resultado["id"]
            st.session_state["resultado"] = resultado
            mensaje += f" Resultados en {resultado['salida']}/. Revisa la pestaña Resultados."
    except (OSError, ValueError, ArithmeticError) as e:
        st.session_state["aviso"] = ("error", f"No se pudo completar la operación: {e}")
    else:
        st.session_state["origen_caso"] = str(ruta)
        st.session_state["_sel_pendiente"] = str(ruta)
        st.session_state["aviso"] = ("success", mensaje)
    st.rerun()


def _sobrescribe_otro_caso(caso):
    """True si guardar reemplazaría un .json de casos/ distinto del que se abrió."""
    try:
        destino = cfg.DIR_CASOS / f"{cfg.nombre_archivo(caso['nombre'])}.json"
    except ValueError:
        return False
    origen = Path(st.session_state.get("origen_caso", ""))
    return destino.exists() and origen.resolve() != destino.resolve()


def pestana_caso():
    opciones = [OPCION_NUEVO] + [str(c) for c in cfg.listar_casos()]
    if st.session_state.get("sel_caso") not in opciones:
        st.session_state["sel_caso"] = OPCION_NUEVO

    c1, c2 = st.columns(2)
    c1.selectbox("Abrir un caso de la carpeta casos/", opciones, key="sel_caso",
                 on_change=_al_elegir_caso)
    archivo = c2.file_uploader("O subir un archivo .json", type=["json"], key="subir_json")
    if archivo is not None:
        firma = (archivo.name, archivo.size)
        if st.session_state.get("_firma_json") != firma:
            st.session_state["_firma_json"] = firma
            try:
                cargar_en_formulario(cfg.leer_json(archivo.getvalue().decode("utf-8-sig")),
                                     archivo.name)
                st.session_state["aviso"] = ("success", f"Caso cargado desde {archivo.name}.")
            except (UnicodeDecodeError, ValueError) as e:
                st.session_state["aviso"] = ("error", str(e))

    aviso = st.session_state.pop("aviso", None)
    if aviso:
        getattr(st, aviso[0])(aviso[1])
    st.caption(f"Editando: {st.session_state.get('origen_caso', '-')}")

    _formulario()

    try:
        caso, error = cfg.construir_caso(valores_actuales()), None
    except ValueError as e:
        caso, error = None, str(e)

    bloqueado = caso is None
    if caso is not None and _sobrescribe_otro_caso(caso):
        destino = f"{cfg.nombre_archivo(caso['nombre'])}.json"
        st.warning(f"Ya existe casos/{destino} y no es el caso que abriste. "
                   "Al guardar se reemplaza. Cambia el nombre o confirma.")
        bloqueado = not st.checkbox(f"Sí, reemplazar casos/{destino}", key=f"conf_{destino}")

    b1, b2, b3, _ = st.columns([1, 1.3, 1.3, 3])
    guardar = b1.button("Guardar", disabled=bloqueado, width="stretch")
    simular = b2.button("Guardar y simular", type="primary", disabled=bloqueado,
                        width="stretch")
    if caso is None:
        st.error(f"Revisa el formulario: {error}")
    else:
        b3.download_button("Descargar .json", cfg.caso_a_json(caso),
                           file_name=f"{caso['nombre']}.json", mime="application/json",
                           width="stretch")
    if guardar or simular:
        _guardar_y_simular(caso, simular)

    st.divider()
    st.subheader("Perfil de la tobera")
    st.caption("Vista previa: se actualiza al editar el formulario, sin simular.")
    if caso is None:
        return
    try:
        pre = cfg.geometria_preliminar(caso)
    except (ValueError, ArithmeticError) as e:
        st.error(f"No se puede construir la tobera con estos datos: {e}")
        return
    d, geo, g = pre["diseno"], pre["geometria"], pre["caso"]["geometria"]
    st.plotly_chart(figura_geometria(pre["tramos"], geo, d, g["espesor_pared_mm"] / 1e3,
                                     g["tipo_pared"]), theme=None, config=CONFIG)


# ---------------------------------------------------------------------
# Pestaña: resultados
# ---------------------------------------------------------------------

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
            texto = f'<span class="insignia {CLAVE_REGIMEN.get(valor, "")}">{texto}</span>'
        return f'<{etiqueta} class="{clase}">{texto}</{etiqueta}>'

    cabecera = "".join(celda("th", c, c) for c in df.columns)
    filas = "".join("<tr>" + "".join(celda("td", v, c) for c, v in fila.items()) + "</tr>"
                    for _, fila in df.iterrows())
    st.markdown(f'<div class="tabla-datos"><table><thead><tr>{cabecera}</tr></thead>'
                f"<tbody>{filas}</tbody></table></div>", unsafe_allow_html=True)


KPIS = ("Mach de salida", "Diámetro de garganta", "Diámetro de salida", "Gasto másico",
        "Coeficiente de empuje", "Longitud total")


def _boton_archivo(resultado, nombre, mime, etiqueta, columna=st, prefijo="res"):
    ruta = resultado["salida"] / nombre
    if ruta.exists():
        columna.download_button(etiqueta, ruta.read_bytes(), file_name=nombre, mime=mime,
                                key=f"{prefijo}_{nombre}_{resultado['id']}")


def pestana_resultados(resultado):
    if resultado is None:
        st.info("Aún no hay resultados. Guarda y simula un caso en la pestaña Caso.")
        return
    caso, res = resultado["caso"], resultado["res"]
    try:
        datos = parsear_resumen(resultado["resumen"])
    except ValueError as e:
        st.error(str(e))
        return

    st.subheader(datos["nombre"])
    if datos["descripcion"]:
        st.caption(datos["descripcion"])

    valores = datos["dimensionamiento"] + datos["geometria"]
    elegidos = [next(v for v in valores if v["nombre"].startswith(k)) for k in KPIS
                if any(v["nombre"].startswith(k) for v in valores)]
    # Tarjetas en filas de 3 para que los valores no se corten
    for i in range(0, len(elegidos), 3):
        for col, v in zip(st.columns(3), elegidos[i:i + 3]):
            col.metric(v["nombre"], f"{v['texto']} {v['unidad']}".strip())

    st.markdown("### Análisis por presión exterior")
    def fmt(valor, formato):
        return "–" if valor is None else format(valor, formato)

    filas = [{
        "p_b [kPa]": fmt(a["pb_kPa"], ".1f"), "Régimen": a["regimen"],
        "Me": fmt(a["Me"], ".3f"), "Gasto [kg/s]": fmt(a["m_kg_s"], ".4f"),
        "Empuje [N]": fmt(a["F_N"], ".2f"),
        "x del choque [mm]": fmt((a["choque"] or {}).get("x_mm"), ".2f"),
    } for a in datos["analisis"]]
    mostrar_tabla(pd.DataFrame(filas), derecha=["p_b [kPa]", "Me", "Gasto [kg/s]",
                                                "Empuje [N]", "x del choque [mm]"],
                  insignia="Régimen")

    with st.expander("Todos los valores de resumen.txt"):
        filas = [{"Sección": titulo, "Parámetro": v["etiqueta"], "Valor": v["texto"],
                  "Unidad": v["unidad"]}
                 for clave, titulo in (("dimensionamiento", "Dimensionamiento"),
                                       ("geometria", "Geometría"),
                                       ("criticas", "Presiones críticas"))
                 for v in datos[clave]]
        mostrar_tabla(pd.DataFrame(filas), derecha=["Valor"])

    st.markdown("### Distribuciones a lo largo de la tobera")
    st.plotly_chart(figura_distribucion(res["x"], res["distribuciones"], "p", res["criticas"]),
                    theme=None, config=CONFIG)
    st.plotly_chart(figura_distribucion(res["x"], res["distribuciones"], "M"), theme=None, config=CONFIG)

    st.markdown("### Campo sobre la tobera")
    st.caption("Misma solución cuasi-1D pintada sobre la geometría real, como se ve en Flow "
               "Simulation. Útil para comparar visualmente con el CFD.")
    dist = res["distribuciones"]
    i_diseno = next((i for i, d in enumerate(dist) if d["pb"] == caso["pa_Pa"]), 0)
    c1, c2 = st.columns([4, 1])
    i_campo = c2.selectbox("Presión exterior", list(range(len(dist))), index=i_diseno,
                           format_func=lambda i: f"{dist[i]['pb']/1e3:.1f} kPa · "
                                                 f"{NOMBRES_REGIMEN[dist[i]['regimen']]}",
                           key=f"campo_pb_{resultado['id']}")
    variable = c2.radio("Variable", ["Mach", "Presión"], key="campo_var")
    c1.plotly_chart(figura_campo(res["x"], res["r"], dist[i_campo],
                                 "M" if variable == "Mach" else "p", caso["camara"]["p0_Pa"]),
                    theme=None, config=CONFIG)

    st.markdown("### Mapa de regímenes")
    st.caption("Empuje de esta tobera para cualquier presión exterior. Las bandas son los "
               "regímenes que separan p₁, p₂ y p₃; los puntos son las presiones analizadas.")
    d = res["diseno"]
    curva = curva_empuje(caso["camara"]["p0_Pa"], caso["camara"]["T0_K"], d["At"], d["Ae_At"],
                         caso["gas"]["gamma"], caso["gas"]["R"])
    st.plotly_chart(figura_mapa_regimenes(curva, res["criticas"], caso["camara"]["p0_Pa"],
                                          caso["pa_Pa"], res["analisis"]), theme=None, config=CONFIG)

    st.markdown("### Archivos")
    st.caption(f"Guardados en {resultado['salida']}/")
    cols = st.columns(4)
    _boton_archivo(resultado, "resumen.txt", "text/plain", "Descargar resumen.txt", cols[0])
    _boton_archivo(resultado, "distribucion.csv", "text/csv", "Descargar distribucion.csv", cols[1])
    _boton_archivo(resultado, "contorno.dxf", "application/dxf", "Descargar contorno.dxf", cols[2])
    _boton_archivo(resultado, "dimensiones.txt", "text/plain", "Descargar dimensiones.txt", cols[3])


# ---------------------------------------------------------------------
# Pestaña: validación con SolidWorks
# ---------------------------------------------------------------------

def _indice(opciones, valor):
    return opciones.index(valor) if valor in opciones else 0


def pestana_validacion(resultado):
    if resultado is None:
        st.info("Primero simula un caso en la pestaña Caso. La comparación usa sus resultados.")
        return
    caso, res = resultado["caso"], resultado["res"]
    geo = res["geometria"]

    st.markdown(
        "1. Descarga el contorno y modélalo en SolidWorks (ver README).\n"
        "2. Corre la simulación en Flow Simulation y exporta los resultados a lo largo "
        "del eje de la tobera como .csv.\n"
        "3. Sube el .csv aquí."
    )
    _boton_archivo(resultado, "contorno.dxf", "application/dxf", "Descargar contorno.dxf",
                   prefijo="val")

    archivo = st.file_uploader("Resultados de SolidWorks (.csv)", type=["csv", "txt"],
                               key="subir_csv")
    if archivo is None:
        return
    try:
        tabla = cmp.leer_csv_solidworks(archivo.getvalue())
    except ValueError as e:
        st.error(f"No se pudo leer el CSV: {e}")
        return

    columnas = list(tabla.columns)
    auto = cmp.detectar_columnas(columnas)
    sufijo = f"{archivo.name}_{archivo.size}"  # reinicia los widgets con cada archivo
    ninguna = "(ninguna)"
    opciones_y = [ninguna] + columnas

    analisis = res["analisis"]
    etiquetas = [f"{a['pb_Pa']/1e3:.1f} kPa · {NOMBRES_REGIMEN[a['regimen']]}" for a in analisis]
    i_diseno = next((i for i, a in enumerate(analisis) if a["pb_Pa"] == caso["pa_Pa"]), 0)

    c = st.columns(4)
    col_x = c[0].selectbox("Columna de posición", columnas,
                           index=_indice(columnas, auto["x"]), key=f"cx_{sufijo}")
    col_p = c[1].selectbox("Columna de presión estática", opciones_y,
                           index=_indice(opciones_y, auto["p"] or ninguna), key=f"cp_{sufijo}")
    col_M = c[2].selectbox("Columna de número de Mach", opciones_y,
                           index=_indice(opciones_y, auto["M"] or ninguna), key=f"cM_{sufijo}")
    i_pb = c[3].selectbox("Presión exterior simulada", list(range(len(etiquetas))),
                          index=i_diseno, format_func=lambda i: etiquetas[i],
                          key=f"pb_{sufijo}_{resultado['id']}")

    with st.expander("Unidades y alineación"):
        a = st.columns(5)
        unidades_l, unidades_p = list(cmp.A_MM), list(cmp.A_PA)
        u_x = a[0].selectbox("Unidad de posición", unidades_l, key=f"ux_{sufijo}_{col_x}",
                             index=_indice(unidades_l,
                                           cmp.unidad_en_nombre(col_x, unidades_l) or "m"))
        u_p = a[1].selectbox("Unidad de presión", unidades_p, key=f"up_{sufijo}_{col_p}",
                             index=_indice(unidades_p,
                                           cmp.unidad_en_nombre(col_p, unidades_p) or "Pa"))
        origen = a[2].selectbox("x = 0 del CSV está en", list(cmp.ORIGENES),
                                format_func=cmp.ORIGENES.get, key="sw_origen")
        desplazamiento = a[3].number_input("Desplazamiento [mm]", step=0.1, format="%.3f",
                                           key="sw_desplazamiento")
        invertir = a[4].checkbox("El flujo va en -x", key="sw_invertir")
        st.caption(f"Tobera del modelo: de x = {geo['x_entrada']*1e3:.2f} mm (entrada) a "
                   f"{geo['x_salida']*1e3:.2f} mm (salida).")

    if col_p == ninguna and col_M == ninguna:
        st.warning("Elige al menos la columna de presión o la de Mach.")
        return

    modo = st.radio("Error a graficar", ["porcentual", "absoluto"], horizontal=True,
                    format_func=str.capitalize)
    d = res["distribuciones"][i_pb]
    x_modelo = res["x"] * 1e3
    if d["x_choque"] is not None:
        st.caption(f"Con esta presión hay un choque normal en x = {d['x_choque']*1e3:.2f} mm. "
                   "El CFD lo reparte en varias celdas, así que el error local ahí es grande.")

    variables = []
    if col_p != ninguna:
        variables.append(("Presión estática", "kPa", "p", col_p, cmp.A_PA[u_p] / 1e3, d["p"] / 1e3))
    if col_M != ninguna:
        variables.append(("Número de Mach", "–", "M", col_M, 1.0, d["M"]))

    x_sw = cmp.alinear_x(tabla[col_x].to_numpy() * cmp.A_MM[u_x], geo, origen, invertir,
                         desplazamiento)
    comparaciones = {}
    for nombre, unidad, clave, col, factor, y_modelo in variables:
        st.subheader(nombre)
        try:
            comp = cmp.comparar(x_modelo, y_modelo, x_sw, tabla[col].to_numpy() * factor)
        except ValueError as e:
            st.error(str(e))
            continue
        comparaciones["p_kPa" if clave == "p" else "M"] = comp
        m = comp["metricas"]
        sufijo_u = "" if unidad == "–" else f" {unidad}"
        k = st.columns(4)
        k[0].metric("RMSE", f"{m['rmse']:.4g}{sufijo_u}")
        k[1].metric("Error medio", f"{m['error_medio_pct']:.2f} %")
        k[2].metric("Error máximo", f"{m['error_max_pct']:.2f} %",
                    help=f"Diferencia máxima {m['dif_max']:+.4g}{sufijo_u} en x = "
                         f"{m['x_dif_max_mm']:.2f} mm")
        k[3].metric("Cobertura de la tobera", f"{m['cobertura_pct']:.0f} %")
        g1, g2 = st.columns(2)
        g1.plotly_chart(figura_superpuesta(x_modelo, y_modelo, comp, nombre, unidad),
                        theme=None, config=CONFIG, key=f"sup_{clave}")
        g2.plotly_chart(figura_error(comp, nombre, unidad, modo), theme=None, config=CONFIG,
                        key=f"err_{clave}")

    if comparaciones:
        st.download_button("Descargar tabla de comparación (.csv)",
                           cmp.tabla_comparacion(comparaciones).to_csv(index=False).encode("utf-8"),
                           file_name=f"comparacion_solidworks_{caso['nombre']}.csv",
                           mime="text/csv")


# ---------------------------------------------------------------------
# Página
# ---------------------------------------------------------------------

IMAGENES = (
    ("rs25_toberas.jpg", "Toberas de los motores RS-25 del cohete SLS. Foto: NASA/Eric Bordelon."),
    ("x2_diamantes_choque.jpg", "Diamantes de choque en el escape del X-2. Foto: NASA."),
)
EQUIPO = "Aldo Sánchez · Andrés Bernal · Ezequiel Trejo · Mateo de Lafuente · Valeria Rodríguez"

# Silueta de una tobera convergente–divergente para el encabezado
LOGO = (
    f'<svg width="26" height="26" viewBox="0 0 26 26" fill="none" stroke="{ACENTO}" '
    'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">'
    '<path d="M2 5 L9 5 Q12 5 13 10 Q14 12 16 10 L24 3"/>'
    '<path d="M2 21 L9 21 Q12 21 13 16 Q14 14 16 16 L24 23"/>'
    '<path d="M2 13 L24 13" stroke-dasharray="2 2" stroke-width="1" opacity="0.6"/></svg>'
)


# ---------------------------------------------------------------------
# Pantalla de inicio
# ---------------------------------------------------------------------

CIFRAS = (
    ("1<span>D</span>", "Flujo cuasi-unidimensional e isentrópico"),
    ("7", "Regímenes de operación clasificados"),
    ("3", "Presiones críticas p₁, p₂, p₃ y choque normal"),
    ("DXF", "Contorno listo para SolidWorks"),
)
TARJETAS = (
    ("Dimensionamiento", "Garganta y salida para expansión ideal a partir del empuje "
                         "requerido, la cámara y la altitud."),
    ("Regímenes", "Presiones críticas p₁, p₂ y p₃ y clasificación del flujo para cualquier "
                  "presión exterior."),
    ("Choque normal", "Posición del choque dentro de la divergente y estado aguas abajo "
                      "con p₀₂/p₀₁."),
    ("Empuje y C_F", "Balance de cantidad de movimiento en un volumen de control: "
                     "F = ṁVₑ + (pₑ − p_b)Aₑ."),
    ("Geometría real", "Contorno cónico con garganta redondeada y M(x), p(x), T(x) sobre "
                       "esa geometría."),
    ("Validación CFD", "Comparación contra Flow Simulation: RMSE, error máximo y "
                       "cobertura a lo largo del eje."),
)
PASOS = (
    ("Define el caso", "Gas, cámara, ambiente y empuje requerido."),
    ("Simula", "Dimensiones, regímenes, distribuciones y mapa de empuje."),
    ("Valida", "Sube el .csv de SolidWorks y mide el error teoría–CFD."),
)


@st.cache_data
def _foto_base64(nombre):
    ruta = DIR_ASSETS / nombre
    return base64.b64encode(ruta.read_bytes()).decode() if ruta.exists() else ""


def _entrar():
    st.session_state["en_programa"] = True


def pantalla_inicio():
    """Portada del proyecto. El programa se abre con el botón Comenzar."""
    estilo.ocultar_barra_lateral()
    foto = _foto_base64(IMAGENES[0][0])
    fondo = f"url(data:image/jpeg;base64,{foto})" if foto else "none"
    st.markdown(
        f'<div class="hero" style="--foto: {fondo};">'
        '<div class="antetitulo">Mecánica de Fluidos · Ingeniería Aeroespacial · UNAM</div>'
        '<div class="gran-titulo">TOBERA<span>-CD</span></div>'
        '<div class="lema">Diseño, análisis y validación de toberas convergente–divergentes.</div>'
        '<div class="texto">A partir del empuje requerido, las condiciones de cámara y la '
        'altitud, la herramienta dimensiona la tobera, predice su régimen de operación para '
        'cualquier presión exterior, localiza el choque normal y genera el contorno para '
        'validarlo en SolidWorks Flow Simulation.</div>'
        f'<div class="creditos-foto">{escape(IMAGENES[0][1])}</div></div>',
        unsafe_allow_html=True,
    )
    c1, _ = st.columns([1, 5])
    c1.button("Comenzar  →", type="primary", on_click=_entrar, width="stretch",
              key="comenzar")

    st.markdown('<div class="seccion-inicio">En números</div><div class="cifras">' +
                "".join(f'<div class="cifra"><div class="valor">{v}</div>'
                        f'<div class="etiqueta">{escape(e)}</div></div>' for v, e in CIFRAS) +
                "</div>", unsafe_allow_html=True)

    st.markdown('<div class="seccion-inicio">Qué hace</div><div class="tarjetas">' +
                "".join(f'<div class="tarjeta"><div class="num">{i:02d}</div>'
                        f'<div class="nombre">{escape(n)}</div>'
                        f'<div class="desc">{escape(d)}</div></div>'
                        for i, (n, d) in enumerate(TARJETAS, 1)) +
                "</div>", unsafe_allow_html=True)

    st.markdown('<div class="seccion-inicio">Modelo físico</div>', unsafe_allow_html=True)
    e1, e2, e3 = st.columns(3)
    with e1:
        st.latex(r"\frac{A}{A^*}=\frac{1}{M}\left[\frac{2}{\gamma+1}\left(1+"
                 r"\frac{\gamma-1}{2}M^2\right)\right]^{\frac{\gamma+1}{2(\gamma-1)}}")
        st.caption("Relación área–Mach (flujo isentrópico)")
    with e2:
        st.latex(r"M_2^2=\frac{1+\frac{\gamma-1}{2}M_1^2}{\gamma M_1^2-\frac{\gamma-1}{2}}")
        st.caption("Choque normal")
    with e3:
        st.latex(r"F=\dot m\,V_e+(p_e-p_b)\,A_e")
        st.caption("Empuje por volumen de control")

    st.markdown('<div class="seccion-inicio">Cómo se usa</div><div class="pasos">' +
                "".join(f'<div class="paso"><div class="nombre">{i}. {escape(n)}</div>'
                        f'<div class="desc">{escape(d)}</div></div>'
                        for i, (n, d) in enumerate(PASOS, 1)) +
                "</div>", unsafe_allow_html=True)

    st.markdown(f'<div class="pie-inicio"><span>{EQUIPO}</span>'
                '<span>ENES Juriquilla · UNAM · Fotos: NASA (dominio público)</span></div>',
                unsafe_allow_html=True)


# ---------------------------------------------------------------------
# Programa
# ---------------------------------------------------------------------

def encabezado():
    """Barra de título compacta con los datos principales del caso que se edita."""
    ss = st.session_state
    chips = [("Caso", ss.get("f_nombre", "–")), ("γ", f"{ss.get('f_gamma', 0):.3f}"),
             ("p₀", f"{ss.get('f_p0_MPa', 0):.3g} MPa"), ("T₀", f"{ss.get('f_T0_K', 0):.0f} K"),
             ("F", f"{ss.get('f_F_N', 0):.4g} N")]
    html_chips = "".join(f'<span class="chip">{escape(k)} <b>{escape(str(v))}</b></span>'
                         for k, v in chips)
    st.markdown(
        f'<div class="encabezado"><div class="marca"><div class="logo">{LOGO}</div><div>'
        '<div class="titulo">TOBERA<span>-CD</span></div>'
        '<div class="subtitulo">Diseño, análisis y validación de toberas '
        'convergente–divergentes</div></div></div>'
        f'<div class="chips">{html_chips}</div></div>',
        unsafe_allow_html=True,
    )


def _volver_al_inicio():
    # Streamlit borra el estado de los widgets que no se dibujan; se guarda una
    # copia del formulario para recuperarlo al volver al programa.
    ss = st.session_state
    ss["_formulario_guardado"] = {k: v for k, v in ss.items()
                                  if k.startswith(("f_", "g_")) or k == "sel_caso"}
    ss["en_programa"] = False


def barra_lateral():
    """Información del proyecto, datos necesarios y fotografías de referencia."""
    with st.sidebar:
        st.button("←  Volver al inicio", on_click=_volver_al_inicio, width="stretch")
        st.markdown("### Proyecto")
        st.markdown("Proyecto final de **Mecánica de Fluidos** · Ingeniería Aeroespacial, "
                    "ENES Juriquilla, UNAM.")
        st.markdown("### Cómo se usa")
        st.markdown(
            "1. **Caso**: datos del gas, la cámara, el ambiente y el empuje.\n"
            "2. **Resultados**: dimensiones, regímenes, p(x), M(x) y empuje.\n"
            "3. **Validación**: sube el .csv de SolidWorks Flow Simulation."
        )
        st.markdown("### Modelo")
        st.markdown("Flujo cuasi-1D, permanente y adiabático de un gas ideal calóricamente "
                    "perfecto; isentrópico salvo en el choque normal.")
        st.markdown("### Referencias")
        for archivo, pie in IMAGENES:
            ruta = DIR_ASSETS / archivo
            if ruta.exists():
                st.image(str(ruta), caption=pie, width="stretch")
        st.markdown("### Equipo")
        st.caption(EQUIPO)


def main():
    if not st.session_state.get("en_programa"):
        pantalla_inicio()
        return

    st.session_state.update(st.session_state.pop("_formulario_guardado", {}))
    pendiente = st.session_state.pop("_sel_pendiente", None)
    if pendiente:
        st.session_state["sel_caso"] = pendiente
    inicializar()

    barra_lateral()
    encabezado()
    tab_caso, tab_res, tab_val = st.tabs(["Caso", "Resultados", "Validación SolidWorks"])
    resultado = st.session_state.get("resultado")
    with tab_caso:
        pestana_caso()
    with tab_res:
        pestana_resultados(resultado)
    with tab_val:
        pestana_validacion(resultado)


main()
