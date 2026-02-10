import streamlit as st
import FinanceDataReader as fdr
import google.generativeai as genai
import datetime

# ---------------------------------------------------------
# [1] 기본 설정
# ---------------------------------------------------------
st.set_page_config(page_title="Ray's AI Analyst", page_icon="📈", layout="wide")

# ---------------------------------------------------------
# [2] 비밀 금고에서 API 키 꺼내기
# ---------------------------------------------------------
try:
    # 스트림릿 금고(Secrets)에서 키를 가져옴
    API_KEY = st.secrets["GEMINI_API_KEY"]
except:
    # 혹시 키 설정 안 했을 때를 대비한 안내
    st.error("⚠️ API 키가 없어요! Streamlit Settings -> Secrets 에 키를 넣어주세요.")
    st.stop()

# ---------------------------------------------------------
# [3] 메인 화면
# ---------------------------------------------------------
st.title("Ray's Intelligent Stock Analyst")
st.caption("Real-time Analysis Powered by Gemini")
st.markdown("---")

# 사이드바 설정
with st.sidebar:
    st.header("🔍 검색 옵션")
    # 기본값을 삼성전자로 설정
    user_input = st.text_input("종목명 또는 코드", value="삼성전자")
    days = st.slider("분석 기간 (일)", 30, 365, 100)

if user_input:
    # 캐싱으로 속도 향상 (매번 다운로드 안 받게)
    @st.cache_data
    def get_stock_list():
        return fdr.StockListing('KRX')

    try:
        with st.spinner("종목 정보를 찾는 중... 슝슝 💨"):
            df_stocks = get_stock_list()
            
        # 이름이나 코드로 종목 찾기
        search_result = df_stocks[ (df_stocks['Code'] == user_input) | (df_stocks['Name'] == user_input) ]
        
        if not search_result.empty:
            target_code = search_result.iloc[0]['Code']
            target_name = search_result.iloc[0]['Name']
            
            st.subheader(f"📈 {target_name} ({target_code})")
            
            # [진짜 데이터 가져오기]
            today = datetime.datetime.now()
            start_date = today - datetime.timedelta(days=days)
            df_chart = fdr.DataReader(target_code, start_date, today)

            # 차트 그리기 (빨간색 상승 그래프 느낌!)
            st.line_chart(df_chart['Close'], color="#FF4B4B")

            # 데이터 표 (최신순 5개만 깔끔하게)
            st.dataframe(df_chart.sort_index(ascending=False).head(5), use_container_width=True)

            # -------------------------------------------------------
            # [AI 분석 버튼] 여기가 하이라이트! ✨
            # -------------------------------------------------------
            if st.button("🤖 AI 심층 리포트 생성 (Click)"):
                with st.spinner(f"{target_name} 데이터를 분석하고 있어! 잠시만... 🧠"):
                    genai.configure(api_key=API_KEY)
                    model = genai.GenerativeModel('gemini-pro')

                    # 데이터 텍스트로 변환
                    recent_data = df_chart.tail(30).to_string()

                    prompt = f"""
                    당신은 전문 주식 애널리스트입니다. '{target_name}'의 주가 데이터를 분석해주세요.
                    
                    [최근 30일 데이터]
                    {recent_data}

                    [요청사항]
                    1. 최근 주가 추세 (상승/하락/횡보)를 요약하세요.
                    2. 투자자가 유의해야 할 변동성이나 패턴이 있는지 설명하세요.
                    3. 향후 전망 및 투자 전략을 제안하세요.
                    4. 한국어로, 전문적이고 간결하게 작성하세요.
                    """

                    response = model.generate_content(prompt)
                    st.success("분석 완료! 😎")
                    st.markdown("### 📝 AI Analyst Report")
                    st.write(response.text)

        else:
            st.warning("음? 그런 종목은 없는데? 이름을 다시 확인해줘! 🤔")

    except Exception as e:
        st.error(f"으악! 에러가 났어: {e}")
