"""
Prueba de humo de la interfaz: la página carga sin errores.
(No se simula aquí porque eso escribe en casos/ y salidas/.)
"""
from pathlib import Path

import pytest

AppTest = pytest.importorskip("streamlit.testing.v1").AppTest


APP = Path(__file__).parent.parent / "app.py"


def abrir_programa():
    """Carga la pantalla de inicio y entra al programa con el botón Comenzar."""
    at = AppTest.from_file(str(APP), default_timeout=60).run()
    at.button(key="comenzar").click().run()
    return at


def test_pantalla_de_inicio():
    at = AppTest.from_file(str(APP), default_timeout=60).run()
    assert not at.exception
    assert not at.tabs  # el programa no se ve todavía
    assert at.button(key="comenzar").label.startswith("Comenzar")


def test_interfaz_carga_sin_errores():
    at = abrir_programa()
    assert not at.exception
    assert [t.label for t in at.tabs] == ["Caso", "Resultados", "Validación SolidWorks"]


def test_volver_al_inicio_conserva_el_formulario():
    at = abrir_programa()
    at.text_input(key="f_descripcion").set_value("prueba de regreso").run()
    next(b for b in at.button if "Volver al inicio" in b.label).click().run()
    assert not at.tabs
    at.button(key="comenzar").click().run()
    assert at.text_input(key="f_descripcion").value == "prueba de regreso"


def test_aviso_al_sobrescribir_otro_caso():
    # Con caso_preliminar abierto, renombrarlo como otro caso existente pide confirmación
    at = abrir_programa()
    at.text_input(key="f_nombre").set_value("motor_knsb").run()
    assert not at.exception
    assert any("motor_knsb.json" in w.value for w in at.warning)
    guardar = next(b for b in at.button if b.label == "Guardar")
    assert guardar.disabled
