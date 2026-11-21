"""
tobera.py — Diseño y análisis de una tobera convergente–divergente.

  1. dimensionar():         garganta y salida para un empuje requerido
  2. presiones_criticas():  p1, p2, p3 que separan los regímenes
  3. regimen():             clasificación para una presión exterior pb
  4. posicion_choque():     dónde se forma el choque normal interno
  5. estado_salida():       condiciones en la salida para cualquier pb
  6. empuje():              balance de cantidad de movimiento en un VC
  7. distribucion():        M, p, T a lo largo de la tobera

Unidades SI en todo el módulo: Pa, K, m, m², kg/s, N.
"""

import math

import numpy as np
from scipy.optimize import brentq

from flujo import (
    GAMMA_AIRE,
    R_AIRE,
    T_T0,
    area_mach,
    choque_normal,
    gasto_estrangulado,
    mach_desde_area,
    mach_desde_presion,
    p_p0,
    velocidad_sonido,
)


def presion_atmosferica(altitud_m):
    """Presión de la atmósfera estándar en la troposfera [Pa] (z < 11 km)."""
    return 101325.0 * (1.0 - 2.25577e-5 * altitud_m) ** 5.25588


def area_circulo(D):
    return math.pi * D**2 / 4.0


def diametro_circulo(A):
    return math.sqrt(4.0 * A / math.pi)


# ---------------------------------------------------------------------
# 1. Dimensionamiento (secciones 4.2 a 4.4 y 4.7)
# ---------------------------------------------------------------------

def dimensionar(p0, T0, pa, F, g=GAMMA_AIRE, R=R_AIRE):
    """
    Dimensiona la tobera para que entregue el empuje F con expansión
    ideal (pe = pa) a la presión ambiente pa.

    Pasos:
      - Me de la relación isentrópica con pe = pa
      - Ae/A* de la relación área–Mach
      - Ve de la ecuación de la energía (Te de la relación isentrópica)
      - m = F/Ve, porque con pe = pa el término de presión del empuje es cero
      - A* de la ecuación de gasto estrangulado
    """
    if pa >= p0:
        raise ValueError("La presión ambiente debe ser menor que la de cámara.")

    Me = mach_desde_presion(pa / p0, g)
    Ae_At = area_mach(Me, g)
    Te = T0 * T_T0(Me, g)
    Ve = Me * velocidad_sonido(Te, g, R)
    m = F / Ve

    # El gasto estrangulado es proporcional a A*: se despeja A*
    At = m / gasto_estrangulado(p0, T0, 1.0, g, R)
    Ae = Ae_At * At

    return {
        "Me": Me,
        "Ae_At": Ae_At,
        "Te": Te,
        "Ve": Ve,
        "m": m,
        "At": At,
        "Ae": Ae,
        "Dt": diametro_circulo(At),
        "De": diametro_circulo(Ae),
        "CF": F / (p0 * At),
    }


# ---------------------------------------------------------------------
# 2–4. Regímenes y choque normal (secciones 4.5 y 4.6)
# ---------------------------------------------------------------------

def presiones_criticas(p0, Ae_At, g=GAMMA_AIRE):
    """
    Presiones exteriores que separan los regímenes de una tobera:
      p1: subsónica en toda la tobera con M = 1 justo en la garganta
      p2: choque normal justo en el plano de salida
      p3: expansión ideal (salida supersónica isentrópica)
    """
    Me_sub = mach_desde_area(Ae_At, "sub", g)
    Me_sup = mach_desde_area(Ae_At, "sup", g)
    p1 = p0 * p_p0(Me_sub, g)
    p3 = p0 * p_p0(Me_sup, g)
    p2 = p3 * choque_normal(Me_sup, g)["p2_p1"]
    return {"p1": p1, "p2": p2, "p3": p3}


def regimen(pb, criticas, tol=1e-6):
    """Nombre del régimen de operación para una presión exterior pb."""
    p1, p2, p3 = criticas["p1"], criticas["p2"], criticas["p3"]
    if pb > p1 * (1 + tol):
        return "subsonico"
    if abs(pb - p1) <= p1 * tol:
        return "estrangulado_subsonico"
    if pb > p2 * (1 + tol):
        return "choque_interno"
    if abs(pb - p2) <= p2 * tol:
        return "choque_en_salida"
    if pb > p3 * (1 + tol):
        return "sobreexpandida"
    if abs(pb - p3) <= p3 * tol:
        return "adaptada"
    return "subexpandida"


def _salida_tras_choque(As_At, Ae_At, g):
    """
    Para un choque en la sección As (en unidades de A*), devuelve
    (Me, pe/p0, datos del choque).

    El gasto se conserva a través del choque: p01·A*1 = p02·A*2.
    Como p02 < p01, después del choque el área sónica de referencia
    crece: A*2 = A*1 / (p02/p01). La salida es subsónica e isentrópica
    respecto a A*2 y p02.
    """
    M1 = mach_desde_area(As_At, "sup", g)
    ch = choque_normal(M1, g)
    r0 = ch["p02_p01"]
    Me = mach_desde_area(Ae_At * r0, "sub", g)  # Ae/A*2 = (Ae/A*1)·(p02/p01)
    pe_p0 = r0 * p_p0(Me, g)
    return Me, pe_p0, M1, ch


def posicion_choque(pb, p0, Ae_At, g=GAMMA_AIRE):
    """
    Localiza el choque normal dentro de la sección divergente cuando
    p2 < pb < p1 (sección 4.6).

    Se busca el área As/A* tal que, después del choque, el flujo subsónico
    llegue a la salida con pe = pb. La función pe(As) - pb es monótona en
    (A*, Ae), así que el método de Brent converge sin problemas.
    """
    crit = presiones_criticas(p0, Ae_At, g)
    if not crit["p2"] < pb < crit["p1"]:
        raise ValueError(
            f"Con pb = {pb:.0f} Pa no hay choque interno "
            f"(debe cumplirse {crit['p2']:.0f} < pb < {crit['p1']:.0f} Pa)."
        )

    def residuo(As_At):
        _, pe_p0, _, _ = _salida_tras_choque(As_At, Ae_At, g)
        return pe_p0 * p0 - pb

    As_At = brentq(residuo, 1.0 + 1e-9, Ae_At - 1e-9, xtol=1e-12)
    Me, pe_p0, M1, ch = _salida_tras_choque(As_At, Ae_At, g)
    return {
        "As_At": As_At,
        "M1": M1,
        "M2": ch["M2"],
        "p02_p01": ch["p02_p01"],
        "Me": Me,
        "pe": pe_p0 * p0,
    }


# ---------------------------------------------------------------------
# 5–6. Condiciones de salida y empuje (sección 4.7)
# ---------------------------------------------------------------------

def estado_salida(pb, p0, T0, At, Ae_At, g=GAMMA_AIRE, R=R_AIRE):
    """
    Condiciones en el plano de salida para cualquier presión exterior pb.

    Devuelve régimen, Me, pe, Te, Ve, gasto m y, si lo hay, el choque.
    T0 se conserva en todos los casos (flujo adiabático, incluso con choque).
    """
    crit = presiones_criticas(p0, Ae_At, g)
    reg = regimen(pb, crit)
    Ae = Ae_At * At
    choque = None

    if reg == "subsonico":
        # Sin estrangular: la salida subsónica se ajusta a pb
        pe = pb
        Me = mach_desde_presion(pb / p0, g)
    elif reg in ("estrangulado_subsonico", "choque_interno"):
        if reg == "choque_interno":
            choque = posicion_choque(pb, p0, Ae_At, g)
            Me = choque["Me"]
        else:
            Me = mach_desde_area(Ae_At, "sub", g)
        pe = pb
    else:
        # Choque en la salida o fuera: dentro de la tobera el flujo es
        # isentrópico y supersónico hasta el plano de salida.
        Me = mach_desde_area(Ae_At, "sup", g)
        pe = p0 * p_p0(Me, g)

    Te = T0 * T_T0(Me, g)
    Ve = Me * velocidad_sonido(Te, g, R)
    rho_e = pe / (R * Te)
    m = rho_e * Ve * Ae  # continuidad en la salida

    return {
        "regimen": reg,
        "Me": Me,
        "pe": pe,
        "Te": Te,
        "Ve": Ve,
        "m": m,
        "choque": choque,
        "criticas": crit,
    }


def empuje(m, Ve, pe, pa, Ae):
    """
    Empuje por balance de cantidad de movimiento en un volumen de control
    que encierra la tobera (sección 4.7):  F = m·Ve + (pe - pa)·Ae
    """
    return m * Ve + (pe - pa) * Ae


def coeficiente_empuje(F, p0, At):
    """Coeficiente de empuje adimensional C_F = F/(p0·A*) (sección 4.8)."""
    return F / (p0 * At)


def curva_empuje(p0, T0, At, Ae_At, g=GAMMA_AIRE, R=R_AIRE, n=200):
    """
    Barrido de la presión exterior para una tobera ya dimensionada.

    Recorre pb desde p3/5 (subexpandida) hasta casi p0 (sin flujo) con
    espaciado logarítmico y devuelve, para cada pb, el régimen, la presión
    de salida pe, el gasto m, el empuje F y C_F. Sirve para el mapa de
    regímenes de la interfaz.
    """
    crit = presiones_criticas(p0, Ae_At, g)
    Ae = Ae_At * At
    curva = {"pb": [], "pe": [], "m": [], "F": [], "CF": [], "regimen": []}
    for pb in np.geomspace(crit["p3"] / 5, 0.999 * p0, n):
        s = estado_salida(pb, p0, T0, At, Ae_At, g, R)
        F = empuje(s["m"], s["Ve"], s["pe"], pb, Ae)
        curva["pb"].append(pb)
        curva["pe"].append(s["pe"])
        curva["m"].append(s["m"])
        curva["F"].append(F)
        curva["CF"].append(coeficiente_empuje(F, p0, At))
        curva["regimen"].append(s["regimen"])
    for clave in ("pb", "pe", "m", "F", "CF"):
        curva[clave] = np.array(curva[clave])
    return curva


# ---------------------------------------------------------------------
# 7. Distribución a lo largo de la tobera
# ---------------------------------------------------------------------

def _mach_rama(A_sobre_Aest, rama, g):
    """Mach en cada sección para una rama ("sub" o "sup") de A/A*."""
    return np.array([mach_desde_area(a, rama, g) for a in A_sobre_Aest])


def _perfil_sin_choque(A, i_g, reg, pb, p0, g):
    """
    Mach en cada sección cuando no hay choque dentro de la tobera.

      subsonico:              sin estrangular; el A* de referencia es
                              "virtual" (menor que la garganta), porque el
                              flujo nunca llega a M = 1.
      estrangulado_subsonico: M = 1 en la garganta y subsónico después.
      resto (supersónicos):   subsónico antes de la garganta y supersónico
                              después; lo que pase fuera no afecta el interior.
    """
    At = A[i_g]
    if reg == "subsonico":
        Me = mach_desde_presion(pb / p0, g)
        A_virtual = A[-1] / area_mach(Me, g)
        return _mach_rama(A / A_virtual, "sub", g)
    if reg == "estrangulado_subsonico":
        return _mach_rama(A / At, "sub", g)
    M = np.empty_like(A)
    M[: i_g + 1] = _mach_rama(A[: i_g + 1] / At, "sub", g)
    M[i_g + 1 :] = _mach_rama(A[i_g + 1 :] / At, "sup", g)
    return M


def _perfil_con_choque(x, A, i_g, pb, p0, g):
    """
    Mach y presión de estancamiento en cada sección con choque normal
    interno (p2 < pb < p1). Devuelve (M, p0_local, x_choque).

    Antes del choque: rama supersónica respecto a A*.
    Después del choque: rama subsónica respecto a A*2 = A*/(p02/p01), y la
    presión de estancamiento baja a p02.
    """
    At = A[i_g]
    ch = posicion_choque(pb, p0, A[-1] / At, g)
    As = ch["As_At"] * At
    r0 = ch["p02_p01"]

    # Primera sección del divergente cuya área supera a la del choque
    j = np.arange(i_g + 1, len(A))
    i_s = int(j[np.argmax(A[j] >= As)])
    x_choque = float(np.interp(As, A[i_s - 1 : i_s + 1], x[i_s - 1 : i_s + 1]))

    M = np.empty_like(A)
    M[: i_g + 1] = _mach_rama(A[: i_g + 1] / At, "sub", g)
    M[i_g + 1 : i_s] = _mach_rama(A[i_g + 1 : i_s] / At, "sup", g)
    M[i_s:] = _mach_rama(A[i_s:] * r0 / At, "sub", g)

    p0_local = np.full_like(A, p0)
    p0_local[i_s:] = p0 * r0
    return M, p0_local, x_choque


def distribucion(x, A, pb, p0, T0, g=GAMMA_AIRE):
    """
    M(x), p(x) y T(x) a lo largo de la tobera para una presión exterior pb.

    x, A: arreglos de posición axial y área de cada sección (la garganta
          es el mínimo de A).
    Devuelve un diccionario con los arreglos M, p, T, el régimen y la
    posición del choque x_choque (None si no hay choque interno).
    """
    x = np.asarray(x, dtype=float)
    A = np.asarray(A, dtype=float)
    i_g = int(np.argmin(A))
    reg = regimen(pb, presiones_criticas(p0, A[-1] / A[i_g], g))

    if reg == "choque_interno":
        M, p0_local, x_choque = _perfil_con_choque(x, A, i_g, pb, p0, g)
    else:
        M = _perfil_sin_choque(A, i_g, reg, pb, p0, g)
        p0_local, x_choque = np.full_like(A, p0), None

    # T0 se conserva incluso a través del choque (flujo adiabático)
    p = p0_local * np.array([p_p0(m, g) for m in M])
    T = T0 * np.array([T_T0(m, g) for m in M])
    return {"M": M, "p": p, "T": T, "x_choque": x_choque, "regimen": reg}
