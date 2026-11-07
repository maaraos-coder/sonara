"""Structured calculation inputs and printable solution sheets."""
from io import BytesIO
from math import isfinite, log10
from xml.sax.saxutils import escape

LABELS = {
    "area": "Área separadora [m²]", "volume": "Volumen receptor [m³]",
    "tr": "TR receptor [s]", "t0": "TR de referencia [s]",
    "shape": "Corrección de fachada [dB]", "lden": "Lden [dB]",
    "source_absorption": "Absorción equivalente emisora [m²]",
    "receiver_absorption": "Absorción equivalente receptora [m²]",
    "receiver_t": "TR receptor [s]", "distance": "Distancia [m]",
    "directivity": "Factor de directividad Q", "separating_area": "Área separadora [m²]",
    "junction_type": "Tipo de unión", "length": "Longitud de unión [m]",
    "kij": "Kij [dB]", "mass_source": "Masa superficial emisora [kg/m²]",
    "mass_receiver": "Masa superficial receptora [kg/m²]",
    "source_curve": "Curva de origen [dB]", "receiver_curve": "R receptor [dB]",
    "delta_source": "Mejora emisor [dB]", "delta_receiver": "Mejora receptor [dB]",
    "reduction_curve": "R separador [dB]", "transfer_curve": "Transferencia [dB]",
    "attenuation_curve": "Atenuación adicional [dB]", "rw_db": "Rw [dB]",
    "masa": "Masa superficial [kg/m²]", "espesor": "Espesor [mm]",
    "densidad_losa": "Densidad losa [kg/m³]", "masa_sobrelosa": "Masa sobrelosa [kg/m²]",
    "rigidez_dinamica": "Rigidez dinámica [MN/m³]", "frecuencia_propia": "Frecuencia propia [Hz]",
    "tipo_piso": "Piso", "tipo_cielo": "Cielo", "ln0w": "Ln,0,w [dB]",
    "dens": "Densidad [kg/m³]", "E": "Módulo de Young [Pa]",
    "camara": "Cámara [mm]", "configuracion": "Configuración",
    "active": "Activo", "kind": "Tipo de vía", "modo": "Método",
    "layers_left": "Capas lado emisor", "layers_right": "Capas lado receptor",
}
FREQUENCY_KEYS = ("frequencies", "frecuencias", "frecuencias_hz")
NAMES = ("name", "nombre")


def label(key):
    return LABELS.get(key, key.replace("_", " ").capitalize())


def display(value):
    if isinstance(value, bool):
        return "Sí" if value else "No"
    if isinstance(value, float):
        return format(value, ".10g") if isfinite(value) else "—"
    return str(value) if value is not None else "—"


def calculation_tables(solution):
    """Return tables from recorded inputs, preserving each spectrum's band grid."""
    tables = []
    frequencies = next((solution[key] for key in FREQUENCY_KEYS if solution.get(key)), [])

    def add(title, record, inherited_grid):
        grid = next((record[key] for key in FREQUENCY_KEYS if record.get(key)), inherited_grid)
        rows, spectra, nested = [], {}, []
        for key, value in record.items():
            if key in (*NAMES, *FREQUENCY_KEYS, "source_frequencies", "receiver_frequencies") or value is None:
                continue
            if isinstance(value, dict):
                nested.append((label(key), value))
            elif isinstance(value, list):
                if value and all(isinstance(item, dict) for item in value):
                    nested.extend((f"{label(key)} · {index}", item)
                                  for index, item in enumerate(value, 1))
                elif value:
                    spectra[key] = value
            else:
                rows.append([label(key), display(value)])
        if rows:
            tables.append((title, ["Parámetro", "Valor"], rows))
        for key, curve in spectra.items():
            name = label(key)
            curve_grid = record.get(key.replace("_curve", "_frequencies")) if key in ("source_curve", "receiver_curve") else None
            band_grid = curve_grid or grid
            has_grid = len(band_grid) == len(curve)
            bands = band_grid if has_grid else range(1, len(curve) + 1)
            tables.append((f"{title} · {name}", ["Hz" if has_grid else "Índice", name],
                           [[display(hz), display(value)] for hz, value in zip(bands, curve)]))
        for subtitle, child in nested:
            child_name = child.get("name") or child.get("nombre")
            add(f"{title} · {subtitle}" + (f" · {child_name}" if child_name else ""), child, grid)

    fields = ("modo", "masa", "espesor", "densidad_losa", "masa_sobrelosa", "rigidez_dinamica",
              "frecuencia_propia", "tipo_piso", "tipo_cielo", "ln0w", "revestimiento_catalogo_id",
              "normalization", "base_spectrum_source", "lden", "delta_lw_piso")
    add("Entradas generales", {key: solution.get(key) for key in fields}, frequencies)
    for key, title in (("geometria", "Geometría y normalización"), ("receta_diseno", "Entradas del método"),
                       ("separador", "Separador directo"), ("entradas_calculo", "Configuración del cálculo")):
        if isinstance(solution.get(key), dict):
            add(title, solution[key], frequencies)
    for key, title in (("flancos", "Flanqueo"), ("vias_instalaciones", "Vía de instalaciones"),
                       ("componentes", "Componente"), ("espectros_componentes", "Espectro del componente"),
                       ("construccion_guardada", "Sección constructiva")):
        for index, record in enumerate(solution.get(key) or [], 1):
            if isinstance(record, dict):
                name = record.get("name") or record.get("nombre") or record.get("Componente")
                add(f"{title} {index}" + (f" · {name}" if name else ""), record, frequencies)
    fields = ("dntw", "dnt50", "dnt_a", "dnt_atr", "lnw", "lntw", "lnt50", "ci", "ci50_2500",
              "d2mntw", "d2mnt_atr", "d2mnt_c", "d2mnt_ctr", "rw_compuesto", "ratr_compuesto",
              "laeq_nt", "lafmax_nt")
    add("Indicadores calculados", {key: solution.get(key) for key in fields}, frequencies)
    return tables


def solution_pdf(solution, requirement, status, tables, columns):
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.graphics.shapes import Drawing, Line, PolyLine, String
    from reportlab.platypus import LongTable, Paragraph, SimpleDocTemplate, Spacer, TableStyle

    output = BytesIO()
    doc = SimpleDocTemplate(output, pagesize=A4, leftMargin=40, rightMargin=40,
                            topMargin=38, bottomMargin=40, title="Ficha técnica SONARA")
    styles = getSampleStyleSheet()
    navy = colors.HexColor("#15465e")
    styles["Heading2"].textColor = navy
    styles["BodyText"].fontSize = 9
    styles["BodyText"].leading = 12

    def paragraph(value, style="BodyText"):
        text = str(value).replace("′", "'").replace("ₙ", "n").replace("Δ", "Delta ").replace("→", " a ").replace("≥", ">=").replace("≤", "<=").replace("‑", "-")
        return Paragraph(escape(text).replace("\n", "<br/>"), styles[style])

    story = [paragraph("SONARA · Ficha técnica", "Heading2"),
             paragraph(solution.get("nombre", "Solución acústica"), "Title")]
    objective = " ".join(str(requirement[key]) for key in ("indicador", "sentido", "valor", "unidad")
                         if requirement.get(key) is not None)
    for value in (solution.get("proyecto"), solution.get("tipo_calculo"), solution.get("created_at"),
                  " → ".join(str(requirement[key]) for key in ("recinto_emisor", "recinto_receptor")
                             if requirement.get(key)),
                  f"Objetivo: {objective} · Estado: {status}" if objective else status,
                  solution.get("resultado_label"), solution.get("descripcion"), solution.get("estado_docente")):
        if value:
            story.append(paragraph(value))
    if solution.get("armado_docente"):
        story.append(paragraph("Composición constructiva", "Heading2"))
        story.extend(paragraph(layer) for layer in solution["armado_docente"])
    story.append(paragraph("La ficha presenta las entradas conservadas en la corrida guardada."))

    def table(title, headers, rows):
        story.append(paragraph(title, "Heading2"))
        widths = [doc.width / len(headers)] * len(headers)
        if headers == ["Parámetro", "Valor"]:
            widths = [doc.width * .38, doc.width * .62]
        grid = LongTable([[paragraph(h) for h in headers]] +
                         [[paragraph(value) for value in row] for row in rows],
                         colWidths=widths, repeatRows=1, hAlign="LEFT")
        grid.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#d8e8ef")),
                                  ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f1f5f7")]),
                                  ("VALIGN", (0, 0), (-1, -1), "TOP")]))
        story.extend([grid, Spacer(1, 6)])

    if len(columns) > 1:
        hz = columns["Hz"]
        series = list(columns.items())[1:]
        for offset in range(0, len(series), 4):
            group = series[offset:offset + 4]
            finite = [v for _, values in group for v in values if isinstance(v, (int, float)) and isfinite(v)]
            if len(hz) > 1 and finite and min(hz) > 0 and max(hz) > min(hz):
                drawing = Drawing(doc.width, 157 + 11 * len(group))
                y_min, y_max = min(finite), max(finite)
                y_max = max(y_min + 1, y_max)
                x_min, x_max = log10(min(hz)), log10(max(hz))
                palette = [navy, colors.HexColor("#a13b19"), colors.HexColor("#49691e"), colors.HexColor("#7b3d86")]
                def x(frequency):
                    return 41 + (doc.width - 62) * (log10(frequency) - x_min) / (x_max - x_min)
                def y(value):
                    return 29 + 112 * (value - y_min) / (y_max - y_min)
                for fraction in (0, .25, .5, .75, 1):
                    value = y_min + fraction * (y_max - y_min)
                    drawing.add(Line(41, y(value), doc.width - 20, y(value), strokeColor=colors.lightgrey))
                    drawing.add(String(4, y(value) - 3, f"{value:.0f}", fontSize=8))
                for frequency in hz[::max(1, len(hz)//6)]:
                    drawing.add(String(x(frequency), 15, f"{frequency:g}", fontSize=8, textAnchor="middle"))
                drawing.add(String(doc.width-18, 3, "Hz", fontSize=8))
                drawing.add(String(4, 146, "dB", fontSize=8))
                for index, (name, values) in enumerate(group):
                    points = [(x(f), y(v)) for f, v in zip(hz, values)
                              if isinstance(v, (int, float)) and isfinite(v)]
                    if len(points) > 1:
                        drawing.add(PolyLine(points, strokeColor=palette[index], strokeWidth=1.4))
                    drawing.add(String(41, 155 + 11 * index, name.replace("Δ", "Delta ").replace("→", " a ").replace("≥", ">=").replace("≤", "<=").replace("‑", "-").replace("ₙ", "n"),
                                       fontSize=8, fillColor=palette[index]))
                story.append(drawing)
            table("Resultados por banda", ["Hz"] + [name for name, _ in group],
                  [[display(value) for value in row] for row in zip(hz, *(values for _, values in group))])
    for title, headers, rows in tables:
        table(title, headers, rows)

    def footer(canvas, document):
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(navy)
        canvas.drawString(40, 23, "SONARA · Ficha técnica")
        canvas.drawRightString(A4[0] - 40, 23, f"Página {document.page}")

    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    return output.getvalue()



