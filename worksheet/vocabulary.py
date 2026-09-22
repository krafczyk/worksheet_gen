"""Load editable US-English spelling word lists with suggested grades 1-5."""

import json
import re
from pathlib import Path
from typing import cast


def load_words(grade: int, filename: str | Path | None = None) -> tuple[str, ...]:
    """Load and validate one suggested grade's spelling words without network access.

    Args:
        grade: Suggested US grade level, from 1 through 5.
        filename: Optional JSON word-list path. Defaults to the bundled starter
            data. The object must contain ``grades`` mapping grade strings to lists.

    Returns:
        A non-empty tuple of distinct lowercase ASCII words for the selected grade.
        The bundled lists are project-authored guidance, not a certified curriculum.

    Raises:
        ValueError: If grade, JSON, or the selected grade's word list is invalid.
        OSError: If the source cannot be read.
    """
    if type(grade) is not int or grade not in range(1, 6):
        raise ValueError("grade must be between 1 and 5")
    path = (
        Path(filename)
        if filename is not None
        else Path(__file__).parent / "data" / "words.json"
    )
    data = cast(object, json.loads(path.read_text(encoding="utf-8")))
    if not isinstance(data, dict):
        raise ValueError("word-list JSON must be an object containing grades")
    grades = cast(dict[str, object], data).get("grades")
    if not isinstance(grades, dict):
        raise ValueError("word-list JSON must contain a grades object")
    words = cast(dict[str, object], grades).get(str(grade))
    if not isinstance(words, list) or not words:
        raise ValueError(f"word list must contain words for grade {grade}")
    validated: list[str] = []
    for word in cast(list[object], words):
        if not isinstance(word, str) or not re.fullmatch(r"[a-z]{1,30}", word):
            raise ValueError("spelling words must contain 1-30 lowercase ASCII letters")
        if word in validated:
            raise ValueError(f"duplicate spelling word: {word}")
        validated.append(word)
    return tuple(validated)
