# README rewrite brief (for the rewrite agent)

You are rewriting `extras/usd/examples/usdGeospatial/README.md` **in place**. This is a
**structural + framing rewrite**, NOT a content rewrite. Preserve every factual/numeric claim and
every image; change only ORDER and FRAMING per this brief.

## Absolute rules
1. **Do NOT invent, drop, or alter any factual or numeric claim.** Every number (0.0 mm, 418.9 m,
   4.86 m, 6,369 km, ~6.4×10⁶ m, 162 mm, 480,000×, 0.40/0.68 mm, 7,320 samples, 3,526 verts, 9/9,
   30/30, ~1.8 ms/prim, EPSG codes, etc.) must survive verbatim, attached to the same claim.
2. **Do NOT touch any file except `README.md`.** Not the deck, not the PR body
   (`PR_REVIEW_GUIDE.md`), not code, not tests. README only.
3. **Every image reference must point at a file that already exists in `docs/`.** Do not reference
   new images. Available: railway_render, coherence, multi_runtime, runtime_parity,
   railway_storm_autoinsert, railway_storm_noplugin, design_equivalence, tree_alignment,
   binding_semantics, globe_visualizer_parity, multiCRS_glyph_renders, illformed_g1/g2/g3,
   illformed_gallery (+ others). Reuse existing markdown `![...](docs/x.png)` lines as-is.
4. **Slide markers travel with their content.** Keep the `<!-- slide:* -->` HTML-comment markers;
   move each with the section it belongs to. Marker grammar (see build_deck.py):
   - `<!-- slide:title subtitle="..." -->`
   - `<!-- slide:section title="..." subtitle="..." -->`
   - `<!-- slide:text eyebrow="..." title="..." body="a | b | c" -->` (body pipes = bullets;
     omit body= to pull README prose up to next marker/heading)
   - `<!-- slide:image src="docs/x.png" eyebrow="..." title="..." caption="..." -->`
   You may re-author marker `body=` text to match the new framing, but keep every numeric claim.

## Terminology (USE PRECISELY — this is the whole point of the rewrite)
- **USD** = the technology / the standard itself.
- **AOUSD** = its governing standards body (owns the normative spec: data model + behavior).
- **OpenUSD** = ONE (currently canonical) implementation, in Pixar's GitHub. NOT the standard.
- "**codeless**" and "**resolve, don't bake**" are **OpenUSD-specific IMPLEMENTATION DETAILS**, not
  part of what is being standardized. The data model does not "know" it is codeless. Present them
  as implementation choices, and as *what enabled multiple independent implementations* — never as
  the headline identity of the proposal.

## Cross-cutting rules
- **Behavior before mechanism.** State what the reader gets (the desired behavior) BEFORE naming
  the OpenUSD mechanism that achieves it. Normative sections (§2, §3) must be free of OpenUSD API
  terms (no resetXformStack, no skipCodeGeneration, no Hydra) — describe behavior irrespective of
  USD API terms.
- **"Us helping them."** This artifact is running EVIDENCE supporting the Esri/AECO geospatial CRS
  proposal (Tamrat-B/OpenUSD-proposals PR #1), authored WITH Simon Haegler (Esri). It mirrors that
  proposal's structure. It is NOT a competing standalone pitch. Say this explicitly in §1.
- **No "conformance oracle" overclaim.** True/legal standardization happens AFTER proposal +
  implementation merge into the Pixar OpenUSD repos and ship in an official OpenUSD release; AOUSD
  governance grows over time. So the Python runtime is a **runnable reference that demonstrates the
  behavior and lets independent implementations check against it** — NOT "the conformance oracle of
  a standard." Soften every "conformance oracle" phrasing accordingly.
- **"composition" collision:** in §8 (coordinate frame) do NOT use the word compose/composition to
  mean "combine transforms" — say "combine offsets in the CRS-implied frame." In §9, USD
  composition (subLayers + over) is the CORRECT meaning — keep it, and make one phrase explicit
  that this is USD composition arcs so it can't blur with §8.

## The locked 12-section outline (USE THESE EXACT SECTION TITLES as `##` headings, in order)

1. `## Supporting the Esri geospatial CRS proposal`
   - Framing: this is running evidence for the Esri proposal (PR #1), co-authored with Simon
     Haegler (Esri); we mirror its bones and back its contested design calls with working
     implementations. Name- and layout-aligned with Simon's `geospatial-prototype`.
   - Include ONE hero teaser image early: `docs/railway_storm_autoinsert.png` (the REAL Storm
     render — honest "look, it works" promise; do NOT tease with a matplotlib plot), captioned as a
     forward-pointer to the proof in §5.
   - Keep the "figures are matplotlib plots of resolved numbers, not renders; the one exception is
     the Storm render" disclaimer (it matters for review) — but it can be tightened.
   - Do NOT lead with "codeless" or "resolve, don't bake" here — those drop to §6.

2. `## Problem statement`
   - NORMATIVE, no USD API terms. Georeferenced data must resolve to a shared real-world frame;
     multiple sources in multiple CRSs must co-register; the open tension is how CRS-driven
     placement reconciles with USD's existing transform hierarchy.
   - **DO NOT** include "binding must not write to authored transform data as a side effect" here —
     that is a SOLUTION CONSTRAINT, not the problem. It belongs in §6/§7. (This was an explicit
     correction.)

3. `## Separation of concerns`
   - Normative (data model + runtime behavior — what AOUSD would own) vs. implementation
     (OpenUSD/APIs/Hydra/codeless/resetXformStack). Use USD / AOUSD / OpenUSD precisely.
   - **Explicitly name the near-term goal in the text:** the path today is landing the proposal +
     implementation in the Pixar OpenUSD repos and an official OpenUSD release; AOUSD governance
     migrates from Pixar over time.
   - No conformance-oracle overclaim. Do NOT dump codeless/resetXformStack mechanics here — name
     the DISTINCTION; mechanisms live in §6.

4. `## The proposal in practice: system architecture`
   - Framing: now that the problem is clear, here are the components that realize the proposal, at
     the ARCHITECTURE/BEHAVIOR level: the CRS prim + binding (what they are, behaviorally), the
     two-runtime structure (INTRODUCE the two runtimes here — job #1 of 3), repo layout (two sibling
     dirs), the projection-engine seam. Architecture diagrams belong here (tree_alignment,
     design_equivalence, binding_semantics as appropriate).
   - Keep out the OpenUSD "how" (skipCodeGeneration, the no-xformOp trick) — that is §6.

5. `## Proving viability: multiple independent implementations`
   - Framing: providing multiple independent implementations that AGREE is standard, often-required
     standards-development practice for showing a data model + behavior is well-specified. This is
     the two-runtime touch #2 of 3 (USE them as evidence; don't re-introduce or re-explain-enabled).
   - The 4 proofs live here (no-overfit railway; NCAT co-registration; two-runtime 0.0 mm;
     real Storm auto-insert). Keep all 4 with their numbers/images.
   - Distinguish CORRECTNESS (Proof 2 vs NCAT + closed-form geodesy — independent authority) from
     CONTRACT-UNAMBIGUITY (impls agree → buildable twice the same way). Keep the honest caveat that
     two impls of the same misreading would also agree — but TIGHTEN it; it currently drowns the
     point.

6. `## How OpenUSD lets us do it`
   - THE one place the OpenUSD-specific HOW headlines. Two implementation details, labeled as such:
     - **codeless** (skipCodeGeneration → schema is pure data, no compiled types to reimplement)
     - **resolve, don't bake** — and HERE is where the behavioral constraint lives: binding a CRS
       must NOT have the side effect of writing to the authored scene description (Aaron's precise
       objection: `SetResetXformStack` writes to scene description; every downstream consumer then
       inherits it). Behavior-first: state "binding must not mutate authored transform data," THEN
       name baking/resetXformStack as the thing that violates it, THEN note OpenUSD lets us honor it
       at runtime instead.
   - Punchline (two-runtime touch #3 of 3): these two choices — pure data + neutral scene — are
     precisely WHAT ENABLED building multiple independent implementations against the same authored
     data. Explain-what-enabled-it; don't re-prove or re-introduce.

7. `## Coexisting with the transform hierarchy`  (mechanism subtitle: inject, don't bake)
   - BEHAVIOR FIRST (Ruling 1): open with what the reader gets — the authored scene stays
     coordinate-neutral, and a child's local placement composes relative to a georeferenced anchor
     at read time. THEN name "inject, don't bake" as the mechanism. Keep anchor-injection content,
     orientation-not-just-position, float32 localization, hand-tweak-survives, all numbers.

8. `## Coordinate frame: projected vs. geographic anchors`
   - The correctness rule (geographic/ECEF anchor → true-ENU basis; projected anchor → grid plane).
     Keep the 4.86 m grid-convergence finding + test_coexist_vs_baked reference.
   - TERMINOLOGY: do NOT use compose/composition to mean "combine transforms" here — say "combine
     in the CRS-implied frame" / "in the grid plane." Avoid the USD-composition collision.

9. `## Non-geometric georeferenced data`
   - Behavior-first already; keep. USD composition (subLayers + over) is CORRECT here — keep the
     word, and add one explicit "this is USD composition arcs" clarifier. Keep the usda snippet,
     globe_visualizer_parity + multiCRS_glyph_renders images and their numbers. The
     "same anchor-injection path, no new code path" is a CALLBACK to §7 — reference, don't
     re-explain injection.

10. `## Detecting and flagging invalid geospatial inputs`  (was "Guard rails")
    - POSITIVE / capability framing: the system can DETECT malformed geospatial inputs and FLAG
      them. Lead with the capability; the corner cases (G1 418.9 m, G2 4.86 m, G3 6,369 km) are
      EVIDENCE detection works (broken → fix → re-measure), not a hazard parade. Do not open
      defensively ("coexist has no showstopper...").
    - The real argument that belongs here and should LEAD: a neutral authored scene keeps CRS
      intent INSPECTABLE, which is what makes detection possible; a baked scene has already
      collapsed intent into a matrix. Keep verify.py + the usdchecker-plugin (near-term deliverable)
      as the MECHANISM after the capability. Keep the loud-and-recoverable vs silent-and-
      unrecoverable tradeoff and the requires-CRS marker where-it-lives (layer meta vs prim schema)
      debate in this section.

11. `## Runtimes, tests, and verifying the results`
    - The reproduce-it-yourself section: the two runtimes (technical A/B detail), the test roster,
      build + run instructions (the two paths). Mechanism-first is APPROPRIATE here by purpose.
    - The "Where the Python reference runtime sits" block: SOFTEN per the no-overclaim rule — it is
      a runnable reference that demonstrates behavior and that implementations check against, NOT
      "the conformance oracle of a standard." Keep the core-spec-supplemental precedent as an
      analogy but downgrade the "conformance oracle" language.

12. `## Status, scope, and open questions`
    - Status, out-of-scope, the open design questions, the asks — framed as HELPING the Esri
      proposal (consistent with §1). Keep the resetXformStack-semantic-vs-baking ask (it is sharp
      and matches Aaron's position). Keep the Redlands-BIM-scene ask. Don't re-argue §6.

## Output
- Overwrite README.md with the rewritten document following the outline exactly.
- Preserve the intro `<!-- slide:title ... -->` marker near the top.
- After writing, print a short self-check: list each of the 12 section headings in order, and
  confirm every numeric claim from the original still appears (grep-style count is fine).
- Do NOT run git, do NOT build the deck, do NOT touch any other file. Stop after writing README.md.
