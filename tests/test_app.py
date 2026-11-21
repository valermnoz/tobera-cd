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


def test_aviso_al_sobrescribir_otro_caso():
    # Con caso_preliminar abierto, renombrarlo como otro caso existente pide confirmación
    app = Path(__file__).parent.parent / "app.py"
    at = AppTest.from_file(str(app), default_timeout=60).run()
    at.text_input(key="f_nombre").set_value("motor_knsb").run()
    assert not at.exception
    assert any("motor_knsb.json" in w.value for w in at.warning)
    guardar = next(b for b in at.button if b.label == "Guardar")
    assert guardar.disabled
