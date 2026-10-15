# DESIGN.md — "Editorial Dark" Design System
### Modeled on sharancreatedthis.in · Adapted for SBWoC'26

> **How this document was made.** I read the live site's home, `/portfolio`, `/products`, `/about` and `/contact` pages and extracted the structure, copy rhythm, section anatomy, labelling system, emphasis patterns and UX behaviour.
> **What I could and could not read.** The fetch returned the page content and metadata, not the stylesheet. So the following are **observed**: layout order, section numbering, eyebrow labels, which words are emphasised (italic), uppercase wordmark, timecode HUD, "typographic cover" cards, dark colour scheme and theme colour `#09090b`, nav/CTA/footer structure, accordion/stat/timeline patterns. The following are **my specified equivalents** because the font files and exact CSS values were not readable: font families, exact sizes, spacing values, easing numbers, accent colours. They are chosen to reproduce the same look and are marked **[spec]**. If you can send the site's CSS or a DevTools "Computed → font-family" screenshot, swap the family names in §4 and nothing else changes.

---

## 1. DESIGN PRINCIPLES

1. **Editorial, not "SaaS".** Big confident type, generous black space, short fragments, one idea per screen.
2. **One headline, two voices.** Every major headline mixes a clean grotesque sans with **one** italic serif word (the emotional word). This is the signature.
3. **Numbered chapters.** Every section is a "chapter": `NN / LABEL` eyebrow + headline + content. The page reads like a film's title sequence.
4. **Technical micro-details.** Mono timecodes (`REC • 00:01:24:08`), index numbers (`01 /`), `SCT / 04` catalogue codes, `/contact` path labels. They make the site feel engineered and authored.
5. **Same skeleton everywhere.** Header → hero (eyebrow + H1 + one-line sub) → chapters → closing CTA band → footer. Sub-pages never invent a new layout.
6. **Restraint.** Near-monochrome palette, one accent, hairline borders, motion that reveals rather than decorates.
7. **Content before chrome.** No clutter, no stock imagery, strong real imagery or typographic covers.

---

## 2. THE SIGNATURE: MIXED-FONT HEADLINES (read this first)

### 2.1 What the reference does (observed)
- Headlines are broken into short lines with deliberate line breaks: *"A filmmaker's eye. / A designer's instinct. / A builder's curiosity. / Always creating."*
- Within a headline, **one word or phrase is emphasised in italic**: *"Have an idea? Let's make it **real.**"* — `real.` is the italic accent. In stats, the **`+`** and **`–`** are italic: `180+`, `7–8`.
- Titles end with a **period**: `Hangly.` `Vision.` `Films.` `Sharan created this.` — periods are part of the brand voice.
- Wordmark is uppercase with a period: `SHARAN CREATED THIS.`
- Eyebrows are small uppercase tracking labels: `ONE MIND`, `THE PORTFOLIO`, `THE PRODUCT LAB`, `THE CURRENT CHAPTER`.
- Technical strings use a monospace voice: `REC • 00:01:24:08`, `SCT / 04`, `PROJECT STUDY / TYPOGRAPHIC COVER`.

### 2.2 The recipe (use this for every H1/H2)
```
[ Sans, tight, weight 500–600 ]  +  [ Serif italic accent word, weight 400 ]  +  [ period ]
```
Rules:
1. **One accent per headline.** Never two italic words in one headline. Pick the word that carries the feeling (a verb or a noun the reader should remember).
2. **Accent is the same size as the sans**, but optically heavier serif italics often look smaller — bump the italic **+4–6%** (`font-size: 1.05em`) and set `letter-spacing: -0.01em`.
3. **Baseline-align** sans and serif; do not shift vertically.
4. **Colour the accent** either in the same off-white (default) or in `--accent` at 100% (hero only). Never gradient text.
5. **Line breaks are authored**, not wrapped. Use `<br class="hide-on-mobile">` or separate `<span class="line">` blocks, and let mobile reflow naturally.
6. **Always end with a period** (headlines, product names, section titles). Eyebrows and buttons do not.
7. **Fragments over sentences.** 2–6 words per line, parallel structure, rule of three.

### 2.3 Example headlines (SBWoC'26 copy in this style)
| Where | Headline (sans · *serif-italic*) |
|---|---|
| Home hero | **Build.** **Contribute.** *Ship.* |
| Manifesto | **A maintainer's eye.** **A mentor's patience.** **A builder's *curiosity.*** |
| Chapter: My world | **Different projects.** **Same *restless* mind.** |
| Numbers | **Impact.** *In motion.* |
| Evolution | **Never just *one* thing.** |
| Selected work | **Made to *mean* something.** |
| Passport | **Proof, not *promises.*** |
| Products/projects | **Open source, *shipped.*** |
| Closing CTA | **Have a project? Let's make it *real.*** |
| About hero | **We're SBWoC. We make *things* happen.** |
| Contact | **Let's build something *worth* remembering.** |

---

## 3. DESIGN TOKENS

### 3.1 Colour (dark first; `color-scheme: dark`; the reference theme colour is `#09090b`)
```css
:root {
  /* Surfaces */
  --bg:            #09090b;  /* observed theme-color; page background */
  --bg-raised:     #0f0f12;  /* [spec] cards, header on scroll */
  --bg-sunken:     #060607;  /* [spec] footer, media wells */
  --bg-hover:      #16161a;  /* [spec] row/card hover */

  /* Text */
  --text:          #fafafa;  /* primary headlines */
  --text-2:        #d4d4d8;  /* body */
  --text-3:        #a1a1aa;  /* secondary / captions */
  --text-4:        #71717a;  /* eyebrows, meta, disabled */

  /* Lines */
  --line:          rgba(255,255,255,0.08);  /* hairlines */
  --line-strong:   rgba(255,255,255,0.16);
  --line-focus:    rgba(255,255,255,0.40);

  /* SBWoC accent system [spec] — brand direction from the strategy:
     icy white, electric blue, cyan, subtle violet. Use ONE at a time. */
  --accent:        #5b8cff;  /* electric blue — primary accent */
  --accent-2:      #22d3ee;  /* cyan — data / live indicators */
  --accent-3:      #8b7cf6;  /* subtle violet — gradients in media only */
  --accent-soft:   rgba(91,140,255,0.12);
  --rec:           #ef4444;  /* the REC dot only */

  /* Semantic */
  --success: #34d399; --warning: #fbbf24; --danger: #f87171;
}
```
**Colour rules:** 90% of any screen is `--bg`/`--text` tones. Accent appears in ≤ 3 places per viewport (primary CTA, one emphasised word, one live indicator). No coloured section backgrounds. Imagery supplies the colour.

### 3.2 Spacing, radius, borders [spec]
```css
--space-1: 4px;  --space-2: 8px;  --space-3: 12px; --space-4: 16px;
--space-5: 24px; --space-6: 32px; --space-7: 48px; --space-8: 64px;
--space-9: 96px; --space-10: 128px; --space-11: 192px;

--section-y: clamp(96px, 14vw, 192px);   /* vertical padding between chapters */
--gutter:    clamp(20px, 4vw, 48px);
--radius-sm: 8px; --radius-md: 14px; --radius-lg: 24px; --radius-pill: 999px;
--border: 1px solid var(--line);
```
Hairline borders (1px, 8% white) separate list rows, stat cells and table rows. Cards use large radii (`--radius-lg`) on media and `--radius-md` on small UI.

### 3.3 Elevation
Almost flat. Use **borders and subtle background shifts**, not shadows. The only glow allowed: a very soft radial `--accent-soft` behind the hero media and behind the primary CTA on hover.

### 3.4 Motion tokens [spec]
```css
--ease-out:      cubic-bezier(0.22, 1, 0.36, 1);   /* reveals */
--ease-in-out:   cubic-bezier(0.65, 0, 0.35, 1);   /* transitions */
--dur-fast: 160ms; --dur-base: 280ms; --dur-slow: 520ms; --dur-hero: 900ms;
```

---

## 4. TYPOGRAPHY SYSTEM

### 4.1 Three voices [spec — swap if you obtain the real families]
| Voice | Role | Recommended family (free) | Weights |
|---|---|---|---|
| **Sans** (display + UI + body) | headlines, nav, buttons, body | **Geist** or **Inter Tight** (headlines) + **Inter** (body) | 400 / 500 / 600 |
| **Serif italic** (accent) | the one emotional word per headline, italic `+`/`–` in stats, pull-quotes | **Instrument Serif Italic** (alt: *Fraunces Italic*, *Playfair Display Italic*) | 400 italic |
| **Mono** (system voice) | eyebrows with numbers, timecodes, catalogue codes, paths, stat indices | **Geist Mono** or **JetBrains Mono** | 400 / 500 |

```ts
// app/fonts.ts (Next.js)
import { Geist, Geist_Mono } from "next/font/google";
import { Instrument_Serif } from "next/font/google";
export const sans  = Geist({ subsets:["latin"], variable:"--font-sans", display:"swap" });
export const mono  = Geist_Mono({ subsets:["latin"], variable:"--font-mono", display:"swap" });
export const serif = Instrument_Serif({ subsets:["latin"], weight:"400", style:"italic", variable:"--font-serif", display:"swap" });
```
Fallbacks: `--font-sans: var(--font-sans), ui-sans-serif, system-ui, -apple-system, "Segoe UI", sans-serif;` `--font-serif: var(--font-serif), "Times New Roman", Georgia, serif;` `--font-mono: var(--font-mono), ui-monospace, "SF Mono", Menlo, monospace;`

### 4.2 Type scale (fluid) [spec]
| Token | Use | Size (clamp) | Line-height | Letter-spacing | Weight |
|---|---|---|---|---|---|
| `display-xl` | Home hero H1 | `clamp(56px, 11vw, 176px)` | 0.92 | -0.045em | 600 |
| `display-l` | Sub-page H1 | `clamp(44px, 8vw, 120px)` | 0.96 | -0.04em | 600 |
| `h2` | Chapter headline | `clamp(36px, 6vw, 88px)` | 1.0 | -0.035em | 500–600 |
| `h3` | Card/product title (`Hangly.`) | `clamp(28px, 3.6vw, 56px)` | 1.05 | -0.03em | 500 |
| `h4` | List titles (`Fashion Design`) | `clamp(20px, 2vw, 28px)` | 1.2 | -0.02em | 500 |
| `lead` | Hero sub-line, chapter intro | `clamp(18px, 1.6vw, 24px)` | 1.45 | -0.01em | 400 |
| `body` | Paragraphs | `17px` (16 on mobile) | 1.65 | 0 | 400 |
| `small` | Captions, meta | `14px` | 1.5 | 0 | 400 |
| `eyebrow` | `ONE MIND`, `THE PORTFOLIO` | `12px` | 1.2 | `0.18em` UPPERCASE | 500 |
| `mono-label` | `01 / MY WORLD`, `SCT / 04` | `12px` mono | 1.2 | `0.08em` UPPERCASE | 400 |
| `stat` | Big numbers (`180+`) | `clamp(64px, 9vw, 144px)` | 0.95 | -0.05em | 500 |
| `nav` | Header links | `14px` | 1 | `0.01em` | 500 |

### 4.3 Typographic details that make it feel "perfect"
- **Tight tracking on large type** (negative letter-spacing) and **tabular numerals** for stats: `font-variant-numeric: tabular-nums;`.
- **Optical alignment:** pull large headline text left by `-0.04em` to align the glyph edge with the grid.
- **Wordmark:** `SHARAN CREATED THIS.` style — uppercase, 600, `0.06em` tracking, ends with a period, 14–16px in header. For SBWoC: `SBWOC'26.` or `7BLOCKS · SBWOC'26.`
- **Italic `+` / `–` in stats:** number in sans (500), the suffix (`+`, `–`, `*`) in serif italic at 0.6em, raised to cap height. E.g. `180` `+`.
- **Index prefix:** `01 /` in mono `--text-4`, then the value in sans — `01 / 180+`.
- **Links in body:** underline offset `0.25em`, thickness `1px`, colour `--text`; on hover underline animates from left to right (`background-size` trick), 280ms.
- **Max line length:** body 62–68ch; headlines no limit but authored breaks.
- **Hanging punctuation / widows:** `text-wrap: balance` on headlines, `text-wrap: pretty` on paragraphs.
- **Emphasis in paragraphs:** `<strong>` = `--text` at 500; `<em>` = serif italic, same size.
- **Case:** headlines sentence case; eyebrows/labels uppercase; buttons sentence case ("Explore my world", "Let's talk").

### 4.4 Reusable CSS for the signature
```css
.h-mix { font-family: var(--font-sans); font-weight: 600; letter-spacing: -0.04em; line-height: .96; text-wrap: balance; }
.h-mix em, .accent-word {
  font-family: var(--font-serif); font-style: italic; font-weight: 400;
  font-size: 1.05em; letter-spacing: -0.01em; color: var(--text);
}
.hero .accent-word { color: var(--accent); }          /* hero only */
.eyebrow { font: 500 12px/1.2 var(--font-sans); letter-spacing: .18em; text-transform: uppercase; color: var(--text-4); }
.mono-label { font: 400 12px/1.2 var(--font-mono); letter-spacing: .08em; text-transform: uppercase; color: var(--text-4); }
.stat-num { font: 500 var(--stat) / .95 var(--font-sans); letter-spacing: -0.05em; font-variant-numeric: tabular-nums; }
.stat-num sup, .stat-num .suffix { font-family: var(--font-serif); font-style: italic; font-size: .6em; }
```

---

## 5. LAYOUT SYSTEM

### 5.1 Grid & containers
- **12-column grid**, max content width `1440px`, outer gutter `--gutter`. Text-heavy blocks use an inner `max-width: 720px` (7 columns).
- Hero and media can be full-bleed (edge to edge) with inner content aligned to the grid.
- Chapters alternate **left-heavy / right-heavy** compositions (headline in cols 1–7, supporting text in cols 8–12) to avoid monotony without changing the system.
- Breakpoints: `360 · 640 · 768 · 1024 · 1280 · 1440 · 1920`.

### 5.2 Page skeleton (identical on every page)
```
[Skip to content]
HEADER  (wordmark · nav · "Let's talk" pill)
MAIN
  HERO          eyebrow · H1 (mixed font) · lead · primary CTA
  CHAPTER 01…N  "NN / LABEL" · H2 · content
  CLOSING CTA   "NN / THE NEXT CHAPTER" · H2 · /path label · sub-line · CTA button
FOOTER  (wordmark · links · tagline · © · Back to top ↑)
```
Sub-pages (Portfolio, Products, About, Contact) **reuse this exact skeleton**; only the hero eyebrow/H1 and the middle chapters change. The closing CTA band and footer are **identical** on every page.

### 5.3 Section ("chapter") anatomy
```
┌─────────────────────────────────────────────────────────────┐
│ 01 / MY WORLD            ← mono-label (top-left, text-4)     │
│                                                              │
│ Different projects.      ← h2 (sans) + italic accent word   │
│ Same restless mind.                                          │
│                                                              │
│ I follow the idea.       ← lead (text-3), 2 short lines      │
│ Wherever it takes me.                                        │
│                                                              │
│ [content: list / grid / timeline / stats / media]            │
└─────────────────────────────────────────────────────────────┘
padding-block: var(--section-y); hairline top border var(--line)
```
Vertical rhythm: label → headline `24px`; headline → lead `24px`; lead → content `64–96px`.

---

## 6. GLOBAL COMPONENTS

### 6.1 Header
- Left: **wordmark** (uppercase + period). Centre/right: **Home · Portfolio · Products · About · Contact** (for SBWoC: **Projects · Leaderboard · Challenges · Mentors · Contributors · Resources · Sponsors · About**). Far right: **pill CTA "Let's talk"** (SBWoC: **"Apply now"**).
- Fixed at top, transparent over hero; on scroll > 24px: `--bg` at 72% + `backdrop-filter: blur(14px)` + bottom hairline. Height 72px desktop / 60px mobile.
- Active link: 1px underline offset 8px **or** a dot indicator; hover: text goes `--text-3 → --text` in 160ms.
- Mobile: hamburger → full-screen overlay menu with **large type links (h2 scale)**, staggered reveal, close on route change/ESC, focus trapped.
- **Skip to content** link is first in tab order (visible on focus).

### 6.2 Buttons
| Type | Style | Use |
|---|---|---|
| **Primary pill** | `--text` background, `--bg` text, radius pill, height 48, padding 0 24, arrow icon `→` that slides 4px on hover | "Explore my world", "Let's create something together" |
| **Header pill** | outline 1px `--line-strong`, text `--text`, height 40; hover fills `--text` | "Let's talk" |
| **Text link + arrow** | underline reveal, `→` | "Enter this world", "Explore Hangly", "View all work" |
| **Secondary text link** | `--text-3`, no arrow | "Privacy", "Documentation" |
| **Chip (filter)** | pill, 1px line, 36px; active = filled `--text` / `--bg` | Portfolio filters: All · Films · Photography… |
States: default · hover (lift 0, brightness/fill shift + arrow nudge) · focus-visible (2px `--text` ring, 3px offset) · active (scale .98) · disabled (40% opacity) · loading (inline spinner; width preserved).

### 6.3 Index list (the "My World" pattern)
Large vertical list: `01 Films / 02 Photography / 03 Design / 04 Products`. Each row: mono index, **h2-size title**, hairline between rows. **Hover/focus a row → the preview media beside it crossfades to that row's image** (280ms), other rows dim to 40%. Active row shows a short sentence + "Enter this world →" link. On mobile: tap-to-expand accordion with media above.

### 6.4 Media with HUD overlay
Film still full-width in a `--radius-lg` frame; overlay chips: top-left `● REC` (red dot, 1.4s pulse) + mono timecode `00:01:24:08` (ticks via JS), bottom-left caption `STORIES THAT STAY.` (eyebrow), bottom-right the category title (`Films.`). Subtle vignette gradient for legibility. For SBWoC replace with: `● LIVE` + `PR #2431 MERGED`, a build-log timecode, or `SBX +120`.

### 6.5 Stats grid ("The work, in numbers")
6 cells, 3×2 desktop / 2×3 tablet / 1×6 mobile. Each cell: mono prefix `01 /`, big number (sans) with italic suffix, label (`small`, text-3). Hairline grid lines. **Count-up on first view** (1.2s, ease-out), once.

### 6.6 Timeline ("The evolution")
Vertical list of 5 steps, each: mono `01`, h4 title (`Fashion Design`), one-line description in text-3. A **vertical hairline** runs down the left; a filled segment grows with scroll progress. The last item carries a tag **`THE CURRENT CHAPTER`** (accent dot + eyebrow) and renders brighter. For SBWoC: `Foundation → Builder → Engineer → Systems → Research`, last = "Current level".

### 6.7 Selected work grid
- Numbered cards `01…09`: media, **h3 title**, category line `Films / Malayalam short film` (text-3), index number top-right.
- Layout: first row asymmetric (1 large 7-col + 1 smaller 5-col), then 3-up grid. **Hover:** image scales 1.04 over 520ms, a "View" cursor/pill appears, title shifts +4px.
- **Typographic covers:** when no image exists, render a designed card: black surface, mono `SCT / 04`, huge title in sans with one italic word, footer mono `PROJECT STUDY / TYPOGRAPHIC COVER`. This avoids ugly placeholders — **never use grey boxes or stock photos.** For SBWoC: `SBWOC / 04 · Project Study / Repository Cover`, showing repo name, language dots, health ring.
- Portfolio page: filter chips above the grid, URL-synced (`?cat=films`), animated layout reflow (FLIP), result count live-region.

### 6.8 Product showcase block (Hangly / Vision pattern)
Two-column: left = **mockup/visual** in a rounded frame with floating microcopy ("A LITTLE JOY. JUST HANGING OUT."), right = eyebrow (`INDEPENDENT SOFTWARE · macOS + Windows`), **h3 `Hangly.`**, 2-line description, **two links** (primary "Explore Hangly →" + secondary "Privacy"). Alternate sides per block. For SBWoC: "SBX Score.", "Developer Passport.", "Project Copilot."

### 6.9 Accordion ("Creative philosophy")
Rows: mono `01`, h2-size title ("Start with curiosity."), `+` on the right (rotates 45° to `×`). Opens with height animation 320ms; only one open at a time; `aria-expanded`, `aria-controls`; the whole row is the button.

### 6.10 Closing CTA band (identical on every page)
```
06 / THE NEXT CHAPTER                (mono-label)
Have an idea? Let's make it real.    (h2 mixed; "real." italic accent)
/contact                              (mono path label, text-4, links to page)
A film. A brand. A product. Something entirely new.   (lead, text-3)
[ Let's create something together → ]                 (primary pill)
```
Centred, very large vertical padding, optional soft `--accent-soft` radial glow behind the headline.

### 6.11 Footer
Row 1: wordmark · links (**Download · Install · FAQ · Compare · Guides** → SBWoC: **Rules · SBX · FAQ · Verify · Guides · GitHub**). Row 2: tagline **"Independent mind. Infinite possibilities."** (SBWoC: **"Build open source. Ship real software."**), `© 2026`, **Back to top ↑**. Contact page adds a sign-off line: `MADE OF CURIOSITY. BASED IN INDIA. CREATING EVERYWHERE.` in eyebrow style. Social links are icon + text, 4 items with mono index (`01 Email · 02 Instagram · 03 LinkedIn · 04 Behance`).

### 6.12 Tables, FAQ, long-form
The sub-pages end with **long-form SEO/editorial content** (comparison table, "who is it for", FAQ). Keep it calm: body 17px, max 68ch, h2/h3 sans without italics, tables with hairline rows and sticky first column on mobile, FAQ as accordion. This content sits **below** the visual chapters and above the closing CTA.

### 6.13 Forms (for Apply / Submit)
Underline-style or soft-border inputs on `--bg-raised`, 52px height, label above in `small` text-3, floating helper text, error text in `--danger` with icon, focus ring `--line-focus` + 2px accent underline. One question group per step with a mono progress label `STEP 02 / 05` and large H2 for the question.

---

## 7. PAGE TEMPLATES (same layout, different content)

### 7.1 Home
1. **Hero:** full-height. Left: eyebrow (`SBWoC'26 · Winter of Code`), **display-xl H1** with one italic word, lead, primary CTA. Right/behind: hero media (portrait or a generated grid/particle field in winter motif) with soft glow. Scroll cue (mono `SCROLL` + thin line).
2. **Manifesto ("ONE MIND"):** eyebrow + 4-line H2 (authored breaks), 2-line lead, **two stats** inline + social links row.
3. **01 / MY WORLD:** index list + media preview (see 6.3).
4. **02 / THE WORK, IN NUMBERS:** stats grid (6).
5. **03 / THE EVOLUTION:** timeline (5).
6. **04 / SELECTED WORK:** numbered grid (+ "View all work").
7. **05 / BUILT FROM CURIOSITY:** product showcase blocks (2).
8. **06 / THE NEXT CHAPTER:** closing CTA band.
9. Footer.

### 7.2 Listing page (Portfolio → Projects, Challenges, Mentors, Contributors)
Hero (eyebrow `THE PORTFOLIO`, H1 `A point of view. In every frame.`, lead) → **filter chips row** → numbered grid → editorial long-form block ("One practice, two halves" style) → closing CTA → footer.

### 7.3 Showcase page (Products → SBX, Passport, Program)
Hero (`THE PRODUCT LAB`, `Curiosity, shipped.`) → product showcase blocks → "Two apps, two unrelated problems"-style explainer → comparison table → "Who each one is for" (suits you / wrong pick) → downloads/links list → FAQ accordion → closing CTA.

### 7.4 Story page (About)
Hero (`THE PERSON BEHIND THE PIXELS`, `I'm Sharan. I make things happen.`) → portrait with caption `Sharan — Creator & builder` → `01 / WHO I AM` → `02 / WHY I CREATE` → evolution timeline → stats → `04 / CREATIVE PHILOSOPHY` accordions → `05 / WHAT COMES NEXT` → closing CTA.

### 7.5 Contact page
Hero (`GOOD THINGS START WITH A CONVERSATION`, `Let's build something worth remembering.`) → lead → primary CTA "Start a conversation" → **4 numbered channel links** → editorial blocks ("About", "What I build", "Working together" with four kinds of conversation) → FAQ → "Elsewhere on this site" link list → sign-off line → footer. (Show the email as a button + copy-to-clipboard with toast; don't expose the raw address to scrapers.)

### 7.6 Mapping to SBWoC dashboards (app pages)
Keep tokens, type scale, eyebrow/mono labels and hairlines; **reduce** display sizes (h2 max 40px), use `body 15px`, tables with hairline rows, stat cells reuse 6.5, sidebar uses wordmark + mono section labels (`01 / OVERVIEW`), page title uses the **same mixed-font recipe at h2-small size** (e.g. *Your **impact.***). No full-bleed media in dashboards.

---

## 8. MOTION & INTERACTION

| Moment | Behaviour | Timing |
|---|---|---|
| **Page load** | Wordmark/nav fade; hero lines reveal **line by line** (mask-up: `translateY(100%) → 0` inside `overflow:hidden`), accent word reveals last | 900ms, 90ms stagger |
| **Scroll reveals** | Headlines mask-up per line; paragraphs fade-up 16px; media clip-path/scale-in 1.06 → 1 | 520ms, `--ease-out`, once |
| **Stats** | Count-up on first view | 1200ms |
| **Timeline** | Progress line fills with scroll; active step brightens | scroll-linked |
| **Index list hover** | Row dims others, preview crossfade | 280ms |
| **Cards** | Image zoom 1.04, title nudge | 520ms |
| **Buttons** | Arrow slides 4px, fill shift | 160–280ms |
| **Accordion** | Height + `+`→`×` rotate | 320ms |
| **Header** | Blur/background fade after 24px; hides on scroll-down, shows on scroll-up | 280ms |
| **Route change** | Fade-through (opacity 0→1) with scroll to top; no layout flash | 280ms |
| **REC dot** | Pulse | 1.4s loop |
| **Cursor** (optional, desktop) | Small ring that grows to a "View" label over media | 160ms |

Rules: animate **transform/opacity only**; trigger once; honour `prefers-reduced-motion` (replace with opacity-only 120ms fades, stop pulse/parallax/count-up); never block interaction during an animation; keep total simultaneous animations ≤ 6.

---

## 9. UX SPECIFICATION

### 9.1 Navigation & wayfinding
- Persistent header; current page indicated; **"Let's talk"/"Apply now" CTA always visible**.
- Every page ends with the same CTA band → no dead ends.
- Numbered chapters help users know where they are; consider a thin **scroll-progress bar** (1px, accent) under the header on long pages.
- **Back to top ↑** in footer; also appears as a floating mini-button after 1.5 viewports.
- Breadcrumbs only on deep pages (project detail, challenge detail): `Projects / Repository`.

### 9.2 Interaction principles
- Hit areas ≥ 44×44px; whole cards clickable; hover states always paired with focus-visible states.
- Filters update instantly, preserve scroll, update URL, announce count via `aria-live="polite"`.
- Forms: validate on blur, summarise on submit, focus first error, preserve input on failure, success screen with next action.
- Copy-to-clipboard shows a toast ("Email copied").
- External links: `target="_blank" rel="noopener noreferrer"` with a small `↗`.

### 9.3 Accessibility
- Contrast: body `--text-2` on `--bg` ≥ 12:1; `--text-4` only for non-essential metadata (≥ 4.5:1 at 12px+ — verify; lighten to `#8b8b94` if it fails).
- Semantic landmarks (`header`, `nav`, `main`, `footer`), one `h1` per page, ordered headings; **the italic accent word is visual only** (don't wrap in extra headings; screen readers read the heading normally).
- Alt text on all media; decorative HUD overlays `aria-hidden`; timecode has no live announcements.
- Visible focus ring everywhere; accordion/menu/dialogs use correct ARIA and ESC to close; skip link first.
- Reduced motion fully supported.

### 9.4 Performance
- Fonts via `next/font` with `display: swap`, only used weights; serif loaded for italic 400 only.
- Hero media: `priority`, AVIF/WebP, explicit dimensions; all other images lazy; `content-visibility: auto` on long sections.
- Particles/canvas dynamically imported, paused off-screen.
- Targets: LCP < 2.5s, CLS < 0.05, INP < 200ms.

### 9.5 Responsive behaviour
| Element | Desktop | Tablet | Mobile (≤ 640) |
|---|---|---|---|
| Header | full nav + pill | nav collapses to menu | hamburger overlay with large links |
| Hero H1 | display-xl | display-l | clamp min 56px, 3–4 authored lines |
| Index list | list + side preview | list + preview below | accordion with media inside |
| Stats | 3×2 | 2×3 | 1×6 or 2-col compact |
| Work grid | asym + 3-up | 2-up | 1-up |
| Product blocks | 2-col alternate | stacked | stacked, media first |
| Timeline | vertical with side hairline | same | same, tighter |

### 9.6 States
Every data block has **skeleton** (hairline-outlined shapes, no shimmer glare), **empty** (a one-line fragment in the brand voice + one CTA, e.g. "Nothing here yet. Be the first to ship."), **error** (plain sentence + retry), **success** (period-ended confirmation + next step).

### 9.7 Voice & copy rules
Short fragments; rule of three; periods on titles; verbs of making (build, ship, create, prove); no jargon walls above the fold; long explanatory content goes **below** the visual chapters; honest, specific, quotable sentences.

---

## 10. SBWoC'26 ADAPTATION CHECKLIST

| Reference element | SBWoC equivalent |
|---|---|
| Hero portrait | Winter-grid / node-field visual, or a Passport card floating with a live SBX counter |
| `Sharan · Creative Technologist` | `SBWoC'26 · 7Blocks Winter of Code` |
| `Explore my world` | `Explore projects` |
| `ONE MIND` manifesto | Core loop: Discover → Build → Review → Ship → Measure → Prove → Grow |
| `01 / MY WORLD` (Films, Photography, Design, Products) | `01 / THE TRACKS` (Contributor, AI Builder, Mentor, Community Lead, Research Builder) |
| Numbers (180+ films) | Live impact: projects, merged PRs, contributors, mentors, SBX shipped, deployments |
| Evolution (Fashion → Creative Technologist) | Levels: Foundation → Builder → Engineer → Systems → Research |
| Selected work (9 cards + typographic covers) | Featured projects (repo covers with language dots, health ring) |
| Products (Hangly., Vision.) | `SBX.` · `Passport.` · `Copilot.` |
| Closing CTA | `Have a project? Let's make it real.` → Apply / Submit a project |
| Footer tagline | `Build open source. Ship real software. Prove your impact.` |
| Contact "four kinds of conversation" | Four ways to join: Contribute · Mentor · Submit a project · Sponsor |

---

## 11. IMPLEMENTATION NOTES (Next.js + Tailwind + shadcn)

- Put tokens in `:root` CSS variables (§3) and map them in `tailwind.config` (`colors`, `fontFamily`, `fontSize` with clamp, `spacing`, `borderRadius`, `transitionTimingFunction`). No hardcoded values in components.
- Create primitives: `<Eyebrow/>`, `<MonoLabel/>`, `<MixedHeading as="h1|h2" parts={[{t:"Let's make it "},{t:"real.",accent:true}]}/>`, `<Stat/>`, `<IndexList/>`, `<Chapter label="01 / MY WORLD">`, `<CtaBand/>`, `<TypographicCover/>`, `<HudMedia/>`.
- `MixedHeading` is the single source of the signature: it renders sans text + `<em class="accent-word">` and enforces one accent word, trailing period and authored line breaks.
- Use `Chapter` for every section so spacing, label style and reveal animation stay identical page to page.
- Animations via the shared motion tokens (§3.4); line-mask reveal as a reusable `<RevealLines>`.
- Preview a **`/dev/styleguide`** page that shows every component in every state.

---

## 12. QA CHECKLIST (design acceptance)

- [ ] Every H1/H2 uses the mixed-font recipe with exactly one italic accent word and a trailing period (hero/CTA/chapters).
- [ ] Every page follows the skeleton (§5.2) and ends with the identical CTA band + footer.
- [ ] Eyebrows are uppercase tracked; chapter labels use mono `NN / LABEL`; stats use tabular numerals and italic suffixes.
- [ ] No grey placeholder boxes; missing imagery uses typographic covers.
- [ ] Accent colour appears ≤ 3 times per viewport; no coloured section backgrounds; no gradient text.
- [ ] Hairline borders only (1px, 8%); no heavy shadows.
- [ ] Header blur/transition, mobile overlay menu, skip link, focus rings all work.
- [ ] Reveals, count-ups, hover previews, accordions run smoothly; reduced-motion verified.
- [ ] 360 → 1920 verified; no horizontal scroll; headlines break as authored on mobile.
- [ ] Contrast, landmarks, heading order and keyboard paths pass axe with 0 serious/critical issues.
- [ ] LCP < 2.5s, CLS < 0.05 on Home, Projects, Leaderboard, Passport.