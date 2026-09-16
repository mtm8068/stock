import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

st.set_page_config(
    page_title="StockVista · 주식 투자 대시보드",
    page_icon="↗",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------- Theme ----------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;600;700;800&display=swap');
    :root { --navy:#061a38; --blue:#0878ff; --ink:#0c2448; --muted:#61708a; --line:#e4ebf4; --bg:#f7faff; }
    .stApp { background:var(--bg); color:var(--ink); font-family:'Noto Sans KR',sans-serif; }
    [data-testid="stHeader"] { background:transparent; }
    [data-testid="stToolbar"] { display:none; }
    .block-container { max-width:1260px; padding:0 28px 40px; }
    .topbar { background:#0b2347; color:white; padding:14px 4%; margin:0 -28px 0; display:flex; align-items:center; gap:30px; }
    .brand { font-size:23px; font-weight:800; white-space:nowrap; }
    .brand-mark { color:#1683ff; font-size:30px; margin-right:7px; }
    .navitem { color:#dce8f8; font-size:14px; font-weight:700; margin-right:24px; }
    .hero { margin:0 -28px; padding:62px 7.6%; min-height:310px; background:linear-gradient(100deg,#061a38,#092750 48%,#0b3a70); color:white; border-radius:0 0 18px 18px; position:relative; overflow:hidden; }
    .hero:after { content:''; position:absolute; width:520px; height:520px; right:-120px; top:-170px; border-radius:50%; background:radial-gradient(circle,rgba(20,120,255,.32),transparent 65%); }
    .eyebrow { color:#b9d7ff; font-size:13px; font-weight:800; letter-spacing:.04em; margin:0 0 9px; }
    .eyebrow.blue { color:var(--blue); }
    .hero h1 { font-size:44px; line-height:1.15; margin:0 0 16px; letter-spacing:-.04em; }
    .hero h1 span { color:#1384ff; }
    .hero-copy { color:#e1ebf9; font-size:16px; line-height:1.7; margin-bottom:22px; }
    .hero-badge { position:absolute; z-index:2; right:9%; top:60px; width:245px; padding:16px 18px; border:1px solid rgba(130,170,220,.35); border-radius:12px; background:rgba(10,33,67,.82); }
    .hero-badge .value { display:block; font-size:22px; font-weight:800; margin:4px 0; }
    .up { color:#ff4d58; }
    .down { color:#1676ef; }
    .section { padding:42px 0 0; }
    .section-title { font-size:28px; font-weight:800; margin:0 0 5px; }
    .muted { color:var(--muted); }
    .card { background:white; border:1px solid var(--line); border-radius:12px; padding:22px; box-shadow:0 7px 22px rgba(23,60,100,.04); height:100%; }
    .icon { width:40px; height:40px; border-radius:50%; display:flex; align-items:center; justify-content:center; color:white; font-size:20px; font-weight:800; }
    .feature-title { font-size:16px; font-weight:800; margin:14px 0 7px; }
    .feature-text { font-size:13px; line-height:1.6; color:var(--muted); min-height:42px; }
    .metric-card { background:white; border:1px solid var(--line); border-radius:9px; padding:15px; }
    .metric-name { color:#667891; font-size:12px; }
    .metric-value { font-size:19px; font-weight:800; margin:6px 0; }
    .metric-change { font-size:11px; font-weight:700; }
    .news-item { padding:12px 0; border-top:1px solid var(--line); font-size:12px; }
    .tag { background:#edf5ff; color:#1676ef; border-radius:9px; padding:3px 7px; font-size:10px; font-weight:700; margin-right:6px; }
    .portfolio { background:linear-gradient(110deg,#eaf4ff,#fff); border:1px solid #dbeaff; border-radius:14px; padding:24px; margin-top:28px; }
    footer { border-top:1px solid var(--line); margin-top:40px; padding:24px 0; color:#7a899f; font-size:12px; }
    @media(max-width:900px) { .hero-badge { display:none; } .hero h1 { font-size:36px; } }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------- Header ----------
st.markdown(
    '<div class="topbar"><div class="brand"><span class="brand-mark">↗</span>StockVista</div>'
    '<div><span class="navitem">홈</span><span class="navitem">시장동향</span><span class="navitem">종목검색</span>'
    '<span class="navitem">분석도구</span><span class="navitem">포트폴리오</span><span class="navitem">커뮤니티</span></div></div>',
    unsafe_allow_html=True,
)

# ---------- Hero ----------
st.markdown(
    '<section class="hero"><p class="eyebrow">데이터로 더 스마트한 투자</p>'
    '<h1>지금, 더 나은<br><span>투자</span>를 시작하세요</h1>'
    '<p class="hero-copy">실시간 주가 정보부터 기업 분석, 재무제표까지<br>StockVista가 당신의 투자를 돕습니다.</p>'
    '<div class="hero-badge"><span>KOSPI</span><span class="value">2,643.21</span>'
    '<span class="up">▲ 12.34 (+0.47%)</span></div></section>',
    unsafe_allow_html=True,
)

# ---------- Search ----------
st.markdown('<div class="section"><p class="eyebrow blue">STOCK SEARCH</p><h2 class="section-title">종목 검색</h2></div>', unsafe_allow_html=True)
query = st.text_input("", placeholder="종목명, 코드, 키워드로 검색하세요...", label_visibility="collapsed")
if query:
    names = pd.DataFrame({"종목": ["삼성전자", "SK하이닉스", "NAVER", "현대차"], "코드": ["005930", "000660", "035420", "005380"]})
    result = names[names.apply(lambda r: query.lower() in str(r).lower(), axis=1)]
    if result.empty:
        st.info(f"'{query}'에 해당하는 샘플 종목이 없습니다.")
    else:
        st.dataframe(result, hide_index=True, use_container_width=True)

# ---------- Features ----------
st.markdown('<div class="section"><p class="eyebrow blue">OUR FEATURES</p><h2 class="section-title">주요 서비스</h2><p class="muted">StockVista는 다양한 투자 도구로 더 나은 의사결정을 지원합니다.</p></div>', unsafe_allow_html=True)
features = [
    ("↗", "#2185ef", "실시간 주가 정보", "국내외 주요 지수와 종목의 주가를 확인하세요."),
    ("⌕", "#12b989", "종목 검색", "관심 있는 종목을 빠르고 정확하게 검색해보세요."),
    ("▤", "#7750e8", "기업 분석", "재무제표, 공시, 뉴스 등 다양한 데이터를 분석합니다."),
    ("◔", "#fb851b", "포트폴리오 관리", "나만의 포트폴리오를 구성하고 수익률을 관리하세요."),
    ("♧", "#11bfc7", "투자 인사이트", "시장 분석과 리포트로 깊이 있는 인사이트를 얻으세요."),
]
cols = st.columns(5)
for col, (icon, bg, title, text) in zip(cols, features):
    with col:
        st.markdown(f'<div class="card"><div class="icon" style="background:{bg}">{icon}</div><div class="feature-title">{title}</div><div class="feature-text">{text}</div><div style="color:#0878ff;font-size:22px;margin-top:12px">→</div></div>', unsafe_allow_html=True)

# ---------- Market ----------
st.markdown('<div class="section"><p class="eyebrow blue">MARKET SNAPSHOT</p><h2 class="section-title">오늘의 시장 현황</h2></div>', unsafe_allow_html=True)
market = [
    ("코스피", "2,643.21", "▲ 12.34 (+0.47%)", "up"),
    ("코스닥", "859.73", "▲ 5.67 (+0.66%)", "up"),
    ("USD/KRW", "1,385.20", "▼ 2.30 (-0.17%)", "down"),
    ("WTI (원유)", "82.45", "▲ 1.12 (+1.38%)", "up"),
]
cols = st.columns(4)
for col, (name, value, change, cls) in zip(cols, market):
    with col:
        st.markdown(f'<div class="metric-card"><div class="metric-name">{name}</div><div class="metric-value">{value}</div><div class="metric-change {cls}">{change}</div></div>', unsafe_allow_html=True)

# ---------- Chart ----------
st.markdown('<div class="section"><p class="eyebrow blue">MARKET CHART</p><h2 class="section-title">KOSPI 추이</h2><p class="muted">디자인용 샘플 데이터 · 실제 시세 API로 교체할 수 있습니다.</p></div>', unsafe_allow_html=True)
rng = np.random.default_rng(42)
dates = pd.date_range(end=pd.Timestamp.today(), periods=30)
values = 2620 + np.cumsum(rng.normal(0.7, 5.0, 30))
fig = go.Figure(go.Scatter(x=dates, y=values, mode="lines", line={"width":3}, fill="tozeroy"))
fig.update_layout(height=300, margin=dict(l=0,r=0,t=10,b=0), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="white", xaxis_title=None, yaxis_title=None, hovermode="x unified")
fig.update_xaxes(showgrid=False)
fig.update_yaxes(gridcolor="#e4ebf4")
st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

# ---------- News ----------
st.markdown('<div class="section"><p class="eyebrow blue">LATEST NEWS</p><h2 class="section-title">최신 투자 소식</h2></div>', unsafe_allow_html=True)
news = [
    ("시장동향", "코스피, 외국인 매수세에 2,640선 회복", "2시간 전"),
    ("기업분석", "삼성전자, 1분기 실적 기대치 상회 전망", "4시간 전"),
    ("정책이슈", "미국 금리 인하 기대감에 글로벌 증시 상승", "6시간 전"),
    ("투자전략", "반도체 섹터, 하반기 실적 개선 기대", "8시간 전"),
]
left, right = st.columns([1.35, .9])
with left:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    for tag, title, time in news:
        st.markdown(f'<div class="news-item"><span class="tag">{tag}</span>{title}<span style="float:right;color:#99a6b7;font-size:10px">{time}</span></div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
with right:
    st.markdown('<div class="portfolio"><p class="eyebrow blue">MY PORTFOLIO</p><h2 class="section-title">관심종목을 한곳에서</h2><p class="muted">관심 종목과 투자 메모를 모아 나만의 투자 화면으로 확장할 수 있습니다.</p></div>', unsafe_allow_html=True)

st.markdown('<footer>© 2026 StockVista <span style="float:right">주식 정보 서비스 · 투자 판단은 본인의 책임입니다.</span></footer>', unsafe_allow_html=True)
