"""Validated sentence exercises with optional, explicit OpenCode generation."""

import json
import math
import os
import re
import shlex
import subprocess
import tempfile
from collections.abc import Sequence
from typing import cast
from urllib.parse import urlsplit

from .writing import WritingExercise


def parse_sentences(text: str, grade: int, count: int | None = None) -> tuple[str, ...]:
    """Validate a JSON sentence bank for capitalization and final-period practice.

    Args:
        text: JSON object containing ``grade`` and a ``sentences`` list. Sentences
            must be distinct, 3-15 words, at most 120 ASCII characters, begin with
            a capital letter, and end with a period. Letters, spaces, commas, and
            apostrophes are allowed inside the sentence.
        grade: Expected suggested grade, 1-5; must match the bank's grade.
        count: Optional exact expected sentence count, from 1 through 40.

    Returns:
        Between 1 and 40 validated sentences, in source order. Validation checks
        structure, not educational accuracy, appropriateness, or sentence meaning.

    Raises:
        ValueError: If the JSON, grade, count, or any sentence is invalid.
    """
    if type(grade) is not int or grade not in range(1, 6):
        raise ValueError("grade must be between 1 and 5")
    if count is not None and (type(count) is not int or not 1 <= count <= 40):
        raise ValueError("sentence count must be between 1 and 40")
    data = cast(object, json.loads(text))
    if not isinstance(data, dict):
        raise ValueError(
            "sentence JSON must be an object containing grade and sentences"
        )
    record = cast(dict[str, object], data)
    if type(record.get("grade")) is not int or record.get("grade") != grade:
        raise ValueError("sentence bank grade must match --grade")
    values = record.get("sentences")
    if not isinstance(values, list):
        raise ValueError("sentence JSON must contain a sentences list")
    sentences = cast(list[object], values)
    if not 1 <= len(sentences) <= 40 or (count is not None and len(sentences) != count):
        raise ValueError("sentence bank has an invalid number of sentences")
    validated: list[str] = []
    for sentence in sentences:
        if (
            not isinstance(sentence, str)
            or len(sentence) > 120
            or not 3 <= len(sentence.split()) <= 15
            or not re.fullmatch(r"[A-Z][A-Za-z ,']*\.", sentence)
            or sentence != " ".join(sentence.split())
        ):
            raise ValueError(
                "sentences must be short, capitalized ASCII statements ending in a period"
            )
        if sentence.lower() in {previous.lower() for previous in validated}:
            raise ValueError("sentence bank contains duplicate sentences")
        validated.append(sentence)
    return tuple(validated)


def sentence_exercises(sentences: tuple[str, ...]) -> list[WritingExercise]:
    """Turn correct sentences into numbered capitalization/final-period exercises.

    Args:
        sentences: Correct sentences already validated by ``parse_sentences``.

    Returns:
        Prompts with letters lowercased and the final period removed. Internal
        commas and apostrophes are preserved; source sentences form the answer key.
    """
    return [
        WritingExercise(f"{index}. {sentence[:-1].lower()}")
        for index, sentence in enumerate(sentences, 1)
    ]


def generate_sentences(
    grade: int,
    count: int,
    model: str,
    timeout: float = 180,
    *,
    server: str | None = None,
    commands: Sequence[str] = ("opencode",),
) -> tuple[str, ...]:
    """Request a sentence bank through the installed OpenCode CLI's JSONL interface.

    Args:
        grade: Suggested US-English grade, 1-5.
        count: Exact number of sentences, 1-40.
        model: Explicit OpenCode provider/model identifier; credentials are managed
            by the user's existing OpenCode installation, not this application.
        timeout: Finite positive process timeout in seconds, including startup.
        server: Optional existing OpenCode server as ``host:port`` (HTTP) or an
            HTTP/HTTPS URL with an explicit port. IPv6 addresses need brackets.
            Credentials, paths, queries, and fragments are not accepted. Uses
            the server's default agent and configuration, not the local text agent.
            Basic authentication uses inherited ``OPENCODE_SERVER_PASSWORD`` and
            ``OPENCODE_SERVER_USERNAME`` environment variables.
        commands: Ordered launchers, parsed with POSIX shell quoting and started
            without an implicit shell. Defaults to ``("opencode",)``. A template
            such as ``nvim_shell -c 'opencode {args}'`` inserts shell-quoted OpenCode
            arguments at one unquoted ``{args}`` word in the shell command text.
            Without a placeholder, arguments are appended as separate argv entries.
            The placeholder cannot occur in the launcher executable. The next launcher is tried
            only if starting the previous executable raises FileNotFoundError.
            Relative executable paths resolve against the caller's directory.
            Launchers must forward arguments, environment, and raw JSONL stdout.

    Returns:
        Structurally validated sentences. An adult must review educational quality
        and suitability before use; the model's language correctness is not proven.

    Raises:
        ValueError: If arguments are invalid.
        RuntimeError: If OpenCode is missing, times out, fails, requests a tool, or
            returns malformed events or invalid sentence data. No retry once a
            launcher has started, including when a wrapper exits with code 127.
            Structured model-not-found events identify the requested model even
            on a nonzero exit; raw provider messages and stderr are not exposed.
        OSError: If a temporary working directory cannot be created.

    Side Effects:
        Appends or substitutes ``--pure run`` and generation arguments in the launcher
        in a disposable local directory, using the
        provider's network and billing. Without ``server``, requests a tool-denied
        agent and disables project config and external plugins. With ``server``,
        passes ``--attach`` and starts a fresh session on that trusted server;
        local restrictions do not control server tools, plugins, or sharing.
        Server/container work may continue after a timeout or interruption. Never
        resumes a session or falls back to a local model if attachment fails.
        OpenCode retains normal session history. This is not a sandbox.
    """
    if type(grade) is not int or grade not in range(1, 6):
        raise ValueError("grade must be between 1 and 5")
    if type(count) is not int or not 1 <= count <= 40:
        raise ValueError("sentence count must be between 1 and 40")
    if not re.fullmatch(r"[^\s/]+/[^\s]+", model):
        raise ValueError("model must be an explicit provider/model identifier")
    if not math.isfinite(timeout) or timeout <= 0:
        raise ValueError("timeout must be finite and positive")
    if isinstance(commands, (str, bytes)) or not commands:
        raise ValueError("commands must be a non-empty sequence of launcher prefixes")
    prefixes: list[list[str]] = []
    for command in commands:
        try:
            prefix = shlex.split(command)
        except ValueError:
            raise ValueError("OpenCode command prefix has invalid quoting") from None
        if (
            not prefix
            or not prefix[0]
            or any("\x00" in argument for argument in prefix)
        ):
            raise ValueError(
                "OpenCode command prefixes must be non-empty and contain no NUL characters"
            )
        if (
            "{args}" in prefix[0]
            or sum(argument.count("{args}") for argument in prefix) > 1
        ):
            raise ValueError(
                "use at most one {args} placeholder, outside the launcher executable"
            )
        if os.path.dirname(prefix[0]):
            prefix[0] = os.path.abspath(os.path.expanduser(prefix[0]))
        prefixes.append(prefix)
    if server is not None:
        invalid_server = "server must be host:port or an HTTP/HTTPS URL with a port, without credentials or a path"
        if not server or any(
            character.isspace() or ord(character) < 32 for character in server
        ):
            raise ValueError(invalid_server)
        try:
            address = urlsplit(server if "://" in server else "http://" + server)
            if (
                address.scheme not in ("http", "https")
                or not address.hostname
                or address.port is None
                or address.port == 0
                or address.username is not None
                or address.password is not None
                or address.path not in ("", "/")
                or "?" in server
                or "#" in server
                or "\\" in server
            ):
                raise ValueError(invalid_server)
        except ValueError:
            raise ValueError(invalid_server) from None
        server = address.geturl().rstrip("/")
    prompt = (
        f"Create exactly {count} different correct US-English sentences for grade {grade} children. "
        + "Use familiar, age-appropriate everyday topics and vocabulary. Each sentence must have "
        + "3-15 words, at most 120 ASCII characters, initial capitalization, and a final period. "
        + "Use only letters, spaces, commas, and apostrophes inside sentences. Avoid proper names, "
        + "abbreviations, quoted speech, and sensitive topics. Use shorter sentences for lower grades. "
        + "Return ONLY a JSON object, no markdown or commentary, with this shape: "
        + json.dumps({"grade": grade, "sentences": ["The small bird can sing."]})
        + ". Do not use tools, inspect files, or execute commands."
    )
    environment = os.environ.copy()
    environment.update(
        {
            "OPENCODE_DISABLE_PROJECT_CONFIG": "1",
            "OPENCODE_DISABLE_CLAUDE_CODE": "1",
            "OPENCODE_DISABLE_DEFAULT_PLUGINS": "1",
            "OPENCODE_DISABLE_LSP_DOWNLOAD": "1",
            "OPENCODE_PERMISSION": '{"*":"deny"}',
            "OPENCODE_CONFIG_CONTENT": json.dumps(
                {
                    "permission": "deny",
                    "agent": {
                        "worksheet-text": {
                            "mode": "primary",
                            "permission": "deny",
                            "steps": 1,
                        }
                    },
                    "default_agent": "worksheet-text",
                    "share": "disabled",
                    "snapshot": False,
                    "autoupdate": False,
                    "lsp": False,
                    "formatter": False,
                }
            ),
        }
    )
    arguments = ["--pure", "run"]
    if server is None:
        arguments.extend(["--agent", "worksheet-text"])
    else:
        arguments.extend(["--attach", server])
    arguments.extend(["--format", "json", "--model", model, prompt])
    try:
        with tempfile.TemporaryDirectory(prefix="worksheet-grammar-") as directory:
            environment["PWD"] = directory
            for prefix in prefixes:
                if any("{args}" in argument for argument in prefix):
                    command = [
                        argument.replace("{args}", shlex.join(arguments))
                        for argument in prefix
                    ]
                else:
                    command = [*prefix, *arguments]
                try:
                    result = subprocess.run(
                        command,
                        cwd=directory,
                        env=environment,
                        capture_output=True,
                        text=True,
                        encoding="utf-8",
                        timeout=timeout,
                        check=False,
                        stdin=subprocess.DEVNULL,
                    )
                except FileNotFoundError:
                    continue
                break
            else:
                raise RuntimeError(
                    "no configured OpenCode launcher was found; check PATH and --opencode-command"
                )
    except subprocess.TimeoutExpired as error:
        if server is not None:
            raise RuntimeError(
                "OpenCode client timed out; the server request may still be running; check before retrying"
            ) from error
        raise RuntimeError(
            "OpenCode launcher timed out; downstream work may still be running; check before retrying"
        ) from error
    except UnicodeError as error:
        raise RuntimeError(
            "OpenCode returned output that was not valid UTF-8"
        ) from error
    except OSError as error:
        raise RuntimeError(
            "could not start the configured OpenCode launcher; check its path and permissions"
        ) from error
    # OpenCode can create a session before model validation fails. Its JSON error
    # is more specific than the exit status, without exposing raw provider logs.
    for line in result.stdout.splitlines():
        try:
            event = cast(object, json.loads(line))
        except ValueError:
            continue
        if not isinstance(event, dict):
            continue
        record = cast(dict[str, object], event)
        failure = record.get("error")
        if record.get("type") != "error" or not isinstance(failure, dict):
            continue
        failure = cast(dict[str, object], failure)
        if (
            failure.get("name") == "ProviderModelNotFoundError"
            or failure.get("_tag") == "ProviderModelNotFoundError"
        ):
            raise RuntimeError(
                f"OpenCode model not found: {model!r}; use an exact provider/model ID from the OpenCode instance"
            )
    if result.returncode != 0:
        if server is not None:
            raise RuntimeError(
                f"OpenCode attachment failed with exit code {result.returncode}; check server address, authentication, and provider configuration"
            )
        raise RuntimeError(
            f"OpenCode failed with exit code {result.returncode}; check its CLI and provider configuration"
        )
    parts: list[str] = []
    try:
        for line in result.stdout.splitlines():
            if not line.strip():
                continue
            event = cast(object, json.loads(line))
            if not isinstance(event, dict):
                raise ValueError("OpenCode event must be an object")
            record = cast(dict[str, object], event)
            if record.get("type") in ("error", "tool_use"):
                raise ValueError("OpenCode reported an error or attempted tool use")
            if record.get("type") == "text":
                part = record.get("part")
                if not isinstance(part, dict):
                    raise ValueError("OpenCode text event has no text part")
                text = cast(dict[str, object], part).get("text")
                if not isinstance(text, str):
                    raise ValueError("OpenCode text part is not a string")
                parts.append(text)
        return parse_sentences("".join(parts), grade, count)
    except ValueError as error:
        raise RuntimeError(
            "OpenCode returned invalid sentence data: " + str(error)
        ) from error
