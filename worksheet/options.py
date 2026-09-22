"""Shared command-line options for worksheet generators."""

import argparse
from collections.abc import Sequence
from dataclasses import dataclass


@dataclass(frozen=True)
class WorksheetOptions:
    """Store command-line settings for one worksheet.

    Attributes:
        output: Destination PDF path.
        rows: Number of problem rows.
        cols: Number of problem columns.
        font_size: Problem text size in points.
    """

    output: str
    rows: int
    cols: int
    font_size: int

    @property
    def problem_count(self) -> int:
        """Return the number of problems required to fill the worksheet."""
        return self.rows * self.cols


class _ArgumentNamespace(argparse.Namespace):
    output: str = ""
    rows: int = 0
    cols: int = 0
    font_size: int = 0


def _positive_integer(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return parsed


def parse_options(
    default_output: str,
    args: Sequence[str] | None = None,
) -> WorksheetOptions:
    """Parse the options shared by all worksheet entry points.

    Args:
        default_output: PDF filename used when ``--output`` is omitted.
        args: Arguments to parse, or ``None`` to read the process arguments.

    Returns:
        Validated output and worksheet layout options.

    Raises:
        SystemExit: If an option is invalid or help is requested.
    """
    parser = argparse.ArgumentParser()
    _ = parser.add_argument("--output", default=default_output)
    _ = parser.add_argument("--rows", type=_positive_integer, default=8)
    _ = parser.add_argument("--cols", type=_positive_integer, default=5)
    _ = parser.add_argument("--font-size", type=_positive_integer, default=20)
    parsed = parser.parse_args(args, namespace=_ArgumentNamespace())
    return WorksheetOptions(
        output=parsed.output,
        rows=parsed.rows,
        cols=parsed.cols,
        font_size=parsed.font_size,
    )
