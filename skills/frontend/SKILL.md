---
name: frontend
description: "MUST USE for frontend/web UI/UX/visual work: building, styling, redesigning pages/components, React setup, performance audits, visual QA, taste, and polish. Routes four rulesets: design taste router and brand references; perfection for Playwright/Chromium Lighthouse/Core Web Vitals; ui-ux-db palettes/fonts/guidelines; designpowers personas/accessibility/critique/handoff; plus enhanced capability routers for atmosphere/motion (react-bits), micro-interactions (beui.dev), CSS paged media (print-paged-media), and spatial layout. Triggers: frontend, UI, UX, design, redesign, styling, layout, animation, motion, ambience, micro-interactions, react-bits, beui.dev, print-paged-media, pdf export, premium, luxury, minimal, brutalist, Awwwards, DESIGN.md, mockup, React, Lighthouse, accessibility, WCAG, Core Web Vitals, looks generic, make it pretty, like X brand, lazyweb, design research."
---

# Frontend

This file is a router, not a rulebook. The rules live in four rulesets under `references/`; your first job is to load the smallest set of files that covers the request, state which you loaded in one sentence, then execute under their guidance. Loading nothing and freestyling produces the generic AI-slop output this skill exists to prevent; loading everything wastes context and creates contradictory instructions.

**The bar is not clean-and-correct — it is work a senior designer at Linear, Stripe, or Supabase would ship.** Correct-but-flat is a failure, not a finish. Protect the surface as hard as you protect the build: design is a first-class deliverable, not a one-shot decision you lock and walk away from.

## Phase 0 — Route (before any UI work)

| Request involves… | Read |
|---|---|
| ANY UI implementation, styling, redesign, mockup, or visual decision | `references/design/README.md` FIRST. It enforces two mandatory gates — the Design System Gate (a `DESIGN.md` must exist before any component is written) and the React Dev Tooling Gate (react-grab / react-scan / react-doctor installed by default) — then routes to the taste and brand references below. |
| Spatial layout & component hierarchies — app shells, scroll ownership, "what goes where", responsive reflow, or section hierarchy ordered by user decision paths | ALSO `references/design/layout-skill.md` for mechanics, then `references/design/stylegallery.md` to fetch a named pattern contract for that exact spatial problem. Stacks on the style skill with zero visual overhead. |
| CSS Paged Media & PDF export — printable reports, invoices, HTML decks printed to paper, headless-Chrome PDF pipelines, or page-break fragmentation defects | ALSO `references/design/print-paged-media.md` for `@page` CSS, page boxes, fragmentation properties (`break-inside: avoid`), atomic blocks, and page-break rules. Stacks on the routed style skill. |
| Micro-interactions — button haptics, spring physics, subtle border beam glows, elevation hover states, tactile transitions, or gestures | ALSO `references/design/interaction-skill.md`. Anchored to `beui.dev` patterns: map nearest pattern, adapt mechanisms to `DESIGN.md` motion tokens, and respect `prefers-reduced-motion`. Stacks on the routed style skill. |
| Atmosphere & motion effects — animated background particles, ambient glows, fluid canvas shaders, typographic reveals (split, blur, shimmer, typewriter, marquee), card surfaces (spotlight, tilt, glare) | ALSO `references/design/ambience-skill.md`. Anchored to `react-bits` patterns: extract mechanisms, enforce retrofit checklist (reduced motion, off-screen pause via IntersectionObserver, compositor-only, tokens, budget); one atmosphere per hero. Stacks on the routed style skill. |
| Writing or modifying frontend code, OR auditing performance / SEO / accessibility / quality | ALSO `references/perfection/README.md`. Lighthouse 100 in every category, measured on real Playwright Chromium (never the `lighthouse` CLI), achieved through architecture — never by dropping animations or hiding content. |
| Looking up a concrete style, color palette, font pairing, chart type, landing-page structure, or UX guideline — or generating a project design system from keywords | `references/ui-ux-db/README.md`. A searchable CSV database with a CLI; a lookup tool, not a posture. Load on demand; `design` stays the source of truth for taste and the `DESIGN.md` contract. |
| ANY implementation or redesign that creates or updates `DESIGN.md` — plus explicit operating-layer asks (personas, critique, debt, handoff, synthetic user testing) | `references/designpowers/README.md` + `references/designpowers/lane-c-review.md`. An internal frontend ruleset, not a separate skill: lane-c is the Phase Final flatness/critique reviewer, and its accessibility-constraints and accepted-debt language fills the required `DESIGN.md` sections. Load other lanes only when their phase applies. |

**For implementation work, design + perfection load together.** A page that hits Lighthouse 100 but looks like AI slop has failed; a page that looks beautiful but ships a 2 MB bundle has failed. Both win or neither does.

## Design System and Component Workflow

Every implementation must choose one of these branches before UI code changes:

1. **Concrete visual reference:** the user supplied a reference — treat it as the visual contract, then handle it by kind:
   - **Static visual reference** (screenshot, generated mockup, Stitch/Imagen output, Figma export, overview, or annotated packet): load `references/design/image-to-code-skill.md` plus the relevant design/perfection files, extract the reference's exact tokens, layout geometry, copy, spacing, states, and responsive intent into `DESIGN.md`, then implement reusable primitives against that contract.
   - **Live site or URL reference** (the user names a site to clone or gives a URL): load `references/design/clone-from-url.md`. Drive a real browser and extract the runtime truth via `getComputedStyle` — tokens, layout geometry, default/hover/focus/active states, transitions and keyframes, and downloaded assets — into `DESIGN.md`, then clone-code reusable primitives against that contract.
   Final QA for both runs `/visual-qa` in reference-fidelity mode: compare the actual UI against the reference pixel-by-pixel and verify the code is an extensible design-system implementation, not a screenshot-matched one-off.
2. **Greenfield or fresh setup:** if the user gave no concrete visual reference, design research is a build step with named deliverables — not exploration to be budgeted. Exploration-stop instincts ("enough exploration", two-wave caps) do not apply here. Fire every research lane IN PARALLEL before `DESIGN.md` is written, and open `DESIGN.md` with a `## 0. Research Log` section recording each lane's deliverable — a lane with no Research Log line did not run. Skip a lane only when its tool or network is genuinely unavailable, and name the skip in `DESIGN.md`:
   - **Embedded references:** use `references/design/_INDEX.md` to shortlist 2-3 plausible Layer B references, then read exactly one Layer A style skill and one Layer B reference in full — every line, no partial reads (they are 200-500 lines; a sliced read produces the flattened token set this gate exists to prevent). Log the shortlist, the pick, and why. Use `open-design` only when the curated set has no fit; add `ui-ux-db` lookups for palette/type/domain questions.
   - **Lazyweb real-product screens:** READ `references/design/lazyweb.md` FIRST and run its recipe verbatim — do not improvise curl calls against lazyweb.com; the recipe mints its own anonymous token. Log the queries run, how many screens you actually VIEWED, and the layout grammar harvested — never pixel copies.
   - **StyleGallery spatial patterns & component hierarchies:** read `references/design/stylegallery.md` and fetch the pattern whose primary spatial problem matches the screen. Log the pattern adopted and the element that owns the scroll.
   - **Imagen concept drafts:** generate 2-3 imagen concept drafts, each seeded with the loaded Layer A + Layer B tokens (palette, type, material); pick the strongest and treat the chosen draft as the reference-fidelity contract. Log the draft paths and the pick.
   Synthesize every lane into `DESIGN.md`. Treat sources as source material, not mood labels: extract tokens, layout grammar, component anatomy, interaction states, motion, and taste decisions, then recombine them into project-specific primitives. Before laying out sections, inventory the content blocks and assign each a job — hook, explain, prove, compare, convert, navigate, retain — then order sections by the visitor's decision path, not by visual symmetry. Never freestyle past the selected references, never copy logos or brand-specific copy. Then run the Primitive Showcase Gate (`references/design/README.md` Phase 0) before any product screen.
3. **Existing project with `DESIGN.md` or a component system:** read it, follow it, and update it before implementation only when the requested work needs a new token, primitive, state, motion rule, accessibility constraint, accepted debt, or reference-fidelity requirement.
4. **Existing project with UI but no `DESIGN.md` and no reusable component layer:** STOP and ask the user one focused question: should you preserve the current look with copy-nearby styling, or extract a real `DESIGN.md` plus reusable components before continuing? Do not silently choose.

For implementation, redesign, or design-system work that creates or updates `DESIGN.md`, `references/designpowers/README.md` + `lane-c-review.md` are part of the default load — feed their personas, accessibility, critique, debt, handoff, and role-reference guidance into the branch above. The resulting `DESIGN.md` is the implementation contract: tokens, typography, spacing, primitives, motion, responsive behavior, accessibility constraints, and accepted debt must be named there before code uses them. Verify component primitives, states, and final screens with real visual QA evidence; pass design-system decisions, implementation evidence, and unresolved debt into `/review-work` for significant implementation work.

## Ruleset 1 — design (`references/design/`)

The reference library has one architecture file, 12 taste skills (Layer A — *how to execute*), and 70 brand design systems (Layer B — *what it should look like*). Most non-trivial tasks load **one Layer A + one Layer B**. `README.md` carries the full routing flow, stacking rules, anti-patterns, and the mandatory browser-based Design QA phase; `_INDEX.md` catalogs all 83 files with mood-to-brand mappings — read it whenever routing is not obvious from the tables below.

### Layer 0 — architecture

| File | Read when |
|---|---|
| `design-system-architecture.md` | The project has no `DESIGN.md` (defines the structure you must create first — 8 sections plus a greenfield-only `## 0. Research Log`), or you are extracting a design system from existing UI code. |

### Layer A — taste skills (pick AT MOST ONE style skill; they encode opposing philosophies)

| File | Read when the user says… |
|---|---|
| `taste-skill.md` | Neutral or operational UI with no surface ambition — internal tools, dashboards, "just make it usable". The safe default; do NOT settle here when the brief signals glossy / premium / startup-grade craft. |
| `gpt-tasteskill.md` | "Awwwards-tier", "wow factor", "cinematic", "scroll-triggered" marketing/landing experiences. |
| `minimalist-skill.md` | "minimal", "clean", "Notion-like", "Linear-like", "editorial". |
| `brutalist-skill.md` | "brutalist", "raw", "Swiss", "experimental", "anti-design". |
| `soft-skill.md` | "premium", "luxury", "calm", "expensive", "elegant", AND glossy / glassy / liquid-glass / startup-grade product surfaces — pair with a high-craft Layer B (`supabase`, `linear.app`, `vercel`, `stripe`). |
| `redesign-skill.md` | Improving EXISTING UI — "this looks bad", "fix the design". Audit-first workflow; never use on greenfield. |
| `image-to-code-skill.md` | "Generate the design first, then code it." Pair with one imagegen file below. |
| `output-skill.md` | Stacks on any style skill when output is incomplete — placeholders, `// TODO`, half-done components. |
| `stitch-skill.md` | Stacks on any style skill for Google Stitch compatibility or a `DESIGN.md` doc export. A complete worked export ships as `stitch-design-example.md`. |
| `interaction-skill.md` | Stacks on any style skill when work adds or changes micro-interactions (`beui.dev` style button haptics, spring physics, subtle border beam glows, elevation hover states). Read mapped component source, adapt to `DESIGN.md` tokens; reduced motion always. |
| `ambience-skill.md` | Stacks on any style skill when work adds hero atmosphere or motion effects (`react-bits` style background particles, ambient glows, fluid canvas shaders, text reveals). Run retrofit checklist; one atmosphere per hero, cursor effects quarantined. |
| `imagegen-frontend-web.md` / `imagegen-frontend-mobile.md` / `imagegen-brandkit.md` | Image-only output (mockup, app-screen concepts, brand board). These NEVER write code — switch to `image-to-code-skill.md` if code is wanted. |

### Layer B — brand design systems (orthogonal to Layer A; stack freely)

When the user names a brand or site — "Linear-style", "like Stripe's landing", "Aside-style browser agent" — load `references/design/<brand>.md` as the token source of truth (palette, type scale, components, do/don'ts). Coverage includes `aside` `apple` `stripe` `linear.app` `notion` `vercel` `claude` `figma` `airbnb` `nike` `tesla` `spotify` `raycast` `revolut` and ~56 more; the full list with mood shortcuts is in `_INDEX.md`. Extract the tokens and apply them to the project's own content — never copy logos or trademarked imagery. If the named brand is missing, fall back to a Layer A mood match or the `open-design` skill.

### Enhanced capability routers (orthogonal to style; stack on any style skill)

| File | Capability | Key Guidance & Constraints |
|---|---|---|
| `references/design/ambience-skill.md` | **Atmosphere & motion effects** | `react-bits` style background particles, ambient glows, fluid canvas shaders, text reveals (split, blur, shimmer, typewriter, marquee), spotlight/tilt/glare card surfaces. Mandatory: run retrofit checklist (reduced motion, off-screen pause via `IntersectionObserver`, GPU-composited only, performance budget). Maximum 1 ambient background per hero. |
| `references/design/interaction-skill.md` | **Micro-interactions** | `beui.dev` style button haptics, spring physics (150–250ms), subtle border beam glows, elevation hover states, gesture feedback, tactile transitions. Map mechanisms directly to `DESIGN.md` motion tokens; never use linear easing for physical interactions. |
| `references/design/print-paged-media.md` | **CSS Paged Media & PDF export** | Printable reports, invoices, statements, and PDF export via `@page` CSS and page-break rules. Enforce `@page` margin/size declarations, page boxes, fragmentation properties (`break-inside: avoid` on cards/tables), orphan/widow prevention (`orphans: 3; widows: 3`), and test in headless Chrome print emulation. |
| `references/design/layout-skill.md` + `stylegallery.md` | **Spatial layout & component hierarchies** | Structural app shells, scroll ownership, viewport containment, responsive reflow, and content-first component hierarchies. Order sections by user decision path (hook -> explain -> prove -> compare -> convert) rather than arbitrary visual symmetry. |

### React dev tooling

| File | Read when |
|---|---|
| `react-dev-tooling-skill.md` | A React project lacks react-grab / react-scan / react-doctor, or you need per-framework install snippets and the dev-only gating pattern (`NODE_ENV === 'development'`). |

## Ruleset 2 — perfection (`references/perfection/`)

| File | Read when |
|---|---|
| `README.md` | Any frontend code is written or audited. Carries the seven tenets: real-browser audits only, 100-in-every-category floor, fix-at-the-architecture, never weaken UX for points, design-system compliance checks, and the response format for audit reports. |
| `react-perf-tooling.md` | Before ANY React audit. The Playwright + `playwright-lighthouse` + `react-scan/lite` injection recipe, per-route render budgets, and the React-specific root-cause checklist. Lighthouse 100 with 30+ unnecessary renders is NOT done. |

Audit CLI (build for production first; never measure a dev server):

```bash
uv run "<skill-root>/scripts/perfection/lighthouse-audit.py" https://localhost:3000
```

Run mobile AND desktop presets, 3–5 runs, take the median, diagnose from the JSON report.

## Ruleset 3 — ui-ux-db (`references/ui-ux-db/`)

`README.md` documents the search CLI and the master-plus-overrides persistence pattern. The CLI (run from the ruleset directory so it finds `data/`):

```bash
python "<skill-root>/references/ui-ux-db/scripts/search.py" "<query>" --design-system -p "Project"   # full design-system generation
python "<skill-root>/references/ui-ux-db/scripts/search.py" "<query>" --domain <domain>             # targeted lookup
python "<skill-root>/references/ui-ux-db/scripts/search.py" "<query>" --stack <stack>               # stack best practices
```

Domains: `product` `style` `typography` `color` `landing` `chart` `ux` `react` `web` `prompt`. Stacks: `html-tailwind` (default) `react` `nextjs` `vue` `svelte` `astro` `swiftui` `react-native` `flutter` `shadcn` `jetpack-compose`.

## Ruleset 4 — designpowers (`references/designpowers/`)

`README.md` routes design operating-layer guidance from the pinned `Owl-Listener/designpowers` reference corpus into the existing frontend workflow. Load it — together with `lane-c-review.md` — for every implementation or redesign that creates or updates `DESIGN.md`, and additionally when a task needs explicit personas, accessibility and cognitive constraints, design critique, design debt, handoff, synthetic user testing, motion guidance, or role-reference prompts. It does not replace this frontend skill, `/visual-qa`, `/ulw-plan`, `/start-work`, or `/review-work`; it supplies richer design context that must first be distilled into the project `DESIGN.md`, then used as the design-system contract for implementation and verification.

## Quick routes — most common requests

| Request | Load |
|---|---|
| "Build a landing page" (no direction given) | `design/README.md` + `design/_INDEX.md` shortlist → exactly one Layer B reference + `design/taste-skill.md` + `perfection/README.md` |
| "Aside-style AI browser / browser agent page" | `design/README.md` + `design/aside.md` + `design/taste-skill.md` + `perfection/README.md` |
| "Linear-style landing page" | `design/README.md` + `design/linear.app.md` + `design/taste-skill.md` + `perfection/README.md` |
| "Premium SaaS hero like Stripe" | `design/README.md` + `design/stripe.md` + `design/soft-skill.md` + `perfection/README.md` |
| "Improve this existing dashboard" | `design/README.md` + `design/redesign-skill.md` + `perfection/README.md` |
| "Add micro-interactions" / "button haptics" / "spring physics" / "border beam glows" / "make it feel alive" | `design/README.md` + `design/interaction-skill.md` on top of current style skill + `perfection/README.md` |
| "Hero atmosphere" / "background particles" / "ambient glow" / "canvas shader" / "text reveals" / "tilt cards" | `design/README.md` + `design/ambience-skill.md` on top of current style skill + `perfection/README.md` |
| "Print report / invoice / export PDF" / "CSS Paged Media" / "fix page-break cuts" | `design/README.md` + `design/print-paged-media.md` on top of current style skill |
| "Where should this go?" / "app shell layout" / "component hierarchy" / "scroll ownership" | `design/layout-skill.md` + `design/stylegallery.md` on top of current style skill |
| "Build this screenshot / Imagen mock / Stitch output exactly" | `design/README.md` + `design/image-to-code-skill.md` + `perfection/README.md` + `/visual-qa` reference-fidelity mode |
| "Audit my site" / "make this page faster" | `perfection/README.md` (+ `perfection/react-perf-tooling.md` if React) |
| "Mockup image of a fintech app" — no code | `design/imagegen-frontend-mobile.md` (+ a Layer B brand if named) |
| "What palette/fonts fit a wellness brand?" | `ui-ux-db/README.md` → search CLI |
| "What do shipped apps in this space look like?" / design-direction research | `design/lazyweb.md` (curl-only) + `design/_INDEX.md` shortlist |
| "Set up this React project" | `design/README.md` + `design/react-dev-tooling-skill.md` |
| "Use designpowers", "make the design workflow stronger", "add personas/accessibility/debt/handoff" | `design/README.md` + `designpowers/README.md` (+ `perfection/README.md` if implementation or audit follows) |

## Shared axioms (all four rulesets agree — apply always)

- **No design system = no UI work.** `DESIGN.md` exists before components do; every color, font size, and spacing value traces back to a token in it.
- **Concrete reference = contract.** When a screenshot, generated mockup, overview, or annotated reference exists, the implementation must match its pixels, copy, component structure, and responsive intent unless the user explicitly accepts a deviation.
- **Never weaken UX OR flatten the surface to buy points.** No dropping animations, hiding content, simplifying interactions, or replacing rendered/lit material with flat fills and flat geometric primitives for a Lighthouse score or a deadline. Hit 100 AND keep the surface dimensional — both, or neither.
- **No emojis as icons.** SVG icon sets only (Lucide, Heroicons, Radix, Phosphor).
- **No coloured accent borders on rounded surfaces.** A `border-l-2 border-primary` stripe on a selected row, a primary-tinted outline on a focused card — any `border-{side}-{primary|warning|destructive|success}` or accent-width rule used to mark selected/focused/active is the most recognizable AI-slop tell in shipped UI. Encode state the way `DESIGN.md` systems do: one ink at many alphas (hover/selected/active wash ramps), a glyph (check) for selection, tonal layering for focus. Keyboard `focus-visible` rings are the only coloured edge allowed.
- **GPU-composited animation only** — `transform`, `opacity`, `filter`; never animate layout properties.
- **Slop animation is forbidden — motion serves meaning.** Every animation or hover must map to a real interaction, state change, or affordance. A hover that changes nothing, motion on a non-interactive element, or a decorative micro-animation with no informational purpose is slop — do not add it.
- **Atmosphere & micro-interaction discipline**: One ambient canvas/shader effect per hero surface; never stack competing particle and shader canvases. Micro-interactions must feel tactile and snappy (150–250ms spring physics), never sluggish. All canvas shaders and particle loops must pause when off-screen (`IntersectionObserver`) and respect `prefers-reduced-motion`.
- **CSS Paged media rigor**: Printable documents and exported PDFs must use `@page` CSS box declarations, prevent split tables and orphan headers via `break-inside: avoid` / `page-break-inside: avoid`, and test with real headless Chrome print emulation.
- **Done is the `/visual-qa` dual-oracle gate, not your own glance.** A frontend design task is verified through `/visual-qa` (real browser at 375 / 768 / 1280px, every page, with interaction states and motion driven and inspected) until the dual-oracle completion gate passes on fresh evidence.

## When to load something else instead

| Situation | Load |
|---|---|
| Brand/style not among the 70 in `references/design/`, or the user says "Open Design" | `open-design` skill — the local nexu-io/open-design library (137+ design skills, 150+ design systems) |
| Driving a browser for the Design QA phase | `agent-browser` skill |
| Pure TypeScript/logic work with zero visual surface | `programming` skill alone — this skill adds nothing there |

## Activation

Use for any frontend, web UI, UX, visual, design, styling, layout, animation, performance, accessibility, or SEO work — building, redesigning, auditing, or generating mockups. Not for backend, CLI, or pure-logic tasks with no visual surface.
