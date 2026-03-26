import os
import json
from datetime import datetime

from modules.pdf_builder import create_pdf
from modules.cover_generator import generate_cover


# ------------------------
# 유틸
# ------------------------

def load_json_safe(path):
    if not os.path.exists(path):
        print("❌ content.json 없음")
        return None

    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ JSON 로드 실패: {e}")
        return None


def sanitize_filename(name):
    invalid_chars = ['\\', '/', ':', '*', '?', '"', '<', '>', '|']
    for ch in invalid_chars:
        name = name.replace(ch, "")
    return name.strip()


def make_unique_folder(base_title):
    safe_title = sanitize_filename(base_title)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    folder_name = f"{safe_title}_{timestamp}"
    folder_path = os.path.join("output", folder_name)

    os.makedirs(folder_path, exist_ok=True)
    return folder_path


def normalize_chapters(data):
    """
    content.json 구조 대응:
    - list 형태
    - dict 안에 chapters 키
    """
    if isinstance(data, list):
        return data

    if isinstance(data, dict):
        if "chapters" in data:
            return data["chapters"]

    print("❌ content.json 구조 이상 (chapters 없음)")
    return None


# ------------------------
# 메인 로직
# ------------------------

def rebuild_book(
    folder_path,
    new_title,
    new_price,
    language,
    author_name,
    publisher_name,
    use_existing_cover=False
):
    print("\n📦 리빌드 시작...")

    # 1. JSON 로드
    json_path = os.path.join(folder_path, "content.json")
    raw_data = load_json_safe(json_path)
    if raw_data is None:
        return

    chapters_data = normalize_chapters(raw_data)
    if not chapters_data:
        return

    # 2. 새 폴더 생성
    new_folder = make_unique_folder(new_title)

    # 3. 표지 처리
    cover_path = None

    if use_existing_cover:
        possible_cover = os.path.join(folder_path, "cover.png")
        if os.path.exists(possible_cover):
            cover_path = possible_cover
            print("📌 기존 표지 재사용")
        else:
            print("⚠ 기존 표지 없음 → 새 표지 생성")
    
    if not cover_path:
        try:
            cover_path = generate_cover(
                new_title,
                language,
                author_name=author_name,
                publisher_name=publisher_name,
                save_dir=new_folder  # 중요
            )
        except Exception as e:
            print(f"❌ 표지 생성 실패: {e}")
            return

    # 4. PDF 생성
    pdf_output_path = os.path.join(new_folder, "book.pdf")

    try:
        pdf_path = create_pdf(
            new_title,
            chapters_data,
            language,
            cover_path=cover_path,
            author_name=author_name,
            publisher_name=publisher_name,
            price=new_price,
            output_path=pdf_output_path
        )
    except Exception as e:
        print(f"❌ PDF 생성 실패: {e}")
        return

    # 5. 메타 포함 JSON 저장
    rebuilt_data = {
        "title": new_title,
        "price": new_price,
        "author": author_name,
        "publisher": publisher_name,
        "language": language,
        "chapters": chapters_data,
        "rebuilt_at": datetime.now().isoformat()
    }

    try:
        with open(os.path.join(new_folder, "content.json"), "w", encoding="utf-8") as f:
            json.dump(rebuilt_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"❌ JSON 저장 실패: {e}")
        return

    print(f"\n✅ 리빌드 완료!")
    print(f"📘 제목: {new_title}")
    print(f"💰 가격: {new_price}")
    print(f"📁 경로: {pdf_path}")


# ------------------------
# CLI 실행
# ------------------------

if __name__ == "__main__":

    print("=== 📚 Ebook Rebuilder ===")

    folder = input("기존 책 폴더 경로: ").strip()
    new_title = input("새 제목: ").strip()

    try:
        new_price = int(input("새 가격 (숫자만): ").strip())
    except:
        print("❌ 가격 입력 오류")
        exit()

    language = input("언어 (Korean/English): ").strip()
    author_name = input("작가명: ").strip()
    publisher_name = input("출판사명: ").strip()

    reuse = input("기존 표지 재사용? (y/n): ").strip().lower()
    use_existing_cover = True if reuse == "y" else False

    rebuild_book(
        folder,
        new_title,
        new_price,
        language,
        author_name,
        publisher_name,
        use_existing_cover=use_existing_cover
    )