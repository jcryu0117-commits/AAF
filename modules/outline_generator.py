from openai import OpenAI
from dotenv import load_dotenv
import re

load_dotenv()

client = OpenAI()


def generate_outline(idea, language):

    prompt = f"""
Create an ebook outline.

Topic: {idea}
Language: {language}

Requirements:
- 5 to 7 chapters
- Each chapter must have 3 to 5 subchapters
- Use STRICT numbering format

Format example:
1. Chapter Title
1.1 Subchapter Title
1.2 Subchapter Title

2. Chapter Title
2.1 Subchapter Title

Rules:
- ALWAYS include numbers (1, 1.1, 1.2 ...)
- DO NOT use "-" or bullet points
- DO NOT skip numbers
- DO NOT remove numbering
- Follow the format exactly

IMPORTANT:
- If Korean → write everything in Korean
- If English → write everything in English
"""

    response = client.responses.create(
        model="gpt-4.1-mini",
        input=prompt
    )

    raw_text = response.output_text.strip()

    # =========================
    # 🔥 핵심: 문자열 → 구조 변환
    # =========================
    lines = [line.strip() for line in raw_text.split("\n") if line.strip()]

    outline = []
    current_chapter = None

    for line in lines:

        # 대챕터 (1. )
        if re.match(r"^\d+\.\s+", line):
            current_chapter = {
                "title": line,
                "sub": []
            }
            outline.append(current_chapter)

        # 소챕터 (1.1)
        elif re.match(r"^\d+\.\d+", line):
            if current_chapter:
                current_chapter["sub"].append(line)

    return outline