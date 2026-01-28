from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

c = canvas.Canvas("test_master.pdf", pagesize=letter)
c.drawString(100, 750, "Flexo Inspection Master Test")
c.drawString(100, 700, "This is a perfect reference image.")
c.rect(50, 50, 500, 600, stroke=1, fill=0)
c.circle(300, 400, 50, stroke=1, fill=1)
c.save()
print("test_master.pdf created")
