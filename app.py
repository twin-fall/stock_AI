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
    # [중요] 안내 문구: 에러 방지를 위해 코드를 넣으라고 안내
    user_input = st.text_input("종목 코드 (예: 005930)", value="005930") 
    days = st.slider("분석 기간 (일)", 30, 365, 100)

if user_input:
    # ---------------------------------------------------------
    # [생존 전략] 명단 검색 에러 무시하고 진행
    # ---------------------------------------------------------
    target_code = user_input 
    target_name = user_input 

    # 명단 가져오기 시도 (실패하면 조용히 넘어감)
    try:
        df_stocks = fdr.StockListing('KRX') 
        search_result = df_stocks[ (df_stocks['Code'] == user_input) | (df_stocks['Name'] == user_input) ]
        if not search_result.empty:
            target_code = search_result.iloc[0]['Code']
            target_name = search_result.iloc[0]['Name']
    except:
        st.toast("⚠️ 거래소 명단 차단됨 -> 코드 검색 모드로 전환합니다.")
        pass

    # ---------------------------------------------------------
    # [4] 차트 & AI 분석
    # ---------------------------------------------------------
    try:
        st.subheader(f"📈 {target_name} ({target_code})")
        
        # 주가 데이터 가져오기
        today = datetime.datetime.now()
        start_date = today - datetime.timedelta(days=days)
        df_chart = fdr.DataReader(target_code, start_date, today)

        if df_chart.empty:
            st.error("데이터가 없어요. 종목 코드(6자리)가 맞나요? (예: 삼성전자 -> 005930)")
        else:
            # 차트 그리기
            st.line_chart(df_chart['Close'], color="#FF4B4B")

            # 데이터 표
            st.dataframe(df_chart.sort_index(ascending=False).head(5), use_container_width=True)

            # AI 분석 버튼
            if st.button("🤖 AI 심층 리포트 생성 (Click)"):
                with st.spinner(f"최신 AI가 데이터를 분석 중입니다... 🧠"):
                    genai.configure(api_key=API_KEY)
                    
                    # [수정된 부분] 모델 이름을 최신형으로 변경! (이게 핵심!)
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    
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
        st.error(f"오류가 발생했습니다: {e}")


