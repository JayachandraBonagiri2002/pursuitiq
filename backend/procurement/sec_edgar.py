"""
SEC EDGAR Financial Intelligence Module
========================================
Pulls real financial data from SEC EDGAR (free, no auth required) for
public IT services companies.

API references:
  - Full-text search: https://efts.sec.gov/LATEST/search-index?q=
  - Company submissions: https://data.sec.gov/submissions/CIK{number}.json
  - Company facts: https://data.sec.gov/api/xbrl/companyfacts/CIK{number}.json

SEC EDGAR requires a User-Agent header with contact info per their fair-use policy.
"""

import logging
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SEC_EDGAR_USER_AGENT = "PursuitIQ/2.0 (hackathon@hcltech.com)"

SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik}.json"
COMPANY_FACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"

# CIK numbers for major IT services competitors (zero-padded to 10 digits)
COMPETITOR_CIKS: dict[str, str] = {
    "accenture": "0001281761",
    "ibm": "0000051143",
    "cognizant": "0001058290",
    "infosys": "0001067491",
    "wipro": "0001107508",
}

HEADERS = {
    "User-Agent": SEC_EDGAR_USER_AGENT,
    "Accept": "application/json",
}

REQUEST_TIMEOUT = 20.0  # seconds


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _normalize_name(name: str) -> str:
    """Normalize company name to match COMPETITOR_CIKS keys."""
    return name.strip().lower().replace(" ", "")


def _fetch_submissions(cik: str) -> Optional[dict]:
    """Fetch company submission data from SEC EDGAR."""
    url = SUBMISSIONS_URL.format(cik=cik)
    try:
        response = httpx.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as e:
        logger.warning("SEC EDGAR submissions HTTP error for CIK %s: %s", cik, e)
    except httpx.RequestError as e:
        logger.warning("SEC EDGAR submissions request error for CIK %s: %s", cik, e)
    except Exception as e:
        logger.warning("Unexpected error fetching submissions for CIK %s: %s", cik, e)
    return None


def _fetch_company_facts(cik: str) -> Optional[dict]:
    """Fetch XBRL company facts (financial data) from SEC EDGAR."""
    url = COMPANY_FACTS_URL.format(cik=cik)
    try:
        response = httpx.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as e:
        logger.warning("SEC EDGAR company facts HTTP error for CIK %s: %s", cik, e)
    except httpx.RequestError as e:
        logger.warning("SEC EDGAR company facts request error for CIK %s: %s", cik, e)
    except Exception as e:
        logger.warning("Unexpected error fetching company facts for CIK %s: %s", cik, e)
    return None


def _get_latest_filings(submissions: dict, form_types: list[str], count: int = 5) -> list[dict]:
    """Extract the most recent filings of given form types from submission data."""
    filings: list[dict] = []
    recent = submissions.get("filings", {}).get("recent", {})
    if not recent:
        return filings

    forms = recent.get("form", [])
    dates = recent.get("filingDate", [])
    accession_numbers = recent.get("accessionNumber", [])
    primary_docs = recent.get("primaryDocument", [])

    for i, form in enumerate(forms):
        if form in form_types and i < len(dates):
            filings.append({
                "form": form,
                "filing_date": dates[i] if i < len(dates) else None,
                "accession_number": accession_numbers[i] if i < len(accession_numbers) else None,
                "primary_document": primary_docs[i] if i < len(primary_docs) else None,
            })
            if len(filings) >= count:
                break

    return filings


def _extract_latest_value(facts: dict, taxonomy: str, concept: str, unit: str = "USD") -> Optional[float]:
    """
    Extract the most recent reported value for a given XBRL concept.
    Looks in us-gaap or ifrs-full taxonomies.
    """
    try:
        concept_data = facts.get("facts", {}).get(taxonomy, {}).get(concept, {})
        units = concept_data.get("units", {})
        values = units.get(unit, [])
        if not values:
            return None
        # Sort by end date descending, take the most recent
        sorted_values = sorted(values, key=lambda x: x.get("end", ""), reverse=True)
        if sorted_values:
            val = sorted_values[0].get("val")
            return float(val) if val is not None else None
    except (KeyError, TypeError, ValueError) as e:
        logger.debug("Could not extract %s/%s: %s", taxonomy, concept, e)
    return None


def _extract_financials_from_facts(facts: dict) -> dict:
    """Extract key financial metrics from XBRL company facts."""
    financials: dict = {}

    # Try US-GAAP first, then IFRS
    revenue = (
        _extract_latest_value(facts, "us-gaap", "Revenues")
        or _extract_latest_value(facts, "us-gaap", "RevenueFromContractWithCustomerExcludingAssessedTax")
        or _extract_latest_value(facts, "us-gaap", "SalesRevenueNet")
        or _extract_latest_value(facts, "ifrs-full", "Revenue")
    )
    if revenue:
        financials["revenue_usd"] = revenue

    operating_income = (
        _extract_latest_value(facts, "us-gaap", "OperatingIncomeLoss")
        or _extract_latest_value(facts, "ifrs-full", "ProfitLossFromOperatingActivities")
    )
    if operating_income:
        financials["operating_income_usd"] = operating_income

    if revenue and operating_income:
        financials["operating_margin_pct"] = round((operating_income / revenue) * 100, 2)

    net_income = (
        _extract_latest_value(facts, "us-gaap", "NetIncomeLoss")
        or _extract_latest_value(facts, "ifrs-full", "ProfitLoss")
    )
    if net_income:
        financials["net_income_usd"] = net_income

    employees = _extract_latest_value(facts, "dei", "EntityNumberOfEmployees", unit="pure")
    if employees:
        financials["employees"] = int(employees)
        if revenue:
            financials["revenue_per_employee_usd"] = round(revenue / employees, 2)

    total_assets = (
        _extract_latest_value(facts, "us-gaap", "Assets")
        or _extract_latest_value(facts, "ifrs-full", "Assets")
    )
    if total_assets:
        financials["total_assets_usd"] = total_assets

    return financials


def _format_currency(value: Optional[float]) -> str:
    """Format a USD value into a human-readable string."""
    if value is None:
        return "N/A"
    if abs(value) >= 1_000_000_000:
        return f"${value / 1_000_000_000:.1f}B"
    if abs(value) >= 1_000_000:
        return f"${value / 1_000_000:.0f}M"
    return f"${value:,.0f}"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def get_competitor_financials(competitor_name: str) -> dict:
    """
    Fetch financial data for a named competitor from SEC EDGAR.

    Args:
        competitor_name: Company name (e.g., "Accenture", "IBM", "Cognizant")

    Returns:
        Dictionary with financial metrics and filing info, or empty dict on failure.
        Keys may include: company, cik, revenue_usd, operating_income_usd,
        operating_margin_pct, net_income_usd, employees, revenue_per_employee_usd,
        total_assets_usd, latest_filings
    """
    normalized = _normalize_name(competitor_name)
    cik = COMPETITOR_CIKS.get(normalized)

    if not cik:
        logger.warning(
            "Company '%s' not found in SEC EDGAR CIK registry. "
            "Available: %s",
            competitor_name,
            list(COMPETITOR_CIKS.keys()),
        )
        return {}

    logger.info("Fetching SEC EDGAR data for %s (CIK: %s)", competitor_name, cik)

    # Fetch submissions for filing history
    submissions = _fetch_submissions(cik)
    latest_filings: list[dict] = []
    company_display_name = competitor_name.title()

    if submissions:
        company_display_name = submissions.get("name", company_display_name)
        latest_filings = _get_latest_filings(submissions, ["10-K", "10-Q", "20-F"], count=5)

    # Fetch XBRL company facts for financial data
    facts = _fetch_company_facts(cik)
    financials: dict = {}
    if facts:
        financials = _extract_financials_from_facts(facts)

    result = {
        "company": company_display_name,
        "cik": cik,
        "latest_filings": latest_filings,
        **financials,
    }

    logger.info(
        "SEC EDGAR data for %s: revenue=%s, margin=%s%%",
        company_display_name,
        _format_currency(financials.get("revenue_usd")),
        financials.get("operating_margin_pct", "N/A"),
    )

    return result


def get_financial_context(competitors: list[str]) -> str:
    """
    Fetch financial data for multiple competitors and return a formatted
    string suitable for injection into agent prompts.

    Args:
        competitors: List of competitor company names.

    Returns:
        Formatted string summarizing competitor financials for prompt context.
        Returns a fallback message if no data could be retrieved.
    """
    if not competitors:
        return ""

    sections: list[str] = []
    sections.append("## Competitor Financial Intelligence (SEC EDGAR - Live Data)\n")

    any_data = False
    for name in competitors:
        data = get_competitor_financials(name)
        if not data or not data.get("revenue_usd"):
            sections.append(f"### {name.title()}\n- Financial data unavailable\n")
            continue

        any_data = True
        lines = [f"### {data.get('company', name.title())}"]
        lines.append(f"- **Revenue**: {_format_currency(data.get('revenue_usd'))}")

        if data.get("operating_margin_pct") is not None:
            lines.append(f"- **Operating Margin**: {data['operating_margin_pct']}%")

        if data.get("net_income_usd") is not None:
            lines.append(f"- **Net Income**: {_format_currency(data['net_income_usd'])}")

        if data.get("employees") is not None:
            lines.append(f"- **Employees**: {data['employees']:,}")

        if data.get("revenue_per_employee_usd") is not None:
            lines.append(
                f"- **Revenue/Employee**: {_format_currency(data['revenue_per_employee_usd'])}"
            )

        if data.get("total_assets_usd") is not None:
            lines.append(f"- **Total Assets**: {_format_currency(data['total_assets_usd'])}")

        if data.get("latest_filings"):
            latest = data["latest_filings"][0]
            lines.append(
                f"- **Latest Filing**: {latest['form']} ({latest['filing_date']})"
            )

        lines.append("")
        sections.append("\n".join(lines))

    if not any_data:
        return (
            "## Competitor Financial Intelligence\n"
            "SEC EDGAR data currently unavailable. Proceed with qualitative analysis.\n"
        )

    return "\n".join(sections)
