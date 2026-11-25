# Kaurivo palette selection rules (from Purist design guidance)

These rules extend [the colour theory guide](KAURIVO_COLOUR_GUIDE.md). They never
override it. Order of authority: the client's approved identity and real source
photography first, the colour theory guide second, these rules third. Use them to
choose and defend a palette when identity material is thin, and to stop different
companies from receiving the same palette.

## Choose a mood, then derive colours from objects

Before writing any hex value, commit to one **mood word**: a physical condition or
register, for example sun-bleached, overcast, inky, mineral, botanical, maritime,
bookish, alpine, candlelit, chalky, tidal, pastoral, gallery, editorial.
Derive every colour from a named object in that scene (mineral: limestone dust,
weathered slate, oxidised copper). A role with no matching object makes the palette
abstract and it will look assembled. Offer both obvious and less obvious mood
candidates per sector and do not default to the first instinct.
Record the mood word and the objects in the concept's brand_continuity field.

## Proven ground and accent pairings

Families to interpret, not fixed values. Pick the hex inside the family from the mood.

| Mood | Ground x primary accent |
| --- | --- |
| mineral | bone x oxidised copper |
| maritime | fog grey x deep navy |
| rusted | graphite x rust |
| industrial | concrete x safety orange |
| bookish | plaster x ink |
| chapel | slate x amethyst |
| candlelit | warm amber x oxblood |
| botanical | bone x moss |
| tropical | palm shadow x hibiscus |
| alpine | snow x evergreen |
| nocturnal | wet asphalt x hot pink |
| signage | ink x chrome yellow |
| gallery / pop | pure white x cadmium red |
| editorial / saturated | pure white x cobalt |
| hypertext | pure white x hyperlink blue |
| highlighter | pure white x fluorescent yellow |
| brutalist | pure white x pure black, no third colour |

## Pairings to avoid

- Warm off-white with red, orange, terracotta or burnt sienna (recent cliche).
- Warm off-white with a fluorescent accent.
- Dark navy or charcoal with electric purple, lime or teal (overused 2019-2024 SaaS look).
- Pure white with a muted earth tone. Earth tones need a ground tinted from the same scene.
- A tinted warm ground with a high-chroma accent. The tint mutes the chroma. Use pure white or pure black instead.

## Neutrals

- Pure white (#FFFFFF) is the ordinary ground for business, product and marketing
  sites. Default to it when the accent is high-chroma, the work is typographic, or
  the mood does not call for a tinted ground.
- Off-white (cream, ivory, bone) is a specific aesthetic (sun-bleached, candlelit,
  pastoral, bookish, vintage), not a generic neutral.
- Greys come from the scene (mineral: slate, maritime: fog) or stay truly neutral
  (#EEEEEE, #CCCCCC, #888888, #444444). A tinted grey with no scene reason reads as
  indecision.
- Pure black is correct when the accent is high-chroma, the client asks for it, or
  the mood is inky, nocturnal or subterranean. Otherwise tint the dark toward the
  mood (warm charcoal for candlelit, graphite for maritime).

## Secondary accents

Allowed when they do a job: grouping, data visualisation, semantic states. Take them
from the same scene as the primary accent. Keep one primary colour as the anchor and
the overall saturation conservative; with several accents, spend less on other
decoration. One intense colour moment is stronger than five.

## Distinct palettes across companies

When several demos or customer sites are produced in the same batch, each gets its
own mood word and its own pairing. Two companies of different sectors must not
resolve to the same ground x accent pair. Record the pair and flag a repeat.

## Contrast reminders (supplements the guide's validation section)

- Text must be readable at a glance. Use reduced opacity and muted text sparingly.
- Be extra strict below 16 px. Avoid text of 12 px or smaller except in dense
  productivity UI or stylistic all-caps.
- Text on a light ground uses the ink colour, never white.
- Text on a photograph always gets a stable backing (a scrim or a semi-opaque layer),
  but the scrim must not blacken the photograph so far that its subject disappears.
  Check the first frame at desktop and phone width.

## Kaurivo's own site

Strategy: editorial / saturated, pure white x cobalt. Keep the current cobalt value.
Ink is black or near black (allowed because the accent is high-chroma). Greys are
truly neutral. Do not add a tinted or warm ground against the cobalt and do not add
a second saturated colour. Semantic feedback colours only for success and error.
