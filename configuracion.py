"""
configuracion.py — Casos .json para la interfaz gráfica.

Funciones sin dependencia de la interfaz para listar, leer, armar, guardar,
previsualizar y ejecutar casos. El cálculo es el mismo de main.py.

Los .json usan unidades SI (Pa, K, N, mm en la geometría); el formulario
usa MPa para p0 y kPa para pa y las presiones exteriores, como el modo
interactivo.
"""

import copy
import json
import re
from pathlib import Path

from geometria import GEOMETRIA_DEFECTO, contorno, muestrear, resumen_geometria
from main import completar_caso, correr, guardar, parametros_geometria
from tobera import dimensionar

DIR_CASOS = Path("casos")
DIR_SALIDAS = Path("salidas")

CLAVES_OBLIGATORIAS = ("nombre", "gas", "camara", "ambiente", "empuje_requerido_N")

# Mismos valores por defecto que interactivo.py
CASO_NUEVO = {
    "nombre": "mi_caso",
    "descripcion": "",
    "gas": {"gamma": 1.4, "R": 287.0},
    "camara": {"p0_Pa": 1.0e6, "T0_K": 300.0},
    "ambiente": {"altitud_m": 1820.0},
    "empuje_requerido_N": 100.0,
    "geometria": dict(GEOMETRIA_DEFECTO),
    "presiones_exteriores_Pa": "auto",
}


# ---------------------------------------------------------------------
# Lectura y escritura
# ---------------------------------------------------------------------

def listar_casos(directorio=DIR_CASOS):
    """Rutas de los .json del directorio de casos, en orden alfabético."""
    return sorted(Path(directorio).glob("*.json"))


def leer_json(texto):
    """
    Caso a partir del texto de un .json (sin completar). Revisa que estén
    las secciones obligatorias para dar un error claro desde el principio.
    """
    try:
        caso = json.loads(texto)
    except json.JSONDecodeError as e:
        raise ValueError(f"El archivo no es un JSON válido: {e}") from e
    if not isinstance(caso, dict):
        raise ValueError("El JSON debe ser un objeto con los datos del caso.")
    faltan = [k for k in CLAVES_OBLIGATORIAS if k not in caso]
    if faltan:
        raise ValueError("Al caso le faltan las claves: " + ", ".join(faltan))
    amb = caso["ambiente"]
    if not (amb.get("pa_Pa") or "altitud_m" in amb):
        raise ValueError('En "ambiente" debe ir "altitud_m" o "pa_Pa".')
    return caso


def nombre_archivo(nombre):
    """Nombre seguro para casos/<nombre>.json y salidas/<nombre>/."""
    limpio = re.sub(r"[^\w\-]+", "_", nombre.strip()).strip("_")
    if not limpio:
        raise ValueError("El nombre del caso no puede quedar vacío.")
    return limpio


def guardar_caso(caso, directorio=DIR_CASOS, sobrescribir=False):
    """Escribe el caso en <directorio>/<nombre>.json y devuelve la ruta."""
    ruta = Path(directorio) / f"{nombre_archivo(caso['nombre'])}.json"
    if ruta.exists() and not sobrescribir:
        raise FileExistsError(f"{ruta} ya existe.")
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(json.dumps(caso, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return ruta


def caso_a_json(caso):
    return json.dumps(caso, indent=2, ensure_ascii=False) + "\n"


# ---------------------------------------------------------------------
# Formulario  <->  caso
# ---------------------------------------------------------------------

def parsear_presiones_kPa(texto):
    """'980, 683; 484' -> [980000.0, 683000.0, 484000.0] (Pa)."""
    valores = [v for v in re.split(r"[;,\s]+", texto) if v]
    if not valores:
        raise ValueError('Escribe las presiones exteriores en kPa o "auto".')
    try:
        presiones = [float(v) * 1e3 for v in valores]
    except ValueError as e:
        raise ValueError(f"Presión exterior no válida: {e}") from e
    if any(p <= 0 for p in presiones):
        raise ValueError("Las presiones exteriores deben ser positivas.")
    return presiones


def valores_formulario(caso):
    """Valores del caso en las unidades del formulario."""
    amb = caso["ambiente"]
    pb = caso.get("presiones_exteriores_Pa", "auto")
    geo = {k: v if isinstance(v, str) else float(v)
           for k, v in {**GEOMETRIA_DEFECTO, **caso.get("geometria", {})}.items()}
    return {
        "nombre": caso["nombre"],
        "descripcion": caso.get("descripcion", ""),
        "gamma": float(caso["gas"]["gamma"]),
        "R": float(caso["gas"]["R"]),
        "p0_MPa": caso["camara"]["p0_Pa"] / 1e6,
        "T0_K": float(caso["camara"]["T0_K"]),
        "por_altitud": not amb.get("pa_Pa"),
        "altitud_m": float(amb.get("altitud_m", 1820.0)),
        "pa_kPa": (amb.get("pa_Pa") or 101325.0) / 1e3,
        "F_N": float(caso["empuje_requerido_N"]),
        "pb_kPa": "auto" if pb == "auto" else ", ".join(f"{p/1e3:g}" for p in pb),
        "geometria": geo,
    }


def construir_caso(v):
    """Caso .json (unidades SI) a partir de los valores del formulario."""
    ambiente = ({"altitud_m": v["altitud_m"]} if v["por_altitud"]
                else {"pa_Pa": v["pa_kPa"] * 1e3})
    return {
        "nombre": nombre_archivo(v["nombre"]),
        "descripcion": v["descripcion"],
        "gas": {"gamma": v["gamma"], "R": v["R"]},
        "camara": {"p0_Pa": v["p0_MPa"] * 1e6, "T0_K": v["T0_K"]},
        "ambiente": ambiente,
        "empuje_requerido_N": v["F_N"],
        "geometria": dict(v["geometria"]),
        "presiones_exteriores_Pa": ("auto" if v["pb_kPa"].strip().lower() in ("", "auto")
                                    else parsear_presiones_kPa(v["pb_kPa"])),
    }


# ---------------------------------------------------------------------
# Cálculo
# ---------------------------------------------------------------------

def geometria_preliminar(caso):
    """
    Dimensionamiento y contorno sin analizar las presiones exteriores
    (es rápido, sirve para la vista previa mientras se edita el caso).
    """
    caso = completar_caso(copy.deepcopy(caso))
    g, R = caso["gas"]["gamma"], caso["gas"]["R"]
    diseno = dimensionar(caso["camara"]["p0_Pa"], caso["camara"]["T0_K"], caso["pa_Pa"],
                         caso["empuje_requerido_N"], g, R)
    tramos = contorno(diseno["Dt"], diseno["De"], **parametros_geometria(caso))
    x, r = muestrear(tramos)
    return {
        "caso": caso,
        "diseno": diseno,
        "tramos": tramos,
        "geometria": resumen_geometria(tramos),
        "x": x,
        "r": r,
    }


def ejecutar(caso, dir_salidas=DIR_SALIDAS):
    """
    Corre el caso completo como main.py y guarda todas las salidas en
    <dir_salidas>/<nombre>/. Devuelve el caso completado, los resultados,
    la carpeta de salida y el texto de resumen.txt.
    """
    completo = completar_caso(copy.deepcopy(caso))
    res = correr(completo)
    salida = Path(dir_salidas) / nombre_archivo(completo["nombre"])
    guardar(completo, res, salida)
    return {
        "caso": completo,
        "res": res,
        "salida": salida,
        "resumen": (salida / "resumen.txt").read_text(encoding="utf-8"),
    }
