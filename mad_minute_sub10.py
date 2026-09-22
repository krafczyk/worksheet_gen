from worksheet.layout import WorksheetLayout, generate_pdf
from worksheet.options import parse_options
from worksheet.sampling import sample_addition_problems


def main() -> None:
    """Generate an addition worksheet whose sums are less than ten."""
    options = parse_options("mad_minute_sub10.pdf")
    problems = sample_addition_problems(options.problem_count, maximum_total=9)
    layout = WorksheetLayout(options.rows, options.cols, options.font_size)
    generate_pdf(options.output, problems, layout)


if __name__ == "__main__":
    main()
