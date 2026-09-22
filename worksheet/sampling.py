"""Sample arithmetic worksheets with configurable operation probabilities."""

import math
import random
from collections.abc import Sequence
from typing import TypeAlias, cast

from .problem import Problem

Operation: TypeAlias = str | tuple[str, float]
"""An operator (+, -, x) or an (operator, relative weight) pair."""


def normalize_operations(operations: object) -> tuple[tuple[str, float], ...]:
    """Validate operation choices and supply a weight of one for bare operators.

    Args:
        operations: Non-empty sequence of ``+``, ``-``, or ``x`` strings and/or
            (operator, weight) tuples. Weights must be finite, non-negative
            numbers with a finite, positive total. Repeated operators add weight.

    Returns:
        An immutable sequence of (operator, float weight) pairs, in input order.

    Raises:
        ValueError: If the sequence, an operator, or its weights are invalid.
    """
    if isinstance(operations, (str, bytes)) or not isinstance(operations, Sequence):
        raise ValueError("operations must be a list or sequence of operations")
    normalized: list[tuple[str, float]] = []
    for entry in operations:
        if isinstance(entry, str):
            operator, weight = entry, 1.0
        elif isinstance(entry, tuple) and len(cast(tuple[object, ...], entry)) == 2:
            operator, weight = cast(tuple[object, object], entry)
        else:
            raise ValueError("each operation must be an operator or (operator, weight) tuple")
        if not isinstance(operator, str) or operator not in ("+", "-", "x"):
            raise ValueError("supported operations are '+', '-', and 'x'")
        if isinstance(weight, bool) or not isinstance(weight, (int, float)):
            raise ValueError("operation weights must be finite, non-negative numbers")
        try:
            weight = float(weight)
        except OverflowError as error:
            raise ValueError("operation weights must be finite, non-negative numbers") from error
        if not math.isfinite(weight) or weight < 0:
            raise ValueError("operation weights must be finite, non-negative numbers")
        normalized.append((operator, weight))
    total = sum(weight for _, weight in normalized)
    if not math.isfinite(total) or total <= 0:
        raise ValueError("operation weights must have a finite, positive total")
    return tuple(normalized)


def sample_problems(
    count: int,
    minimum_operand: int,
    maximum_operand: int,
    operations: Sequence[Operation] = ("+", "-", "x"),
) -> list[Problem]:
    """Sample problems using relative operation weights and inclusive bounds.

    Args:
        count: Number of problems to sample. Must not be negative.
        minimum_operand: Smallest displayed operand. Must not be negative.
        maximum_operand: Largest displayed operand.
        operations: Operators or (operator, weight) tuples accepted by
            ``normalize_operations``. Defaults to equal chances of +, -, and x.
            Bare operators have weight one; zero-weight entries are never chosen.

    Returns:
        Random problems with both operands in the supplied range. Subtraction
        results are non-negative. Weights specify probabilities, not exact counts.

    Raises:
        ValueError: If count, operand bounds, or the operation distribution is
            invalid, even when count is zero.

    Side Effects:
        Consumes randomness from Python's global random generator.
    """
    _validate_count(count)
    _validate_operand_range(minimum_operand, maximum_operand)
    distribution = normalize_operations(operations)
    operators = tuple(operator for operator, _ in distribution)
    weights = tuple(weight for _, weight in distribution)
    problems: list[Problem] = []
    for operator in random.choices(operators, weights=weights, k=count):
        first_operand = random.randint(minimum_operand, maximum_operand)
        second_operand = random.randint(
            minimum_operand,
            first_operand if operator == "-" else maximum_operand,
        )
        problems.append(Problem(first_operand, second_operand, operator))
    return problems


def _validate_count(count: int) -> None:
    if count < 0:
        raise ValueError("count cannot be negative")


def _validate_operand_range(minimum_operand: int, maximum_operand: int) -> None:
    if minimum_operand < 0:
        raise ValueError("minimum_operand cannot be negative")
    if minimum_operand > maximum_operand:
        raise ValueError("minimum_operand cannot exceed maximum_operand")


def sample_addition_problems(
    count: int,
    minimum_operand: int,
    maximum_operand: int,
) -> list[Problem]:
    """Sample addition problems from an inclusive operand range.

    Args:
        count: Number of problems to sample. Must not be negative.
        minimum_operand: Smallest possible operand. Must not be negative.
        maximum_operand: Largest possible operand.

    Returns:
        Random addition problems whose operands are within the supplied
        inclusive range.

    Raises:
        ValueError: If ``count`` is negative or the operand range is invalid.

    Side Effects:
        Consumes randomness from Python's global random generator.
    """
    return sample_problems(count, minimum_operand, maximum_operand, ("+",))


def sample_addition_subtraction_problems(
    count: int,
    minimum_operand: int,
    maximum_operand: int,
) -> list[Problem]:
    """Sample addition and non-negative subtraction problems.

    Args:
        count: Number of problems to sample. Must not be negative.
        minimum_operand: Smallest possible operand. Must not be negative.
        maximum_operand: Largest possible operand.

    Returns:
        Randomly mixed addition and non-negative subtraction problems whose
        displayed operands are within the supplied inclusive range.

    Raises:
        ValueError: If ``count`` is negative or the operand range is invalid.

    Side Effects:
        Consumes randomness from Python's global random generator.
    """
    return sample_problems(count, minimum_operand, maximum_operand, ("+", "-"))


def sample_multiplication_problems(
    count: int,
    minimum_operand: int,
    maximum_operand: int,
) -> list[Problem]:
    """Sample multiplication problems from an inclusive operand range.

    Args:
        count: Number of problems to sample. Must not be negative.
        minimum_operand: Smallest possible operand.
        maximum_operand: Largest possible operand.

    Returns:
        Random multiplication problems whose operands are within the supplied
        inclusive range.

    Raises:
        ValueError: If ``count`` is negative or the operand range is invalid.

    Side Effects:
        Consumes randomness from Python's global random generator.
    """
    return sample_problems(count, minimum_operand, maximum_operand, ("x",))
