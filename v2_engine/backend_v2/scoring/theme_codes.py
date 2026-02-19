"""
GKG Theme Code Translator

Maps GDELT GKG theme codes to human-readable descriptions.
Over 100 entries covering the most common GKG themes.
"""

from __future__ import annotations

THEME_DESCRIPTIONS = {
    # Economy
    "TAX_FNCACT": "Taxation and fiscal policy",
    "ECON_DEBT": "Economic debt",
    "ECON_TRADE": "International trade",
    "ECON_BANKRUPTCY": "Bankruptcy and insolvency",
    "ECON_COST_OF_LIVING": "Cost of living",
    "ECON_HOUSING": "Housing market",
    "ECON_CURRENCY": "Currency and exchange rates",
    "ECON_INFLATION": "Inflation",
    "ECON_UNEMPLOYMENT": "Unemployment",
    "ECON_STOCKMARKET": "Stock market",
    "ECON_GDP": "GDP and economic growth",
    "ECON_FDI": "Foreign direct investment",
    "ECON_REMITTANCES": "Remittances",
    "ECON_INTEREST_RATE": "Interest rates",
    "ECON_POVERTY": "Poverty",
    "ECON_PRICE_CONTROLS": "Price controls",

    # Environment
    "ENV_CLIMATECHANGE": "Climate change",
    "ENV_DEFORESTATION": "Deforestation",
    "ENV_GREEN": "Green energy and sustainability",
    "ENV_POLLUTION": "Pollution",
    "ENV_WATERQUALITY": "Water quality",
    "ENV_OIL": "Oil spill or pollution",

    # Health
    "HEALTH_PANDEMIC": "Pandemic health crisis",
    "HEALTH_SARS": "SARS/respiratory outbreak",
    "HEALTH_EBOLA": "Ebola outbreak",
    "HEALTH_VACCINATION": "Vaccination",
    "HEALTH_MENTAL": "Mental health",

    # Security / Military
    "SECURITY_MILITARY": "Military security",
    "SECURITY_CYBER": "Cybersecurity",
    "SECURITY_MARITIME": "Maritime security",

    # Governance
    "GOV_CORRUPTION": "Government corruption",
    "GOV_ELECTION": "Elections",
    "GOV_REFORM": "Government reform",
    "GOV_CENSORSHIP": "Censorship",
    "GOV_REGULATION": "Government regulation",

    # Protest / Crime
    "PROTEST": "Public protest",
    "CRIME_CARTELS": "Organized crime",
    "CRIME_KIDNAP": "Kidnapping",
    "CRIME_CYBERCRIME": "Cybercrime",
    "CRIME_DRUGS": "Drug trafficking",

    # Terrorism / Conflict
    "TERROR": "Terrorism",
    "DISPLACEMENT": "Population displacement",
    "REFUGEES": "Refugees",

    # Food / Water / Energy
    "FOOD_SECURITY": "Food security",
    "WATER_SECURITY": "Water security",
    "ENERGY_NUCLEAR": "Nuclear energy",
    "ENERGY_OIL": "Oil and petroleum",
    "ENERGY_SOLAR": "Solar energy",
    "ENERGY_WIND": "Wind energy",

    # Cyber
    "CYBER_ATTACK": "Cyber attack",

    # Elections / Rights
    "ELECTION": "Elections",
    "HUMAN_RIGHTS": "Human rights",
    "IMMIGRATION": "Immigration",
    "EDUCATION": "Education",

    # Infrastructure / Transport
    "INFRASTRUCTURE": "Infrastructure development",
    "TRANSPORT": "Transportation",
    "TOURISM": "Tourism",

    # Media
    "MEDIA_CENSORSHIP": "Media censorship",
    "MEDIA_SOCIAL": "Social media",

    # Labor
    "LABOR": "Labor and employment",
    "LABOR_STRIKE": "Labor strike",
    "LABOR_UNION": "Labor unions",

    # Social
    "WOMEN_RIGHTS": "Women's rights",
    "CHILDREN": "Children's issues",
    "RELIGION": "Religion",
    "ETHNIC_VIOLENCE": "Ethnic violence",

    # Natural disasters
    "NATURAL_DISASTER": "Natural disaster",
    "EARTHQUAKE": "Earthquake",
    "FLOOD": "Flooding",
    "DROUGHT": "Drought",
    "HURRICANE": "Hurricane/typhoon",
    "TSUNAMI": "Tsunami",
    "WILDFIRE": "Wildfire",
    "EPIDEMIC": "Epidemic",
    "FAMINE": "Famine",

    # Industry
    "AGRICULTURE": "Agriculture",
    "MINING": "Mining",
    "MANUFACTURING": "Manufacturing",
    "AVIATION": "Aviation",
    "SHIPPING": "Shipping and logistics",

    # Technology
    "TECH_AI": "Artificial intelligence",
    "TECH_BLOCKCHAIN": "Blockchain and cryptocurrency",
    "TECH_BIOTECH": "Biotechnology",
    "TECH_SPACE": "Space technology",

    # Social issues
    "POVERTY": "Poverty",
    "INEQUALITY": "Economic inequality",
    "HOUSING": "Housing",
    "URBANIZATION": "Urbanization",
    "GENTRIFICATION": "Gentrification",
    "PUBLIC_HEALTH": "Public health",
    "SANITATION": "Sanitation",
    "CORRUPTION": "Corruption",

    # International relations
    "DIPLOMACY": "Diplomacy",
    "TRADE_WAR": "Trade war",
    "SANCTIONS": "Economic sanctions",
    "ARMS_TRADE": "Arms trade",
    "PEACEKEEPING": "Peacekeeping",

    # GDELT special codes
    "WB_2024": "World Bank development indicators",
    "UNGP": "UN Global Programs",
    "USPEC_POLITICS": "Political speculation",
    "USPEC_ECON": "Economic speculation",
    "SOC_POINTSOFINTEREST": "Social points of interest",
    "SOC_GENERALCRIME": "General crime",
    "CRISISLEX_CRISISLEXREC": "Crisis language detected",
    "MANMADE_DISASTER": "Man-made disaster",

    # Common general themes
    "TAX_ETHNICITY": "Ethnic/racial issues",
    "TAX_WORLDLANGUAGES": "Language diversity",
    "TAX_WORLDMAMMALS": "Wildlife conservation",
    "ARMEDCONFLICT": "Armed conflict",
    "SELF_IDENTIFIED_ENVIRON_DISASTER": "Environmental disaster",
    "WB_2685_POVERTY_REDUCTION": "Poverty reduction",
    "WB_696_PUBLIC_SECTOR_DEVELOPMENT": "Public sector development",
    "WB_621_HEALTH_NUTRITION_AND_POPULATION": "Health and population",
    "WB_831_ECONOMIC_POLICY": "Economic policy",
    "WB_2266_URBAN_DEVELOPMENT": "Urban development",

    # EPU (Economic Policy Uncertainty) — very common in GKG
    "EPU_ECONOMY_HISTORIC": "Economic policy uncertainty",
    "EPU_ECONOMY_RECENT": "Recent economic uncertainty",
    "EPU_ECONOMY": "Economic policy uncertainty",
    "EPU_POLICY": "Policy uncertainty",
    "EPU_CATS_GOVERNMENT_SPENDING": "Government spending uncertainty",
    "EPU_CATS_MONETARY_POLICY": "Monetary policy uncertainty",
    "EPU_CATS_TAX_POLICY": "Tax policy uncertainty",
    "EPU_CATS_FINANCIAL_REGULATION": "Financial regulation uncertainty",
    "EPU_CATS_TRADE_POLICY": "Trade policy uncertainty",
    "EPU_CATS_HEALTHCARE": "Healthcare policy uncertainty",
    "EPU_CATS_NATIONAL_SECURITY": "National security uncertainty",
    "EPU_CATS_ENTITLEMENT_PROGRAMS": "Entitlement program uncertainty",

    # World Bank sector codes (WB_NNN_TOPIC format)
    "WB_507_ENERGY_AND_EXTRACTIVES": "Energy and extractives",
    "WB_509_FINANCE_AND_MARKETS": "Finance and capital markets",
    "WB_534_TRADE": "International trade",
    "WB_537_TRANSPORT": "Transport infrastructure",
    "WB_541_WATER": "Water resources",
    "WB_546_SOCIAL_PROTECTION": "Social protection",
    "WB_548_EDUCATION": "Education",
    "WB_552_HEALTH": "Health systems",
    "WB_555_ICT": "Information and communication technology",
    "WB_557_AGRICULTURE": "Agriculture",
    "WB_559_ENVIRONMENT": "Environment",
    "WB_560_URBAN": "Urban development",
    "WB_562_PRIVATE_SECTOR": "Private sector development",
    "WB_563_PUBLIC_SECTOR": "Public sector governance",
    "WB_565_MACROECONOMICS": "Macroeconomics",
    "WB_567_POVERTY": "Poverty and inequality",
    "WB_570_GENDER": "Gender equality",
    "WB_572_JOBS": "Labor and jobs",
    "WB_574_CLIMATE": "Climate change policy",

    # TAX functional actor categories (very common prefix)
    "TAX_FNCACT_PRESIDENT": "Presidential politics",
    "TAX_FNCACT_MINISTER": "Government minister activity",
    "TAX_FNCACT_POLICE": "Law enforcement",
    "TAX_FNCACT_MILITARY": "Military activity",
    "TAX_FNCACT_GENERAL": "Military command",
    "TAX_FNCACT_REBEL": "Rebel activity",
    "TAX_FNCACT_PROTESTOR": "Public protest",
    "TAX_FNCACT_STUDENT": "Student activity",
    "TAX_FNCACT_OPPOSITION": "Political opposition",
    "TAX_FNCACT_JUDGE": "Judicial activity",
    "TAX_FNCACT_DOCTOR": "Medical activity",
    "TAX_FNCACT_BANKER": "Banking and finance",
    "TAX_FNCACT_CEO": "Corporate leadership",
    "TAX_FNCACT_DIPLOMAT": "Diplomatic activity",
    "TAX_FNCACT_LEGISLATOR": "Legislative activity",

    # CRISISLEX codes
    "CRISISLEX_T01_WEATHER": "Weather emergency",
    "CRISISLEX_T02_EARTHQUAKE": "Earthquake",
    "CRISISLEX_T03_FLOOD": "Flood",
    "CRISISLEX_T04_FIRE": "Fire emergency",
    "CRISISLEX_T05_TRANSPORTATION": "Transport accident",
    "CRISISLEX_T06_INDUSTRIAL": "Industrial accident",
    "CRISISLEX_T07_DISEASE": "Disease outbreak",
    "CRISISLEX_T08_CONFLICT": "Conflict and violence",
    "CRISISLEX_T09_TERRORISM": "Terrorism",
    "CRISISLEX_T10_OTHER": "Emergency event",

    # UNGP sub-codes
    "UNGP_FORESTS_RIVERS_OCEANS": "Natural resource governance",
    "UNGP_FORESTS_RIVERS_OCEANS_RIVERS": "River governance",
    "UNGP_FORESTS_RIVERS_OCEANS_OCEANS": "Ocean governance",
}


def describe_theme(code: str) -> str:
    """
    Return a human-readable description for a GKG theme code.

    Lookup order:
    1. Exact match in THEME_DESCRIPTIONS
    2. Strip known opaque prefixes (EPU_, WB_NNN_, TAX_FNCACT_, CRISISLEX_,
       UNGP_) and try again with just the meaningful suffix
    3. Convert underscores to spaces and title-case as last resort
    """
    if not code:
        return "Unknown theme"

    if code in THEME_DESCRIPTIONS:
        return THEME_DESCRIPTIONS[code]

    # Try progressively shorter prefix strips for structured code families
    # EPU_CATS_XXX → try EPU_CATS_XXX, then EPU_XXX suffix meaning
    # WB_507_XXX → strip "WB_507_" and humanise remainder
    # TAX_FNCACT_XXX → strip "TAX_FNCACT_" and humanise remainder
    import re as _re

    # Pattern: starts with known prefix families that carry no semantic value
    _OPAQUE_PREFIXES = (
        # WB_NNN_ — World Bank sector code with numeric ID
        _re.compile(r"^WB_\d+_(.+)$"),
        # EPU_CATS_ — EPU sub-category
        _re.compile(r"^EPU_CATS_(.+)$"),
        # TAX_FNCACT_ — functional actor taxonomy
        _re.compile(r"^TAX_FNCACT_(.+)$"),
        # CRISISLEX_T\d+_ — crisis type with numeric ID
        _re.compile(r"^CRISISLEX_T\d+_(.+)$"),
        # UNGP_ — strip prefix, keep remainder
        _re.compile(r"^UNGP_(.+)$"),
        # TAX_ — generic taxonomy prefix
        _re.compile(r"^TAX_(.+)$"),
        # SOC_ prefix
        _re.compile(r"^SOC_(.+)$"),
    )

    for pattern in _OPAQUE_PREFIXES:
        m = pattern.match(code)
        if m:
            suffix = m.group(1)
            # Check if the stripped suffix maps to something known
            if suffix in THEME_DESCRIPTIONS:
                return THEME_DESCRIPTIONS[suffix]
            # Otherwise humanise the suffix only (better than the full code)
            return suffix.replace("_", " ").title()

    # Final fallback: replace underscores and title-case
    return code.replace("_", " ").title()
