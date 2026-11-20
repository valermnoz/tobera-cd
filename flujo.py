"""
flujo.py — Relaciones de flujo compresible unidimensional.

Contiene las relaciones isentrópicas, la relación área–Mach, el gasto
estrangulado y las relaciones de choque normal. Todas las funciones son
para un gas ideal calóricamente perfecto (gamma y cp constantes).

Las referencias "ec. 4.x" apuntan a las secciones del marco teórico del
documento de la propuesta.
"""

import math

from scipy.optimize import brentq

# Propiedades del aire como gas ideal
GAMMA_AIRE = 1.4
R_AIRE = 287.0  # J/(kg·K)


# ---------------------------------------------------------------------
# Velocidad del sonido y relaciones isentrópicas (sección 4.3)
# ---------------------------------------------------------------------

def velocidad_sonido(T, g=GAMMA_AIRE, R=R_AIRE):
    """Velocidad del sonido a = sqrt(gamma·R·T) [m/s]."""
    return math.sqrt(g * R * T)


def T_T0(M, g=GAMMA_AIRE):
    """Relación de temperaturas T/T0 = [1 + (gamma-1)/2·M²]^-1."""
    return 1.0 / (1.0 + 0.5 * (g - 1.0) * M**2)


def p_p0(M, g=GAMMA_AIRE):
    """Relación de presiones p/p0 = (T/T0)^(gamma/(gamma-1))."""
    return T_T0(M, g) ** (g / (g - 1.0))


def rho_rho0(M, g=GAMMA_AIRE):
    """Relación de densidades rho/rho0 = (T/T0)^(1/(gamma-1))."""
    return T_T0(M, g) ** (1.0 / (g - 1.0))


def mach_desde_presion(p_sobre_p0, g=GAMMA_AIRE):
    """
    Mach a partir de p/p0, invirtiendo la relación isentrópica.
    Tiene solución analítica: M² = 2/(gamma-1)·[(p0/p)^((gamma-1)/gamma) - 1].
    """
    if not 0.0 < p_sobre_p0 <= 1.0:
        raise ValueError("p/p0 debe estar en (0, 1].")
    return math.sqrt(2.0 / (g - 1.0) * (p_sobre_p0 ** (-(g - 1.0) / g) - 1.0))


# ---------------------------------------------------------------------
# Relación área–Mach y gasto estrangulado (sección 4.4)
# ---------------------------------------------------------------------

def area_mach(M, g=GAMMA_AIRE):
    """
    Relación A/A* en función de Mach:
    A/A* = (1/M)·[2/(gamma+1)·(1 + (gamma-1)/2·M²)]^((gamma+1)/(2(gamma-1)))
    Tiene un mínimo igual a 1 en M = 1.
    """
    expo = (g + 1.0) / (2.0 * (g - 1.0))
    return (1.0 / M) * ((2.0 / (g + 1.0)) * (1.0 + 0.5 * (g - 1.0) * M**2)) ** expo


def mach_desde_area(A_sobre_Aest, rama, g=GAMMA_AIRE):
    """
    Mach para un A/A* dado. Como A/A* tiene dos soluciones (una subsónica
    y una supersónica), hay que indicar la rama: "sub" o "sup".

    Cada rama es monótona, así que se resuelve con el método de Brent en
    un intervalo que contiene una sola raíz.
    """
    if A_sobre_Aest < 1.0 - 1e-12:
        raise ValueError("A/A* no puede ser menor que 1.")
    if A_sobre_Aest <= 1.0 + 1e-12:
        return 1.0

    def f(M):
        return area_mach(M, g) - A_sobre_Aest

    if rama == "sub":
        return brentq(f, 1e-8, 1.0)
    if rama == "sup":
        return brentq(f, 1.0, 50.0)
    raise ValueError('La rama debe ser "sub" o "sup".')


def gasto_estrangulado(p0, T0, A_garganta, g=GAMMA_AIRE, R=R_AIRE):
    """
    Gasto másico máximo cuando la garganta llega a M = 1 [kg/s]:
    m = p0·A*/sqrt(T0) · sqrt(gamma/R) · (2/(gamma+1))^((gamma+1)/(2(gamma-1)))
    """
    expo = (g + 1.0) / (2.0 * (g - 1.0))
    return p0 * A_garganta / math.sqrt(T0) * math.sqrt(g / R) * (2.0 / (g + 1.0)) ** expo


# ---------------------------------------------------------------------
# Choque normal (sección 4.6)
# ---------------------------------------------------------------------

def choque_normal(M1, g=GAMMA_AIRE):
    """
    Propiedades a través de un choque normal para un Mach de llegada M1 > 1.

    Devuelve un diccionario con:
      M2      Mach después del choque (subsónico)
      p2_p1   salto de presión estática
      T2_T1   salto de temperatura estática
      rho2_rho1 salto de densidad
      p02_p01 caída de presión de estancamiento (< 1)
    """
    if M1 <= 1.0:
        raise ValueError("Un choque normal requiere M1 > 1.")

    M1c = M1**2
    M2 = math.sqrt((1.0 + 0.5 * (g - 1.0) * M1c) / (g * M1c - 0.5 * (g - 1.0)))
    p2_p1 = 1.0 + 2.0 * g / (g + 1.0) * (M1c - 1.0)
    rho2_rho1 = (g + 1.0) * M1c / ((g - 1.0) * M1c + 2.0)
    T2_T1 = p2_p1 / rho2_rho1
    p02_p01 = (rho2_rho1 ** (g / (g - 1.0))) * (
        ((g + 1.0) / (2.0 * g * M1c - (g - 1.0))) ** (1.0 / (g - 1.0))
    )
    return {
        "M2": M2,
        "p2_p1": p2_p1,
        "T2_T1": T2_T1,
        "rho2_rho1": rho2_rho1,
        "p02_p01": p02_p01,
    }
