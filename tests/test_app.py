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
    assert "Iniciar" in at.button(key="comenzar").label


def test_interfaz_carga_sin_errores():
    at = abrir_programa()
    assert not at.exception
    assert [t.label for t in at.tabs] == ["Caso", "Resultados", "Explorador de choque",
                                          "Análisis dimensional", "Comparar casos",
                                          "Validación SolidWorks"]


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


def test_todas_las_pestanas_con_resultado(tmp_path):
    # Se simula en una carpeta temporal y se pasa el resultado a la interfaz:
    # las seis pestañas deben dibujarse sin errores (incluye el PDF y la animación)
    import configuracion as cfg
    from main import leer_caso

    caso = leer_caso(Path(__file__).parent / "datos" / "caso_prueba.json")
    resultado = cfg.ejecutar(caso, dir_salidas=tmp_path)
    resultado["id"] = 1
    at = abrir_programa()
    at.session_state["resultado"] = resultado
    at.run()
    assert not at.exception
    assert at.slider(key="explorador_pb_1").value > 0
    assert resultado["pdf"].startswith(b"%PDF")


def test_comparar_un_caso_consigo_mismo(tmp_path):
    # Dos casos con el mismo nombre no deben romper la hoja de comparación
    import configuracion as cfg
    from main import leer_caso

    caso = leer_caso(Path(__file__).parent.parent / "casos" / "caso_preliminar.json")
    resultado = cfg.ejecutar(caso, dir_salidas=tmp_path)
    resultado["id"] = 1
    at = abrir_programa()
    at.session_state["resultado"] = resultado
    at.run()
    at.selectbox(key="comp_b").set_value("casos/caso_preliminar.json").run()
    assert not at.exception
