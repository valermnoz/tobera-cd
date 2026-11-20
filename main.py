"""
main.py — Corre un caso completo de TOBERA-CD.

Uso:
    python main.py casos/caso_preliminar.json

Lee el caso, dimensiona la tobera, genera su contorno, calcula las
presiones críticas y analiza cada presión exterior. Escribe los
resultados y los archivos para SolidWorks en salidas/<caso>/.
"""

import json
import sys
from pathlib import Path

from geometria import (
    contorno, exportar_dimensiones, exportar_dxf, exportar_xyz, resumen_geometria,
)
from tobera import (
    coeficiente_empuje, dimensionar, empuje, estado_salida,
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


def leer_caso(ruta):
    with open(ruta, encoding="utf-8") as f:
        caso = json.load(f)
    amb = caso["ambiente"]
    caso["pa_Pa"] = amb.get("pa_Pa") or presion_atmosferica(amb["altitud_m"])
    return caso


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


def correr(caso):
    g, R = caso["gas"]["gamma"], caso["gas"]["R"]
    p0, T0 = caso["camara"]["p0_Pa"], caso["camara"]["T0_K"]
    pa, F = caso["pa_Pa"], caso["empuje_requerido_N"]

    diseno = dimensionar(p0, T0, pa, F, g, R)
    crit = presiones_criticas(p0, diseno["Ae_At"], g)
    tramos = contorno(diseno["Dt"], diseno["De"], **parametros_geometria(caso))

    # Siempre se analiza también la presión ambiente de diseño
    presiones = sorted(set(caso["presiones_exteriores_Pa"]) | {pa}, reverse=True)

    analisis = []
    for pb in presiones:
        s = estado_salida(pb, p0, T0, diseno["At"], diseno["Ae_At"], g, R)
        Fb = empuje(s["m"], s["Ve"], s["pe"], pb, diseno["Ae"])
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
        })
    return {
        "diseno": diseno,
        "criticas": crit,
        "analisis": analisis,
        "tramos": tramos,
        "geometria": resumen_geometria(tramos),
    }


def resumen(caso, res):
    d, c = res["diseno"], res["criticas"]
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
        f"  Diámetro de entrada      {2*res['geometria']['r_entrada']*1e3:9.2f} mm",
        f"  Longitud entrada-garganta {res['geometria']['L_aguas_arriba']*1e3:8.2f} mm",
        f"  Longitud del divergente  {res['geometria']['L_divergente']*1e3:9.2f} mm",
        f"  Longitud total           {res['geometria']['L_total']*1e3:9.2f} mm",
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
                f"  {'':9} choque en A/A* = {ch['As_At']:.3f}: M1 = {ch['M1']:.3f} -> "
                f"M2 = {ch['M2']:.3f}, p02/p01 = {ch['p02_p01']:.3f}"
            )
    return "\n".join(lineas)


def main():
    ruta = sys.argv[1] if len(sys.argv) > 1 else "casos/caso_preliminar.json"
    caso = leer_caso(ruta)
    res = correr(caso)
    texto = resumen(caso, res)
    print(texto)

    salida = Path("salidas") / caso["nombre"]
    salida.mkdir(parents=True, exist_ok=True)
    (salida / "resumen.txt").write_text(texto, encoding="utf-8")
    with open(salida / "resultados.json", "w", encoding="utf-8") as f:
        datos = {k: v for k, v in res.items() if k != "tramos"}
        json.dump(datos, f, indent=2, ensure_ascii=False)

    # Archivos para SolidWorks
    d = res["diseno"]
    pg = parametros_geometria(caso)
    espesor = caso["geometria"]["espesor_pared_mm"] / 1e3
    exportar_xyz(res["tramos"], salida / "contorno_xyz.txt")
    exportar_dxf(res["tramos"], salida / "contorno.dxf", espesor)
    exportar_dimensiones(d["Dt"], d["De"], res["geometria"], salida / "dimensiones.txt",
                         espesor=espesor, **pg)

    print(f"\nResultados guardados en {salida.resolve()}")


if __name__ == "__main__":
    main()
