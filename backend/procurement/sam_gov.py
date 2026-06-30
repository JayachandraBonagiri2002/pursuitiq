"""
sam_gov.py — US Federal procurement data (SAM.gov / USASpending.gov).

USASpending.gov has ALL US federal contract awards.
Free, no auth, comprehensive API.

API: https://api.usaspending.gov/
"""

import logging
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

USA_SPENDING_BASE = "https://api.usaspending.gov/api/v2"


def search_us_contracts(
    keywords: list[str],
    naics_codes: Optional[list[str]] = None,
    min_value_usd: Optional[int] = None,
    max_results: int = 15,
) -> list[dict]:
    """
    Search USASpending.gov for federal contract awards.

    NAICS codes for IT services:
        541511 - Custom Computer Programming Services
        541512 - Computer Systems Design Services
        541513 - Computer Facilities Management Services
        541519 - Other Computer Related Services
        518210 - Data Processing, Hosting, and Related Services

    Args:
        keywords: Search terms
        naics_codes: NAICS industry codes (default: IT services)
        min_value_usd: Minimum award amount
        max_results: Max results

    Returns:
        List of contract awards
    """
    if naics_codes is None:
        naics_codes = ["541512"]  # Computer Systems Design Services

    search_body = {
        "filters": {
            "keywords": keywords,
            "award_type_codes": ["A", "B", "C", "D"],
            "time_period": [{"start_date": "2024-01-01", "end_date": "2026-12-31"}],
        },
        "fields": [
            "Award ID", "Recipient Name", "Description",
            "Award Amount", "Awarding Agency", "Period of Performance Start Date",
            "NAICS Code",
        ],
        "limit": max_results,
        "page": 1,
        "sort": "Award Amount",
        "order": "desc",
    }

    results = []
    try:
        resp = httpx.post(
            f"{USA_SPENDING_BASE}/search/spending_by_award/",
            json=search_body,
            timeout=20,
        )

        if resp.status_code == 200:
            data = resp.json()
            for award in data.get("results", [])[:max_results]:
                contract = {
                    "source": "USASpending.gov",
                    "notice_id": award.get("Award ID", ""),
                    "title": award.get("Description", "")[:100],
                    "buyer": award.get("Awarding Agency", ""),
                    "buyer_country": "US",
                    "winner": award.get("Recipient Name", ""),
                    "winner_country": "US",
                    "contract_value_usd": award.get("Award Amount"),
                    "contract_value_eur": (award.get("Award Amount") or 0) * 0.92,
                    "publication_date": award.get("Period of Performance Start Date", ""),
                    "naics_code": award.get("NAICS Code", ""),
                }
                results.append(contract)

            logger.info(f"USASpending: {len(results)} contracts for {keywords}")
        else:
            logger.warning(f"USASpending API returned {resp.status_code}")

    except Exception as e:
        logger.warning(f"USASpending request failed: {e}")

    return results


def get_vendor_federal_contracts(
    vendor_name: str,
    max_results: int = 10,
) -> list[dict]:
    """
    Find all federal contracts awarded to a specific vendor.
    Reveals competitor pricing patterns in US government space.
    """
    search_body = {
        "filters": {
            "recipient_search_text": [vendor_name],
            "award_type_codes": ["A", "B", "C", "D"],
        },
        "fields": [
            "Award ID", "Recipient Name", "Description",
            "Award Amount", "Awarding Agency", "Period of Performance Start Date",
        ],
        "limit": max_results,
        "page": 1,
        "sort": "Award Amount",
        "order": "desc",
    }

    results = []
    try:
        resp = httpx.post(
            f"{USA_SPENDING_BASE}/search/spending_by_award/",
            json=search_body,
            timeout=20,
        )

        if resp.status_code == 200:
            data = resp.json()
            for award in data.get("results", [])[:max_results]:
                results.append({
                    "source": "USASpending.gov",
                    "title": award.get("Description", "")[:100],
                    "buyer": award.get("Awarding Agency", ""),
                    "winner": award.get("Recipient Name", ""),
                    "contract_value_usd": award.get("Award Amount"),
                    "publication_date": award.get("Period of Performance Start Date", ""),
                })

    except Exception as e:
        logger.warning(f"USASpending vendor search failed: {e}")

    return results
