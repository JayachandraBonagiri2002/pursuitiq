"""
Job Intelligence Module
========================
Searches for competitor and client job postings to derive intelligence
about hiring activity, technology stacks, and potential bid signals.

Uses OpenAI Responses API with web search to find and analyze job postings
from publicly accessible job boards.
"""

import logging
from typing import Optional

from openai_client import get_client
from config import MODEL, REASONING_LOW

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
            model=MODEL,
            tools=[{"type": "web_search_preview", "search_context_size": SEARCH_CONTEXT_SIZE}],
            instructions=(
                "You are a job market intelligence analyst. Search the web for the given "
                "job posting query and return structured findings. Focus on: number of open "
                "roles found, key technologies mentioned, seniority levels, locations, and "
                "any patterns that indicate strategic hiring or expansion."
            ),
            input=query,
            reasoning={"effort": REASONING_LOW},
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

    Args:
        raw_text: Raw text from web search results.

    Returns:
        Dictionary with parsed hiring signal data.
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

    # Use the model to structure the response
    client = get_client()
    try:
        response = client.responses.create(
            model=MODEL,
            instructions=(
                "Extract structured data from this job market research. Return ONLY a "
                "valid JSON object with these keys:\n"
                '- "role_count_estimate": integer (estimated number of open roles found)\n'
                '- "technologies": list of strings (technologies/tools mentioned)\n'
                '- "seniority_levels": list of strings (e.g., "Senior", "Lead", "Director")\n'
                '- "locations": list of strings (locations mentioned)\n'
                '- "signals": list of strings (brief intelligence signals, e.g., '
                '"Rapid cloud expansion", "New AI/ML team forming")\n'
                '- "summary": string (2-3 sentence summary of findings)\n\n'
                "Return ONLY the JSON object, no markdown formatting."
            ),
            input=raw_text,
            reasoning={"effort": REASONING_LOW},
        )
        import json

        for item in response.output:
            if item.type == "message":
                for content in item.content:
                    if content.type == "output_text":
                        text = content.text.strip()
                        # Strip markdown code fences if present
                        if text.startswith("```"):
                            text = text.split("\n", 1)[-1]
                            text = text.rsplit("```", 1)[0]
                        parsed = json.loads(text)
                        parsed["raw_summary"] = parsed.pop("summary", raw_text[:500])
                        return parsed
    except (json.JSONDecodeError, Exception) as e:
        logger.warning("Failed to parse hiring signals into structured data: %s", e)

    # Fallback: return raw text as summary
    return {
        "role_count_estimate": 0,
        "technologies": [],
        "seniority_levels": [],
        "locations": [],
        "signals": [],
        "raw_summary": raw_text[:1000] if raw_text else "No data available.",
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

    # Client hiring signals
    client_signals = get_client_hiring_signals(client, industry_keywords)
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

    # Competitor hiring signals
    any_competitor_data = False
    for comp in competitors:
        signals = get_competitor_hiring_signals(comp, geography, industry_keywords)
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
