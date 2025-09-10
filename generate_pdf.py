from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Register fonts (DejaVu for sans, Times for serif)
pdfmetrics.registerFont(TTFont("DejaVuSans", "DejaVuSans.ttf"))
pdfmetrics.registerFont(TTFont("DejaVuSans-Bold", "DejaVuSans-Bold.ttf"))
pdfmetrics.registerFont(TTFont("Times-Roman", "Times.ttf"))
pdfmetrics.registerFont(TTFont("Times-Bold", "Times-Bold.ttf"))

# Question data (from user)
question_data = {
    "chapter_title": "Atomic Physics",  
    "exam_series": "Oct/Nov 2018",  
    "subject": "Physics 5054",  
    "paper_ref": "Paper 2 Variant 2",  
    "original_ref": "5054_w18_qp_22 Q11",  
    "marks": 6,  

    "question_text": """  
A smoke detector contains a small quantity of americium-241 which emits alpha particles.

a) Explain briefly how the alpha source ionises the air in the detector and how this is used to detect smoke. (3 marks)

b) The half-life of Am-241 is given as 430 years. If a detector initially contains 8.0×10^11 atoms,
calculate the time required for the number of atoms to fall to 1.0×10^11 atoms. (3 marks)

(Diagram reference: see original paper)  
""",  

    "answer_text": """  
a) Alpha particles ionise air because they are highly ionising; they knock electrons from air molecules, producing ion pairs. The detector measures the resulting current between electrodes; smoke reduces ionisation/current causing an alarm. (Award 2–3 marking points for ionisation + current/alarm link.)

b) 8.0×10^11 → 1.0×10^11 is a factor of 8 = 2^3 so 3 half-lives. Time = 3 × 430 = 1290 years. (Show working for full credit.)
""",  

    "tags": ["Atomic Physics", "Radioactivity", "Half-life"],  
    "source_manifest": {
        "question_pdf": "5054_w18_qp_22.pdf",  
        "markscheme_pdf": "5054_w18_ms_22.pdf"  
    }  
}

# Filepath
filepath = "/mnt/data/Atomic_Physics_Clean_Final.pdf"

# Create canvas
c = canvas.Canvas(filepath, pagesize=A4)
width, height = A4

def draw_border(c):
    # thin border
    c.setLineWidth(2)
    c.rect(1*cm, 1*cm, width-2*cm, height-2*cm)

def draw_header(c, data, page_num, total_pages):
    c.setFont("DejaVuSans-Bold", 12)
    header_text = f"{data['subject']} | {data['paper_ref']} | {data['exam_series']} | {data['chapter_title']}"
    c.drawCentredString(width/2, height-1.2*cm, header_text)
    # Footer
    c.setFont("DejaVuSans", 9)
    c.drawString(1.2*cm, 0.6*cm, f"Source: {data['source_manifest']['question_pdf']} + {data['source_manifest']['markscheme_pdf']}")
    c.drawCentredString(width/2, 0.6*cm, f"Page {page_num} of {total_pages}")
    c.drawRightString(width-1.2*cm, 0.6*cm, "Compiled by OpenAI")

def draw_marks_sidebar(c, marks, tags):
    sidebar_width = 3*cm
    x = width - 1*cm - sidebar_width
    y = height - 3*cm
    c.setStrokeColor(colors.black)
    c.setFillColorRGB(0.95, 0.95, 0.95)
    c.rect(x, y-3*cm, sidebar_width, 3*cm, fill=1)
    c.setFillColor(colors.black)
    c.setFont("DejaVuSans-Bold", 14)
    c.drawCentredString(x+sidebar_width/2, y-0.6*cm, f"{marks} marks")
    c.setFont("DejaVuSans", 8)
    tag_text = ", ".join(tags)
    c.drawCentredString(x+sidebar_width/2, y-1.4*cm, tag_text)

def draw_wrapped_text(c, text, x, y, max_width, font="DejaVuSans", size=11, leading=14):
    c.setFont(font, size)
    from reportlab.platypus import Paragraph
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.platypus import Frame

    style = ParagraphStyle(name="normal", fontName=font, fontSize=size, leading=leading)
    p = Paragraph(text.replace("\n", "<br/>"), style)
    f = Frame(x, y-8*cm, max_width, 8*cm, showBoundary=0)
    f.addFromList([p], c)

def draw_answer_lines(c, x, y, width, lines=12, spacing=18):
    for i in range(lines):
        c.line(x, y - i*spacing, x+width, y - i*spacing)

# ---- Page 1: Question ----
draw_border(c)
draw_header(c, question_data, 1, 2)
draw_marks_sidebar(c, question_data["marks"], question_data["tags"])

# Question text area
text_x = 2*cm
text_y = height - 4*cm
text_width = width - 7*cm
draw_wrapped_text(c, question_data["question_text"], text_x, text_y, text_width)

# Diagram placeholder only if mentioned
if "(Diagram reference:" in question_data["question_text"]:
    c.setStrokeColor(colors.grey)
    c.rect(text_x, text_y-7*cm, 6*cm, 4*cm)
    c.setFont("DejaVuSans", 9)
    c.drawCentredString(text_x+3*cm, text_y-5*cm, "Diagram placeholder")

# Answer lines
draw_answer_lines(c, text_x, 5*cm, width-4*cm, lines=12, spacing=18)

c.showPage()

# ---- Page 2: Markscheme ----
draw_border(c)
draw_header(c, question_data, 2, 2)

c.setFont("Times-Bold", 12)
c.drawString(2*cm, height-3*cm, "Markscheme (for teachers only):")

draw_wrapped_text(c, question_data["answer_text"], 2*cm, height-4*cm, width-4*cm, font="DejaVuSans", size=11, leading=14)

c.save()
filepath
