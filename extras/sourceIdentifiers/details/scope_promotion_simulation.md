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

<!-- PHASE 1 CONTENT PLACEHOLDER -->

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
