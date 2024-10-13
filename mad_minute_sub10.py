from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import random

def generate_addition_problems(rows, cols):
    """Generate a list of random addition problems where the sum is less than 10."""
    problems = []
    for _ in range(rows * cols):
        while True:
            a = random.randint(0, 9)
            b = random.randint(0, 9)
            if a + b < 10:
                problems.append((a, b))
                break
    return problems

def draw_addition_problems(c, problems, rows, cols, width, height, font_size):
    """Draw the addition problems on the PDF canvas."""
    c.setFont("Helvetica", font_size)
    problem_width = width / cols
    problem_height = height / rows
    
    for row in range(rows):
        for col in range(cols):
            x = col * problem_width + 20
            y = height - row * problem_height - 40
            a, b = problems[row * cols + col]
            
            # Draw the numbers and space for the answer
            c.drawString(x, y, str(a))
            c.drawString(x, y - font_size, "+ " + str(b))
            c.line(x, y - font_size * 2, x + font_size * 2, y - font_size * 2)
            c.drawString(x, y - font_size * 3, "__")

def generate_pdf(filename, rows=5, cols=5, font_size=14):
    """Generate a PDF with the specified number of rows, columns, and font size."""
    width, height = letter
    c = canvas.Canvas(filename, pagesize=letter)
    
    problems = generate_addition_problems(rows, cols)
    
    draw_addition_problems(c, problems, rows, cols, width, height, font_size)
    
    c.save()

if __name__ == "__main__":
    # Example usage
    generate_pdf("mad_minute_sub10.pdf", rows=6, cols=4, font_size=20)
