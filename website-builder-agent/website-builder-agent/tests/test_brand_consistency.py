from utils.brand_consistency import typeface_issues


def test_one_or_two_families_pass():
    assert typeface_issues({"manrope": 4000}) == []
    assert typeface_issues({"manrope": 4000, "dm sans": 900, "sans-serif": 30}) == []


def test_section_by_section_typefaces_fail():
    problems = typeface_issues({"bricolage grotesque": 3000, "inter": 2500, "fraunces": 300,
                                "sora": 200, "space grotesk": 150})
    assert problems and "5 typefaces" in problems[0]


def test_trace_amounts_ignored():
    assert typeface_issues({"manrope": 10000, "inter": 2000, "times new roman": 20}) == []
