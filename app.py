import zipfile
import io
import streamlit as st
import os
from main import run_pipeline

def make_zip_multi(folders):
    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for folder in folders:
            for root, dirs, files in os.walk(folder):
                for file in files:
                    file_path = os.path.join(root, file)

                    arcname = os.path.join(
                        os.path.basename(folder),
                        os.path.relpath(file_path, folder)
                    )

                    zf.write(file_path, arcname)

    zip_buffer.seek(0)
    return zip_buffer

st.set_page_config(page_title="AI Ebook Factory", layout="centered")

st.title("📚 AI 전자책 자동 생성기")

# ------------------------
# 🔥 실행 상태 플래그 (핵심)
# ------------------------
if "running" not in st.session_state:
    st.session_state.running = False

# ------------------------
# 입력 UI
# ------------------------
topic = st.text_input("📌 주제 입력", placeholder="예: AI로 돈 버는 방법")

language = st.selectbox(
    "🌐 언어 선택",
    ["Korean", "English"]
)

author = st.text_input("✍️ 작가명 (비우면 기본값)")
publisher = st.text_input("🏢 출판사명 (비우면 기본값)")

# 🔥 영역 분리
generate_area = st.container()
result_area = st.container()

# ------------------------
# 생성 영역
# ------------------------
with generate_area:

    if st.button("🚀 전자책 생성 시작") and not st.session_state.running:

        if not topic.strip():
            st.warning("주제를 입력하세요.")
        else:
            # 🔥 실행 시작
            st.session_state.running = True

            if language == "Korean":
                author_name = "유지철" if author.strip() == "" else ("" if author.strip() == "-" else author)
                publisher_name = "JC Contents LAB" if publisher.strip() == "" else ("" if publisher.strip() == "-" else publisher)
            else:
                author_name = "Ryu JiCheol" if author.strip() == "" else ("" if author.strip() == "-" else author)
                publisher_name = "JC Contents LAB" if publisher.strip() == "" else ("" if publisher.strip() == "-" else publisher)

            status_text = st.empty()

            try:
                with st.spinner("📚 전자책 생성 중... (몇 분 소요될 수 있음)"):

                    status_text.text("✍️ 전자책 생성 시작...")

                    log_box = st.empty()
                    logs = []

                    def update_progress(msg=None):
                        if not msg:
                            return

                        if msg.startswith("BOOK_DONE::"):
                            _, idx, title = msg.split("::")
                            logs.append(f"📘 {idx}번 책 완료: {title}")
                            status_text.text(f"📘 {idx}번 책 완료")

                        log_box.text("\n".join(logs[-10:]))

                    folders = run_pipeline(
                        topic,
                        language,
                        author_name,
                        publisher_name,
                        progress_callback=update_progress
                    )

                    zip_data = make_zip_multi(folders)

                status_text.text("완료!")
                st.success("✅ 전자책 생성 완료!")

                st.download_button(
                    label="📦 전체 전자책 다운로드 (ZIP)",
                    data=zip_data,
                    file_name="ebooks_package.zip",
                    mime="application/zip"
                )

            finally:
                # 🔥 무조건 해제 (에러 나도 풀림)
                st.session_state.running = False

# ------------------------
# 결과 영역
# ------------------------
with result_area:

    st.divider()
    st.subheader("📂 생성된 전자책")

    output_dir = "output"

    if not os.path.exists(output_dir):
        st.info("아직 생성된 전자책이 없습니다.")
    else:
        pdf_files = []

        # 🔥 하위 폴더까지 모두 탐색
        for root, dirs, files in os.walk(output_dir):
            for file in files:
                if file.endswith(".pdf"):
                    pdf_files.append(os.path.join(root, file))

        if not pdf_files:
            st.info("아직 생성된 전자책이 없습니다.")
        else:
            pdf_files.sort(reverse=True)

            for file_path in pdf_files:

                filename = os.path.basename(file_path)

                col1, col2 = st.columns([3, 1])

                with col1:
                    st.write(f"📘 {filename}")

                with col2:
                    with open(file_path, "rb") as f:
                        st.download_button(
                            label="다운로드",
                            data=f,
                            file_name=filename,
                            mime="application/pdf",
                            key=file_path
                        )