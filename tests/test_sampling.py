"""Regression tests for worksheet problem sampling."""

import random
import unittest
from collections.abc import Sequence
from typing import cast
from unittest.mock import patch

from worksheet.sampling import (
    Operation,
    sample_addition_problems,
    sample_addition_subtraction_problems,
    sample_multiplication_problems,
    sample_problems,
)


def _return_minimum(minimum: int, maximum: int) -> int:
    del maximum
    return minimum


class OperandRangeTests(unittest.TestCase):
    """Verify that configured operand bounds apply to displayed values."""

    def test_addition_respects_minimum_operand(self) -> None:
        """Addition must not sample either operand below the minimum."""
        with patch(
            "worksheet.sampling.random.randint",
            side_effect=_return_minimum,
        ):
            problem = sample_addition_problems(1, 1, 6)[0]

        self.assertEqual((problem.first_operand, problem.second_operand), (1, 1))

    def test_mixed_addition_respects_minimum_operand(self) -> None:
        """Mixed-sheet addition must keep both operands within the range."""
        with (
            patch("worksheet.sampling.random.randint", side_effect=_return_minimum),
            patch("worksheet.sampling.random.choices", return_value=["+"]),
        ):
            problem = sample_addition_subtraction_problems(1, 1, 6)[0]

        self.assertEqual((problem.first_operand, problem.second_operand), (1, 1))

    def test_mixed_subtraction_respects_minimum_operand(self) -> None:
        """Mixed-sheet subtraction must keep both operands within the range."""
        with (
            patch("worksheet.sampling.random.randint", side_effect=_return_minimum),
            patch("worksheet.sampling.random.choices", return_value=["-"]),
        ):
            problem = sample_addition_subtraction_problems(1, 1, 6)[0]

        self.assertEqual((problem.first_operand, problem.second_operand), (1, 1))
        self.assertEqual(problem.operator, "-")

    def test_all_samplers_respect_operand_bounds(self) -> None:
        """Every sampler must constrain both operands to the inclusive range."""
        problem_sets = (
            sample_addition_problems(500, 2, 7),
            sample_addition_subtraction_problems(500, 2, 7),
            sample_multiplication_problems(500, 2, 7),
        )

        for problems in problem_sets:
            with self.subTest(operator=problems[0].operator):
                self.assertTrue(
                    all(
                        2 <= operand <= 7
                        for problem in problems
                        for operand in (problem.first_operand, problem.second_operand)
                    )
                )


class OperationDistributionTests(unittest.TestCase):
    """Verify shared sampling probabilities, bounds, and input validation."""

    def test_bare_operations_have_equal_weight(self) -> None:
        """Bare operators must each receive a weight of one."""
        with patch("worksheet.sampling.random.choices", return_value=["x", "+"]) as choose:
            problems = sample_problems(2, 1, 9, ["+", "x"])

        choose.assert_called_once_with(("+", "x"), weights=(1.0, 1.0), k=2)
        self.assertEqual([problem.operator for problem in problems], ["x", "+"])

    def test_mixed_weighted_and_bare_operations(self) -> None:
        """Weights must be passed through without imposing exact quotas."""
        with patch("worksheet.sampling.random.choices", return_value=["-"]) as choose:
            problems = sample_problems(1, 1, 9, ["+", ("-", 2.5), ("x", 0)])

        choose.assert_called_once_with(("+", "-", "x"), weights=(1.0, 2.5, 0.0), k=1)
        self.assertEqual(problems[0].operator, "-")

    def test_weighted_distribution(self) -> None:
        """A seeded sample must reflect relative operation probabilities."""
        with patch("worksheet.sampling.random.choices", side_effect=random.Random(42).choices):
            problems = sample_problems(1000, 1, 9, [("+", 3), ("-", 1)])

        additions = sum(problem.operator == "+" for problem in problems)
        self.assertTrue(700 < additions < 800)

    def test_zero_weight_is_never_selected(self) -> None:
        """Entries with zero weight must be excluded from generated problems."""
        problems = sample_problems(100, 1, 9, [("+", 0), ("-", 1), ("x", 0)])
        self.assertEqual({problem.operator for problem in problems}, {"-"})

    def test_repeated_operations_add_weight(self) -> None:
        """Repeated entries must retain their individual probability weights."""
        with patch("worksheet.sampling.random.choices", return_value=[]) as choose:
            self.assertEqual(sample_problems(0, 1, 9, ["+", "+", "-"]), [])
        choose.assert_called_once_with(("+", "+", "-"), weights=(1.0, 1.0, 1.0), k=0)

    def test_default_operations(self) -> None:
        """The generic sampler must default to all three supported operations."""
        with patch("worksheet.sampling.random.choices", return_value=[]) as choose:
            self.assertEqual(sample_problems(0, 1, 9), [])
        choose.assert_called_once_with(("+", "-", "x"), weights=(1.0, 1.0, 1.0), k=0)

    def test_subtraction_bounds_and_non_negative_results(self) -> None:
        """Subtraction must bound its second operand by its first operand."""
        with patch("worksheet.sampling.random.randint", side_effect=[4, 3]) as randint:
            problem = sample_problems(1, 2, 7, ["-"])[0]
        self.assertEqual(randint.call_args_list[0].args, (2, 7))
        self.assertEqual(randint.call_args_list[1].args, (2, 4))
        self.assertEqual((problem.first_operand, problem.second_operand), (4, 3))
        problems = sample_problems(100, 2, 7, ["-"])
        self.assertTrue(all(2 <= p.second_operand <= p.first_operand <= 7 for p in problems))

    def test_single_value_ranges(self) -> None:
        """Zero and equal nonzero bounds must work for every operation."""
        for operator in ("+", "-", "x"):
            for operand in (0, 3):
                with self.subTest(operator=operator, operand=operand):
                    problem = sample_problems(1, operand, operand, [operator])[0]
                    self.assertEqual(problem.first_operand, operand)
                    self.assertEqual(problem.second_operand, operand)
                    self.assertEqual(problem.operator, operator)

    def test_invalid_distributions(self) -> None:
        """Invalid operation specifications must fail even for zero problems."""
        invalid_distributions: tuple[object, ...] = (
            [], "+", None, ["/"], [1], [("+",)], [("+", 1, 2)],
            [("+", "2")], [("+", True)], [("+", -1)], [("+", 0)],
            [("+", float("nan"))], [("+", float("inf"))],
            [("+", 1e308), ("-", 1e308)], [("+", 10**1000)],
        )
        for operations in invalid_distributions:
            with self.subTest(operations=operations), self.assertRaises(ValueError):
                _ = sample_problems(0, 1, 9, cast(Sequence[Operation], operations))

    def test_invalid_counts_and_ranges(self) -> None:
        """Invalid counts and operand bounds must fail before sampling."""
        for count, minimum, maximum in ((-1, 1, 9), (0, -1, 9), (0, 9, 1)):
            with self.subTest(count=count, minimum=minimum, maximum=maximum):
                with self.assertRaises(ValueError):
                    _ = sample_problems(count, minimum, maximum)


if __name__ == "__main__":
    _ = unittest.main()
