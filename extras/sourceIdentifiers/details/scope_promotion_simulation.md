# Scope Promotion Simulation: From Overflow Dict to Schema Property

← [Back to COMPARISON.md](../COMPARISON.md)

## Overview

This simulation traces the lifecycle of a single metadata field — `scope`
(type-vs-instance identifier classification) — as it evolves from a
domain-specific convention in one vendor's overflow dictionary to a
ratified schema property on the base `SourceIdHybridAPI`. The simulation
demonstrates Hybrid C's key architectural advantage: **the overflow dict
is not a dead end, but a staging area for field maturation.**

Each phase includes concrete `.usda` files in
[`examples/scope_promotion/`](../examples/scope_promotion/) and, where
applicable, Python scripts demonstrating validation and migration.

**Timeline (illustrative):**

| Phase | Timeframe | `scope` lives in | Who uses it |
|-------|-----------|-------------------|-------------|
| 1 | Day 1 | AAS overflow dict only | AAS/DPP stakeholders |
| 2 | ~6–12 months | Overflow dict (3+ domains) | AAS, manufacturing, robotics |
| 3 | ~1–2 years | Overflow dict + registry-spec validation | All adopters; CI-enforced |
| 4 | ~2+ years | Schema property (5th field) | Everyone; TAC-ratified |
| 5 | Post-promotion | Schema property; overflow deprecated | Migration complete |

---

## Phase 1: AAS-Only Overflow (Day 1)

_`scope` is a domain-specific AAS convention. No other stakeholder uses it._

**Scenario.** The AAS/Industry 4.0 community needs to distinguish type-level
identifiers (product families, part designations) from instance-level identifiers
(serial numbers, deployed units). AAS calls these `globalAssetId` (type) and
`specificAssetIds` (instance). They encode this as a `scope` string in their
`assetInfo` overflow dictionary.

Meanwhile, IFC's GlobalId is always instance-level by definition, and Windchill's
part OID always references a specific part revision. Neither domain needs `scope`.

**What the `.usda` shows:**
([`examples/scope_promotion/phase1_aas_overflow.usda`](../examples/scope_promotion/phase1_aas_overflow.usda))

- `BatteryPack_SN42` — DPP with `scope = "instance"` (a specific battery unit)
- `BatteryPack_LFP280` — DPP with `scope = "type"` (the product family)
- `Column_C14` — IFC, no scope (GlobalId is always instance-level)
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

- **IFC:** Still no need for `scope`. IFC GlobalId is always instance-level
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
domains that don't need it (IFC, glTF, MaterialX) are unaffected.

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

<!-- PHASE 5 CONTENT PLACEHOLDER -->

---

## Conclusions

<!-- CONCLUSIONS PLACEHOLDER -->
