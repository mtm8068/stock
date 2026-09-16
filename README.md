# StockVista

주식 관련 홈페이지 메인 페이지를 **Python + Streamlit**으로 구현한 프로젝트입니다.

## 구성

- `app.py` — Streamlit 기반 메인 홈페이지
- `requirements.txt` — Python 실행에 필요한 패키지
- `index.html` / `styles.css` / `script.js` — 기존 정적 웹 버전
- `assets/homepage-preview.svg` — 메인 페이지 시각 시안

## Python으로 실행

```bash
pip install -r requirements.txt
streamlit run app.py
```

실행 후 표시되는 로컬 주소를 Chrome에서 열면 됩니다.

## 현재 기능

- StockVista 메인 화면
- 종목 검색 샘플 기능
- KOSPI/KOSDAQ/USD/KRW/WTI 시장 카드
- KOSPI 샘플 차트
- 최신 투자 소식 영역
- 반응형 Streamlit UI

현재 시장 수치와 뉴스는 디자인용 샘플 데이터입니다. 실제 서비스로 사용하려면 주가 API, 기업정보/재무 API, 뉴스 API 등을 연결하면 됩니다.
