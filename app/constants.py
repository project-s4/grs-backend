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
    ComplaintCategory.SANITATION: "SAN",        # Sanitation
    ComplaintCategory.WATER_SUPPLY: "WAT",       # Water
    ComplaintCategory.STREET_LIGHTING: "ELE",     # Electrical (for lighting)
    ComplaintCategory.ROADS: "ROD",              # Roads
    ComplaintCategory.PUBLIC_SAFETY: "HEL",       # Health (or use HEL for safety/health issues)
    ComplaintCategory.OTHER: "SAN",              # Default to Sanitation
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

