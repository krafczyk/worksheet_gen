"""Credential-free tests for sentence validation and the OpenCode boundary."""

import contextlib
import io
import json
import os
import shlex
import subprocess
import sys
import unittest
from typing import cast
from unittest.mock import patch

import grammar_practice
from worksheet.grammar import generate_sentences, parse_sentences, sentence_exercises
from worksheet.writing import WritingExercise, WritingLayout


def _bank() -> str:
    return json.dumps(
        {"grade": 2, "sentences": ["The small bird can sing.", "I like to read."]}
    )


class SentenceTests(unittest.TestCase):
    """Validate sentence banks before deriving exercises and answer keys."""

    def test_valid_bank_and_exercise_transformation(self) -> None:
        """Exercise errors must be deterministic and preserve original answers."""
        sentences = parse_sentences(_bank(), 2, 2)
        self.assertEqual(sentences, ("The small bird can sing.", "I like to read."))
        self.assertEqual(
            sentence_exercises(sentences),
            [
                WritingExercise("1. the small bird can sing"),
                WritingExercise("2. i like to read"),
            ],
        )

    def test_invalid_sentence_banks(self) -> None:
        """Invalid JSON structures, counts, grades, and sentence text must fail."""
        for text in (
            "not json",
            "[]",
            "{}",
            '{"grade":2,"sentences":[]}',
            '{"grade":1,"sentences":["The bird can sing."]}',
            '{"grade":true,"sentences":["The bird can sing."]}',
            '{"grade":2,"sentences":[5]}',
            '{"grade":2,"sentences":["the bird can sing."]}',
            '{"grade":2,"sentences":["The bird can sing"]}',
            '{"grade":2,"sentences":["The bird can sing. The sun shines."]}',
            '{"grade":2,"sentences":["The  bird can sing."]}',
            '{"grade":2,"sentences":["The bird can sing.","The bird can sing."]}',
        ):
            with self.subTest(text=text), self.assertRaises(ValueError):
                _ = parse_sentences(text, 2)
        with self.assertRaises(ValueError):
            _ = parse_sentences(_bank(), 2, 3)


class OpenCodeTests(unittest.TestCase):
    """Test launcher contracts without invoking OpenCode, a model, or credentials."""

    def test_container_launcher_preserves_arguments(self) -> None:
        """A launcher prefix must receive all OpenCode arguments without a shell."""
        result = subprocess.CompletedProcess(
            ["nvim_shell"],
            0,
            stdout=json.dumps({"type": "text", "part": {"text": _bank()}}),
            stderr="",
        )
        with patch("worksheet.grammar.subprocess.run", return_value=result) as run:
            self.assertEqual(
                generate_sentences(
                    2,
                    2,
                    "p/m",
                    server="127.0.0.1:4096",
                    commands=("nvim_shell opencode",),
                ),
                parse_sentences(_bank(), 2),
            )
        arguments = cast(list[str], run.call_args.args[0])
        self.assertEqual(
            arguments[:6],
            [
                "nvim_shell",
                "opencode",
                "--pure",
                "run",
                "--attach",
                "http://127.0.0.1:4096",
            ],
        )
        self.assertTrue(arguments[-1].startswith("Create exactly 2"))
        self.assertFalse(run.call_args.kwargs.get("shell", False))

    def test_quoted_and_relative_launcher_paths(self) -> None:
        """Quoted paths and arguments must survive tokenization and temporary cwd changes."""
        result = subprocess.CompletedProcess(
            [],
            0,
            stdout=json.dumps({"type": "text", "part": {"text": _bank()}}),
            stderr="",
        )
        with patch("worksheet.grammar.subprocess.run", return_value=result) as run:
            _ = generate_sentences(
                2, 2, "p/m", commands=('"./tools with spaces/launcher" "opencode cli"',)
            )
        arguments = cast(list[str], run.call_args.args[0])
        self.assertEqual(
            arguments[:4],
            [
                os.path.abspath("./tools with spaces/launcher"),
                "opencode cli",
                "--pure",
                "run",
            ],
        )

    def test_command_template_passes_one_shell_string(self) -> None:
        """nvim_shell -c must receive the options and prompt inside its command string."""
        result = subprocess.CompletedProcess(
            [],
            0,
            stdout=json.dumps({"type": "text", "part": {"text": _bank()}}),
            stderr="",
        )
        for server in (None, "127.0.0.1:4096"):
            with (
                self.subTest(server=server),
                patch("worksheet.grammar.subprocess.run", return_value=result) as run,
            ):
                _ = generate_sentences(2, 2, "p/m", server=server)
                direct = cast(list[str], run.call_args.args[0])
                _ = generate_sentences(
                    2,
                    2,
                    "p/m",
                    server=server,
                    commands=("nvim_shell -c 'opencode {args}'",),
                )
                wrapped = cast(list[str], run.call_args.args[0])
                self.assertEqual(len(wrapped), 3)
                self.assertEqual(wrapped[:2], ["nvim_shell", "-c"])
                self.assertEqual(shlex.split(wrapped[2]), direct)
                self.assertFalse(run.call_args.kwargs.get("shell", False))

    def test_missing_launcher_uses_next_candidate(self) -> None:
        """Only a missing executable may advance to the next ordered launcher."""
        result = subprocess.CompletedProcess(
            [],
            0,
            stdout=json.dumps({"type": "text", "part": {"text": _bank()}}),
            stderr="",
        )
        with patch(
            "worksheet.grammar.subprocess.run",
            side_effect=[FileNotFoundError(), result],
        ) as run:
            _ = generate_sentences(
                2, 2, "p/m", commands=("opencode", "nvim_shell -c 'opencode {args}'")
            )
        self.assertEqual(run.call_count, 2)
        first = cast(list[str], run.call_args_list[0].args[0])
        second = cast(list[str], run.call_args_list[1].args[0])
        self.assertEqual(first[0], "opencode")
        self.assertEqual(second[:2], ["nvim_shell", "-c"])
        self.assertEqual(first, shlex.split(second[2]))

    def test_successful_launcher_stops_search(self) -> None:
        """Successful generation must not run another configured candidate."""
        result = subprocess.CompletedProcess(
            [],
            0,
            stdout=json.dumps({"type": "text", "part": {"text": _bank()}}),
            stderr="",
        )
        with patch("worksheet.grammar.subprocess.run", return_value=result) as run:
            _ = generate_sentences(
                2, 2, "p/m", commands=("opencode", "nvim_shell opencode")
            )
        run.assert_called_once()

    def test_all_launchers_missing(self) -> None:
        """Exhausted candidates must give an actionable launcher configuration error."""
        with patch(
            "worksheet.grammar.subprocess.run", side_effect=FileNotFoundError()
        ) as run:
            with self.assertRaisesRegex(
                RuntimeError, "no configured OpenCode launcher was found"
            ):
                _ = generate_sentences(
                    2, 2, "p/m", commands=("opencode", "nvim_shell opencode")
                )
        self.assertEqual(run.call_count, 2)

    def test_started_failure_never_tries_another_launcher(self) -> None:
        """Wrapper failures, invalid output, timeouts, and permission errors must not retry."""
        failures = (
            subprocess.CompletedProcess(
                [], 127, stdout="", stderr="missing inner command"
            ),
            subprocess.CompletedProcess([], 1, stdout="", stderr="failed"),
            subprocess.CompletedProcess([], 0, stdout="not JSON", stderr=""),
            subprocess.TimeoutExpired("launcher", 1),
            PermissionError("not executable"),
        )
        for failure in failures:
            with (
                self.subTest(failure=failure),
                patch("worksheet.grammar.subprocess.run", side_effect=[failure]) as run,
            ):
                with self.assertRaises(RuntimeError):
                    _ = generate_sentences(
                        2,
                        2,
                        "p/m",
                        commands=("nvim_shell -c 'opencode {args}'", "opencode"),
                    )
                run.assert_called_once()

    def test_invalid_command_prefixes_fail_before_launch(self) -> None:
        """Empty prefixes, malformed quotes, and NULs must fail before any model call."""
        for commands in (
            (),
            "opencode",
            ("",),
            ("  ",),
            ('"" opencode',),
            ("opencode", "'"),
            ("open\x00code",),
            ("{args}",),
            ("wrapper -c 'opencode {args} {args}'",),
            ("wrapper -c '{args}' '{args}'",),
        ):
            with (
                self.subTest(commands=commands),
                patch("worksheet.grammar.subprocess.run") as run,
            ):
                with self.assertRaises(ValueError):
                    _ = generate_sentences(2, 2, "p/m", commands=commands)
                run.assert_not_called()

    def test_real_subprocess_launcher_without_a_model(self) -> None:
        """A local Python fake launcher verifies real argument transport without network use."""
        program = (
            "import json, sys; "
            + "assert sys.argv[1:5] == ['--pure', 'run', '--attach', 'http://127.0.0.1:4096']; "
            + "assert sys.argv[-1].startswith('Create exactly 2'); "
            + "print(json.dumps({'type': 'text', 'part': {'text': "
            + repr(_bank())
            + "}}))"
        )
        self.assertEqual(
            generate_sentences(
                2,
                2,
                "p/m",
                server="127.0.0.1:4096",
                commands=(shlex.join([sys.executable, "-B", "-c", program]),),
            ),
            parse_sentences(_bank(), 2),
        )

    def test_real_shell_template_preserves_quoted_arguments(self) -> None:
        """One POSIX shell must preserve quotes, substitutions, and the entire JSON prompt."""
        model = "p/model'\";$HOME$(exit${IFS}23)"
        program = (
            "import json, sys; args = sys.argv[1:]; "
            + "assert args[:4] == ['--pure', 'run', '--attach', 'http://127.0.0.1:4096']; "
            + "assert len(args) == 9; assert args[-2] == "
            + repr(model)
            + "; "
            + "assert args[-1].startswith('Create exactly 2'); "
            + "assert '\"grade\": 2' in args[-1]; "
            + "print(json.dumps({'type': 'text', 'part': {'text': "
            + repr(_bank())
            + "}}))"
        )
        template = shlex.join([sys.executable, "-B", "-c", program]) + " {args}"
        self.assertEqual(
            generate_sentences(
                2,
                2,
                model,
                server="127.0.0.1:4096",
                commands=(shlex.join(["sh", "-c", template]),),
            ),
            parse_sentences(_bank(), 2),
        )

    def test_jsonl_text_is_assembled_and_validated(self) -> None:
        """The adapter must parse raw text events and request an isolated tool-denied run."""
        bank = _bank()
        events = [
            {"type": "step_start"},
            {"type": "text", "part": {"text": bank[:20]}},
            {"type": "text", "part": {"text": bank[20:]}},
            {"type": "step_finish"},
        ]
        result = subprocess.CompletedProcess(
            ["opencode"],
            0,
            stdout="\n".join(json.dumps(event) for event in events),
            stderr="",
        )
        with patch("worksheet.grammar.subprocess.run", return_value=result) as run:
            self.assertEqual(
                generate_sentences(2, 2, "provider/model"), parse_sentences(bank, 2)
            )
        arguments = cast(list[str], run.call_args.args[0])
        self.assertEqual(arguments[:4], ["opencode", "--pure", "run", "--agent"])
        self.assertIn("json", arguments)
        self.assertIn("provider/model", arguments)
        self.assertNotIn("--auto", arguments)
        self.assertNotIn("--continue", arguments)
        self.assertNotIn("--attach", arguments)
        self.assertEqual(run.call_args.kwargs["timeout"], 180)
        environment = cast(dict[str, str], run.call_args.kwargs["env"])
        self.assertEqual(environment["PWD"], run.call_args.kwargs["cwd"])
        self.assertEqual(environment["OPENCODE_DISABLE_PROJECT_CONFIG"], "1")
        self.assertEqual(environment["OPENCODE_PERMISSION"], '{"*":"deny"}')
        config = cast(
            dict[str, object], json.loads(environment["OPENCODE_CONFIG_CONTENT"])
        )
        self.assertEqual(config["permission"], "deny")
        self.assertEqual(config["share"], "disabled")

    def test_existing_server_addresses(self) -> None:
        """Attached runs must use normalized server addresses and server-side defaults."""
        result = subprocess.CompletedProcess(
            ["opencode"],
            0,
            stdout=json.dumps({"type": "text", "part": {"text": _bank()}}),
            stderr="",
        )
        for server, expected in (
            ("127.0.0.1:4096", "http://127.0.0.1:4096"),
            ("localhost:4096", "http://localhost:4096"),
            ("http://192.168.1.10:4096/", "http://192.168.1.10:4096"),
            ("https://opencode.example:443", "https://opencode.example:443"),
            ("[::1]:4096", "http://[::1]:4096"),
        ):
            with (
                self.subTest(server=server),
                patch("worksheet.grammar.subprocess.run", return_value=result) as run,
            ):
                self.assertEqual(
                    generate_sentences(2, 2, "p/m", server=server),
                    parse_sentences(_bank(), 2),
                )
                run.assert_called_once()
                arguments = cast(list[str], run.call_args.args[0])
                self.assertEqual(
                    arguments[:5], ["opencode", "--pure", "run", "--attach", expected]
                )
                self.assertNotIn("--agent", arguments)
                self.assertNotIn("--dir", arguments)
                self.assertNotIn("--continue", arguments)
                self.assertNotIn("--session", arguments)

    def test_invalid_servers_fail_before_starting_client(self) -> None:
        """Invalid endpoints and embedded credentials must be rejected without leaking input."""
        for server in (
            "",
            "localhost",
            "http://localhost",
            "localhost:0",
            "localhost:65536",
            "localhost:abc",
            "localhost:-1",
            "http://:4096",
            "ftp://localhost:4096",
            "http://user:test-secret@localhost:4096",
            "http://localhost:4096/api",
            "localhost:4096?query=yes",
            "localhost:4096#fragment",
            "localhost:4096?",
            "localhost:4096#",
            "localhost:4096\n",
            " local:4096",
            "local host:4096",
            "http://[::1:4096",
            "http://localhost:4096\\path",
        ):
            with (
                self.subTest(server=server),
                patch("worksheet.grammar.subprocess.run") as run,
            ):
                with self.assertRaises(ValueError) as error:
                    _ = generate_sentences(2, 2, "p/m", server=server)
                self.assertNotIn("test-secret", str(error.exception))
                run.assert_not_called()

    def test_server_authentication_stays_in_environment(self) -> None:
        """OpenCode basic auth must use inherited environment variables, not CLI arguments."""
        result = subprocess.CompletedProcess(
            ["opencode"],
            0,
            stdout=json.dumps({"type": "text", "part": {"text": _bank()}}),
            stderr="",
        )
        credentials = {
            "OPENCODE_SERVER_USERNAME": "test-user",
            "OPENCODE_SERVER_PASSWORD": "test-password",
        }
        with (
            patch.dict("worksheet.grammar.os.environ", credentials),
            patch("worksheet.grammar.subprocess.run", return_value=result) as run,
        ):
            _ = generate_sentences(2, 2, "p/m", server="127.0.0.1:4096")
        environment = cast(dict[str, str], run.call_args.kwargs["env"])
        arguments = cast(list[str], run.call_args.args[0])
        for name, value in credentials.items():
            self.assertEqual(environment[name], value)
            self.assertNotIn(value, arguments)

    def test_attachment_failures_do_not_fall_back(self) -> None:
        """Connection failures and timeouts must never silently start local generation."""
        with patch(
            "worksheet.grammar.subprocess.run",
            return_value=subprocess.CompletedProcess(
                ["opencode"], 1, stdout="", stderr="private diagnostics"
            ),
        ) as run:
            with self.assertRaisesRegex(RuntimeError, "attachment failed") as error:
                _ = generate_sentences(2, 2, "p/m", server="127.0.0.1:4096")
            self.assertNotIn("private", str(error.exception))
            run.assert_called_once()
        with patch(
            "worksheet.grammar.subprocess.run",
            side_effect=subprocess.TimeoutExpired("opencode", 1),
        ) as run:
            with self.assertRaisesRegex(
                RuntimeError, "server request may still be running"
            ):
                _ = generate_sentences(2, 2, "p/m", server="127.0.0.1:4096")
            run.assert_called_once()

    def test_model_not_found_is_reported_before_exit_status(self) -> None:
        """Structured model failures must not be hidden as generic attachment failures."""
        for returncode in (0, 1):
            for key in ("name", "_tag"):
                event = {
                    "type": "error",
                    "error": {
                        key: "ProviderModelNotFoundError",
                        "message": "private provider diagnostics",
                        "data": {"message": "private response body"},
                    },
                }
                result = subprocess.CompletedProcess(
                    ["opencode"],
                    returncode,
                    stdout="\n" + json.dumps(event),
                    stderr="private stderr",
                )
                with (
                    self.subTest(returncode=returncode, key=key),
                    patch(
                        "worksheet.grammar.subprocess.run", return_value=result
                    ) as run,
                    self.assertRaisesRegex(RuntimeError, "model not found") as error,
                ):
                    _ = generate_sentences(
                        3,
                        8,
                        "openai/missing-model",
                        server="127.0.0.1:4096",
                        commands=("opencode", "nvim_shell -c 'opencode {args}'"),
                    )
                self.assertIn("openai/missing-model", str(error.exception))
                self.assertNotIn("private", str(error.exception))
                run.assert_called_once()

    def test_unstructured_failure_output_remains_private(self) -> None:
        """Nonzero exits with unstructured output must not expose raw logs or response data."""
        result = subprocess.CompletedProcess(
            ["opencode"],
            1,
            stdout="private stdout\n[]\n{}",
            stderr="private stderr",
        )
        with patch("worksheet.grammar.subprocess.run", return_value=result):
            with self.assertRaisesRegex(RuntimeError, "attachment failed") as error:
                _ = generate_sentences(
                    3, 8, "openai/missing-model", server="127.0.0.1:4096"
                )
        self.assertNotIn("private", str(error.exception))

    def test_invalid_events_and_responses_fail(self) -> None:
        """Malformed output, provider errors, and tool attempts must not produce exercises."""
        for stdout in (
            "",
            "not json",
            "[]",
            '{"type":"error","error":{"message":"failure"}}',
            '{"type":"tool_use"}',
            '{"type":"text"}',
            '{"type":"text","part":{"text":5}}',
            json.dumps(
                {"type": "text", "part": {"text": "```json\n" + _bank() + "\n```"}}
            ),
            json.dumps(
                {
                    "type": "text",
                    "part": {"text": _bank().replace('"grade": 2', '"grade": 3')},
                }
            ),
        ):
            result = subprocess.CompletedProcess(
                ["opencode"], 0, stdout=stdout, stderr=""
            )
            with (
                self.subTest(stdout=stdout),
                patch("worksheet.grammar.subprocess.run", return_value=result),
            ):
                with self.assertRaises(RuntimeError):
                    _ = generate_sentences(2, 2, "provider/model")

    def test_process_failures(self) -> None:
        """Missing executables, nonzero exits, and timeouts must be actionable failures."""
        for error in (FileNotFoundError(), subprocess.TimeoutExpired("opencode", 1)):
            with (
                self.subTest(error=error),
                patch("worksheet.grammar.subprocess.run", side_effect=error),
            ):
                with self.assertRaises(RuntimeError):
                    _ = generate_sentences(2, 2, "provider/model")
        result = subprocess.CompletedProcess(
            ["opencode"], 1, stdout="", stderr="private provider diagnostics"
        )
        with patch("worksheet.grammar.subprocess.run", return_value=result):
            with self.assertRaises(RuntimeError) as error:
                _ = generate_sentences(2, 2, "provider/model")
            self.assertNotIn("private", str(error.exception))

    def test_invalid_request_does_not_start_opencode(self) -> None:
        """Invalid grades, counts, models, and timeouts must fail before an LLM call."""
        for grade, count, model, timeout in (
            (0, 2, "p/m", 180),
            (2, 0, "p/m", 180),
            (2, 41, "p/m", 180),
            (2, 2, "model", 180),
            (2, 2, "p/m", 0),
            (2, 2, "p/m", float("nan")),
        ):
            with self.subTest(grade=grade, count=count, model=model, timeout=timeout):
                with (
                    patch("worksheet.grammar.subprocess.run") as run,
                    self.assertRaises(ValueError),
                ):
                    _ = generate_sentences(grade, count, model, timeout)
                run.assert_not_called()

    def test_interruption_is_not_retried(self) -> None:
        """User interruption must propagate instead of silently starting another call."""
        with patch(
            "worksheet.grammar.subprocess.run", side_effect=KeyboardInterrupt
        ) as run:
            with self.assertRaises(KeyboardInterrupt):
                _ = generate_sentences(
                    2, 2, "provider/model", commands=("opencode", "nvim_shell opencode")
                )
        run.assert_called_once()


class GrammarScriptTests(unittest.TestCase):
    """Verify offline reuse, answer keys, and explicit LLM invocation."""

    def test_saved_sentences_need_no_llm(self) -> None:
        """Local sentence banks must render exercises and original answers offline."""
        with (
            patch(
                "sys.argv",
                [
                    "grammar_practice",
                    "--grade",
                    "2",
                    "--sentences",
                    "bank.json",
                    "--answer-key",
                    "answers.pdf",
                    "--font",
                    "Courier",
                ],
            ),
            patch("grammar_practice.Path.read_text", return_value=_bank()),
            patch("grammar_practice.generate_sentences") as generate,
            patch("grammar_practice.generate_writing_pdf") as render,
        ):
            grammar_practice.main()
        generate.assert_not_called()
        self.assertEqual(render.call_count, 2)
        answers = cast(list[WritingExercise], render.call_args.args[1])
        self.assertEqual(answers[1].prompt, "2. I like to read.")
        layout = cast(WritingLayout, render.call_args.args[2])
        self.assertEqual(layout.lines_per_exercise, 0)
        self.assertEqual(layout.font_name, "Courier")
        self.assertEqual(
            cast(WritingLayout, render.call_args_list[0].args[2]).font_name, "Courier"
        )

    def test_explicit_model_and_saved_bank(self) -> None:
        """Model generation must honor count/timeout and save validated source sentences."""
        sentences = parse_sentences(_bank(), 2)
        with (
            patch(
                "sys.argv",
                [
                    "grammar_practice",
                    "--grade",
                    "2",
                    "--model",
                    "p/m",
                    "--count",
                    "2",
                    "--timeout",
                    "90",
                    "--save-sentences",
                    "bank.json",
                ],
            ),
            patch(
                "grammar_practice.generate_sentences", return_value=sentences
            ) as generate,
            patch("grammar_practice.Path.write_text") as save,
            patch("grammar_practice.generate_writing_pdf") as render,
        ):
            grammar_practice.main()
        generate.assert_called_once_with(
            2, 2, "p/m", 90, server=None, commands=("opencode",)
        )
        self.assertEqual(
            parse_sentences(cast(str, save.call_args.args[0]), 2), sentences
        )
        render.assert_called_once()
        self.assertEqual(
            cast(WritingLayout, render.call_args.args[2]).font_name, "Andika"
        )

    def test_existing_server_option_reaches_generator(self) -> None:
        """The grammar CLI must forward an existing-server address to generation."""
        with (
            patch(
                "sys.argv",
                [
                    "grammar_practice",
                    "--grade",
                    "2",
                    "--model",
                    "p/m",
                    "--server",
                    "127.0.0.1:4096",
                ],
            ),
            patch(
                "grammar_practice.generate_sentences",
                return_value=parse_sentences(_bank(), 2),
            ) as generate,
            patch("grammar_practice.generate_writing_pdf") as render,
        ):
            grammar_practice.main()
        generate.assert_called_once_with(
            2, 8, "p/m", 180, server="127.0.0.1:4096", commands=("opencode",)
        )
        render.assert_called_once()

    def test_command_candidates_reach_generator_in_order(self) -> None:
        """Repeated command flags must replace defaults and preserve candidate order."""
        with (
            patch(
                "sys.argv",
                [
                    "grammar_practice",
                    "--grade",
                    "2",
                    "--model",
                    "p/m",
                    "--opencode-command",
                    "nvim_shell -c 'opencode {args}'",
                    "--opencode-command",
                    "opencode",
                ],
            ),
            patch(
                "grammar_practice.generate_sentences",
                return_value=parse_sentences(_bank(), 2),
            ) as generate,
            patch("grammar_practice.generate_writing_pdf") as render,
        ):
            grammar_practice.main()
        generate.assert_called_once_with(
            2,
            8,
            "p/m",
            180,
            server=None,
            commands=["nvim_shell -c 'opencode {args}'", "opencode"],
        )
        render.assert_called_once()

    def test_commands_cannot_be_combined_with_offline_source(self) -> None:
        """Explicit launcher options must not be silently ignored in offline mode."""
        with (
            patch(
                "sys.argv",
                [
                    "grammar_practice",
                    "--grade",
                    "2",
                    "--sentences",
                    "bank.json",
                    "--opencode-command",
                    "nvim_shell opencode",
                ],
            ),
            patch("grammar_practice.Path.read_text") as read,
            patch("grammar_practice.generate_sentences") as generate,
            contextlib.redirect_stderr(io.StringIO()),
            self.assertRaises(SystemExit),
        ):
            grammar_practice.main()
        read.assert_not_called()
        generate.assert_not_called()

    def test_server_cannot_be_combined_with_offline_source(self) -> None:
        """An ignored server option in offline mode must fail before reading or writing files."""
        with (
            patch(
                "sys.argv",
                [
                    "grammar_practice",
                    "--grade",
                    "2",
                    "--sentences",
                    "bank.json",
                    "--server",
                    "127.0.0.1:4096",
                ],
            ),
            patch("grammar_practice.generate_sentences") as generate,
            patch("grammar_practice.Path.read_text") as read,
            patch("grammar_practice.generate_writing_pdf") as render,
            contextlib.redirect_stderr(io.StringIO()),
            self.assertRaises(SystemExit),
        ):
            grammar_practice.main()
        generate.assert_not_called()
        read.assert_not_called()
        render.assert_not_called()

    def test_generation_failure_does_not_write_outputs(self) -> None:
        """Provider failure must not create or replace PDF or sentence-bank outputs."""
        with (
            patch(
                "sys.argv",
                [
                    "grammar_practice",
                    "--grade",
                    "2",
                    "--model",
                    "p/m",
                    "--save-sentences",
                    "bank.json",
                ],
            ),
            patch(
                "grammar_practice.generate_sentences",
                side_effect=RuntimeError("provider failed"),
            ),
            patch("grammar_practice.Path.write_text") as save,
            patch("grammar_practice.generate_writing_pdf") as render,
            contextlib.redirect_stderr(io.StringIO()),
            self.assertRaises(SystemExit),
        ):
            grammar_practice.main()
        save.assert_not_called()
        render.assert_not_called()

    def test_paths_must_not_collide(self) -> None:
        """Output paths must not overwrite each other or the input sentence bank."""
        for flags in (
            ["--sentences", "same.json", "--output", "same.json"],
            ["--model", "p/m", "--answer-key", "grammar_practice.pdf"],
        ):
            with (
                self.subTest(flags=flags),
                patch("sys.argv", ["grammar_practice", "--grade", "2", *flags]),
                patch("grammar_practice.generate_sentences") as generate,
                patch("grammar_practice.generate_writing_pdf") as render,
                contextlib.redirect_stderr(io.StringIO()),
                self.assertRaises(SystemExit),
            ):
                grammar_practice.main()
            generate.assert_not_called()
            render.assert_not_called()

    def test_impossible_layout_does_not_call_model(self) -> None:
        """Static layout errors must be rejected before spending a model request."""
        for flags in (
            ["--lines-per-sentence", "100"],
            ["--instructions", "directions\n" * 100],
            ["--font-size", "1000"],
            ["--font", "missing-font"],
        ):
            with (
                self.subTest(flags=flags),
                patch(
                    "sys.argv",
                    ["grammar_practice", "--grade", "2", "--model", "p/m", *flags],
                ),
                patch("grammar_practice.generate_sentences") as generate,
                patch("grammar_practice.generate_writing_pdf") as render,
                contextlib.redirect_stderr(io.StringIO()),
                self.assertRaises(SystemExit),
            ):
                grammar_practice.main()
            generate.assert_not_called()
            render.assert_not_called()


if __name__ == "__main__":
    _ = unittest.main()
