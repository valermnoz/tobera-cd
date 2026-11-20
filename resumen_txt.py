"""
resumen_txt.py — Lectura de salidas/<caso>/resumen.txt.

Convierte el texto que escribe main.resumen() en un diccionario para
mostrarlo como tarjetas y tablas en la interfaz gráfica:

  {
    "nombre": ..., "descripcion": ...,
    "dimensionamiento": [valor, ...],
    "geometria":        [valor, ...],
    "criticas":         [valor, ...],
    "analisis":         [fila, ...],
  }

Cada valor es {"etiqueta", "nombre", "detalle", "valor", "texto", "unidad"};
"texto" conserva los decimales del archivo. Cada fila del análisis trae
pb_kPa, regimen, Me, m_kg_s, F_N y, si hay choque interno, "choque" con
x_mm, As_At, M1, M2 y p02_p01.
"""

import re

SECCIONES = {
    "DIMENSIONAMIENTO": "dimensionamiento",
    "GEOMETRÍA": "geometria",
    "PRESIONES CRÍTICAS": "criticas",
    "ANÁLISIS POR PRESIÓN EXTERIOR": "analisis",
}

_NUM = r"-?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?"
_RE_VALOR = re.compile(rf"^(?P<etiqueta>.+?)\s+(?P<valor>{_NUM})(?:\s+(?P<unidad>\S+))?$")
_RE_FILA = re.compile(
    rf"^(?P<pb>{_NUM})\s+(?P<regimen>.+?)\s+(?P<Me>{_NUM})\s+(?P<m>{_NUM})\s+(?P<F>{_NUM})$"
)
_RE_CHOQUE = re.compile(
    rf"choque en x = (?P<x_mm>{_NUM}) mm \(A/A\* = (?P<As_At>{_NUM})\): "
    rf"M1 = (?P<M1>{_NUM}) -> M2 = (?P<M2>{_NUM}), p02/p01 = (?P<p02_p01>{_NUM})"
)


def _valor(linea):
    """'Diámetro de garganta D*  9.91 mm' -> diccionario, o None si no es un valor."""
    m = _RE_VALOR.match(linea)
    if not m:
        return None
    etiqueta = m["etiqueta"].strip()
    nombre, _, resto = etiqueta.partition(" (")
    return {
        "etiqueta": etiqueta,
        "nombre": nombre.strip(),
        "detalle": resto.rstrip(")").strip(),
        "valor": float(m["valor"]),
        "texto": m["valor"],
        "unidad": m["unidad"] or "",
    }


def parsear_resumen(texto):
    """Lee el contenido de un resumen.txt de TOBERA-CD."""
    lineas = texto.splitlines()
    if not lineas or not lineas[0].startswith("TOBERA-CD"):
        raise ValueError("El archivo no parece un resumen.txt de TOBERA-CD.")

    datos = {
        "nombre": lineas[0].split("·", 1)[-1].strip(),
        # main.resumen() siempre escribe la descripción en la segunda línea
        "descripcion": lineas[1].strip() if len(lineas) > 1 else "",
        **{clave: [] for clave in SECCIONES.values()},
    }

    seccion = None
    for linea in lineas[2:]:
        if not linea.strip():
            continue
        if not linea.startswith(" "):
            # Encabezado de sección (las secciones desconocidas se ignoran)
            seccion = next((c for t, c in SECCIONES.items() if linea.startswith(t)), None)
            continue
        contenido = linea.strip()
        if seccion == "analisis":
            ch = _RE_CHOQUE.search(contenido)
            fila = _RE_FILA.match(contenido)
            if ch and datos["analisis"]:
                datos["analisis"][-1]["choque"] = {k: float(v) for k, v in ch.groupdict().items()}
            elif fila:
                datos["analisis"].append({
                    "pb_kPa": float(fila["pb"]),
                    "regimen": fila["regimen"].strip(),
                    "Me": float(fila["Me"]),
                    "m_kg_s": float(fila["m"]),
                    "F_N": float(fila["F"]),
                    "choque": None,
                })
        elif seccion is not None:
            v = _valor(contenido)
            if v:
                datos[seccion].append(v)

    if not any(datos[c] for c in SECCIONES.values()):
        raise ValueError("No se encontró ninguna sección de resultados en el resumen.")
    return datos
