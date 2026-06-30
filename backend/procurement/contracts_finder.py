"""
contracts_finder.py — UK Contracts Finder API integration.

All UK public sector contracts above £10K are published here.
Free, no auth required.

API: https://www.contractsfinder.service.gov.uk/apidocumentation
"""

import logging
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

CF_API_BASE = "https://www.contractsfinder.service.gov.uk/Published/Notices/OCDS/Search"


def search_uk_contracts(
    keywords: list[str],
    min_value_gbp: Optional[int] = None,
    max_results: int = 15,
) -> list[dict]:
    """
    Search UK Contracts Finder for awarded contracts.

    Args:
        keywords: Search terms (e.g. ["IT services", "cloud migration", "banking"])
        min_value_gbp: Minimum contract value in GBP
        max_results: Max results to return

    Returns:
        List of contract awards with value, winner, scope
    """
    params = {
        "searchCriteria.keyword": " ".join(keywords),
        "searchCriteria.stage": "award",
        "searchCriteria.limit": str(max_results),
    }

    if min_value_gbp:
        params["searchCriteria.valueFrom"] = str(min_value_gbp)

    results = []
    try:
        resp = httpx.get(CF_API_BASE, params=params, timeout=20)

        if resp.status_code == 200:
            data = resp.json()
            releases = data.get("releases", [])

            for release in releases[:max_results]:
                contract = _parse_cf_release(release)
                if contract:
                    results.append(contract)

            logger.info(f"UK Contracts Finder: {len(results)} results for {keywords}")
        else:
            logger.warning(f"Contracts Finder API returned {resp.status_code}")

    except Exception as e:
        logger.warning(f"UK Contracts Finder request failed: {e}")

    return results


def _parse_cf_release(release: dict) -> Optional[dict]:
    """Parse an OCDS release into our standard format."""
    try:
        awards = release.get("awards", [])
        tender = release.get("tender", {})
        buyer = release.get("buyer", {})

        award = awards[0] if awards else {}
        suppliers = award.get("suppliers", [{}])
        winner = suppliers[0] if suppliers else {}

        value = award.get("value", tender.get("value", {}))

        return {
            "source": "UK Contracts Finder",
            "notice_id": release.get("id", ""),
            "title": tender.get("title", release.get("tag", [""])[0] if release.get("tag") else ""),
            "buyer": buyer.get("name", ""),
            "buyer_country": "GB",
            "winner": winner.get("name", ""),
            "winner_country": winner.get("address", {}).get("countryName", "GB"),
            "contract_value_eur": _gbp_to_eur(value.get("amount")) if value.get("amount") else None,
            "contract_value_gbp": value.get("amount"),
            "currency": value.get("currency", "GBP"),
            "publication_date": release.get("date", ""),
            "description": tender.get("description", "")[:200],
        }
    except Exception:
        return None


def _gbp_to_eur(gbp: Optional[float]) -> Optional[float]:
    """Approximate GBP to EUR conversion."""
    if gbp is None:
        return None
    return gbp * 1.17  # Approximate rate
