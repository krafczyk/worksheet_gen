"""Offline tests for grade-level word data and rote-spelling entry points."""

import contextlib
import io
import json
import unittest
from typing import cast
from unittest.mock import patch

import spelling_practice
from worksheet.vocabulary import load_words
from worksheet.writing import WritingExercise, WritingLayout


class VocabularyTests(unittest.TestCase):
    """Verify bundled words and custom grade-list validation."""

    def test_all_grades_have_distinct_starter_words(self) -> None:
        """Every supported grade must have forty usable, distinct starter words."""
        for grade in range(1, 6):
            with self.subTest(grade=grade):
                words = load_words(grade)
                self.assertEqual(len(words), 40)
                self.assertEqual(len(set(words)), 40)
                self.assertTrue(
                    all(
                        word.isascii() and word.isalpha() and word.islower()
                        for word in words
                    )
                )

    def test_custom_word_list(self) -> None:
        """A custom source may supply only the requested grade."""
        with patch(
            "worksheet.vocabulary.Path.read_text",
            return_value='{"grades":{"2":["train","rain"]}}',
        ):
            self.assertEqual(load_words(2, "custom.json"), ("train", "rain"))

    def test_invalid_word_lists(self) -> None:
        """Invalid structures, unsupported text, missing grades, and duplicates fail."""
        invalid: tuple[object, ...] = (
            [],
            {},
            {"grades": []},
            {"grades": {"1": []}},
            {"grades": {"2": ["cat"]}},
            {"grades": {"1": ["cat", "cat"]}},
            {"grades": {"1": ["Cat"]}},
            {"grades": {"1": [5]}},
            {"grades": {"1": ["two words"]}},
        )
        for data in invalid:
            with (
                self.subTest(data=data),
                patch(
                    "worksheet.vocabulary.Path.read_text", return_value=json.dumps(data)
                ),
            ):
                with self.assertRaises(ValueError):
                    _ = load_words(1)

    def test_unsupported_grade(self) -> None:
        """Grades outside the supported range must not load a word list."""
        for grade in (0, 6, True):
            with self.subTest(grade=grade), self.assertRaises(ValueError):
                _ = load_words(grade)


class SpellingScriptTests(unittest.TestCase):
    """Verify grade defaults, explicit words, and sampling controls."""

    def test_grade_defaults_and_seeded_sampling(self) -> None:
        """Grades 1-2 use guides, later grades use baselines, and seeds repeat words."""
        for grade in range(1, 6):
            with (
                self.subTest(grade=grade),
                patch(
                    "sys.argv",
                    ["spelling_practice", "--grade", str(grade), "--seed", "42"],
                ),
                patch("spelling_practice.generate_writing_pdf") as render,
            ):
                spelling_practice.main()
                first = cast(list[WritingExercise], render.call_args.args[1])
                layout = cast(WritingLayout, render.call_args.args[2])
                spelling_practice.main()
                self.assertEqual(first, render.call_args.args[1])
                self.assertEqual(len(first), 10)
                self.assertEqual(layout.font_name, "Andika")
                self.assertEqual(len({exercise.prompt for exercise in first}), 10)
                self.assertEqual(
                    layout.line_style, "guided" if grade <= 2 else "baseline"
                )

    def test_explicit_words_and_style(self) -> None:
        """Supplied words must retain order and honor writing and instruction options."""
        with (
            patch(
                "sys.argv",
                [
                    "spelling_practice",
                    "--grade",
                    "5",
                    "--words",
                    "cat",
                    "dog",
                    "--line-style",
                    "guided",
                    "--lines-per-word",
                    "3",
                    "--instructions",
                    "Copy three times.",
                    "--font",
                    "Helvetica",
                ],
            ),
            patch("spelling_practice.generate_writing_pdf") as render,
        ):
            spelling_practice.main()
        self.assertEqual(
            render.call_args.args[1], [WritingExercise("cat"), WritingExercise("dog")]
        )
        layout = cast(WritingLayout, render.call_args.args[2])
        self.assertEqual(layout.font_name, "Helvetica")
        self.assertEqual(
            (layout.line_style, layout.lines_per_exercise, layout.instructions),
            ("guided", 3, "Copy three times."),
        )

    def test_invalid_options_do_not_render(self) -> None:
        """Malformed input and input/output collisions must fail without writing PDFs."""
        for flags in (
            ["--count", "0"],
            ["--count", "41"],
            ["--words", "Cat"],
            ["--lines-per-word", "0"],
            ["--font-size", "0"],
            ["--font", "missing-font"],
            ["--words", "cat", "--word-list", "custom.json"],
            ["--words", "cat", "--count", "2"],
            ["--word-list", "custom.json", "--output", "custom.json"],
        ):
            with (
                self.subTest(flags=flags),
                patch("sys.argv", ["spelling_practice", "--grade", "1", *flags]),
                patch("spelling_practice.generate_writing_pdf") as render,
                contextlib.redirect_stderr(io.StringIO()),
                self.assertRaises(SystemExit),
            ):
                spelling_practice.main()
            render.assert_not_called()


if __name__ == "__main__":
    _ = unittest.main()
