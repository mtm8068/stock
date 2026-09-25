import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime
from supabase import create_client

st.set_page_config(
    page_title="Stock Insight",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
.stApp { background:#f6f8fb; }
.block-container { max-width:1400px; padding-top:1.2rem; }
[data-testid="stSidebar"] { background:#fff; border-right:1px solid #e5e7eb; }
.hero { padding:30px; background:#fff; border:1px solid #e5e7eb; border-radius:22px; margin-bottom:20px; }
.hero h1 { font-size:38px; letter-spacing:-.05em; margin:0 0 6px; }
.hero p { color:#64748b; }
.section-title { font-size:19px; font-weight:750; margin:22px 0 10px; }
.stock-header { background:#fff; border:1px solid #e5e7eb; border-radius:18px; padding:22px 24px; margin-bottom:16px; }
.quote-card { background:#fff; border:1px solid #e5e7eb; border-radius:16px; padding:18px; min-height:120px; box-shadow:0 3px 14px rgba(15,23,42,.035); }
.quote-name { font-weight:750; font-size:16px; }
.quote-price { font-size:25px; font-weight:800; margin-top:7px; }
.muted { color:#64748b; font-size:12px; }
.positive { color:#dc2626; font-weight:700; }
.negative { color:#2563eb; font-weight:700; }
div[data-testid="stButton"] > button { border-radius:10px; }
</style>
""", unsafe_allow_html=True)

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
    "관심종목": "⭐ 내 관심종목",
}


def get_supabase():
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
    except Exception:
        return None
    return create_client(url, key)


def restore_supabase_session(supabase):
    session = st.session_state.get("supabase_session")
    if not session:
        return None
    try:
        supabase.auth.set_session(session["access_token"], session["refresh_token"])
        user = supabase.auth.get_user()
        return user.user if user else None
    except Exception:
        st.session_state.pop("supabase_session", None)
        return None


def get_current_user():
    supabase = get_supabase()
    if supabase is None:
        return None
    return restore_supabase_session(supabase)


def auth_sidebar(supabase):
    st.sidebar.markdown("---")
    st.sidebar.subheader("🔐 계정")

    user = restore_supabase_session(supabase) if supabase else None

    if user:
        st.sidebar.caption(user.email or "로그인 사용자")
        if st.sidebar.button("로그아웃", use_container_width=True):
            try:
                supabase.auth.sign_out()
            except Exception:
                pass
            st.session_state.pop("supabase_session", None)
            st.rerun()
        return user

    tab_login, tab_signup = st.sidebar.tabs(["로그인", "회원가입"])

    with tab_login:
        email = st.text_input("이메일", key="login_email")
        password = st.text_input("비밀번호", type="password", key="login_password")
        if st.button("로그인", key="login_button", use_container_width=True):
            if not email or not password:
                st.warning("이메일과 비밀번호를 입력하세요.")
            else:
                try:
                    result = supabase.auth.sign_in_with_password(
                        {"email": email, "password": password}
                    )
                    if result.session:
                        st.session_state["supabase_session"] = {
                            "access_token": result.session.access_token,
                            "refresh_token": result.session.refresh_token,
                        }
                        st.success("로그인되었습니다.")
                        st.rerun()
                except Exception as exc:
                    st.error(f"로그인 실패: {exc}")

    with tab_signup:
        signup_email = st.text_input("이메일", key="signup_email")
        signup_password = st.text_input(
            "비밀번호 (6자 이상)", type="password", key="signup_password"
        )
        if st.button("회원가입", key="signup_button", use_container_width=True):
            if not signup_email or not signup_password:
                st.warning("이메일과 비밀번호를 입력하세요.")
            elif len(signup_password) < 6:
                st.warning("비밀번호는 6자 이상이어야 합니다.")
            else:
                try:
                    result = supabase.auth.sign_up(
                        {"email": signup_email, "password": signup_password}
                    )
                    if result.session:
                        st.session_state["supabase_session"] = {
                            "access_token": result.session.access_token,
                            "refresh_token": result.session.refresh_token,
                        }
                        st.success("회원가입 및 로그인이 완료되었습니다.")
                        st.rerun()
                    else:
                        st.success("회원가입 완료! 이메일 인증 후 로그인해 주세요.")
                except Exception as exc:
                    st.error(f"회원가입 실패: {exc}")


def get_watchlist(user_id):
    supabase = get_supabase()
    if supabase is None:
        return []
    try:
        response = (
            supabase.table("watchlist")
            .select("ticker,name,market,created_at")
            .eq("user_id", str(user_id))
            .order("created_at", desc=True)
            .execute()
        )
        return response.data or []
    except Exception as exc:
        st.error(f"관심종목 조회 실패: {exc}")
        return []


def is_watched(user_id, ticker):
    return any(item["ticker"] == ticker for item in get_watchlist(user_id))


def add_watchlist(user_id, name, ticker, market):
    supabase = get_supabase()
    if supabase is None:
        return False, "Supabase 설정이 없습니다."
    try:
        supabase.table("watchlist").insert(
            {
                "user_id": str(user_id),
                "ticker": ticker,
                "name": name,
                "market": market,
            }
        ).execute()
        return True, "관심종목에 추가했습니다."
    except Exception as exc:
        message = str(exc)
        if "duplicate" in message.lower() or "23505" in message:
            return True, "이미 관심종목에 있습니다."
        return False, f"관심종목 추가 실패: {exc}"


def remove_watchlist(user_id, ticker):
    supabase = get_supabase()
    if supabase is None:
        return False, "Supabase 설정이 없습니다."
    try:
        supabase.table("watchlist").delete().eq(
            "user_id", str(user_id)
        ).eq("ticker", ticker).execute()
        return True, "관심종목에서 삭제했습니다."
    except Exception as exc:
        return False, f"관심종목 삭제 실패: {exc}"


@st.cache_data(ttl=60)
def get_stock_data(ticker_code, period="6mo", interval="1d"):
    try:
        data = yf.Ticker(ticker_code).history(
            period=period, interval=interval, auto_adjust=False
        )
        return None if data.empty else data
    except Exception:
        return None


@st.cache_data(ttl=300)
def get_stock_profile(ticker_code):
    try:
        return yf.Ticker(ticker_code).get_info() or {}
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
    st.query_params.clear()
    st.query_params["page"] = page_key
    st.rerun()


def go_stock(name, ticker_code):
    st.query_params.clear()
    st.query_params["code"] = ticker_code
    st.rerun()


def stock_card(name, ticker_code):
    info = get_stock_info(ticker_code)
    if info is None:
        st.warning(f"{name}: 데이터를 가져오지 못했습니다.")
        return
    st.markdown(
        f'<div class="quote-card"><div class="quote-name">{name}</div>'
        f'<div class="quote-price">{info["price"]:,.2f}</div>'
        f'<div class="{"positive" if info["change"] >= 0 else "negative"}">'
        f'{info["change"]:+,.2f} ({info["change_percent"]:+.2f}%)</div>'
        f'<div class="muted">{ticker_code}</div></div>',
        unsafe_allow_html=True,
    )
    c1, c2 = st.columns([2, 1])
    with c1:
        st.metric(
            "현재가",
            f"{info['price']:,.2f}",
            f"{info['change']:+,.2f} ({info['change_percent']:+.2f}%)",
        )
    with c2:
        st.link_button("종목 상세 →", f"?code={ticker_code}", use_container_width=True)


def render_navigation():
    st.sidebar.title("📈 Stock Insight")
    st.sidebar.markdown("---")
    current_page = st.query_params.get("page", "홈")

    supabase = get_supabase()
    user = auth_sidebar(supabase) if supabase else None

    for key, label in PAGES.items():
        if key == "관심종목" and not user:
            continue
        if st.sidebar.button(label, key=f"nav_{key}", use_container_width=True):
            go_page(key)

    if not supabase:
        st.sidebar.info("Supabase 설정을 추가하면 로그인/관심종목 기능을 사용할 수 있습니다.")
    st.sidebar.markdown("---")
    st.sidebar.caption("Python + Streamlit + Supabase")
    return current_page, user


def render_price_chart(ticker_code, period="6mo", chart_type="캔들"):
    data = get_stock_data(ticker_code, period, "1d")
    if data is None or data.empty:
        st.error("주가 데이터를 가져오지 못했습니다.")
        return
    if chart_type == "캔들":
        fig = go.Figure(go.Candlestick(
            x=data.index, open=data["Open"], high=data["High"],
            low=data["Low"], close=data["Close"], name="주가"
        ))
    else:
        fig = go.Figure(go.Scatter(
            x=data.index, y=data["Close"], mode="lines", name="종가"
        ))
    data = data.copy()
    data["MA20"] = data["Close"].rolling(20).mean()
    data["MA60"] = data["Close"].rolling(60).mean()
    fig.add_trace(go.Scatter(x=data.index, y=data["MA20"], mode="lines", name="20일선"))
    fig.add_trace(go.Scatter(x=data.index, y=data["MA60"], mode="lines", name="60일선"))
    fig.update_layout(height=560, hovermode="x unified", xaxis_rangeslider_visible=False,
                      margin=dict(l=10, r=10, t=50, b=10))
    st.plotly_chart(fig, use_container_width=True)


def render_volume_chart(ticker_code, period="6mo"):
    data = get_stock_data(ticker_code, period, "1d")
    if data is None or data.empty or "Volume" not in data:
        st.info("거래량 데이터를 가져오지 못했습니다.")
        return
    fig = go.Figure(go.Bar(x=data.index, y=data["Volume"], name="거래량"))
    fig.update_layout(height=300, margin=dict(l=10, r=10, t=30, b=10))
    st.plotly_chart(fig, use_container_width=True)


def render_profile(ticker_code):
    info = get_stock_profile(ticker_code)
    if not info:
        st.info("재무/기업 정보가 제공되지 않았습니다.")
        return
    keys = [
        ("시가총액", "marketCap"), ("PER", "trailingPE"), ("PBR", "priceToBook"),
        ("EPS", "trailingEps"), ("배당수익률", "dividendYield"),
        ("52주 최고", "fiftyTwoWeekHigh"), ("52주 최저", "fiftyTwoWeekLow"),
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
        url = (content.get("canonicalUrl", {}) or {}).get("url") or (
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


def render_watch_button(user, stock_name, ticker_code):
    if not user:
        st.info("로그인하면 관심종목을 저장할 수 있습니다.")
        return
    market = "국내주식" if ticker_code.endswith((".KS", ".KQ")) else "미국주식"
    watched = is_watched(user.id, ticker_code)
    label = "★ 관심종목 삭제" if watched else "☆ 관심종목 추가"
    if st.button(label, key=f"watch_{ticker_code}", use_container_width=True):
        ok, message = (
            remove_watchlist(user.id, ticker_code)
            if watched
            else add_watchlist(user.id, stock_name, ticker_code, market)
        )
        if ok:
            st.success(message)
            st.rerun()
        else:
            st.error(message)


def render_stock_detail(ticker_code, user):
    stock_name = CODE_TO_NAME.get(ticker_code, ticker_code)
    market = "국내주식" if ticker_code.endswith((".KS", ".KQ")) else "미국주식"
    info = get_stock_info(ticker_code)
    if info is None:
        st.error("종목 데이터를 가져오지 못했습니다.")
        return
    change_class = "positive" if info["change"] >= 0 else "negative"
    st.markdown(
        f'<div class="stock-header"><div class="muted">{market} · {ticker_code}</div>'
        f'<div style="font-size:30px;font-weight:800">{stock_name}</div>'
        f'<div style="font-size:28px;font-weight:800;margin-top:8px">{info["price"]:,.2f}</div>'
        f'<div class="{change_class}">{info["change"]:+,.2f} ({info["change_percent"]:+.2f}%)</div></div>',
        unsafe_allow_html=True,
    )
    render_watch_button(user, stock_name, ticker_code)
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
    period = st.selectbox("조회 기간", ["1mo", "3mo", "6mo", "1y", "2y", "5y"],
                          index=2, key=f"period_{ticker_code}")
    chart_type = st.radio("차트", ["캔들", "라인"], horizontal=True, key=f"chart_{ticker_code}")
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
    for col, (name, code) in zip(cols, [("삼성전자", "005930.KS"), ("NVIDIA", "NVDA"), ("Apple", "AAPL")]):
        with col:
            st.link_button(name, f"?code={code}", use_container_width=True)


def render_watchlist(user):
    st.title("⭐ 내 관심종목")
    if not user:
        st.info("로그인 후 이용할 수 있습니다.")
        return
    items = get_watchlist(user.id)
    if not items:
        st.info("아직 저장한 관심종목이 없습니다. 종목 상세 화면에서 ☆ 관심종목 추가를 눌러보세요.")
        return
    for item in items:
        name, ticker = item["name"], item["ticker"]
        info = get_stock_info(ticker)
        c1, c2, c3 = st.columns([3, 2, 1])
        with c1:
            st.markdown(f"### {name}")
            st.caption(f"{item['market']} · {ticker}")
        with c2:
            if info:
                st.metric("현재가", f"{info['price']:,.2f}",
                          f"{info['change']:+,.2f} ({info['change_percent']:+.2f}%)")
        with c3:
            if st.button("상세", key=f"wl_detail_{ticker}", use_container_width=True):
                go_stock(name, ticker)
            if st.button("삭제", key=f"wl_delete_{ticker}", use_container_width=True):
                ok, message = remove_watchlist(user.id, ticker)
                if ok:
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)
        st.markdown("---")


def render_home():
    st.markdown('<div class="hero"><h1>Stock Insight</h1><p>국내·미국 주식의 시세, 차트, 기업정보와 뉴스를 한 화면에서 확인하세요.</p></div>', unsafe_allow_html=True)
    st.markdown("---")
    st.header("🔥 주요 종목")
    cols = st.columns(3)
    for col, (name, code) in zip(cols, [("삼성전자", "005930.KS"), ("NVIDIA", "NVDA"), ("Apple", "AAPL")]):
        with col:
            stock_card(name, code)
    st.markdown("---")
    st.header("빠른 이동")
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("🇰🇷 국내주식", use_container_width=True): go_page("국내주식")
    with c2:
        if st.button("🇺🇸 미국주식", use_container_width=True): go_page("미국주식")
    with c3:
        if st.button("🔍 종목검색", use_container_width=True): go_page("검색")


def render_market(title, stocks):
    st.title(title)
    st.markdown("---")
    for name, code in stocks.items():
        stock_card(name, code)
        st.markdown("---")


def render_search():
    st.title("🔍 종목검색")
    search = st.text_input("종목명 또는 티커", placeholder="예: 삼성전자 / AAPL / NVDA", key="search_input").strip()
    if not search:
        st.info("종목명 또는 티커를 입력하세요.")
        return
    results = [(name, code) for name, code in ALL_STOCKS.items()
               if search.lower() in name.lower() or search.lower() in code.lower()]
    if not results:
        st.warning("검색 결과가 없습니다.")
        return
    st.success(f"{len(results)}개의 종목을 찾았습니다.")
    for name, code in results:
        stock_card(name, code)
        st.markdown("---")


supabase = get_supabase()
page, user = render_navigation()

ticker_code = st.query_params.get("code")
if ticker_code:
    if ticker_code not in ALL_STOCKS.values():
        st.error("존재하지 않는 종목 코드입니다.")
    else:
        render_stock_detail(ticker_code, user)
elif page == "홈":
    render_home()
elif page == "국내주식":
    render_market("🇰🇷 국내주식", KOREA_STOCKS)
elif page == "미국주식":
    render_market("🇺🇸 미국주식", USA_STOCKS)
elif page == "검색":
    render_search()
elif page == "관심종목":
    render_watchlist(user)
else:
    render_home()

st.markdown("---")
st.caption(f"Stock Insight | 업데이트: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
