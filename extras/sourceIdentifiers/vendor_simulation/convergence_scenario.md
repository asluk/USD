# Convergence Scenario: Competing Identifier Schemes Over Time

## The Setup

Two companies independently build USD pipelines for digital twin workflows.
Both need to bind USD prims to real-world equipment for operational telemetry.

- **Contoso Corp** creates an identifier scheme called `"contoso_iot"` that
  carries a device ID, a telemetry endpoint, and a data format version.
- **Fabrikam Inc** creates `"fabrikam_dt"` that carries a twin ID, a
  connection string, and a model version.

Both are solving the same problem (operational binding), but with different
metadata structures and naming conventions.

**Year 1:** Both vendors ship independently.
**Year 2:** AOUSD Digital Engineering Working Group recognizes the pattern
and proposes a standard `"aousd_opbinding"` (operational binding) scheme.
**Year 3:** Both vendors migrate to the standard. Existing content must
interoperate with new content during the transition.

## What the simulation tests

1. **Independent authoring** (Year 1): Can both vendors coexist on the same prim?
2. **Discovery** (Year 1-2): Can tools find "all operational bindings" without
   knowing vendor-specific conventions?
3. **Convergence** (Year 2-3): How hard is the migration? What breaks?
4. **Coexistence** (Year 3+): Can old content and new content interoperate?
