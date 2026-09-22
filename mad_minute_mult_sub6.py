import argparse
import random

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


def generate_problems(rows, cols):
    """Return multiplication operand pairs for a worksheet grid.

    Both operands are randomly selected from one through six.

    Args:
        rows: Number of worksheet rows.
        cols: Number of worksheet columns.

    Returns:
        A list of ``(a, b)`` integer operand pairs in row-major order.
    """
    return [
        (random.randint(1, 6), random.randint(1, 6))
        for _ in range(rows * cols)
    ]


def draw_problems(pdf, problems, rows, cols, width, height, font_size):
    """Draw multiplication problems on a PDF canvas.

    Args:
        pdf: ReportLab canvas receiving the worksheet.
        problems: Operand pairs in row-major order.
        rows: Number of worksheet rows.
        cols: Number of worksheet columns.
        width: Page width in points.
        height: Page height in points.
        font_size: Problem text size in points.
    """
    pdf.setFont("Helvetica", font_size)
    problem_width = width / cols
    problem_height = height / rows

    for row in range(rows):
        for col in range(cols):
            x = (col + 1) * problem_width - 50
            y = height - row * problem_height - 40
            a, b = problems[row * cols + col]
            first_width = pdf.stringWidth(str(a), "Helvetica", font_size)
            second_line = f"x {b}"
            second_width = pdf.stringWidth(second_line, "Helvetica", font_size)

            pdf.drawString(x - first_width, y, str(a))
            pdf.drawString(x - second_width, y - font_size, second_line)
            pdf.line(
                x - max(first_width, second_width),
                y - font_size * 1.2,
                x,
                y - font_size * 1.2,
            )


def generate_pdf(filename, rows=5, cols=5, font_size=14):
    """Generate a multiplication worksheet PDF.

    Args:
        filename: Destination PDF path.
        rows: Number of worksheet rows.
        cols: Number of worksheet columns.
        font_size: Problem text size in points.
    """
    width, height = letter
    pdf = canvas.Canvas(filename, pagesize=letter)
    problems = generate_problems(rows, cols)
    draw_problems(pdf, problems, rows, cols, width, height, font_size)
    pdf.save()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="mad_minute_mult_sub6.pdf")
    args = parser.parse_args()

    generate_pdf(args.output, rows=8, cols=5, font_size=20)
