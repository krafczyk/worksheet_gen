"""Generate configurable worksheets with multiplication-only defaults."""

from worksheet.layout import WorksheetLayout, generate_pdf
from worksheet.options import parse_options
from worksheet.sampling import sample_problems


def main() -> None:
    """Parse CLI options and write a PDF, defaulting to multiplication over 1-6.

    Raises SystemExit for invalid options or help, ValueError if instructions
    cannot fit the layout, and OSError on output failure.
    """
    options = parse_options("mad_minute_mult.pdf", 1, 6, default_operations=("x",))
    problems = sample_problems(
        options.problem_count,
        minimum_operand=options.minimum,
        maximum_operand=options.maximum,
        operations=options.operations,
    )
    layout = WorksheetLayout(
        options.rows, options.cols, options.font_size,
        instructions=options.instructions, font_name=options.font_name,
    )
    generate_pdf(options.output, problems, layout)


if __name__ == "__main__":
    main()
