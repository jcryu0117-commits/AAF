import os
import re

from modules.idea_generator import generate_ideas
from modules.outline_generator import generate_outline
from modules.chapter_generator import generate_chapter
from modules.pdf_builder import create_pdf
from modules.cover_generator import generate_cover


def run_pipeline(topic, language, author_name, publisher_name, progress_callback=None, total_tasks_callback=None):

    # 아이디어 생성
    ideas_text = generate_ideas(topic, language)

    ideas_list = ideas_text.split("\n")

    cleaned_ideas = []

    for idea in ideas_list:
        idea = idea.strip()
        if idea:
            if ". " in idea:
                idea = idea.split(". ", 1)[1]
            cleaned_ideas.append(idea)

    ideas_list = cleaned_ideas[:5]

    print("\nSelected Ideas:")
    for i, idea in enumerate(ideas_list, start=1):
        print(f"{i}. {idea}")

    # 🔥 5권 자동 생성 + resume 기능 포함
    for idx, selected_idea in enumerate(ideas_list, start=1):

        safe_title = re.sub(r'[\\/*?:"<>|]', "", selected_idea).strip()
        pdf_path_check = os.path.join("output", f"{safe_title}.pdf")

        if os.path.exists(pdf_path_check):
            print(f"Skipping (already exists): {safe_title}")
            continue

        print(f"\n===== Generating Book {idx} =====")

        outline = generate_outline(selected_idea, language)

        total_tasks = 0

        for ch in outline:
            total_tasks += 1
            total_tasks += len(ch["sub"])

        if total_tasks_callback:
            total_tasks_callback(total_tasks)

        print("\nGenerated Outline:\n")
        print(outline)

        book_title = selected_idea

        folder_path = os.path.join("output", safe_title)
        os.makedirs(folder_path, exist_ok=True)

        cover_path = generate_cover(
            book_title,
            language,
            author_name=author_name,
            publisher_name=publisher_name,
            save_dir=folder_path
        )

        chapters_data = []

        print("\nGenerating chapters...\n")

        from concurrent.futures import ThreadPoolExecutor, as_completed

        tasks = []
        task_map = {}

        with ThreadPoolExecutor(max_workers=5) as executor:

            for ch in outline:
                chapter_title = ch["title"]

                print(f"Queue: {chapter_title}")
                future = executor.submit(generate_chapter, chapter_title, selected_idea, language)
                tasks.append(future)
                task_map[future] = chapter_title

                for sub in ch["sub"]:
                    print(f"Queue: {sub}")
                    future = executor.submit(generate_chapter, sub, selected_idea, language)
                    tasks.append(future)
                    task_map[future] = sub

            results_dict = {}

            # 🔥 완료되는 순서대로 받음
            for future in as_completed(tasks):
                title = task_map[future]
                content = future.result()
                print(f"Done: {title}")
                if progress_callback:
                    progress_callback(title)
                results_dict[title] = content
                
                if progress_callback:
                    progress_callback()

        # 🔥 순서 복원
        for ch in outline:
            chapter_title = ch["title"]
            chapters_data.append((chapter_title, results_dict[chapter_title]))

            for sub in ch["sub"]:
                chapters_data.append((sub, results_dict[sub]))

        print("\nCreating PDF...\n")

        import json

        # 🔥 content.json 저장

        json_path = os.path.join(folder_path, "content.json")

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(chapters_data, f, ensure_ascii=False, indent=2)

        pdf_path = create_pdf(
            book_title,
            chapters_data,
            language,
            cover_path=cover_path,
            author_name=author_name,
            publisher_name=publisher_name,
            output_path=os.path.join(folder_path, f"{safe_title}.pdf")  # 🔥 추가
        )

        print(f"\nPDF created: {pdf_path}")

        if progress_callback:
            progress_callback(f"BOOK_DONE::{idx}::{book_title}")


# ================= CLI 실행 유지 =================

if __name__ == "__main__":

    # 언어 선택
    print("\nSelect language:")
    print("1. English")
    print("2. Korean")

    lang_choice = input("Enter number: ")

    if lang_choice == "1":
        language = "English"
    elif lang_choice == "2":
        language = "Korean"
    else:
        print("Invalid input. Defaulting to English.")
        language = "English"

    # 작가명 / 출판사
    if language == "Korean":
        print("비워두면 기본값이 적용됩니다. 내용에 표시하지 않으려면 - 를 입력하세요.")

        author_name = input("작가명을 입력하세요: ").strip()
        if author_name == "":
            author_name = "유지철"
        elif author_name == "-":
            author_name = ""

        publisher_name = input("출판사명을 입력하세요: ").strip()
        if publisher_name == "":
            publisher_name = "JC Contents LAB"
        elif publisher_name == "-":
            publisher_name = ""

    else:
        print("Leave blank for default. Enter - if you do not want it shown in the content.")

        author_name = input("Enter author name: ").strip()
        if author_name == "":
            author_name = "Ryu JiCheol"
        elif author_name == "-":
            author_name = ""

        publisher_name = input("Enter publisher name: ").strip()
        if publisher_name == "":
            publisher_name = "JC Contents LAB"
        elif publisher_name == "-":
            publisher_name = ""

    # 주제 입력
    topic = input("Enter ebook topic: ")

    # 실행
    run_pipeline(topic, language, author_name, publisher_name)