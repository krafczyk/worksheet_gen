"""Reusable plain-text instructions and handwriting guides for PDF worksheets."""

import math
from typing import Literal, TypeAlias, cast

from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen.canvas import Canvas

from .fonts import DEFAULT_FONT, resolve_font

LineStyle: TypeAlias = Literal["guided", "baseline"]
"""Guided handwriting rails or a single bottom writing line."""


def wrap_text(
    text: str, width: float, font_size: float, font_name: str = DEFAULT_FONT
) -> tuple[str, ...]:
    """Wrap plain text to a width in points, retaining explicit paragraph breaks.

    Args:
        text: Text to wrap; whitespace within paragraphs is collapsed.
        width: Available width in PDF points, finite and positive.
        font_size: Font size in points, finite and positive.
        font_name: Font name or .ttf path accepted by ``resolve_font``; defaults
            to bundled Andika. The selected font is used for all measurements.

    Returns:
        Lines that fit the requested width; empty text produces no lines.

    Raises:
        ValueError: If dimensions or the font are invalid, or a word cannot fit.

    Side Effects:
        Lazily registers TrueType fonts through ``resolve_font``.
    """
    if (
        not math.isfinite(width)
        or width <= 0
        or not math.isfinite(font_size)
        or font_size <= 0
    ):
        raise ValueError("text width and font size must be finite and positive")
    font_name = resolve_font(font_name)
    if not text.strip():
        return ()
    lines: list[str] = []
    for paragraph in text.splitlines():
        line = ""
        for word in paragraph.split():
            if stringWidth(word, font_name, font_size) > width:
                raise ValueError("a word is too wide for the available writing area")
            candidate = f"{line} {word}" if line else word
            if stringWidth(candidate, font_name, font_size) > width:
                lines.append(line)
                line = word
            else:
                line = candidate
        lines.append(line)
    return tuple(lines)


def draw_instructions(
    pdf: Canvas,
    text: str,
    x: float,
    y: float,
    width: float,
    font_size: float = 12,
    font_name: str = DEFAULT_FONT,
) -> float:
    """Draw wrapped instructions and return the next text baseline in points.

    Args:
        pdf: Canvas receiving plain text; graphics state is restored.
        text: Instructions, with optional newline-separated paragraphs.
        x: Left edge in page points.
        y: First text baseline in page points.
        width: Available text width in points.
        font_size: Text size in points; line spacing is 4 points larger.
        font_name: Font name or .ttf path; defaults to bundled Andika.

    Raises:
        ValueError: If dimensions or font are invalid, or an instruction cannot fit.

    Side Effects:
        Registers the font if needed and draws instructions without changing page state.
    """
    font_name = resolve_font(font_name)
    lines = wrap_text(text, width, font_size, font_name)
    pdf.saveState()
    try:
        pdf.setFont(font_name, font_size)
        for line in lines:
            pdf.drawString(x, y, line)
            y -= font_size + 4
    finally:
        pdf.restoreState()
    return y


def draw_writing_line(
    pdf: Canvas,
    x: float,
    top_y: float,
    width: float,
    height: float = 28,
    style: LineStyle = "guided",
) -> None:
    """Draw a handwriting guide, preserving the canvas graphics state.

    Args:
        pdf: Destination ReportLab canvas.
        x: Left edge in points.
        top_y: Top rail position in points.
        width: Length of each rail in points, finite and positive.
        height: Distance from top to bottom rail, finite and positive.
        style: ``guided`` draws solid top/bottom and dashed middle rails;
            ``baseline`` draws only the bottom rail at ``top_y - height``.

    Raises:
        ValueError: If the style or dimensions are invalid.

    Side Effects:
        Draws two solid rails and one dashed rail, or one solid baseline.
    """
    if cast(str, style) not in ("guided", "baseline"):
        raise ValueError("line style must be guided or baseline")
    if (
        not math.isfinite(width)
        or width <= 0
        or not math.isfinite(height)
        or height <= 0
    ):
        raise ValueError("writing line width and height must be finite and positive")
    pdf.saveState()
    try:
        pdf.setLineWidth(0.6)
        pdf.setStrokeGray(0.45)
        pdf.setDash()
        pdf.line(x, top_y - height, x + width, top_y - height)
        if style == "guided":
            pdf.line(x, top_y, x + width, top_y)
            pdf.setDash(3, 3)
            pdf.line(x, top_y - height / 2, x + width, top_y - height / 2)
    finally:
        pdf.restoreState()
