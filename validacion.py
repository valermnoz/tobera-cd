"""
validacion.py — Pestaña "Validación SolidWorks" de la interfaz.

Compara el modelo 1D con el CSV de Flow Simulation y lo muestra de varias
formas para que el error se entienda de un vistazo:

  · veredicto y métricas (error medio, máximo, RMSE, cobertura)
  · empalme animado: las dos curvas encimadas, el hueco entre ellas sombreado
    y un cursor que recorre la tobera con el error en cada punto
  · mapa de error: la tobera pintada con |error| para ver DÓNDE se separan
  · paridad: SolidWorks contra código, con la diagonal y una franja de ±5 %
  · magnitudes globales (ṁ, Me, pe, F) capturadas a mano de los goals

Los cálculos están en comparacion.py y las figuras en graficas_gui.py.
"""

import streamlit as st

import comparacion as cmp
import estilo
from graficas_gui import (CONFIG, figura_empalme, figura_error, figura_globales,
                          figura_mapa_error, figura_paridad)
from main import NOMBRES_REGIMEN

NINGUNA = "(ninguna)"


def _indice(opciones, valor):
    return opciones.index(valor) if valor in opciones else 0


def _grafica(fig, columna=st, key=None):
    columna.plotly_chart(fig, theme=None, config=CONFIG, key=key)


def _indice_ejemplo(res, caso):
    """Para los datos de ejemplo: la presión con choque interno si la hay (es la más ilustrativa)."""
    analisis = res["analisis"]
    con_choque = next((i for i, a in enumerate(analisis) if a["regimen"] == "choque_interno"), None)
    if con_choque is not None:
        return con_choque
    return next((i for i, a in enumerate(analisis) if a["pb_Pa"] == caso["pa_Pa"]), 0)


def _leer_datos(resultado):
    """Devuelve (bytes del CSV, nombre, es_ejemplo) o None si aún no hay datos."""
    archivo = st.file_uploader("Resultados de SolidWorks (.csv)", type=["csv", "txt"],
                               key="subir_csv")
    if archivo is not None:
        st.session_state.pop("val_ejemplo", None)
        return archivo.getvalue(), f"{archivo.name}_{archivo.size}", False

    if st.session_state.get("val_ejemplo"):
        if st.button("Quitar datos de ejemplo"):
            st.session_state.pop("val_ejemplo")
            st.rerun()
    elif st.button("Probar con datos de ejemplo"):
        st.session_state["val_ejemplo"] = True
        st.rerun()
    if not st.session_state.get("val_ejemplo"):
        st.caption("¿Aún no tienen el CFD? Los datos de ejemplo imitan un resultado de Flow "
                   "Simulation para ver cómo se presenta la comparación.")
        return None

    res, caso = resultado["res"], resultado["caso"]
    d = res["distribuciones"][_indice_ejemplo(res, caso)]
    datos = cmp.datos_ejemplo(res["x"] * 1e3, d["p"], d["M"])
    return datos, f"ejemplo_{resultado['id']}", True


def pestana_validacion(resultado):
    if resultado is None:
        st.info("Primero simula un caso en la pestaña Caso. La comparación usa sus resultados.")
        return
    caso, res = resultado["caso"], resultado["res"]
    geo = res["geometria"]

    estilo.titulo_seccion("01", "Datos de SolidWorks")
    st.markdown(
        "1. Descarga el contorno y modélalo en SolidWorks (ver README).\n"
        "2. Corre Flow Simulation y exporta los resultados a lo largo del eje como .csv.\n"
        "3. Sube el .csv aquí."
    )
    ruta_dxf = resultado["salida"] / "contorno.dxf"
    if ruta_dxf.exists():
        st.download_button("Descargar contorno.dxf", ruta_dxf.read_bytes(),
                           file_name="contorno.dxf", mime="application/dxf",
                           key=f"val_dxf_{resultado['id']}")

    leido = _leer_datos(resultado)
    if leido is None:
        return
    datos, sufijo, ejemplo = leido
    if ejemplo:
        st.warning("**Datos de ejemplo:** se fabricaron a partir del modelo 1D (choque "
                   "suavizado, Mach 1.5 % menor en la divergente y ruido). **No son resultados "
                   "de SolidWorks**; sirven solo para ver la presentación.")
    try:
        tabla = cmp.leer_csv_solidworks(datos)
    except ValueError as e:
        st.error(f"No se pudo leer el CSV: {e}")
        return

    # --- Columnas y alineación -----------------------------------------
    columnas = list(tabla.columns)
    auto = cmp.detectar_columnas(columnas)
    opciones_y = [NINGUNA] + columnas
    analisis = res["analisis"]
    etiquetas = [f"{a['pb_Pa']/1e3:.1f} kPa · {NOMBRES_REGIMEN[a['regimen']]}" for a in analisis]
    i_inicial = (_indice_ejemplo(res, caso) if ejemplo else
                 next((i for i, a in enumerate(analisis) if a["pb_Pa"] == caso["pa_Pa"]), 0))

    estilo.titulo_seccion("02", "Columnas y alineación")
    c = st.columns(4)
    col_x = c[0].selectbox("Columna de posición", columnas,
                           index=_indice(columnas, auto["x"]), key=f"cx_{sufijo}")
    col_p = c[1].selectbox("Columna de presión estática", opciones_y,
                           index=_indice(opciones_y, auto["p"] or NINGUNA), key=f"cp_{sufijo}")
    col_M = c[2].selectbox("Columna de número de Mach", opciones_y,
                           index=_indice(opciones_y, auto["M"] or NINGUNA), key=f"cM_{sufijo}")
    i_pb = c[3].selectbox("Presión exterior simulada", list(range(len(etiquetas))),
                          index=i_inicial, format_func=lambda i: etiquetas[i],
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

    if col_p == NINGUNA and col_M == NINGUNA:
        st.warning("Elige al menos la columna de presión o la de Mach.")
        return

    d = res["distribuciones"][i_pb]
    x_modelo = res["x"] * 1e3
    variables = []
    if col_p != NINGUNA:
        variables.append(("Presión estática", "kPa", "p", col_p, cmp.A_PA[u_p] / 1e3,
                          d["p"] / 1e3))
    if col_M != NINGUNA:
        variables.append(("Número de Mach", "–", "M", col_M, 1.0, d["M"]))
    x_sw = cmp.alinear_x(tabla[col_x].to_numpy() * cmp.A_MM[u_x], geo, origen, invertir,
                         desplazamiento)

    # --- Concordancia por variable -------------------------------------
    estilo.titulo_seccion("03", "Concordancia a lo largo de la tobera")
    st.latex(r"\varepsilon(x) = \frac{y_{\text{código}}(x) - y_{\text{SW}}(x)}"
             r"{\left|\, y_{\text{SW}}(x) \,\right|} \times 100\,\%")
    st.caption("SolidWorks es la referencia. El CSV se interpola en las secciones del modelo "
               "sin extrapolar.")
    if d["x_choque"] is not None:
        st.caption(f"Con esta presión hay un choque normal en $x = {d['x_choque']*1e3:.2f}$ mm. "
                   "El CFD lo reparte en varias celdas, así que el error local ahí es grande "
                   "aunque el resto de la tobera coincida.")

    comparaciones = {}
    for nombre, unidad, clave, col, factor, y_modelo in variables:
        try:
            comp = cmp.comparar(x_modelo, y_modelo, x_sw, tabla[col].to_numpy() * factor)
        except ValueError as e:
            st.error(str(e))
            continue
        comparaciones["p_kPa" if clave == "p" else "M"] = comp
        _bloque_variable(nombre, unidad, clave, comp, x_modelo, res["r"] * 1e3)

    # --- Magnitudes globales -------------------------------------------
    _magnitudes_globales(analisis[i_pb], resultado["id"])

    if comparaciones:
        estilo.titulo_seccion("05", "Descargas")
        st.download_button("Descargar tabla de comparación (.csv)",
                           cmp.tabla_comparacion(comparaciones).to_csv(index=False).encode("utf-8"),
                           file_name=f"comparacion_solidworks_{caso['nombre']}.csv",
                           mime="text/csv")


def _bloque_variable(nombre, unidad, clave, comp, x_modelo, r_modelo):
    m = comp["metricas"]
    sufijo_u = "" if unidad == "–" else f" {unidad}"
    nivel, texto = cmp.veredicto(m["error_medio_pct"])
    st.markdown(f"#### {nombre}")
    st.markdown(estilo.insignia(f"veredicto-{nivel}", texto), unsafe_allow_html=True)
    estilo.telemetria([
        ("Error medio", f"{m['error_medio_pct']:.2f}", " %"),
        ("Error máximo", f"{m['error_max_pct']:.2f}", " %"),
        ("En x =", f"{m['x_dif_max_mm']:.2f}", " mm"),
        ("RMSE", f"{m['rmse']:.4g}", sufijo_u),
        ("Cobertura", f"{m['cobertura_pct']:.0f}", " %"),
    ])
    vistas = st.tabs(["Empalme animado", "Dónde está el error", "Paridad", "Error contra x"])
    with vistas[0]:
        st.caption("El área roja entre las curvas es el error. Pulsa ▶ para que el cursor "
                   "recorra la tobera y muestre los dos valores en cada sección.")
        _grafica(figura_empalme(comp, nombre, unidad), key=f"emp_{clave}")
    with vistas[1]:
        st.caption("La tobera pintada con el error de cada sección: azul oscuro donde "
                   "coinciden, rojo donde más se separan.")
        _grafica(figura_mapa_error(x_modelo, r_modelo, comp, nombre), key=f"mapa_{clave}")
    with vistas[2]:
        st.caption("Cada punto es una sección. Si coincidieran exactamente, todos caerían sobre "
                   "la diagonal; la franja azul es ±5 %.")
        _grafica(figura_paridad(comp, nombre, unidad), key=f"par_{clave}")
    with vistas[3]:
        modo = st.radio("Error a graficar", ["porcentual", "absoluto"], horizontal=True,
                        format_func=str.capitalize, key=f"modo_{clave}")
        _grafica(figura_error(comp, nombre, unidad, modo), key=f"err_{clave}")


def _magnitudes_globales(a, id_resultado):
    estilo.titulo_seccion("04", "Magnitudes globales de Flow Simulation")
    st.caption("Escribe los goals que reporta Flow Simulation para esta presión exterior "
               "(deja en 0 los que no tengas). Se comparan con el modelo 1D.")
    c = st.columns(4)
    sw = {
        "Gasto másico ṁ": c[0].number_input("ṁ de SolidWorks [kg/s]", min_value=0.0,
                                            format="%.5f", step=0.001,
                                            key=f"g_m_{id_resultado}"),
        "Mach de salida Mₑ": c[1].number_input("Mₑ de SolidWorks", min_value=0.0,
                                                format="%.4f", step=0.01,
                                                key=f"g_M_{id_resultado}"),
        "Presión de salida pₑ": c[2].number_input("pₑ de SolidWorks [kPa]", min_value=0.0,
                                                   format="%.2f", step=1.0,
                                                   key=f"g_p_{id_resultado}"),
        "Empuje F": c[3].number_input("F de SolidWorks [N]", min_value=0.0, format="%.3f",
                                      step=1.0, key=f"g_F_{id_resultado}"),
    }
    modelo = {"Gasto másico ṁ": a["m_kg_s"], "Mach de salida Mₑ": a["Me"],
              "Presión de salida pₑ": a["pe_Pa"] / 1e3, "Empuje F": a["F_N"]}
    st.caption(f"Modelo 1D: ṁ = {a['m_kg_s']:.5f} kg/s · Mₑ = {a['Me']:.4f} · "
               f"pₑ = {a['pe_Pa']/1e3:.2f} kPa · F = {a['F_N']:.3f} N")
    filas = cmp.errores_globales(modelo, sw)
    if filas:
        _grafica(figura_globales(filas), key="globales")
