from openai import OpenAI
from dotenv import load_dotenv
import re
import time

load_dotenv()

client = OpenAI()


def _clean_generated_text(text, chapter_title):
    if not text:
        return ""

    text = text.replace("\r\n", "\n").replace("\r", "\n").strip()

    lines = [line.strip() for line in text.split("\n")]
    cleaned_lines = []
    normalized_title = re.sub(r"\s+", " ", chapter_title.strip()).lower()

    skipped_title_once = False

    for line in lines:
        if not line:
            continue

        line = re.sub(r"^#+\s*", "", line)
        line = re.sub(r"^\d+(\.\d+)*\.?\s*", "", line).strip()
        line = re.sub(r"\*\*(.*?)\*\*", r"\1", line).strip()

        normalized_line = re.sub(r"\s+", " ", line).lower()

        if not skipped_title_once and normalized_line == normalized_title:
            skipped_title_once = True
            continue

        cleaned_lines.append(line)

    return "\n".join(cleaned_lines).strip()


def _is_text_too_short(text, min_chars=800):
    plain = re.sub(r"\s+", "", text)
    return len(plain) < min_chars


def _is_title_only_text(text, chapter_title):
    plain_text = re.sub(r"\s+", "", text).lower()
    plain_title = re.sub(r"\s+", "", chapter_title).lower()

    if not plain_text:
        return True

    return plain_text == plain_title


def generate_chapter(chapter_title, topic, language, max_retry=3):

    prompt = f"""
Write one ebook chapter.

Book topic: {topic}
Chapter title: {chapter_title}
Language: {language}

Requirements:
- around 900 words
- practical and easy to read
- no markdown (#, ##, ###)
- no numbering like 1.1, 2.3
- no "Chapter 1" repetition
- no meta phrases like "Here is", "Certainly"
- write naturally like a real ebook

Style improvements:
- mix short and long sentences naturally
- avoid repeating patterns like "~것이다", "~중요하다"
- vary sentence endings and tone
- include occasional conversational flow (but still professional)
- avoid overly formal textbook tone

IMPORTANT:
- If language is Korean, write everything in Korean
- If language is English, write everything in English
"""

    for attempt in range(max_retry):
        try:
            response = client.responses.create(
                model="gpt-4.1-mini",
                input=prompt
            )

            text = _clean_generated_text(response.output_text, chapter_title)

            # 🔥 기존 검증 로직 유지
            if _is_title_only_text(text, chapter_title):
                raise ValueError(f"제목만 생성됨: {chapter_title}")

            if _is_text_too_short(text):
                raise ValueError(f"분량 부족: {chapter_title}")

            return text

        except Exception as e:
            print(f"[Retry {attempt+1}/{max_retry}] {chapter_title} → {e}")

            if attempt == max_retry - 1:
                print(f"❌ 최종 실패 → fallback 사용: {chapter_title}")

                if language == "Korean":
                    return f"{chapter_title}\n\n내용 생성에 실패했습니다. 다시 시도해주세요."
                else:
                    return f"{chapter_title}\n\nFailed to generate content. Please retry."

            time.sleep(2 * (attempt + 1))