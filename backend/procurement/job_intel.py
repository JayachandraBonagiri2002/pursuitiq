"""
Job Intelligence Module
========================
Searches for competitor and client job postings to derive intelligence
about hiring activity, technology stacks, and potential bid signals.

Uses OpenAI Responses API with web search to find and analyze job postings
from publicly accessible job boards.

All web searches run concurrently via ThreadPoolExecutor to minimize latency.
"""

import logging
from typing import Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from openai_client import get_client
from config import MODEL_LIGHT

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MAX_SEARCH_RESULTS = 10
SEARCH_CONTEXT_SIZE = "medium"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _web_search_jobs(query: str) -> Optional[str]:
    """
    Execute a web search via OpenAI Responses API and return synthesized results.

    Args:
        query: The search query string.

    Returns:
        Text response from the model with web search results, or None on failure.
    """
    client = get_client()
    try:
        response = client.responses.create(
            model=MODEL_LIGHT,
            tools=[{"type": "web_search_preview", "search_context_size": SEARCH_CONTEXT_SIZE}],
            instructions=(
                "You are a job market intelligence analyst. Search the web for the given "
                "job posting query and return structured findings. Focus on: number of open "
                "roles found, key technologies mentioned, seniority levels, locations, and "
                "any patterns that indicate strategic hiring or expansion."
            ),
            input=query,
        )
        # Extract text from response output
        for item in response.output:
            if item.type == "message":
                for content in item.content:
                    if content.type == "output_text":
                        return content.text
        return None
    except Exception as e:
        logger.warning("Web search failed for query '%s': %s", query, e)
        return None


def _parse_hiring_signals(raw_text: Optional[str]) -> dict:
    """
    Parse the raw web search response into structured hiring signals.
    Uses simple text parsing to avoid an extra API call per company.
    """
    if not raw_text:
        return {
            "role_count_estimate": 0,
            "technologies": [],
            "seniority_levels": [],
            "locations": [],
            "signals": [],
            "raw_summary": "No data available.",
        }

    # Simple extraction without an extra API call — the web search response
    # is already synthesized by the model, just use it directly
    import re

    text_lower = raw_text.lower()

    # Extract role count estimates from common patterns
    role_count = 0
    count_patterns = [
        r'(\d+)\s*(?:open|active|current)\s*(?:roles?|positions?|jobs?|openings?)',
        r'(?:found|identified|listed)\s*(\d+)\s*(?:roles?|positions?|jobs?)',
        r'(\d+)\+?\s*(?:roles?|positions?|jobs?|openings?)',
    ]
    for pattern in count_patterns:
        match = re.search(pattern, text_lower)
        if match:
            role_count = int(match.group(1))
            break

    # Extract technologies mentioned
    tech_keywords = [
        "cloud", "aws", "azure", "gcp", "kubernetes", "docker", "ai", "ml",
        "python", "java", "devops", "sap", "oracle", "salesforce", "terraform",
        "microservices", "data engineering", "cybersecurity", "iot", "5g",
    ]
    technologies = [t for t in tech_keywords if t in text_lower]

    # Extract brief signals from the text (first 3 sentences are usually key)
    sentences = [s.strip() for s in raw_text.split('.') if len(s.strip()) > 20]
    signals = sentences[:4]

    return {
        "role_count_estimate": role_count,
        "technologies": technologies[:8],
        "seniority_levels": [],
        "locations": [],
        "signals": signals,
        "raw_summary": raw_text[:1000],
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def get_competitor_hiring_signals(
    competitor: str,
    geography: str,
    keywords: list[str],
) -> dict:
    """
    Search for competitor job postings to derive hiring intelligence.

    Args:
        competitor: Competitor company name (e.g., "Accenture").
        geography: Target geography (e.g., "United States", "UK", "India").
        keywords: Technology or role keywords to search for (e.g., ["cloud", "SAP", "AI"]).

    Returns:
        Dictionary with hiring signal data including:
        - role_count_estimate: Estimated number of open roles
        - technologies: Technologies mentioned in postings
        - seniority_levels: Seniority levels being hired
        - locations: Specific locations
        - signals: Intelligence signals derived from postings
        - raw_summary: Human-readable summary
    """
    keyword_str = " OR ".join(keywords) if keywords else ""
    query = (
        f"{competitor} job openings {geography} {keyword_str} "
        f"site:linkedin.com OR site:indeed.com OR site:glassdoor.com"
    )

    logger.info("Searching competitor hiring signals: %s in %s", competitor, geography)
    raw_result = _web_search_jobs(query)
    signals = _parse_hiring_signals(raw_result)
    signals["competitor"] = competitor
    signals["geography"] = geography
    signals["keywords_searched"] = keywords

    logger.info(
        "Competitor %s hiring signals: ~%d roles, techs=%s",
        competitor,
        signals.get("role_count_estimate", 0),
        signals.get("technologies", [])[:5],
    )

    return signals


def get_client_hiring_signals(
    client_name: str,
    keywords: list[str],
) -> dict:
    """
    Search for client (buyer organization) job postings to understand
    their technology needs and expansion areas.

    Args:
        client_name: Client/buyer organization name.
        keywords: Technology or role keywords to focus on.

    Returns:
        Dictionary with hiring signal data including:
        - role_count_estimate: Estimated number of open roles
        - technologies: Technologies the client is investing in
        - seniority_levels: Seniority levels being hired
        - locations: Office/project locations
        - signals: Intelligence signals (e.g., "Building new data platform team")
        - raw_summary: Human-readable summary
    """
    keyword_str = " OR ".join(keywords) if keywords else "technology IT"
    query = (
        f"{client_name} hiring {keyword_str} "
        f"site:linkedin.com OR site:indeed.com OR site:glassdoor.com"
    )

    logger.info("Searching client hiring signals: %s", client_name)
    raw_result = _web_search_jobs(query)
    signals = _parse_hiring_signals(raw_result)
    signals["client"] = client_name
    signals["keywords_searched"] = keywords

    logger.info(
        "Client %s hiring signals: ~%d roles, techs=%s",
        client_name,
        signals.get("role_count_estimate", 0),
        signals.get("technologies", [])[:5],
    )

    return signals


def get_job_intel_context(
    competitors: list[str],
    client: str,
    geography: str,
    industry: str,
) -> str:
    """
    Gather job intelligence for competitors and client, returning a formatted
    string suitable for injection into agent prompts.

    Args:
        competitors: List of competitor company names.
        client: Client/buyer organization name.
        geography: Target geography for the opportunity.
        industry: Industry vertical (used to refine keyword search).

    Returns:
        Formatted string summarizing job market intelligence for prompt context.
        Returns a fallback message if no data could be retrieved.
    """
    # Build industry-relevant keywords
    industry_keywords = _get_industry_keywords(industry)

    sections: list[str] = []
    sections.append("## Job Market Intelligence (Live Web Search)\n")

    # ── Run ALL web searches concurrently (client + all competitors) ──────────
    # This reduces 30-60s of sequential searches to ~10-15s parallel execution
    all_signals: dict[str, dict] = {}

    def _fetch_client():
        return ("client", client, get_client_hiring_signals(client, industry_keywords))

    def _fetch_competitor(comp):
        return ("competitor", comp, get_competitor_hiring_signals(comp, geography, industry_keywords))

    with ThreadPoolExecutor(max_workers=len(competitors) + 1) as executor:
        futures = [executor.submit(_fetch_client)]
        for comp in competitors:
            futures.append(executor.submit(_fetch_competitor, comp))

        for future in as_completed(futures):
            try:
                signal_type, name, signals = future.result()
                all_signals[name] = {"type": signal_type, "signals": signals}
            except Exception as e:
                logger.warning(f"Job intel search failed for one target: {e}")

    # ── Format client signals ─────────────────────────────────────────────────
    client_signals = all_signals.get(client, {}).get("signals", {})
    sections.append(f"### Client: {client}")
    if client_signals.get("role_count_estimate", 0) > 0:
        sections.append(f"- **Open Roles (est.)**: {client_signals['role_count_estimate']}")
        if client_signals.get("technologies"):
            sections.append(
                f"- **Technologies Investing In**: {', '.join(client_signals['technologies'][:8])}"
            )
        if client_signals.get("signals"):
            for signal in client_signals["signals"][:4]:
                sections.append(f"- {signal}")
    else:
        sections.append(f"- {client_signals.get('raw_summary', 'No hiring data found.')}")
    sections.append("")

    # ── Format competitor signals ─────────────────────────────────────────────
    any_competitor_data = False
    for comp in competitors:
        signals = all_signals.get(comp, {}).get("signals", {})
        sections.append(f"### Competitor: {comp}")

        if signals.get("role_count_estimate", 0) > 0:
            any_competitor_data = True
            sections.append(f"- **Open Roles in {geography} (est.)**: {signals['role_count_estimate']}")
            if signals.get("technologies"):
                sections.append(
                    f"- **Tech Focus**: {', '.join(signals['technologies'][:6])}"
                )
            if signals.get("signals"):
                for signal in signals["signals"][:3]:
                    sections.append(f"  - {signal}")
            # Bid signal interpretation
            if signals["role_count_estimate"] > 20:
                sections.append(
                    f"  - **BID SIGNAL**: High hiring in {geography} suggests active pursuit "
                    f"or recent win in this market"
                )
        else:
            sections.append(f"- {signals.get('raw_summary', 'No hiring data found.')}")
        sections.append("")

    if not any_competitor_data and client_signals.get("role_count_estimate", 0) == 0:
        return (
            "## Job Market Intelligence\n"
            "Job posting data currently unavailable. Proceed with other intelligence sources.\n"
        )

    return "\n".join(sections)


def _get_industry_keywords(industry: str) -> list[str]:
    """
    Map industry vertical to relevant technology/role keywords for job searches.

    Args:
        industry: Industry name (e.g., "healthcare", "financial services").

    Returns:
        List of relevant search keywords.
    """
    industry_lower = industry.lower()

    keyword_map: dict[str, list[str]] = {
        "healthcare": ["EHR", "HIPAA", "clinical", "health IT", "Epic", "Cerner", "cloud"],
        "financial": ["fintech", "banking", "payments", "risk", "compliance", "cloud", "AI"],
        "banking": ["fintech", "banking", "payments", "risk", "compliance", "cloud", "AI"],
        "insurance": ["insurtech", "claims", "underwriting", "actuarial", "cloud", "AI"],
        "manufacturing": ["IoT", "MES", "ERP", "SAP", "supply chain", "digital twin", "cloud"],
        "retail": ["e-commerce", "omnichannel", "POS", "supply chain", "cloud", "AI", "CRM"],
        "telecom": ["5G", "network", "OSS", "BSS", "cloud native", "AI", "automation"],
        "energy": ["smart grid", "SCADA", "renewable", "IoT", "cloud", "sustainability"],
        "government": ["FedRAMP", "cloud", "cybersecurity", "zero trust", "AI", "modernization"],
        "defense": ["cleared", "cybersecurity", "C4ISR", "cloud", "AI", "DevSecOps"],
        "technology": ["cloud", "AI", "ML", "DevOps", "SRE", "platform", "microservices"],
    }

    # Find best matching industry
    for key, keywords in keyword_map.items():
        if key in industry_lower:
            return keywords

    # Default keywords for unknown industries
    return ["cloud", "AI", "digital transformation", "IT services", "automation"]
