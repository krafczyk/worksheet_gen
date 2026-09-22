"""Page and grid layout for arithmetic worksheets."""

from collections.abc import Sequence
from dataclasses import dataclass
from os import PathLike, fspath

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen.canvas import Canvas

from .components import draw_instructions, wrap_text
from .fonts import DEFAULT_FONT, resolve_font
from .problem import Problem, draw_problem


@dataclass(frozen=True)
class WorksheetLayout:
    """Configure a worksheet's page-wide problem grid.

    Args:
        rows: Number of problem rows. Must be positive.
        cols: Number of problem columns. Must be positive.
        font_size: Problem text size in points. Must be positive.
        page_size: Page width and height in points.
        right_margin: Space between each cell's right edge and its problem.
        top_margin: Space above the first row's first operand.
        instructions: Optional plain-text directions repeated above each grid.
        font_name: Font name or .ttf path for problems and instructions; defaults to Andika.

    Raises:
        ValueError: If the font is invalid, rows, columns, or font size are not positive, or instructions
            cannot fit above the problem grid.

    Side Effects:
        Registers the selected font if needed during layout validation.
    """

    rows: int = 8
    cols: int = 5
    font_size: int = 20
    page_size: tuple[float, float] = letter
    right_margin: float = 50
    top_margin: float = 40
    instructions: str = ""
    font_name: str = DEFAULT_FONT

    def __post_init__(self) -> None:
        _ = resolve_font(self.font_name)
        if self.rows <= 0:
            raise ValueError("rows must be positive")
        if self.cols <= 0:
            raise ValueError("cols must be positive")
        if self.font_size <= 0:
            raise ValueError("font_size must be positive")
        if self.instructions.strip():
            lines = wrap_text(self.instructions, self.page_size[0] - 80, 12, self.font_name)
            header_height = len(lines) * 16 + 12
            minimum_row_height = max(
                self.font_size * 2.5 + 8,
                self.top_margin + self.font_size * 1.2,
            )
            if self.page_size[1] - header_height < self.rows * minimum_row_height:
                raise ValueError("instructions leave too little room for the problem grid")


def draw_worksheet(
    pdf: Canvas,
    problems: Sequence[Problem],
    layout: WorksheetLayout,
) -> None:
    """Draw a complete problem grid on a PDF canvas.

    Args:
        pdf: ReportLab canvas receiving the worksheet.
        problems: Problems in row-major order. The number of problems must
            exactly fill the configured grid.
        layout: Page and grid layout settings.

    Raises:
        ValueError: If the selected font cannot be loaded or the number of problems
            does not match the grid size.

    Side Effects:
        Draws optional instructions and all supplied problems on ``pdf``.
    """
    expected_count = layout.rows * layout.cols
    if len(problems) != expected_count:
        raise ValueError(
            f"expected {expected_count} problems, received {len(problems)}"
        )

    width, height = layout.page_size
    if layout.instructions.strip():
        lines = wrap_text(layout.instructions, width - 80, 12, layout.font_name)
        _ = draw_instructions(
            pdf, layout.instructions, 40, height - 28, width - 80, font_name=layout.font_name
        )
        height -= len(lines) * 16 + 12
    problem_width = width / layout.cols
    problem_height = height / layout.rows
    for index, problem in enumerate(problems):
        row, col = divmod(index, layout.cols)
        right_x = (col + 1) * problem_width - layout.right_margin
        top_y = height - row * problem_height - layout.top_margin
        draw_problem(pdf, problem, right_x, top_y, layout.font_size, layout.font_name)


def generate_pdf(
    filename: str | PathLike[str],
    problems: Sequence[Problem],
    layout: WorksheetLayout,
) -> None:
    """Render one or more complete problem grids to a PDF worksheet.

    Args:
        filename: Destination PDF path.
        problems: Problems in row-major order. The number of problems must be
            a positive multiple of the configured grid size.
        layout: Page, grid, and repeated instruction settings.

    Raises:
        ValueError: If the problems do not fill one or more complete pages.
        OSError: If the destination cannot be written.

    Side Effects:
        Creates or replaces ``filename``. Selected TrueType fonts are embedded.
    """
    problems_per_page = layout.rows * layout.cols
    if not problems or len(problems) % problems_per_page != 0:
        raise ValueError(
            f"expected a positive multiple of {problems_per_page} problems, got {len(problems)}"
        )

    pdf = Canvas(fspath(filename), pagesize=layout.page_size)
    for page_start in range(0, len(problems), problems_per_page):
        page_end = page_start + problems_per_page
        draw_worksheet(pdf, problems[page_start:page_end], layout)
        if page_end < len(problems):
            pdf.showPage()
    pdf.save()
