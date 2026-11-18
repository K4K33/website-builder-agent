"""Pure checkpoint stage decision for private Kaurivo demo workers.

Every restored archive must independently pass its authenticated SHA and
identity verification before this helper is used. A blocked concept is not an
approval and must be regenerated with the active browser and quality gates.
"""


def needs_research_restart(resumed, restored_company, current_master_sha256, current_v7_sha256=None):
    """Old private checkpoints never approve a build under a newer master.

    The source URL and identity are validated during archive restoration. If
    the canonical prompt changed, research and all downstream visual evidence
    must be rebuilt, not treated as an unrepairable HOLD or waved through.
    Partial research performs its own versioned progress validation.
    """
    if resumed in (None, "research_partial"):
        return False
    research = (restored_company or {}).get("research") if isinstance(restored_company, dict) else None
    if not isinstance(research, dict) or research.get("master_prompt_sha256") != current_master_sha256:
        return True
    # The archived V6 policy SHA does not include the independently versioned
    # V7 art-direction contract. Require both hashes when V7 is in force.
    if current_v7_sha256 is not None:
        brief = research.get("v7_design_brief")
        if (not isinstance(brief, dict) or
                brief.get("master_sha256") != current_v7_sha256):
            return True
    return False


def completed_stage_index(resumed, restored_company=None, *, concept_root=None):
    """Return the last usable stage, retaining source research for failed concepts."""
    if resumed in (None, "research_partial"):
        return -1
    stages = ("researched", "concepts", "selected", "built",
              "revised_1", "revised_2")
    position = stages.index(resumed)
    if resumed == "concepts":
        preview = ((restored_company or {}).get("concept_previews") or {})
        if preview.get("status") != "ready_for_comparison":
            # Do not trust a denied browser review. Rebuild just the concept
            # phase while preserving the checkpoint's verified research.
            return 0
        if concept_root is not None:
            from utils.concept_previews import ConceptContextChanged, load_verified_set

            try:
                load_verified_set(preview, restored_company["research"],
                                  allowed_root=concept_root)
            except ConceptContextChanged:
                return 0
    return position
