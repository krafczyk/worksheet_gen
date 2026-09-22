"""Generate configurable worksheets with addition/subtraction defaults."""

from worksheet.layout import WorksheetLayout, generate_pdf
from worksheet.options import parse_options
from worksheet.sampling import sample_problems


def main() -> None:
    """Parse CLI options and write a PDF, defaulting to + and - with operands 1-19.

    Raises SystemExit for invalid options or help, and OSError on output failure.
    """
    options = parse_options(
        "mad_minute_addsub.pdf", 1, 19, default_operations=("+", "-")
    )
    problems = sample_problems(
        options.problem_count,
        minimum_operand=options.minimum,
        maximum_operand=options.maximum,
        operations=options.operations,
    )
    layout = WorksheetLayout(options.rows, options.cols, options.font_size)
    generate_pdf(options.output, problems, layout)


if __name__ == "__main__":
    main()
