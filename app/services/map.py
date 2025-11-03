from app.constants import ComplaintCategory, DEPARTMENT_MAPPING


def map_department(category: str) -> str:
    """Map complaint category to department code."""
    # Try to find exact match first
    for cat in ComplaintCategory:
        if cat.value == category:
            return DEPARTMENT_MAPPING[cat]
    
    # Default fallback
    return DEPARTMENT_MAPPING[ComplaintCategory.OTHER]

