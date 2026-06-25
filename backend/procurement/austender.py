"""
austender.py — AusTender (Australia) procurement data integration.

AusTender publishes all Australian Government contracts above AUD $10K.
Covers IT services, consulting, infrastructure, and more.

Primary search: https://www.tenders.gov.au/Search/
Fallback open data: https://data.gov.au/data/api/3/action/datastore_search

Free, no auth required.
"""

import logging
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

AUSTENDER_SEARCH_URL = "https://www.tenders.gov.au/Search/Search"
AUSTENDER_CN_URL = "https://www.tenders.gov.au/cn/search"
DATA_GOV_AU_API = "https://data.gov.au/data/api/3/action/datastore_search"

# AusTender contract notice resource IDs on data.gov.au
# These are the open data datasets for CN (Contract Notices)
CN_RESOURCE_ID = "d40a0896-c9e8-43d4-9a49-a4a3b7b5b4a5"

AUD_TO_EUR_RATE = 0.61


def search_au_contracts(
    keywords: list[str],
    min_value_aud: int | None = None,
    max_results: int = 15,
) -> list[dict]:
    """
    Search AusTender for awarded contracts matching criteria.

    Args:
        keywords: Search terms (e.g. ["IT services", "cloud", "cybersecurity"])
        min_value_aud: Minimum contract value in AUD
        max_results: Max results to return

    Returns:
        List of contract awards with value, winner, buyer details.
    """
    results = _search_austender_primary(keywords, min_value_aud, max_results)

    if not results:
        logger.info("AusTender primary search returned no results, trying data.gov.au fallback")
        results = _search_data_gov_au_fallback(keywords, min_value_aud, max_results)

    return results


def get_vendor_au_contracts(
    vendor_name: str,
    max_results: int = 10,
) -> list[dict]:
    """
    Find Australian Government contracts awarded to a specific vendor.
    Reveals competitor pricing patterns in Australian government space.

    Args:
        vendor_name: Name of the vendor/supplier to search for
        max_results: Max results to return

    Returns:
        List of contracts awarded to this vendor.
    """
    results = _search_austender_primary([vendor_name], None, max_results)

    if not results:
        results = _search_data_gov_au_fallback([vendor_name], None, max_results)

    # Filter to only results where this vendor is the winner
    filtered = [
        r for r in results
        if vendor_name.lower() in (r.get("winner") or "").lower()
    ]

    return filtered if filtered else results[:max_results]


def _search_austender_primary(
    keywords: list[str],
    min_value_aud: int | None,
    max_results: int,
) -> list[dict]:
    """Search AusTender via the primary web search endpoint."""
    params = {
        "SearchFrom": "CN",
        "Type": "CN",
        "keyword": " ".join(keywords),
        "AgencyStatus": "0",
        "DateType": "Publish Date",
        "PageNumber": "1",
        "PageSize": str(max_results),
    }

    if min_value_aud:
        params["ValueFrom"] = str(min_value_aud)

    results = []
    try:
        resp = httpx.get(
            AUSTENDER_CN_URL,
            params=params,
            timeout=20,
            headers={
                "Accept": "application/json",
                "User-Agent": "PursuitIQ/1.0 (Research Tool)",
            },
            follow_redirects=True,
        )

        if resp.status_code == 200:
            content_type = resp.headers.get("content-type", "")
            if "application/json" in content_type:
                data = resp.json()
                notices = data.get("results", data.get("items", data.get("data", [])))
                for notice in notices[:max_results]:
                    contract = _parse_austender_notice(notice)
                    if contract:
                        results.append(contract)
                logger.info(f"AusTender: {len(results)} contracts for {keywords}")
            else:
                logger.info("AusTender returned non-JSON response, trying fallback")
        else:
            logger.warning(f"AusTender returned {resp.status_code}")

    except Exception as e:
        logger.warning(f"AusTender primary search failed: {e}")

    return results


def _search_data_gov_au_fallback(
    keywords: list[str],
    min_value_aud: int | None,
    max_results: int,
) -> list[dict]:
    """
    Fallback: search via data.gov.au open data API.
    Uses CKAN datastore_search for contract notices.
    """
    query = " ".join(keywords)

    params = {
        "resource_id": CN_RESOURCE_ID,
        "q": query,
        "limit": max_results,
    }

    if min_value_aud:
        params["filters"] = f'{{"Value":"{min_value_aud}"}}'

    results = []
    try:
        resp = httpx.get(
            DATA_GOV_AU_API,
            params=params,
            timeout=20,
            headers={"User-Agent": "PursuitIQ/1.0 (Research Tool)"},
        )

        if resp.status_code == 200:
            data = resp.json()
            if data.get("success"):
                records = data.get("result", {}).get("records", [])
                for record in records[:max_results]:
                    contract = _parse_data_gov_au_record(record)
                    if contract:
                        results.append(contract)
                logger.info(f"data.gov.au fallback: {len(results)} contracts for {keywords}")
            else:
                logger.warning("data.gov.au returned success=false")
        else:
            logger.warning(f"data.gov.au API returned {resp.status_code}")

    except Exception as e:
        logger.warning(f"data.gov.au fallback search failed: {e}")

    return results


def _parse_austender_notice(notice: dict) -> Optional[dict]:
    """Parse an AusTender notice into our standard format."""
    try:
        value_aud = notice.get("Value", notice.get("value", notice.get("contract_value")))
        if isinstance(value_aud, str):
            value_aud = float(value_aud.replace(",", "").replace("$", "")) if value_aud else None
        elif isinstance(value_aud, (int, float)):
            pass
        else:
            value_aud = None

        return {
            "source": "AusTender",
            "notice_id": notice.get("CN_ID", notice.get("id", notice.get("CNID", ""))),
            "title": notice.get("Title", notice.get("title", notice.get("Description", ""))),
            "buyer": notice.get("Agency", notice.get("agency", notice.get("AgencyName", ""))),
            "buyer_country": "AU",
            "winner": notice.get(
                "Supplier_Name",
                notice.get("supplier_name", notice.get("SupplierName", "")),
            ),
            "contract_value_aud": value_aud,
            "contract_value_eur": _aud_to_eur(value_aud),
            "publication_date": notice.get(
                "Publish_Date",
                notice.get("publish_date", notice.get("PublishDate", "")),
            ),
            "category": notice.get("Category", notice.get("category", "")),
        }
    except Exception:
        return None


def _parse_data_gov_au_record(record: dict) -> Optional[dict]:
    """Parse a data.gov.au CKAN record into our standard format."""
    try:
        value_aud = record.get("Value", record.get("Contract_Value"))
        if isinstance(value_aud, str):
            value_aud = float(value_aud.replace(",", "").replace("$", "")) if value_aud else None
        elif isinstance(value_aud, (int, float)):
            pass
        else:
            value_aud = None

        return {
            "source": "AusTender",
            "notice_id": record.get("CN_ID", record.get("_id", "")),
            "title": record.get("Title", record.get("Description", "")),
            "buyer": record.get("Agency", record.get("Agency_Name", "")),
            "buyer_country": "AU",
            "winner": record.get("Supplier_Name", record.get("Supplier", "")),
            "contract_value_aud": value_aud,
            "contract_value_eur": _aud_to_eur(value_aud),
            "publication_date": record.get("Publish_Date", record.get("Start_Date", "")),
            "category": record.get("Category", record.get("UNSPSC_Title", "")),
        }
    except Exception:
        return None


def _aud_to_eur(aud: float | int | None) -> float | None:
    """Convert AUD to EUR at approximate rate."""
    if aud is None:
        return None
    return round(float(aud) * AUD_TO_EUR_RATE, 2)
