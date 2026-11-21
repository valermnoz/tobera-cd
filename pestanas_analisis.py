"""
pestanas_analisis.py — Pestañas de análisis de la interfaz (después de simular).

  pestana_explorador()   Explorador de choque: p_b con un deslizador y animación
  pestana_dimensional()  Análisis dimensional (objetivo 5): C_F, semejanza, Re*, γ
  pestana_comparar()     Dos casos lado a lado

Igual que app.py, aquí solo hay interfaz: los cálculos están en tobera.py y
analisis_dimensional.py, y las figuras en graficas_gui.py.
"""

import copy
import math
from pathlib import Path

import pandas as pd
import streamlit as st

import analisis_dimensional as ad
import configuracion as cfg
import estilo
from geometria import area
from graficas_gui import (CONFIG, figura_animacion_choque, figura_campo, figura_cf,
                          figura_comparar_mach, figura_comparar_perfiles, figura_distribucion)
from main import NOMBRES_REGIMEN, completar_caso, correr
from tobera import coeficiente_empuje, distribucion, empuje, estado_salida


def _grafica(fig, columna=st, key=None):
    columna.plotly_chart(fig, theme=None, config=CONFIG, key=key)


def _sin_resultado():
    st.info("Primero simula un caso en la pestaña Caso.")


def _potencia_diez(valor):
    """1.446e6 -> '1.45 × 10⁶' (para el número de Reynolds)."""
    exponente = int(math.floor(math.log10(valor)))
    supers = str.maketrans("-0123456789", "⁻⁰¹²³⁴⁵⁶⁷⁸⁹")
    return f"{valor / 10**exponente:.2f} × 10{str(exponente).translate(supers)}"


# ---------------------------------------------------------------------
# Ecuaciones del modelo
# ---------------------------------------------------------------------

# (grupo, [(descripción, LaTeX)]) — las mismas relaciones que usan flujo.py,
# tobera.py y analisis_dimensional.py
ECUACIONES = (
    ("Flujo isentrópico", (
        ("Temperatura de estancamiento", r"\frac{T_0}{T} = 1 + \frac{\gamma - 1}{2} M^2"),
        ("Presión de estancamiento",
         r"\frac{p_0}{p} = \left(\frac{T_0}{T}\right)^{\frac{\gamma}{\gamma - 1}}"),
        ("Densidad de estancamiento",
         r"\frac{\rho_0}{\rho} = \left(\frac{T_0}{T}\right)^{\frac{1}{\gamma - 1}}"),
        ("Velocidad del sonido", r"a = \sqrt{\gamma R T}"),
        ("Relación área–Mach",
         r"\frac{A}{A^*} = \frac{1}{M}\left[\frac{2}{\gamma + 1}\left(1 + \frac{\gamma - 1}{2}"
         r"M^2\right)\right]^{\frac{\gamma + 1}{2(\gamma - 1)}}"),
        ("Gasto estrangulado",
         r"\dot m = \frac{p_0 A^*}{\sqrt{T_0}}\sqrt{\frac{\gamma}{R}}\left(\frac{2}{\gamma + 1}"
         r"\right)^{\frac{\gamma + 1}{2(\gamma - 1)}}"),
    )),
    ("Choque normal", (
        ("Mach aguas abajo",
         r"M_2^2 = \frac{1 + \frac{\gamma - 1}{2} M_1^2}{\gamma M_1^2 - \frac{\gamma - 1}{2}}"),
        ("Salto de presión", r"\frac{p_2}{p_1} = 1 + \frac{2\gamma}{\gamma + 1}\left(M_1^2 - 1\right)"),
        ("Pérdida de presión total",
         r"\frac{p_{02}}{p_{01}} = \left[\frac{(\gamma + 1) M_1^2}{(\gamma - 1) M_1^2 + 2}"
         r"\right]^{\frac{\gamma}{\gamma - 1}}\left[\frac{\gamma + 1}{2\gamma M_1^2 - (\gamma - 1)}"
         r"\right]^{\frac{1}{\gamma - 1}}"),
        ("Posición del choque", r"p_{01} A_1^* = p_{02} A_2^*"),
    )),
    ("Empuje y semejanza", (
        ("Empuje (volumen de control)", r"F = \dot m V_e + \left(p_e - p_b\right) A_e"),
        ("Coeficiente de empuje",
         r"C_F = \frac{F}{p_0 A^*} = f\left(\gamma,\ \frac{A_e}{A^*},\ \frac{p_b}{p_0}\right)"),
        ("Factor de divergencia cónica", r"\lambda = \frac{1 + \cos\alpha_d}{2}"),
        ("Reynolds en la garganta", r"Re^* = \frac{\rho^* V^* D^*}{\mu^*}"),
        ("Viscosidad (Sutherland)",
         r"\mu = \mu_{ref}\left(\frac{T}{T_{ref}}\right)^{3/2}\frac{T_{ref} + S}{T + S}"),
        ("Atmósfera estándar (z < 11 km)",
         r"p_a = 101\,325\left(1 - 2.25577\times10^{-5}\,z\right)^{5.25588}"),
    )),
)


def mostrar_ecuaciones():
    """Las ecuaciones del modelo en tres columnas, una por grupo."""
    for col, (grupo, ecuaciones) in zip(st.columns(len(ECUACIONES)), ECUACIONES):
        with col:
            st.markdown(f'<div class="grupo">{grupo}</div>', unsafe_allow_html=True)
            for descripcion, latex in ecuaciones:
                st.caption(descripcion)
                st.latex(latex)


# ---------------------------------------------------------------------
# Explorador de choque
# ---------------------------------------------------------------------

def pestana_explorador(resultado):
    if resultado is None:
        return _sin_resultado()
    caso, res = resultado["caso"], resultado["res"]
    p0, T0 = caso["camara"]["p0_Pa"], caso["camara"]["T0_K"]
    g, R = caso["gas"]["gamma"], caso["gas"]["R"]
    d, crit = res["diseno"], res["criticas"]
    A = area(res["r"])

    estilo.titulo_seccion("01", "Presión exterior en vivo",
                          "Mueve $p_b$ y la solución se recalcula al instante: régimen, "
                          "posición del choque, empuje y campo de Mach.")
    minimo = round(0.3 * crit["p3"] / 1e3, 1)
    maximo = round(0.995 * p0 / 1e3, 1)
    inicial = min(max(round((crit["p1"] + crit["p2"]) / 2e3, 1), minimo), maximo)
    pb = 1e3 * st.slider("Presión exterior $p_b$ [kPa]", minimo, maximo, inicial, step=0.5,
                         key=f"explorador_pb_{resultado['id']}")

    s = estado_salida(pb, p0, T0, d["At"], d["Ae_At"], g, R)
    F = empuje(s["m"], s["Ve"], s["pe"], pb, d["Ae"])
    perfil = distribucion(res["x"], A, pb, p0, T0, g)
    perfil["pb"] = pb
    reg = s["regimen"]
    # Factor de divergencia de una tobera cónica: λ = (1 + cos αd)/2
    alfa = math.radians(caso["geometria"]["angulo_divergente_deg"])
    lam = (1 + math.cos(alfa)) / 2

    st.markdown(estilo.insignia(reg, NOMBRES_REGIMEN[reg].upper()), unsafe_allow_html=True)
    x_ch = "—" if perfil["x_choque"] is None else f"{perfil['x_choque']*1e3:.2f}"
    estilo.telemetria([
        ("Mach de salida M<sub>e</sub>", f"{s['Me']:.3f}", ""),
        ("Presión de salida p<sub>e</sub>", f"{s['pe']/1e3:.1f}", " kPa"),
        ("Gasto másico ṁ", f"{s['m']:.4f}", " kg/s"),
        ("Empuje ideal F", f"{F:.2f}", " N"),
        ("Empuje con λ", f"{lam * s['m'] * s['Ve'] + (s['pe'] - pb) * d['Ae']:.2f}", " N"),
        ("C<sub>F</sub>", f"{coeficiente_empuje(F, p0, d['At']):.4f}", ""),
        ("Choque x<sub>s</sub>", x_ch, " mm" if perfil["x_choque"] is not None else ""),
    ])
    alfa_g = caso["geometria"]["angulo_divergente_deg"]
    st.caption("Empuje con λ: corrige el término de cantidad de movimiento por la divergencia "
               rf"cónica, $F = \lambda\,\dot m V_e + (p_e - p_b)A_e$ con "
               rf"$\lambda = \frac{{1 + \cos {alfa_g:g}^\circ}}{{2}} = {lam:.4f}$.")
    if reg in ("sobreexpandida", "choque_en_salida") and s["pe"] < 0.4 * pb:
        st.warning(f"$p_e/p_b = {s['pe']/pb:.2f} < 0.4$: según el criterio de Summerfield es "
                   "probable que la capa límite se desprenda dentro de la divergente. El CFD "
                   "mostraría separación y un choque oblicuo en lugar de un chorro limpio.")
    if reg == "choque_interno" and s["choque"] is not None:
        ch = s["choque"]
        st.caption(rf"Choque normal: $M_1 = {ch['M1']:.3f} \rightarrow M_2 = {ch['M2']:.3f}$, "
                   rf"$p_{{02}}/p_{{01}} = {ch['p02_p01']:.4f}$ (pérdida de presión total "
                   f"{100 * (1 - ch['p02_p01']):.1f} %).")

    c1, c2 = st.columns(2)
    _grafica(figura_campo(res["x"], res["r"], perfil, "M"), c1, key="expl_campo")
    fig_p = figura_distribucion(res["x"], [perfil], "p", crit)
    fig_p.update_layout(showlegend=False, margin=dict(r=24))  # una sola curva
    _grafica(fig_p, c2, key="expl_p")

    estilo.titulo_seccion("02", "Animación del choque",
                          "Al bajar $p_b$ desde $p_1$ el choque nace en la garganta, recorre "
                          "la divergente y sale por el plano de salida ($p_b = p_2$). Pulsa ▶.")
    _grafica(_animacion(resultado["id"], res, p0, T0, g), key="expl_anim")


def _animacion(id_resultado, res, p0, T0, g):
    """La animación tarda ~0.5 s; se guarda por resultado para no rehacerla."""
    clave = f"_animacion_{id_resultado}"
    if clave not in st.session_state:
        st.session_state[clave] = figura_animacion_choque(res["x"], res["r"], area(res["r"]),
                                                          p0, T0, g, res["criticas"])
    return st.session_state[clave]


# ---------------------------------------------------------------------
# Análisis dimensional
# ---------------------------------------------------------------------

@st.cache_data(show_spinner=False)
def _curvas_area(Ae_At, g):
    relaciones = sorted({1.5, 3.0, 5.0, 10.0, round(Ae_At, 4)})
    return ad.curvas_cf(relaciones, g)


@st.cache_data(show_spinner=False)
def _curvas_gamma(Ae_At, g):
    return ad.efecto_gamma(Ae_At, sorted({1.4, 1.3, 1.2, 1.13, round(g, 4)}, reverse=True))


def pestana_dimensional(resultado):
    if resultado is None:
        return _sin_resultado()
    caso, res = resultado["caso"], resultado["res"]
    p0, T0 = caso["camara"]["p0_Pa"], caso["camara"]["T0_K"]
    g, R = caso["gas"]["gamma"], caso["gas"]["R"]
    d = res["diseno"]
    pa_p0 = caso["pa_Pa"] / p0
    re = ad.reynolds_garganta(p0, T0, d["Dt"], g, R)

    estilo.titulo_seccion("01", "Teorema Π de Buckingham",
                          "Siete variables con tres dimensiones (M, L, T) dejan cuatro grupos "
                          "adimensionales: el empuje adimensional depende solo de tres.")
    c1, c2 = st.columns(2)
    with c1:
        st.latex(r"F = f\left(p_0,\; R T_0,\; A^*,\; A_e,\; p_b,\; \gamma\right)")
    with c2:
        st.latex(r"C_F = \frac{F}{p_0 A^*} = f\left(\gamma,\; \frac{A_e}{A^*},\; "
                 r"\frac{p_b}{p_0}\right)")
    estilo.telemetria([
        ("γ", f"{g:.3f}", ""),
        ("A<sub>e</sub>/A<sup>*</sup>", f"{d['Ae_At']:.4f}", ""),
        ("p<sub>a</sub>/p<sub>0</sub> de diseño", f"{pa_p0:.4f}", ""),
        ("C<sub>F</sub> de diseño", f"{d['CF']:.4f}", ""),
        ("Re<sup>*</sup> en la garganta", _potencia_diez(re["Re"]), ""),
    ])
    regimen_capa = "turbulenta" if re["Re"] > 5e5 else "laminar o de transición"
    st.caption(rf"$Re^* = \dfrac{{\rho^* V^* D^*}}{{\mu^*}}$ con "
               rf"$\rho^* = {re['rho']:.3f}$ kg/m³, $V^* = {re['V']:.1f}$ m/s y "
               rf"$\mu^* = {re['mu']*1e5:.4f}\times10^{{-5}}$ Pa·s (Sutherland, aire). "
               f"Capa límite {regimen_capa}: la "
               "viscosidad solo actúa en una capa delgada, por eso el modelo ideal funciona y "
               "el coeficiente de descarga real queda cerca de 0.98–0.99.")

    estilo.titulo_seccion("02", "C<sub>F</sub> contra presión exterior para varias "
                                "A<sub>e</sub>/A<sup>*</sup>",
                          "Curvas universales para $\\gamma$ fijo: sirven para cualquier tamaño, "
                          "temperatura o presión de cámara.")
    _grafica(figura_cf(_curvas_area(d["Ae_At"], g), f"C_F = f(Aₑ/A*, p_b/p₀)  ·  γ = {g:.3f}",
                       lambda ar: f"Aₑ/A* = {ar:g}", resaltar=round(d["Ae_At"], 4),
                       pb_p0_diseno=pa_p0), key="dim_area")

    estilo.titulo_seccion("03", "Prueba de semejanza",
                          r"Cinco toberas con los mismos grupos $\Pi$ "
                          r"$\left(\gamma,\ A_e/A^*,\ p_b/p_0\right)$ pero distinto tamaño, "
                          r"$T_0$ y $p_0$: el empuje cambia, $C_F$ no.")
    filas = ad.prueba_semejanza(d["Ae_At"], pa_p0, g, R)
    tabla = pd.DataFrame([{
        "Tobera": f["nombre"], "p₀ [MPa]": f"{f['p0_Pa']/1e6:.2f}", "T₀ [K]": f"{f['T0_K']:.0f}",
        "D* [mm]": f"{f['Dt_mm']:.2f}", "ṁ [kg/s]": f"{f['m_kg_s']:.4f}",
        "F [N]": f"{f['F_N']:.2f}", "C_F": f"{f['CF']:.6f}",
    } for f in filas])
    _tabla(tabla, derecha=list(tabla.columns[1:]))
    dispersion = max(f["CF"] for f in filas) - min(f["CF"] for f in filas)
    st.caption(f"Diferencia máxima de $C_F$ entre las cinco toberas: {dispersion:.1e} (error "
               "numérico). Por eso se puede validar con aire frío en un modelo a escala.")

    estilo.titulo_seccion("04", "Efecto de γ: semejanza incompleta",
                          r"El aire ($\gamma = 1.4$) y los gases de combustión "
                          r"($\gamma \approx 1.2$) no comparten el grupo $\gamma$, así que sus "
                          r"$C_F$ no coinciden.")
    curvas_g = _curvas_gamma(d["Ae_At"], g)
    _grafica(figura_cf(curvas_g, f"C_F para Aₑ/A* = {d['Ae_At']:.3f} y distintos γ",
                       lambda gg: f"γ = {gg:g}", resaltar=round(g, 4), pb_p0_diseno=pa_p0),
             key="dim_gamma")
    cf_14 = ad.cf_adimensional(d["Ae_At"], pa_p0, 1.4)[0]
    cf_12 = ad.cf_adimensional(d["Ae_At"], pa_p0, 1.2)[0]
    st.caption(rf"Con la misma tobera y $p_b/p_0 = {pa_p0:.4f}$: $C_F = {cf_14:.4f}$ con "
               rf"$\gamma = 1.4$ y $C_F = {cf_12:.4f}$ con $\gamma = 1.2$ "
               f"({100 * (cf_12 - cf_14) / cf_14:+.1f} %). Una prueba "
               "con aire no reproduce exactamente el empuje del motor real.")


def _tabla(df, derecha=()):
    estilo.mostrar_tabla(df, derecha=derecha)


# ---------------------------------------------------------------------
# Comparar casos
# ---------------------------------------------------------------------

ACTUAL = "(resultado actual)"


@st.cache_data(show_spinner=False)
def _correr_json(texto):
    """Corre un caso sin guardar nada en disco (el texto del .json es la clave de caché)."""
    caso = completar_caso(cfg.leer_json(texto))
    res = correr(caso)
    return caso, {k: res[k] for k in ("diseno", "criticas", "geometria", "x", "r",
                                      "distribuciones")}


def _cargar(opcion, resultado):
    if opcion == ACTUAL:
        return resultado["caso"], resultado["res"]
    return _correr_json(open(opcion, encoding="utf-8").read())


def _mach_diseno(caso, res):
    """M(x) en la presión de diseño (la tobera adaptada)."""
    A = area(res["r"])
    return distribucion(res["x"], A, caso["pa_Pa"], caso["camara"]["p0_Pa"],
                        caso["camara"]["T0_K"], caso["gas"]["gamma"])["M"]


def pestana_comparar(resultado):
    opciones = ([ACTUAL] if resultado else []) + [str(c) for c in cfg.listar_casos()]
    if len(opciones) < 2:
        st.info("Se necesitan al menos dos casos (en casos/ o el resultado actual).")
        return
    estilo.titulo_seccion("01", "Casos a comparar",
                          "Los casos de casos/ se corren aquí sin escribir archivos.")
    c1, c2 = st.columns(2)
    # Por defecto B es un caso distinto del resultado actual
    nombre_actual = resultado["caso"]["nombre"] if resultado else None
    i_b = next((i for i, o in enumerate(opciones)
                if o != ACTUAL and Path(o).stem != nombre_actual), min(1, len(opciones) - 1))
    op_a = c1.selectbox("Caso A", opciones, index=0, key="comp_a")
    op_b = c2.selectbox("Caso B", opciones, index=i_b, key="comp_b")
    try:
        caso_a, res_a = _cargar(op_a, resultado)
        caso_b, res_b = _cargar(op_b, resultado)
    except (OSError, ValueError, ArithmeticError) as e:
        st.error(f"No se pudo correr el caso: {e}")
        return
    caso_a, caso_b = copy.deepcopy(caso_a), copy.deepcopy(caso_b)
    na, nb = caso_a["nombre"], caso_b["nombre"]

    da, db = res_a["diseno"], res_b["diseno"]
    filas = [
        ("γ", caso_a["gas"]["gamma"], caso_b["gas"]["gamma"], "–", ".3f"),
        ("p₀", caso_a["camara"]["p0_Pa"] / 1e6, caso_b["camara"]["p0_Pa"] / 1e6, "MPa", ".3f"),
        ("T₀", caso_a["camara"]["T0_K"], caso_b["camara"]["T0_K"], "K", ".0f"),
        ("Empuje de diseño", caso_a["empuje_requerido_N"], caso_b["empuje_requerido_N"], "N",
         ".1f"),
        ("Mach de salida", da["Me"], db["Me"], "–", ".3f"),
        ("Aₑ/A*", da["Ae_At"], db["Ae_At"], "–", ".3f"),
        ("Velocidad de salida", da["Ve"], db["Ve"], "m/s", ".1f"),
        ("Gasto másico", da["m"], db["m"], "kg/s", ".4f"),
        ("D*", da["Dt"] * 1e3, db["Dt"] * 1e3, "mm", ".2f"),
        ("Dₑ", da["De"] * 1e3, db["De"] * 1e3, "mm", ".2f"),
        ("Longitud total", res_a["geometria"]["L_total"] * 1e3,
         res_b["geometria"]["L_total"] * 1e3, "mm", ".2f"),
        ("C_F", da["CF"], db["CF"], "–", ".4f"),
        ("Impulso específico Ve/g₀", da["Ve"] / 9.80665, db["Ve"] / 9.80665, "s", ".1f"),
    ]
    # Columnas con prefijo A/B: así no chocan si los dos casos se llaman igual
    col_a, col_b = f"A · {na}", f"B · {nb}"
    tabla = pd.DataFrame([{
        "Magnitud": n, col_a: format(a, f), col_b: format(b, f), "Unidad": u,
        "B − A": "–" if a == 0 else f"{100 * (b - a) / a:+.1f} %",
    } for n, a, b, u, f in filas])
    estilo.titulo_seccion("02", "Hoja de comparación")
    _tabla(tabla, derecha=list(tabla.columns[1:3]) + ["B − A"])

    estilo.titulo_seccion("03", "Geometría y flujo")
    g1, g2 = st.columns(2)
    _grafica(figura_comparar_perfiles([(f"A · {na}", res_a["x"], res_a["r"]),
                                       (f"B · {nb}", res_b["x"], res_b["r"])]), g1,
             key="comp_perfil")
    _grafica(figura_comparar_mach([
        (f"A · {na}", res_a["x"], res_a["r"], _mach_diseno(caso_a, res_a)),
        (f"B · {nb}", res_b["x"], res_b["r"], _mach_diseno(caso_b, res_b)),
    ]), g2, key="comp_mach")

    estilo.titulo_seccion("04", "Coeficiente de empuje",
                          "$C_F$ contra $p_b/p_0$ de cada tobera: compara su desempeño fuera de "
                          "diseño sin importar el tamaño.")
    curvas = {}
    for etiqueta, caso, d in ((f"A · {na}", caso_a, da), (f"B · {nb}", caso_b, db)):
        curvas[etiqueta] = ad.curvas_cf([d["Ae_At"]], caso["gas"]["gamma"])[d["Ae_At"]]
    _grafica(_figura_cf_casos(curvas), key="comp_cf")


def _figura_cf_casos(curvas):
    """figura_cf con etiquetas de texto (los parámetros son los nombres de los casos)."""
    nombres = list(curvas)
    indice = {i: curvas[n] for i, n in enumerate(nombres)}
    return figura_cf(indice, "C_F contra presión exterior", lambda i: nombres[int(i)],
                     resaltar=0, sufijo="")
