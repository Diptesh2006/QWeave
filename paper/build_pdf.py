"""Build the formatted PDF manuscript directly from the maintained TeX source."""

from html import escape
from pathlib import Path
import re

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    FrameBreak,
    Image,
    KeepTogether,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from build_docx import AUTHORS, LEARNING_CURVE, REFERENCES, SOURCE, _clean


OUTPUT = Path(__file__).resolve().parent / "pdf" / "QWeave_Manuscript.pdf"
BLACK = colors.HexColor("#000000")


def _register_fonts() -> None:
    fonts = Path("C:/Windows/Fonts")
    pdfmetrics.registerFont(TTFont("TimesNewRoman", str(fonts / "times.ttf")))
    pdfmetrics.registerFont(TTFont("TimesNewRoman-Bold", str(fonts / "timesbd.ttf")))
    pdfmetrics.registerFont(TTFont("CourierNew", str(fonts / "cour.ttf")))


def _styles() -> dict[str, ParagraphStyle]:
    return {
        "title": ParagraphStyle(
            "PaperTitle", fontName="TimesNewRoman-Bold", fontSize=14.5,
            leading=17, alignment=TA_CENTER, textColor=BLACK, spaceAfter=5,
        ),
        "authors": ParagraphStyle(
            "Authors", fontName="TimesNewRoman-Bold", fontSize=12,
            leading=14, alignment=TA_CENTER, textColor=BLACK, spaceAfter=2,
        ),
        "email": ParagraphStyle(
            "Email", fontName="CourierNew", fontSize=12,
            leading=14, alignment=TA_CENTER, textColor=BLACK, spaceAfter=2,
        ),
        "affiliation": ParagraphStyle(
            "Affiliation", fontName="TimesNewRoman", fontSize=12,
            leading=14, alignment=TA_CENTER, textColor=BLACK,
        ),
        "abstract_heading": ParagraphStyle(
            "AbstractHeading", fontName="TimesNewRoman-Bold", fontSize=12,
            leading=14, alignment=TA_CENTER, textColor=BLACK, spaceAfter=2,
        ),
        "abstract": ParagraphStyle(
            "Abstract", fontName="TimesNewRoman", fontSize=10, leading=12,
            alignment=TA_JUSTIFY, textColor=BLACK, leftIndent=0.6 * cm,
            rightIndent=0.6 * cm, firstLineIndent=0, spaceAfter=0,
            hyphenationLang="en_US",
        ),
        "section": ParagraphStyle(
            "Section", fontName="TimesNewRoman-Bold", fontSize=12,
            leading=14, alignment=TA_LEFT, textColor=BLACK,
            spaceBefore=7, spaceAfter=3, keepWithNext=True,
        ),
        "subsection": ParagraphStyle(
            "Subsection", fontName="TimesNewRoman-Bold", fontSize=11,
            leading=13.6, alignment=TA_LEFT, textColor=BLACK,
            spaceBefore=5, spaceAfter=2, keepWithNext=True,
        ),
        "runin": ParagraphStyle(
            "RunIn", fontName="TimesNewRoman-Bold", fontSize=11,
            leading=13.6, alignment=TA_LEFT, textColor=BLACK,
            spaceBefore=3, spaceAfter=0, keepWithNext=True,
        ),
        "body": ParagraphStyle(
            "Body", fontName="TimesNewRoman", fontSize=11, leading=13.6,
            alignment=TA_JUSTIFY, textColor=BLACK, firstLineIndent=0.38 * cm,
            spaceBefore=0, spaceAfter=0,
            hyphenationLang="en_US",
        ),
        "body_first": ParagraphStyle(
            "BodyFirst", fontName="TimesNewRoman", fontSize=11, leading=13.6,
            alignment=TA_JUSTIFY, textColor=BLACK, firstLineIndent=0,
            spaceBefore=0, spaceAfter=0,
            hyphenationLang="en_US",
        ),
        "equation": ParagraphStyle(
            "Equation", fontName="TimesNewRoman", fontSize=11, leading=13.6,
            alignment=TA_CENTER, textColor=BLACK, spaceBefore=2, spaceAfter=2,
        ),
        "caption": ParagraphStyle(
            "Caption", fontName="TimesNewRoman", fontSize=10, leading=12,
            alignment=TA_CENTER, textColor=BLACK, spaceBefore=2, spaceAfter=2,
        ),
        "reference": ParagraphStyle(
            "Reference", fontName="TimesNewRoman", fontSize=10, leading=12,
            alignment=TA_LEFT, textColor=BLACK, leftIndent=0.35 * cm,
            firstLineIndent=-0.35 * cm, spaceBefore=0, spaceAfter=0,
        ),
        "table": ParagraphStyle(
            "TableText", fontName="TimesNewRoman", fontSize=7.8, leading=9,
            alignment=TA_CENTER, textColor=BLACK,
        ),
        "table_left": ParagraphStyle(
            "TableTextLeft", fontName="TimesNewRoman", fontSize=7.8, leading=9,
            alignment=TA_LEFT, textColor=BLACK,
        ),
    }


def _paragraph(text: str, style: ParagraphStyle) -> Paragraph:
    return Paragraph(escape(_clean(text)), style)


def _results_table(styles: dict[str, ParagraphStyle], width: float):
    raw = [
        ("Method", "Depth", "SWAP", "Runtime", "Fallback"),
        ("Basic", "48.5", "11.5", "0.0022", "0"),
        ("Weighted", "36.0", "0.0", "0.0036", "0"),
        ("SABRE", "46.0", "7.0", "0.0028", "0"),
        ("GNN-PPO", "37.5", "0.0", "0.3473", "4543"),
        ("No-message PPO", "36.0", "0.0", "0.1040", "742"),
        ("Untrained GNN", "198.0", "193.0", "0.6681", "8059"),
    ]
    data = []
    for row_index, row in enumerate(raw):
        data.append([
            Paragraph(
                f"<b>{escape(value)}</b>" if row_index == 0 else escape(value),
                styles["table_left"] if column_index == 0 else styles["table"],
            )
            for column_index, value in enumerate(row)
        ])
    col_widths = [0.35 * width, 0.14 * width, 0.14 * width, 0.19 * width, 0.18 * width]
    table = Table(data, colWidths=col_widths, repeatRows=1, hAlign="CENTER")
    table.setStyle(TableStyle([
        ("TEXTCOLOR", (0, 0), (-1, -1), BLACK),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("LEFTPADDING", (0, 0), (-1, -1), 1),
        ("RIGHTPADDING", (0, 0), (-1, -1), 1),
        ("LINEABOVE", (0, 0), (-1, 0), 0.75, BLACK),
        ("LINEBELOW", (0, 0), (-1, 0), 0.75, BLACK),
        ("LINEBELOW", (0, -1), (-1, -1), 0.75, BLACK),
    ]))
    caption = Paragraph(
        "Table 1  Benchmark-v2 test summary. Runtime is median wall time in seconds.",
        styles["caption"],
    )
    return KeepTogether([table, caption])


def _learning_figure(styles: dict[str, ParagraphStyle], width: float):
    if not LEARNING_CURVE.exists():
        raise FileNotFoundError(f"missing benchmark figure: {LEARNING_CURVE}")
    image = Image(str(LEARNING_CURVE), width=width, height=width * 0.38)
    image.hAlign = "CENTER"
    caption = Paragraph(
        "Figure 1  Five-seed learning curves. Lines show the median recent "
        "episode return and bands show the interquartile range.",
        styles["caption"],
    )
    return KeepTogether([image, caption])


def build() -> Path:
    _register_fonts()
    styles = _styles()
    source = SOURCE.read_text(encoding="utf-8")
    title = re.search(r"\\title\{.*?\\textbf\{(.+?)\}\}", source, re.S).group(1)
    abstract = re.search(
        r"\\begin\{abstract\}(.*?)\\end\{abstract\}", source, re.S
    ).group(1)
    body = source.split(r"\end{abstract}", 1)[1].split(r"\bibliographystyle", 1)[0]
    body = re.sub(
        r"\\begin\{table\*?\}.*?\\end\{table\*?\}",
        "\n\n[[RESULTS_TABLE]]\n\n",
        body,
        flags=re.S,
    )
    body = re.sub(
        r"\\begin\{figure\*\}.*?\\end\{figure\*\}",
        "\n\n[[LEARNING_FIGURE]]\n\n",
        body,
        flags=re.S,
    )
    equations = [
        "J(m) = &#8721;<sub>(i,j) in E_C</sub> w<sub>ij</sub> "
        "d<sub>H</sub>(m(i),m(j)).   (1)",
        "U<sub>Rk</sub>P<sub>m0</sub> = "
        "P<sub>mk</sub>U<sub>Ck</sub>, for 0 &#8804; k &#8804; T.   (2)",
        "r<sub>i</sub> = d<sub>i</sub> + max<sub>j in succ(i)</sub> r<sub>j</sub>; "
        "<br/>s<sub>i</sub> = max<sub>j in pred(i)</sub>"
        "(s<sub>j</sub> + d<sub>j</sub>).   (3)",
        "CX<sub>u&#8594;v</sub> = (H<sub>u</sub> x H<sub>v</sub>) "
        "CX<sub>v&#8594;u</sub> (H<sub>u</sub> x H<sub>v</sub>).   (4)",
    ]
    for equation in equations:
        body = re.sub(
            r"\\begin\{equation\}.*?\\end\{equation\}",
            f"\n\n[[EQUATION:{equation}]]\n\n",
            body,
            count=1,
            flags=re.S,
        )

    page_width, page_height = A4
    margin = 2.54 * cm
    gap = 0.6 * cm
    usable_width = page_width - 2 * margin
    usable_height = page_height - 2 * margin
    column_width = (usable_width - gap) / 2
    title_height = 6.8 * cm
    title_frame = Frame(
        margin, page_height - margin - title_height, usable_width, title_height,
        leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0,
        id="title",
    )
    first_column_height = usable_height - title_height - 0.25 * cm
    first_left = Frame(
        margin, margin, column_width, first_column_height,
        leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0,
        id="first-left",
    )
    first_right = Frame(
        margin + column_width + gap, margin, column_width, first_column_height,
        leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0,
        id="first-right",
    )
    left = Frame(
        margin, margin, column_width, usable_height,
        leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0,
        id="left",
    )
    right = Frame(
        margin + column_width + gap, margin, column_width, usable_height,
        leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0,
        id="right",
    )
    document = BaseDocTemplate(
        str(OUTPUT), pagesize=A4, leftMargin=margin, rightMargin=margin,
        topMargin=margin, bottomMargin=margin,
        title=_clean(title),
        author="; ".join(name for name, _ in AUTHORS),
        subject="Correctness-first qubit mapping and routing study",
    )
    document.addPageTemplates([
        PageTemplate(
            id="First", frames=[title_frame, first_left, first_right],
            autoNextPageTemplate="TwoColumn",
        ),
        PageTemplate(id="TwoColumn", frames=[left, right]),
    ])

    author_line_1 = ", ".join(
        f"{escape(name)}<super>{marker}</super>" for name, marker in AUTHORS[:3]
    )
    author_line_2 = ", ".join(
        f"{escape(name)}<super>{marker}</super>" for name, marker in AUTHORS[3:]
    )
    story = [
        Paragraph(escape(_clean(title)), styles["title"]),
        Paragraph(author_line_1 + "<br/>" + author_line_2, styles["authors"]),
        Paragraph(
            "atharva.sheersh2024@vitstudent.ac.in; "
            "diptesh.das2024@vitstudent.ac.in;<br/>"
            "shrivardhini.n2024@vitstudent.ac.in; "
            "haridasu.sreedhar2024@vitstudent.ac.in",
            styles["email"],
        ),
        Paragraph(
            "<super>1</super>School of Computer Science and Engineering, VIT Vellore",
            styles["affiliation"],
        ),
        Paragraph(
            "<super>2</super>Faculty Guide, School of Computer Science and Engineering, VIT Vellore",
            styles["affiliation"],
        ),
        FrameBreak(),
        Paragraph("Abstract", styles["abstract_heading"]),
        _paragraph(abstract, styles["abstract"]),
    ]

    tokens = re.split(
        r"(\\section\{[^}]+\}|\\subsection\{[^}]+\}|"
        r"\\paragraph\{[^}]+\}|\[\[RESULTS_TABLE\]\]|"
        r"\[\[LEARNING_FIGURE\]\]|\[\[EQUATION:.*?\]\])",
        body,
    )
    section_number = 0
    subsection_number = 0
    first_after_heading = False
    for token in tokens:
        token = token.strip()
        if not token:
            continue
        section_match = re.fullmatch(r"\\section\{([^}]+)\}", token)
        subsection_match = re.fullmatch(r"\\subsection\{([^}]+)\}", token)
        paragraph_match = re.fullmatch(r"\\paragraph\{([^}]+)\}", token)
        if section_match:
            section_number += 1
            subsection_number = 0
            story.append(_paragraph(
                f"{section_number} {section_match.group(1)}", styles["section"]
            ))
            first_after_heading = True
        elif subsection_match:
            subsection_number += 1
            story.append(_paragraph(
                f"{section_number}.{subsection_number} {subsection_match.group(1)}",
                styles["subsection"],
            ))
            first_after_heading = True
        elif paragraph_match:
            story.append(_paragraph(paragraph_match.group(1), styles["runin"]))
            first_after_heading = True
        elif token == "[[RESULTS_TABLE]]":
            story.append(_results_table(styles, column_width))
            first_after_heading = True
        elif token == "[[LEARNING_FIGURE]]":
            story.append(_learning_figure(styles, column_width))
            first_after_heading = True
        elif token.startswith("[[EQUATION:"):
            equation = token[len("[[EQUATION:"):-2]
            story.append(Paragraph(equation, styles["equation"]))
            first_after_heading = False
        else:
            for block in re.split(r"\n\s*\n", token):
                if _clean(block):
                    story.append(_paragraph(
                        block,
                        styles["body_first"] if first_after_heading else styles["body"],
                    ))
                    first_after_heading = False

    story.append(Paragraph("References", styles["section"]))
    for reference in REFERENCES:
        story.append(KeepTogether([
            Paragraph(escape(reference), styles["reference"])
        ]))

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    document.build(story)
    return OUTPUT


if __name__ == "__main__":
    print(build())
