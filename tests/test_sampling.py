"""Regression tests for worksheet problem sampling."""

import unittest
from unittest.mock import patch

from worksheet.sampling import (
    sample_addition_problems,
    sample_addition_subtraction_problems,
    sample_multiplication_problems,
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
            patch("worksheet.sampling.random.choice", return_value="+"),
        ):
            problem = sample_addition_subtraction_problems(1, 1, 6)[0]

        self.assertEqual((problem.first_operand, problem.second_operand), (1, 1))

    def test_mixed_subtraction_respects_minimum_operand(self) -> None:
        """Mixed-sheet subtraction must keep both operands within the range."""
        with (
            patch("worksheet.sampling.random.randint", side_effect=_return_minimum),
            patch("worksheet.sampling.random.choice", return_value="-"),
        ):
            problem = sample_addition_subtraction_problems(1, 1, 6)[0]

        self.assertEqual((problem.first_operand, problem.second_operand), (1, 1))

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


if __name__ == "__main__":
    _ = unittest.main()
