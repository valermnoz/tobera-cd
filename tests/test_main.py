"""
Pruebas del flujo completo (main.py e interactivo.py) con el caso preliminar.
"""
import json
from pathlib import Path

import numpy as np
import pytest

import interactivo
from main import completar_caso, correr, guardar, leer_caso, presiones_a_analizar

# Copia fija del caso preliminar: la interfaz puede sobrescribir los de casos/
CASO = Path(__file__).parent / "datos" / "caso_prueba.json"


@pytest.fixture(scope="module")
def res():
    return correr(leer_caso(CASO))


def test_distribucion_geometria_real_choque(res):
    a = next(a for a in res["analisis"] if a["pb_Pa"] == 683000)
    d = next(d for d in res["distribuciones"] if d["pb"] == 683000)
    assert a["regimen"] == "choque_interno"
    # El choque queda en el divergente, dentro de la tobera
    assert 0 < a["x_choque_mm"] < res["geometria"]["L_divergente"] * 1e3
    # El área en esa posición corresponde a A/A* del choque
    r_s = np.interp(d["x_choque"], res["x"], res["r"])
    assert (r_s / res["r"].min()) ** 2 == pytest.approx(a["choque"]["As_At"], rel=1e-3)
    # La salida subsónica descarga a la presión exterior
    assert d["p"][-1] == pytest.approx(683000, rel=1e-3)


def test_distribucion_geometria_real_adaptada(res):
    pa = leer_caso(CASO)["pa_Pa"]
    d = next(d for d in res["distribuciones"] if d["pb"] == pa)
    i_g = int(np.argmin(res["r"]))
    assert d["M"][i_g] == pytest.approx(1.0, abs=1e-9)
    assert d["p"][-1] == pytest.approx(pa, rel=1e-6)
    assert d["M"][-1] == pytest.approx(res["diseno"]["Me"], rel=1e-6)


def test_presiones_automaticas():
    caso = leer_caso(CASO)
    caso["presiones_exteriores_Pa"] = "auto"
    r = correr(caso)
    regimenes = {a["regimen"] for a in r["analisis"]}
    assert {"subsonico", "choque_interno", "sobreexpandida", "adaptada",
            "subexpandida"} <= regimenes


def test_guardar_genera_archivos(res, tmp_path):
    guardar(leer_caso(CASO), res, tmp_path)
    for nombre in ("resumen.txt", "resultados.json", "distribucion.csv", "contorno.dxf",
                   "contorno_xyz.txt", "dimensiones.txt", "contorno.png",
                   "presiones.png", "mach.png"):
        assert (tmp_path / nombre).stat().st_size > 0
    tabla = np.genfromtxt(tmp_path / "distribucion.csv", delimiter=",", names=True)
    assert len(tabla) == len(res["x"])
    assert "M_6830kPa" in tabla.dtype.names  # genfromtxt quita el punto del nombre


def test_modo_interactivo(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    respuestas = iter([
        "",            # crear caso nuevo
        "prueba",      # nombre
        "",            # descripción
        "2",           # p0 [MPa]
        "",            # T0
        "",            # aire
        "n",           # no por altitud
        "101.325",     # pa [kPa]
        "250",         # empuje
        "",            # presiones automáticas
        "",            # geometría por defecto
    ])
    monkeypatch.setattr("builtins.input", lambda _: next(respuestas))
    caso = interactivo.preguntar_caso()
    assert caso["camara"]["p0_Pa"] == 2e6
    assert caso["ambiente"]["pa_Pa"] == pytest.approx(101325)
    assert json.loads((tmp_path / "casos" / "prueba.json").read_text(encoding="utf-8"))
    r = correr(completar_caso(caso))
    assert r["diseno"]["Me"] > 2.0


def test_caso_con_unidades_equivocadas():
    caso = leer_caso(CASO)
    caso["camara"]["p0_Pa"] = 5.0e12  # 5e6 "MPa" escrito por error
    with pytest.raises(ValueError, match="unidades"):
        completar_caso(caso)


def test_interactivo_rechaza_presion_en_pascales(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    respuestas = iter(["", "x", "", "5.0e6", "5", "", "", "", "", "", "", ""])
    monkeypatch.setattr("builtins.input", lambda _: next(respuestas))
    caso = interactivo.preguntar_caso()
    assert caso["camara"]["p0_Pa"] == 5e6  # el 5.0e6 se rechazó y se aceptó el 5
