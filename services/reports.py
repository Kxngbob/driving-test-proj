from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from datetime import datetime
import os


# ================= TABLE PDF =================
def export_table_pdf(filename, rows, provincia=None, anyo=None):
    doc = SimpleDocTemplate(filename, pagesize=A4)
    elements = []

    styles = getSampleStyleSheet()

    # Title
    elements.append(Paragraph("<b>Driving Exam Report</b>", styles["Title"]))
    elements.append(Spacer(1, 12))

    # Metadata
    elements.append(
        Paragraph(
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            styles["Normal"]
        )
    )
    elements.append(
        Paragraph(
            f"Filters → Province: {provincia or 'All'} | Year: {anyo or 'All'}",
            styles["Normal"]
        )
    )
    elements.append(Spacer(1, 12))

    if not rows:
        elements.append(Paragraph("No data available.", styles["Normal"]))
        doc.build(elements)
        return

    # Build table data
    headers = list(rows[0].keys())
    data = [headers]

    for row in rows[:50]:
        data.append([str(row[col]) for col in headers])

    table = Table(data, repeatRows=1)

    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 7),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))

    elements.append(table)

    doc.build(elements)


# ================= CHART PDF =================
def export_chart_pdf(filename, figure):
    temp_image = "temp_chart.png"
    figure.savefig(temp_image)

    c = canvas.Canvas(filename, pagesize=A4)
    width, height = A4

    c.setFont("Helvetica-Bold", 16)
    c.drawString(40, height - 40, "Driving Exam Chart")

    c.drawImage(temp_image, 40, 200, width=500, height=350)

    c.save()

    if os.path.exists(temp_image):
        os.remove(temp_image)
