---
name: design-layout
description: Review and fix the reading layout of a swe-prep chapter on desktop and phone, including placement of code, figures, checks and asides. Use after a chapter is drafted and its visuals are in.
---

# Design review of a chapter's layout

The content is the author's job. Yours is how it reads on the page: rhythm,
placement, and whether the eye goes where the lesson goes.

## Look at it

Take screenshots with Playwright at 1280×900 and at iPhone size (390×844), the
top of the page plus every section. Also toggle light theme (`t`) once.

## Check

- **Rhythm:** no more than ~4 paragraphs in a row without something visual
  (code, figure, key idea, check, table). No section that's one huge wall.
- **Order inside a section:** words that raise the question → the figure or
  code that answers it → `.keyidea` → `.check`. A figure should never appear
  before the text that tells you why to look at it. Code follows the plain
  explanation, it doesn't replace it.
- **Code blocks:** short (aim ≤ 15 lines), placed next to the prose that
  explains them; side-by-side comparisons use `.cols` and stack on mobile.
- **Figures:** caption says what to look at; controls fit on one line on
  desktop and wrap cleanly on mobile; nothing overflows sideways.
- **Tables:** wrapped in `.table-wrap`; on mobile they scroll inside their box,
  not the page.
- **Asides:** "Go deeper" and "another way" sit right after the idea they
  extend, closed by default, and the summary text says what's inside.
- **Hierarchy:** h2 numbered sections, h3 for sub-steps only; the sidebar TOC
  reads as a sensible outline on its own.
- **Contrast and theme:** text and cell states readable in both themes.
- **Consistency:** same classes, spacing and patterns as the reference
  chapters. If you need a new pattern, add it to `assets/style.css` under the
  "Book chapters" block and document it in `templates/README.md`.

## Report and fix

List concrete changes with section ids ("s4: move the partition figure above
the code block; the code references it"). Make the fixes, then re-screenshot to
confirm. Check `document.documentElement.scrollWidth - innerWidth === 0` at
390px.
