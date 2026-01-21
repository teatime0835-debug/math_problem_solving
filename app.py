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
    page_title="중학생 수학 문제 AI 튜터",
    page_icon="📘",
    layout="centered"
)

st.title("📘 중학생 수학 문제 AI 튜터")
st.info(
    "📌 이 서비스는 **교육 목적의 AI 시연**입니다.\n\n"
    "- 문제 분석 및 유사 문제는 학습용입니다.\n"
    "- 정답은 별도 버튼을 눌러 확인하세요."
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
        "1. 소인수분해": [
            "1.1 소수와 합성수", "1.2 소인수분해", "1.3 최대공약수", "1.4 최소공배수"
        ],
        "2. 정수와 유리수": [
            "2.1 정수와 유리수", "2.2 정수와 유리수의 대소 관계",
            "2.3 정수와 유리수의 덧셈", "2.4 정수와 유리수의 뺄셈",
            "2.5 정수와 유리수의 곱셈", "2.6 정수와 유리수의 나눗셈"
        ],
        "3. 문자의 사용과 식": [
            "3.1 문자의 사용", "3.2 식의 값",
            "3.3 일차식의 곱셈과 나눗셈", "3.4 일차식의 덧셈과 뺄셈",
            "3.5 일차방정식과 그 해", "3.6 일차방정식의 풀이"
        ],
        "4. 좌표평면과 그래프": [
            "4.1 순서쌍과 좌표", "4.2 그래프의 뜻과 표현",
            "4.3 정비례와 그 그래프", "4.4 반비례와 그 그래프"
        ],
        "5. 기본 도형과 작도": [
            "5.1 점, 선, 면", "5.2 각의 뜻과 성질", "5.3 위치 관계",
            "5.4 평행선의 성질", "5.5 삼각형의 작도", "5.6 삼각형의 합동"
        ],
        "6. 평면도형의 성질": [
            "6.1 다각형의 대각선의 개수", "6.2 삼각형의 내각의 크기의 합",
            "6.3 다각형의 내각의 크기의 합", "6.4 다각형의 외각의 크기의 합",
            "6.5 원과 부채꼴", "6.6 부채꼴의 중심각, 길이와 넓이"
        ],
        "7. 입체도형의 성질": [
            "7.1 다면체", "7.2 회전체", "7.3 기둥과 뿔의 겉넓이",
            "7.4 기둥과 뿔의 부피", "7.5 구의 겉넓이와 부피"
        ],
        "8. 자료의 정리와 해석": [
            "8.1 대푯값", "8.2 줄기와 잎 그림", "8.3 도수분포표",
            "8.4 히스토그램과 도수분포다각형", "8.5 상대도수", "8.6 통계 프로젝트"
        ],
    },
    "2학년": {
        "1. 유리수와 순환소수": [
            "1.1 유리수의 소수 표현", "1.2 유한소수와 순환소수", "1.3 순환소수의 분수 표현"
        ],
        "2. 식의 계산": [
            "2.1 지수법칙 (1), (2)", "2.2 지수법칙 (3), (4)",
            "2.3 단항식의 곱셈과 나눗셈", "2.4 다항식의 덧셈과 뺄셈",
            "2.5 다항식의 곱셈과 나눗셈"
        ],
        "3. 부등식과 연립방정식": [
            "3.1 부등식의 해와 성질", "3.2 일차부등식의 풀이",
            "3.3 일차부등식 문제해결", "3.4 연립일차방정식과 그 해",
            "3.5 연립방정식의 풀이", "3.6 연립방정식 문제해결"
        ],
        "4. 일차함수와 그래프": [
            "4.1 함수와 함숫값", "4.2 일차함수의 뜻과 그래프",
            "4.3 절편과 기울기", "4.4 그래프의 성질",
            "4.5 일차함수식 구하기", "4.6 일차함수와 일차방정식",
            "4.7 두 일차함수와 연립방정식"
        ],
    },
    "3학년": {
        "7. 통계": [
            "7.1 대푯값", "7.2 분산과 표준편차", "7.3 산점도와 상관관계"
        ]
    }
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
    # 1단계: 문제 분석
    # ===============================
    if st.button("🔍 문제 분석"):
        with st.spinner("문제를 분석 중입니다..."):
            analysis_prompt = """
너는 중학교 수학 교사야.
사진 속 문제를 분석해서 아래 JSON 형식으로만 출력해.

{
  "학년": "",
  "대단원": "",
  "소단원": "",
  "문제유형": ""
}

⚠️ JSON 외의 설명은 절대 쓰지 마.
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
# 분석 수정 UI
# ===============================
if "analysis" in st.session_state:
    st.markdown("## 🛠️ 문제 분석 수정")

    grade = st.selectbox("학년", list(CURRICULUM.keys()))
    big = st.selectbox("대단원", list(CURRICULUM[grade].keys()))
    small = st.selectbox("소단원", CURRICULUM[grade][big])

    if st.button("🧩 유사 문제 생성"):
        with st.spinner("유사 문제 생성 중..."):
            gen_prompt = f"""
너는 중학교 수학 문제 출제 전문가야.

📌 조건
- 학년: {grade}
- 대단원: {big}
- 소단원: {small}
- 원래 문제와 거의 동일한 유형
- 수치나 조건만 약간 변경
- 단원 이탈 금지

① 먼저 문제를 네모 박스 안에 제시
② 문제 유형 1~2개 간단히 표시
③ 정답과 풀이는 출력하지 말 것
"""

            out = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": gen_prompt}]
            )

            st.markdown("## 🧩 유사 문제")
            st.markdown(out.choices[0].message.content)

# ===============================
# Footer
# ===============================
st.markdown("---")
st.caption("© 2026 인공지능융합교육 프로젝트 | 중학생 수학 AI 튜터 (교육용)")
