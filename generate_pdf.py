# make_pdf_with_end_of_topic_fixed.py
# Adds support for explicit end_of_topic markers to force fresh divider pages,
# improves simulation parity, and prints actual divider/MS page numbers during render.

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import Paragraph, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
import os, textwrap, re, math, requests

DEFAULT_SKETCH_H = 7.0 * cm  # default sketch box height

# -------------------------
# Debug helper (uses canvas page number)
# -------------------------
def dbg(msg):
    try:
        print(f"DEBUG [page {c.getPageNumber()}]: {msg}")
    except Exception:
        print("DEBUG [page ?:]", msg)

# -------------------------
# Questions (sample; add `end_of_topic: True` to final Q of each topic)
# -------------------------
questions = [
    # ---------------- Topic: Electricity and Magnetism ----------------
    {
        "chapter_title": "Electricity and Magnetism",
        "exam_series": "May/Jun 2014",
        "subject": "Physics 5054",
        "original_ref": "5054_s14_qp_11 Q1",
        "marks": 2,
        "question_number": "1",
        "question_text": "Define potential difference. [2]",
        "answer_text": {"a": "Work done per unit charge moving between two points."},
        "end_of_topic": False
    },
    {
        "chapter_title": "Electricity and Magnetism",
        "exam_series": "May/Jun 2017",
        "subject": "Physics 5054",
        "original_ref": "5054_s17_qp_22 Q2",
        "marks": 6,
        "question_number": "2",
        "question_text": """(a) State Ohm’s law. [1]

(b) A resistor has V = 12 V and I = 2.0 A. Calculate its resistance. [2]

(c) Sketch the I–V graph for a filament lamp. [3]""",
        "answer_text": {
            "a": "V ∝ I provided temperature is constant.",
            "b": "R = V / I = 12 / 2.0 = 6.0 Ω",
            "c": "Non-linear graph: slope decreases as current increases."
        },
        "sketch": {"c": True},          # requires sketch for (c)
        "sketch_only": {"c": False},    # sketch + answer lines
        "end_of_topic": True
    },

    # ---------------- Topic: Waves ----------------
    {
        "chapter_title": "Waves",
        "exam_series": "Oct/Nov 2018",
        "subject": "Physics 5054",
        "original_ref": "5054_w18_qp_11 Q3",
        "marks": 5,
        "question_number": "3",
        "question_text": """A student measures the speed of sound using resonance in a tube. 
Describe the experiment and how the data is used. [5]""",
        "answer_text": {
            "a": "Adjust tube length until resonance with tuning fork. Measure length, calculate wavelength, then use v = fλ."
        },
        "sketch": True,       # whole question sketch box
        "sketch_only": True,  # sketch only, no lines
        "end_of_topic": False
    },
    {
        "chapter_title": "Waves",
        "exam_series": "May/Jun 2015",
        "subject": "Physics 5054",
        "original_ref": "5054_s15_qp_21 Q4",
        "marks": 8,
        "question_number": "4",
        "question_text": """(a) Define wavelength. [1]

(b) On Fig. 4.1, sketch two waves of equal amplitude but different frequency. [2]

(c) Explain how diffraction occurs when waves pass through a gap. [2]

(d) Explain why light shows less diffraction than sound. [3]""",
        "answer_text": {
            "a": "Distance between two successive crests or compressions.",
            "b": "One wave has more cycles in the same distance.",
            "c": "Waves spread out when passing through a gap about same size as λ.",
            "d": "λ of light is much smaller than gap size, so diffraction is negligible."
        },
        "sketch": {"b": True},        # sketch needed
        "sketch_only": {"b": True},   # sketch only, no lines
        "image": {"b": "wave_placeholder.png"},   # test local/URL image for part
        "end_of_topic": True
    },

    # ---------------- Topic: Thermal Physics ----------------
    {
        "chapter_title": "Thermal Physics",
        "exam_series": "Oct/Nov 2019",
        "subject": "Physics 5054",
        "original_ref": "5054_w19_qp_22 Q5",
        "marks": 4,
        "question_number": "5",
        "question_text": "Explain why evaporation causes cooling of a liquid. [4]",
        "answer_text": {
            "a": "Fastest molecules escape; average KE of remaining molecules decreases; temperature falls."
        },
        "end_of_topic": False
    },
    {
        "chapter_title": "Thermal Physics",
        "exam_series": "Specimen 2020",
        "subject": "Physics 5054",
        "original_ref": "5054_sp20_qp_12 Q6",
        "marks": 6,
        "question_number": "6",
        "question_text": """(a) State what is meant by specific latent heat. [2]

(b) Sketch a temperature–time graph for ice being heated until boiling. [4]""",
        "answer_text": {
            "a": "Energy required to change state of unit mass without temperature change.",
            "b": "Graph: flat at 0°C (melting), rises, flat at 100°C (boiling)."
        },
        "sketch": {"b": True},
        "sketch_only": {"b": False},   # sketch + lines
        "end_of_topic": True
    },

    # ---------------- Topic: Nuclear Physics ----------------
    {
        "chapter_title": "Nuclear Physics",
        "exam_series": "May/Jun 2016",
        "subject": "Physics 5054",
        "original_ref": "5054_s16_qp_21 Q7",
        "marks": 7,
        "question_number": "7",
        "question_text": """(a) Define half-life. [1]

(b) A sample has activity 800 Bq. After 15 min it is 100 Bq. Calculate the half-life. [3]

(c) Sketch a decay curve for this process. [3]""",
        "answer_text": {
            "a": "Time for activity/mass to halve.",
            "b": "800 → 400 → 200 → 100 in 3 half-lives. Half-life = 15 ÷ 3 = 5 min.",
            "c": "Exponential curve decreasing with time."
        },
        "sketch": {"c": True},
        "sketch_only": {"c": False},
        "end_of_topic": True
    }
]



# -------------------------
# Output
# -------------------------
output_filename = "Topical_Booklet_with_end_of_topic_fixed.pdf"
filepath = os.path.join(os.getcwd(), output_filename)

# -------------------------
# Helpers (same as before)
# -------------------------
def superscript_digits(s):
    sup_map = str.maketrans("0123456789-+", "⁰¹²³⁴⁵⁶⁷⁸⁹⁻⁺")
    s = re.sub(r'(\d+)\^(\d+)', lambda m: m.group(1) + ''.join(ch.translate(sup_map) for ch in m.group(2)), s)
    s = re.sub(r'\^(\d+)', lambda m: ''.join(ch.translate(sup_map) for ch in m.group(1)), s)
    s = re.sub(r'×10\^(\d+)', lambda m: '×10' + ''.join(ch.translate(sup_map) for ch in m.group(1)), s)
    return s

def tidy_text_for_math(text):
    if not text:
        return ""
    text = re.sub(r'\(?Diagram reference:.*?\)?', '', text, flags=re.IGNORECASE)
    text = text.replace('x10^', '×10^')
    return superscript_digits(text)

def wrapped_lines(text, max_chars):
    out = []
    if text is None:
        return out
    for para in str(text).split("\n\n"):
        para = para.strip()
        if not para:
            out.append("")
            continue
        wrap_lines = textwrap.wrap(para, width=max_chars)
        if not wrap_lines:
            out.append("")
        else:
            out.extend(wrap_lines)
        out.append("")
    return out

def download_image(url, filename):
    if not url:
        return None
    if os.path.exists(url):
        return url
    try:
        if not os.path.exists(filename):
            r = requests.get(url, stream=True, timeout=15)
            r.raise_for_status()
            with open(filename, "wb") as f:
                for chunk in r.iter_content(1024):
                    f.write(chunk)
        return filename
    except Exception as e:
        print("Image download error:", e)
        return None

def lines_per_marks(marks):
    return int(math.ceil(1.7 * (marks or 0))) if marks and marks > 0 else 3
# -------------------------
# Sketch helpers (new, small & local)
# -------------------------
def _get_part_sketch_height(q, label):
    """Always return fixed sketch height if part needs a sketch."""
    spec = q.get("sketch")
    if isinstance(spec, dict):
        if spec.get(label):
            return DEFAULT_SKETCH_H
        return 0
    if spec:
        return DEFAULT_SKETCH_H
    return 0

def _is_part_sketch_only(q, label):
    """Return True if this part should be sketch-only (no answer lines)."""
    spec = q.get("sketch_only")
    if isinstance(spec, dict):
        return bool(spec.get(label))
    # If sketch_only is a truthy non-dict value, apply to all parts/whole
    return bool(spec)

def _get_whole_sketch_height(q):
    """Always return fixed sketch height if whole-question sketch requested."""
    spec = q.get("sketch")
    if isinstance(spec, dict):
        if spec.get("whole"):
            return DEFAULT_SKETCH_H
        return 0
    if spec:
        return DEFAULT_SKETCH_H
    return 0

def _is_whole_sketch_only(q):
    """Return True if whole-question sketch_only is set."""
    spec = q.get("sketch_only")
    if isinstance(spec, dict):
        return bool(spec.get("whole"))
    return bool(spec)


# -------------------------
# PDF setup
# -------------------------
c = canvas.Canvas(filepath, pagesize=A4)
width, height = A4
page_has_content = False

left_margin = 2 * cm
right_margin = 2 * cm
top_margin = 1.5 * cm
bottom_margin = 2.0 * cm
gutter_x = left_margin
text_x = gutter_x + 25
line_height = 13
styles = getSampleStyleSheet()
normal_style = ParagraphStyle("normal", parent=styles["Normal"], fontName="Helvetica", fontSize=10, leading=12)
toc_entry_style = ParagraphStyle("toc_entry", parent=styles["Normal"], fontName="Helvetica", fontSize=12, leading=14)
toc_header_style = ParagraphStyle("toc_header", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=14, leading=16)
content_width = width - left_margin - right_margin

# normalize images_for_parts
for q in questions:
    image_field = q.get("image")
    if isinstance(image_field, dict):
        q["_images_for_parts"] = image_field
    else:
        q["_images_for_parts"] = {"b": image_field} if image_field else {}

# -------------------------
# Page helpers
# -------------------------
# ---------- Page helpers (simplified & deterministic) ----------
def finish_page(start_new=True, footer_text=None, force=False):
    """Draw footer and page number then (usually) start a new page.

    - If start_new True we WILL call showPage() unless:
        * start_new==True and force==False and page_has_content==False:
          -> we will NOT create a new page (this preserves earlier small optimization).
    - For clarity: whenever you *must* advance to a fresh page (divider, end_of_topic),
      call finish_page(start_new=True, force=True).
    """
    global page_has_content
    try:
        # draw footer & page number only if anything was drawn (or if user wants footer anyway)
        if page_has_content or footer_text:
            c.setFont("Helvetica", 8)
            c.setFillColor(colors.grey)
            ft = footer_text or ""
            c.drawString(left_margin, bottom_margin - 14, ft)
            c.setFillColor(colors.black)
            c.setFont("Helvetica-Bold", 11)
            c.drawRightString(width - right_margin, bottom_margin - 10, str(c.getPageNumber()))
            dbg("Finishing page (with content/footer)")
        else:
            dbg("Finishing page (no content & no footer)")

        # Decision to actually create a new page:
        if start_new:
            if page_has_content or force:
                c.showPage()
                dbg("start_new -> showPage() called")
            else:
                dbg("start_new requested but page empty & force==False -> skipping showPage()")
        # reset content flag on the new current page
        page_has_content = False
    except Exception as e:
        dbg(f"finish_page exception: {e}")
        # fallback: try to show a new page to keep running
        if start_new:
            c.showPage()
            page_has_content = False

def start_new_page(header_text=None):
    """Convenience: finish current page (if necessary) and start a fresh page with header drawn.
       This *forces* a new page even if current page had no content.
       Use this when you want an absolutely clean page for the next section.
    """
    # force break from whatever we're on
    finish_page(start_new=True, force=True)
    dbg("New (forced) page started")
    # draw header on the new page (header doesn't mark the page as content)
    if header_text:
        c.setFont("Helvetica-Bold", 9)
        c.drawCentredString(width/2.0, height - top_margin + 6, header_text)
    else:
        c.setFont("Helvetica-Bold", 9)
        c.drawCentredString(width/2.0, height - top_margin + 6, "")
    c.setLineWidth(0.4)
    c.setStrokeColor(colors.grey)
    c.line(left_margin, height - top_margin - 2, width - right_margin, height - top_margin - 2)
    c.setStrokeColor(colors.black)
    # header alone is not 'content'; leave page_has_content False
    return height - top_margin - 36

# -------------------------
# Build topic order
# -------------------------
topics_in_order = list(dict.fromkeys(q["chapter_title"] for q in questions))

# -------------------------
# SIMULATION PASS (uses end_of_topic to predict divider pages)
# -------------------------
def simulate_layout(questions, topics):
    """Return (topic_divider_pages, topic_ms_start_pages, ms_divider_page)."""
    # page 1 front, page 2 TOC
    p = 2
    topic_divider_pages = {}
    topic_ms_start_pages = {}

    def sim_question(q, y, page):
        # simulate layout for a single question, returning (y, page)
        y -= 36
        if y < bottom_margin + 40:
            page += 1
            y = height - top_margin - 36
            y -= 36
        qtext = tidy_text_for_math(q.get("question_text", ""))
        parts = re.split(r'(?=\([a-z]\))', qtext, flags=re.IGNORECASE)
        if len(parts) == 1:
            for _ in wrapped_lines(parts[0], 95):
                y -= line_height
                if y < bottom_margin + 40:
                    page += 1
                    y = height - top_margin - 36
            lp = lines_per_marks(q.get("marks", 0))
            for _ in range(lp):
                y -= (line_height + 2)
                if y < bottom_margin + 40:
                    page += 1
                    y = height - top_margin - 36
        else:
            intro = parts[0].strip()
            if intro:
                for _ in wrapped_lines(intro, 95):
                    y -= line_height
                    if y < bottom_margin + 40:
                        page += 1
                        y = height - top_margin - 36
            for part_block in parts[1:]:
                if not part_block.strip():
                    continue
                m = re.match(r'\(([a-z])\)\s*(.*)', part_block.strip(), re.S | re.I)
                if not m:
                    for _ in wrapped_lines(part_block, 95):
                        y -= line_height
                        if y < bottom_margin + 40:
                            page += 1
                            y = height - top_margin - 36
                    continue
                body = m.group(2).strip()
                for _ in wrapped_lines(body, 80):
                    y -= line_height
                    if y < bottom_margin + 40:
                        page += 1
                        y = height - top_margin - 36
                if q.get("image") or any(q.get("_images_for_parts", {}).values()):
                    y -= 4.0 * cm
                    if y < bottom_margin + 40:
                        page += 1
                        y = height - top_margin - 36
                mmarks = re.search(r'\[(\d+)\]', body)
                marks_for_part = int(mmarks.group(1)) if mmarks else 0
                lp = lines_per_marks(marks_for_part)
                for _ in range(lp):
                    y -= (line_height + 2)
                    if y < bottom_margin + 40:
                        page += 1
                        y = height - top_margin - 36
        y -= 12
        if y < bottom_margin + 40:
            page += 1
            y = height - top_margin - 36
        return y, page

    # --- simulate topical content ---
    page = p
    for t in topics:
        # divider consumes a page -> that is the divider page for this topic
        page += 1
        topic_divider_pages[t] = page

        # questions start on the next page
        page += 1
        y = height - top_margin - 36

        for q in [qq for qq in questions if qq["chapter_title"] == t]:
            y, page = sim_question(q, y, page)
            # if the question explicitly ends the topic, simulate the forced page break
            if q.get("end_of_topic"):
                page += 1
                y = height - top_margin - 36

    # --- simulate marking scheme pages ---
    # place the MS divider on the page after the last topical page
    ms_divider = max(page - 1, p + 1)

    # start simulation from the divider page; MS content begins on the page after the divider
    page = ms_divider

    for t in topics:
        # MS topic will start on the next page
        page += 1
        topic_ms_start_pages[t] = page

        # start at top of that page
        y = height - top_margin - 36
        y -= 20  # header area for MS topic

        for q in [qq for qq in questions if qq["chapter_title"] == t]:
            y -= 18  # small gap per question/block
            if y < bottom_margin + 60:
                page += 1
                y = height - top_margin - 36
                y -= 18

            qtext = tidy_text_for_math(q.get("question_text", ""))
            has_parts = bool(re.search(r'\([a-z]\)', qtext, flags=re.IGNORECASE))

            if not has_parts:
                para_lines = wrapped_lines(next(iter(q.get("answer_text", {}).values()), ""), 95)
                for _ in para_lines:
                    y -= line_height
                    if y < bottom_margin + 60:
                        page += 1
                        y = height - top_margin - 36
            else:
                for part in sorted(q.get("answer_text", {}).keys()):
                    para_lines = wrapped_lines(q["answer_text"][part], 95)
                    for _ in para_lines:
                        y -= line_height
                        if y < bottom_margin + 60:
                            page += 1
                            y = height - top_margin - 36
                            y -= line_height
            y -= 12

        # we do NOT force an extra page increment here because rendering forces a clean page after each topic;
        # the page variable already reflects how many pages the MS topic consumed.

    return topic_divider_pages, topic_ms_start_pages, ms_divider

topic_divider_pages, topic_ms_start_pages, ms_divider_page = simulate_layout(questions, topics_in_order)

print("SIMULATION: topic divider pages:", topic_divider_pages)
print("SIMULATION: topic MS start pages:", topic_ms_start_pages)
print("SIMULATION: MS divider page:", ms_divider_page)

# -------------------------
# FRONT PAGE
# -------------------------
c.setFont("Times-Bold", 22)
c.drawCentredString(width/2, height/2 + 40, "Physics — Topical Past Papers")
c.setFont("Helvetica", 12)
c.drawCentredString(width/2, height/2 + 15, "Compiled booklet")
page_has_content = True
finish_page(start_new=True)

# -------------------------
# TABLE OF CONTENTS
# -------------------------
tp_rows = []
tp_rows.append([Paragraph('<b>Topical Past Papers</b>', toc_header_style), Paragraph('<b>Page</b>', toc_header_style)])
for topic in topics_in_order:
    tp_rows.append([Paragraph(topic, toc_entry_style), Paragraph(str(topic_divider_pages.get(topic, '')), toc_entry_style)])

tp_col_widths = [content_width - 3.0*cm, 3.0*cm]
tp_tbl = Table(tp_rows, colWidths=tp_col_widths)
tp_tbl.setStyle(TableStyle([
    ("FONT", (0,0), (-1,0), "Helvetica-Bold", 14),
    ("BACKGROUND", (0,0), (-1,0), colors.lightgrey),
    ("ALIGN", (0,0), (-1,-1), "LEFT"),
    ("VALIGN", (0,0), (-1,-1), "TOP"),
    ("GRID", (0,0), (-1,-1), 0.5, colors.black),
    ("LEFTPADDING", (0,0), (-1,-1), 8),
    ("RIGHTPADDING", (0,0), (-1,-1), 6),
    ("TOPPADDING", (0,0), (-1,-1), 6),
    ("BOTTOMPADDING", (0,0), (-1,-1), 6),
]))

t_w, t_h = tp_tbl.wrap(content_width, height)
tbl_x = left_margin
tbl_y = height - top_margin - 40 - t_h
if tbl_y < bottom_margin:
    finish_page(start_new=True)
    tbl_y = height - top_margin - 40 - t_h
tp_tbl.drawOn(c, tbl_x, tbl_y)
page_has_content = True

# === CHANGE ===
# Keep the topical TOC table and the MS TOC table on the same page.
# Do NOT force a page break here. Instead draw the MS TOC below if it fits.
gap_after = 18
y_after = tbl_y - gap_after
# === END CHANGE ===

ms_rows = []
ms_rows.append([Paragraph('<b>Marking Scheme</b>', toc_header_style), Paragraph('<b>Page</b>', toc_header_style)])
for topic in topics_in_order:
    ms_rows.append([Paragraph(topic, toc_entry_style), Paragraph(str(topic_ms_start_pages.get(topic, '')), toc_entry_style)])

ms_tbl = Table(ms_rows, colWidths=tp_col_widths)
ms_tbl.setStyle(TableStyle([
    ("FONT", (0,0), (-1,0), "Helvetica-Bold", 14),
    ("BACKGROUND", (0,0), (-1,0), colors.lightgrey),
    ("ALIGN", (0,0), (-1,-1), "LEFT"),
    ("VALIGN", (0,0), (-1,-1), "TOP"),
    ("GRID", (0,0), (-1,-1), 0.5, colors.black),
    ("LEFTPADDING", (0,0), (-1,-1), 8),
    ("RIGHTPADDING", (0,0), (-1,-1), 6),
    ("TOPPADDING", (0,0), (-1,-1), 6),
    ("BOTTOMPADDING", (0,0), (-1,-1), 6),
]))
m_w, m_h = ms_tbl.wrap(content_width, height)
tbl2_y = y_after - m_h
if tbl2_y < bottom_margin:
    # if it doesn't fit, then force a new page and draw the MS TOC there
    finish_page(start_new=True)
    tbl2_y = height - top_margin - 40 - m_h
ms_tbl.drawOn(c, tbl_x, tbl2_y)
page_has_content = True

# === CHANGE ===
# Only force a fresh page after both TOC tables are drawn, so the first topic divider starts on a clean page.
finish_page(start_new=True, force=True)
# === END CHANGE ===

# -------------------------
# Render topical content grouped by topic
# -------------------------
# We'll capture the actual divider & MS start pages during rendering to compare with simulation.
actual_topic_divider_pages = {}       # === CHANGE: ensure this dict exists before draw_topic_divider uses it
actual_topic_ms_start_pages = {}

def draw_topic_divider(title):
    global page_has_content
    # draw divider on current page
    c.setFont("Times-Bold", 20)
    c.drawCentredString(width/2, height/2 + 20, title)
    c.setFont("Helvetica", 13)
    c.drawCentredString(width/2, height/2 - 6, "Topical Past Papers")
    page_has_content = True      # mark that this page has content

    # === CHANGE ===
    # record the actual divider page number at render time
    actual_topic_divider_pages[title] = c.getPageNumber()
    # === END CHANGE ===

    # finish the divider page and force a new page for the questions (divider must be alone)
    finish_page(start_new=True, force=True)

    # Now draw the subtle header on the fresh page, but DO NOT mark page_has_content = True for this header
    c.setFont("Helvetica-Bold", 9)
    c.drawCentredString(width/2.0, height - top_margin + 6, "")
    c.setLineWidth(0.4)
    c.setStrokeColor(colors.grey)
    c.line(left_margin, height - top_margin - 2, width - right_margin, height - top_margin - 2)
    c.setStrokeColor(colors.black)

    return height - top_margin - 36


def draw_question(q, y):
    global page_has_content
    dbg(f"Start question {q.get('question_number')} ({q.get('chapter_title')}) at y={y}")
    page_has_content = True
    ident = f"{q.get('exam_series','')} | {q.get('subject','')} | {q.get('original_ref','')}"
    y = ensure_space_for_render(y, 36)
    c.setFont("Helvetica-Oblique", 8.5)
    c.drawString(left_margin, y, ident)
    y -= 16

    qtext = tidy_text_for_math(q.get("question_text",""))
    parts = re.split(r'(?=\([a-z]\))', qtext, flags=re.IGNORECASE)
    has_parts = len(parts) > 1
    printed_number = False
    last_text_line_y = None

    if has_parts:
        intro = parts[0].strip()
        intro_lines = wrapped_lines(intro, max_chars=95) if intro else []
        for line in intro_lines:
            if not line.strip():
                y -= line_height; continue
            y = ensure_space_for_render(y, line_height)
            if not printed_number:
                c.setFont("Helvetica-Bold", 11)
                c.drawString(gutter_x - 12, y, str(q.get("question_number","")))  # shift left by 12 pts
                printed_number = True
            c.setFont("Helvetica", 10.5)
            c.drawString(text_x, y, line)
            last_text_line_y = y
            y -= line_height
        if last_text_line_y:
            total_marks_label = f"[{q.get('marks',0)}]"
            c.setFont("Helvetica-Bold", 9)
            c.drawRightString(width - right_margin, last_text_line_y, total_marks_label)
        y -= 6

        for part_block in parts[1:]:
            if not part_block.strip():
                continue
            m = re.match(r'\(([a-z])\)\s*(.*)', part_block.strip(), re.S | re.IGNORECASE)
            if not m:
                for line in wrapped_lines(part_block, max_chars=95):
                    if not line.strip():
                        y -= line_height; continue
                    y = ensure_space_for_render(y, line_height)
                    if not printed_number:
                        c.setFont("Helvetica-Bold", 11)
                        c.drawString(gutter_x - 12, y, str(q.get("question_number","")))  # shift left by 12 pts
                        printed_number = True
                    c.setFont("Helvetica", 10.5)
                    c.drawString(text_x, y, line)
                    last_text_line_y = y
                    y -= line_height
                continue

            label = m.group(1).lower()
            body = m.group(2).strip()
            body_lines = wrapped_lines(body, max_chars=80)
            body_lines_count = sum(1 for L in body_lines if L.strip())

            image_present = bool(q["_images_for_parts"].get(label))
            image_est_h = 4.0 * cm if image_present else 0

            # per-part sketch height and sketch_only flag (NEW logic)
            sketch_h_cm = _get_part_sketch_height(q, label)
            sketch_only_for_part = _is_part_sketch_only(q, label)

            mmarks = re.search(r'\[(\d+)\]', body)
            marks_for_part = int(mmarks.group(1)) if mmarks else 0
            lp = lines_per_marks(marks_for_part)

            # if sketch_only for this part, we do not reserve answer lines after the sketch
            lines_to_draw = 0 if sketch_only_for_part else lp

            needed = body_lines_count * line_height + image_est_h + sketch_h_cm + lines_to_draw * (line_height + 2) + 60
            y = ensure_space_for_render(y, needed)

            c.setFont("Helvetica-Bold", 10.5)
            c.drawString(text_x - 20, y, f"({label})")
            c.setFont("Helvetica", 10.5)
            for bl in body_lines:
                if not bl.strip():
                    y -= line_height
                    continue
                if not printed_number:
                    c.setFont("Helvetica-Bold", 11)
                    c.drawString(gutter_x - 12, y, str(q.get("question_number","")))  # shift left by 12 pts
                    printed_number = True
                    c.setFont("Helvetica", 10.5)
                # shift part text rightwards so it doesn’t clash with number
                c.drawString(text_x + 12, y, bl)   # +12 offset
                last_text_line_y = y
                y -= line_height
                last_text_line_y = y
                y -= line_height

            img_url = q["_images_for_parts"].get(label)
            if img_url:
                local_ext = os.path.splitext(img_url)[1] or ".img"
                local_name = download_image(img_url, f"img_q{q.get('question_number')}_{label}" + local_ext)
                if local_name and os.path.exists(local_name):
                    try:
                        max_w, max_h = 7.0 * cm, 4.0 * cm
                        if y - max_h < bottom_margin + 20:
                            y = start_new_page(None)
                        c.drawImage(local_name, text_x, y - max_h, max_w, max_h, preserveAspectRatio=True, mask='auto')
                        y -= (max_h + 12)
                    except Exception:
                        pass

            # draw sketch area if requested (keeps previous behavior for numeric sizes)
            if sketch_h_cm:
                rect_top = y
                rect_bottom = y - sketch_h_cm
                if rect_bottom < bottom_margin + 20:
                    y = start_new_page(None)
                    rect_top = y
                    rect_bottom = y - sketch_h_cm
                # Draw a clean sketch area (no dashed box, just top & bottom lines)
                c.setStrokeColor(colors.lightgrey)
                c.setLineWidth(0.8)

                # Top line
                c.line(text_x, rect_top, width - right_margin, rect_top)
                # Bottom line
                c.line(text_x, rect_bottom, width - right_margin, rect_bottom)

                c.setStrokeColor(colors.black)

                y = rect_bottom - 24

            # draw answer lines only if not sketch_only_for_part
            c.setStrokeColor(colors.grey)
            c.setLineWidth(0.6)
            c.setDash(1, 3)
            for i in range(lines_to_draw):
                if y < bottom_margin + 20:
                    y = start_new_page(None)
                c.line(text_x, y, width - right_margin, y)
                y -= (line_height + 2)
            c.setDash()
            y -= 8

    else:
        body_lines = wrapped_lines(parts[0], max_chars=95)
        body_count = sum(1 for L in body_lines if L.strip())

        # whole-question sketch height and sketch_only
        sketch_h = _get_whole_sketch_height(q)
        sketch_only_whole = _is_whole_sketch_only(q)

        lp = lines_per_marks(q.get("marks", 0))
        lines_to_draw = 0 if sketch_only_whole else lp

        needed = body_count * line_height + sketch_h + lines_to_draw * (line_height + 2) + 60
        y = ensure_space_for_render(y, needed)
        printed_number = False
        last_text_line_y = None
        for bl in body_lines:
            if not bl.strip():
                y -= line_height; continue
            if not printed_number:
                c.setFont("Helvetica-Bold", 11)
                c.drawString(gutter_x - 12, y, str(q.get('question_number','')))
                printed_number = True
            c.setFont("Helvetica", 10.5)
            c.drawString(text_x, y, bl)
            last_text_line_y = y
            y -= line_height
        if last_text_line_y:
            total_marks_label = f"[{q.get('marks',0)}]"
            c.setFont("Helvetica-Bold", 9)
            c.drawRightString(width - right_margin, last_text_line_y, total_marks_label)

        # draw single-block sketch area (if any)
        # draw single-block sketch area (if any)
        if sketch_h:
            rect_top = y
            rect_bottom = y - sketch_h
            if rect_bottom < bottom_margin + 20:
                y = start_new_page(None)
                rect_top = y
                rect_bottom = y - sketch_h
            # Draw a clean sketch area (no dashed box, just top & bottom lines)
            c.setStrokeColor(colors.lightgrey)
            c.setLineWidth(0.8)

            # Top line
            c.line(text_x, rect_top, width - right_margin, rect_top)
            # Bottom line
            c.line(text_x, rect_bottom, width - right_margin, rect_bottom)

            c.setStrokeColor(colors.black)

            y = rect_bottom - 24

            # Add breathing space depending on sketch_only
            if sketch_only_whole:
                y -= line_height * 2   # more gap if sketch-only
            else:
                y -= line_height * 2   # gap before answer lines

        # draw answer lines (unless whole sketch_only)
        c.setStrokeColor(colors.grey)
        c.setLineWidth(0.6)
        c.setDash(1, 3)
        for i in range(lines_to_draw):
            if y < bottom_margin + 20:
                y = start_new_page(None)
            c.line(text_x, y, width - right_margin, y)
            y -= (line_height + 2)
        c.setDash()
        y -= 8

    dbg(f"End question {q.get('question_number')} on page {c.getPageNumber()} at y={y}")
    return y

def ensure_space_for_render(y, needed_h):
    if y - needed_h < bottom_margin + 20:
        return start_new_page(None)
    return y

# Keep track: which topic we're in to record actual ms start pages later
topic_pages_map = {}

# Render topical content grouped by topic
for topic in topics_in_order:
    y = draw_topic_divider(topic)
    # iterate over questions in topic preserving input order
    topic_questions = [qq for qq in questions if qq["chapter_title"] == topic]
    for idx, q in enumerate(topic_questions):
        y = draw_question(q, y)
        y -= 12
        # If the question explicitly ends the topic, force a clean page break so next divider starts on a fresh page
        if q.get("end_of_topic"):
            dbg("Question marked end_of_topic -> forcing page break")
            finish_page(start_new=True, force=True)
            # then set up header for next page if you like (not marking page_has_content)
            c.setFont("Helvetica-Bold", 9)
            c.drawCentredString(width/2.0, height - top_margin + 6, "")
            c.setLineWidth(0.4)
            c.setStrokeColor(colors.grey)
            c.line(left_margin, height - top_margin - 2, width - right_margin, height - top_margin - 2)
            c.setStrokeColor(colors.black)
            y = height - top_margin - 36

# -------------------------
# MARKING SCHEME SECTION (REPLACEMENT BLOCK)
# -------------------------
# Ensure ms pages dict exists
# actual_topic_ms_start_pages already declared above

# 1) Ensure a clean page and draw MS divider (force the page break so divider is alone)
finish_page(start_new=True, force=True)
c.setFont("Times-Bold", 20)
c.drawCentredString(width/2, height/2 + 20, "Marking Scheme")
dbg("Drawing Marking Scheme divider")
c.setFont("Helvetica", 13)
c.drawCentredString(width/2, height/2 - 6, "Answers grouped by topic")
page_has_content = True

# Record MS divider page explicitly
ms_divider_actual_page = c.getPageNumber()
dbg(f"At MS divider (actual page {ms_divider_actual_page})")

# Finish divider page and force a fresh page for first MS topic
finish_page(start_new=True, force=True)

# 2) For each topic: ensure MS starts on its own page, record its start page, draw table
for topic in topics_in_order:
    # Start a fresh page for this MS topic (if current page has content, this will advance; force=True ensures a clean start)
    # However since we just forced a fresh page after the divider, the first topic will start on that page.
    # To be absolutely robust, force a (possibly empty) page break BEFORE starting each topic except when page is already blank.
    # Use finish_page with force=True to guarantee page boundaries are consistent.
    finish_page(start_new=False, force=False)  # no-op if page empty, safe otherwise

    # Record the page number where this MS topic begins
    actual_ms_start = c.getPageNumber()
    actual_topic_ms_start_pages[topic] = actual_ms_start
    dbg(f"MS for topic '{topic}' starts on actual page {actual_ms_start}")

    # Draw MS topic header (this marks the page as having content)
    c.setFont("Helvetica-Bold", 14)
    y = height - top_margin - 36
    c.drawString(left_margin, y, topic + " — Marking Scheme")
    y -= 20
    page_has_content = True

    # Build table rows with Marks column. Single-block questions: Part = "-", Marks = total.
    table_rows = [["Question", "Part", "Marks", "Answer"]]
    for q in [qq for qq in questions if qq["chapter_title"] == topic]:
        qtext = tidy_text_for_math(q.get("question_text", ""))
        has_parts = bool(re.search(r'\([a-z]\)', qtext, flags=re.IGNORECASE))
        if not has_parts:
            # single-block question -> single row with Part = "-" and Marks = question marks
            ans_text = tidy_text_for_math(next(iter(q.get("answer_text", {}).values()), ""))
            para = Paragraph(ans_text, normal_style)
            table_rows.append([f"{q.get('question_number')}", "-", f"{q.get('marks', 0)}", para])
        else:
            # question has parts -> list each part on its own row and attempt to extract per-part marks
            first_row = True
            for part_key in sorted(q.get("answer_text", {}).keys()):
                ans = tidy_text_for_math(q["answer_text"][part_key])
                para = Paragraph(ans, normal_style)
                marks_part = "-"
                # best-effort: find "[n]" immediately after the (part) text in the question body
                m = re.search(rf'\({re.escape(part_key)}\)[^\[]*\[(\d+)\]', tidy_text_for_math(q.get("question_text","")), flags=re.IGNORECASE)
                if m:
                    marks_part = int(m.group(1))
                if first_row:
                    table_rows.append([f"{q.get('question_number')}", f"({part_key})", marks_part, para])
                    first_row = False
                else:
                    table_rows.append(["", f"({part_key})", marks_part, para])

    # Table drawing: give a dedicated start; if it doesn't fit, start a new page and draw there.
    col_widths = [2.0*cm, 2.0*cm, 2.0*cm, content_width - 6.0*cm]
    tbl = Table(table_rows, colWidths=col_widths, repeatRows=1)
    tbl.setStyle(TableStyle([
        ("FONT", (0,0), (-1,0), "Helvetica-Bold", 10),
        ("BACKGROUND", (0,0), (-1,0), colors.lightgrey),
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("GRID", (0,0), (-1,-1), 0.5, colors.black),
        ("LEFTPADDING", (0,0), (-1,-1), 6),
        ("RIGHTPADDING", (0,0), (-1,-1), 6),
        ("TOPPADDING", (0,0), (-1,-1), 6),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
    ]))

    # wrap the table to see if it fits on the current page under the header area
    w_tbl, h_tbl = tbl.wrapOn(c, content_width, height)
    available = y - bottom_margin - 20
    if h_tbl > available:
        # not enough space: start a fresh page for this table
        finish_page(start_new=True, force=True)
        # header for table continuation (marks this new page as content)
        c.setFont("Helvetica-Bold", 14)
        y = height - top_margin - 36
        c.drawString(left_margin, y, topic + " — Marking Scheme (cont.)")
        y -= 20
        page_has_content = True
        w_tbl, h_tbl = tbl.wrapOn(c, content_width, height)

    # draw table on the current page
    tbl.drawOn(c, left_margin, y - h_tbl)
    page_has_content = True

    # After finishing a topic MS, force a page break so the next topic's MS starts on its own page.
    finish_page(start_new=True, force=True)

# Final footer on last page (do not add spurious pages)
finish_page(start_new=False)   # draw footer if needed, but do NOT create a new page
c.save()

# Print simulation vs actual maps for you to inspect
print("--- SIMULATION RESULTS (reprinted) ---")
print("Simulated topic divider pages:", topic_divider_pages)
print("Simulated topic MS start pages:", topic_ms_start_pages)
print("Simulated MS divider page:", ms_divider_page)
print("--- ACTUAL (render-time) RESULTS ---")
print("Actual topic divider pages:", actual_topic_divider_pages)
print("Actual topic MS start pages:", actual_topic_ms_start_pages)
print("Actual MS divider page:", ms_divider_actual_page)
print("Done — PDF written to:", filepath)
