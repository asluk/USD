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

The recurring distribution-and-maintenance load is the substantial
cost of ratifying a new applied schema today, materially larger than
the local codegen step that `governance.md §6.7` quantifies in lines
and files.

> **Aaron's call (2026-05-07) on how heavily this weighs.** Earlier
> drafts of this document called the recurring distribution load
> *"the dominant cost"* unconditionally. That phrasing is retracted
> in favor of a conditional reading: the matrix burden is **currently
> elevated** — fragmented across vendors who ship USD binaries today
> — and is **trending lighter** as the AOUSD Build IG initiatives
> land (hosted binaries via the parent epic
> [`aousd/build-ig-initiatives#28`](https://github.com/aousd/build-ig-initiatives/issues/28),
> plugin registration via importlib, conda-forge / PyPI distribution,
> CI infrastructure). Proposal 105's original B-cons phrasing flagged
> the cost (*"requires distributing schema plugins"*) but read it as
> manageable in the current ecosystem; the difference between the
> proposal's framing and the elaboration in this document is one of
> articulation — the proposal flagged the burden, this document
> describes what the burden looks like operationally as a build
> matrix. Both framings are honest; the rebuilt scoring in
> `stress_tests/vendor_adoption_analysis.{py,json}` reflects the
> conditional weight directly in the Minimal disruption score (B and
> C scored at the elevated weight today, with the trajectory expected
> to lighten).

## Where each approach lands on the tradeoff

| Approach | Formality benefits delivered | Distribution cost incurred | Carries heterogeneous typed fields? |
|---|---|---|---|
| A — `assetInfo` dictionaries | None of the schema benefits (no schema involved) — relies on registry-as-spec for offline validation only | Zero — no schema to ship | Yes (freeform dicts) |
| B — New multi-apply schema | All eight benefits, with bespoke types and accessors *for the four common fields* | Full distribution matrix per ratified version, recurring across releases | No (fixed four-property surface) |
| C — Refinement of B (schema + `assetInfo` overflow) | All eight for the four common fields; `assetInfo` overflow inherits A's profile | Full matrix (same as B) plus the dict-overflow A carries | Yes (overflow tier) |
| D — Refinement of B (existing `UsdSemanticsLabelsAPI` + `assetInfo`) | Six of eight via reuse, *for the controlled-vocabulary classification axis only*; bespoke fallbacks and domain-specific schema versioning are what a new schema would add | None new — `UsdSemanticsLabelsAPI` already shipped in 24.11; the existing distribution carries it | No (`token[]` label values + `string` identifiers cannot represent typed numerics, dates, composite refs, or polymorphic XSD values) |

The tradeoff has three dimensions, not two: formality benefits,
distribution cost, **and** whether the mechanism carries the
heterogeneous typed surface real source systems bundle. Earlier
drafts of this document collapsed the third dimension by asserting
the surface was empty; the field experiment shows it is not. Among
the four candidates, A and C carry it; B-alone and D do not.

## What the field experiment shows about the heterogeneity surface

Earlier drafts of this section asserted that *"no domain-specific field
surfaced that required typed non-token-array structure"* across the four
verticals tested, and used that assertion as the empirical basis for a
leaning toward Approach D. **That assertion is retracted.** The
field-by-field census documented in
[`field_classification_experiment.md`](field_classification_experiment.md)
draws fields from authoritative spec surfaces (IFC4x3, Revit API, AAS
metamodel, Windchill REST, SAP MARA, ROS/URDF/SDF, OpenAssetIO/MovieLabs
OMC/ShotGrid) under pre-registered classification criteria, and shows
that heterogeneous typed fields surface in every vertical surveyed:

- **Timestamps are universal.** IFC `IfcTimeStamp`, Windchill
  `Edm.DateTimeOffset`, SAP `DATS`, ROS `std_msgs/Header.stamp`,
  ShotGrid `created_at`/`updated_at`, OMC `lifecycleEvents`.
- **Numeric measures with units appear in AECO, PLM, and Robotics.**
  IFC `IfcMeasureValue` family, SAP `QUAN(13,3)` (`NTGEW`/`BRGEW`/
  `VOLUM`), URDF/SDF mass/inertia/joint limits/dynamics.
- **Composite typed references are universal.** IFC
  `IfcPersonAndOrganization`/`IfcApplication`, AAS `Reference`/
  `RelationshipElement`, Revit `ElementId`-typed relations, ShotGrid
  entity-link fields, OMC `participants`/`creationContext`.
- **Polymorphic XSD-typed values are the standard surface in AAS.**
  `Property.value` is typed across `xs:string`/`xs:int`/`xs:long`/
  `xs:decimal`/`xs:double`/`xs:float`/`xs:boolean`/`xs:date`/
  `xs:dateTime`/`xs:duration`/`xs:anyURI`/`xs:base64Binary` by design.
  AAS is the standard the proposal already cites in its
  emerging-consensus list.

These shapes do not flatten to `token[]` without losing structural
type. Whether they belong inside the source-identifier mechanism's
scope or outside it is the open question above; what the experiment
shows is that the spec surfaces include them.

## What this means for the formality/distribution tradeoff

The previous version of this section concluded that the formality
benefits a new applied schema adds *beyond reuse of
`UsdSemanticsLabelsAPI`* (domain-calibrated fallbacks, domain-specific
versioning hooks) "didn't show up as decisive across the four
verticals tested" — which was true *for the synthesized field set* the
earlier industry_scenarios document used, but does not generalize to
the spec-surface heterogeneity the field experiment documents.

The retracted form: *"in the verticals tested, the distribution cost
outweighs what a new schema would add."*

What the experiment supports:

- Reuse of `UsdSemanticsLabelsAPI` carries the controlled-vocabulary
  classification axis cleanly across all four verticals — that part of
  the prior reading holds.
- The heterogeneity surface (heterogeneous typed fields, recurring
  across all four verticals) is not carried by `UsdSemanticsLabelsAPI`
  at all — its `token[]` value type cannot represent timestamps,
  numeric measures with units, composite references, or polymorphic
  XSD-typed values.
- A solution proposal that wants to carry the heterogeneity surface
  needs either freeform `assetInfo` dictionaries (Approach A's tier),
  a typed multi-apply schema with overflow (Approach C), or
  per-domain companion schemas (Approach B's natural extension).
- Whether the heterogeneity surface *should* be carried by the
  source-identifier mechanism, or excluded by scope and carried by a
  separate mechanism, is the load-bearing scope question. The
  comparison materials cannot answer it on their own — it is
  ultimately a member judgment about what counts as identifier
  metadata and what counts as the asset's content.

## Open questions where AOUSD member input would help

1. **Where should the identifier-package boundary sit?** Authoritative
   spec surfaces include heterogeneous typed fields (timestamps,
   numeric measures, composite refs, polymorphic AAS Properties) in
   the metadata bundles real source systems carry alongside their
   identifiers. Are those fields *part of* source-identifier metadata
   for AOUSD's purposes, or *the asset's content*, carried by a
   separate mechanism? This is the load-bearing scope question for
   any mechanism choice that follows.

2. **Which domains' members are affected by which buckets?** A member
   working primarily in AECO/M&E may see the heterogeneity surface as
   modest; a member working in Manufacturing/PLM (where AAS makes
   typed `Property` values the standard surface) sees it as central.
   The mechanism choice that works across members may need to admit
   the heterogeneous surface even if some members do not feel it.

3. **Do any identifier domains need bespoke fallback values?** Empty
   defaults worked in the tested verticals; a domain where
   "unspecified" must default to a specific non-empty value would
   shift the analysis.

4. **Is the distribution cost felt differently across member
   contexts?** Members who currently maintain large slices of the USD
   distribution matrix may have sharper pictures of the recurring
   cost than members who consume binaries from upstream. The
   comparison materials elevate distribution to the dominant cost
   under D's framing; the proposal's original B-cons phrasing
   downplays it (*"tools already ship their own domain plugins and
   unrecognized schema data roundtrips without loss"*). Resolution
   here is itself load-bearing.

These questions are open — the doc does not answer them. They are
inputs the AOUSD review process is positioned to gather.
