"""Coupling score calculation and usage aggregation."""

from exitwise.models import UsageLocation, UsageSummary, Provenance


def compute_usage_coupling(locations: list[UsageLocation]) -> UsageSummary:
    """Compute structural coupling score and summary from observed usage locations."""
    if not locations:
        return UsageSummary(
            total_files=0,
            total_occurrences=0,
            distinct_symbols=[],
            is_monkey_patched=False,
            is_test_only=False,
            coupling_score=0.0,
            provenance=Provenance.OBSERVED,
        )

    distinct_files = {loc.file for loc in locations}
    distinct_symbols = sorted(list({loc.symbol for loc in locations}))
    has_patching = any(loc.kind == "patch" or loc.context == "patching" for loc in locations)
    has_inheritance = any(loc.kind == "inheritance" for loc in locations)
    is_test_only = all(loc.context == "test" or "test" in loc.file.lower() for loc in locations)

    # Base score calculated from breadth and depth
    score = 0.0
    # Files factor (up to 3.0 pts)
    score += min(len(distinct_files) * 0.75, 3.0)
    # Distinct symbols factor (up to 2.5 pts)
    score += min(len(distinct_symbols) * 0.5, 2.5)

    # Hazardous coupling modifiers
    if has_patching:
        score += 3.5  # Monkey patching significantly increases migration risk
    if has_inheritance:
        score += 1.5  # Subclassing binds repo tightly to base class contracts

    if is_test_only:
        score *= 0.5  # Test-only dependency is less risky to swap out

    score = round(min(score, 10.0), 1)

    return UsageSummary(
        total_files=len(distinct_files),
        total_occurrences=len(locations),
        distinct_symbols=distinct_symbols,
        is_monkey_patched=has_patching,
        is_test_only=is_test_only,
        coupling_score=score,
        provenance=Provenance.OBSERVED,
    )
