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
    "- 문제 분석 및 유사 문제는 **학습용**입니다.\n"
    "- 실제 시험 문제와 다를 수 있습니다."
)

# ===============================
# OpenAI API 설정
# ===============================
API_KEY = os.getenv("OPENAI_API_KEY")
if not API_KEY:
    st.error("⚠️ OpenAI API 키가 설정되지 않았습니다.")
    st.stop()

client = OpenAI(api_key=API_KEY)

# ===============================
# 중학교 단원 데이터
# ===============================
CURRICULUM = {
    "중1": {
        "소인수분해": ["소수와 합성수", "소인수분해", "최대공약수", "최소공배수"],
        "정수와 유리수": ["정수와 유리수", "대소 관계", "덧셈", "뺄셈", "곱셈", "나눗셈"],
        "문자의 사용과 식": ["문자의 사용", "식의 값", "일차식의 계산"],
        "좌표평면과 그래프": ["순서쌍", "그래프의 뜻과 표현"],
    },
    "중2": {
        "유리수와 순환소수": ["유한소수", "순환소수"],
        "식의 계산": ["지수법칙", "다항식의 덧셈과 뺄셈"],
        "일차함수와 그래프": ["일차함수의 뜻", "그래프", "기울기"],
        "삼각형의 성질": ["삼각형의 외심", "내심"],
    },
    "중3": {
        "이차방정식": ["이차방정식의 풀이", "근의 공식"],
        "이차함수와 그래프": ["y=ax²", "y=a(x-p)²"],
        "삼각비": ["sin, cos, tan", "삼각비의 활용"],
        "통계": ["대푯값", "산포도"],
    }
}

# ===============================
# 이미지 업로드
# ===============================
uploaded = st.file_uploader(
    "📷 문제 이미지를 업로드하세요 (JPG, PNG)",
    type=["jpg", "jpeg", "png"]
)

if uploaded:
    image = Image.open(uploaded).convert("RGB")
    st.image(image, caption="업로드된 문제", width=400)

    base64_image = base64.b64encode(uploaded.getvalue()).decode()

    # ===============================
    # 1단계: 문제 분석
    # ===============================
    if st.button("🔍 문제 분석"):
        with st.spinner("문제를 분석 중입니다..."):
            prompt = """
너는 대한민국 중학교 수학 교과 과정을 정확히 알고 있는 AI 교사야.

주어진 문제 이미지를 보고 다음 정보를 JSON 형식으로만 출력해.

{
  "grade": "중1/중2/중3",
  "major": "대단원명",
  "minor": "소단원명",
  "type": "구체적인 문제 유형 (예: 정비례 관계인지 판단하기)"
}

⚠️ 반드시 실제 교과 단원 체계에 맞게 가장 적합한 것으로 판단해.
"""
            res = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url",
                         "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                    ]
                }],
                temperature=0.1
            )

            try:
                st.session_state.analysis = json.loads(
                    res.choices[0].message.content
                )
            except:
                st.error("❗ 문제 분석에 실패했습니다.")
                st.stop()

    # ===============================
    # 2단계: 분석 결과 수정
    # ===============================
    if "analysis" in st.session_state:
        st.markdown("## ✏️ 문제 분석 결과 (수정 가능)")

        grade = st.selectbox(
            "학년",
            list(CURRICULUM.keys()),
            index=list(CURRICULUM.keys()).index(
                st.session_state.analysis["grade"])
        )

        major = st.selectbox(
            "대단원",
            list(CURRICULUM[grade].keys())
        )

        minor = st.selectbox(
            "소단원",
            CURRICULUM[grade][major]
        )

        problem_type = st.text_input(
            "문제 유형 (간단히)",
            st.session_state.analysis["type"]
        )

        # ===============================
        # 3단계: 유사 문제 출제
        # ===============================
        if st.button("🧩 유사 문제 출제"):
            with st.spinner("유사 문제를 생성 중입니다..."):
                sim_prompt = f"""
다음 조건을 반드시 지켜 유사 문제를 만들어라.

- 학년: {grade}
- 대단원: {major}
- 소단원: {minor}
- 문제 유형: {problem_type}

⚠️ 원 문제와 **동일한 개념·유형**을 유지하되,
수나 조건만 살짝 바꾼 문제를 1문제만 출제하라.
⚠️ 문제만 출력하라. 풀이 금지.
"""

                out = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": sim_prompt}],
                    temperature=0.3
                )

                st.session_state.similar = out.choices[0].message.content

    # ===============================
    # 유사 문제 표시 (항상 유지)
    # ===============================
    if "similar" in st.session_state:
        st.markdown("## 🧩 유사 문제")
        st.markdown(
            f"""
<div style="border:2px solid #999;padding:15px;border-radius:8px">
{st.session_state.similar}
</div>
""",
            unsafe_allow_html=True
        )

        st.caption(f"문제 유형: {problem_type}")

        # ===============================
        # 4단계: 정답 및 풀이
        # ===============================
        if st.button("✅ 정답 및 풀이 보기"):
            with st.spinner("풀이를 생성 중입니다..."):
                solve_prompt = f"""
다음 유사 문제의 풀이를 단계별로 설명하라.

규칙:
- 숫자×숫자 → × 사용
- 숫자·문자 / 문자·문자 → 곱셈기호 생략
- 중학생 눈높이 설명
"""
                sol = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "user", "content": st.session_state.similar},
                        {"role": "user", "content": solve_prompt}
                    ],
                    temperature=0.2
                )

                st.markdown("### 📘 풀이")
                st.markdown(sol.choices[0].message.content)

# ===============================
# Footer
# ===============================
st.markdown("---")
st.caption("© 2026 인공지능융합교육 프로젝트 | 중학생 수학 AI 튜터 (교육용)")
