"""Random sampling policies for arithmetic worksheet problems."""

import random

from .problem import Problem


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
    """
    _validate_count(count)
    _validate_operand_range(minimum_operand, maximum_operand)

    return [
        Problem(
            random.randint(minimum_operand, maximum_operand),
            random.randint(minimum_operand, maximum_operand),
            "+",
        )
        for _ in range(count)
    ]


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
    """
    _validate_count(count)
    _validate_operand_range(minimum_operand, maximum_operand)

    problems: list[Problem] = []
    for _ in range(count):
        operator = random.choice(("+", "-"))
        first_operand = random.randint(minimum_operand, maximum_operand)
        if operator == "+":
            second_operand = random.randint(minimum_operand, maximum_operand)
        else:
            second_operand = random.randint(minimum_operand, first_operand)
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
        ValueError: If ``count`` is negative or the operand range is invalid.
    """
    _validate_count(count)
    _validate_operand_range(minimum_operand, maximum_operand)

    return [
        Problem(
            random.randint(minimum_operand, maximum_operand),
            random.randint(minimum_operand, maximum_operand),
            "x",
        )
        for _ in range(count)
    ]
