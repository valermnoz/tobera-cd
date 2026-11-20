"""
comparacion.py — Validación contra SolidWorks Flow Simulation.

  leer_csv_solidworks():  tabla numérica de un .csv exportado de Flow Simulation
                          (separador , ; o tabulador, punto o coma decimal,
                          líneas de título antes del encabezado)
  detectar_columnas():    adivina las columnas de x, presión y Mach
  unidad_en_nombre():     unidad escrita en el encabezado, p. ej. "Pressure [Pa]"
  alinear_x():            lleva la coordenada del CSV al eje del modelo
                          (garganta en x = 0, en mm)
  comparar():             interpola SolidWorks en los nodos del modelo y
                          calcula la diferencia y el error porcentual

Convención: diferencia = código − SolidWorks y
error % = (código − SolidWorks) / |SolidWorks| · 100, con SolidWorks como
referencia.
"""

import re

import numpy as np
import pandas as pd

# Factores de conversión a las unidades del modelo en la interfaz
A_MM = {"m": 1e3, "mm": 1.0, "cm": 10.0, "in": 25.4}
A_PA = {"Pa": 1.0, "kPa": 1e3, "MPa": 1e6, "bar": 1e5, "atm": 101325.0, "psi": 6894.757}

ORIGENES = {
    "garganta": "x = 0 del CSV en la garganta (modelo hecho con contorno.dxf)",
    "entrada": "x = 0 del CSV en el plano de entrada",
    "salida": "x = 0 del CSV en el plano de salida",
    "extremos": "primer punto del CSV en el plano de entrada",
}

_SEPARADORES = ("\t", ";", ",")


# ---------------------------------------------------------------------
# Lectura del CSV
# ---------------------------------------------------------------------

def _decodificar(datos):
    if isinstance(datos, str):
        return datos
    for codificacion in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            return datos.decode(codificacion)
        except UnicodeDecodeError:
            continue
    raise ValueError("No se pudo leer el archivo como texto.")


def _numero(campo, decimal):
    """float del campo; NaN si está vacío; None si no es un número."""
    campo = campo.strip().strip('"').strip()
    if campo == "":
        return np.nan
    if decimal == ",":
        campo = campo.replace(",", ".")
    try:
        return float(campo)
    except ValueError:
        return None


def _es_fila_numerica(campos, decimal):
    valores = [_numero(c, decimal) for c in campos]
    return (all(v is not None for v in valores)
            and any(not np.isnan(v) for v in valores)), valores


def _formato(lineas):
    """Separador y signo decimal que dan más filas numéricas con más columnas."""
    mejor, puntaje_mejor = None, (0, 0)
    for sep in _SEPARADORES:
        for decimal in (".", ","):
            if sep == "," and decimal == ",":
                continue
            filas = [l.split(sep) for l in lineas]
            n_num = [len(f) for f in filas if len(f) > 1 and _es_fila_numerica(f, decimal)[0]]
            if not n_num:
                continue
            puntaje = (len(n_num), max(set(n_num), key=n_num.count))
            if puntaje > puntaje_mejor:
                mejor, puntaje_mejor = (sep, decimal), puntaje
    if mejor is None:
        raise ValueError("No se encontraron filas numéricas con al menos dos columnas.")
    return mejor


def leer_csv_solidworks(datos):
    """
    Tabla numérica (DataFrame) de un CSV de Flow Simulation.

    El encabezado es la última línea no numérica antes de los datos; si no
    hay, las columnas se llaman col_1, col_2, ... Las filas numéricas con
    otro número de columnas (resúmenes al final, etc.) se descartan.
    """
    lineas = [l for l in _decodificar(datos).splitlines() if l.strip()]
    sep, decimal = _formato(lineas)

    filas, encabezado, n_col = [], None, None
    previa = None
    for linea in lineas:
        campos = linea.split(sep)
        es_num, valores = _es_fila_numerica(campos, decimal)
        if es_num and len(campos) > 1:
            if n_col is None:
                n_col = len(campos)
                if previa is not None and len(previa) == n_col:
                    encabezado = previa
            if len(campos) == n_col:
                filas.append(valores)
        elif n_col is None:
            previa = [c.strip().strip('"').strip() for c in campos]

    nombres, vistos = [], {}
    for i in range(n_col):
        nombre = (encabezado[i] if encabezado else "") or f"col_{i + 1}"
        if nombre in vistos:
            vistos[nombre] += 1
            nombre = f"{nombre} ({vistos[nombre]})"
        else:
            vistos[nombre] = 0
        nombres.append(nombre)

    tabla = pd.DataFrame(filas, columns=nombres, dtype=float)
    return tabla.dropna(axis=1, how="all")


# ---------------------------------------------------------------------
# Columnas y unidades
# ---------------------------------------------------------------------

def _puntaje(nombre, variable):
    n = nombre.lower()
    if variable == "x":
        if re.search(r"(^|[^a-z])x([^a-z]|$)", n):
            return 3
        if any(k in n for k in ("curve length", "longitud", "length", "distan", "arc length")):
            return 2
        return 0
    if variable == "p":
        if "pres" not in n:
            return 0
        if any(k in n for k in ("total", "dynamic", "dinámica", "dinamica", "relative", "relativa")):
            return 1
        return 3 if any(k in n for k in ("static", "estática", "estatica")) else 2
    if variable == "M":
        return 3 if "mach" in n else 0
    raise ValueError(variable)


def detectar_columnas(columnas):
    """{"x": nombre o None, "p": ..., "M": ...} según los encabezados."""
    elegidas = {}
    for variable in ("x", "p", "M"):
        puntajes = [(_puntaje(c, variable), -i, c) for i, c in enumerate(columnas)]
        mejor = max(puntajes, default=(0, 0, None))
        elegidas[variable] = mejor[2] if mejor[0] > 0 else None
    if elegidas["x"] is None and columnas:
        elegidas["x"] = columnas[0]  # Flow Simulation exporta la coordenada primero
    return elegidas


def unidad_en_nombre(nombre, opciones):
    """Unidad entre [] o () en el encabezado si está en 'opciones', o None."""
    for u in reversed(re.findall(r"[\[\(]\s*([^\]\)]*?)\s*[\]\)]", nombre or "")):
        for opcion in opciones:
            if u.lower() == opcion.lower():
                return opcion
    return None


# ---------------------------------------------------------------------
# Alineación y comparación
# ---------------------------------------------------------------------

def alinear_x(x_csv_mm, geo, origen="garganta", invertir=False, desplazamiento_mm=0.0):
    """
    Coordenada del CSV (ya en mm) en el eje del modelo: garganta en x = 0
    y el flujo en +x.

    geo:      resumen de la geometría (x_entrada, x_salida en m)
    origen:   dónde está el x = 0 del CSV (ver ORIGENES)
    invertir: True si en SolidWorks el flujo va en −x
    desplazamiento_mm: corrección adicional que se suma al final
    """
    x = -np.asarray(x_csv_mm, dtype=float) if invertir else np.asarray(x_csv_mm, dtype=float)
    if origen == "garganta":
        x0 = 0.0
    elif origen == "entrada":
        x0 = geo["x_entrada"] * 1e3
    elif origen == "salida":
        x0 = geo["x_salida"] * 1e3
    elif origen == "extremos":
        x0 = geo["x_entrada"] * 1e3 - np.nanmin(x)
    else:
        raise ValueError(f"Origen desconocido: {origen}")
    return x + x0 + desplazamiento_mm


def _limpiar(x, y):
    """Quita NaN, ordena por x y promedia los valores con la misma x."""
    x, y = np.asarray(x, dtype=float), np.asarray(y, dtype=float)
    ok = np.isfinite(x) & np.isfinite(y)
    if ok.sum() < 2:
        raise ValueError("El CSV necesita al menos dos puntos válidos para interpolar.")
    serie = pd.Series(y[ok]).groupby(x[ok]).mean()
    return serie.index.to_numpy(), serie.to_numpy()


def comparar(x_modelo_mm, y_modelo, x_sw_mm, y_sw):
    """
    Interpola linealmente los datos de SolidWorks en los nodos del modelo
    que caen dentro del tramo cubierto por el CSV (no se extrapola).

    Devuelve un diccionario con x [mm], codigo, solidworks, diferencia,
    error_pct y las métricas globales.
    """
    xs, ys = _limpiar(x_sw_mm, y_sw)
    xm, ym = np.asarray(x_modelo_mm, dtype=float), np.asarray(y_modelo, dtype=float)
    tol = 1e-6 * max(1.0, xs[-1] - xs[0])  # redondeo al convertir unidades
    dentro = (xm >= xs[0] - tol) & (xm <= xs[-1] + tol)
    if dentro.sum() < 2:
        raise ValueError(
            f"El CSV ({xs[0]:.2f} a {xs[-1]:.2f} mm) casi no se traslapa con la tobera "
            f"({xm.min():.2f} a {xm.max():.2f} mm): revisa el origen y las unidades de x."
        )

    x, codigo = xm[dentro], ym[dentro]
    sw = np.interp(x, xs, ys)
    dif = codigo - sw
    with np.errstate(divide="ignore", invalid="ignore"):
        err = np.where(np.abs(sw) > 1e-12, dif / np.abs(sw) * 100.0, np.nan)

    i_max = int(np.nanargmax(np.abs(dif)))
    metricas = {
        "n_nodos": int(dentro.sum()),
        "n_puntos_csv": int(len(xs)),
        "x_min_mm": float(x[0]),
        "x_max_mm": float(x[-1]),
        "cobertura_pct": float(100.0 * (x[-1] - x[0]) / (xm.max() - xm.min())),
        "rmse": float(np.sqrt(np.mean(dif**2))),
        "mae": float(np.mean(np.abs(dif))),
        "dif_max": float(dif[i_max]),
        "x_dif_max_mm": float(x[i_max]),
        "error_medio_pct": float(np.nanmean(np.abs(err))),
        "error_max_pct": float(np.nanmax(np.abs(err))),
    }
    return {
        "x": x,
        "codigo": codigo,
        "solidworks": sw,
        "diferencia": dif,
        "error_pct": err,
        "x_csv": xs,
        "y_csv": ys,
        "metricas": metricas,
    }


def tabla_comparacion(comparaciones):
    """
    Tabla para descargar: x_mm y, por variable, código, SolidWorks,
    diferencia y error %. comparaciones = {"p_kPa": comp, "M": comp}.
    """
    tablas = []
    for nombre, c in comparaciones.items():
        tablas.append(pd.DataFrame({
            "x_mm": c["x"],
            f"{nombre}_codigo": c["codigo"],
            f"{nombre}_solidworks": c["solidworks"],
            f"{nombre}_diferencia": c["diferencia"],
            f"{nombre}_error_pct": c["error_pct"],
        }).set_index("x_mm"))
    return pd.concat(tablas, axis=1).sort_index().reset_index()
