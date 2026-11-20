"""
Pruebas de comparacion.py: lectura de CSV de Flow Simulation, detección de
columnas, alineación del eje x y cálculo del error.
"""
import numpy as np
import pytest

import comparacion as cmp

GEO = {"x_entrada": -0.030, "x_salida": 0.010}  # tobera de -30 a 10 mm


# ---------------------------------------------------------------------
# Lectura del CSV
# ---------------------------------------------------------------------

def test_csv_coma_y_punto_decimal():
    t = cmp.leer_csv_solidworks("X [m],Pressure [Pa],Mach Number\n0,100000,0.1\n0.01,90000,0.5\n")
    assert list(t.columns) == ["X [m]", "Pressure [Pa]", "Mach Number"]
    assert t.shape == (2, 3)
    assert t["Pressure [Pa]"].tolist() == [100000, 90000]


def test_csv_punto_y_coma_con_coma_decimal_y_titulos():
    texto = ("XY Plot 1\nModelo: tobera.SLDPRT\n\n"
             "Curve Length [m];Pressure [Pa];Mach Number [ ]\n"
             "0,000;1000000,5;0,05\n0,010;950000,25;0,30\n")
    t = cmp.leer_csv_solidworks(texto.encode("cp1252"))
    assert t.shape == (2, 3)
    assert t.iloc[1, 0] == pytest.approx(0.010)
    assert t.iloc[0, 1] == pytest.approx(1000000.5)


def test_csv_tabuladores_sin_encabezado():
    t = cmp.leer_csv_solidworks("0\t1\t2\n1\t3\t4\n")
    assert list(t.columns) == ["col_1", "col_2", "col_3"]


def test_csv_descarta_filas_de_resumen():
    texto = "x [mm],p [Pa]\n0,1\n1,2\n2,3\nPromedio,2\n5\n"
    assert len(cmp.leer_csv_solidworks(texto)) == 3


def test_csv_sin_datos_numericos():
    with pytest.raises(ValueError):
        cmp.leer_csv_solidworks("solo\ntexto\n")


# ---------------------------------------------------------------------
# Columnas y unidades
# ---------------------------------------------------------------------

@pytest.mark.parametrize("columnas, esperado", [
    (["X [m]", "Pressure [Pa]", "Mach Number [ ]"],
     {"x": "X [m]", "p": "Pressure [Pa]", "M": "Mach Number [ ]"}),
    (["Longitud de curva [m]", "Presión total [Pa]", "Presión estática [Pa]", "Número de Mach"],
     {"x": "Longitud de curva [m]", "p": "Presión estática [Pa]", "M": "Número de Mach"}),
    (["a", "b"], {"x": "a", "p": None, "M": None}),
])
def test_detectar_columnas(columnas, esperado):
    assert cmp.detectar_columnas(columnas) == esperado


@pytest.mark.parametrize("nombre, opciones, esperado", [
    ("Pressure [kPa]", list(cmp.A_PA), "kPa"),
    ("X (mm)", list(cmp.A_MM), "mm"),
    ("Mach Number", list(cmp.A_PA), None),
])
def test_unidad_en_nombre(nombre, opciones, esperado):
    assert cmp.unidad_en_nombre(nombre, opciones) == esperado


# ---------------------------------------------------------------------
# Alineación y comparación
# ---------------------------------------------------------------------

@pytest.mark.parametrize("origen, x_csv, esperado", [
    ("garganta", [0.0, 5.0], [0.0, 5.0]),
    ("entrada", [0.0, 40.0], [-30.0, 10.0]),
    ("salida", [-40.0, 0.0], [-30.0, 10.0]),
    ("extremos", [12.0, 52.0], [-30.0, 10.0]),
])
def test_alinear_x(origen, x_csv, esperado):
    assert cmp.alinear_x(x_csv, GEO, origen) == pytest.approx(esperado)


def test_alinear_x_invertido_y_desplazado():
    # Flujo en -x con el origen en la garganta, y 1 mm de corrección
    assert cmp.alinear_x([0.0, -5.0], GEO, "garganta", invertir=True,
                         desplazamiento_mm=1.0) == pytest.approx([1.0, 6.0])


def test_comparar_datos_identicos():
    x = np.linspace(-30, 10, 50)
    y = 1 + x**2
    comp = cmp.comparar(x, y, x, y)
    assert comp["metricas"]["rmse"] == pytest.approx(0.0, abs=1e-12)
    assert comp["metricas"]["cobertura_pct"] == pytest.approx(100.0)


def test_comparar_error_conocido():
    # SolidWorks 2 % arriba del código en todos los puntos
    x = np.linspace(-30, 10, 50)
    y = np.full_like(x, 100.0)
    comp = cmp.comparar(x, y, x, 1.02 * y)
    # error % = (código − SW)/|SW|·100 = (100 − 102)/102·100 ≈ −1.96 %
    assert comp["metricas"]["error_medio_pct"] == pytest.approx(2 / 1.02)
    assert np.allclose(comp["diferencia"], -2.0)


def test_comparar_solo_donde_hay_csv():
    # El CSV cubre la mitad de la tobera: no se extrapola fuera de ese tramo
    x = np.linspace(-30, 10, 41)
    comp = cmp.comparar(x, x, np.array([-10.0, 10.0]), np.array([-10.0, 10.0]))
    assert comp["x"].min() == pytest.approx(-10.0)
    assert comp["metricas"]["cobertura_pct"] == pytest.approx(50.0)


def test_comparar_sin_traslape():
    x = np.linspace(-30, 10, 41)
    with pytest.raises(ValueError, match="traslapa"):
        cmp.comparar(x, x, np.array([100.0, 200.0]), np.array([1.0, 2.0]))


def test_tabla_comparacion():
    x = np.linspace(0, 1, 5)
    comp = cmp.comparar(x, x, x, x)
    tabla = cmp.tabla_comparacion({"M": comp})
    assert list(tabla.columns) == ["x_mm", "M_codigo", "M_solidworks", "M_diferencia", "M_error_pct"]
    assert len(tabla) == 5


def test_validacion_de_punta_a_punta():
    # CSV sintético a partir del propio modelo, con el formato de Flow Simulation
    from main import correr, leer_caso
    from pathlib import Path
    res = correr(leer_caso(Path(__file__).parent / "datos" / "caso_prueba.json"))
    d = next(d for d in res["distribuciones"] if d["pb"] == 683000)
    xs = np.linspace(res["x"][0], res["x"][-1], 120)
    p = np.interp(xs, res["x"], d["p"])
    lineas = ["Curve Length [m];Pressure [Pa]"] + [
        f"{a:.7f};{b:.3f}".replace(".", ",") for a, b in zip(xs - xs[0], p)]
    t = cmp.leer_csv_solidworks("\n".join(lineas))
    x_sw = cmp.alinear_x(t["Curve Length [m]"].to_numpy() * cmp.A_MM["m"],
                         res["geometria"], "extremos")
    comp = cmp.comparar(res["x"] * 1e3, d["p"], x_sw, t["Pressure [Pa]"].to_numpy())
    # Lejos del choque coinciden; el error grande queda junto al choque
    lejos = np.abs(comp["x"] - d["x_choque"] * 1e3) > 0.5
    assert np.nanmax(np.abs(comp["error_pct"][lejos])) < 1.0
    assert abs(comp["metricas"]["x_dif_max_mm"] - d["x_choque"] * 1e3) < 0.5
