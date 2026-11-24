# Design skills for Kaurivo work

Loaded by Claude when it works in this repository.

- `impeccable/` — Impeccable by Paul Bakaus (Apache 2.0, see its LICENSE and NOTICE.md): design, critique, audit,
  polish, animate, typeset, bolder/quieter commands and the craft floor.
- `emil-*` — Emil Kowalski's design-engineering and animation skills (MIT, see each LICENSE), renamed with an
  `emil-` prefix so they do not collide with Impeccable's commands.

The builder itself (agents/builder.py) does not load skills; its distilled craft rules live in
`website-builder-agent/website-builder-agent/utils/craft_brief.py`.
