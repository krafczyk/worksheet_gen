"""Generate offline rote-spelling worksheets from grade-level or supplied words."""

import argparse
import random
import re
from pathlib import Path
from typing import Protocol, cast

from worksheet.components import LineStyle
from worksheet.fonts import DEFAULT_FONT
from worksheet.vocabulary import load_words
from worksheet.writing import WritingExercise, WritingLayout, generate_writing_pdf


class _Arguments(Protocol):
    grade: int
    count: int | None
    words: list[str] | None
    word_list: str | None
    seed: int | None
    output: str
    instructions: str
    line_style: LineStyle | None
    lines_per_word: int
    font_size: int
    font_name: str


def main() -> None:
    """Parse CLI arguments and write an automatically paginated spelling PDF.

    Grade 1-2 defaults use guided handwriting; grades 3-5 use baselines. Words
    are sampled without replacement, or supplied explicitly in print order.
    Raises SystemExit for help, invalid inputs, or unreadable word lists, and
    OSError if PDF output fails. No network or LLM is used.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    _ = parser.add_argument("--grade", type=int, choices=range(1, 6), required=True)
    selection = parser.add_mutually_exclusive_group()
    _ = selection.add_argument("--count", type=int, help="words to sample; default 10")
    _ = selection.add_argument(
        "--words", nargs="+", help="explicit lowercase words, in print order"
    )
    _ = parser.add_argument(
        "--word-list", help="custom grade-list JSON instead of bundled words"
    )
    _ = parser.add_argument("--seed", type=int, help="repeatable word selection")
    _ = parser.add_argument("--output", default="spelling_practice.pdf")
    _ = parser.add_argument(
        "--instructions", default="Read each word. Copy it on the lines below."
    )
    _ = parser.add_argument("--line-style", choices=("guided", "baseline"))
    _ = parser.add_argument("--lines-per-word", type=int, default=2)
    _ = parser.add_argument("--font-size", type=int, default=22)
    _ = parser.add_argument(
        "--font",
        dest="font_name",
        default=DEFAULT_FONT,
        help="font name (default: Andika) or path to a TrueType .ttf file",
    )
    args = cast(_Arguments, cast(object, parser.parse_args()))
    try:
        if (
            args.word_list is not None
            and Path(args.word_list).resolve() == Path(args.output).resolve()
        ):
            raise ValueError("output PDF and input word list paths must be distinct")
        if args.lines_per_word <= 0:
            raise ValueError("--lines-per-word must be positive")
        if args.words is not None:
            if args.word_list is not None:
                raise ValueError("--words cannot be combined with --word-list")
            if any(not re.fullmatch(r"[a-z]{1,30}", word) for word in args.words):
                raise ValueError(
                    "--words must contain 1-30 lowercase ASCII letters each"
                )
            words = args.words
        else:
            vocabulary = load_words(args.grade, args.word_list)
            count = args.count if args.count is not None else 10
            if not 1 <= count <= len(vocabulary):
                raise ValueError(f"--count must be between 1 and {len(vocabulary)}")
            words = random.Random(args.seed).sample(vocabulary, count)
        layout = WritingLayout(
            title=f"Spelling practice - Grade {args.grade}",
            instructions=args.instructions,
            font_size=args.font_size,
            font_name=args.font_name,
            lines_per_exercise=args.lines_per_word,
            line_style=args.line_style or ("guided" if args.grade <= 2 else "baseline"),
        )
    except (ValueError, OSError) as error:
        parser.error(str(error))
    try:
        generate_writing_pdf(
            args.output, [WritingExercise(word) for word in words], layout
        )
    except ValueError as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()
