"""
Pruebas de humo de graficas_gui.py: las figuras se construyen con el caso
preliminar y traen lo que la interfaz promete (p1, p2, p3 y regímenes).
"""
from pathlib import Path

import pytest

pytest.importorskip("plotly")

from graficas_gui import figura_distribucion, figura_mapa_regimenes  # noqa: E402
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
