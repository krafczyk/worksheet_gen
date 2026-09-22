"""Paginated writing worksheets for spelling practice and sentence exercises."""

import math
from collections.abc import Sequence
from dataclasses import dataclass
from os import PathLike, fspath

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen.canvas import Canvas

from .components import LineStyle, draw_instructions, draw_writing_line, wrap_text
from .fonts import DEFAULT_FONT, resolve_font


@dataclass(frozen=True)
class WritingExercise:
    """A printed prompt followed by space for handwriting.

    Attributes:
        prompt: Non-empty plain text, such as a model word or sentence to correct.
    """

    prompt: str


@dataclass(frozen=True)
class WritingLayout:
    """Configure automatically paginated writing exercises on US Letter pages.

    Attributes:
        title: Heading repeated on every page.
        instructions: Wrapped plain-text directions repeated on every page.
        font_size: Prompt text size in points, finite and positive.
        lines_per_exercise: Number of practice guides; zero supports answer keys.
        line_style: ``guided`` or ``baseline`` handwriting guides.
        line_height: Writing space height in points, finite and positive.
        margin: Page margin in points, finite and positive.
        page_size: Page width and height in points, finite and positive.
        font_name: Font name or .ttf path for all text; defaults to bundled Andika.

    Raises:
        ValueError: If dimensions, font, line count, or line style are invalid, or the
            header and even a one-line prompt with its guides cannot fit a page.

    Side Effects:
        Registers the selected font if needed during layout validation.
    """

    title: str = "Writing practice"
    instructions: str = "Read each prompt and write on the lines below."
    font_size: int = 22
    lines_per_exercise: int = 2
    line_style: LineStyle = "guided"
    line_height: float = 28
    margin: float = 40
    page_size: tuple[float, float] = letter
    font_name: str = DEFAULT_FONT

    def __post_init__(self) -> None:
        _ = resolve_font(self.font_name)
        dimensions = (self.font_size, self.line_height, self.margin, *self.page_size)
        if any(not math.isfinite(value) or value <= 0 for value in dimensions):
            raise ValueError("writing layout dimensions must be finite and positive")
        if type(self.lines_per_exercise) is not int or self.lines_per_exercise < 0:
            raise ValueError("lines_per_exercise must be a non-negative integer")
        if self.line_style not in ("guided", "baseline"):
            raise ValueError("line style must be guided or baseline")
        if self.margin * 2 >= min(self.page_size):
            raise ValueError("page margins leave no writing area")
        minimum_block_height = (
            self.font_size + 4 + self.lines_per_exercise * (self.line_height + 12) + 12
        )
        if minimum_block_height > self.content_top - self.margin:
            raise ValueError(
                "layout cannot fit an exercise; reduce instructions, text size, or practice lines"
            )

    @property
    def content_top(self) -> float:
        """Return the first prompt baseline in page points below the wrapped header."""
        available_width = self.page_size[0] - 2 * self.margin
        title_lines = wrap_text(self.title, available_width, 18, self.font_name)
        instruction_lines = wrap_text(
            self.instructions, available_width, 12, self.font_name
        )
        header_height = len(title_lines) * 22 + len(instruction_lines) * 16 + 16
        return self.page_size[1] - self.margin - header_height


def generate_writing_pdf(
    filename: str | PathLike[str],
    exercises: Sequence[WritingExercise],
    layout: WritingLayout,
) -> None:
    """Write exercises to a PDF, keeping each prompt and its guides on one page.

    Args:
        filename: Output PDF path; an existing file is replaced after validation.
        exercises: Non-empty sequence of plain-text writing prompts.
        layout: Heading, instructions, typography, and handwriting configuration.

    Raises:
        ValueError: If the font is invalid, prompts are empty, text cannot fit, or an exercise and the
            repeated header cannot fit a single page. Validated before output opens.
        OSError: If the destination cannot be written.

    Side Effects:
        Creates or replaces a PDF with automatic page breaks and page numbers.
        TrueType fonts are embedded; every text element uses the selected font.
    """
    if not exercises:
        raise ValueError("at least one writing exercise is required")
    width, height = layout.page_size
    available_width = width - 2 * layout.margin
    font_name = resolve_font(layout.font_name)
    start_y = layout.content_top
    prompt_lines = [
        wrap_text(exercise.prompt, available_width, layout.font_size, font_name)
        for exercise in exercises
    ]
    block_heights = [
        len(lines) * (layout.font_size + 4)
        + layout.lines_per_exercise * (layout.line_height + 12)
        + 12
        for lines in prompt_lines
    ]
    if any(not lines for lines in prompt_lines):
        raise ValueError("writing prompts must not be empty")
    if any(block_height > start_y - layout.margin for block_height in block_heights):
        raise ValueError(
            "an exercise cannot fit on a page; reduce text size or practice lines"
        )

    pdf = Canvas(fspath(filename), pagesize=layout.page_size)
    y = layout.margin
    page_number = 0
    for lines, block_height in zip(prompt_lines, block_heights):
        if y - block_height < layout.margin:
            if page_number:
                pdf.showPage()
            page_number += 1
            header_y = draw_instructions(
                pdf,
                layout.title,
                layout.margin,
                height - layout.margin,
                available_width,
                18,
                font_name,
            )
            _ = draw_instructions(
                pdf,
                layout.instructions,
                layout.margin,
                header_y,
                available_width,
                font_name=font_name,
            )
            pdf.setFont(font_name, 10)
            pdf.drawRightString(
                width - layout.margin, layout.margin / 2, str(page_number)
            )
            y = start_y
        pdf.setFont(font_name, layout.font_size)
        for line in lines:
            pdf.drawString(layout.margin, y, line)
            y -= layout.font_size + 4
        for _ in range(layout.lines_per_exercise):
            draw_writing_line(
                pdf,
                layout.margin,
                y,
                available_width,
                layout.line_height,
                layout.line_style,
            )
            y -= layout.line_height + 12
        y -= 12
    pdf.save()
