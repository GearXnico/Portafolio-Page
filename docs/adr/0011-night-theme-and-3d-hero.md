# 0011 · Night theme and 3D hero

Status: accepted · Date: 2026-10-27

## Context

The first public version used system fonts, a light or dark theme that followed the device and plain cards. It worked, but it looked like any generated portfolio and said little about the person behind it. The new design is a neo-noir night city with interface details: one dark palette with a single neon accent, a display typeface for headings and labels, projects shown as film stills, and a neon figure in the hero that rotates, glitches and turns into another shape.

Constraints that any option must keep:

- The CSP stays as it is: `script-src 'self'`, `style-src 'self'`, `font-src 'self'`, no external hosts.
- The content has to be readable before any decoration loads, also on a slow phone.
- People who ask the device for reduced motion get a still page.

## Options considered

| Option | Cost | Limits |
|---|---|---|
| A. CSS and SVG only | No new dependency | Flat 3D (rotated rings and boxes); no real perspective, lighting or pointer response |
| B. three.js through react-three-fiber | ~242 kB gzip extra; a React renderer on top of three.js | More than a single figure needs; r3f pulls the whole three.js namespace |
| C. three.js used directly, loaded on demand | ~133 kB gzip extra, only when the figure is shown | A small imperative effect to set up and dispose the renderer |

## Decision

Option C. The hero renders the text and a static SVG skyline first; `web/src/components/Entity.tsx` and three.js are a separate chunk that is imported only when the screen is at least 48rem wide, the device doesn't ask for reduced motion and the browser has WebGL (`web/src/motion.ts`). Nothing else on the page depends on it.

The fonts (Chakra Petch and Barlow, SIL Open Font License) come from `@fontsource` packages, Latin subset only, and are bundled with the build, so `font-src 'self'` still holds.

The site has a single dark theme. The colors are CSS variables in `web/src/styles.css`, so a different accent only changes those variables; the figure reads `--accent` when it starts.

## Consequences

- A visitor on a wide screen downloads about 133 kB more, after the content. Phones and reduced-motion visitors don't download it at all.
- jsdom has no WebGL, so unit tests replace three.js with stand-ins: they check when the figure loads, that it swaps shapes and releases its resources, and that a WebGL failure leaves the hero without the figure instead of breaking the page. How it looks is checked by eye.
- The light theme is gone. Adding one later means a second set of the same variables.
