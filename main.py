"""
main.py — Corre un caso completo de TOBERA-CD.

Uso:
    python main.py                              (modo interactivo: pregunta los datos)
    python main.py casos/caso_preliminar.json   (lee un caso guardado)

Dimensiona la tobera, genera su contorno, calcula las presiones críticas y
analiza cada presión exterior: régimen, posición del choque, empuje y la
distribución de M, p y T a lo largo de la tobera. Escribe resultados,
gráficas y archivos para SolidWorks en salidas/<caso>/.
"""

import json
import sys
from pathlib import Path

import numpy as np

from geometria import (
    GEOMETRIA_DEFECTO, area, contorno, exportar_dimensiones, exportar_dxf, exportar_xyz,
    muestrear, resumen_geometria,
)
from graficas import graficar_contorno, graficar_mach, graficar_presiones
from tobera import (
    coeficiente_empuje, dimensionar, distribucion, empuje, estado_salida,
    presion_atmosferica, presiones_criticas,
)

NOMBRES_REGIMEN = {
    "subsonico": "Subsónico (sin estrangular)",
    "estrangulado_subsonico": "Estrangulado, subsónico",
    "choque_interno": "Choque normal interno",
    "choque_en_salida": "Choque normal en la salida",
    "sobreexpandida": "Sobreexpandida",
    "adaptada": "Adaptada (expansión ideal)",
    "subexpandida": "Subexpandida",
}

# ---------------------------------------------------------------------
# Lectura del caso
# ---------------------------------------------------------------------

def completar_caso(caso):
    """Agrega pa y los valores por defecto de la geometría que falten."""
    amb = caso["ambiente"]
    caso["pa_Pa"] = amb.get("pa_Pa") or presion_atmosferica(amb["altitud_m"])
    caso["geometria"] = {**GEOMETRIA_DEFECTO, **caso.get("geometria", {})}
    caso.setdefault("presiones_exteriores_Pa", "auto")
    return caso


def leer_caso(ruta):
    with open(ruta, encoding="utf-8") as f:
        return completar_caso(json.load(f))


def parametros_geometria(caso):
    """Parámetros del contorno en las unidades que usa geometria.contorno()."""
    g = caso["geometria"]
    return {
        "ang_conv": g["angulo_convergente_deg"],
        "ang_div": g["angulo_divergente_deg"],
        "relacion_contraccion": g["relacion_contraccion"],
        "L_recta": g["longitud_recta_entrada_mm"] / 1e3,
        "f_entrada": g["radio_arco_entrada_rt"],
        "f_arriba": g["radio_garganta_arriba_rt"],
        "f_abajo": g["radio_garganta_abajo_rt"],
    }


def presiones_a_analizar(caso, crit, p0):
    """
    Presiones exteriores del caso. Con "auto" se elige una por régimen:
    subsónico, choque interno, sobreexpandida y subexpandida.
    La presión ambiente de diseño (tobera adaptada) siempre se incluye.
    """
    lista = caso["presiones_exteriores_Pa"]
    if lista == "auto":
        p1, p2, p3 = crit["p1"], crit["p2"], crit["p3"]
        lista = [
            min(1.02 * p1, 0.5 * (p1 + p0)),  # subsónico
            0.5 * (p1 + p2),                   # choque interno
            0.5 * (p2 + p3),                   # sobreexpandida
            0.5 * p3,                          # subexpandida
        ]
    return sorted(set(lista) | {caso["pa_Pa"]}, reverse=True)


# ---------------------------------------------------------------------
# Cálculo
# ---------------------------------------------------------------------

def correr(caso):
    g, R = caso["gas"]["gamma"], caso["gas"]["R"]
    p0, T0 = caso["camara"]["p0_Pa"], caso["camara"]["T0_K"]
    pa, F = caso["pa_Pa"], caso["empuje_requerido_N"]

    diseno = dimensionar(p0, T0, pa, F, g, R)
    crit = presiones_criticas(p0, diseno["Ae_At"], g)
    tramos = contorno(diseno["Dt"], diseno["De"], **parametros_geometria(caso))

    # Secciones de la tobera real (con la garganta redondeada)
    x, r = muestrear(tramos)
    A = area(r)

    analisis, distribuciones = [], []
    for pb in presiones_a_analizar(caso, crit, p0):
        s = estado_salida(pb, p0, T0, diseno["At"], diseno["Ae_At"], g, R)
        Fb = empuje(s["m"], s["Ve"], s["pe"], pb, diseno["Ae"])
        d = distribucion(x, A, pb, p0, T0, g)
        d["pb"] = pb
        distribuciones.append(d)
        analisis.append({
            "pb_Pa": pb,
            "regimen": s["regimen"],
            "Me": s["Me"],
            "pe_Pa": s["pe"],
            "Ve_m_s": s["Ve"],
            "m_kg_s": s["m"],
            "F_N": Fb,
            "CF": coeficiente_empuje(Fb, p0, diseno["At"]),
            "choque": s["choque"],
            "x_choque_mm": None if d["x_choque"] is None else d["x_choque"] * 1e3,
        })

    return {
        "diseno": diseno,
        "criticas": crit,
        "analisis": analisis,
        "geometria": resumen_geometria(tramos),
        # Lo siguiente no se guarda en el JSON (son arreglos o geometría)
        "tramos": tramos,
        "x": x,
        "r": r,
        "distribuciones": distribuciones,
    }


# ---------------------------------------------------------------------
# Salidas
# ---------------------------------------------------------------------

def resumen(caso, res):
    d, c, geo = res["diseno"], res["criticas"], res["geometria"]
    lineas = [
        f"TOBERA-CD · {caso['nombre']}",
        f"{caso.get('descripcion', '')}",
        "",
        "DIMENSIONAMIENTO",
        f"  Presión ambiente pa      {caso['pa_Pa']/1e3:9.2f} kPa",
        f"  Mach de salida Me        {d['Me']:9.3f}",
        f"  Relación de áreas Ae/A*  {d['Ae_At']:9.3f}",
        f"  Velocidad de salida Ve   {d['Ve']:9.1f} m/s",
        f"  Gasto másico             {d['m']:9.4f} kg/s",
        f"  Diámetro de garganta D*  {d['Dt']*1e3:9.2f} mm",
        f"  Diámetro de salida De    {d['De']*1e3:9.2f} mm",
        f"  Coeficiente de empuje CF {d['CF']:9.3f}",
        "",
        "GEOMETRÍA (garganta en x = 0)",
        f"  Diámetro de entrada      {2*geo['r_entrada']*1e3:9.2f} mm",
        f"  Longitud entrada-garganta {geo['L_aguas_arriba']*1e3:8.2f} mm",
        f"  Longitud del divergente  {geo['L_divergente']*1e3:9.2f} mm",
        f"  Longitud total           {geo['L_total']*1e3:9.2f} mm",
        "",
        "PRESIONES CRÍTICAS",
        f"  p1 (subsónica, M=1 en garganta)  {c['p1']/1e3:8.1f} kPa",
        f"  p2 (choque en la salida)         {c['p2']/1e3:8.1f} kPa",
        f"  p3 (expansión ideal)             {c['p3']/1e3:8.1f} kPa",
        "",
        "ANÁLISIS POR PRESIÓN EXTERIOR",
        f"  {'pb [kPa]':>9} {'Régimen':<28} {'Me':>6} {'m [kg/s]':>9} {'F [N]':>8}",
    ]
    for a in res["analisis"]:
        lineas.append(
            f"  {a['pb_Pa']/1e3:9.1f} {NOMBRES_REGIMEN[a['regimen']]:<28} "
            f"{a['Me']:6.3f} {a['m_kg_s']:9.4f} {a['F_N']:8.2f}"
        )
        if a["choque"]:
            ch = a["choque"]
            lineas.append(
                f"  {'':9} choque en x = {a['x_choque_mm']:.2f} mm (A/A* = {ch['As_At']:.3f}): "
                f"M1 = {ch['M1']:.3f} -> M2 = {ch['M2']:.3f}, p02/p01 = {ch['p02_p01']:.3f}"
            )
    return "\n".join(lineas)


def guardar_distribucion_csv(res, ruta):
    """
    Tabla sección por sección: x, r, A/A* y, para cada presión exterior,
    M, p [kPa] y T [K]. Se abre directo en Excel para comparar con SolidWorks.
    """
    x, r = res["x"], res["r"]
    A_At = (r / r.min()) ** 2
    columnas, nombres = [x * 1e3, r * 1e3, A_At], ["x_mm", "r_mm", "A_sobre_At"]
    for d in res["distribuciones"]:
        etiqueta = f"{d['pb']/1e3:.1f}kPa"
        columnas += [d["M"], d["p"] / 1e3, d["T"]]
        nombres += [f"M_{etiqueta}", f"p_kPa_{etiqueta}", f"T_K_{etiqueta}"]
    np.savetxt(ruta, np.column_stack(columnas), fmt="%.5f", delimiter=",",
               header=",".join(nombres), comments="")


def guardar(caso, res, salida):
    salida.mkdir(parents=True, exist_ok=True)
    (salida / "resumen.txt").write_text(resumen(caso, res), encoding="utf-8")
    with open(salida / "resultados.json", "w", encoding="utf-8") as f:
        claves = ("diseno", "criticas", "analisis", "geometria")
        json.dump({k: res[k] for k in claves}, f, indent=2, ensure_ascii=False)
    guardar_distribucion_csv(res, salida / "distribucion.csv")

    # Archivos para SolidWorks
    d, tramos = res["diseno"], res["tramos"]
    geo_caso = caso["geometria"]
    espesor = geo_caso["espesor_pared_mm"] / 1e3
    pared = geo_caso["tipo_pared"]
    exportar_xyz(tramos, salida / "contorno_xyz.txt")
    exportar_dxf(tramos, salida / "contorno.dxf", espesor, pared)
    exportar_dimensiones(d["Dt"], d["De"], res["geometria"], salida / "dimensiones.txt",
                         espesor=espesor, **parametros_geometria(caso))

    # Gráficas
    p0 = caso["camara"]["p0_Pa"]
    graficar_contorno(tramos, d, res["geometria"], espesor, pared, salida / "contorno.png")
    graficar_presiones(tramos, espesor, pared, res["x"], res["distribuciones"], p0,
                       salida / "presiones.png")
    graficar_mach(tramos, espesor, pared, res["x"], res["distribuciones"], salida / "mach.png")


def main():
    if len(sys.argv) > 1:
        caso = leer_caso(sys.argv[1])
    else:
        from interactivo import preguntar_caso
        caso = completar_caso(preguntar_caso())

    res = correr(caso)
    print(resumen(caso, res))

    salida = Path("salidas") / caso["nombre"]
    guardar(caso, res, salida)
    print(f"\nResultados guardados en {salida.resolve()}")


if __name__ == "__main__":
    main()
