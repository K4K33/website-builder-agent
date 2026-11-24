"""Typeface and brand consistency check on the rendered page.

Owner feedback (24.11.2026): the Kaurivo preview changed typeface from section to section
and lost the brand. A site keeps one type system everywhere, including illustrative demo
content shown inside it: one family is best, two at most.
"""

MAX_FAMILIES = 2

# Collect the first family of every visible text element, weighted by characters x font size,
# so a display face used for a few big headlines counts as much as it is seen.
FAMILY_SCRIPT = """() => {
  const seen = {};
  const skip = new Set(['SCRIPT','STYLE','NOSCRIPT','TITLE','HEAD','META','LINK','SVG','PATH',
                        'INPUT','SELECT','TEXTAREA','OPTION','CODE','PRE','KBD','SAMP']);
  for (const el of document.body.querySelectorAll('*')) {
    if (skip.has(el.tagName)) continue;
    let own = '';
    for (const n of el.childNodes) if (n.nodeType === 3) own += n.textContent;
    own = own.trim();
    if (!own) continue;
    const cs = getComputedStyle(el);
    if (cs.visibility === 'hidden' || cs.display === 'none') continue;
    const first = cs.fontFamily.split(',')[0].replace(/["']/g, '').trim().toLowerCase();
    seen[first] = (seen[first] || 0) + own.length * parseFloat(cs.fontSize || '16');
  }
  return seen;
}"""

GENERIC = {"serif", "sans-serif", "monospace", "system-ui", "-apple-system", "cursive", "fantasy",
           "ui-sans-serif", "ui-serif", "ui-monospace", "emoji", "math"}


def typeface_issues(family_chars, *, limit=MAX_FAMILIES, min_share=0.01):
    """Return problems for a {family: weighted characters} map measured in the browser."""
    total = sum(family_chars.values()) or 1
    used = sorted((f for f, n in family_chars.items()
                   if f and f not in GENERIC and n / total >= min_share),
                  key=lambda f: -family_chars[f])
    if len(used) > limit:
        return [f"inconsistent typography: {len(used)} typefaces in visible text ({', '.join(used)}); "
                f"keep one type system across the whole site, at most {limit} families, "
                "including any illustrative demo content"]
    return []
