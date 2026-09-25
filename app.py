import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(
    page_title="Stock Insight",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

KOREA_STOCKS = {
    "삼성전자": "005930.KS",
    "SK하이닉스": "000660.KS",
    "현대차": "005380.KS",
    "NAVER": "035420.KS",
    "카카오": "035720.KS",
}

USA_STOCKS = {
    "Apple": "AAPL",
    "NVIDIA": "NVDA",
    "Microsoft": "MSFT",
    "Amazon": "AMZN",
    "Tesla": "TSLA",
}

ALL_STOCKS = {**KOREA_STOCKS, **USA_STOCKS}


@st.cache_data(ttl=60)
def get_stock_data(ticker_code, period="6mo"):
    try:
        data = yf.Ticker(ticker_code).history(period=period)
        return None if data.empty else data
    except Exception:
        return None


def get_stock_info(ticker_code):
    data = get_stock_data(ticker_code, "5d")
    if data is None or data.empty:
        return None

    current_price = float(data["Close"].iloc[-1])
    previous_price = (
        float(data["Close"].iloc[-2]) if len(data) >= 2 else current_price
    )
    change = current_price - previous_price
    change_percent = (change / previous_price * 100) if previous_price else 0

    return {
        "price": current_price,
        "change": change,
        "change_percent": change_percent,
    }


def show_chart(ticker_code, period="6mo"):
    data = get_stock_data(ticker_code, period)

    if data is None or data.empty:
        st.error("주가 데이터를 가져오지 못했습니다.")
        return

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=data.index,
            y=data["Close"],
            mode="lines",
            name="종가",
        )
    )
    fig.update_layout(
        title="주가 차트",
        xaxis_title="날짜",
        yaxis_title="가격",
        height=500,
        hovermode="x unified",
    )
    st.plotly_chart(fig, use_container_width=True)


def open_stock(name, ticker_code):
    st.session_state["selected_stock"] = ticker_code
    st.session_state["selected_name"] = name


def stock_card(name, ticker_code):
    info = get_stock_info(ticker_code)

    if info is None:
        st.warning(f"{name}: 데이터를 가져오지 못했습니다.")
        return

    st.markdown(f"### {name}")
    col1, col2 = st.columns([2, 1])

    with col1:
        st.metric(
            "현재가",
            f"{info['price']:,.2f}",
            f"{info['change']:+,.2f} ({info['change_percent']:+.2f}%)",
        )

    with col2:
        if st.button("📈 상세보기", key=f"detail_{ticker_code}", use_container_width=True):
            open_stock(name, ticker_code)
            st.rerun()


if "selected_stock" not in st.session_state:
    st.session_state["selected_stock"] = "AAPL"

if "selected_name" not in st.session_state:
    st.session_state["selected_name"] = "Apple"


st.sidebar.title("📈 Stock Insight")
st.sidebar.markdown("---")

menu = st.sidebar.radio(
    "메뉴",
    ["🏠 홈", "🇰🇷 국내주식", "🇺🇸 미국주식", "🔍 종목검색", "📊 종목 상세"],
)

st.sidebar.markdown("---")
st.sidebar.caption("Python + Streamlit")


if menu == "🏠 홈":
    st.title("📈 Stock Insight")
    st.subheader("주식 정보를 한 곳에서")
    st.write("국내주식과 미국주식의 가격과 차트를 확인할 수 있습니다.")

    st.markdown("---")
    st.header("🔥 주요 종목")

    cols = st.columns(3)
    for col, (name, code) in zip(
        cols,
        [("삼성전자", "005930.KS"), ("NVIDIA", "NVDA"), ("Apple", "AAPL")],
    ):
        with col:
            stock_card(name, code)

    st.markdown("---")
    st.info("왼쪽 메뉴에서 국내주식, 미국주식, 종목검색 또는 종목 상세를 선택하세요.")


elif menu == "🇰🇷 국내주식":
    st.title("🇰🇷 국내주식")
    st.write("주요 국내 종목")
    st.markdown("---")

    for name, code in KOREA_STOCKS.items():
        stock_card(name, code)
        st.markdown("---")


elif menu == "🇺🇸 미국주식":
    st.title("🇺🇸 미국주식")
    st.write("주요 미국 종목")
    st.markdown("---")

    for name, code in USA_STOCKS.items():
        stock_card(name, code)
        st.markdown("---")


elif menu == "🔍 종목검색":
    st.title("🔍 종목검색")

    search = st.text_input(
        "종목명 또는 티커를 입력하세요",
        placeholder="예: 삼성전자 / AAPL / NVDA",
    ).strip()

    if search:
        results = [
            (name, code)
            for name, code in ALL_STOCKS.items()
            if search.lower() in name.lower() or search.lower() in code.lower()
        ]

        if results:
            st.success(f"{len(results)}개의 종목을 찾았습니다.")
            for name, code in results:
                stock_card(name, code)
                st.markdown("---")
        else:
            st.warning("검색 결과가 없습니다.")
    else:
        st.info("종목명 또는 티커를 입력하세요.")


elif menu == "📊 종목 상세":
    ticker_code = st.session_state["selected_stock"]
    stock_name = st.session_state["selected_name"]

    st.title(f"📊 {stock_name}")
    st.caption(f"Ticker: {ticker_code}")

    info = get_stock_info(ticker_code)

    if info is None:
        st.error("종목 데이터를 가져오지 못했습니다.")
    else:
        c1, c2, c3 = st.columns(3)

        with c1:
            st.metric("현재가", f"{info['price']:,.2f}")
        with c2:
            st.metric("등락", f"{info['change']:+,.2f}")
        with c3:
            st.metric("등락률", f"{info['change_percent']:+.2f}%")

        st.markdown("---")
        st.subheader("📈 주가 차트")

        period = st.selectbox(
            "조회 기간",
            ["1mo", "3mo", "6mo", "1y", "2y", "5y"],
            index=2,
        )
        show_chart(ticker_code, period)

        st.markdown("---")
        st.subheader("🔗 다른 종목")

        c1, c2, c3 = st.columns(3)

        for col, (name, code) in zip(
            [c1, c2, c3],
            [("삼성전자", "005930.KS"), ("NVIDIA", "NVDA"), ("Apple", "AAPL")],
        ):
            with col:
                if st.button(name, key=f"quick_{code}", use_container_width=True):
                    open_stock(name, code)
                    st.rerun()


st.markdown("---")
st.caption(
    f"Stock Insight | 업데이트: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
)
