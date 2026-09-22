"""Reusable components for arithmetic, spelling, and writing worksheets."""

from .components import LineStyle, draw_instructions, draw_writing_line
from .fonts import DEFAULT_FONT, resolve_font
from .layout import WorksheetLayout, draw_worksheet, generate_pdf
from .options import WorksheetOptions, parse_options
from .problem import Problem, draw_problem
from .sampling import (
    Operation,
    sample_addition_problems,
    sample_addition_subtraction_problems,
    sample_multiplication_problems,
    sample_problems,
)
from .vocabulary import load_words
from .writing import WritingExercise, WritingLayout, generate_writing_pdf

__all__ = [
    "DEFAULT_FONT",
    "LineStyle",
    "Operation",
    "Problem",
    "WorksheetLayout",
    "WorksheetOptions",
    "WritingExercise",
    "WritingLayout",
    "draw_instructions",
    "draw_problem",
    "draw_worksheet",
    "draw_writing_line",
    "generate_pdf",
    "generate_writing_pdf",
    "load_words",
    "parse_options",
    "resolve_font",
    "sample_addition_problems",
    "sample_addition_subtraction_problems",
    "sample_multiplication_problems",
    "sample_problems",
]
