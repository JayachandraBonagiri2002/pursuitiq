"""
procurement — Real public procurement data from government databases.

Provides actual contract awards, real prices, real winners from 5 sources:
- TED.europa.eu (EU - all 27 member states)
- UK Contracts Finder (United Kingdom)
- USASpending.gov (United States federal)
- AusTender (Australia)
- GeBIZ (Singapore)
"""

from procurement.ted_europe import search_ted_contracts, get_client_procurement_history
from procurement.contracts_finder import search_uk_contracts
from procurement.sam_gov import search_us_contracts
from procurement.austender import search_au_contracts
from procurement.gebiz import search_sg_contracts
