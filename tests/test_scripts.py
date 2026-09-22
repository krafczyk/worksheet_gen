"""Verify operation configuration is wired through every worksheet script."""

import contextlib
import io
import unittest
from typing import cast
from unittest.mock import patch

import mad_minute
import mad_minute_add
import mad_minute_addsub
import mad_minute_mult
from worksheet import Problem, WorksheetLayout


class WorksheetScriptTests(unittest.TestCase):
    """Exercise CLI-to-renderer behavior without writing output files."""

    def test_script_defaults(self) -> None:
        """Existing scripts retain their ranges and operation presets."""
        for name, main, operators, maximum in (
            ("mad_minute", mad_minute.main, ("+", "-", "x"), 9),
            ("mad_minute_add", mad_minute_add.main, ("+",), 9),
            ("mad_minute_addsub", mad_minute_addsub.main, ("+", "-"), 19),
            ("mad_minute_mult", mad_minute_mult.main, ("x",), 6),
        ):
            with (
                self.subTest(script=name),
                patch("sys.argv", [name]),
                patch(f"{name}.sample_problems", return_value=[]) as sample,
                patch(f"{name}.generate_pdf") as render,
            ):
                main()
                sample.assert_called_once_with(
                    40, minimum_operand=1, maximum_operand=maximum,
                    operations=tuple((operator, 1.0) for operator in operators),
                )
                self.assertEqual(render.call_args.args[0], f"{name}.pdf")

    def test_all_scripts_accept_operation_overrides(self) -> None:
        """Every script must honor weighted operations and existing layout flags."""
        for name, main in (
            ("mad_minute", mad_minute.main),
            ("mad_minute_add", mad_minute_add.main),
            ("mad_minute_addsub", mad_minute_addsub.main),
            ("mad_minute_mult", mad_minute_mult.main),
        ):
            with (
                self.subTest(script=name),
                patch("sys.argv", [
                    name, "--operations", "[('+', 0), ('-', 2)]",
                    "--minimum", "2", "--maximum", "7", "--pages", "2",
                    "--rows", "3", "--cols", "4", "--font-size", "18",
                    "--output", "custom.pdf",
                ]),
                patch(f"{name}.generate_pdf") as render,
            ):
                main()
                render.assert_called_once()
                filename, problems, layout = cast(
                    tuple[str, list[Problem], WorksheetLayout], render.call_args.args
                )
                self.assertEqual(filename, "custom.pdf")
                self.assertEqual(len(problems), 24)
                self.assertEqual({p.operator for p in problems}, {"-"})
                self.assertTrue(all(2 <= p.second_operand <= p.first_operand <= 7 for p in problems))
                self.assertEqual((layout.rows, layout.cols, layout.font_size), (3, 4, 18))

    def test_invalid_operations_do_not_render(self) -> None:
        """Invalid input must fail before creating or replacing the output PDF."""
        with (
            patch("sys.argv", ["mad_minute", "--operations", "[]"]),
            patch.object(mad_minute, "generate_pdf") as render,
            contextlib.redirect_stderr(io.StringIO()),
            self.assertRaises(SystemExit),
        ):
            mad_minute.main()
        render.assert_not_called()


if __name__ == "__main__":
    _ = unittest.main()
