import streamlit as st
from openai import OpenAI
from PIL import Image
import base64
import os
import json
import warnings

warnings.filterwarnings("ignore", category=FutureWarning)

# ===============================
# 1. 기본 설정
# ===============================
st.set_page_config(
    page_title="중학생 수학 문제 분석 & 유사문제 생성",
    page_icon="📘",
    layout="centered"
)

st.title("📘 AI 수학 문제 분석 튜터")

st.info(
    "📌 이 서비스는 **교육 목적의 AI 시연**입니다.\n\n"
    "- 문제 분석 및 유사 문제는 **교과서 기반 추정 결과**입니다.\n"
    "- 정답 제공은 학습자 요청 시에만 이루어집니다."
)

# ===============================
# 2. OpenAI API
# ===============================
API_KEY = os.getenv("OPENAI_API_KEY")
if not API_KEY:
    st.error("⚠️ OpenAI API 키가 설정되지 않았습니다.")
    st.stop()

client = OpenAI(api_key=API_KEY)

# ===============================
# 3. 이미지 업로드
# ===============================
uploaded_file = st.file_uploader(
    "📷 수학 문제 사진 업로드 (JPG, PNG)",
    type=["jpg", "jpeg", "png"]
)

if uploaded_file:
    image = Image.open(uploaded_file).convert("RGB")
    st.image(image, caption="업로드된 문제", width=450)

    # base64 인코딩
    base64_image = base64.b64encode(uploaded_file.getvalue()).decode("utf-8")

    # ===============================
    # 4. 문제 분석
    # ===============================
    if st.button("🔍 문제 분석"):
        with st.spinner("문제를 분석 중입니다..."):
            analysis_prompt = """
너는 대한민국 중학교 수학 교과서를 정확히 알고 있는 교육 전문가 AI야.

[목표]
- 사진 속 수학 문제를 보고
- 학년, 단원, 문제 유형을 **가장 적합하게 하나만** 판단해
- 절대 다른 단원이나 다른 유형으로 확장하지 마

[중요 제약]
- ‘비례’, ‘함수’처럼 포괄적인 유형 금지
- 반드시 교과서에서 실제로 사용하는 구체적 유형으로 분류할 것
- 애매하면 가장 핵심이 되는 유형 1개만 선택

[출력 형식]
아래 JSON 형식만 출력해. 설명 문장, 코드블록 금지.

{
  "grade": "중학교 ○학년",
  "unit": "단원명",
  "type": "문제 유형 (예: 정비례 관계 판별)",
  "core_concept": "사용된 핵심 개념 한 줄 요약"
}
"""

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": analysis_prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                temperature=0.2,
                max_tokens=400
            )

            raw = response.choices[0].message.content.strip()

            if not raw:
                st.error("AI가 분석 결과를 반환하지 않았습니다.")
                st.stop()

            # JSON 안전 파싱
            try:
                if raw.startswith("```"):
                    raw = raw.split("```")[1]
                analysis = json.loads(raw)
            except json.JSONDecodeError:
                st.error("문제 분석 결과를 구조화하지 못했습니다.")
                st.code(raw)
                st.stop()

            st.session_state.analysis = analysis

    # ===============================
    # 5. 분석 결과 표시 + 수정
    # ===============================
    if "analysis" in st.session_state:
        st.subheader("📌 문제 분석 결과")

        grade = st.text_input("학년", st.session_state.analysis["grade"])
        unit = st.text_input("단원", st.session_state.analysis["unit"])
        ptype = st.text_input("문제 유형", st.session_state.analysis["type"])
        concept = st.text_area("핵심 개념", st.session_state.analysis["core_concept"])

        st.session_state.analysis.update({
            "grade": grade,
            "unit": unit,
            "type": ptype,
            "core_concept": concept
        })

        # ===============================
        # 6. 유사 문제 생성
        # ===============================
        if st.button("✏️ 유사 문제 출제"):
            with st.spinner("유사 문제를 생성 중입니다..."):
                gen_prompt = f"""
너는 중학교 수학 문제 출제 전문가야.

[원문제 정보]
- 학년: {grade}
- 단원: {unit}
- 문제 유형: {ptype}
- 핵심 개념: {concept}

[출제 규칙]
- 원문제와 **수학적 관계와 구조는 동일**
- 숫자나 상황만 소폭 변경
- 절대 다른 단원·다른 유형 금지
- 방정식 풀이, 함수 접근 금지 (필요 없는 경우)

[출력]
1️⃣ 네모 상자 안에 유사 문제 제시
2️⃣ 문제 아래에 관련 유형 1~2개만 간단히 표시
"""

                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": gen_prompt}],
                    temperature=0.3,
                    max_tokens=500
                )

                st.session_state.similar_problem = response.choices[0].message.content

        if "similar_problem" in st.session_state:
            st.markdown("### 📝 유사 문제")
            st.markdown(st.session_state.similar_problem)

            if st.button("✅ 정답과 풀이 보기"):
                with st.spinner("풀이 생성 중..."):
                    sol_prompt = f"""
다음 유사 문제에 대한 풀이를 제시해라.

[규칙]
- 문제를 먼저 다시 제시
- 단계별 풀이
- 곱셈 표기 규칙:
  · 숫자×숫자 → × 사용
  · 숫자×문자, 문자×문자 → 곱셈기호 생략
- 정답은 마지막에 제시
"""

                    response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[
                            {"role": "user", "content": st.session_state.similar_problem + sol_prompt}
                        ],
                        temperature=0.2,
                        max_tokens=700
                    )

                    st.markdown("### 📘 풀이")
                    st.markdown(response.choices[0].message.content)

# ===============================
# Footer
# ===============================
st.markdown("---")
st.caption("© 2026 인공지능융합교육 프로젝트 | 중학생 수학 AI 튜터 (교육용)")
