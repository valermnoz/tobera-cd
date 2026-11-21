"""
analisis_dimensional.py — Objetivo 5: análisis dimensional y semejanza (Unidad 4).

Por Buckingham, el empuje F = f(p0, R·T0, A*, Ae, pb, γ) se reduce a

    C_F = F / (p0·A*) = f(γ, Ae/A*, pb/p0)

Este módulo calcula esa función y lo que se deduce de ella:

  cf_adimensional():   C_F para una tobera dada por sus grupos Π
  curvas_cf():         C_F contra pb/p0 para varias Ae/A*
  efecto_gamma():      C_F contra pb/p0 para varios γ (aire contra gases de combustión)
  prueba_semejanza():  toberas de distinto tamaño, T0 y p0 con los mismos grupos Π
  reynolds_garganta(): Re* en la garganta (régimen de la capa límite)
"""

import numpy as np

from flujo import GAMMA_AIRE, R_AIRE
from tobera import coeficiente_empuje, empuje, estado_salida

# Valores de referencia arbitrarios: C_F no depende de ellos (eso es lo que
# se demuestra en prueba_semejanza)
_P0, _T0, _AT = 1.0e6, 300.0, 1.0e-4

# Viscosidad del aire por la ley de Sutherland
MU_REF, T_REF, S_SUTHERLAND = 1.716e-5, 273.15, 110.4


def cf_adimensional(Ae_At, pb_p0, g=GAMMA_AIRE):
    """C_F = f(γ, Ae/A*, pb/p0). Acepta un número o un arreglo de pb/p0."""
    pb_p0 = np.atleast_1d(pb_p0)
    cf = []
    for r in pb_p0:
        pb = r * _P0
        s = estado_salida(pb, _P0, _T0, _AT, Ae_At, g, R_AIRE)
        F = empuje(s["m"], s["Ve"], s["pe"], pb, Ae_At * _AT)
        cf.append(coeficiente_empuje(F, _P0, _AT))
    return np.array(cf)


def _eje_pb_p0(n):
    """pb/p0 de 0.002 a 0.99 con espaciado logarítmico."""
    return np.geomspace(2e-3, 0.99, n)


def curvas_cf(relaciones_area, g=GAMMA_AIRE, n=120):
    """{Ae/A*: (pb/p0, C_F)} para cada relación de áreas."""
    eje = _eje_pb_p0(n)
    return {ar: (eje, cf_adimensional(ar, eje, g)) for ar in relaciones_area}


def efecto_gamma(Ae_At, gammas, n=120):
    """{γ: (pb/p0, C_F)} con la misma relación de áreas."""
    eje = _eje_pb_p0(n)
    return {g: (eje, cf_adimensional(Ae_At, eje, g)) for g in gammas}


def prueba_semejanza(Ae_At, pb_p0, g=GAMMA_AIRE, R=R_AIRE, variantes=None):
    """
    Calcula F y C_F para toberas con los mismos grupos Π pero distinta
    escala, T0 y p0. Si el análisis dimensional es correcto, C_F sale igual
    en todas aunque F cambie mucho.
    """
    if variantes is None:
        variantes = (
            ("Referencia", 1.0e6, 300.0, 10.0),
            ("Doble de tamaño", 1.0e6, 300.0, 20.0),
            ("Gas caliente (T0 × 5)", 1.0e6, 1500.0, 10.0),
            ("p0 × 3 (y pb × 3)", 3.0e6, 300.0, 10.0),
            ("Modelo a escala 1:4", 1.0e6, 300.0, 2.5),
        )
    filas = []
    for nombre, p0, T0, Dt_mm in variantes:
        At = np.pi * (Dt_mm / 1e3) ** 2 / 4
        pb = pb_p0 * p0
        s = estado_salida(pb, p0, T0, At, Ae_At, g, R)
        F = empuje(s["m"], s["Ve"], s["pe"], pb, Ae_At * At)
        filas.append({"nombre": nombre, "p0_Pa": p0, "T0_K": T0, "Dt_mm": Dt_mm,
                      "m_kg_s": s["m"], "F_N": F, "CF": coeficiente_empuje(F, p0, At)})
    return filas


def viscosidad_sutherland(T):
    """Viscosidad dinámica del aire [Pa·s] (ley de Sutherland)."""
    return MU_REF * (T / T_REF) ** 1.5 * (T_REF + S_SUTHERLAND) / (T + S_SUTHERLAND)


def reynolds_garganta(p0, T0, Dt, g=GAMMA_AIRE, R=R_AIRE):
    """
    Re* = ρ*·V*·D*/μ* con las condiciones sónicas de la garganta (M = 1).
    La viscosidad es la del aire (Sutherland); para otros gases es una
    estimación del orden de magnitud.
    """
    T_s = T0 * 2 / (g + 1)
    p_s = p0 * (2 / (g + 1)) ** (g / (g - 1))
    rho_s = p_s / (R * T_s)
    V_s = np.sqrt(g * R * T_s)
    mu_s = viscosidad_sutherland(T_s)
    return {"Re": rho_s * V_s * Dt / mu_s, "T": T_s, "p": p_s, "rho": rho_s, "V": V_s,
            "mu": mu_s}
