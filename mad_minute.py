"""Generate arithmetic worksheets with configurable operation probabilities."""

from worksheet.layout import WorksheetLayout, generate_pdf
from worksheet.options import parse_options
from worksheet.sampling import sample_problems


def main() -> None:
    """Parse CLI options and write a PDF, defaulting to +, -, x over operands 1-9.

    Raises SystemExit for invalid options or help, ValueError if instructions
    cannot fit the layout, and OSError on output failure.
    """
    options = parse_options("mad_minute.pdf", 1, 9)
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
