# Scope Promotion Simulation: From Overflow Dict to Schema Property (Approach C)

← [Back to COMPARISON.md](../COMPARISON.md)

> **Scope under D vs. C.** Under Approach D, a field like `scope` is a
> classification facet from day one — it lives at
> `SemanticsLabelsAPI:aas:scope`. "Promotion" reduces to a registry-level
> facet addition (a GitHub PR adding `scope` to the registered facets for
> the `aas` system, then optionally to other systems' facet lists as
> adoption broadens). No schema property to ratify, no codegen, no plugin
> distribution. The five-phase lifecycle in this document is the
> Approach-C path — preserved here as illustrative of the harder
> graduation a future field would face if it needs typed structure
> beyond what `SemanticsLabelsAPI` supports. For D-aware planning, see
> COMPARISON.md "Open Questions" §2 on AAS scoping.

## Overview

This simulation traces the lifecycle of a single metadata field — `scope`
(type-vs-instance identifier classification) — as it evolves through the
hybrid's **three-tier promotion path**: from a domain-specific convention
in one vendor's overflow dictionary, through a codeless companion schema,
to a ratified core schema property on the base `SourceIdHybridAPI`. The
simulation demonstrates Hybrid C's key architectural advantage: **the
overflow dict is not a dead end, but the first stage of a governed
graduation path.**

Each phase includes concrete `.usda` files in
[`examples/scope_promotion/`](../examples/scope_promotion/) and, where
applicable, Python scripts demonstrating validation and migration.

**Timeline (illustrative):**

| Phase | Timeframe | `scope` lives in | Who uses it |
|-------|-----------|-------------------|-------------|
| 1 | Day 1 | AAS overflow dict only | AAS/DPP stakeholders |
| 2 | ~6–12 months | Overflow dict (3+ domains) | AAS, manufacturing, robotics |
| 3 | ~1–2 years | Overflow dict + registry-spec validation | All adopters; CI-enforced |
| 3b | ~1.5–2 years | Codeless companion schema | Domains with stable `scope` usage |
| 4 | ~2+ years | Core schema property (5th field) | Everyone; TAC-ratified |
| 5 | Post-promotion | Core schema property; overflow deprecated | Migration complete |

**Phase 3b** is the codeless companion schema tier: domains that have
stabilized their use of `scope` can publish a codeless companion schema
(~80 lines, no C++) that gives `scope` type safety, per-property
composition, and `UsdSchemaRegistry` discoverability — without waiting
for TAC ratification into the core schema. This intermediate tier reduces
the jump from freeform dict to core property and gives the TAC evidence
that the field is production-ready before committing core schema surface
area.

---

## Phase 1: AAS-Only Overflow (Day 1)

_`scope` is a domain-specific AAS convention. No other stakeholder uses it._

**Scenario.** The AAS/Industry 4.0 community needs to distinguish type-level
identifiers (product families, part designations) from instance-level identifiers
(serial numbers, deployed units). AAS calls these `globalAssetId` (type) and
`specificAssetIds` (instance). They encode this as a `scope` string in their
`assetInfo` overflow dictionary.

Meanwhile, IFC's GlobalId identifies each entity uniquely (both type objects
and instance objects), and Windchill's
part OID always references a specific part revision. Neither domain needs `scope`.

**What the `.usda` shows:**
([`examples/scope_promotion/phase1_aas_overflow.usda`](../examples/scope_promotion/phase1_aas_overflow.usda))

- `BatteryPack_SN42` — DPP with `scope = "instance"` (a specific battery unit)
- `BatteryPack_LFP280` — DPP with `scope = "type"` (the product family)
- `Column_C14` — IFC, no scope (GlobalId identifies each entity, type or instance)
- `Chiller_01` — Windchill, no scope (OID is always a specific part)

**Key observation:** `scope` lives entirely in the overflow dict. The base schema
is untouched. No schema change, no TAC review, no impact on non-AAS domains.
This is exactly the escape hatch Hybrid C is designed to provide.

**Interoperability status of `scope` at this phase:**

| Capability | Status |
|------------|--------|
| AAS tools can read/write scope | ✅ They know their own dict structure |
| Non-AAS tools can discover scope exists | ❌ Must parse `assetInfo` dicts |
| Validation | ❌ No enforcement; typos like `scope = "instnace"` pass silently |
| GUI rendering | ❌ Hidden inside metadata dict |

---

## Phase 2: Cross-Domain Adoption (~6–12 Months)

_Manufacturing and robotics adopt the same `scope` convention. Registry-spec documents it._

**Scenario.** Six months after DPP adoption, two other communities independently
reach the same conclusion: they need to distinguish type-level from instance-level
identifiers.

- **Manufacturing (PTC Windchill):** Their PLM export pipeline now distinguishes
  product family designations (`scope = "type"`) from specific part revisions
  (`scope = "instance"`). PTC's pipeline team saw the AAS convention in the
  registry-spec documentation and adopted it rather than inventing their own.

- **Robotics (ROS/URDF):** Robot model definitions (the URDF source) are
  type-level; deployed fleet instances are instance-level. The robotics
  community adopted `scope` with the same semantics.

- **IFC:** Still no need for `scope`. IFC GlobalId identifies each entity
  uniquely (both type objects and instance objects), so the type-vs-instance
  distinction is structural, not at the identifier level
  by definition. The convention exists alongside IFC identifiers without
  requiring any change.

**What the `.usda` shows:**
([`examples/scope_promotion/phase2_cross_domain.usda`](../examples/scope_promotion/phase2_cross_domain.usda))

- `BatteryPack_SN42` — DPP, `scope = "instance"` (unchanged from Phase 1)
- `Chiller_Series7500` — Windchill, `scope = "type"` (product family) — **NEW**
- `Chiller_01` — Windchill, `scope = "instance"` (specific deployed unit) — **NEW**
- `UR10e_ModelDef` — ROS, `scope = "type"` (URDF model definition) — **NEW**
- `UR10e_Cell3_Unit7` — ROS, `scope = "instance"` (deployed robot) — **NEW**
- `Column_C14` — IFC, no scope (still unnecessary)

**Key observation:** The `scope` convention spread organically through the
registry-spec documentation — not through schema changes. Each domain adopted
it independently, using the same values (`"type"`, `"instance"`) because the
registry-spec provided a clear definition. No schema work was required. No
TAC review. No C++ code.

**The trigger for promotion consideration:** When 3+ domains independently
adopt the same overflow field with the same semantics, that's a strong signal
the field has graduated from domain-specific to cross-cutting. The AOUSD
Domains Registry now has a discussion item: should `scope` be promoted?

**Interoperability status of `scope` at this phase:**

| Capability | Status |
|------------|--------|
| Multi-domain tools can filter by scope | ⚠️ Must parse overflow dicts, but convention is documented |
| Validation | ❌ Still no enforcement; inconsistent values possible |
| GUI rendering | ❌ Still hidden in metadata dict |
| Cross-domain consistency | ✅ Registry-spec ensures same field name and allowed values |

---

## Phase 3: Registry-Spec Validation (~1–2 Years)

_AOUSD CI validator enforces `scope` values. The convention is formalized._

**Scenario.** With three domains using `scope`, the AOUSD community formalizes
the field in the registry-spec. A CI validator is added to the AOUSD validation
toolkit that reads overflow dictionaries and checks `scope` values against the
registered allowed set.

**What the script shows:**
([`examples/scope_promotion/phase3_validator.py`](../examples/scope_promotion/phase3_validator.py))

The validator reads `assetInfo["sourceIds"]` overflow dictionaries and checks:
- `scope` must be a string (catches wrong types)
- `scope` must be `"type"` or `"instance"` (catches typos)
- Missing `scope` is fine (it's optional)

**Sample output:**

```
AOUSD Source Identifier Validator — scope field (registry-spec v1.0)

  ✅ /BatteryPack_SN42: 'scope' = 'instance' in domain 'org.idta.dpp'
  ✅ /Chiller_Series7500: 'scope' = 'type' in domain 'com.ptc.windchill'
  ✅ /Chiller_01: 'scope' = 'instance' in domain 'com.ptc.windchill'
  ✅ /UR10e_ModelDef: 'scope' = 'type' in domain 'org.ros.urdf'
  ✅ /UR10e_Cell3_Unit7: 'scope' = 'instance' in domain 'org.ros.urdf'
  ⚠️  /BadPrim_Typo: unrecognized value 'instnace' (allowed: ['type', 'instance'])
  ❌ /BadPrim_WrongType: must be a string, got int: 42

Results: 5 passed, 1 warnings, 1 errors
VALIDATION FAILED
```

**Key observation:** The registry-spec mechanism delivers **CI-level validation**
for an overflow dict field — without any schema changes to USD. The validator
is ~50 lines of Python. This is the intermediate step between "freeform
overflow" and "schema property": the field is still in `assetInfo`, but its
values are now governed.

**What's still missing:** Runtime validation (would need a USD plugin) and
GUI discoverability (would need property-panel integration). These gaps
are what motivate the next phase: promotion to schema property.

**Interoperability status of `scope` at this phase:**

| Capability | Status |
|------------|--------|
| CI/offline validation | ✅ Registry-spec validator catches errors |
| Runtime validation | ❌ Still external-only |
| GUI rendering | ❌ Still hidden in metadata dict |
| Cross-domain consistency | ✅ Enforced by validator |

---

## Phase 4: Schema Promotion (~2+ Years)

_TAC ratifies `scope` as an optional 5th property on `SourceIdHybridAPI`._

**Scenario.** After ~18 months of cross-domain adoption and registry-spec
validation, the AOUSD TAC considers a proposal to promote `scope` from the
overflow dict to a typed schema property. The evidence is strong:

- 3+ domains adopted it independently with consistent semantics
- The CI validator has been catching errors in production pipelines
- The two remaining gaps (runtime validation, GUI rendering) can only be
  closed by making `scope` a schema property

The TAC ratifies `scope` as an **optional** `token` property with
`allowedTokens = ["type", "instance", ""]`. The empty default means
domains that don't need it are unaffected — IFC assigns GlobalIds to both
type and instance objects without distinction, and glTF and MaterialX have
no equivalent external identifier scoping.

**What the files show:**

[`examples/scope_promotion/phase4_schema.usda`](../examples/scope_promotion/phase4_schema.usda)
— The updated `SourceIdHybridAPI` class definition with `scope` as the
5th property. Input to `usdGenSchema`.

[`examples/scope_promotion/phase4_promoted.usda`](../examples/scope_promotion/phase4_promoted.usda)
— Same prims as Phase 2, but `scope` has moved from the overflow dict
to a schema property. Domain-specific metadata (batteryModel, displayNumber,
frameId, etc.) **remains in the overflow dict** — only `scope` was promoted.

**Before (Phase 2) vs After (Phase 4) — BatteryPack_SN42:**

```diff
  def Xform "BatteryPack_SN42" (
      prepend apiSchemas = ["SourceIdHybridAPI:dpp"]
      assetInfo = {
          dictionary sourceIds = {
              dictionary dpp = {
-                 string scope = "instance"
                  string batteryModel = "LFP-280Ah-48V"
                  string chemistry = "LFP"
              }
          }
      }
  )
  {
      string sourceIdentifier:dpp:primaryId = "urn:idta:dpp:battery:SN42:2025"
      token sourceIdentifier:dpp:domain = "org.idta.dpp"
      string sourceIdentifier:dpp:label = "IEC 62474 Digital Battery Passport"
+     token sourceIdentifier:dpp:scope = "instance"
  }
```

**What promotion buys:**

| Capability | Before (overflow) | After (schema property) |
|------------|-------------------|------------------------|
| Runtime validation | ❌ External only | ✅ USD-native (`allowedTokens`) |
| GUI rendering | ❌ Hidden in metadata | ✅ Automatic in property panels |
| Per-property composition | ❌ Dict-level merge | ✅ Independent opinion stack |
| Query/filter | ❌ Parse all `assetInfo` dicts | ✅ `GetScopeAttr().Get()` |
| Backwards compatibility | N/A | ✅ Old files without scope still work (defaults to "") |

**Key observation:** Promotion is **non-breaking**. Existing files without
`scope` continue to work — the empty default means the property exists but
is unset. Existing files with `scope` in the overflow dict also continue
to work (the overflow dict is not validated against the schema), but a
migration script can clean them up (see Phase 5).

---

## Phase 5: Coexistence & Migration (Post-Promotion)

_Old stages with `scope` in overflow still work. Migration script moves values to schema property._

**Scenario.** Post-promotion, the ecosystem has a mix of old and new content:

- **Old stages:** `scope` in `assetInfo` overflow dict (written before promotion)
- **New stages:** `scope` as schema property `sourceIdentifier:<domain>:scope`
- **Mixed stages:** Some prims migrated, some not (incremental pipeline updates)

All three cases work correctly because:
1. The schema property defaults to `""` (empty token) — old files without the
   property are valid
2. The overflow dict is not schema-validated — leftover `scope` keys don't
   cause errors
3. Migration can happen per-layer, per-domain, without disrupting composition

**What the script shows:**
([`examples/scope_promotion/phase5_migration.py`](../examples/scope_promotion/phase5_migration.py))

The migration script processes a mixed stage:
- `BatteryPack_SN42` — scope in overflow, not in schema → **migrated**
- `Chiller_01` — already migrated, no scope in overflow → **skipped**
- `UR10e_ModelDef` — scope in overflow, not in schema → **migrated**
- `Column_C14` — never had scope → **skipped**

**Sample output:**

```
Actions:
  ✅ /BatteryPack_SN42 (dpp): migrated scope='instance' from overflow to schema
  ⏭️  /Chiller_01 (windchill): no scope in overflow — skipped
  ✅ /UR10e_ModelDef (ros): migrated scope='type' from overflow to schema
  ⏭️  /Column_C14 (ifc): no scope in overflow — skipped

Summary: 2 migrated, 0 cleaned, 2 skipped

Before (BatteryPack_SN42):
  schema scope: ''
  overflow:     {"batteryModel": "LFP-280Ah-48V", "chemistry": "LFP", "scope": "instance"}

After (BatteryPack_SN42):
  schema scope: 'instance'
  overflow:     {"batteryModel": "LFP-280Ah-48V", "chemistry": "LFP"}
```

**Key observation:** Migration is straightforward, incremental, and non-breaking.
No big-bang migration required. The overflow dict naturally shrinks as fields
are promoted, while domain-specific metadata (batteryModel, chemistry, etc.)
remains in the overflow where it belongs.

---

## Conclusions

### The overflow dict is a staging area, not a dead end

This simulation demonstrates the complete lifecycle of a metadata field
through Hybrid C's architecture:

```
Phase 1: Freeform overflow     → Domain-specific, no governance
Phase 2: Cross-domain adoption  → Convention spreads via registry docs
Phase 3: Registry-spec validation → CI enforcement, still in overflow
Phase 4: Schema promotion        → Full USD-native validation + GUI
Phase 5: Migration               → Incremental cleanup, non-breaking
```

At no point was the process blocked. At every phase, the existing content
continued to work. The overflow dict provided a **zero-friction onramp**
for AAS-specific metadata, and the promotion path provided a **governed
escalation** when the field proved universally useful.

### Why this matters for the Hybrid C recommendation

1. **The overflow dict answers the "what if we need more fields" objection.**
   Stakeholders can ship immediately without schema work. Fields that prove
   their worth get promoted. Fields that remain domain-specific stay in
   overflow — and that's fine.

2. **The promotion path answers the "overflow is opaque" objection.**
   Yes, overflow dicts lack schema validation and GUI rendering. But that's
   a *temporary* condition for cross-cutting fields, not a permanent one.
   The registry-spec mechanism (Phase 3) provides intermediate governance,
   and schema promotion (Phase 4) provides full governance.

3. **The migration path answers the "how do we evolve" objection.**
   Schema changes are non-breaking (empty defaults). Migration is
   incremental (per-layer, per-domain). Old and new content coexist.
   This is the same pattern USD uses for schema versioning generally.

### Promotion criteria (suggested)

Based on this simulation, a field should be considered for promotion when:

| Criterion | Threshold |
|-----------|-----------|
| Cross-domain adoption | 3+ independent domains using it |
| Semantic consistency | Same field name, type, and allowed values across domains |
| Validation demand | CI validators exist and are catching real errors |
| Runtime gap | Stakeholders are requesting GUI/query support |
| Stability | Field semantics haven't changed in 6+ months |

These criteria could be formalized in the AOUSD governance documentation
alongside the three-tier domain promotion path (vendor → multi-vendor →
standard).
