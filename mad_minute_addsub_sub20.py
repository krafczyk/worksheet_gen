from worksheet.layout import WorksheetLayout, generate_pdf
from worksheet.options import parse_options
from worksheet.sampling import sample_addition_subtraction_problems


def main() -> None:
    """Generate a mixed-operation worksheet with values less than twenty."""
    options = parse_options("mad_minute_addsub_sub20.pdf")
    problems = sample_addition_subtraction_problems(
        options.problem_count,
        maximum_value=19,
    )
    layout = WorksheetLayout(options.rows, options.cols, options.font_size)
    generate_pdf(options.output, problems, layout)


if __name__ == "__main__":
    main()
