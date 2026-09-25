import time
import pandas as pd
import streamlit as st

from kis_api import KISClient, to_number


def _fmt_money(value):
    n = to_number(value)
    if n >= 1e12:
        return f"{n/1e12:,.2f}조원"
    if n >= 1e8:
        return f"{n/1e8:,.1f}억원"
    return f"{n:,.0f}원"


def _pick(row, keys):
    for key in keys:
        if row.get(key) not in (None, ""):
            return row.get(key)
    return None


def render_kis_panel(client: KISClient, symbol: str):
    @st.fragment(run_every=1.0)
    def panel():
        try:
            quote = client.current_price(symbol)
            book = client.orderbook(symbol)
        except Exception as exc:
            st.error(f"KIS 시세 조회 실패: {exc}")
            return

        price = to_number(quote.get("stck_prpr"))
        change = to_number(quote.get("prdy_vrss"))
        pct = to_number(quote.get("prdy_ctrt"))
        strength = to_number(quote.get("cttr"))
        turnover = to_number(quote.get("acml_tr_pbmn"))
        volume = int(to_number(quote.get("acml_vol")))

        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("KIS 현재가", f"{price:,.0f}원", f"{change:+,.0f} ({pct:+.2f}%)")
        c2.metric("체결강도", f"{strength:.2f}%")
        c3.metric("누적 거래량", f"{volume:,}")
        c4.metric("실시간 거래대금", _fmt_money(turnover))
        c5.metric("갱신", time.strftime("%H:%M:%S"))

        left, right = st.columns([1.15, 1])
        with left:
            rows = []
            for i in range(1, 11):
                rows.append({
                    "단계": i,
                    "매도호가": to_number(book.get(f"askp{i}")),
                    "매도잔량": int(to_number(book.get(f"askp_rsqn{i}"))),
                    "매수호가": to_number(book.get(f"bidp{i}")),
                    "매수잔량": int(to_number(book.get(f"bidp_rsqn{i}"))),
                })
            st.markdown("**10호가 실시간 잔량**")
            st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
            st.caption(
                f"총 매도잔량 {int(to_number(book.get('total_askp_rsqn'))):,} · "
                f"총 매수잔량 {int(to_number(book.get('total_bidp_rsqn'))):,}"
            )

        with right:
            st.markdown("**외국인·기관 수급**")
            now = time.time()
            if now - st.session_state.get("kis_investor_at", 0) > 30:
                try:
                    st.session_state.kis_investor_rows = client.investor_estimate(symbol)
                    st.session_state.kis_investor_at = now
                except Exception as exc:
                    st.session_state.kis_investor_rows = []
                    st.session_state.kis_investor_error = str(exc)

            rows = st.session_state.get("kis_investor_rows", [])
            if rows:
                latest = rows[-1]
                fqty = _pick(latest, ["frgn_ntby_qty", "frgn_ntby_qty1", "frgn_ntby"])
                iqty = _pick(latest, ["orgn_ntby_qty", "orgn_ntby_qty1", "orgn_ntby"])
                a, b = st.columns(2)
                a.metric("외국인 순매수", f"{to_number(fqty):,.0f}주")
                b.metric("기관 순매수", f"{to_number(iqty):,.0f}주")
                st.dataframe(pd.DataFrame(rows[-5:]), hide_index=True, use_container_width=True)
                st.caption("장중 추정 수급은 증권사 집계 시각에 갱신되며 최종 확정 수급과 다를 수 있습니다.")
            else:
                st.info("장중 추정 수급 데이터가 아직 없습니다.")

        st.caption("KIS 연결은 국내주식 시장데이터 조회 전용입니다. 주문 기능은 연결하지 않았습니다.")

    panel()
