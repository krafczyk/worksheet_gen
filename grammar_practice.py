"""Generate capitalization/final-period worksheets from OpenCode or saved sentences."""

import argparse
import json
from dataclasses import replace
from pathlib import Path
from typing import Protocol, cast

from worksheet.components import LineStyle
from worksheet.fonts import DEFAULT_FONT
from worksheet.grammar import generate_sentences, parse_sentences, sentence_exercises
from worksheet.writing import WritingExercise, WritingLayout, generate_writing_pdf


class _Arguments(Protocol):
    grade: int
    count: int | None
    model: str | None
    server: str | None
    opencode_command: list[str] | None
    sentences: str | None
    save_sentences: str | None
    timeout: float
    output: str
    answer_key: str | None
    instructions: str
    line_style: LineStyle | None
    lines_per_sentence: int
    font_size: int
    font_name: str


def main() -> None:
    """Write grammar exercises, optionally saving source JSON and an answer-key PDF.

    Requires either an explicit provider/model for an LLM call or a local sentence
    bank for offline use. An optional --server host:port uses an existing trusted
    OpenCode server's default agent and configuration for the model request.
    Repeat --opencode-command to select launcher prefixes in fallback order;
    fallback happens only when an executable cannot be found before starting.
    A {args} placeholder supports shell command-string launchers such as nvim_shell -c.
    Source sentences are lowercased and lose their final
    period; the originals are the answers. Raises SystemExit for help or invalid
    input, provider, layout, and filesystem failures. LLM use may incur charges and
    retains OpenCode session history; all generated content needs adult review.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    _ = parser.add_argument("--grade", type=int, choices=range(1, 6), required=True)
    source = parser.add_mutually_exclusive_group(required=True)
    _ = source.add_argument(
        "--model", help="explicit OpenCode provider/model; makes an LLM call"
    )
    _ = source.add_argument("--sentences", help="saved sentence-bank JSON; no LLM call")
    _ = parser.add_argument(
        "--server",
        metavar="HOST:PORT",
        help="existing OpenCode server (host:port or HTTP/HTTPS URL); requires --model",
    )
    _ = parser.add_argument(
        "--opencode-command",
        action="append",
        metavar="COMMAND",
        help="launcher prefix or template, e.g. nvim_shell -c 'opencode {args}'; repeat for missing-executable fallbacks (default: opencode)",
    )
    _ = parser.add_argument(
        "--count", type=int, help="generated count (default 8), or expected saved count"
    )
    _ = parser.add_argument(
        "--save-sentences", help="save validated source JSON for review and reuse"
    )
    _ = parser.add_argument(
        "--timeout", type=float, default=180, help="OpenCode timeout in seconds"
    )
    _ = parser.add_argument("--output", default="grammar_practice.pdf")
    _ = parser.add_argument("--answer-key", help="optional answer-key PDF path")
    _ = parser.add_argument(
        "--instructions",
        default="Rewrite each sentence with correct capital letters and a final period.",
    )
    _ = parser.add_argument("--line-style", choices=("guided", "baseline"))
    _ = parser.add_argument("--lines-per-sentence", type=int, default=2)
    _ = parser.add_argument("--font-size", type=int, default=16)
    _ = parser.add_argument(
        "--font",
        dest="font_name",
        default=DEFAULT_FONT,
        help="font name (default: Andika) or path to a TrueType .ttf file",
    )
    args = cast(_Arguments, cast(object, parser.parse_args()))
    try:
        if args.server is not None and args.model is None:
            raise ValueError(
                "--server requires --model and cannot be used with --sentences"
            )
        if args.opencode_command is not None and args.model is None:
            raise ValueError(
                "--opencode-command requires --model and cannot be used with --sentences"
            )
        paths = [
            Path(path).resolve()
            for path in (
                args.output,
                args.answer_key,
                args.save_sentences,
                args.sentences,
            )
            if path
        ]
        if len(set(paths)) != len(paths):
            raise ValueError(
                "PDF, answer key, saved JSON, and input JSON paths must be distinct"
            )
        if args.lines_per_sentence <= 0:
            raise ValueError("--lines-per-sentence must be positive")
        layout = WritingLayout(
            title=f"Grammar practice - Grade {args.grade}",
            instructions=args.instructions,
            font_size=args.font_size,
            font_name=args.font_name,
            lines_per_exercise=args.lines_per_sentence,
            line_style=args.line_style or ("guided" if args.grade <= 2 else "baseline"),
        )
        if args.sentences is not None:
            sentences = parse_sentences(
                Path(args.sentences).read_text(encoding="utf-8"), args.grade, args.count
            )
        else:
            assert args.model is not None
            sentences = generate_sentences(
                args.grade,
                args.count if args.count is not None else 8,
                args.model,
                args.timeout,
                server=args.server,
                commands=(
                    args.opencode_command
                    if args.opencode_command is not None
                    else ("opencode",)
                ),
            )
        if args.save_sentences is not None:
            _ = Path(args.save_sentences).write_text(
                json.dumps({"grade": args.grade, "sentences": sentences}, indent=2)
                + "\n",
                encoding="utf-8",
            )
        generate_writing_pdf(args.output, sentence_exercises(sentences), layout)
        if args.answer_key is not None:
            answers = [
                WritingExercise(f"{index}. {sentence}")
                for index, sentence in enumerate(sentences, 1)
            ]
            generate_writing_pdf(
                args.answer_key,
                answers,
                replace(
                    layout,
                    title=f"Grammar answers - Grade {args.grade}",
                    instructions="Review these suggested answers before using the worksheet.",
                    lines_per_exercise=0,
                ),
            )
    except (ValueError, OSError, RuntimeError) as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()
