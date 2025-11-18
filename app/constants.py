from enum import Enum


class ComplaintCategory(str, Enum):
    SANITATION = "Sanitation"
    WATER_SUPPLY = "Water Supply"
    STREET_LIGHTING = "Street Lighting"
    ROADS = "Roads"
    PUBLIC_SAFETY = "Public Safety"
    OTHER = "Other"


class UserIntent(str, Enum):
    COMPLAINT = "complaint"
    REQUEST = "request"
    SUGGESTION = "suggestion"
    QUERY = "query"
    OTHER = "other"


# Department mapping to actual department codes in database
DEPARTMENT_MAPPING = {
    # Map to actual department codes that exist in the seeded database
    # Bengaluru-specific local bodies:
    ComplaintCategory.SANITATION: "BBMP",      # BBMP (Bruhat Bengaluru Mahanagara Palike) handles sanitation issues in Bengaluru
    ComplaintCategory.STREET_LIGHTING: "BESCOM", # BESCOM (Bangalore Electricity Supply Company) handles electricity and street lighting in Bengaluru
    # Other categories:
    ComplaintCategory.WATER_SUPPLY: "PW",      # Public Works manages water supply
    ComplaintCategory.ROADS: "PW-SUB",         # Roads sub-department under Public Works
    ComplaintCategory.PUBLIC_SAFETY: "PD",     # Police Department for safety concerns
    ComplaintCategory.OTHER: "PW",             # Default fallback to Public Works
}

# Keyword-based fallback classification rules
KEYWORD_RULES = {
    ComplaintCategory.SANITATION: [
        "garbage", "trash", "waste", "kachra", "gandagi", "safai",
        "dustbin", "collection", "cleaning", "sweeping", "dead animal",
        "carcass", "dead dog", "dead cat", "rotting", "smell", "stench",
        "rotting", "decomposing", "corpse", "dead"
    ],
    ComplaintCategory.WATER_SUPPLY: [
        "water", "pani", "supply", "tap", "pipeline", "leakage",
        "shortage", "quality", "contamination", "bore", "well"
    ],
    ComplaintCategory.STREET_LIGHTING: [
        "light", "lighting", "street", "lamp", "pole", "electricity",
        "dark", "bulb", "illumination", "batti"
    ],
    ComplaintCategory.ROADS: [
        "road", "street", "path", "pothole", "repair", "construction",
        "footpath", "sidewalk", "sadak", "rasta"
    ],
    ComplaintCategory.PUBLIC_SAFETY: [
        "safety", "crime", "police", "security", "harassment",
        "accident", "emergency", "fire", "suraksha"
    ]
}

