"""JSON Schema definition and validator for Exitwise Dependency Exit Capsules."""

import json
from typing import Any
from exitwise.models import DependencyCapsule


def get_capsule_json_schema() -> dict[str, Any]:
    """Generate canonical JSON Schema from Pydantic model."""
    return DependencyCapsule.model_json_schema()


def validate_capsule_dict(data: dict[str, Any]) -> tuple[bool, str | None]:
    """Validate a serialized capsule dictionary against Pydantic schema and provenance rules."""
    try:
        capsule = DependencyCapsule.model_validate(data)

        # Strict validation: verify that required sections are present
        if not capsule.meta.gemma_model_id:
            return False, "Missing gemma_model_id in capsule metadata"

        # Check provenance tags on leaf collections
        for ind in capsule.risk_indicators:
            if not ind.provenance:
                return False, f"Risk indicator {ind.id} missing provenance"

        for loc in capsule.usage_locations:
            if not loc.provenance:
                return False, f"Usage location {loc.file}:{loc.line} missing provenance"

        for tr in capsule.executed_test_results:
            if not tr.provenance:
                return False, f"Test run for {tr.side} missing provenance"

        return True, None
    except Exception as e:
        return False, str(e)
