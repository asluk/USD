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

<!-- PHASE 2 CONTENT PLACEHOLDER -->

---

## Phase 3: Registry-Spec Validation (~1–2 Years)

_AOUSD CI validator enforces `scope` values. The convention is formalized._

<!-- PHASE 3 CONTENT PLACEHOLDER -->

---

## Phase 4: Schema Promotion (~2+ Years)

_TAC ratifies `scope` as an optional 5th property on `SourceIdHybridAPI`._

<!-- PHASE 4 CONTENT PLACEHOLDER -->

---

## Phase 5: Coexistence & Migration (Post-Promotion)

_Old stages with `scope` in overflow still work. Migration script moves values to schema property._

<!-- PHASE 5 CONTENT PLACEHOLDER -->

---

## Conclusions

<!-- CONCLUSIONS PLACEHOLDER -->
