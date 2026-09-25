import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd
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
CODE_TO_NAME = {code: name for name, code in ALL_STOCKS.items()}

PAGES = {
    "홈": "🏠 홈",
    "국내주식": "🇰🇷 국내주식",
    "미국주식": "🇺🇸 미국주식",
    "검색": "🔍 종목검색",
}

PAGE_TO_KEY = {value: key for key, value in PAGES.items()}


@st.cache_data(ttl=60)
def get_stock_data(ticker_code, period="6mo", interval="1d"):
    try:
        data = yf.Ticker(ticker_code).history(
            period=period,
            interval=interval,
            auto_adjust=False,
        )
        return None if data.empty else data
    except Exception:
        return None


@st.cache_data(ttl=300)
def get_stock_profile(ticker_code):
    try:
        info = yf.Ticker(ticker_code).get_info()
        return info or {}
    except Exception:
        return {}


@st.cache_data(ttl=300)
def get_stock_news(ticker_code):
    try:
        return yf.Ticker(ticker_code).get_news(count=10) or []
    except Exception:
        return []


def get_stock_info(ticker_code):
    data = get_stock_data(ticker_code, "5d", "1d")
    if data is None or data.empty:
        return None

    current_price = float(data["Close"].iloc[-1])
    previous_price = float(data["Close"].iloc[-2]) if len(data) >= 2 else current_price
    change = current_price - previous_price
    change_percent = (change / previous_price * 100) if previous_price else 0

    return {
        "price": current_price,
        "change": change,
        "change_percent": change_percent,
        "volume": int(data["Volume"].iloc[-1]) if "Volume" in data else 0,
    }


def go_page(page_key):
    st.query_params["page"] = page_key
    st.rerun()


def go_stock(name, ticker_code):
    st.query_params.from_dict({"page": "종목", "code": ticker_code})


def stock_card(name, ticker_code):
    info = get_stock_info(ticker_code)

    if info is None:
        st.warning(f"{name}: 데이터를 가져오지 못했습니다.")
        return

    st.markdown(f"### {name}")

    c1, c2 = st.columns([2, 1])

    with c1:
        st.metric(
            "현재가",
            f"{info['price']:,.2f}",
            f"{info['change']:+,.2f} ({info['change_percent']:+.2f}%)",
        )

    with c2:
        if st.button(
            "📈 상세보기",
            key=f"detail_{ticker_code}",
            use_container_width=True,
        ):
            go_stock(name, ticker_code)


def render_navigation():
    st.sidebar.title("📈 Stock Insight")
    st.sidebar.markdown("---")

    current_page = st.query_params.get("page", "홈")

    for key, label in PAGES.items():
        if st.sidebar.button(
            label,
            key=f"nav_{key}",
            use_container_width=True,
        ):
            go_page(key)

    st.sidebar.markdown("---")
    st.sidebar.caption("Python + Streamlit")
    return current_page


def render_price_chart(ticker_code, period="6mo", chart_type="캔들"):
    data = get_stock_data(ticker_code, period, "1d")

    if data is None or data.empty:
        st.error("주가 데이터를 가져오지 못했습니다.")
        return

    if chart_type == "캔들":
        fig = go.Figure(
            go.Candlestick(
                x=data.index,
                open=data["Open"],
                high=data["High"],
                low=data["Low"],
                close=data["Close"],
                name="주가",
            )
        )
    else:
        fig = go.Figure(
            go.Scatter(
                x=data.index,
                y=data["Close"],
                mode="lines",
                name="종가",
            )
        )

    data = data.copy()
    data["MA20"] = data["Close"].rolling(20).mean()
    data["MA60"] = data["Close"].rolling(60).mean()

    fig.add_trace(
        go.Scatter(x=data.index, y=data["MA20"], mode="lines", name="20일선")
    )
    fig.add_trace(
        go.Scatter(x=data.index, y=data["MA60"], mode="lines", name="60일선")
    )

    fig.update_layout(
        height=560,
        hovermode="x unified",
        xaxis_rangeslider_visible=False,
        margin=dict(l=10, r=10, t=50, b=10),
    )

    st.plotly_chart(fig, use_container_width=True)


def render_volume_chart(ticker_code, period="6mo"):
    data = get_stock_data(ticker_code, period, "1d")

    if data is None or data.empty or "Volume" not in data:
        st.info("거래량 데이터를 가져오지 못했습니다.")
        return

    fig = go.Figure(
        go.Bar(
            x=data.index,
            y=data["Volume"],
            name="거래량",
        )
    )
    fig.update_layout(height=300, margin=dict(l=10, r=10, t=30, b=10))
    st.plotly_chart(fig, use_container_width=True)


def render_profile(ticker_code):
    info = get_stock_profile(ticker_code)
    if not info:
        st.info("재무/기업 정보가 제공되지 않았습니다.")
        return

    keys = [
        ("시가총액", "marketCap"),
        ("PER", "trailingPE"),
        ("PBR", "priceToBook"),
        ("EPS", "trailingEps"),
        ("배당수익률", "dividendYield"),
        ("52주 최고", "fiftyTwoWeekHigh"),
        ("52주 최저", "fiftyTwoWeekLow"),
    ]

    cols = st.columns(4)
    shown = 0

    for label, key in keys:
        value = info.get(key)
        if value is None:
            continue

        if key == "marketCap":
            value_text = f"{value:,.0f}"
        elif key == "dividendYield":
            value_text = f"{float(value) * 100:.2f}%"
        else:
            try:
                value_text = f"{float(value):,.2f}"
            except Exception:
                value_text = str(value)

        with cols[shown % 4]:
            st.metric(label, value_text)
        shown += 1


def render_news(ticker_code):
    news = get_stock_news(ticker_code)

    if not news:
        st.info("관련 뉴스를 가져오지 못했습니다.")
        return

    for item in news:
        content = item.get("content", item)
        title = content.get("title", "제목 없음")
        url = (
            content.get("canonicalUrl", {}) or {}
        ).get("url") or (
            content.get("clickThroughUrl", {}) or {}
        ).get("url")
        publisher = content.get("provider", {}).get("displayName", "")

        if url:
            st.markdown(f"**[{title}]({url})**")
        else:
            st.markdown(f"**{title}**")

        if publisher:
            st.caption(publisher)

        st.markdown("---")


def render_stock_detail(ticker_code):
    stock_name = CODE_TO_NAME.get(ticker_code, ticker_code)

    st.title(f"📊 {stock_name}")
    st.caption(f"Ticker: {ticker_code}")

    info = get_stock_info(ticker_code)

    if info is None:
        st.error("종목 데이터를 가져오지 못했습니다.")
        return

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.metric("현재가", f"{info['price']:,.2f}")
    with c2:
        st.metric("등락", f"{info['change']:+,.2f}")
    with c3:
        st.metric("등락률", f"{info['change_percent']:+.2f}%")
    with c4:
        st.metric("거래량", f"{info['volume']:,}")

    st.markdown("---")

    period = st.selectbox(
        "조회 기간",
        ["1mo", "3mo", "6mo", "1y", "2y", "5y"],
        index=2,
        key=f"period_{ticker_code}",
    )

    chart_type = st.radio(
        "차트",
        ["캔들", "라인"],
        horizontal=True,
        key=f"chart_{ticker_code}",
    )

    st.subheader("📈 주가 차트")
    render_price_chart(ticker_code, period, chart_type)

    st.subheader("📊 거래량")
    render_volume_chart(ticker_code, period)

    st.subheader("🏢 기업/재무 정보")
    render_profile(ticker_code)

    st.markdown("---")
    st.subheader("📰 관련 뉴스")
    render_news(ticker_code)

    st.markdown("---")
    st.subheader("🔗 다른 종목")

    cols = st.columns(3)
    quick = [("삼성전자", "005930.KS"), ("NVIDIA", "NVDA"), ("Apple", "AAPL")]

    for col, (name, code) in zip(cols, quick):
        with col:
            if st.button(name, key=f"quick_{code}", use_container_width=True):
                go_stock(name, code)


def render_home():
    st.title("📈 Stock Insight")
    st.subheader("주식 정보를 한 곳에서")
    st.write("국내주식과 미국주식의 가격, 차트, 거래량, 기업정보와 뉴스를 확인합니다.")

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
    st.header("빠른 이동")

    c1, c2, c3 = st.columns(3)

    with c1:
        if st.button("🇰🇷 국내주식", use_container_width=True):
            go_page("국내주식")

    with c2:
        if st.button("🇺🇸 미국주식", use_container_width=True):
            go_page("미국주식")

    with c3:
        if st.button("🔍 종목검색", use_container_width=True):
            go_page("검색")


def render_market(title, stocks):
    st.title(title)
    st.markdown("---")

    for name, code in stocks.items():
        stock_card(name, code)
        st.markdown("---")


def render_search():
    st.title("🔍 종목검색")

    search = st.text_input(
        "종목명 또는 티커",
        placeholder="예: 삼성전자 / AAPL / NVDA",
        key="search_input",
    ).strip()

    if not search:
        st.info("종목명 또는 티커를 입력하세요.")
        return

    results = [
        (name, code)
        for name, code in ALL_STOCKS.items()
        if search.lower() in name.lower() or search.lower() in code.lower()
    ]

    if not results:
        st.warning("검색 결과가 없습니다.")
        return

    st.success(f"{len(results)}개의 종목을 찾았습니다.")

    for name, code in results:
        stock_card(name, code)
        st.markdown("---")


page = render_navigation()

if page == "종목":
    ticker_code = st.query_params.get("code", "AAPL")
    if ticker_code not in ALL_STOCKS.values():
        ticker_code = "AAPL"
    render_stock_detail(ticker_code)
elif page == "홈":
    render_home()
elif page == "국내주식":
    render_market("🇰🇷 국내주식", KOREA_STOCKS)
elif page == "미국주식":
    render_market("🇺🇸 미국주식", USA_STOCKS)
elif page == "검색":
    render_search()
else:
    render_home()

st.markdown("---")
st.caption(
    f"Stock Insight | 업데이트: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
)
