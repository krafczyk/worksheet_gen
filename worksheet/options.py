"""Shared command-line options for worksheet generators."""

import argparse
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol, cast


@dataclass(frozen=True)
class WorksheetOptions:
    """Store command-line settings for one worksheet.

    Attributes:
        output: Destination PDF path.
        rows: Number of problem rows.
        cols: Number of problem columns.
        font_size: Problem text size in points.
        minimum: Smallest generated operand, inclusive.
        maximum: Largest generated operand, inclusive.
        pages: Number of worksheet pages to generate.
    """

    output: str
    rows: int
    cols: int
    font_size: int
    minimum: int
    maximum: int
    pages: int = 1

    @property
    def problem_count(self) -> int:
        """Return the number of problems required to fill all pages."""
        return self.rows * self.cols * self.pages


class _ArgumentNamespace(Protocol):
    output: str
    rows: int
    cols: int
    font_size: int
    minimum: int
    maximum: int
    pages: int


def _positive_integer(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return parsed


def _non_negative_integer(value: str) -> int:
    parsed = int(value)
    if parsed < 0:
        raise argparse.ArgumentTypeError("must be a non-negative integer")
    return parsed


def parse_options(
    default_output: str,
    default_minimum: int,
    default_maximum: int,
    args: Sequence[str] | None = None,
) -> WorksheetOptions:
    """Parse the options shared by all worksheet entry points.

    Args:
        default_output: PDF filename used when ``--output`` is omitted.
        default_minimum: Smallest generated operand used by default.
        default_maximum: Largest generated operand used by default.
        args: Arguments to parse, or ``None`` to read the process arguments.

    Returns:
        Validated output and worksheet layout options.

    Raises:
        ValueError: If a default range is negative or empty.
        SystemExit: If a command-line option is invalid or help is requested.
    """
    if default_minimum < 0 or default_maximum < 0:
        raise ValueError("default range values must be non-negative")
    if default_minimum > default_maximum:
        raise ValueError("default_minimum cannot exceed default_maximum")

    parser = argparse.ArgumentParser()
    _ = parser.add_argument("--output", default=default_output)
    _ = parser.add_argument("--rows", type=_positive_integer, default=8)
    _ = parser.add_argument("--cols", type=_positive_integer, default=5)
    _ = parser.add_argument("--font-size", type=_positive_integer, default=20)
    _ = parser.add_argument("--pages", type=_positive_integer, default=1)
    _ = parser.add_argument(
        "--minimum",
        type=_non_negative_integer,
        default=default_minimum,
        help="smallest generated operand, inclusive",
    )
    _ = parser.add_argument(
        "--maximum",
        type=_non_negative_integer,
        default=default_maximum,
        help="largest generated operand, inclusive",
    )
    parsed = cast(
        _ArgumentNamespace,
        cast(object, parser.parse_args(args)),
    )
    if parsed.minimum > parsed.maximum:
        parser.error("--minimum cannot exceed --maximum")

    return WorksheetOptions(
        output=parsed.output,
        rows=parsed.rows,
        cols=parsed.cols,
        font_size=parsed.font_size,
        minimum=parsed.minimum,
        maximum=parsed.maximum,
        pages=parsed.pages,
    )
