"""
Pruebas de tobera.py con el caso preliminar del documento:
aire, p0 = 1 MPa, T0 = 300 K, pa = 81.3 kPa (Querétaro), F = 100 N.
"""
import numpy as np
import pytest

from tobera import (
    curva_empuje, dimensionar, distribucion, empuje, estado_salida,
    posicion_choque, presion_atmosferica, presiones_criticas, regimen,
)

P0, T0, F = 1.0e6, 300.0, 100.0
PA = presion_atmosferica(1820.0)


@pytest.fixture
def caso():
    return dimensionar(P0, T0, PA, F)


def test_presion_queretaro():
    assert PA == pytest.approx(81.3e3, rel=2e-3)


def test_dimensionamiento_caso_preliminar(caso):
    assert caso["Me"] == pytest.approx(2.29, abs=0.01)
    assert caso["Ae_At"] == pytest.approx(2.17, abs=0.01)
    assert caso["Ve"] == pytest.approx(555, abs=1)
    assert caso["m"] == pytest.approx(0.180, abs=0.001)
    assert caso["Dt"] * 1e3 == pytest.approx(9.9, abs=0.05)
    assert caso["De"] * 1e3 == pytest.approx(14.6, abs=0.05)
    assert caso["CF"] == pytest.approx(1.30, abs=0.01)


def test_empuje_reproduce_requerido(caso):
    # Con la tobera adaptada (pe = pa) el empuje debe ser exactamente F
    s = estado_salida(PA, P0, T0, caso["At"], caso["Ae_At"])
    assert s["regimen"] == "adaptada"
    assert s["m"] == pytest.approx(caso["m"], rel=1e-9)
    assert empuje(s["m"], s["Ve"], s["pe"], PA, caso["Ae"]) == pytest.approx(F, rel=1e-9)


def test_presiones_criticas(caso):
    c = presiones_criticas(P0, caso["Ae_At"])
    assert c["p1"] == pytest.approx(947e3, rel=2e-3)
    assert c["p2"] == pytest.approx(484e3, rel=2e-3)
    assert c["p3"] == pytest.approx(PA, rel=1e-9)


@pytest.mark.parametrize("pb, esperado", [
    (980e3, "subsonico"),
    (700e3, "choque_interno"),
    (300e3, "sobreexpandida"),
    (50e3, "subexpandida"),
])
def test_regimen(caso, pb, esperado):
    assert regimen(pb, presiones_criticas(P0, caso["Ae_At"])) == esperado


def test_choque_interno_caso_2(caso):
    ch = posicion_choque(683e3, P0, caso["Ae_At"])
    assert ch["As_At"] == pytest.approx(1.59, abs=0.01)
    assert ch["M1"] == pytest.approx(1.92, abs=0.01)
    assert ch["M2"] == pytest.approx(0.59, abs=0.01)
    assert ch["p02_p01"] == pytest.approx(0.76, abs=0.01)
    assert ch["pe"] == pytest.approx(683e3, rel=1e-9)


def test_choque_se_mueve_con_pb(caso):
    # Al subir pb el choque avanza hacia la garganta
    c = presiones_criticas(P0, caso["Ae_At"])
    cerca_salida = posicion_choque(c["p2"] * 1.001, P0, caso["Ae_At"])
    cerca_garganta = posicion_choque(c["p1"] * 0.999, P0, caso["Ae_At"])
    assert cerca_salida["As_At"] == pytest.approx(caso["Ae_At"], rel=1e-2)
    assert cerca_garganta["As_At"] == pytest.approx(1.0, abs=2e-2)


def test_gasto_estrangulado_no_depende_de_pb(caso):
    m = [estado_salida(pb, P0, T0, caso["At"], caso["Ae_At"])["m"]
         for pb in (900e3, 683e3, 300e3, PA, 50e3)]
    assert np.allclose(m, caso["m"], rtol=1e-6)


def test_distribucion_con_choque(caso):
    # Tobera cónica sencilla: convergente y divergente lineales en el radio
    rt, re = caso["Dt"] / 2, caso["De"] / 2
    x = np.linspace(-0.02, 0.0, 200)
    x = np.concatenate([x, np.linspace(0.0, 0.009, 400)[1:]])
    r = np.where(x < 0, rt - x * np.tan(np.radians(30)), rt + x * np.tan(np.radians(15)))
    r[-1] = re
    d = distribucion(x, np.pi * r**2, 683e3, P0, T0)
    assert d["regimen"] == "choque_interno"
    assert d["x_choque"] is not None and 0 < d["x_choque"] < x[-1]
    assert d["p"][-1] == pytest.approx(683e3, rel=5e-3)
    assert d["M"].max() == pytest.approx(1.92, abs=0.02)


def test_curva_empuje_recorre_los_regimenes(caso):
    curva = curva_empuje(P0, T0, caso["At"], caso["Ae_At"])
    # pb crece a lo largo de la curva: subexpandida -> ... -> subsónico
    assert np.all(np.diff(curva["pb"]) > 0)
    assert curva["regimen"][0] == "subexpandida"
    assert curva["regimen"][-1] == "subsonico"
    assert {"sobreexpandida", "choque_interno"} <= set(curva["regimen"])
    # El empuje baja al subir la presión exterior
    assert np.all(np.diff(curva["F"]) < 0)


def test_curva_empuje_coincide_con_el_diseno(caso):
    curva = curva_empuje(P0, T0, caso["At"], caso["Ae_At"])
    F_pa = np.interp(PA, curva["pb"], curva["F"])
    assert F_pa == pytest.approx(F, rel=1e-3)
