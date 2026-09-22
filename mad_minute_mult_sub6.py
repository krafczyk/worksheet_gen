from worksheet.layout import WorksheetLayout, generate_pdf
from worksheet.options import parse_options
from worksheet.sampling import sample_multiplication_problems


def main() -> None:
    """Generate a multiplication worksheet with operands from one to six."""
    options = parse_options("mad_minute_mult_sub6.pdf")
    problems = sample_multiplication_problems(
        options.problem_count,
        minimum_operand=1,
        maximum_operand=6,
    )
    layout = WorksheetLayout(options.rows, options.cols, options.font_size)
    generate_pdf(options.output, problems, layout)


if __name__ == "__main__":
    main()
