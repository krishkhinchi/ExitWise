"""Pydantic v2 schemas for structured Gemma 4 prompt inputs and outputs."""

from typing import Literal
from pydantic import BaseModel, Field


class TriageOutput(BaseModel):
    """Schema for Gemma Job 1: Risk Triage."""

    summary_explanation: str = Field(description="Clear explanation of the dependency risks")
    cited_evidence_ids: list[str] = Field(description="List of EV-* IDs supporting this triage")
    recommendation_direction: Literal["REPLACE", "UPGRADE", "MONITOR", "REMOVE"] = Field(
        description="High-level suggested migration direction"
    )


class UsageCharacterizationOutput(BaseModel):
    """Schema for Gemma Job 2: Usage Characterization."""

    depth_assessment: Literal["SHALLOW", "MODERATE", "DEEP", "CRITICAL"] = Field(
        description="Depth of coupling to the repository"
    )
    narrative_summary: str = Field(description="Clear analysis of how the dependency is used in the repo")
    hazard_notes: list[str] = Field(default_factory=list, description="Migration hazards (e.g. monkey patching)")
    cited_evidence_ids: list[str] = Field(description="List of EV-* IDs supporting this analysis")


class CandidateProposal(BaseModel):
    """Single candidate proposal from Gemma."""

    name: str = Field(description="PyPI distribution name or Python stdlib module name (e.g. 'platformdirs', 'tomllib')")
    is_stdlib: bool = Field(default=False, description="True if candidate is in Python 3.12/3.13 stdlib")
    rank: int = Field(description="Preference rank (1 being most recommended)")
    tradeoffs: list[str] = Field(default_factory=list, description="Pros, cons, and behavioral trade-offs")
    cited_evidence_ids: list[str] = Field(default_factory=list)


class ReplacementProposalOutput(BaseModel):
    """Schema for Gemma Job 3: Replacement Candidates."""

    candidates: list[CandidateProposal] = Field(description="1 to 3 ranked replacement candidates")
    reasoning: str = Field(description="Technical rationale for the recommended replacement")


class MigrationPlanOutput(BaseModel):
    """Schema for Gemma Job 4: Migration Steps & Unified Diff."""

    ordered_steps: list[str] = Field(description="Step-by-step migration instructions")
    unified_diff: str = Field(description="Unified git diff to apply to the repository")
    target_dependency: str = Field(description="Name of replaced dependency")
    replacement_dependency: str = Field(description="Name of replacement dependency")


class DifferentialTestOutput(BaseModel):
    """Schema for Gemma Job 5: Differential Compat Tests."""

    test_file_name: str = Field(default="test_differential_compat.py")
    test_code: str = Field(description="Complete executable pytest code testing the exact APIs used")
    exercised_apis: list[str] = Field(default_factory=list, description="List of API symbols exercised")


class GapNarrativeOutput(BaseModel):
    """Schema for Gemma Job 6: Gap Analysis Narrative."""

    narrative: str = Field(description="Technical explanation of observed test discrepancies")
    surfaced_gaps: list[str] = Field(default_factory=list, description="Descriptions of concrete differences")
    unresolved_risks: list[str] = Field(default_factory=list, description="Risks that remain unaddressed")
