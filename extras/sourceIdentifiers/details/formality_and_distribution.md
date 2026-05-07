# Formality and Distribution: When Does a New Applied Schema Pay?

← [Back to COMPARISON.md](../COMPARISON.md)

## What this section is about

Schemas in OpenUSD provide real benefits — type validation, fallback
values, GUI integration, discoverability, validator targeting, and
others detailed below. They also commit the OpenUSD ecosystem to a
recurring distribution and maintenance cost. The choice of how to
carry source-identifier metadata is therefore a tradeoff: which
formality benefits does the use case actually need, and is the extra
value of a new schema worth that recurring cost?

This section lays out both sides — the formality benefits a new
applied schema provides, and the ecosystem cost it commits — so the
comparison reads as a tradeoff rather than a verdict.

## What schemas formally provide

Eight formality benefits a schema-backed mechanism delivers. None are
hypothetical.

1. **Type validation enforced at runtime.** Authored properties type-check
   against the schema during load and authoring — not by an external
   validator pass that has to run separately.

2. **Fallback values via `UsdPrimDefinition`.** Unauthored properties
   surface meaningful defaults. Tools that read a property always see a
   value; the schema's contract makes the empty case well-defined.

3. **Discoverability via `apiSchemas` + `HasAPI<>()` / `GetAll()`.** A
   consumer asking "is this schema applied to this prim?" gets an answer
   from the prim definition without parsing metadata. Multi-apply schemas
   expose instance names in the `apiSchemas` list.

4. **GUI integration.** Schema-aware DCCs render properties automatically
   with the schema's stated type, doc string, allowed values, and units.
   The UX comes for free once the schema is registered.

5. **Typed accessors.** `GetPrimaryIdAttr()`, `GetRevisionAttr()`, etc.,
   for compiled schemas; even codeless schemas give consumers typed
   property access through the generic `GetAttribute()` interface.

6. **Schema versioning hooks.** Built-in semantics for evolving the schema
   over time — new properties with empty defaults are non-breaking;
   deprecated properties can be marked.

7. **Validator targeting.** `plugInfo.json schemaTypes` lets a validator
   declare which schema it targets; the runtime skips prims that don't
   carry the schema. This makes per-domain validators efficient.

8. **Schema-driven property metadata.** Kind, doc, allowed values that
   GUIs and validators can lean on directly without separate spec
   lookup.

These benefits are real. The question this section asks isn't *whether*
they're real, but which require a *new* schema specifically and which
come from having *some* schema involved at all.

## Which benefits require a *new* schema?

Take each benefit and ask where it comes from:

| Benefit | Met by any schema involvement | Requires a new domain-specific schema |
|---|---|---|
| 1. Type validation at runtime | Yes — `UsdSemanticsLabelsAPI`'s token arrays validate at runtime | Bespoke types per domain (numeric tolerances, structured records) require a new schema |
| 2. Fallback values | Generic empty arrays from `UsdSemanticsLabelsAPI` | Domain-calibrated defaults (a meaningful "unset" for a specific domain) require a new schema |
| 3. Discoverability via `apiSchemas` | Yes — applied schemas show up regardless of which schema | New schema lets the instance name carry domain semantics |
| 4. GUI integration | Yes — `UsdSemanticsLabelsAPI` properties render schema-aware in DCCs already | New schema lets you carry domain-specific doc strings and allowed-values |
| 5. Typed accessors | Yes — `UsdSemantics.LabelsAPI.Get()` works today | Compiled new-schema gives `Get<DomainSpecificField>()` accessors |
| 6. Schema versioning hooks | Versioning of `UsdSemanticsLabelsAPI` itself is OpenUSD's responsibility | Versioning of *that domain's* properties is the schema's responsibility |
| 7. Validator targeting | Yes — `schemaTypes: ["SemanticsLabelsAPI"]` works today | `schemaTypes: ["DomainSpecificAPI"]` lets a validator skip non-target prims more narrowly |
| 8. Schema-driven property metadata | Yes — `SemanticsLabelsAPI` carries kind, doc, allowed-values | New schema lets you carry domain-specific values for those |

Six of the eight (1, 3, 4, 5, 7, 8) are met through any schema
involvement, including reuse of an existing core schema. The two
narrower ones (2 fallbacks, 6 schema-versioning of a specific domain) —
plus the *quality* of 1, 4, 5, 7, 8 (domain-specific types, labels,
accessors, metadata) — are what a *new* schema specifically adds.

The ecosystem already paid the distribution cost for
`UsdSemanticsLabelsAPI` once when it landed in OpenUSD 24.11.
Approach D consumes those benefits without paying again.

## The ecosystem cost a new applied schema commits

A new applied schema, once ratified, must be distributed to every
USD-consuming runtime in the ecosystem before content using it is
consumable: DCC integrations (Maya, Houdini, 3ds Max, Blender,
Cinema 4D, others), game-engine importers (Unreal, Unity, in-house),
web/cloud viewers, AR/VR runtimes, CI/validation pipelines. Each
runtime pins a USD release × Python × OS × runtime × build flavor ×
DCC config that distribution must ABI-match.

The matrix already exists today, distributed across vendors who ship
USD binaries into their own ecosystems. Per the AOUSD Build Interest
Group's parent epic for binary distribution
([`aousd/build-ig-initiatives#28`](https://github.com/aousd/build-ig-initiatives/issues/28)):

> *"There is currently no 'official' source to go for pre-built
> stand-alone OpenUSD binaries. Some do exist, but the lack of an
> official or standard place to go for USD binaries on non-MacOS
> platforms hurts the ecosystem, and adoption in general — both for
> practical and perception reasons."*

The Build IG is actively scoping consolidation — distribution-channel
prioritization (clickable download / PyPI / homebrew / conda-forge),
an AOUSD-controlled cmake branch into Pixar's dev, hosted PyPI usd-core
packaging, plugin registration via importlib, CI infrastructure
([initiatives index](https://github.com/aousd/build-ig-initiatives/issues)).
The matrix is real, multi-vendor, and currently fragmented; the IG
coordinates the substrate that's forming around it.

Schema distribution depends on that substrate. A new applied schema
ratifying today commits whichever distribution path takes it — built
into core, or shipped as a separate plugin — to the same matrix. The
cost has two shapes:

- **Initial distribution.** A binary build per consumer cell,
  ABI-matched to each. The matrix solves the "how do downstream
  consumers consume" question one cell at a time.
- **Recurring maintenance.** When OpenUSD evolves a base type,
  deprecates an API, or changes plugin-loading conventions, every cell
  may need a re-test pass at minimum and often a rebuild. Schema
  versioning and consumer-side compatibility are recurring, not
  one-time.

Codeless schemas reduce but do not eliminate this cost: they avoid
C++ ABI drift but still need plugin discovery, distribution channels,
versioning, and consumer-side support across the matrix.

The dominant cost of ratifying a new applied schema is this recurring
distribution-and-maintenance load, not the local codegen step that
`governance.md §6.7` quantifies in lines and files.

## Where each approach lands on the tradeoff

| Approach | Formality benefits delivered | Distribution cost incurred |
|---|---|---|
| A — `assetInfo` dictionaries | None of the schema benefits (no schema involved) — relies on registry-as-spec for offline validation only | Zero — no schema to ship |
| B — New multi-apply schema | All eight benefits, with bespoke types and accessors | Full distribution matrix per ratified version, recurring across releases |
| C — Refinement of B (schema + `assetInfo` overflow) | All eight for the four common fields; `assetInfo` overflow inherits A's profile | Full matrix (same as B) plus the dict-overflow A carries |
| D — Refinement of B (existing `UsdSemanticsLabelsAPI` + `assetInfo`) | Six of eight via reuse; bespoke fallbacks and domain-specific schema versioning are what a new schema would add | None new — `UsdSemanticsLabelsAPI` already shipped in 24.11; the existing distribution carries it |

The tradeoff is sharpest between B/C and D: B and C deliver the
remaining two-of-eight benefits (domain-calibrated fallbacks,
domain-specific versioning hooks) at the cost of committing the
ecosystem to a recurring distribution matrix. D delivers six-of-eight
at no incremental cost.

## Where the data leans across the four verticals

Whether what a new schema adds justifies the distribution cost depends
on whether the verticals AOUSD members care about surface fields that
*require* the new-schema-only benefits. Across the four verticals
exercised in this work (AECO, Manufacturing, Robotics, M&E):

- **No domain-specific field surfaced that required typed non-token-array
  structure.** Token arrays + identifier strings carried every metadata
  case tested.
- **No identifier domain surfaced where bespoke fallback values were
  necessary.** Empty token arrays / absent identifier strings communicate
  "unauthored" cleanly across all four verticals.
- **No identifier domain surfaced where domain-specific schema versioning
  was necessary in a way the AOUSD Domains Registry couldn't track.**
  The registry-level promotion path captured the lifecycle pattern the
  verticals showed.

This is the empirical basis of the doc's leaning toward D. It is not a
verdict: AOUSD review may surface domains where what a new schema adds
becomes decisive — numeric tolerances with units, structured records
that don't fit into token arrays, lifecycle states that need typed
transitions. The leaning says *"in the verticals tested, the
distribution cost outweighs what a new schema would add;"* the AOUSD
review weighs whether the verticals tested are representative of the
verticals that matter most.

## Open questions where AOUSD member input would help

1. **Which domain-specific fields, if any, surface non-token-array typed
   structure that `UsdSemanticsLabelsAPI` cannot represent in the
   verticals each member operates in?** The four verticals tested are
   not exhaustive; a member working in (e.g.) chemistry, automotive, or
   aerospace metadata may surface fields that change the answer.

2. **Do any identifier domains need bespoke fallback values?** Empty
   defaults worked in the tested verticals; a domain where "unspecified"
   must default to a specific non-empty value would shift the analysis.

3. **Is the distribution cost felt differently across member contexts?**
   Members who currently maintain large slices of the matrix may have
   sharper pictures of the recurring cost than members who consume
   binaries from upstream.

4. **Does the existing `UsdSemanticsLabelsAPI` versioning approach work
   for the identifier domains AOUSD prioritizes?** A new schema's
   versioning is what would be added; whether it matters depends on
   what evolution the prioritized domains expect.

These questions are open — the doc does not answer them. They are
inputs the AOUSD review process is positioned to gather.
