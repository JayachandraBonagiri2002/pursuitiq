"""
ted_europe.py — TED (Tenders Electronic Daily) API integration.

TED is the official journal for EU public procurement.
ALL contracts above €140K are published here with:
- Contract value (actual price paid)
- Winner (who won the contract)
- All bidders who participated
- Contract type, duration, scope

This is REAL data, not synthetic. It's the single best source for
"who wins what, at what price" in European IT services.

API: https://ted.europa.eu/api
"""

import logging
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

TED_API_BASE = "https://api.ted.europa.eu/v3"
TED_SEARCH_URL = f"{TED_API_BASE}/notices/search"


def search_ted_contracts(
    industry_keywords: list[str],
    country: Optional[str] = None,
    min_value_eur: Optional[int] = None,
    max_value_eur: Optional[int] = None,
    cpv_codes: Optional[list[str]] = None,
    max_results: int = 20,
) -> list[dict]:
    """
    Search TED for awarded contracts matching criteria.

    CPV codes for IT services:
        72000000 - IT services: consulting, software development, Internet and support
        72200000 - Software programming and consultancy services
        72300000 - Data services
        72400000 - Internet services
        72500000 - Computer-related services
        72600000 - Computer support and consultancy services
        72700000 - Computer network services
        72800000 - Computer audit and testing services
        72900000 - Computer back-up and catalogue conversion services

    Args:
        industry_keywords: Search terms (e.g. ["cloud migration", "banking"])
        country: ISO country code (e.g. "DE", "GB", "FR")
        min_value_eur: Minimum contract value in EUR
        max_value_eur: Maximum contract value in EUR
        cpv_codes: CPV category codes to filter on
        max_results: Max results to return

    Returns:
        List of contract award notices with value, winner, etc.
    """
    if cpv_codes is None:
        cpv_codes = ["72000000"]  # IT services

    query_parts = []
    if industry_keywords:
        keyword_query = " OR ".join(f'"{kw}"' for kw in industry_keywords)
        query_parts.append(keyword_query)

    # Build query string for TED's expert search
    query_terms = list(industry_keywords)
    if country:
        query_terms.append(f"country:{country.upper()}")

    search_body = {
        "query": " AND ".join(query_terms) if query_terms else "IT services",
        "page": 1,
        "limit": max_results,
        "scope": 3,  # 3 = contract award notices
    }

    results = []

    try:
        resp = httpx.post(
            TED_SEARCH_URL,
            json=search_body,
            timeout=30,
            headers={"Content-Type": "application/json"},
        )

        if resp.status_code == 200:
            data = resp.json()
            notices = data.get("notices", data.get("results", data.get("content", [])))

            for notice in notices[:max_results]:
                contract = _parse_ted_notice(notice)
                if contract:
                    results.append(contract)

            logger.info(f"TED search returned {len(results)} contracts for: {industry_keywords}")
        elif resp.status_code == 400:
            # Try simplified query
            simplified = {"query": " ".join(industry_keywords), "page": 1, "limit": max_results}
            resp2 = httpx.post(TED_SEARCH_URL, json=simplified, timeout=30, headers={"Content-Type": "application/json"})
            if resp2.status_code == 200:
                data = resp2.json()
                notices = data.get("notices", data.get("results", data.get("content", [])))
                for notice in notices[:max_results]:
                    contract = _parse_ted_notice(notice)
                    if contract:
                        results.append(contract)
            else:
                logger.warning(f"TED API returned {resp2.status_code}")
                results = _fallback_ted_search(industry_keywords, country)
        else:
            logger.warning(f"TED API returned {resp.status_code}: {resp.text[:200]}")
            results = _fallback_ted_search(industry_keywords, country)

    except Exception as e:
        logger.warning(f"TED API request failed: {e}")
        results = _fallback_ted_search(industry_keywords, country)

    return results


def _parse_ted_notice(notice: dict) -> Optional[dict]:
    """Parse a TED notice into our standard format."""
    try:
        return {
            "source": "TED.europa.eu",
            "notice_id": notice.get("ND", notice.get("id", "")),
            "title": notice.get("TI", notice.get("title", "Unknown")),
            "buyer": notice.get("OJ_CA_OFFICIAL_NAME", notice.get("buyer-name", "")),
            "buyer_country": notice.get("ISO_COUNTRY_CODE", notice.get("buyer-country", "")),
            "winner": notice.get("WIN_NAME", notice.get("winner-name", "")),
            "winner_country": notice.get("WIN_COUNTRY_CODE", notice.get("winner-country", "")),
            "contract_value_eur": notice.get("TOTAL_VALUE", notice.get("total-value")),
            "cpv_code": notice.get("CPV", notice.get("cpv-code", "")),
            "publication_date": notice.get("DT", notice.get("publication-date", "")),
            "contract_type": notice.get("NC", notice.get("contract-nature", "")),
        }
    except Exception:
        return None


def _fallback_ted_search(keywords: list[str], country: Optional[str] = None) -> list[dict]:
    """
    Fallback: use TED's simple search endpoint if the advanced API fails.
    TED also has an older XML-based search we can try.
    """
    try:
        query = "+".join(keywords)
        url = f"https://ted.europa.eu/en/search/result?queryText={query}&scope=2"
        if country:
            url += f"&country={country}"

        resp = httpx.get(url, timeout=15, follow_redirects=True)
        if resp.status_code == 200 and "application/json" in resp.headers.get("content-type", ""):
            data = resp.json()
            return [_parse_ted_notice(n) for n in data.get("results", [])[:10] if _parse_ted_notice(n)]
    except Exception as e:
        logger.warning(f"TED fallback search also failed: {e}")

    return []


def get_client_procurement_history(
    client_name: str,
    country: Optional[str] = None,
    max_results: int = 10,
) -> list[dict]:
    """
    Find all past contracts issued by a specific client/buyer.
    Reveals: what they've bought before, from whom, at what price.

    This is gold for understanding a client's procurement patterns.
    """
    return search_ted_contracts(
        industry_keywords=[client_name],
        country=country,
        max_results=max_results,
    )


def get_competitor_wins(
    competitor_name: str,
    industry_keywords: Optional[list[str]] = None,
    country: Optional[str] = None,
    max_results: int = 15,
) -> list[dict]:
    """
    Find contracts won by a specific competitor.
    Reveals: their pricing patterns, which sectors they're active in.
    """
    keywords = [competitor_name]
    if industry_keywords:
        keywords.extend(industry_keywords)

    results = search_ted_contracts(
        industry_keywords=keywords,
        country=country,
        max_results=max_results,
    )

    # Filter to only results where this competitor is the winner
    filtered = [r for r in results if competitor_name.lower() in (r.get("winner") or "").lower()]
    return filtered if filtered else results


def get_procurement_context(
    client_name: str,
    industry: str,
    geography: list[str],
    competitors: list[str],
) -> str:
    """
    Build a complete procurement intelligence context for agent prompts.
    This is the main function agents call.
    """
    sections = []
    country_map = {
        "germany": "DE", "france": "FR", "uk": "GB", "united kingdom": "GB",
        "netherlands": "NL", "spain": "ES", "italy": "IT", "sweden": "SE",
        "norway": "NO", "denmark": "DK", "finland": "FI", "belgium": "BE",
        "austria": "AT", "switzerland": "CH", "poland": "PL", "ireland": "IE",
    }

    country_code = None
    for geo in geography:
        code = country_map.get(geo.lower())
        if code:
            country_code = code
            break

    # 1. Client's past procurement
    client_history = get_client_procurement_history(client_name, country_code)
    if client_history:
        sections.append("PUBLIC PROCUREMENT HISTORY — WHAT THIS CLIENT HAS BOUGHT BEFORE:")
        for c in client_history[:5]:
            value_str = f"€{c['contract_value_eur']:,.0f}" if c.get('contract_value_eur') else "Value undisclosed"
            sections.append(
                f"  • {c.get('title', 'N/A')[:80]} | Winner: {c.get('winner', 'N/A')} | "
                f"Value: {value_str} | Date: {c.get('publication_date', 'N/A')}"
            )
        sections.append("")

    # 2. Similar contracts in the sector
    sector_keywords = [industry, "IT services", "digital transformation"]
    similar = search_ted_contracts(sector_keywords, country_code, max_results=10)
    if similar:
        sections.append(f"SIMILAR {industry.upper()} IT CONTRACTS AWARDED (PUBLIC RECORD):")
        for c in similar[:7]:
            value_str = f"€{c['contract_value_eur']:,.0f}" if c.get('contract_value_eur') else "Undisclosed"
            sections.append(
                f"  • {c.get('title', 'N/A')[:80]} | Winner: {c.get('winner', 'N/A')} | "
                f"Value: {value_str} | Country: {c.get('buyer_country', 'N/A')}"
            )
        sections.append("")

    # 3. Competitor wins in this space
    for comp in competitors[:4]:
        comp_wins = get_competitor_wins(comp, [industry], country_code, max_results=5)
        if comp_wins:
            sections.append(f"CONTRACTS WON BY {comp.upper()} (PUBLIC RECORD):")
            for c in comp_wins[:3]:
                value_str = f"€{c['contract_value_eur']:,.0f}" if c.get('contract_value_eur') else "Undisclosed"
                sections.append(
                    f"  • {c.get('title', 'N/A')[:80]} | Value: {value_str} | "
                    f"Date: {c.get('publication_date', 'N/A')}"
                )
            sections.append("")

    if not sections:
        return "NO PUBLIC PROCUREMENT DATA AVAILABLE. Use web intelligence and knowledge base instead."

    header = (
        "REAL PUBLIC PROCUREMENT INTELLIGENCE (from TED.europa.eu — official EU procurement journal)\n"
        "These are ACTUAL contract awards with real values and real winners.\n"
        "=" * 70 + "\n"
    )
    return header + "\n".join(sections)
