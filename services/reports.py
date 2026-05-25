from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
    Image
)
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4, landscape
from datetime import datetime
import os


# ======================================================
# HELPER FUNCTIONS
# ======================================================
def format_filter(value):
    return str(value) if value else "All"


def build_filter_text(
    provincia=None,
    anyo=None,
    mes=None,
    tipo_examen=None,
    permiso=None
):
    return (
        f"Province: {format_filter(provincia)} | "
        f"Year: {format_filter(anyo)} | "
        f"Month: {format_filter(mes)} | "
        f"Exam Type: {format_filter(tipo_examen)} | "
        f"Permit: {format_filter(permiso)}"
    )


# ======================================================
# TABLE PDF REPORT
# ======================================================
def export_table_pdf(
    filename,
    rows,
    provincia=None,
    anyo=None,
    mes=None,
    tipo_examen=None,
    permiso=None
):
    """
    Exports filtered table data to a formatted PDF report.
    """

    doc = SimpleDocTemplate(
        filename,
        pagesize=landscape(A4),
        rightMargin=25,
        leftMargin=25,
        topMargin=25,
        bottomMargin=25
    )

    elements = []
    styles = getSampleStyleSheet()

    # ---------- TITLE ----------
    elements.append(
        Paragraph("<b>Driving Exams Statistics Report</b>", styles["Title"])
    )
    elements.append(Spacer(1, 10))

    # ---------- METADATA ----------
    elements.append(
        Paragraph(
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            styles["Normal"]
        )
    )

    elements.append(
        Paragraph(
            build_filter_text(provincia, anyo, mes, tipo_examen, permiso),
            styles["Normal"]
        )
    )

    elements.append(Spacer(1, 12))

    if not rows:
        elements.append(
            Paragraph("No data available for selected filters.", styles["Normal"])
        )
        doc.build(elements)
        return

    # ---------- TOTALS ----------
    total_passed = 0
    total_failed = 0

    for row in rows:
        keys = row.keys()

        if "Passed" in keys:
            total_passed += row["Passed"] or 0
        elif "num_aptos" in keys:
            total_passed += row["num_aptos"] or 0

        if "Failed" in keys:
            total_failed += row["Failed"] or 0
        elif "num_no_aptos" in keys:
            total_failed += row["num_no_aptos"] or 0

    total_presented = total_passed + total_failed
    pass_rate = 0

    if total_presented > 0:
        pass_rate = (total_passed / total_presented) * 100

    summary_data = [
        ["Total Presented", "Total Passed", "Total Failed", "Pass Rate"],
        [
            str(total_presented),
            str(total_passed),
            str(total_failed),
            f"{pass_rate:.2f}%"
        ]
    ]

    summary_table = Table(summary_data)
    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.darkgrey),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
    ]))

    elements.append(summary_table)
    elements.append(Spacer(1, 14))

    # ---------- DATA TABLE ----------
    headers = list(rows[0].keys())
    data = [headers]

    for row in rows[:100]:
        data.append([str(row[col]) for col in headers])

    table = Table(data, repeatRows=1)

    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.black),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 7),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [
            colors.whitesmoke,
            colors.lightgrey
        ]),
    ]))

    elements.append(table)
    doc.build(elements)


# ======================================================
# CHART PDF REPORT
# ======================================================
def export_chart_pdf(filename, figure):
    """
    Exports the current matplotlib chart to a formatted PDF report.
    """

    temp_image = "temp_chart.png"
    figure.savefig(temp_image, dpi=150, bbox_inches="tight")

    doc = SimpleDocTemplate(
        filename,
        pagesize=A4,
        rightMargin=35,
        leftMargin=35,
        topMargin=35,
        bottomMargin=35
    )

    styles = getSampleStyleSheet()
    elements = []

    elements.append(
        Paragraph("<b>Driving Exams Chart Report</b>", styles["Title"])
    )
    elements.append(Spacer(1, 10))

    elements.append(
        Paragraph(
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            styles["Normal"]
        )
    )

    elements.append(Spacer(1, 16))
    elements.append(Image(temp_image, width=500, height=300))

    doc.build(elements)

    if os.path.exists(temp_image):
        os.remove(temp_image)