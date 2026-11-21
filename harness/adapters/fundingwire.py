"""FundingWire: match the domain to a company, then read that company's newest funding rounds."""
from __future__ import annotations

from typing import Any

from ..http_client import Response
from ..models import Answer, Company
from ..question import funding_fields
from ._common import DataApiAdapter, envelope

API_URL = "https://oia5pwm9y8.execute-api.us-east-1.amazonaws.com/prod"
UNNAMED_STAGES = {"", "unspecified"}


def _body(response: Response) -> dict[str, Any]:
    return response.body if isinstance(response.body, dict) else {}


def _failure(response: Response) -> tuple[str, str] | None:
    """None for a 2xx response. Every other status is an error: these routes answer 404 only when the API is off."""
    if response.ok:
        return None
    error = _body(response).get("error")
    detail = (error.get("code") or error.get("message")) if isinstance(error, dict) else error
    return "error", f"HTTP {response.status}" + (f": {detail}" if detail else "")


def _credits(*responses: Response) -> float | None:
    """The credits each response reports it charged (`billing.credits_charged`), summed."""
    charged = []
    for response in responses:
        billing = _body(response).get("billing")
        value = billing.get("credits_charged") if isinstance(billing, dict) else None
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            charged.append(value)
    return sum(charged) if charged else None


def _latest(rounds: list[dict[str, Any]]) -> dict[str, Any]:
    """The newest round. On the newest date, a round with a named stage wins over an undisclosed one."""
    rows = sorted(rounds, key=lambda row: str(row.get("funding_date") or ""), reverse=True)
    newest_day = str(rows[0].get("funding_date") or "")[:10]
    same_day = [row for row in rows if str(row.get("funding_date") or "")[:10] == newest_day]
    named = [row for row in same_day if str(row.get("round") or "").strip().lower() not in UNNAMED_STAGES]
    return (named or same_day)[0]


class FundingWire(DataApiAdapter):
    def lookup(self, company: Company) -> Answer:
        headers = {"X-API-Key": self.key("FUNDINGWIRE_API_KEY"), "Accept": "application/json"}
        matched = self.get(f"{API_URL}/v1/companies", headers=headers, params={"domain": company.domain, "limit": 5})
        raw: dict[str, Any] = {"match": envelope(matched)}
        failure = _failure(matched)
        if failure:
            return self.answer(company, failure[0], error=failure[1], latency_ms=matched.latency_ms, raw=raw)
        companies = [row for row in _body(matched).get("data") or [] if isinstance(row, dict) and row.get("id")]
        if not companies:
            units = _credits(matched)
            return self.answer(company, "not_found", error="no company for domain", latency_ms=matched.latency_ms,
                               cost_units=units, cost_unit="credit" if units is not None else None, raw=raw)
        rounds = self.get(f"{API_URL}/v1/funding-rounds", headers=headers,
                          params={"company_id": ",".join(str(row["id"]) for row in companies), "limit": 5,
                                  "sort": "funding_date"})
        raw["funding_enrichment"] = envelope(rounds)
        latency = matched.latency_ms + rounds.latency_ms
        units = _credits(matched, rounds)
        unit = "credit" if units is not None else None
        failure = _failure(rounds)
        if failure:
            return self.answer(company, failure[0], error=failure[1], latency_ms=latency,
                               cost_units=units, cost_unit=unit, raw=raw)
        body = _body(rounds)
        rows = [row for row in body.get("data") or [] if isinstance(row, dict)]
        if not rows:
            return self.answer(company, "not_found", error="no funding rounds", latency_ms=latency,
                               cost_units=units, cost_unit=unit, raw=raw)
        latest = _latest(rows)
        total = companies[0].get("total_funding_usd")
        meta = body.get("meta") if isinstance(body.get("meta"), dict) else {}
        normalized = {
            "latest_stage": latest.get("round"),
            "latest_date": latest.get("funding_date"),
            "latest_amount": latest.get("usd_amount"),
            "total_raised": total if isinstance(total, (int, float)) and total > 0 else None,
            "round_count": meta.get("total") if isinstance(meta.get("total"), int) else len(rows),
        }
        if str(normalized["latest_stage"] or "").strip().lower() in UNNAMED_STAGES:
            normalized["latest_stage"] = None  # FundingWire's label for an undisclosed round type
        return self.answer(company, "ok", funding_fields(normalized), latency_ms=latency,
                           cost_units=units, cost_unit=unit, raw=raw)


def build(setup: str, spec: dict[str, Any], env: list[str]) -> FundingWire:
    return FundingWire(setup, spec, env)
