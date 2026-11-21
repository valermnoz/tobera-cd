"""
El reporte PDF se genera con las figuras del caso.
"""
from pathlib import Path

from main import completar_caso, correr, guardar, leer_caso
from reporte_pdf import generar_pdf

CASO = Path(__file__).parent / "datos" / "caso_prueba.json"


def test_pdf_con_figuras(tmp_path):
    caso = completar_caso(leer_caso(CASO))
    res = correr(caso)
    guardar(caso, res, tmp_path)
    pdf = generar_pdf(caso, res, tmp_path)
    assert pdf.startswith(b"%PDF")
    assert pdf.count(b"/Type /Page\n") + pdf.count(b"/Type /Page ") >= 1
    # Sin carpeta de salida solo queda la hoja de datos, más corta
    assert len(generar_pdf(caso, res)) < len(pdf)
