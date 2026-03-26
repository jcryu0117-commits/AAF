import streamlit as st
import json
import os
from datetime import datetime

from modules.pdf_builder import create_pdf
from modules.cover_generator import generate_cover


st.title("📚 Ebook Rebuilder")

uploaded_json = st.file_uploader("content.json 업로드", type=["json"])

new_title = st.text_input("새 제목 (비우면 기존 유지)")
new_price = st.number_input("가격 (0이면 기존 유지)", min_value=0, step=100)

language = st.selectbox("언어", ["Korean", "English"])
author_name = st.text_input("작가명 (비우면 기존 유지)")
publisher_name = st.text_input("출판사명 (비우면 기존 유지)")


if st.button("🔥 리빌드 실행"):

    # JSON 체크
    if not uploaded_json:
        st.error("content.json 업로드 필요")
        st.stop()

    # JSON 로드
    try:
        data = json.load(uploaded_json)
    except Exception as e:
        st.error(f"JSON 읽기 실패: {e}")
        st.stop()

    # 구조 대응
    if isinstance(data, dict):
        chapters = data.get("chapters", [])
        original_title = data.get("title", "")
        original_author = data.get("author", "")
        original_publisher = data.get("publisher", "")
        original_price = data.get("price", 0)
    else:
        chapters = data
        original_title = ""
        original_author = ""
        original_publisher = ""
        original_price = 0

    if not chapters:
        st.error("chapters 없음")
        st.stop()

    # 🔥 최종 값 결정
    final_title = new_title if new_title else original_title
    final_author = author_name if author_name else original_author
    final_publisher = publisher_name if publisher_name else original_publisher
    final_price = new_price if new_price > 0 else original_price

    # 제목 완전 없는 경우 방어
    if not final_title:
        final_title = "untitled"

    # UI 확인
    st.info(f"""
    📘 제목: {final_title}  
    ✍ 작가: {final_author}  
    🏢 출판사: {final_publisher}  
    💰 가격: {final_price}
    """)

    # 🔥 폴더 생성 (final_title 기준)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_title = final_title.replace("/", "").replace("\\", "")
    folder = os.path.join("output", f"{safe_title}_{timestamp}")
    os.makedirs(folder, exist_ok=True)

    # 🔥 표지 무조건 새로 생성 (핵심)
    try:
        cover_path = generate_cover(
            final_title,
            language,
            author_name=final_author,
            publisher_name=final_publisher,
            save_dir=folder
        )
    except Exception as e:
        st.error(f"표지 생성 실패: {e}")
        st.stop()

    # PDF 생성
    pdf_path = os.path.join(folder, "book.pdf")

    try:
        create_pdf(
            final_title,
            chapters,
            language,
            cover_path=cover_path,
            author_name=final_author,
            publisher_name=final_publisher,
            price=final_price,
            output_path=pdf_path
        )
    except Exception as e:
        st.error(f"PDF 생성 실패: {e}")
        st.stop()

    st.success("✅ 리빌드 완료!")

    # 다운로드
    with open(pdf_path, "rb") as f:
        st.download_button(
            "📥 PDF 다운로드",
            f,
            file_name=f"{safe_title}.pdf"
        )