"""
Pruebas de configuracion.py (casos para la interfaz) y resumen_txt.py.
"""
import json
from pathlib import Path

import pytest

import configuracion as cfg
from main import correr, leer_caso, resumen
from resumen_txt import parsear_resumen

CASO = Path(__file__).parent / "datos" / "caso_prueba.json"


def texto_caso():
    return CASO.read_text(encoding="utf-8")


def test_leer_json_valido():
    assert cfg.leer_json(texto_caso())["nombre"] == "caso_prueba"


@pytest.mark.parametrize("texto, mensaje", [
    ("{no es json", "JSON válido"),
    ("[1, 2]", "objeto"),
    ('{"nombre": "x"}', "faltan"),
    ('{"nombre": "x", "gas": {}, "camara": {}, "ambiente": {}, "empuje_requerido_N": 1}',
     "altitud_m"),
])
def test_leer_json_con_errores(texto, mensaje):
    with pytest.raises(ValueError, match=mensaje):
        cfg.leer_json(texto)


@pytest.mark.parametrize("nombre, esperado", [
    ("motor knsb", "motor_knsb"),
    ("caso/../raro", "caso_raro"),
    ("  prueba-1  ", "prueba-1"),
])
def test_nombre_archivo(nombre, esperado):
    assert cfg.nombre_archivo(nombre) == esperado


def test_nombre_archivo_vacio():
    with pytest.raises(ValueError):
        cfg.nombre_archivo(" / ")


def test_parsear_presiones():
    assert cfg.parsear_presiones_kPa("980, 683; 484") == [980e3, 683e3, 484e3]
    with pytest.raises(ValueError):
        cfg.parsear_presiones_kPa("100, -5")


def test_formulario_ida_y_vuelta():
    # caso -> formulario (MPa, kPa) -> caso: debe quedar igual
    caso = cfg.leer_json(texto_caso())
    otra_vez = cfg.construir_caso(cfg.valores_formulario(caso))
    assert otra_vez["camara"] == pytest.approx(caso["camara"])
    assert otra_vez["presiones_exteriores_Pa"] == pytest.approx(caso["presiones_exteriores_Pa"])
    assert otra_vez["ambiente"] == caso["ambiente"]
    assert otra_vez["geometria"] == caso["geometria"]


def test_guardar_caso_no_sobrescribe_sin_permiso(tmp_path):
    caso = cfg.leer_json(texto_caso())
    ruta = cfg.guardar_caso(caso, tmp_path)
    assert json.loads(ruta.read_text(encoding="utf-8"))["nombre"] == "caso_prueba"
    with pytest.raises(FileExistsError):
        cfg.guardar_caso(caso, tmp_path)
    cfg.guardar_caso(caso, tmp_path, sobrescribir=True)


def test_geometria_preliminar():
    pre = cfg.geometria_preliminar(cfg.leer_json(texto_caso()))
    assert pre["diseno"]["Dt"] * 1e3 == pytest.approx(9.91, abs=0.01)
    assert len(pre["x"]) == len(pre["r"]) > 100


def test_ejecutar_en_carpeta_temporal(tmp_path):
    r = cfg.ejecutar(cfg.leer_json(texto_caso()), tmp_path)
    assert (tmp_path / "caso_prueba" / "contorno.dxf").exists()
    assert r["resumen"].startswith("TOBERA-CD")


def test_parsear_resumen():
    caso = leer_caso(CASO)
    res = correr(caso)
    datos = parsear_resumen(resumen(caso, res))
    assert datos["nombre"] == "caso_prueba"
    nombres = [v["nombre"] for v in datos["dimensionamiento"]]
    assert "Diámetro de garganta D*" in nombres
    assert len(datos["analisis"]) == len(res["analisis"])
    con_choque = [a for a in datos["analisis"] if a["choque"]]
    assert con_choque[0]["choque"]["x_mm"] == pytest.approx(
        res["analisis"][1]["x_choque_mm"], abs=0.01)


def test_parsear_resumen_invalido():
    with pytest.raises(ValueError):
        parsear_resumen("otro archivo")
