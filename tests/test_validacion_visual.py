"""
Pruebas de la validación visual: veredicto, errores globales, datos de
ejemplo y figuras (empalme animado, mapa de error, paridad, globales).
"""
from pathlib import Path

import numpy as np
import pytest

import comparacion as cmp
from graficas_gui import figura_empalme, figura_globales, figura_mapa_error, figura_paridad
from main import completar_caso, correr, leer_caso

CASO = Path(__file__).parent / "datos" / "caso_prueba.json"


@pytest.fixture(scope="module")
def comp_mach():
    res = correr(completar_caso(leer_caso(CASO)))
    d = next(d for d in res["distribuciones"] if d["x_choque"] is not None)
    tabla = cmp.leer_csv_solidworks(cmp.datos_ejemplo(res["x"] * 1e3, d["p"], d["M"]))
    comp = cmp.comparar(res["x"] * 1e3, d["M"], tabla["X [m]"].to_numpy() * 1e3,
                        tabla["Mach Number [ ]"].to_numpy())
    return res, comp


@pytest.mark.parametrize("error, clave", [(0.5, "excelente"), (2.0, "excelente"),
                                          (3.0, "buena"), (8.0, "aceptable"), (30, "revisar")])
def test_veredicto(error, clave):
    assert cmp.veredicto(error)[0] == clave


def test_errores_globales_omite_los_vacios():
    filas = cmp.errores_globales({"F": 100.0, "m": 0.18}, {"F": 98.0, "m": 0})
    assert len(filas) == 1
    assert filas[0][1] == pytest.approx(100 * 2 / 98)


def test_datos_de_ejemplo_se_leen_como_solidworks():
    x = np.linspace(-30, 10, 50)
    tabla = cmp.leer_csv_solidworks(cmp.datos_ejemplo(x, np.full(50, 5e5), np.ones(50)))
    assert cmp.detectar_columnas(list(tabla.columns)) == {
        "x": "X [m]", "p": "Pressure [Pa]", "M": "Mach Number [ ]"}
    assert tabla["X [m]"].iloc[0] == pytest.approx(-0.030)


def test_datos_de_ejemplo_parecidos_al_modelo(comp_mach):
    _, comp = comp_mach
    # Imitan un CFD razonable: error medio de unos pocos por ciento
    assert 0.3 < comp["metricas"]["error_medio_pct"] < 6


def test_figuras_de_validacion(comp_mach):
    res, comp = comp_mach
    emp = figura_empalme(comp, "Número de Mach", "–", n_cuadros=10)
    assert len(emp.frames) == 10 and emp.data[1].fill == "tonexty"
    mapa = figura_mapa_error(res["x"] * 1e3, res["r"] * 1e3, comp, "Mach")
    assert np.isnan(np.array(mapa.data[0].z, dtype=float)[0, 0])
    par = figura_paridad(comp, "Mach", "–")
    assert "dentro de" in par.layout.title.text
    glo = figura_globales([("Empuje F", 1.2), ("Gasto", -7.0)])
    assert list(glo.data[0].x) == [1.2, -7.0]
