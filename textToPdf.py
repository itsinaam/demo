from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
import json
from reportlab.platypus import PageBreak
from reportlab.platypus import HRFlowable
from reportlab.lib.enums import TA_LEFT

logo_path = "./response.png"

def generate_review_pdf(parsed_json: dict, output_path: str , url : str):
    key_map = {
        "Customer Review Analysis": "Customer_Review_Analysis",
        "What you’ll get from this document": "What_You_Get",
        "Disclaimer": "Disclaimer",
        "Overall Sentiment Analysis": "Overall_Sentiment_Analysis",
        "Pros": "Pros",
        "Cons": "Cons",
        "Existing Copy Summary": "Existing_Copy_Summary",
        "General Copy & Messaging Suggestions": "Messaging_Suggestions",
        "Headline & Subhead Suggestions": "Headline_Suggestions",
        "CTA Suggestions": "CTA_Suggestions",
        "CTA Overall Why It Works": "CTA_Overall_Why_It_Works",
        "Conclusion": "Conclusion"
    }
    normalized_json = {key_map.get(k, k): v for k, v in parsed_json.items()}


    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    # Register Arial
    pdfmetrics.registerFont(TTFont('Arial', './ARIAL.TTF'))
    pdfmetrics.registerFont(TTFont('Arial-Bold', './ARIALBD.TTF'))
 

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="TitleStyle", fontName="Arial-Bold", fontSize=25, leading=22, alignment=TA_CENTER, spaceAfter=30,textColor=colors.HexColor("#581d6b")))
    styles.add(ParagraphStyle(name="HeadingStyle", fontName="Arial-Bold", fontSize=12, leading=18, spaceAfter=2,leftIndent=20))
    styles.add(ParagraphStyle(name="HeadingStyle-color", fontName="Arial-Bold", fontSize=16, leading=18, spaceAfter=2,textColor=colors.HexColor("#581d6b")))
    styles.add(ParagraphStyle(name="SubHeadingStyle", fontName="Arial-Bold", fontSize=12, leading=16, spaceAfter=6))
    styles.add(ParagraphStyle(name="ProsTitle", fontName="Arial-Bold", fontSize=12,leftIndent=45))
    styles.add(ParagraphStyle(name="BodyStyle", fontName="Arial", fontSize=12, leading=16, alignment=TA_LEFT, spaceAfter=6, rightIndent=20, leftIndent=20))
    styles.add(ParagraphStyle(name="ItalicStyle", fontName="Helvetica-Oblique", fontSize=12, leading=14, leftIndent=20))
    styles.add(ParagraphStyle(name="cta-style", fontName="Arial-Bold", fontSize=12, leftIndent=20))
    # Custom styles for messaging section
    styles.add(ParagraphStyle(name="SectionHeadingPurple", fontName="Arial-Bold", fontSize=16,textColor=colors.HexColor("#581d6b"), spaceAfter=12))
    styles.add(ParagraphStyle(name="SubHeadingBold", fontName="Arial-Bold", fontSize=13,textColor=colors.black, spaceAfter=4))
    styles.add(ParagraphStyle(name="SubHeadingBold-color", fontName="Arial-Bold", fontSize=16,textColor=colors.HexColor("#581d6b"),spaceAfter=4,spaceBefore=8,leftIndent=20))
    styles.add(ParagraphStyle(name="SuggestionBox", fontName="Helvetica", fontSize=11,backColor=colors.HexColor("#f8ecfc"),borderColor=colors.HexColor("#581d6b"),borderWidth=1,leading=16,leftIndent=6, rightIndent=6,spaceBefore=6, spaceAfter=6,borderPadding=(6, 6, 6, 6)))
    styles.add(ParagraphStyle(name="HeadlineNumber", fontName="Arial-Bold", fontSize=13,textColor=colors.HexColor("#581d6b"), spaceAfter=6))
    styles.add(ParagraphStyle(name="MainHeadline", fontName="Arial-Bold", fontSize=16,alignment=TA_CENTER, spaceAfter=4))
    styles.add(ParagraphStyle(name="SubheadItalic", fontName="Helvetica-Oblique", fontSize=14,alignment=TA_CENTER, textColor=colors.black, spaceAfter=10))
    styles.add(ParagraphStyle(name="WhyHeading", fontName="Arial-Bold", fontSize=12,textColor=colors.black, spaceAfter=2))
    styles.add(ParagraphStyle(name="WhyBody", fontName="Arial", fontSize=12,textColor=colors.black, spaceAfter=12))
    styles.add(ParagraphStyle(name="BodyStyle-url", fontName="Arial", fontSize=12, leading=14, alignment=TA_LEFT, spaceAfter=6,))
    styles.add(ParagraphStyle(name="summaryStyle", fontName="Arial", fontSize=12, leading=16, alignment=TA_LEFT, spaceAfter=6, rightIndent=5, leftIndent=5))
    styles.add(ParagraphStyle(name="whyTheyWork", fontName="Arial", fontSize=12, spaceAfter=6,leading=16, spaceBefore=0, leftIndent=20,alignment=TA_LEFT))
    styles.add(ParagraphStyle(name="whyTheyWork-title", fontName="Arial-Bold", fontSize=12, spaceAfter=6,leading=16, spaceBefore=8, leftIndent=20,alignment=TA_LEFT))
    Story = []

    def add_header(canvas, doc):
        canvas.saveState()
        page_width, page_height = A4
        logo_width = 1.42 * inch
        logo_height = 0.34 * inch
        logo_x = (page_width - logo_width) / 2
        logo_y = page_height - 1.0 * inch
        try:
            canvas.setFillAlpha(0.5)  # 50% opacity
        except AttributeError:
            pass  
        canvas.drawImage(ImageReader(logo_path), logo_x, logo_y, width=logo_width, height=logo_height, mask='auto')
        canvas.linkURL("https://www.crogenie.com/report", (logo_x, logo_y, logo_x + logo_width, logo_y + logo_height))
        canvas.restoreState()

    def add_footer(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 11)
        page_width, _ = A4
        y = 0.5 * inch
        static = "Generated by "
        link = "CROGenie.com"
        x = (page_width - canvas.stringWidth(static + link, "Helvetica", 11)) / 2
        canvas.drawString(x, y, static)
        canvas.setFillColorRGB(0, 0, 1)
        canvas.drawString(x + canvas.stringWidth(static, "Helvetica", 11), y, link)
        canvas.line(x + canvas.stringWidth(static, "Helvetica", 11), y - 1,
                    x + canvas.stringWidth(static + link, "Helvetica", 11), y - 1)
        canvas.linkURL("https://www.crogenie.com/report",
                       (x + canvas.stringWidth(static, "Helvetica", 11), y,
                        x + canvas.stringWidth(static + link, "Helvetica", 11), y + 10))
        canvas.restoreState()

    def add_paragraph(text):
        Story.append(Paragraph(text, styles["BodyStyle"]))
        Story.append(Spacer(1, 10))

    def add_section_title(title, bookmark_name=None):
        if bookmark_name:
            Story.append(Paragraph(f'<a name="{bookmark_name}"/>{title}', styles["SubHeadingBold-color"]))
        else:
            Story.append(Paragraph(title, styles["SubHeadingBold-color"]))
        Story.append(Spacer(1, 25))
    
    def why_they_work_title(title):
        Story.append(Paragraph(title, styles["whyTheyWork-title"]))
        Story.append(Spacer(1, 3))

    def add_numbered_items(items):
        for idx, item in enumerate(items, 1):
            Story.append(Paragraph(f"{idx}. <b>{item.get('title')}</b>",styles["ProsTitle"] ))
            Story.append(Spacer(1, 12))
            if item.get("description"):
                Story.append(Paragraph(item["description"], styles["BodyStyle"]))
                Story.append(Spacer(1, 10))
            if item.get("example"):
                Story.append(Paragraph(f" Example: {item['example']}", styles["ItalicStyle"]))
                Story.append(Spacer(1, 10))
            Story.append(Spacer(1, 40))
        Story.append(Spacer(1, 40))

    def add_table(rows):
        header_style = styles["HeadingStyle"]
        cell_style = styles["BodyStyle"]
        Story.append(Paragraph("<b>Breakdown by User Types:</b>",header_style))
        data = [[Paragraph("<b>User Type</b>", header_style),
                 Paragraph("<b>Positive Sentiment</b>", header_style),
                 Paragraph("<b>Negative Sentiment</b>", header_style),
                 Paragraph("<b>Key Themes</b>", header_style)]]
        for r in rows:
            data.append([
                Paragraph(r["User Type"], cell_style),
                Paragraph(r["Positive Sentiment"], cell_style),
                Paragraph(r["Negative Sentiment"], cell_style),
                Paragraph(r["Key Themes"], cell_style)
            ])
        t = Table(data, colWidths=[140, 80, 80, 160])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#f2e6ff")),
            ('FONTNAME', (0, 0), (-1, 0), 'Arial-Bold'),
            ('GRID', (0, 0), (-1, -1), 0.25, colors.HexColor("#660066")),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        Story.append(t)
        Story.append(Spacer(1, 12))

    def add_structured_dict(data, url: str):
        print(url)
        rows = []

        label_style = styles["SubHeadingStyle"]
        value_style = styles["BodyStyle-url"]

        # ---- URL row ----
        label = "<b>URL:</b>"
        value = f'<a href="{url}" color="blue"><u>{url}</u></a>'
        rows.append([
            Paragraph(label, label_style),
            Paragraph(value, value_style)
        ])

        # ---- Copy Alignment Score row ----
        if "alignment_score" in data:
            label = "<b>Copy Alignment Score:</b>"
            percent_value = int(data.get("alignment_score", "")) /100 * 100
            value = str(f"{percent_value}%")
            rows.append([
                Paragraph(label, label_style),
                Paragraph(value, value_style)
            ])

        # ---- Summary label row (full width, single cell) ----
        if "summary" in data:
            rows.append([
                Paragraph("<b>Summary:</b>", label_style),
                ''
            ])  # empty second cell to keep table structure
            rows.append([
                Paragraph(data["summary"], styles["summaryStyle"]),
                ''
            ])

        # ---- Table formatting ----
        t = Table(rows, colWidths=[180, 300])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f6eff8")),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('FONTNAME', (0, 0), (-1, -1), 'Arial'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('INNERGRID', (0, 0), (-1, -1), 0.7, colors.HexColor("#581d6b")),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#581d6b")),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),

            # ✅ Merge "Summary:" label across both columns
            ('SPAN', (0, len(rows)-2), (1, len(rows)-2)),

            # ✅ Merge summary text across both columns
            ('SPAN', (0, len(rows)-1), (1, len(rows)-1)),

            # ❌ Remove horizontal line between "Summary:" and its content
            ('LINEBELOW', (0, len(rows)-2), (1, len(rows)-2), 0, colors.HexColor("#f6eff8")),
        ]))

        Story.append(t)
        Story.append(Spacer(1, 30))


        # Strengths section
        if "strengths" in data and isinstance(data["strengths"], list):
            Story.append(Paragraph("<b>Strengths:</b>", styles["SubHeadingStyle"]))
            for s in data["strengths"]:
                Story.append(Paragraph(f"• {s}", styles["BodyStyle"]))
            Story.append(Spacer(1, 30))

        # Gaps section
        if "gaps" in data and isinstance(data["gaps"], list):
            Story.append(Paragraph("<b>Gaps:</b>", styles["SubHeadingStyle"]))
            for g in data["gaps"]:
                Story.append(Paragraph(f"• {g}", styles["BodyStyle"]))
            Story.append(Spacer(1, 30))



    def add_messaging_suggestions(suggestions):
        Story.append(Spacer(1, 6))
        for idx, item in enumerate(suggestions, 1):
            Story.append(Paragraph(f"<b>Core Idea #{idx}:</b> {item['core_idea_heading']}", styles["SubHeadingBold-color"]))
            Story.append(Spacer(1, 15))

            if item.get("suggestion"):
                text = f"<b>Suggestion:</b><br/>{item['suggestion']}"
                Story.append(Spacer(1, 5))
                Story.append(Paragraph(text, styles["SuggestionBox"]))
                Story.append(Spacer(1, 15))

            if item.get("why_it_works"):
                Story.append(Paragraph("<b>Why it works:</b>", styles["SubHeadingBold"]))
                Story.append(Spacer(1, 5))
                Story.append(Paragraph(item["why_it_works"], styles["BodyStyle"]))
                Story.append(Spacer(1, 15))

            if item.get("where_to_add"):
                Story.append(Paragraph("<b>Where to add:</b>", styles["SubHeadingBold"]))
                Story.append(Spacer(1, 5))
                Story.append(Paragraph(item["where_to_add"], styles["BodyStyle"]))
                Story.append(Spacer(1, 15))

            # ✅ Horizontal line separator
            Story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#666666"), spaceBefore=10, spaceAfter=20))


    def add_headlines(headlines):
        for idx, item in enumerate(headlines, 1):
            # Headline #1
            Story.append(Paragraph(f"Headline #{idx}:", styles["HeadlineNumber"]))
            Story.append(Spacer(1, 18))

            # Main headline (centered & bold)
            Story.append(Paragraph(f"{item.get('headline')}", styles["MainHeadline"]))
            Story.append(Spacer(1, 10))

            # Subhead (centered & italic)
            if item.get("subhead"):
                Story.append(Paragraph(item["subhead"], styles["SubheadItalic"]))
                Story.append(Spacer(1, 12))

            # Why it works section
            if item.get("why_it_works"):
                Story.append(Paragraph("Why it works:", styles["WhyHeading"]))
                Story.append(Spacer(1, 12))
                Story.append(Paragraph(item["why_it_works"], styles["WhyBody"]))

            # Horizontal line
            Story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#999999"),spaceBefore=6, spaceAfter=18))
            Story.append(Spacer(1, 25))


    def add_ctas(calls):
        for item in calls:
            Story.append(Paragraph(f' <b>"{item["cta"]}"</b>',styles["cta-style"]))
            # Story.append(Paragraph(item["why_it_works"]))
            Story.append(Spacer(1, 6))
        Story.append(Spacer(1, 12))
        
    def add_paragraph_why(content):
        Story.append(Paragraph(content, styles["whyTheyWork"]))

        

    # Start content
    Story.append(Spacer(1, 35))
    Story.append(Paragraph('<a name="top"/>Customer Review Analysis', styles["TitleStyle"]))

    for section, content in normalized_json.items():
        if section == "Customer_Review_Analysis":
            add_paragraph(content)
            Story.append(Spacer(1, 70))

        elif section == "What_You_Get":
            add_section_title("What you'll get from this document:")
            bullets = [
                ("Overall Sentiment Analysis", "Overall_Sentiment_Analysis"),
                ("Existing Copy Summary", "Existing_Copy_Summary"),
                ("General Copy & Messaging Suggestions", "Messaging_Suggestions"),
                ("Headline & Subhead Suggestions", "Headline_Suggestions"),
                ("CTA Suggestions", "CTA_Suggestions"),
                ("Conclusion", "Conclusion")
            ]
            for label, anchor in bullets:
                Story.append(Paragraph(f' <a href="#{anchor}" color="blue"><u>{label}</u></a>', styles["BodyStyle"]))
            Story.append(Spacer(1, 70))

        elif section == "Disclaimer":
            add_section_title("Disclaimer:")
            add_paragraph(content)
            Story.append(PageBreak())

        elif section == "Overall_Sentiment_Analysis":
            Story.append(Spacer(1, 40))
            add_section_title("Overall Sentiment Analysis", "Overall_Sentiment_Analysis")
            add_paragraph(content.get("Summary", ""))
            Story.append(Spacer(1, 40))
            add_table(content.get("Sentiment Data",[]))
            Story.append(PageBreak())

        elif section == "Pros":
            add_section_title("Pros")
            add_numbered_items(content)


        elif section == "Cons":
            add_section_title("Cons")
            add_numbered_items(content)
            Story.append(PageBreak())
            

        elif section == "Existing_Copy_Summary":
            add_section_title("Existing Copy Summary", "Existing_Copy_Summary")
            add_structured_dict(content,url)
            Story.append(PageBreak())


        elif section == "Messaging_Suggestions":
            Story.append(Spacer(1, 25))
            add_section_title("General Copy & Messaging Suggestions", "Messaging_Suggestions")  # ✅ FIXED!
            add_messaging_suggestions(content)
            Story.append(PageBreak())

        elif section == "Headline_Suggestions":
            Story.append(Spacer(1, 35))
            add_section_title("Headline & Subhead Suggestions", "Headline_Suggestions")
            add_headlines(content)
            Story.append(PageBreak())
            

        elif section == "CTA_Suggestions":
            Story.append(Spacer(1, 35))
            add_section_title("CTA Suggestions", "CTA_Suggestions")
            add_ctas(content)
            

        elif section == "overall_why_it_works":
            Story.append(Spacer(1, 15))
            why_they_work_title("Why They Work:")
            add_paragraph_why(content)
            Story.append(PageBreak())

        elif section == "Conclusion":
            Story.append(Spacer(1, 15))
            add_section_title("Conclusion", "Conclusion")
            add_paragraph(content)

    doc = SimpleDocTemplate(output_path, pagesize=A4, rightMargin=40, leftMargin=40, topMargin=60, bottomMargin=60)
    doc.build(Story,
              onFirstPage=lambda canvas, doc: (add_header(canvas, doc), add_footer(canvas, doc)),
              onLaterPages=lambda canvas, doc: (add_header(canvas, doc), add_footer(canvas, doc)))

# # Load JSON and call generator
# with open("./data.json", "r", encoding="utf-8") as f:
#     json_data = json.load(f)

# generate_review_pdf(json_data, "output.pdf", "https://video.crogenie.com/conversations/5090748c-af23-5b2e-bb17-7f1c05648824") #www.google.com/home/about/test/logn/url/tesing/dfgh

