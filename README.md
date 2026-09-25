# Stock Insight

Python + Streamlit + yfinance + Plotly 기반 주식 대시보드입니다.

## 기능
- 국내/미국 주식 가격과 차트
- 캔들/라인 차트, 20일/60일 이동평균, 거래량
- 기업/재무 정보와 관련 뉴스
- 종목 검색 및 상세 페이지
- Supabase 이메일 회원가입/로그인/로그아웃
- 사용자별 관심종목 추가/삭제/조회
- Supabase Row Level Security(RLS)로 사용자별 데이터 분리

## Supabase 설정

현재 연결된 Supabase 프로젝트:
- Project: `stock`
- URL: `https://wtwvxelfpfbhfcpxkvyn.supabase.co`

로컬에서는 프로젝트 루트에 `.streamlit/secrets.toml`을 만들고 아래처럼 설정하세요.

```toml
SUPABASE_URL = "https://wtwvxelfpfbhfcpxkvyn.supabase.co"
SUPABASE_KEY = "YOUR_SUPABASE_PUBLISHABLE_KEY"
```

실제 publishable key는 GitHub에 커밋하지 마세요. Streamlit Cloud를 사용하는 경우 앱의 Secrets 설정에 같은 두 값을 등록하면 됩니다.

Supabase Auth에서 이메일 확인을 켜면 회원가입 후 인증 메일을 확인한 뒤 로그인해야 합니다.

## 실행

```bash
pip install -r requirements.txt
streamlit run app.py
```
