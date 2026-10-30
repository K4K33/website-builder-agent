# Kaurivo — premium animated studio website

A production-shaped, zero-paid-dependency, international-English website for Kaurivo.

## Where to view

Static GitHub Pages route after an explicitly approved merge into `main`:

`https://k4k33.github.io/website-builder-agent/kaurivo/`

The branch / PR is for review first. Do not change the root application or the website-builder-agent's prospecting pipeline. No commercial domains or paid hosting are needed at this stage.

## Original art direction

- Reuse the user-approved metallic split-K symbol (optimized from the original user-provided image).
- Black/dark navy, restrained silver and icy blue, editorial oversized type, geometric details.
- Study high-quality digital studios' editorial hierarchy and scroll pacing, while producing original design.
- The uploaded reference clip depicts an Apple-style product exploded-view assembly. Adapt the *principle* into a visual story explaining website design and development, never copy someone else's page or content.

## Demonstrated motion and design expertise

- Cinematic responsive browser mockup with ambient orbits and floating labels in the hero.
- Scroll-pinned, perspective-correct 3D HTML/CSS construction sequence: wireframe, typography, visual asset, CTA, HTML markup and navigation assemble into a site.
- Native browser WebGL custom fragment shader for animated ambient light (no JS libraries needed; content remains usable without WebGL).
- Kinetic marquee, pointer-friendly hover states, staggered on-scroll reveals, editorial inverse-color typographic break, concept previews.
- Real `mailto:hello.kaurivo@gmail.com` links.
- Full responsive CSS, keyboard focus, skip link, semantic sections, reduced-motion mode.

## Truthfulness

The two concept showcases are explicitly described as *concept studies*, not completed client work. No fabricated clients, five-star testimonials, awards, conversion lift, revenue claims, or fake contact details.

Before publicly launching the brand, replace concept work with verified, permitted portfolio samples when available. Do a copy review with the owner.

## Offline QA already completed in the working environment

Native browser via Playwright/Chromium (no external API calls): 1440×900, 768×1024, 390×844 and 320×740; no horizontal overflow; visual identity asset loaded; primary CTA valid; all four scroll chapters update; page errors absent; reduced-motion reveals functional.

The offline QA screenshot runner disables WebGL only in headless SwiftShader; the actual page includes native WebGL with graceful fallback. WebGL behavior and real-world mobile hardware should be revisited before claiming production-perfect performance.

## Deployment notes

GitHub Pages action in `.github/workflows/static.yml` publishes `website-builder-agent/website-builder-agent/docs` on main. This site lives under the `/kaurivo/` subpath, so asset references are relative.

No paid services, web design API calls, third-party JS bundles or secret tokens are required.
