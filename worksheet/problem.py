"""Arithmetic problem data and individual problem rendering."""

from dataclasses import dataclass

from reportlab.pdfgen.canvas import Canvas


@dataclass(frozen=True)
class Problem:
    """Describe one vertically formatted arithmetic problem.

    Attributes:
        first_operand: Operand shown on the first line.
        second_operand: Operand shown on the second line.
        operator: Arithmetic operator shown beside the second operand.
    """

    first_operand: int
    second_operand: int
    operator: str


def draw_problem(
    pdf: Canvas,
    problem: Problem,
    right_x: float,
    top_y: float,
    font_size: int,
    font_name: str = "Helvetica",
) -> None:
    """Draw one right-aligned arithmetic problem on a PDF canvas.

    Args:
        pdf: ReportLab canvas receiving the problem.
        problem: Arithmetic problem to draw.
        right_x: Right edge of the problem in page points.
        top_y: Baseline of the first operand in page points.
        font_size: Problem text size in points.
        font_name: ReportLab font used to measure the problem text.

    Side Effects:
        Draws two text lines and an answer line on ``pdf``.
    """
    pdf.setFont(font_name, font_size)
    first_line = str(problem.first_operand)
    second_line = f"{problem.operator} {problem.second_operand}"
    first_width = pdf.stringWidth(first_line, font_name, font_size)
    second_width = pdf.stringWidth(second_line, font_name, font_size)

    pdf.drawString(right_x - first_width, top_y, first_line)
    pdf.drawString(right_x - second_width, top_y - font_size, second_line)
    pdf.line(
        right_x - max(first_width, second_width),
        top_y - font_size * 1.2,
        right_x,
        top_y - font_size * 1.2,
    )
