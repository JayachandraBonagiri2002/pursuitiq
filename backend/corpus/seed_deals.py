"""
corpus/seed_deals.py — 100 synthetic past deals for the Vector Store.

These records simulate HCLTech's historical bid data.
Agent 2 searches these to find similar wins/losses and calculate win probability.

Format: each deal becomes a plain-text document uploaded to OpenAI Vector Stores.
"""

import random

random.seed(42)  # reproducible


# ── 20 detailed deals (rich, realistic) ───────────────────────────────────────

DETAILED_DEALS = [
    {
        "id": "DEAL-001", "title": "Core Banking Modernisation",
        "industry": "Banking", "client": "Tier 1 European Bank",
        "geo": "Germany", "size": "$52M", "years": 5, "outcome": "WON",
        "competitors": "TCS, Capgemini",
        "win_reason": "Only bidder with Frankfurt entity + BaFin BAIT compliance framework + 500k+ COBOL lines migrated track record",
        "win_themes": "On-shore first model, COBOL pedigree, German regulatory expertise",
        "lesson": "Local entity requirement in Appendix A was the hidden disqualifier TCS missed. We caught it and made it our advantage.",
        "certs": "ISO 27001:2022, PCI-DSS L1, Azure Gold Partner",
    },
    {
        "id": "DEAL-002", "title": "Digital Banking Platform",
        "industry": "Banking", "client": "UK Retail Bank top-5",
        "geo": "United Kingdom", "size": "$38M", "years": 4, "outcome": "WON",
        "competitors": "Infosys, IBM",
        "win_reason": "Pre-cleared BPSS security personnel pool of 340 engineers; only bidder who could start within 6 weeks of contract award",
        "win_themes": "Pre-cleared workforce, UK-first delivery, Open Banking API expertise",
        "lesson": "Government clearance requirement buried in Schedule C. Infosys and IBM did not have pre-cleared pool. We did.",
        "certs": "ISO 27001, Cyber Essentials Plus, FCA registered",
    },
    {
        "id": "DEAL-003", "title": "SAP S/4HANA Global Rollout",
        "industry": "Manufacturing", "client": "Fortune 500 Automotive OEM",
        "geo": "Germany, USA, Mexico", "size": "$71M", "years": 4, "outcome": "WON",
        "competitors": "Accenture, Deloitte",
        "win_reason": "Largest SAP S/4HANA RISE team in automotive vertical globally; BMW case study was the decisive reference",
        "win_themes": "SAP automotive accelerator, zero downtime methodology, global follow-the-sun",
        "lesson": "Executive sponsor alignment matters. CTO at this client had worked with our SAP lead at a previous company.",
        "certs": "SAP Gold Partner, RISE with SAP certified, ISO 9001",
    },
    {
        "id": "DEAL-004", "title": "Nordic Insurance Cloud",
        "industry": "Insurance", "client": "Nordic Multi-line Insurer",
        "geo": "Sweden, Norway, Denmark, Finland", "size": "$29M", "years": 3, "outcome": "WON",
        "competitors": "Wipro, CGI",
        "win_reason": "Best price with Solvency II native compliance; carbon-neutral delivery centres were a surprise differentiator the client cared about",
        "win_themes": "Solvency II compliance, Nordic data sovereignty, carbon-neutral ops",
        "lesson": "Carbon neutrality was mentioned once in Section 7. We made it a win theme. Wipro ignored it.",
        "certs": "ISO 27001, Azure Expert MSP, ISAE 3402 Type II",
    },
    {
        "id": "DEAL-005", "title": "Telecom BSS/OSS Modernisation",
        "industry": "Telecom", "client": "Tier 1 European Mobile Operator",
        "geo": "Netherlands, Belgium", "size": "$44M", "years": 5, "outcome": "LOST",
        "competitors": "TCS",
        "win_reason": "N/A — lost",
        "loss_reason": "No registered entity in Netherlands. TCS had Dutch BV. Client's procurement required local entity under EU AI Act compliance. We missed this in Appendix B.",
        "lesson": "ALWAYS check for local entity requirements in every appendix. This cost us a $44M deal.",
        "certs": "ISO 27001 only",
    },
    {
        "id": "DEAL-006", "title": "NHS Healthcare Data Platform",
        "industry": "Healthcare", "client": "NHS Foundation Trust",
        "geo": "United Kingdom", "size": "$18M", "years": 3, "outcome": "WON",
        "competitors": "DXC, Fujitsu",
        "win_reason": "NHS DSPT certified from day one; UK-only data processing commitment; FHIR R4 implementation team ready",
        "win_themes": "NHS DSPT compliance, UK-only data, FHIR interoperability",
        "lesson": "UK public sector requires data never to leave UK. Our commitment was unconditional. Competitors were vague.",
        "certs": "NHS DSPT, ISO 27001, Cyber Essentials Plus",
    },
    {
        "id": "DEAL-007", "title": "Supply Chain AI Platform",
        "industry": "Retail & FMCG", "client": "Global FMCG Top-10",
        "geo": "USA, UK, Singapore, Brazil", "size": "$63M", "years": 4, "outcome": "WON",
        "competitors": "Cognizant, EY",
        "win_reason": "Proprietary AI supply chain accelerator cut estimated timeline by 8 months; pre-built SAP + Oracle connectors",
        "win_themes": "Proprietary accelerator, 8 months faster, pre-built connectors",
        "lesson": "Proprietary IP that demonstrably saves time beats lower hourly rates every time.",
        "certs": "ISO 27001, SOC 2 Type II, SAP Gold Partner, Oracle Platinum",
    },
    {
        "id": "DEAL-008", "title": "Sovereign Wealth Fund Cybersecurity SOC",
        "industry": "Government / Finance", "client": "UAE Sovereign Wealth Fund",
        "geo": "UAE", "size": "$22M", "years": 3, "outcome": "LOST",
        "competitors": "Accenture",
        "win_reason": "N/A — lost",
        "loss_reason": "Mandatory 40% UAE national (Emiratisation) staffing ratio. We could not meet it. Accenture had UAE nationals on staff. Scored highest technically but eliminated at screening.",
        "lesson": "GCC government deals have Emiratisation / Saudization quotas. Check these before spending 6 weeks on a bid.",
        "certs": "ISO 27001",
    },
    {
        "id": "DEAL-009", "title": "Energy Grid Cybersecurity",
        "industry": "Energy & Utilities", "client": "European Grid Operator",
        "geo": "France, Spain", "size": "$34M", "years": 4, "outcome": "WON",
        "competitors": "Capgemini, Atos",
        "win_reason": "IEC 62443 industrial cybersecurity certification; OT/IT convergence team; critical infrastructure track record",
        "win_themes": "IEC 62443 expertise, OT/IT convergence, critical infrastructure trust",
        "lesson": "IEC 62443 was listed as 'preferred' not 'mandatory'. We certified our team and made it mandatory in our response.",
        "certs": "IEC 62443, ISO 27001, NIS Directive compliance",
    },
    {
        "id": "DEAL-010", "title": "Global Law Firm Digital Workplace",
        "industry": "Legal & Professional Services", "client": "Magic Circle Law Firm",
        "geo": "UK, USA, Hong Kong, Singapore", "size": "$27M", "years": 4, "outcome": "WON",
        "competitors": "DXC, Unisys",
        "win_reason": "Legal AI expertise; M365 Copilot for legal workflows; privileged data handling protocols that passed Magic Circle governance",
        "win_themes": "Legal AI, M365 Copilot, privileged data governance",
        "lesson": "Legal clients care about privilege protection above everything. We had a Legal AI Data Governance Framework. Competitors didn't.",
        "certs": "ISO 27001, Microsoft Solutions Partner, SRA regulated",
    },
    {
        "id": "DEAL-011", "title": "Core Insurance Platform Migration",
        "industry": "Insurance", "client": "Global Life Insurer",
        "geo": "USA, Canada", "size": "$45M", "years": 5, "outcome": "WON",
        "competitors": "Cognizant, Wipro",
        "win_reason": "Guidewire PolicyCenter and ClaimCenter certified team; only bidder with North American Guidewire reference from a comparable insurer",
        "win_themes": "Guidewire expertise, North American delivery, pre-built accelerators",
        "lesson": "Product certifications (Guidewire, Salesforce, etc.) are decisive when the client has already chosen the product.",
        "certs": "ISO 27001, SOC 2 Type II, Guidewire PartnerConnect Elite",
    },
    {
        "id": "DEAL-012", "title": "Pharmaceutical Data Platform",
        "industry": "Pharmaceuticals", "client": "Big Pharma Top-5",
        "geo": "USA, UK, Switzerland", "size": "$58M", "years": 4, "outcome": "WON",
        "competitors": "Accenture, IBM",
        "win_reason": "GxP-compliant data management with FDA 21 CFR Part 11 validation; clinical trial data integration experience",
        "win_themes": "FDA compliance, GxP validation, clinical data expertise",
        "lesson": "Pharma clients need FDA-compliant delivery. This is a technical pre-requisite that eliminated Accenture who proposed a workaround.",
        "certs": "ISO 27001, FDA 21 CFR Part 11, GxP certified",
    },
    {
        "id": "DEAL-013", "title": "Central Bank Payment System",
        "industry": "Banking / Government", "client": "Central Bank",
        "geo": "India", "size": "$31M", "years": 4, "outcome": "WON",
        "competitors": "TCS, Infosys",
        "win_reason": "Existing RBI-approved vendor status; payment systems ISO 20022 expertise; team with government security clearances",
        "win_themes": "RBI approved vendor, ISO 20022, government track record",
        "lesson": "Central banks prefer existing approved vendors. Building approval status before a bid is a strategic moat.",
        "certs": "ISO 27001, PCI-DSS L1, RBI Technology Vendor approved",
    },
    {
        "id": "DEAL-014", "title": "Airport IT Transformation",
        "industry": "Transportation", "client": "International Airport Authority",
        "geo": "Singapore", "size": "$40M", "years": 5, "outcome": "LOST",
        "competitors": "SITA",
        "win_reason": "N/A — lost",
        "loss_reason": "SITA is the dominant aviation IT incumbent. No local Singapore entity. SITA's airport-specific product suite (DCS, BRS) was purpose-built for this use case.",
        "lesson": "Know when an incumbent has an insurmountable product advantage. Consider partnering rather than competing head-on.",
        "certs": "ISO 27001",
    },
    {
        "id": "DEAL-015", "title": "Retail Banking Digital Transformation",
        "industry": "Banking", "client": "Latin American Bank",
        "geo": "Mexico, Colombia, Peru", "size": "$33M", "years": 4, "outcome": "WON",
        "competitors": "Capgemini, Globant",
        "win_reason": "Spanish-speaking delivery team; LATAM-based nearshore centres; existing Mexican banking sector references",
        "win_themes": "Spanish-first delivery, LATAM nearshore, banking references",
        "lesson": "Language and cultural fit matter enormously in LATAM. Capgemini's French-accented Spanish delivery model was rejected by the client.",
        "certs": "ISO 27001, PCI-DSS L1",
    },
    {
        "id": "DEAL-016", "title": "Defense Logistics Digitalisation",
        "industry": "Defense / Government", "client": "European Defense Ministry",
        "geo": "Germany", "size": "$65M", "years": 6, "outcome": "LOST",
        "competitors": "Rheinmetall, T-Systems",
        "win_reason": "N/A — lost",
        "loss_reason": "Required NATO SECRET clearance for all personnel and vendor must be HQ-based in NATO member state with defense sector certification (CMMC equivalent). We were disqualified at screening.",
        "lesson": "Defense ministry deals almost always have security classification requirements that eliminate commercial IT firms without defense sector registrations.",
        "certs": "ISO 27001 only — insufficient for defense",
    },
    {
        "id": "DEAL-017", "title": "Wealth Management Platform",
        "industry": "Banking / Finance", "client": "Swiss Private Bank",
        "geo": "Switzerland, Luxembourg", "size": "$24M", "years": 3, "outcome": "WON",
        "competitors": "Sopra Banking, Temenos SI",
        "win_reason": "FINMA regulatory expertise; Geneva-based team; GDPR-plus Swiss FADP compliance framework",
        "win_themes": "Swiss regulatory compliance, Geneva presence, FADP expertise",
        "lesson": "Swiss clients prefer local teams. Geneva office + FINMA knowledge was more important than best technical solution.",
        "certs": "ISO 27001, Swiss FADP compliant, FINMA approved processes",
    },
    {
        "id": "DEAL-018", "title": "E-commerce Platform Replatform",
        "industry": "Retail", "client": "European Fashion Retailer",
        "geo": "UK, France, Germany", "size": "$19M", "years": 2, "outcome": "WON",
        "competitors": "Accenture Interactive, EPAM",
        "win_reason": "Fastest delivery timeline (14 months vs competitors' 20-24 months); pre-built Salesforce Commerce Cloud accelerator",
        "win_themes": "Speed to market, pre-built accelerator, multi-market rollout expertise",
        "lesson": "Fashion retail has seasonal deadlines. The client needed to launch before Christmas. We were the only bidder who committed to 14 months.",
        "certs": "ISO 27001, Salesforce Summit Partner",
    },
    {
        "id": "DEAL-019", "title": "Government Tax System Modernisation",
        "industry": "Government / Public Sector", "client": "National Tax Authority",
        "geo": "Australia", "size": "$78M", "years": 6, "outcome": "WON",
        "competitors": "Deloitte, DXC",
        "win_reason": "ASD-certified (Australian Signals Directorate) team; existing Australian federal government approved panel vendor status; NV1 cleared personnel",
        "win_themes": "ASD certified, federal panel approved, NV1 cleared team",
        "lesson": "Australian government deals require ASD certification and panel membership. Without these you cannot bid. Build these first.",
        "certs": "ISO 27001, ASD certified, IRAP assessed, AusTender panel member",
    },
    {
        "id": "DEAL-020", "title": "Telecom Network Automation",
        "industry": "Telecommunications", "client": "US Tier 1 Operator",
        "geo": "USA", "size": "$55M", "years": 4, "outcome": "WON",
        "competitors": "IBM, Ericsson",
        "win_reason": "5G network automation expertise; TM Forum certified OSS/BSS; existing AT&T and Verizon references provided confidence",
        "win_themes": "5G automation, TM Forum certified, strong US telco references",
        "lesson": "US telco clients want to see you've worked with their direct peers. Verizon reference clinched the deal against Ericsson.",
        "certs": "ISO 27001, TM Forum Catalyst certified, AWS Premier Partner",
    },
]


def _generate_bulk(n: int = 80) -> list[dict]:
    """Generate n additional synthetic deals to reach 100 total."""
    industries = ["Banking", "Insurance", "Manufacturing", "Healthcare",
                  "Telecom", "Energy", "Retail", "Government", "Pharma", "Transport"]
    geos       = ["USA", "UK", "Germany", "France", "Australia", "Singapore",
                  "India", "UAE", "Canada", "Netherlands"]
    outcomes   = ["WON"] * 65 + ["LOST"] * 35
    sizes      = ["$8M", "$14M", "$22M", "$31M", "$44M", "$58M", "$72M", "$95M", "$120M"]
    comps      = [["TCS", "Infosys"], ["Wipro", "Cognizant"], ["Accenture", "IBM"],
                  ["Capgemini", "Atos"], ["DXC", "Fujitsu"]]
    win_r = [
        "Strongest domain credentials in client's sector",
        "Fastest mobilisation — team ready within 2 weeks",
        "Pre-built accelerator reduced timeline by 6 months",
        "Pre-existing client relationship from previous engagement",
        "Proprietary IP reduced risk profile significantly",
        "Only bidder with required local entity in the jurisdiction",
        "Best price-to-quality ratio with balanced shore model",
    ]
    loss_r = [
        "Missed local entity requirement in compliance appendix",
        "Incumbent vendor relationship was too strong to displace",
        "Pricing 20% above winning bid despite better solution",
        "Could not meet mandatory nationality staffing ratio",
        "Lacked required certification discovered late in process",
    ]
    bulk = []
    for i in range(21, 21 + n):
        ind = random.choice(industries)
        geo = random.choice(geos)
        out = random.choice(outcomes)
        cmp = random.choice(comps)
        sz  = random.choice(sizes)
        yrs = random.randint(2, 7)
        deal = {
            "id": f"DEAL-{i:03d}", "title": f"{ind} IT Transformation",
            "industry": ind, "client": f"{ind} enterprise client",
            "geo": geo, "size": sz, "years": yrs, "outcome": out,
            "competitors": ", ".join(cmp),
        }
        if out == "WON":
            deal["win_reason"]  = random.choice(win_r)
            deal["win_themes"]  = random.choice(win_r)
            deal["lesson"]      = "Win driven by domain depth and client trust."
        else:
            deal["loss_reason"] = random.choice(loss_r)
            deal["lesson"]      = deal["loss_reason"]
        deal["certs"] = random.choice(["ISO 27001", "ISO 27001, SOC 2 Type II",
                                       "ISO 27001, Azure Gold", "ISO 27001, PCI-DSS L1"])
        bulk.append(deal)
    return bulk


def get_all_deals() -> list[dict]:
    return DETAILED_DEALS + _generate_bulk(80)


def format_for_vector_store(deal: dict) -> str:
    """Format a deal as readable text for embedding. Agent 2 searches these."""
    lines = [
        f"DEAL ID: {deal['id']}",
        f"TITLE: {deal['title']}",
        f"INDUSTRY: {deal['industry']}",
        f"GEOGRAPHY: {deal['geo']}",
        f"DEAL SIZE: {deal['size']}",
        f"DURATION: {deal['years']} years",
        f"OUTCOME: {deal['outcome']}",
        f"COMPETITORS: {deal['competitors']}",
        f"CERTIFICATIONS: {deal.get('certs', 'Not recorded')}",
    ]
    if deal['outcome'] == "WON":
        lines += [
            f"WIN REASON: {deal.get('win_reason', '')}",
            f"WIN THEMES: {deal.get('win_themes', '')}",
        ]
    else:
        lines.append(f"LOSS REASON: {deal.get('loss_reason', deal.get('loss_reason', ''))}")
    lines.append(f"KEY LESSON: {deal.get('lesson', '')}")
    return "\n".join(lines)


if __name__ == "__main__":
    deals = get_all_deals()
    print(f"Total deals: {len(deals)}")
    print("\nSample:\n")
    print(format_for_vector_store(deals[0]))