from worksheet.layout import WorksheetLayout, generate_pdf
from worksheet.options import parse_options
from worksheet.sampling import sample_addition_subtraction_problems


def main() -> None:
    """Generate a mixed-operation worksheet from a configurable value range."""
    options = parse_options("mad_minute_addsub.pdf", 1, 19)
    problems = sample_addition_subtraction_problems(
        options.problem_count,
        minimum_value=options.minimum,
        maximum_value=options.maximum,
    )
    layout = WorksheetLayout(options.rows, options.cols, options.font_size)
    generate_pdf(options.output, problems, layout)


if __name__ == "__main__":
    main()
