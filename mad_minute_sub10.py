from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import random
import argparse

def generate_addition_problems(rows, cols):
    """Generate a list of random addition problems where the sum is less than 10."""
    problems = []
    for _ in range(rows * cols):
        total = random.randint(1,9)
        a = random.randint(0,total)
        b = total-a
        problems.append((a,b))
    return problems

def draw_addition_problems(c, problems, rows, cols, width, height, font_size):
    """Draw the addition problems on the PDF canvas."""
    c.setFont("Helvetica", font_size)
    problem_width = width / cols
    problem_height = height / rows
    
    for row in range(rows):
        for col in range(cols):
            x = (col + 1) * problem_width - 50  # Right margin for the column
            y = height - row * problem_height - 40
            a, b = problems[row * cols + col]
            
            # Right-justify by calculating width of number strings
            a_width = c.stringWidth(str(a), "Helvetica", font_size)
            b_width = c.stringWidth("+ " + str(b), "Helvetica", font_size)
            line_width = c.stringWidth("___", "Helvetica", font_size)
            
            # Draw the numbers, right-justified
            c.drawString(x - a_width, y, str(a))
            c.drawString(x - b_width, y - font_size, "+ " + str(b))
            
            # Draw the line for the answer, right-justified
            c.line(x - line_width, y - font_size*1.2, x, y - font_size*1.2)


def generate_pdf(filename, rows=5, cols=5, font_size=14):
    """Generate a PDF with the specified number of rows, columns, and font size."""
    width, height = letter
    c = canvas.Canvas(filename, pagesize=letter)
    
    problems = generate_addition_problems(rows, cols)
    
    draw_addition_problems(c, problems, rows, cols, width, height, font_size)
    
    c.save()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=str, default="mad_minute_sub10.pdf")

    args = parser.parse_args()

    # Example usage
    generate_pdf(args.output, rows=8, cols=5, font_size=20)
