import time
from typing import Any

import requests

REAL_REST = "https://openapi.koreainvestment.com:9443"
PAPER_REST = "https://openapivts.koreainvestment.com:29443"


class KISClient:
    """한국투자증권 국내주식 시장데이터 전용 REST 클라이언트."""

    def __init__(self, appkey: str, appsecret: str, paper: bool = False):
        self.appkey = appkey
        self.appsecret = appsecret
        self.paper = paper
        self.rest = PAPER_REST if paper else REAL_REST
        self._token = None
        self._token_expiry = 0.0

    def access_token(self) -> str:
        if self._token and time.time() < self._token_expiry - 60:
            return self._token
        response = requests.post(
            f"{self.rest}/oauth2/tokenP",
            headers={"content-type": "application/json; charset=UTF-8"},
            json={
                "grant_type": "client_credentials",
                "appkey": self.appkey,
                "appsecret": self.appsecret,
            },
            timeout=10,
        )
        response.raise_for_status()
        body = response.json()
        if not body.get("access_token"):
            raise RuntimeError(body.get("msg1") or "KIS 접근토큰 발급 실패")
        self._token = body["access_token"]
        self._token_expiry = time.time() + int(body.get("expires_in", 86400))
        return self._token

    def get(self, path: str, tr_id: str, params: dict[str, str]) -> dict[str, Any]:
        response = requests.get(
            f"{self.rest}{path}",
            headers={
                "content-type": "application/json; charset=UTF-8",
                "authorization": f"Bearer {self.access_token()}",
                "appkey": self.appkey,
                "appsecret": self.appsecret,
                "tr_id": tr_id,
                "custtype": "P",
            },
            params=params,
            timeout=10,
        )
        response.raise_for_status()
        body = response.json()
        if body.get("rt_cd") not in (None, "0"):
            raise RuntimeError(f"{body.get('msg_cd', '')} {body.get('msg1', '')}".strip())
        return body

    def current_price(self, symbol: str) -> dict[str, Any]:
        body = self.get(
            "/uapi/domestic-stock/v1/quotations/inquire-price",
            "FHKST01010100",
            {"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": symbol},
        )
        return body.get("output") or {}

    def orderbook(self, symbol: str) -> dict[str, Any]:
        body = self.get(
            "/uapi/domestic-stock/v1/quotations/inquire-asking-price-exp-ccn",
            "FHKST01010200",
            {"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": symbol},
        )
        return body.get("output1") or {}

    def investor_estimate(self, symbol: str) -> list[dict[str, Any]]:
        body = self.get(
            "/uapi/domestic-stock/v1/quotations/investor-trend-estimate",
            "HHPTJ04160200",
            {"MKSC_SHRN_ISCD": symbol},
        )
        return body.get("output2") or []

    def investor_daily(self, symbol: str) -> list[dict[str, Any]]:
        body = self.get(
            "/uapi/domestic-stock/v1/quotations/inquire-investor",
            "FHKST01010900",
            {"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": symbol},
        )
        return body.get("output") or []


def to_number(value: Any, default: float = 0.0) -> float:
    try:
        if value in (None, ""):
            return default
        return float(str(value).replace(",", ""))
    except (TypeError, ValueError):
        return default
