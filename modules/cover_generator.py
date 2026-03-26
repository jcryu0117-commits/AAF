import os
import re
import random
from PIL import Image, ImageDraw, ImageFont


# ------------------------
# 유틸
# ------------------------

def sanitize_filename(name):
    return re.sub(r'[\\/*?:"<>|]', "", name).strip()


def wrap_text(draw, text, font, max_width):
    words = text.split()
    if not words:
        return [""]

    lines = []
    current = words[0]

    for word in words[1:]:
        test = current + " " + word
        bbox = draw.textbbox((0, 0), test, font=font)
        width = bbox[2] - bbox[0]

        if width <= max_width:
            current = test
        else:
            lines.append(current)
            current = word

    lines.append(current)
    return lines


def wrap_korean_text(draw, text, font, max_width):
    if " " in text:
        return wrap_text(draw, text, font, max_width)

    lines = []
    current = ""

    for ch in text:
        test = current + ch
        bbox = draw.textbbox((0, 0), test, font=font)
        width = bbox[2] - bbox[0]

        if width <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = ch

    if current:
        lines.append(current)

    return lines


def split_title_subtitle(title):
    if ":" in title:
        parts = title.split(":", 1)
        return parts[0].strip(), parts[1].strip()
    return title.strip(), ""


def draw_centered_multiline(draw, lines, font, fill, center_x, start_y, line_spacing):
    y = start_y
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        width = bbox[2] - bbox[0]
        x = center_x - width / 2
        draw.text((x, y), line, font=font, fill=fill)
        y += (bbox[3] - bbox[1]) + line_spacing
    return y


# ------------------------
# 메인 함수 (🔥 핵심 수정됨)
# ------------------------

def generate_cover(
    title,
    language="Korean",
    author_name="",
    publisher_name="",
    save_dir="output"   # 🔥 추가
):
    """
    지정된 폴더에 cover.png로 저장
    """

    # 🔥 저장 경로 강제
    os.makedirs(save_dir, exist_ok=True)
    file_path = os.path.join(save_dir, "cover.png")

    width, height = 1600, 2560

    # 배경
    img = Image.new("RGB", (width, height), "#ffffff")
    draw = ImageDraw.Draw(img)

    base_dir = os.path.dirname(os.path.abspath(__file__))
    font_dir = os.path.join(base_dir, "..", "Fonts")

    font_regular = os.path.join(font_dir, "malgun.ttf")
    font_bold = os.path.join(font_dir, "malgunbd.ttf")

    # 폰트 랜덤
    title_font = ImageFont.truetype(font_bold, random.randint(130, 160))
    subtitle_font = ImageFont.truetype(font_regular, 70)
    author_font = ImageFont.truetype(font_regular, 58)
    publisher_font = ImageFont.truetype(font_regular, 44)

    main_title, subtitle = split_title_subtitle(title)

    margin = 110
    top_block_y = 180
    block_h = 980

    # 비주얼 랜덤
    visual_type = random.choice(["circle", "bar", "diagonal", "pattern"])

    if visual_type == "circle":
        draw.ellipse((200, 300, 1400, 1500), fill="#e8f0ff")

    elif visual_type == "bar":
        draw.rectangle((0, 0, width, 300), fill="#1f4e79")

    elif visual_type == "diagonal":
        draw.polygon([(0, 800), (1600, 400), (1600, 1000), (0, 1400)], fill="#d9e4f5")

    elif visual_type == "pattern":
        for _ in range(10):
            x = random.randint(0, width)
            y = random.randint(0, height)
            r = random.randint(40, 120)
            draw.ellipse((x, y, x+r, y+r), fill="#f0f0f0")

    # 제목
    title_max_width = width - 2 * (margin + 60)
    title_lines = wrap_korean_text(draw, main_title, title_font, title_max_width)

    title_start_y = top_block_y + 160
    next_y = draw_centered_multiline(
        draw,
        title_lines,
        title_font,
        "#111111",
        width / 2,
        title_start_y,
        16
    )

    # 부제
    if subtitle:
        sub_lines = wrap_korean_text(draw, subtitle, subtitle_font, title_max_width)
        draw_centered_multiline(
            draw,
            sub_lines,
            subtitle_font,
            "#555555",
            width / 2,
            next_y + 40,
            10
        )

    # 저자
    if author_name.strip():
        bbox = draw.textbbox((0, 0), author_name, font=author_font)
        author_w = bbox[2] - bbox[0]
        author_x = width - margin - 30 - author_w
        author_y = top_block_y + block_h - 120
        draw.text((author_x, author_y), author_name, font=author_font, fill="#222222")

    # 출판사
    if publisher_name.strip():
        pub_bbox = draw.textbbox((0, 0), publisher_name, font=publisher_font)
        pub_w = pub_bbox[2] - pub_bbox[0]
        pub_x = (width - pub_w) / 2
        pub_y = height - 120
        draw.text((pub_x, pub_y), publisher_name, font=publisher_font, fill="#444444")

    img.save(file_path)

    return file_path