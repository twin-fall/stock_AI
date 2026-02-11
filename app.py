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
    API_KEY = st.secrets["GEMINI_API_KEY"]
except:
    st.error("⚠️ API 키가 없어요! Settings -> Secrets 에 키를 넣어주세요.")
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
    # 팁: 에러가 나면 '종목명' 대신 '코드(005930)'를 넣으면 됨!
    user_input = st.text_input("종목명 또는 코드 (예: 005930)", value="005930") 
    days = st.slider("분석 기간 (일)", 30, 365, 100)

if user_input:
    # ---------------------------------------------------------
    # [핵심 수정] 리스트 다운로드 실패 시 '좀비 모드' 발동 🧟
    # ---------------------------------------------------------
    @st.cache_data
    def get_stock_list():
        try:
            return fdr.StockListing('KRX')
        except Exception:
            return None # 실패하면 그냥 빈손으로 돌아옴 (에러 안 냄!)

    # 1. 일단 거래소 명단 가져오기 시도
    with st.spinner("종목 정보 확인 중..."):
        df_stocks = get_stock_list()

    target_code = ""
    target_name = ""

    # 2. 명단을 가져왔으면 이름으로 찾기
    if df_stocks is not None:
        search_result = df_stocks[ (df_stocks['Code'] == user_input) | (df_stocks['Name'] == user_input) ]
        if not search_result.empty:
            target_code = search_result.iloc[0]['Code']
            target_name = search_result.iloc[0]['Name']
    
    # 3. [중요] 명단 못 가져왔거나 검색 실패하면 -> 입력값을 그냥 '코드'로 인식!
    if not target_code:
        # 사용자가 입력한 게 6자리 숫자(코드)라고 가정
        target_code = user_input
        target_name = user_input # 이름은 모르니까 그냥 코드 보여줌

    # ---------------------------------------------------------
    # [4] 차트 & AI 분석 (여기는 동일!)
    # ---------------------------------------------------------
    if target_code:
        try:
            st.subheader(f"📈 {target_name} ({target_code})")
            
            # 주가 데이터 가져오기
            today = datetime.datetime.now()
            start_date = today - datetime.timedelta(days=days)
            df_chart = fdr.DataReader(target_code, start_date, today)

            if df_chart.empty:
                st.warning("데이터를 찾을 수 없습니다. 올바른 종목 코드(6자리)인지 확인해주세요!")
            else:
                # 차트 그리기
                st.line_chart(df_chart['Close'], color="#FF4B4B")

                # 데이터 표
                st.dataframe(df_chart.sort_index(ascending=False).head(5), use_container_width=True)

                # AI 분석 버튼
                if st.button("🤖 AI 심층 리포트 생성 (Click)"):
                    with st.spinner(f"데이터 분석 중... 🧠"):
                        genai.configure(api_key=API_KEY)
                        model = genai.GenerativeModel('gemini-pro')
                        recent_data = df_chart.tail(30).to_string()

                        prompt = f"""
                        당신은 주식 전문가입니다. '{target_name}'(코드:{target_code})의 주가를 분석해주세요.
                        [최근 30일 데이터]
                        {recent_data}
                        [요청]
                        1. 추세 요약 (상승/하락)
                        2. 특이 패턴 분석
                        3. 투자 전략 제안
                        4. 한국어로 작성
                        """
                        response = model.generate_content(prompt)
                        st.success("분석 완료!")
                        st.markdown(response.text)

        except Exception as e:
            # 여기서 나는 에러는 진짜 데이터가 없는 경우
            st.error(f"데이터를 가져올 수 없습니다. (종목 코드를 정확히 입력했나요?): {e}")
