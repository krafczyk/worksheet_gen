"""Random sampling policies for arithmetic worksheet problems."""

import random

from .problem import Problem


def _validate_count(count: int) -> None:
    if count < 0:
        raise ValueError("count cannot be negative")


def sample_addition_problems(count: int, maximum_total: int) -> list[Problem]:
    """Sample addition problems whose totals are within a positive bound.

    Args:
        count: Number of problems to sample. Must not be negative.
        maximum_total: Largest possible sum. Must be at least one.

    Returns:
        Random addition problems with sums from one through
        ``maximum_total`` and non-negative operands.

    Raises:
        ValueError: If ``count`` is negative or ``maximum_total`` is below one.
    """
    _validate_count(count)
    if maximum_total < 1:
        raise ValueError("maximum_total must be at least one")

    problems: list[Problem] = []
    for _ in range(count):
        total = random.randint(1, maximum_total)
        first_operand = random.randint(0, total)
        problems.append(Problem(first_operand, total - first_operand, "+"))
    return problems


def sample_addition_subtraction_problems(
    count: int,
    maximum_value: int,
) -> list[Problem]:
    """Sample addition and non-negative subtraction problems.

    Args:
        count: Number of problems to sample. Must not be negative.
        maximum_value: Largest sum or minuend. Must be at least one.

    Returns:
        Randomly mixed addition and subtraction problems. Addition sums and
        subtraction minuends range from one through ``maximum_value``.

    Raises:
        ValueError: If ``count`` is negative or ``maximum_value`` is below one.
    """
    _validate_count(count)
    if maximum_value < 1:
        raise ValueError("maximum_value must be at least one")

    problems: list[Problem] = []
    for _ in range(count):
        total = random.randint(1, maximum_value)
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
