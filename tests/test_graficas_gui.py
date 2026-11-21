"""
Pruebas de humo de graficas_gui.py: las figuras se construyen con el caso
preliminar y traen lo que la interfaz promete (p1, p2, p3 y regímenes).
"""
from pathlib import Path

import numpy as np
import pytest

pytest.importorskip("plotly")

from graficas_gui import figura_campo, figura_distribucion, figura_mapa_regimenes  # noqa: E402
from main import completar_caso, correr, leer_caso  # noqa: E402
from tobera import curva_empuje  # noqa: E402

CASO = Path(__file__).parent / "datos" / "caso_prueba.json"


@pytest.fixture(scope="module")
def corrida():
    caso = completar_caso(leer_caso(CASO))
    return caso, correr(caso)


def _textos(fig):
    return [a.text for a in fig.layout.annotations]


def test_presion_marca_las_presiones_criticas(corrida):
    _, res = corrida
    fig = figura_distribucion(res["x"], res["distribuciones"], "p", res["criticas"])
    textos = " ".join(_textos(fig))
    for nombre in ("p₁", "p₂", "p₃"):
        assert nombre in textos


def test_mapa_de_regimenes(corrida):
    caso, res = corrida
    d = res["diseno"]
    curva = curva_empuje(caso["camara"]["p0_Pa"], caso["camara"]["T0_K"], d["At"], d["Ae_At"],
                         caso["gas"]["gamma"], caso["gas"]["R"], n=40)
    fig = figura_mapa_regimenes(curva, res["criticas"], caso["camara"]["p0_Pa"],
                                caso["pa_Pa"], res["analisis"])
    assert fig.layout.xaxis.type == "log"
    assert len(fig.data[1].x) == len(res["analisis"])
    assert "sobreexpandida" in _textos(fig)


def test_campo_de_mach_solo_dentro_de_la_tobera(corrida):
    _, res = corrida
    d = next(d for d in res["distribuciones"] if d["x_choque"] is not None)
    fig = figura_campo(res["x"], res["r"], d, "M")
    z = np.array(fig.data[0].z, dtype=float)
    # Las esquinas quedan fuera de la tobera (sin color) y el centro tiene M(x)
    assert np.isnan(z[0, 0]) and np.isnan(z[-1, -1])
    assert np.nanmax(z) == pytest.approx(np.max(d["M"]))
    assert any("choque" in (a.text or "") for a in fig.layout.annotations)
