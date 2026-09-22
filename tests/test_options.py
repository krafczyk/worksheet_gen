"""Regression tests for configurable command-line operation distributions."""

import contextlib
import io
import unittest

from worksheet.options import parse_options


class OperationOptionsTests(unittest.TestCase):
    """Verify operation parsing and rejection of invalid command-line input."""

    def test_default_operations(self) -> None:
        """Generic defaults must give all supported operators equal weight."""
        options = parse_options("test.pdf", 1, 9, [])
        self.assertEqual(options.operations, (("+", 1.0), ("-", 1.0), ("x", 1.0)))

    def test_custom_defaults(self) -> None:
        """Entry points may supply bare or weighted default operations."""
        options = parse_options("test.pdf", 1, 9, [], default_operations=["+", ("-", 3)])
        self.assertEqual(options.operations, (("+", 1.0), ("-", 3.0)))

    def test_cli_replaces_defaults(self) -> None:
        """The supplied list must replace rather than extend script defaults."""
        options = parse_options(
            "test.pdf", 1, 9,
            ["--operations", "['-', ('x', 2.5)]", "--pages", "2"],
            default_operations=["+"],
        )
        self.assertEqual(options.operations, (("-", 1.0), ("x", 2.5)))
        self.assertEqual(options.problem_count, 80)

    def test_invalid_cli_operations(self) -> None:
        """Malformed literals, unsupported operators, and invalid weights fail."""
        for value in (
            "", "[", "[]", "'+'", "None", "['/']", "[('+',)]", "[('+', '2')]",
            "[('+', -1)]", "[('+', 0)]", "[('+', 1e309)]", "[('+', True)]",
            "__import__('os').getcwd()",
        ):
            with self.subTest(value=value), contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as error:
                    _ = parse_options("test.pdf", 1, 9, ["--operations", value])
                self.assertEqual(error.exception.code, 2)

    def test_invalid_default_operations(self) -> None:
        """Invalid programmatic defaults must raise ValueError."""
        with self.assertRaises(ValueError):
            _ = parse_options("test.pdf", 1, 9, [], default_operations=[])


if __name__ == "__main__":
    _ = unittest.main()
