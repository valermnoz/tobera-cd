"""
Pruebas del análisis dimensional (objetivo 5) con el caso preliminar.
"""
import numpy as np
import pytest

import analisis_dimensional as ad
from tobera import dimensionar, presion_atmosferica

P0, T0, F = 1.0e6, 300.0, 100.0
PA = presion_atmosferica(1820.0)


@pytest.fixture
def diseno():
    return dimensionar(P0, T0, PA, F)


def test_cf_adimensional_reproduce_el_diseno(diseno):
    assert ad.cf_adimensional(diseno["Ae_At"], PA / P0)[0] == pytest.approx(diseno["CF"],
                                                                            rel=1e-9)


@pytest.mark.parametrize("pb_p0", [0.05, 0.3, 0.7, 0.96])
def test_semejanza_mismo_cf_en_todos_los_regimenes(diseno, pb_p0):
    filas = ad.prueba_semejanza(diseno["Ae_At"], pb_p0)
    cf = [f["CF"] for f in filas]
    assert max(cf) - min(cf) < 1e-9
    # ...aunque el empuje cambie con el tamaño y la presión de cámara
    F = [f["F_N"] for f in filas]
    assert max(F) / min(F) > 10


def test_reynolds_garganta_caso_preliminar(diseno):
    re = ad.reynolds_garganta(P0, T0, diseno["Dt"])
    assert re["Re"] == pytest.approx(1.45e6, rel=0.02)
    assert re["T"] == pytest.approx(250.0, rel=1e-9)   # T* = 2 T0 / (γ + 1)


def test_sutherland_valor_de_tabla():
    # Aire a 300 K: μ ≈ 1.846e-5 Pa·s
    assert ad.viscosidad_sutherland(300.0) == pytest.approx(1.846e-5, rel=5e-3)


def test_gamma_menor_da_mas_cf(diseno):
    curvas = ad.efecto_gamma(diseno["Ae_At"], [1.4, 1.2], n=20)
    eje, cf_14 = curvas[1.4]
    _, cf_12 = curvas[1.2]
    # Con la tobera estrangulada (pb/p0 bajo) un γ menor da más empuje adimensional
    bajo = eje < 0.1
    assert np.all(cf_12[bajo] > cf_14[bajo])
