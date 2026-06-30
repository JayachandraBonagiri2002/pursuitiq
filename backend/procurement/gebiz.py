"""
gebiz.py — GeBIZ (Singapore) government procurement data integration.

GeBIZ is the Singapore Government's one-stop e-procurement portal.
Open data is available via data.gov.sg.

All Singapore Government ministries and agencies use GeBIZ for procurement.
Covers IT services, consulting, infrastructure, and all government purchases.

API: https://data.gov.sg/api/action/datastore_search
"""

import logging
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

DATA_GOV_SG_API = "https://data.gov.sg/api/action/datastore_search"

# GeBIZ procurement data resource IDs on data.gov.sg
# Government procurement (awarded contracts)
GEBIZ_AWARDED_RESOURCE_ID = "d_9db67af2361f26acdb84c25e45017382"

SGD_TO_EUR_RATE = 0.69


def search_sg_contracts(
    keywords: list[str],
    max_results: int = 15,
) -> list[dict]:
    """
    Search GeBIZ (Singapore) for awarded government contracts.

    Args:
        keywords: Search terms (e.g. ["IT services", "cloud", "digital"])
        max_results: Max results to return

    Returns:
        List of contract awards with value, winner, buyer details.
    """
    results = _search_gebiz_primary(keywords, max_results)

    if not results:
        logger.info("GeBIZ primary search returned no results, trying alternate resource")
        results = _search_gebiz_alternate(keywords, max_results)

    return results


def _search_gebiz_primary(
    keywords: list[str],
    max_results: int,
) -> list[dict]:
    """Search GeBIZ via data.gov.sg datastore API."""
    query = " ".join(keywords)

    params = {
        "resource_id": GEBIZ_AWARDED_RESOURCE_ID,
        "q": query,
        "limit": max_results,
    }

    results = []
    try:
        resp = httpx.get(
            DATA_GOV_SG_API,
            params=params,
            timeout=20,
            headers={
                "User-Agent": "PursuitIQ/1.0 (Research Tool)",
                "Accept": "application/json",
            },
        )

        if resp.status_code == 200:
            data = resp.json()
            if data.get("success"):
                records = data.get("result", {}).get("records", [])
                for record in records[:max_results]:
                    contract = _parse_gebiz_record(record)
                    if contract:
                        results.append(contract)
                logger.info(f"GeBIZ: {len(results)} contracts for {keywords}")
            else:
                logger.warning(f"GeBIZ API returned success=false: {data.get('error', {})}")
        else:
            logger.warning(f"GeBIZ API returned {resp.status_code}")

    except Exception as e:
        logger.warning(f"GeBIZ search failed: {e}")

    return results


def _search_gebiz_alternate(
    keywords: list[str],
    max_results: int,
) -> list[dict]:
    """
    Alternate search using a different data.gov.sg endpoint format.
    data.gov.sg has updated their API format over time.
    """
    query = " ".join(keywords)

    # Try the newer datasets API format
    url = "https://api-production.data.gov.sg/v2/public/api/datasets"

    results = []
    try:
        # Search for GeBIZ datasets
        resp = httpx.get(
            f"{DATA_GOV_SG_API}",
            params={
                "resource_id": GEBIZ_AWARDED_RESOURCE_ID,
                "q": query,
                "limit": max_results,
                "sort": "award_date desc",
            },
            timeout=20,
            headers={"User-Agent": "PursuitIQ/1.0 (Research Tool)"},
        )

        if resp.status_code == 200:
            data = resp.json()
            if data.get("success"):
                records = data.get("result", {}).get("records", [])
                for record in records[:max_results]:
                    contract = _parse_gebiz_record(record)
                    if contract:
                        results.append(contract)
                logger.info(f"GeBIZ alternate: {len(results)} contracts for {keywords}")
        else:
            logger.warning(f"GeBIZ alternate search returned {resp.status_code}")

    except Exception as e:
        logger.warning(f"GeBIZ alternate search failed: {e}")

    return results


def _parse_gebiz_record(record: dict) -> Optional[dict]:
    """Parse a GeBIZ record from data.gov.sg into our standard format."""
    try:
        # GeBIZ data fields vary by dataset version
        value_sgd = record.get(
            "awarded_amt",
            record.get("award_price", record.get("contract_value", record.get("awarded_value"))),
        )
        if isinstance(value_sgd, str):
            # Clean currency string: remove $, commas, SGD prefix
            cleaned = value_sgd.replace(",", "").replace("$", "").replace("SGD", "").strip()
            value_sgd = float(cleaned) if cleaned else None
        elif isinstance(value_sgd, (int, float)):
            pass
        else:
            value_sgd = None

        # Extract supplier/winner name
        winner = record.get(
            "supplier_name",
            record.get(
                "awarded_to",
                record.get("awardee", record.get("company_name", "")),
            ),
        )

        # Extract buyer/agency
        buyer = record.get(
            "agency",
            record.get(
                "procurement_entity",
                record.get("ministry", record.get("organisation", "")),
            ),
        )

        # Extract title/description
        title = record.get(
            "tender_description",
            record.get(
                "title",
                record.get("description", record.get("tender_no", "")),
            ),
        )

        # Extract notice/tender ID
        notice_id = record.get(
            "tender_no",
            record.get(
                "reference_no",
                record.get("id", record.get("_id", "")),
            ),
        )

        # Extract publication/award date
        pub_date = record.get(
            "award_date",
            record.get(
                "awarded_date",
                record.get("publish_date", record.get("tender_closing_date", "")),
            ),
        )

        return {
            "source": "GeBIZ Singapore",
            "notice_id": str(notice_id),
            "title": str(title)[:200] if title else "",
            "buyer": str(buyer) if buyer else "",
            "buyer_country": "SG",
            "winner": str(winner) if winner else "",
            "contract_value_sgd": value_sgd,
            "contract_value_eur": _sgd_to_eur(value_sgd),
            "publication_date": str(pub_date) if pub_date else "",
        }
    except Exception:
        return None


def _sgd_to_eur(sgd: float | int | None) -> float | None:
    """Convert SGD to EUR at approximate rate."""
    if sgd is None:
        return None
    return round(float(sgd) * SGD_TO_EUR_RATE, 2)
