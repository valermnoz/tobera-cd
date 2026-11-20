"""
Pruebas de geometria.py con la tobera del caso preliminar.
"""
import math

import numpy as np
import pytest

from geometria import (
    _extremos, area, contorno, exportar_dimensiones, exportar_dxf,
    exportar_xyz, muestrear, resumen_geometria,
)

DT, DE = 9.9115e-3, 14.6091e-3


@pytest.fixture
def tramos():
    return contorno(DT, DE)


def pendiente(t, extremo):
    """Pendiente dr/dx de un tramo en su punto inicial (0) o final (1)."""
    if t["tipo"] == "linea":
        (x0, r0), (x1, r1) = t["p0"], t["p1"]
        return (r1 - r0) / (x1 - x0)
    phi = math.radians(t["phi0"] if extremo == 0 else t["phi1"])
    sentido = 1 if t["phi1"] > t["phi0"] else -1
    dx, dr = -math.sin(phi) * sentido, math.cos(phi) * sentido
    return dr / dx


def test_tramos_continuos_y_tangentes(tramos):
    for a, b in zip(tramos[:-1], tramos[1:]):
        fin_a, ini_b = _extremos(a)[1], _extremos(b)[0]
        assert fin_a == pytest.approx(ini_b, abs=1e-12)
        assert pendiente(a, 1) == pytest.approx(pendiente(b, 0), abs=1e-9)


def test_garganta_en_cero_con_radio_correcto(tramos):
    x, r = muestrear(tramos)
    i = np.argmin(r)
    assert x[i] == pytest.approx(0.0, abs=1e-12)
    assert r[i] == pytest.approx(DT / 2, rel=1e-12)


def test_entrada_y_salida(tramos):
    geo = resumen_geometria(tramos)
    assert geo["r_salida"] == pytest.approx(DE / 2, rel=1e-12)
    assert geo["r_entrada"] == pytest.approx(DT / 2 * 3.0, rel=1e-12)  # A_in/A* = 9
    assert geo["L_total"] == pytest.approx(geo["L_aguas_arriba"] + geo["L_divergente"])


def test_radio_monotono(tramos):
    x, r = muestrear(tramos)
    assert np.all(np.diff(x) > 0)
    assert np.all(np.diff(r[x <= 0]) <= 1e-15)   # no crece antes de la garganta
    assert np.all(np.diff(r[x >= 0]) >= -1e-15)  # no decrece después


def test_pendientes_de_los_conos(tramos):
    assert pendiente(tramos[2], 0) == pytest.approx(-math.tan(math.radians(30)))
    assert pendiente(tramos[5], 0) == pytest.approx(math.tan(math.radians(15)))


def test_area_minima_es_A_garganta(tramos):
    _, r = muestrear(tramos)
    assert area(r).min() == pytest.approx(math.pi * DT**2 / 4, rel=1e-12)


def test_geometria_imposible():
    with pytest.raises(ValueError):
        contorno(DT, DE, relacion_contraccion=1.2)


def test_exportar_xyz(tramos, tmp_path):
    ruta = tmp_path / "c.txt"
    exportar_xyz(tramos, ruta)
    datos = np.loadtxt(ruta)
    assert datos.shape[1] == 3
    assert np.all(datos[:, 2] == 0)
    assert datos[:, 1].min() == pytest.approx(DT / 2 * 1e3, rel=1e-6)  # en mm


def test_exportar_dxf_perfil_cerrado(tramos, tmp_path):
    ezdxf = pytest.importorskip("ezdxf")
    ruta = tmp_path / "c.dxf"
    exportar_dxf(tramos, ruta, espesor=0.002)
    msp = ezdxf.readfile(ruta).modelspace()
    contorno_dxf = [e for e in msp if e.dxf.layer == "CONTORNO"]
    assert len(msp.query("ARC")) == 3
    # Perfil cerrado: cada extremo aparece exactamente dos veces
    puntos = []
    for e in contorno_dxf:
        if e.dxftype() == "LINE":
            puntos += [tuple(e.dxf.start)[:2], tuple(e.dxf.end)[:2]]
        else:
            puntos += [tuple(p)[:2] for p in (e.start_point, e.end_point)]
    redondeados = [tuple(round(c, 4) + 0.0 for c in p) for p in puntos]
    assert all(redondeados.count(p) == 2 for p in redondeados)


def test_exportar_dimensiones(tramos, tmp_path):
    ruta = tmp_path / "d.txt"
    exportar_dimensiones(DT, DE, resumen_geometria(tramos), ruta, ang_conv=30, ang_div=15,
                         relacion_contraccion=9, L_recta=0.01, f_entrada=2, f_arriba=1.5,
                         f_abajo=1.5, espesor=0.002)
    texto = ruta.read_text(encoding="utf-8")
    assert '"D_garganta" = 9.9115' in texto
    assert '"espesor_pared" = 2.0000' in texto
