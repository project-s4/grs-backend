from app.constants import ComplaintCategory, DEPARTMENT_MAPPING
from typing import Optional


def map_department(category: str, db: Optional[object] = None) -> str:
    """Map complaint category to department code.

    If a DB session is provided, prefer department codes that exist in the database.
    If the configured mapping points to a non-existing code, try a case-insensitive
    match against department names in the DB (e.g., 'Public Works' -> 'PW').

    Returns the mapped code (possibly from DEPARTMENT_MAPPING) as a best-effort.
    """
    if not category:
        return DEPARTMENT_MAPPING[ComplaintCategory.OTHER]

    # Try to find exact match first in our enum mapping
    for cat in ComplaintCategory:
        if cat.value == category:
            mapped_code = DEPARTMENT_MAPPING.get(cat)

            # If we have a DB session, verify this code exists and try name matching fallback
            if db is not None and mapped_code:
                try:
                    from app.models.models import Department
                    # Exact code exists?
                    dept = db.query(Department).filter_by(code=mapped_code).first()
                    if dept:
                        return mapped_code

                    # Try to match by department name (contains category words)
                    possible = db.query(Department).filter(Department.name.ilike(f"%{category}%"))
                    first = possible.first()
                    if first:
                        return first.code
                except Exception:
                    # If DB lookup fails for any reason, fall back to configured code
                    pass

            # If mapped_code not found in DB or name matching failed, try a simple token-based
            # similarity across available departments and pick the best candidate.
            if db is not None:
                try:
                    from app.models.models import Department
                    depts = db.query(Department).all()
                    category_tokens = set((category or "").lower().replace('/', ' ').split())
                    best = None
                    best_score = 0
                    for d in depts:
                        name_tokens = set((d.name or "").lower().split())
                        code_token = (d.code or "").lower()
                        # score by token overlap plus code match
                        score = len(category_tokens & name_tokens)
                        if any(tok for tok in category_tokens if tok in code_token):
                            score += 1
                        if score > best_score:
                            best_score = score
                            best = d
                    if best and best_score > 0:
                        return best.code
                    # As last resort, return the first department code available in DB
                    if depts:
                        return depts[0].code
                except Exception:
                    pass

            return mapped_code

    # Default fallback
    return DEPARTMENT_MAPPING[ComplaintCategory.OTHER]

