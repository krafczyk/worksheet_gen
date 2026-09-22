"""Tests for offline font loading, embedding, and font-aware text measurement."""

import tempfile
import re
import unittest
from pathlib import Path
from typing import cast
from unittest.mock import Mock, call, patch

from reportlab.pdfbase.pdfmetrics import getRegisteredFontNames, stringWidth
from reportlab.pdfgen.canvas import Canvas

from worksheet.components import draw_instructions, wrap_text
from worksheet.fonts import DEFAULT_FONT, resolve_font
from worksheet.layout import WorksheetLayout, generate_pdf
from worksheet.problem import Problem, draw_problem
from worksheet.writing import WritingExercise, WritingLayout, generate_writing_pdf


class FontTests(unittest.TestCase):
    """Verify font registration, errors, and TrueType PDF embedding."""

    def test_default_and_standard_fonts(self) -> None:
        """Andika must load offline while standard PDF font names remain usable."""
        self.assertEqual(DEFAULT_FONT, "Andika")
        self.assertEqual(resolve_font(), "Andika")
        self.assertIn("Andika", getRegisteredFontNames())
        for name in ("Helvetica", "Times-Roman", "Courier", "Helvetica-Bold"):
            self.assertEqual(resolve_font(name), name)
        with patch("worksheet.fonts.TTFont") as load:
            self.assertEqual(resolve_font("Andika"), "Andika")
        load.assert_not_called()

    def test_custom_font_paths_and_registration_names(self) -> None:
        """Different paths with the same filename must receive distinct registry names."""
        source = (
            Path(__file__).resolve().parents[1]
            / "worksheet/data/fonts/Andika-Regular.ttf"
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = root / "first" / "my font.ttf"
            second = root / "second" / "my font.ttf"
            first.parent.mkdir()
            second.parent.mkdir()
            _ = first.write_bytes(source.read_bytes())
            _ = second.write_bytes(source.read_bytes())
            name = resolve_font(str(first))
            other = resolve_font(str(second))
            self.assertNotEqual(name, other)
            self.assertEqual(resolve_font(name), name)
            self.assertEqual(resolve_font(str(first)), name)
            self.assertEqual(
                stringWidth("rain", name, 22), stringWidth("rain", other, 22)
            )

    def test_unknown_missing_and_corrupt_fonts(self) -> None:
        """Invalid font choices must report errors instead of silently substituting fonts."""
        with self.assertRaisesRegex(ValueError, "unknown font"):
            _ = resolve_font("not-a-font")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "broken.ttf"
            with self.assertRaisesRegex(ValueError, "cannot load TrueType"):
                _ = resolve_font(str(path))
            _ = path.write_bytes(b"not a font file")
            with self.assertRaisesRegex(ValueError, "cannot load TrueType"):
                _ = resolve_font(str(path))

    def test_missing_bundled_font_does_not_fall_back(self) -> None:
        """An incomplete installation must report its missing default font."""
        with (
            patch("worksheet.fonts.getRegisteredFontNames", return_value=[]),
            patch("worksheet.fonts.TTFont", side_effect=OSError("missing font")),
            self.assertRaisesRegex(ValueError, "Andika-Regular.ttf"),
        ):
            _ = resolve_font()

    def test_default_font_is_embedded_in_both_pdf_layouts(self) -> None:
        """Spelling and arithmetic PDFs must carry Andika rather than require its installation."""
        with tempfile.TemporaryDirectory() as directory:
            writing = Path(directory) / "writing.pdf"
            arithmetic = Path(directory) / "arithmetic.pdf"
            generate_writing_pdf(writing, [WritingExercise("rain")], WritingLayout())
            generate_pdf(arithmetic, [Problem(1, 2, "+")] * 40, WorksheetLayout())
            for path in (writing, arithmetic):
                with self.subTest(path=path):
                    data = path.read_bytes()
                    self.assertIn(b"/FontFile2", data)
                    self.assertTrue(
                        re.search(rb"/BaseFont /[A-Z]{6}\+Andika\b", data) is not None
                    )


class FontMeasurementTests(unittest.TestCase):
    """Keep text wrapping and alignment consistent with the rendered font."""

    def test_wrapping_uses_selected_font_widths(self) -> None:
        """The same text and width must wrap differently for genuinely different metrics."""
        text = "iiii iiii iiii"
        self.assertEqual(wrap_text(text, 70, 12, "Helvetica"), (text,))
        self.assertEqual(wrap_text(text, 70, 12, "Courier"), ("iiii iiii", "iiii"))

    def test_instruction_measurement_matches_rendering(self) -> None:
        """Directions must use the requested face for both line wrapping and drawing."""
        with patch("worksheet.components.wrap_text", wraps=wrap_text) as wrap:
            with patch("worksheet.components.Canvas", autospec=True) as canvas:
                pdf = cast(Canvas, cast(object, canvas.return_value))
                _ = draw_instructions(
                    pdf, "iiii iiii iiii", 40, 700, 70, font_name="Courier"
                )
            wrap.assert_called_once_with("iiii iiii iiii", 70, 12, "Courier")
        cast(Mock, pdf.setFont).assert_called_once_with("Courier", 12)
        cast(Mock, pdf.drawString).assert_has_calls(
            [
                call(40, 700, "iiii iiii"),
                call(40, 684, "iiii"),
            ]
        )

    def test_arithmetic_measurement_matches_rendering(self) -> None:
        """Problem operands must be right-aligned using the selected face's widths."""
        with patch("worksheet.problem.Canvas", autospec=True) as canvas:
            pdf = cast(Canvas, cast(object, canvas.return_value))
            cast(Mock, pdf.stringWidth).side_effect = stringWidth
            draw_problem(pdf, Problem(12, 3, "+"), 100, 700, 20, "Courier")
        cast(Mock, pdf.stringWidth).assert_has_calls(
            [
                call("12", "Courier", 20),
                call("+ 3", "Courier", 20),
            ]
        )
        cast(Mock, pdf.setFont).assert_called_once_with("Courier", 20)
        cast(Mock, pdf.drawString).assert_has_calls(
            [
                call(76, 700, "12"),
                call(64, 680, "+ 3"),
            ]
        )


if __name__ == "__main__":
    _ = unittest.main()
