"""
Pruebas de flujo.py contra valores tabulados (gamma = 1.4).
Fuente de los valores: tablas de flujo isentrópico y de choque normal
de cualquier texto del curso (Çengel y Cimbala, White, Anderson).
"""
import pytest

from flujo import (
    T_T0, area_mach, choque_normal, gasto_estrangulado,
    mach_desde_area, mach_desde_presion, p_p0, rho_rho0,
)

TOL = 1e-4


@pytest.mark.parametrize("M, A, p, T, rho", [
    (0.5, 1.33984, 0.84302, 0.95238, 0.88517),
    (1.0, 1.00000, 0.52828, 0.83333, 0.63394),
    (2.0, 1.68750, 0.12780, 0.55556, 0.23005),
    (3.0, 4.23457, 0.027224, 0.35714, 0.076226),
])
def test_relaciones_isentropicas(M, A, p, T, rho):
    assert area_mach(M) == pytest.approx(A, rel=TOL)
    assert p_p0(M) == pytest.approx(p, rel=TOL)
    assert T_T0(M) == pytest.approx(T, rel=TOL)
    assert rho_rho0(M) == pytest.approx(rho, rel=TOL)


@pytest.mark.parametrize("M", [0.2, 0.5, 0.9, 1.5, 2.3, 4.0])
def test_inversion_area_mach(M):
    rama = "sub" if M < 1 else "sup"
    assert mach_desde_area(area_mach(M), rama) == pytest.approx(M, rel=1e-8)


@pytest.mark.parametrize("M", [0.3, 1.0, 2.29, 3.5])
def test_inversion_presion(M):
    assert mach_desde_presion(p_p0(M)) == pytest.approx(M, rel=1e-10)


def test_garganta_es_sonica():
    assert mach_desde_area(1.0, "sub") == 1.0
    assert mach_desde_area(1.0, "sup") == 1.0


@pytest.mark.parametrize("M1, M2, p21, T21, p0201", [
    (1.5, 0.70109, 2.45833, 1.32022, 0.92979),
    (2.0, 0.57735, 4.50000, 1.68750, 0.72087),
    (3.0, 0.47519, 10.33333, 2.67901, 0.32834),
])
def test_choque_normal(M1, M2, p21, T21, p0201):
    ch = choque_normal(M1)
    assert ch["M2"] == pytest.approx(M2, rel=TOL)
    assert ch["p2_p1"] == pytest.approx(p21, rel=TOL)
    assert ch["T2_T1"] == pytest.approx(T21, rel=TOL)
    assert ch["p02_p01"] == pytest.approx(p0201, rel=TOL)


def test_choque_requiere_supersonico():
    with pytest.raises(ValueError):
        choque_normal(0.9)


def test_gasto_estrangulado_aire():
    # Para aire: m·sqrt(T0)/(p0·A*) = 0.040418 (kg·K^0.5/(N·s))
    assert gasto_estrangulado(1.0, 1.0, 1.0) == pytest.approx(0.040418, rel=TOL)
