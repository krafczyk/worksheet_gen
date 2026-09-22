"""Deterministic tests for reusable handwriting and paginated writing layouts."""

# Canvas mocks expose dynamic drawing methods.
# pyright: reportAny=false

import unittest
from typing import cast
from unittest.mock import Mock, call, patch

from reportlab.pdfgen.canvas import Canvas

from worksheet.components import (
    LineStyle,
    draw_instructions,
    draw_writing_line,
    wrap_text,
)
from worksheet.layout import WorksheetLayout, generate_pdf
from worksheet.problem import Problem
from worksheet.writing import WritingExercise, WritingLayout, generate_writing_pdf


class WritingComponentTests(unittest.TestCase):
    """Check rail geometry, dashed-line state, and instruction wrapping."""

    def test_guided_rails(self) -> None:
        """Guides must have solid top/bottom and a dashed middle rail."""
        pdf = Mock(spec=Canvas)
        draw_writing_line(cast(Canvas, pdf), 40, 700, 500, 28, "guided")
        self.assertEqual(
            pdf.line.call_args_list,
            [
                call(40, 672, 540, 672),
                call(40, 700, 540, 700),
                call(40, 686, 540, 686),
            ],
        )
        self.assertEqual(pdf.setDash.call_args_list, [call(), call(3, 3)])
        pdf.saveState.assert_called_once()
        pdf.restoreState.assert_called_once()

    def test_baseline_only(self) -> None:
        """Advanced writing guides must use only a solid bottom line."""
        pdf = Mock(spec=Canvas)
        draw_writing_line(cast(Canvas, pdf), 40, 700, 500, style="baseline")
        pdf.line.assert_called_once_with(40, 672, 540, 672)
        pdf.setDash.assert_called_once_with()
        pdf.restoreState.assert_called_once()

    def test_invalid_line_settings(self) -> None:
        """Bad dimensions and styles must fail before drawing anything."""
        for width, height, style in (
            (0, 28, "guided"),
            (50, -1, "guided"),
            (50, 28, "other"),
        ):
            pdf = Mock(spec=Canvas)
            with self.subTest(
                style=style, width=width, height=height
            ), self.assertRaises(ValueError):
                draw_writing_line(
                    cast(Canvas, pdf), 40, 700, width, height, cast(LineStyle, style)
                )
            pdf.saveState.assert_not_called()

    def test_instructions_wrap_and_preserve_paragraphs(self) -> None:
        """Long directions must wrap, preserve newlines, and return usable space."""
        text = "Read each word carefully.\nThen copy it."
        lines = wrap_text(text, 100, 12)
        self.assertGreater(len(lines), 2)
        pdf = Mock(spec=Canvas)
        bottom = draw_instructions(cast(Canvas, pdf), text, 40, 700, 100)
        self.assertEqual(bottom, 700 - len(lines) * 16)
        self.assertEqual(pdf.drawString.call_count, len(lines))
        pdf.restoreState.assert_called_once()

    def test_unbreakable_text_is_rejected(self) -> None:
        """An oversized word must not silently run past the page edge."""
        with self.assertRaises(ValueError):
            _ = wrap_text("unbreakable", 5, 12)


class WritingLayoutTests(unittest.TestCase):
    """Check automatic pagination and preflight validation without PDF files."""

    def test_all_writing_text_uses_selected_font(self) -> None:
        """Headings, directions, page numbers, and prompts must use one selected font."""
        for font in ("Andika", "Courier"):
            pdf = Mock(spec=Canvas)
            with self.subTest(font=font), patch(
                "worksheet.writing.Canvas", return_value=pdf
            ):
                generate_writing_pdf(
                    "test.pdf", [WritingExercise("rain")], WritingLayout(font_name=font)
                )
            self.assertEqual(
                {entry.args[0] for entry in pdf.setFont.call_args_list}, {font}
            )
            self.assertEqual(
                {entry.args[1] for entry in pdf.setFont.call_args_list},
                {10, 12, 18, 22},
            )

    def test_header_measurement_uses_selected_font(self) -> None:
        """Header height must reflect the same face used to render directions."""
        text = "iiii " * 40
        compact = WritingLayout(instructions=text, font_name="Helvetica")
        wide = WritingLayout(instructions=text, font_name="Courier")
        self.assertGreater(compact.content_top, wide.content_top)

    def test_spelling_paginated_without_splitting_blocks(self) -> None:
        """Ten words with two guides each must paginate with repeated instructions."""
        pdf = Mock(spec=Canvas)
        words = [WritingExercise(f"word {index}") for index in range(10)]
        with patch("worksheet.writing.Canvas", return_value=pdf):
            generate_writing_pdf(
                "test.pdf", words, WritingLayout(instructions="Copy each word.")
            )
        self.assertEqual(pdf.showPage.call_count, 1)
        printed = [cast(str, entry.args[2]) for entry in pdf.drawString.call_args_list]
        self.assertEqual(printed.count("Copy each word."), 2)
        for word in words:
            self.assertEqual(printed.count(word.prompt), 1)
        self.assertEqual(pdf.line.call_count, 60)
        for entry in pdf.line.call_args_list:
            _, y1, _, y2 = cast(tuple[float, float, float, float], entry.args)
            self.assertGreaterEqual(min(y1, y2), 40)
        pdf.save.assert_called_once()

    def test_answer_layout_has_no_writing_lines(self) -> None:
        """Zero-line layouts must support compact answer-key pages."""
        pdf = Mock(spec=Canvas)
        with patch("worksheet.writing.Canvas", return_value=pdf):
            generate_writing_pdf(
                "test.pdf",
                [WritingExercise("The bird can sing.")],
                WritingLayout(lines_per_exercise=0),
            )
        pdf.line.assert_not_called()
        pdf.save.assert_called_once()

    def test_wrapped_prompt_stays_with_guides(self) -> None:
        """Multi-line sentences must wrap rather than clip horizontally."""
        pdf = Mock(spec=Canvas)
        prompt = "The small bird likes to sing in the garden on a sunny morning."
        with patch("worksheet.writing.Canvas", return_value=pdf):
            generate_writing_pdf(
                "test.pdf",
                [WritingExercise(prompt)],
                WritingLayout(page_size=(350, 792)),
            )
        printed = [cast(str, entry.args[2]) for entry in pdf.drawString.call_args_list]
        self.assertNotIn(prompt, printed)
        self.assertEqual(pdf.line.call_count, 6)

    def test_invalid_exercises_do_not_open_output(self) -> None:
        """Empty or overflowing worksheets must not truncate the destination."""
        for exercises, layout in (
            ([], WritingLayout()),
            ([WritingExercise(" ")], WritingLayout()),
            ([WritingExercise("a" * 100)], WritingLayout()),
        ):
            with self.subTest(exercises=exercises), patch(
                "worksheet.writing.Canvas"
            ) as canvas:
                with self.assertRaises(ValueError):
                    generate_writing_pdf("test.pdf", exercises, layout)
                canvas.assert_not_called()

    def test_invalid_layouts(self) -> None:
        """Invalid typography, page sizes, and line counts must fail early."""
        with self.assertRaises(ValueError):
            _ = WritingLayout(font_size=0)
        with self.assertRaises(ValueError):
            _ = WritingLayout(lines_per_exercise=-1)
        with self.assertRaises(ValueError):
            _ = WritingLayout(line_height=float("nan"))
        with self.assertRaises(ValueError):
            _ = WritingLayout(margin=400)
        with self.assertRaises(ValueError):
            _ = WritingLayout(lines_per_exercise=100)
        with self.assertRaises(ValueError):
            _ = WritingLayout(instructions="directions\n" * 100)

    def test_arithmetic_instructions_repeat_per_page(self) -> None:
        """Arithmetic pages must share the instruction component without losing problems."""
        pdf = Mock(spec=Canvas)
        pdf.stringWidth.return_value = 20.0
        layout = WorksheetLayout(instructions="Solve each problem.")
        with patch("worksheet.layout.Canvas", return_value=pdf):
            generate_pdf("test.pdf", [Problem(1, 2, "+")] * 80, layout)
        printed = [cast(str, entry.args[2]) for entry in pdf.drawString.call_args_list]
        self.assertEqual(printed.count("Solve each problem."), 2)
        self.assertEqual(printed.count("+ 2"), 80)
        self.assertEqual(pdf.showPage.call_count, 1)
        self.assertEqual(
            {entry.args[0] for entry in pdf.setFont.call_args_list}, {"Andika"}
        )

    def test_arithmetic_header_must_fit(self) -> None:
        """Long instructions must not consume the arithmetic problem area."""
        with self.assertRaises(ValueError):
            _ = WorksheetLayout(instructions="instructions\n" * 100)

    def test_dense_arithmetic_grid_does_not_clip_answer_lines(self) -> None:
        """Header validation must account for top margins and the final answer line."""
        with self.assertRaises(ValueError):
            _ = WorksheetLayout(
                rows=12, font_size=20, instructions="Solve each problem."
            )
        pdf = Mock(spec=Canvas)
        pdf.stringWidth.return_value = 20.0
        with patch("worksheet.layout.Canvas", return_value=pdf):
            generate_pdf(
                "test.pdf",
                [Problem(1, 2, "+")] * 55,
                WorksheetLayout(rows=11, instructions="Solve each problem."),
            )
        for entry in pdf.line.call_args_list:
            self.assertGreaterEqual(cast(float, entry.args[1]), 0)
        _ = WorksheetLayout(rows=12, font_size=20, instructions="")


if __name__ == "__main__":
    _ = unittest.main()
