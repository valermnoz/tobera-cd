"""
Prueba de humo de la interfaz: la página carga sin errores.
(No se simula aquí porque eso escribe en casos/ y salidas/.)
"""
from pathlib import Path

import pytest

AppTest = pytest.importorskip("streamlit.testing.v1").AppTest


def test_interfaz_carga_sin_errores():
    app = Path(__file__).parent.parent / "app.py"
    at = AppTest.from_file(str(app), default_timeout=60).run()
    assert not at.exception
    assert [t.label for t in at.tabs] == ["Caso", "Resultados", "Validación SolidWorks"]
