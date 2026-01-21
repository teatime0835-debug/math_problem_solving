import streamlit as st
from openai import OpenAI
from PIL import Image
import base64
import os
import json

# ===============================
# Streamlit 기본 설정
# ===============================
st.set_page_config(
    page_title="중학생 수학 AI 튜터",
    page_icon="📘",
    layout="centered"
)

st.title("📘 중학생 수학 AI 튜터")
st.info(
    "📌 이 서비스는 **교육 목적의 AI 시연**입니다.\n\n"
    "- 문제 분석 및 유사 문제는 학습용입니다.\n"
    "- 정답과 풀이는 버튼을 눌러 확인하세요."
)

# ===============================
# OpenAI API
# ===============================
API_KEY = os.getenv("OPENAI_API_KEY")
if not API_KEY:
    st.error("⚠️ OpenAI API 키가 설정되지 않았습니다.")
    st.stop()

client = OpenAI(api_key=API_KEY)

# ===============================
# 중학교 1·2·3학년 단원 체계 (최종 확정본)
# ===============================
CURRICULUM = {
    "1학년": {
        "4. 좌표평면과 그래프": [
            "4.1 순서쌍과 좌표",
            "4.2 그래프의 뜻과 표현",
            "4.3 정비례와 그 그래프",
            "4.4 반비례와 그 그래프",
        ],
        "7. 입체도형의 성질": [
            "7.1 다면체",
            "7.2 회전체",
            "7.3 기둥과 뿔의 겉넓이",
            "7.4 기둥과 뿔의 부피",
            "7.5 구의 겉넓이와 부피",
        ],
    },
    "2학년": {
        "4. 일차함수와 그래프": [
            "4.1 함수와 함숫값",
            "4.2 일차함수의 뜻과 그래프",
            "4.3 절편과 기울기",
            "4.4 그래프의 성질",
            "4.5 일차함수식 구하기",
            "4.6 일차함수와 일차방정식",
            "4.7 두 일차함수와 연립일차방정식",
        ],
    },
    "3학년": {
        "7. 통계": [
            "7.1 대푯값",
            "7.2 분산과 표준편차",
            "7.3 산점도와 상관관계",
        ],
    },
}

# ===============================
# 이미지 업로드
# ===============================
uploaded_file = st.file_uploader("📷 문제 사진 업로드", type=["jpg", "jpeg", "png"])

if uploaded_file:
    image = Image.open(uploaded_file).convert("RGB")
    st.image(image, caption="업로드된 문제", use_container_width=True)

    base64_img = base64.b64encode(uploaded_file.getvalue()).decode()

    # ===============================
    # 1️⃣ 문제 분석
    # ===============================
    if st.button("🔍 문제 분석"):
        with st.spinner("문제를 분석 중입니다..."):
            analysis_prompt = """
너는 대한민국 중학교 수학 교사야.

아래 중학교 수학 단원 체계 안에서만 선택해서
사진 속 문제를 가장 정확하게 분류해.

📌 판단 기준
1. 문제 해결에 반드시 필요한 핵심 개념
2. 대표적인 단원 고유 문제 유형
3. 애매하면 가장 직접적으로 사용된 개념 기준

📌 출력 형식 (JSON만!)
{
  "학년": "",
  "대단원": "",
  "소단원": "",
  "문제유형": ""
}
"""

            res = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": analysis_prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_img}"}}
                    ]
                }]
            )

            try:
                st.session_state.analysis = json.loads(
                    res.choices[0].message.content.strip()
                )
            except:
                st.error("❌ 문제 분석에 실패했습니다. 다시 시도해 주세요.")
                st.stop()

# ===============================
# 분석 결과 수정 UI
# ===============================
if "analysis" in st.session_state:
    st.markdown("## 🛠️ 문제 분석 결과")

    grade = st.selectbox(
        "학년",
        CURRICULUM.keys(),
        index=list(CURRICULUM.keys()).index(
            st.session_state.analysis.get("학년", "1학년")
        )
    )

    big_unit = st.selectbox(
        "대단원",
        CURRICULUM[grade].keys()
    )

    small_unit = st.selectbox(
        "소단원",
        CURRICULUM[grade][big_unit]
    )

    problem_type = st.text_input(
        "문제 유형",
        st.session_state.analysis.get("문제유형", "")
    )

    # ===============================
    # 2️⃣ 유사 문제 생성
    # ===============================
    if st.button("🧩 유사 문제 생성"):
        with st.spinner("유사 문제를 생성 중입니다..."):
            gen_prompt = f"""
너는 중학교 수학 문제 출제 전문가야.

📌 조건
- 학년: {grade}
- 대단원: {big_unit}
- 소단원: {small_unit}
- 문제 유형: {problem_type}

📌 출제 규칙
- 원래 문제와 거의 동일한 유형
- 숫자나 조건만 약간 변경
- 단원 이탈 절대 금지

📌 출력 형식
1. 네모 박스 안에 문제 제시
2. 문제 아래에 문제 유형 1~2개만 간단히 표시
3. 정답과 풀이는 쓰지 말 것
"""

            out = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": gen_prompt}]
            )

            st.session_state.similar_problem = out.choices[0].message.content
            st.session_state.show_answer = False
            st.session_state.show_solution = False

# ===============================
# 유사 문제 출력
# ===============================
if "similar_problem" in st.session_state:
    st.markdown("## 🧩 유사 문제")
    st.markdown(st.session_state.similar_problem)

    col1, col2 = st.columns(2)

    with col1:
        if st.button("✅ 정답 보기"):
            st.session_state.show_answer = True

    with col2:
        if st.button("📘 풀이 보기"):
            st.session_state.show_solution = True

# ===============================
# 정답 / 풀이
# ===============================
if st.session_state.get("show_answer") or st.session_state.get("show_solution"):
    solve_prompt = f"""
너는 중학교 수학 교사야.

아래 [유사 문제]에 대해
- 정답
- 풀이 과정

을 작성해.

📌 규칙
- 숫자×숫자 → 반드시 × 사용
- 숫자×문자, 문자×문자 → 곱셈기호 생략
- 단계별로 간결하고 친절하게 설명

[유사 문제]
{st.session_state.similar_problem}
"""

    sol = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": solve_prompt}]
    )

    if st.session_state.get("show_answer"):
        st.markdown("### ✅ 정답")
        st.markdown(sol.choices[0].message.content.split("풀이")[0])

    if st.session_state.get("show_solution"):
        st.markdown("### 📘 풀이")
        st.markdown(sol.choices[0].message.content)

# ===============================
# Footer
# ===============================
st.markdown("---")
st.caption("© 2026 인공지능융합교육 프로젝트 | 중학생 수학 AI 튜터 (교육용)")
