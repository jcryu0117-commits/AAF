import os
import re
from datetime import datetime

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    PageBreak,
    Image,
    Table,
    TableStyle,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A5
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas as pdfcanvas


def register_fonts():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    font_dir = os.path.join(base_dir, "..", "Fonts")

    try:
        pdfmetrics.getFont("Malgun")
    except KeyError:
        pdfmetrics.registerFont(
            TTFont("Malgun", os.path.join(font_dir, "malgun.ttf"))
        )

    try:
        pdfmetrics.getFont("Malgun-Bold")
    except KeyError:
        bold_path = os.path.join(font_dir, "malgunbd.ttf")
        if os.path.exists(bold_path):
            pdfmetrics.registerFont(
                TTFont("Malgun-Bold", bold_path)
            )


def sanitize_filename(name):
    return re.sub(r'[\\/*?:"<>|]', "", name)


def get_unique_filename(path):
    if not os.path.exists(path):
        return path

    base, ext = os.path.splitext(path)
    i = 1
    while True:
        new_path = f"{base}_{i}{ext}"
        if not os.path.exists(new_path):
            return new_path
        i += 1


def clean_chapter_text(text, chapter_title):
    lines = text.split("\n")
    cleaned = []
    skipped_first_matching_title = False

    normalized_title = re.sub(r"\s+", " ", chapter_title.strip()).lower()
    normalized_title_no_num = re.sub(r"^\d+(\.\d+)*\.?\s*", "", normalized_title).strip()

    for line in lines:
        raw_line = line.strip()
        if not raw_line:
            continue

        raw_line = re.sub(r"^#+\s*", "", raw_line)
        raw_line = re.sub(r"\*\*(.*?)\*\*", r"\1", raw_line)

        normalized_line = re.sub(r"\s+", " ", raw_line).lower()
        normalized_line_no_num = re.sub(r"^\d+(\.\d+)*\.?\s*", "", normalized_line).strip()

        if not skipped_first_matching_title:
            if normalized_line == normalized_title or normalized_line_no_num == normalized_title_no_num:
                skipped_first_matching_title = True
                continue

        cleaned.append(raw_line)

    return "\n".join(cleaned)


def generate_copyright_page(title, author_name, publisher_name, price=2000):
    today = datetime.today().strftime("%Y년 %m월 %d일")
    year = datetime.today().year

    return [
        ("title", title),
        ("space", 18),
        ("line", f"지은이 {author_name}"),
        ("line", f"발행일 {today}"),
        ("line", f"전자책 정가 {price}원"),
        ("line", f"발행처 {publisher_name}"),
        ("space", 16),
        ("line", "[저작권 정보]"),
        ("line", "본 전자책은 저작권법에 의해 보호를 받는 저작물이므로"),
        ("line", "무단전재 및 무단복제를 금지합니다."),
        ("line", f"Copyright ⓒ {author_name} {year}"),
    ]


class NumberedCanvas(pdfcanvas.Canvas):
    def __init__(self, *args, **kwargs):
        self._chapter_page_map = kwargs.pop("chapter_page_map", {})
        self._page_states = []
        super().__init__(*args, **kwargs)

    def showPage(self):
        self._page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        for state in self._page_states:
            self.__dict__.update(state)
            super().showPage()
        super().save()

    def draw_chapter_marker(self, chapter_title):
        self._chapter_page_map[chapter_title] = self._pageNumber


def create_pdf(title, chapters_data, language, cover_path=None, author_name="유지철", publisher_name="유페이퍼", price=5000, output_path=None):
    os.makedirs("output", exist_ok=True)
    register_fonts()

    safe_title = sanitize_filename(title)

    #cover_output_path = cover_path if cover_path and os.path.exists(cover_path) else None

    if output_path:
        dir_name = os.path.dirname(output_path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
        file_path = output_path
    else:
        base_path = os.path.join("output", f"{safe_title}.pdf")
        file_path = get_unique_filename(base_path)

    styles = getSampleStyleSheet()

    for style_name in styles.byName:
        styles[style_name].fontName = "Malgun"

    bold_font = "Malgun-Bold"
    try:
        pdfmetrics.getFont("Malgun-Bold")
    except KeyError:
        bold_font = "Malgun"

    styles["Heading1"].fontName = bold_font
    styles["Heading1"].fontSize = 14
    styles["Heading1"].leading = 18
    styles["Heading1"].spaceAfter = 10

    styles["Heading2"].fontName = bold_font
    styles["Heading2"].fontSize = 12
    styles["Heading2"].leading = 16
    styles["Heading2"].spaceAfter = 8

    styles["BodyText"].fontName = "Malgun"
    styles["BodyText"].fontSize = 10
    styles["BodyText"].leading = 16

    styles["Normal"].fontName = "Malgun"
    styles["Normal"].fontSize = 10
    styles["Normal"].leading = 16

    copyright_title_style = ParagraphStyle(
        name="CopyrightTitle",
        parent=styles["Heading1"],
        fontName=bold_font,
        fontSize=16,
        leading=22,
        alignment=TA_CENTER,
        spaceAfter=0,
    )

    toc_title_style = ParagraphStyle(
        name="TOCTitle",
        parent=styles["Heading1"],
        fontName=bold_font,
        fontSize=16,
        leading=22,
        alignment=TA_CENTER,
        spaceAfter=16,
    )

    toc_main_item_style = ParagraphStyle(
        name="TOCMainItem",
        parent=styles["Normal"],
        fontName=bold_font,
        fontSize=10,
        leading=16,
        alignment=TA_LEFT,
    )

    toc_sub_item_style = ParagraphStyle(
        name="TOCSubItem",
        parent=styles["Normal"],
        fontName="Malgun",
        fontSize=9,
        leading=14,
        alignment=TA_LEFT,
        leftIndent=12,
    )

    toc_page_style = ParagraphStyle(
        name="TOCPage",
        parent=styles["Normal"],
        fontName="Malgun",
        fontSize=10,
        leading=16,
        alignment=TA_RIGHT,
    )

    toc_entries = []
    seen_titles = set()

    for chapter_title, _chapter_text in chapters_data:
        if not isinstance(chapter_title, str):
            chapter_title = str(chapter_title)

        chapter_title = chapter_title.strip()
        if not chapter_title or chapter_title in seen_titles:
            continue
        seen_titles.add(chapter_title)

        is_subchapter = bool(re.match(r"^\d+\.\d+", chapter_title))
        toc_entries.append((chapter_title, is_subchapter))

    # active_doc을 리스트로 감싸서 클로저 안에서 교체 가능하게 함
    # (after_flowable이 항상 현재 빌드 중인 doc.canv를 참조해야 함)
    active_doc = [None]

    def make_doc(path, with_meta=True):
        kwargs = dict(
            pagesize=A5,
            leftMargin=32,
            rightMargin=32,
            topMargin=36,
            bottomMargin=36,
        )
        if with_meta:
            kwargs.update(
                title=title,
                author=author_name,
                subject=title,
                creator="AI Ebook Auto Factory",
            )
        return SimpleDocTemplate(path, **kwargs)

    def build_toc_story(page_map):
        toc_story = [Paragraph("목차", toc_title_style)]

        toc_rows = []
        for chapter_title, is_subchapter in toc_entries:
            page_num = page_map.get(chapter_title, "")
            item_style = toc_sub_item_style if is_subchapter else toc_main_item_style

            toc_rows.append([
                Paragraph(chapter_title, item_style),
                Paragraph(str(page_num), toc_page_style),
            ])

        if toc_rows:
            # colWidths를 고정값으로 지정해서 page_map 내용물과 무관하게
            # 목차 렌더링 높이(=페이지 수)가 항상 동일하게 유지됨
            toc_table = Table(
                toc_rows,
                colWidths=[283, 40],
                hAlign="LEFT",
                repeatRows=0,
            )
            toc_table.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                ("LINEBELOW", (0, 0), (-1, -1), 0.2, colors.lightgrey),
            ]))
            toc_story.append(toc_table)

        return toc_story

    def build_story(include_toc, page_map):
        story = []

        if cover_path and os.path.exists(cover_path):
            cur_doc = active_doc[0]
            usable_width = cur_doc.width * 0.95
            usable_height = cur_doc.height * 0.95

            img = Image(cover_path)
            ratio = min(usable_width / img.imageWidth, usable_height / img.imageHeight)
            img.drawWidth = img.imageWidth * ratio
            img.drawHeight = img.imageHeight * ratio
            img.hAlign = "CENTER"

            story.append(img)
            story.append(PageBreak())

        if language == "Korean":
            for item_type, value in generate_copyright_page(title, author_name, publisher_name,price):
                if item_type == "title":
                    story.append(Paragraph(value, copyright_title_style))
                elif item_type == "line":
                    story.append(Paragraph(value, styles["Normal"]))
                    story.append(Spacer(1, 8))
                elif item_type == "space":
                    story.append(Spacer(1, value))

            story.append(PageBreak())

        if include_toc and toc_entries:
            story.extend(build_toc_story(page_map))
            story.append(PageBreak())

        seen_body_titles = set()
        first_main_chapter = True

        for chapter_title, chapter_text in chapters_data:
            if not isinstance(chapter_title, str):
                chapter_title = str(chapter_title)
            if not isinstance(chapter_text, str):
                chapter_text = str(chapter_text)

            chapter_title = chapter_title.strip()
            if not chapter_title:
                continue

            if chapter_title in seen_body_titles:
                continue
            seen_body_titles.add(chapter_title)

            is_subchapter = bool(re.match(r"^\d+\.\d+", chapter_title))

            if not is_subchapter:
                if not first_main_chapter:
                    story.append(PageBreak())
                first_main_chapter = False

                marker = Paragraph(chapter_title, styles["Heading1"])
                marker._chapter_title = chapter_title
                story.append(marker)
                story.append(Spacer(1, 10))
            else:
                marker = Paragraph(chapter_title, styles["Heading2"])
                marker._chapter_title = chapter_title
                story.append(marker)
                story.append(Spacer(1, 8))

            clean_text = clean_chapter_text(chapter_text, chapter_title)

            for para in clean_text.split("\n"):
                para = para.strip()
                if para:
                    story.append(Paragraph(para, styles["BodyText"]))
                    story.append(Spacer(1, 6))

        return story

    def set_pdf_meta(canvas_obj, doc_obj):
        canvas_obj.setTitle(title)
        canvas_obj.setAuthor(author_name)
        canvas_obj.setSubject(title)
        canvas_obj.setCreator("AI Ebook Auto Factory")

    def after_flowable(flowable):
        if hasattr(flowable, "_chapter_title"):
            # active_doc[0]을 통해 현재 빌드 중인 doc을 참조
            active_doc[0].canv.draw_chapter_marker(flowable._chapter_title)

    # ────────────────────────────────────────────────
    # PASS 1: 목차 없이 빌드 → 각 챕터 시작 페이지 수집
    # ────────────────────────────────────────────────
    chapter_page_map = {}
    d1 = make_doc(file_path)
    d1.afterFlowable = after_flowable
    active_doc[0] = d1

    d1.build(
        build_story(include_toc=False, page_map={}),
        onFirstPage=set_pdf_meta,
        onLaterPages=set_pdf_meta,
        canvasmaker=lambda *args, **kwargs: NumberedCanvas(
            *args, chapter_page_map=chapter_page_map, **kwargs
        ),
    )

    # ────────────────────────────────────────────────
    # 목차 페이지 수 계산 (1회 고정)
    # 핵심: 실제 페이지 번호가 채워진 상태로 렌더링해야
    #       행 높이가 최종 빌드와 완전히 동일해짐
    # ────────────────────────────────────────────────
    toc_pages = 0
    if toc_entries:
        toc_counter = {"n": 0}

        def _count(canvas_obj, doc_obj):
            toc_counter["n"] += 1

        tmp = make_doc(file_path, with_meta=False)
        tmp.build(
            build_toc_story(chapter_page_map),  # 실제 번호로 렌더링
            onFirstPage=_count,
            onLaterPages=_count,
        )
        toc_pages = toc_counter["n"]

        # 수집된 페이지 번호에 목차 페이지 수를 1회만 반영
        # 🔥 수정됨 (KeyError 방지)
        for k in list(chapter_page_map.keys()):
            chapter_page_map[k] = chapter_page_map.get(k, 0) + toc_pages

    # ────────────────────────────────────────────────
    # PASS 2 (최종): 목차 포함, 보정된 페이지 번호 사용
    # ────────────────────────────────────────────────
    d2 = make_doc(file_path)
    d2.afterFlowable = after_flowable
    active_doc[0] = d2

    d2.build(
        build_story(include_toc=True, page_map=chapter_page_map),
        onFirstPage=set_pdf_meta,
        onLaterPages=set_pdf_meta,
        canvasmaker=lambda *args, **kwargs: NumberedCanvas(
            *args, chapter_page_map={}, **kwargs
        ),
    )

    return file_path
