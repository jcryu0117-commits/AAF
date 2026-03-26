from modules.cover_generator import generate_cover
from modules.pdf_builder import create_pdf


# =========================
# 테스트 설정
# =========================
title = "전자책 제작 A to Z: 실전 편집 및 디자인 노하우"
language = "Korean"


# =========================
# 1. 표지 생성 (0원)
# =========================
print("=== COVER TEST ===")
cover_path = generate_cover(title, language)
print("Cover created:", cover_path)


# =========================
# 2. 고정 데이터 (핵심)
# =========================
chapters_data = [
    ("1. 전자출판의 개념과 역사", ""),
    ("1.1 전자출판의 정의", "전자출판은 디지털 형태로 제작되는 출판 콘텐츠를 의미한다."),
    ("1.2 전자출판의 발전 과정", "인터넷과 모바일의 발전으로 전자출판은 빠르게 성장하였다."),

    ("2. 플랫폼과 시장 구조", ""),
    ("2.1 주요 전자출판 플랫폼", "아마존 킨들, 리디북스, 유페이퍼 등이 대표적이다."),
    ("2.2 전통 출판과 비교", "전자출판은 제작 비용이 낮고 접근성이 높다."),
]


# =========================
# 3. PDF 생성
# =========================
print("\n=== PDF TEST ===")
pdf_path = create_pdf(title, chapters_data, language, cover_path)

print("PDF created:", pdf_path)