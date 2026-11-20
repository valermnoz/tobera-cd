"""
interactivo.py — Modo interactivo de TOBERA-CD en la terminal.

Pregunta los datos del caso uno por uno (Enter acepta el valor por
defecto entre paréntesis) y guarda el caso en casos/<nombre>.json para
poder repetirlo con:  python main.py casos/<nombre>.json
"""

import json
from pathlib import Path

from geometria import GEOMETRIA_DEFECTO

DESCRIPCION_GEOMETRIA = {
    "angulo_convergente_deg": "Semiángulo del convergente [°]",
    "angulo_divergente_deg": "Semiángulo del divergente [°]",
    "relacion_contraccion": "Relación de contracción A_entrada/A*",
    "longitud_recta_entrada_mm": "Longitud del tramo recto de entrada [mm]",
    "radio_arco_entrada_rt": "Radio del arco de entrada [múltiplos de r*]",
    "radio_garganta_arriba_rt": "Radio de garganta aguas arriba [múltiplos de r*]",
    "radio_garganta_abajo_rt": "Radio de garganta aguas abajo [múltiplos de r*]",
    "espesor_pared_mm": "Espesor de pared [mm]",
}


def preguntar(texto, defecto, tipo=float, minimo=None):
    """Pregunta un valor; Enter devuelve el valor por defecto."""
    while True:
        resp = input(f"{texto} ({defecto}): ").strip()
        if resp == "":
            return defecto
        try:
            valor = tipo(resp.replace(",", ".")) if tipo is float else tipo(resp)
        except ValueError:
            print("  Valor no válido, intenta de nuevo.")
            continue
        if minimo is not None and valor <= minimo:
            print(f"  Debe ser mayor que {minimo}.")
            continue
        return valor


def preguntar_si(texto, defecto=False):
    opciones = "S/n" if defecto else "s/N"
    resp = input(f"{texto} ({opciones}): ").strip().lower()
    return defecto if resp == "" else resp.startswith("s")


def preguntar_caso():
    print("\nTOBERA-CD · modo interactivo (Enter acepta el valor entre paréntesis)\n")

    ruta = input("Ruta de un caso guardado (Enter para crear uno nuevo): ").strip()
    if ruta:
        with open(ruta, encoding="utf-8") as f:
            return json.load(f)

    nombre = preguntar("Nombre del caso", "mi_caso", str)
    descripcion = preguntar("Descripción breve", "", str)

    print("\nCámara")
    p0 = preguntar("  Presión de cámara p0 [MPa]", 1.0, minimo=0) * 1e6
    T0 = preguntar("  Temperatura de cámara T0 [K]", 300.0, minimo=0)

    print("\nGas")
    if preguntar_si("  ¿Usar aire (gamma = 1.4, R = 287 J/kg·K)?", defecto=True):
        gamma, R = 1.4, 287.0
    else:
        gamma = preguntar("  gamma", 1.2, minimo=1.0)
        R = preguntar("  R [J/kg·K]", 300.0, minimo=0)

    print("\nAmbiente")
    if preguntar_si("  ¿Definir por altitud (atmósfera estándar)?", defecto=True):
        ambiente = {"altitud_m": preguntar("  Altitud [m]", 1820.0)}
    else:
        ambiente = {"pa_Pa": preguntar("  Presión ambiente [kPa]", 101.325, minimo=0) * 1e3}

    print("\nDiseño")
    F = preguntar("  Empuje requerido [N]", 100.0, minimo=0)

    texto = input("  Presiones exteriores a analizar en kPa, separadas por comas "
                  "(Enter = una por régimen): ").strip()
    if texto:
        presiones = [float(v) * 1e3 for v in texto.replace(";", ",").split(",") if v.strip()]
    else:
        presiones = "auto"

    geometria = dict(GEOMETRIA_DEFECTO)
    if preguntar_si("\n¿Modificar la geometría por defecto?"):
        for clave, texto in DESCRIPCION_GEOMETRIA.items():
            geometria[clave] = preguntar(f"  {texto}", geometria[clave], minimo=0)
        if not preguntar_si("  ¿Pared de espesor constante (forma de tobera de cohete)?", True):
            geometria["tipo_pared"] = "cilindrica"

    caso = {
        "nombre": nombre,
        "descripcion": descripcion,
        "gas": {"gamma": gamma, "R": R},
        "camara": {"p0_Pa": p0, "T0_K": T0},
        "ambiente": ambiente,
        "empuje_requerido_N": F,
        "geometria": geometria,
        "presiones_exteriores_Pa": presiones,
    }

    ruta_caso = Path("casos") / f"{nombre}.json"
    ruta_caso.parent.mkdir(exist_ok=True)
    ruta_caso.write_text(json.dumps(caso, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nCaso guardado en {ruta_caso}. Para repetirlo: python main.py {ruta_caso}\n")
    return caso
