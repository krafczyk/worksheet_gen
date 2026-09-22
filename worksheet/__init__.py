"""Reusable components for generating arithmetic worksheets."""

from .layout import WorksheetLayout, draw_worksheet, generate_pdf
from .options import WorksheetOptions, parse_options
from .problem import Problem, draw_problem
from .sampling import (
    sample_addition_problems,
    sample_addition_subtraction_problems,
    sample_multiplication_problems,
)

__all__ = [
    "Problem",
    "WorksheetLayout",
    "WorksheetOptions",
    "draw_problem",
    "draw_worksheet",
    "generate_pdf",
    "parse_options",
    "sample_addition_problems",
    "sample_addition_subtraction_problems",
    "sample_multiplication_problems",
]
