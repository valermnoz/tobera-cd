"""
geometria.py — Contorno de la tobera y archivos para SolidWorks.

La tobera es cónica con transiciones redondeadas. Recorriendo el flujo:

  1. tramo recto de entrada          (radio r_entrada)
  2. arco de entrada                 (de horizontal a -ang_conv)
  3. convergente cónico              (pendiente -tan(ang_conv))
  4. arco de garganta aguas arriba   (de -ang_conv a horizontal)
  5. arco de garganta aguas abajo    (de horizontal a +ang_div)
  6. divergente cónico               (pendiente +tan(ang_div)) hasta r_salida

Todos los tramos son tangentes entre sí, así que el contorno no tiene
esquinas. La garganta (radio mínimo r_t) queda en x = 0.

Unidades: metros dentro del módulo; los archivos para SolidWorks se
escriben en milímetros.
"""

import math
from pathlib import Path

import numpy as np

# Parámetros de geometría por defecto (mismos nombres que en los casos .json)
GEOMETRIA_DEFECTO = {
    "angulo_convergente_deg": 30.0,
    "angulo_divergente_deg": 15.0,
    "relacion_contraccion": 9.0,
    "longitud_recta_entrada_mm": 10.0,
    "radio_arco_entrada_rt": 2.0,
    "radio_garganta_arriba_rt": 1.5,
    "radio_garganta_abajo_rt": 1.5,
    "espesor_pared_mm": 2.0,
    "tipo_pared": "constante",
}


# ---------------------------------------------------------------------
# Construcción del contorno
# ---------------------------------------------------------------------

def contorno(Dt, De, ang_conv=30.0, ang_div=15.0, relacion_contraccion=9.0,
             L_recta=0.010, f_entrada=2.0, f_arriba=1.5, f_abajo=1.5):
    """
    Construye el contorno interior de la tobera.

    Dt, De:               diámetros de garganta y salida [m]
    ang_conv, ang_div:    semiángulos del convergente y del divergente [grados]
    relacion_contraccion: A_entrada/A* (define el diámetro de entrada)
    L_recta:              longitud del tramo recto de entrada [m]
    f_entrada:            radio del arco de entrada, en múltiplos de r*
    f_arriba, f_abajo:    radios de los arcos de garganta, en múltiplos de r*

    Devuelve una lista de tramos. Cada tramo es un diccionario:
      {"tipo": "linea", "p0": (x, r), "p1": (x, r)}
      {"tipo": "arco",  "centro": (x, r), "R": radio,
       "phi0": ángulo inicial, "phi1": ángulo final}   (ángulos en grados)
    """
    rt, re = Dt / 2, De / 2
    r_in = rt * math.sqrt(relacion_contraccion)
    a_c, a_d = math.radians(ang_conv), math.radians(ang_div)
    R_e, R_u, R_d = f_entrada * rt, f_arriba * rt, f_abajo * rt

    # Arco de garganta aguas abajo: de la garganta (0, rt) hasta pendiente +ang_div
    x5, r5 = R_d * math.sin(a_d), rt + R_d * (1 - math.cos(a_d))
    # Arco de garganta aguas arriba: desde pendiente -ang_conv hasta la garganta
    x4, r4 = -R_u * math.sin(a_c), rt + R_u * (1 - math.cos(a_c))
    # Fin del arco de entrada (inicio del cono convergente)
    r3 = r_in - R_e * (1 - math.cos(a_c))
    x3 = x4 - (r3 - r4) / math.tan(a_c)
    # Inicio del arco de entrada (fin del tramo recto)
    x2 = x3 - R_e * math.sin(a_c)
    x1 = x2 - L_recta
    # Salida
    xe = x5 + (re - r5) / math.tan(a_d)

    if r3 <= r4:
        raise ValueError("La entrada es muy angosta para los arcos elegidos: "
                         "aumenta relacion_contraccion o reduce los radios.")
    if re <= r5:
        raise ValueError("La salida es muy angosta para el arco de garganta: "
                         "reduce f_abajo.")

    deg = math.degrees
    return [
        {"tipo": "linea", "p0": (x1, r_in), "p1": (x2, r_in)},
        {"tipo": "arco", "centro": (x2, r_in - R_e), "R": R_e,
         "phi0": 90.0, "phi1": 90.0 - deg(a_c)},
        {"tipo": "linea", "p0": (x3, r3), "p1": (x4, r4)},
        {"tipo": "arco", "centro": (0.0, rt + R_u), "R": R_u,
         "phi0": 270.0 - deg(a_c), "phi1": 270.0},
        {"tipo": "arco", "centro": (0.0, rt + R_d), "R": R_d,
         "phi0": 270.0, "phi1": 270.0 + deg(a_d)},
        {"tipo": "linea", "p0": (x5, r5), "p1": (xe, re)},
    ]


def _extremos(tramo):
    """Puntos inicial y final de un tramo, en el sentido del flujo."""
    if tramo["tipo"] == "linea":
        return tramo["p0"], tramo["p1"]
    cx, cr = tramo["centro"]
    R = tramo["R"]
    p = [(cx + R * math.cos(math.radians(f)), cr + R * math.sin(math.radians(f)))
         for f in (tramo["phi0"], tramo["phi1"])]
    return p[0], p[1]


def muestrear(tramos, n_por_tramo=60):
    """
    Puntos (x, r) a lo largo del contorno, en el sentido del flujo.
    Cada tramo se divide en n_por_tramo partes; los puntos compartidos
    entre tramos no se repiten.
    """
    xs, rs = [], []
    for i, t in enumerate(tramos):
        s = np.linspace(0.0, 1.0, n_por_tramo + 1)
        if i > 0:
            s = s[1:]
        if t["tipo"] == "linea":
            (x0, r0), (x1, r1) = t["p0"], t["p1"]
            xs.extend(x0 + s * (x1 - x0))
            rs.extend(r0 + s * (r1 - r0))
        else:
            cx, cr = t["centro"]
            phi = np.radians(t["phi0"] + s * (t["phi1"] - t["phi0"]))
            xs.extend(cx + t["R"] * np.cos(phi))
            rs.extend(cr + t["R"] * np.sin(phi))
    return np.array(xs), np.array(rs)


def area(r):
    """Área de la sección circular de radio r."""
    return np.pi * np.asarray(r) ** 2


def resumen_geometria(tramos):
    """Longitudes y radios principales del contorno [m]."""
    (x_ini, r_in), _ = _extremos(tramos[0])
    _, (x_fin, r_sal) = _extremos(tramos[-1])
    return {
        "r_entrada": r_in,
        "r_garganta": tramos[3]["centro"][1] - tramos[3]["R"],
        "r_salida": r_sal,
        "x_entrada": x_ini,
        "x_salida": x_fin,
        "L_total": x_fin - x_ini,
        "L_aguas_arriba": -x_ini,
        "L_divergente": x_fin,
    }


def contorno_exterior(tramos, espesor, pared="constante"):
    """
    Contorno exterior de la pared, en el sentido del flujo.

    pared = "constante":  la pared sigue al contorno interior con espesor
                          constante (forma de tobera de cohete). Cada línea se
                          desplaza 'espesor' hacia afuera y cada arco cambia de
                          radio (R - espesor si su centro queda del lado de la
                          pared, R + espesor si queda del lado del eje). El último
                          tramo se prolonga hasta el plano de salida para que el
                          extremo quede plano.
    pared = "cilindrica": tubo exterior de radio r_entrada + espesor.
    """
    (x_ini, r_in), _ = _extremos(tramos[0])
    _, (x_fin, _) = _extremos(tramos[-1])

    if pared == "cilindrica":
        r_ext = r_in + espesor
        return [{"tipo": "linea", "p0": (x_ini, r_ext), "p1": (x_fin, r_ext)}]
    if pared != "constante":
        raise ValueError('pared debe ser "constante" o "cilindrica".')

    exterior = []
    for t in tramos:
        if t["tipo"] == "linea":
            (x0, r0), (x1, r1) = t["p0"], t["p1"]
            L = math.hypot(x1 - x0, r1 - r0)
            nx, nr = -(r1 - r0) / L, (x1 - x0) / L  # normal hacia afuera
            exterior.append({"tipo": "linea",
                             "p0": (x0 + espesor * nx, r0 + espesor * nr),
                             "p1": (x1 + espesor * nx, r1 + espesor * nr)})
        else:
            # Si el centro del arco está arriba del contorno (del lado de la
            # pared), el arco exterior es concéntrico con radio menor.
            centro_del_lado_de_la_pared = t["centro"][1] > _extremos(t)[0][1]
            R = t["R"] - espesor if centro_del_lado_de_la_pared else t["R"] + espesor
            if R <= 0:
                raise ValueError("El espesor de pared es mayor que el radio de un "
                                 "arco de garganta: reduce el espesor.")
            exterior.append({**t, "R": R})

    # Prolongar el último tramo (recta del divergente) hasta x = x_fin
    (x0, r0), (x1, r1) = exterior[-1]["p0"], exterior[-1]["p1"]
    m = (r1 - r0) / (x1 - x0)
    exterior[-1]["p1"] = (x_fin, r1 + m * (x_fin - x1))
    return exterior


# ---------------------------------------------------------------------
# Archivos para SolidWorks (milímetros)
# ---------------------------------------------------------------------

def exportar_xyz(tramos, ruta, n_por_tramo=60):
    """
    Coordenadas del contorno interior para Insertar → Curva → Curva por
    puntos XYZ. Tres columnas X Y Z separadas por tabulador, en mm, Z = 0.
    X es el eje de la tobera y Y el radio.
    """
    x, r = muestrear(tramos, n_por_tramo)
    datos = np.column_stack([x * 1e3, r * 1e3, np.zeros_like(x)])
    np.savetxt(ruta, datos, fmt="%.5f", delimiter="\t")


def exportar_dxf(tramos, ruta, espesor=0.002, pared="constante"):
    """
    Perfil cerrado de media tobera para croquis y revolución en SolidWorks.

    Capa CONTORNO: pared interior y exterior con líneas y arcos exactos, y
                   líneas de cierre planas en la entrada y la salida.
    Capa EJE:      eje de revolución (y = 0).

    pared: "constante" (sigue al contorno, forma de tobera de cohete) o
           "cilindrica" (tubo exterior recto). Ver contorno_exterior().
    """
    import ezdxf  # se importa aquí para que el resto del módulo no dependa de ezdxf

    mm = 1e3
    doc = ezdxf.new("R2010", setup=False)
    doc.units = ezdxf.units.MM
    doc.layers.add("CONTORNO")
    doc.layers.add("EJE")
    msp = doc.modelspace()
    capa = {"layer": "CONTORNO"}

    def dibujar(t):
        if t["tipo"] == "linea":
            (x0, r0), (x1, r1) = t["p0"], t["p1"]
            msp.add_line((x0 * mm, r0 * mm), (x1 * mm, r1 * mm), dxfattribs=capa)
        else:
            # En DXF los arcos van en sentido antihorario: ángulo inicial < final
            a0, a1 = sorted((t["phi0"], t["phi1"]))
            msp.add_arc((t["centro"][0] * mm, t["centro"][1] * mm), t["R"] * mm, a0, a1,
                        dxfattribs=capa)

    exterior = contorno_exterior(tramos, espesor, pared)
    for t in tramos + exterior:
        dibujar(t)

    # Cierres planos en la entrada y en la salida
    (x_ini, r_in), _ = _extremos(tramos[0])
    _, (x_fin, r_sal) = _extremos(tramos[-1])
    r_ext_ini = _extremos(exterior[0])[0][1]
    r_ext_fin = _extremos(exterior[-1])[1][1]
    dibujar({"tipo": "linea", "p0": (x_ini, r_in), "p1": (x_ini, r_ext_ini)})
    dibujar({"tipo": "linea", "p0": (x_fin, r_sal), "p1": (x_fin, r_ext_fin)})

    msp.add_line((x_ini * mm, 0.0), (x_fin * mm, 0.0), dxfattribs={"layer": "EJE"})
    doc.saveas(ruta)


def exportar_dimensiones(Dt, De, geo, ruta, ang_conv, ang_div, relacion_contraccion,
                         L_recta, f_entrada, f_arriba, f_abajo, espesor):
    """
    Variables globales para Herramientas → Ecuaciones → Vincular a archivo
    externo en SolidWorks. Longitudes en mm y ángulos en grados.
    """
    rt = Dt / 2
    valores = {
        "D_garganta": Dt * 1e3,
        "D_salida": De * 1e3,
        "D_entrada": 2 * geo["r_entrada"] * 1e3,
        "ang_convergente": ang_conv,
        "ang_divergente": ang_div,
        "L_recta_entrada": L_recta * 1e3,
        "R_arco_entrada": f_entrada * rt * 1e3,
        "R_garganta_arriba": f_arriba * rt * 1e3,
        "R_garganta_abajo": f_abajo * rt * 1e3,
        "L_aguas_arriba": geo["L_aguas_arriba"] * 1e3,
        "L_divergente": geo["L_divergente"] * 1e3,
        "L_total": geo["L_total"] * 1e3,
        "espesor_pared": espesor * 1e3,
        "relacion_contraccion": relacion_contraccion,
    }
    lineas = [f'"{k}" = {v:.4f}' for k, v in valores.items()]
    Path(ruta).write_text("\n".join(lineas) + "\n", encoding="utf-8")
