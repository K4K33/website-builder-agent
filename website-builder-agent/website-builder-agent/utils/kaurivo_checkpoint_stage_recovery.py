"""Pure checkpoint stage decision for private Kaurivo demo workers.

Every restored archive must independently pass its authenticated SHA and
identity verification before this helper is used. A blocked concept is not an
approval and must be regenerated with the active browser and quality gates.
"""


def completed_stage_index(resumed, restored_company=None):
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
    return position
