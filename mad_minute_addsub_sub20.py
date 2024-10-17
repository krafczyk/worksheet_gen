from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import random
import argparse

def generate_problems(rows, cols):
    """Generate a list of random addition problems where the sum is less than 10."""
    problems = []
    for _ in range(rows * cols):
        total = random.randint(1,19)
        op = random.choice(['+', '-'])
        if op == '+':
            a = random.randint(0,total)
            b = total-a
            problems.append((a,b,op))
        else:
            b = random.randint(0,total)
            problems.append((total,b,op))
    return problems

def draw_problems(c, problems, rows, cols, width, height, font_size):
    """Draw the problems on the PDF canvas."""
    c.setFont("Helvetica", font_size)
    problem_width = width / cols
    problem_height = height / rows
    
    for row in range(rows):
        for col in range(cols):
            x = (col + 1) * problem_width - 50  # Right margin for the column
            y = height - row * problem_height - 40
            a, b, op = problems[row * cols + col]
            
            # Right-justify by calculating width of number strings
            a_width = c.stringWidth(str(a), "Helvetica", font_size)
            b_width = c.stringWidth(str(b), "Helvetica", font_size)
            space_width = c.stringWidth(" ", "Helvetica", font_size)
            op_width = c.stringWidth(op, "Helvetica", font_size)

            max_width = max(a_width, op_width+space_width+b_width)
            
            # Draw the numbers, right-justified
            c.drawString(x - a_width, y, str(a))
            c.drawString(x - (op_width+space_width+b_width), y - font_size, op+" "+str(b))
            
            # Draw the line for the answer, right-justified
            c.line(x - max_width, y - font_size*1.2, x, y - font_size*1.2)


def generate_pdf(filename, rows=5, cols=5, font_size=14):
    """Generate a PDF with the specified number of rows, columns, and font size."""
    width, height = letter
    c = canvas.Canvas(filename, pagesize=letter)
    
    problems = generate_problems(rows, cols)
    
    draw_problems(c, problems, rows, cols, width, height, font_size)
    
    c.save()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=str, default="mad_minute_addsub_sub20.pdf")

    args = parser.parse_args()

    # Example usage
    generate_pdf(args.output, rows=8, cols=5, font_size=20)
