from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


def export_table_pdf(filename, rows):
    c = canvas.Canvas(filename, pagesize=A4)
    width, height = A4

    y = height - 40
    c.setFont("Helvetica", 8)

    headers = rows[0].keys()

    # Header
    for h in headers:
        c.drawString(40, y, h)
        y -= 12

    y -= 10

    # Rows
    for row in rows[:40]:  # limit to first 40 rows
        for value in row:
            c.drawString(40, y, str(value))
            y -= 12
        y -= 8

        if y < 40:
            c.showPage()
            y = height - 40

    c.save()


def export_chart_pdf(filename, figure):
    c = canvas.Canvas(filename, pagesize=A4)
    figure.savefig("temp_chart.png")
    c.drawImage("temp_chart.png", 40, 200, width=500, height=350)
    c.save()
