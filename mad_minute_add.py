from worksheet.layout import WorksheetLayout, generate_pdf
from worksheet.options import parse_options
from worksheet.sampling import sample_addition_problems


def main() -> None:
    """Generate an addition worksheet from a configurable sum range."""
    options = parse_options("mad_minute_add.pdf", 1, 9)
    problems = sample_addition_problems(
        options.problem_count,
        minimum_total=options.minimum,
        maximum_total=options.maximum,
    )
    layout = WorksheetLayout(options.rows, options.cols, options.font_size)
    generate_pdf(options.output, problems, layout)


if __name__ == "__main__":
    main()
