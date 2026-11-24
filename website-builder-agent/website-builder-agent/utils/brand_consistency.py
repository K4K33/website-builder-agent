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


# Webfonts that the page asked for but the browser could not load fall back silently to
# a system face; a preview judged in that state looks nothing like what visitors get.
FONT_ERROR_SCRIPT = r"""async () => {
  await document.fonts.ready;
  const failed = [...document.fonts].filter(f => f.status === 'error').map(f => f.family.replace(/["']/g, ''));
  const linked = new Set();
  // Families the page requests from a webfont service or @font-face but that do not render:
  // measured against two different fallbacks, a missing face measures exactly like each fallback.
  const requested = new Set([...document.fonts].map(f => f.family.replace(/["']/g, '')));
  for (const link of document.querySelectorAll('link[rel~="stylesheet"][href*="family="]'))
    for (const m of link.href.matchAll(/family=([^:&;]+)/g)) {
      const fam = decodeURIComponent(m[1]).replace(/\+/g, ' ');
      requested.add(fam); linked.add(fam);
    }
  const ctx = document.createElement('canvas').getContext('2d');
  const width = f => { ctx.font = '40px ' + f; return ctx.measureText('Hamburgefontsiv Äö 0123').width; };
  for (const fam of requested) {
    if (width('"' + fam + '", monospace') === width('monospace') && width('"' + fam + '", serif') === width('serif'))
      failed.push(fam);
  }
  return [...new Set(failed)].map(family => ({family, external: linked.has(family)}));
}"""


def font_load_issues(failed):
    """Blocking problems for self-hosted faces that did not render.

    ``failed`` is the FONT_ERROR_SCRIPT result; plain family names are treated as self-hosted.
    Faces linked from an external font service are reported by external_font_notes instead,
    because browser QA blocks the network and cannot tell whether visitors would get them.
    """
    local = [f if isinstance(f, str) else f["family"] for f in failed
             if isinstance(f, str) or not f.get("external")]
    if not local:
        return []
    return ["webfonts failed to load (" + ", ".join(local) + "); the page renders in a fallback face, "
            "so typography cannot be judged and visitors may see a different design"]


def external_font_notes(failed):
    external = [f["family"] for f in failed if isinstance(f, dict) and f.get("external")]
    if not external:
        return []
    return ["typography reviewed in a FALLBACK face: " + ", ".join(external) + " is linked from an external "
            "font service that QA cannot load; self-host the woff2 files so the reviewed page matches the real one"]
