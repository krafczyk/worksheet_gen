"""Random sampling policies for arithmetic worksheet problems."""

import random

from .problem import Problem


def _validate_count(count: int) -> None:
    if count < 0:
        raise ValueError("count cannot be negative")


def sample_addition_problems(
    count: int,
    minimum_total: int,
    maximum_total: int,
) -> list[Problem]:
    """Sample addition problems from an inclusive total range.

    Args:
        count: Number of problems to sample. Must not be negative.
        minimum_total: Smallest possible sum. Must not be negative.
        maximum_total: Largest possible sum.

    Returns:
        Random addition problems with sums from ``minimum_total`` through
        ``maximum_total`` and non-negative operands.

    Raises:
        ValueError: If ``count`` is negative or the total range is invalid.
    """
    _validate_count(count)
    if minimum_total < 0:
        raise ValueError("minimum_total cannot be negative")
    if minimum_total > maximum_total:
        raise ValueError("minimum_total cannot exceed maximum_total")

    problems: list[Problem] = []
    for _ in range(count):
        total = random.randint(minimum_total, maximum_total)
        first_operand = random.randint(0, total)
        problems.append(Problem(first_operand, total - first_operand, "+"))
    return problems


def sample_addition_subtraction_problems(
    count: int,
    minimum_value: int,
    maximum_value: int,
) -> list[Problem]:
    """Sample addition and non-negative subtraction problems.

    Args:
        count: Number of problems to sample. Must not be negative.
        minimum_value: Smallest sum or minuend. Must not be negative.
        maximum_value: Largest sum or minuend.

    Returns:
        Randomly mixed addition and subtraction problems. Addition sums and
        subtraction minuends range from ``minimum_value`` through
        ``maximum_value``.

    Raises:
        ValueError: If ``count`` is negative or the value range is invalid.
    """
    _validate_count(count)
    if minimum_value < 0:
        raise ValueError("minimum_value cannot be negative")
    if minimum_value > maximum_value:
        raise ValueError("minimum_value cannot exceed maximum_value")

    problems: list[Problem] = []
    for _ in range(count):
        total = random.randint(minimum_value, maximum_value)
        operator = random.choice(("+", "-"))
        if operator == "+":
            first_operand = random.randint(0, total)
            second_operand = total - first_operand
        else:
            first_operand = total
            second_operand = random.randint(0, total)
        problems.append(Problem(first_operand, second_operand, operator))
    return problems


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
        ValueError: If ``count`` is negative or the operand range is empty.
    """
    _validate_count(count)
    if minimum_operand > maximum_operand:
        raise ValueError("minimum_operand cannot exceed maximum_operand")

    return [
        Problem(
            random.randint(minimum_operand, maximum_operand),
            random.randint(minimum_operand, maximum_operand),
            "x",
        )
        for _ in range(count)
    ]
