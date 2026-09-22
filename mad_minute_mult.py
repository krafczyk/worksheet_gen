from worksheet.layout import WorksheetLayout, generate_pdf
from worksheet.options import parse_options
from worksheet.sampling import sample_multiplication_problems


def main() -> None:
    """Generate a multiplication worksheet from a configurable operand range."""
    options = parse_options("mad_minute_mult.pdf", 1, 6)
    problems = sample_multiplication_problems(
        options.problem_count,
        minimum_operand=options.minimum,
        maximum_operand=options.maximum,
    )
    layout = WorksheetLayout(options.rows, options.cols, options.font_size)
    generate_pdf(options.output, problems, layout)


if __name__ == "__main__":
    main()
