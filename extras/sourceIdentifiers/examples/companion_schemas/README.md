# Illustrative Companion Schemas

These schemas are **illustrative examples**, not normative specifications.
They demonstrate how a domain body (buildingSMART, IDTA) could produce
codeless companion schemas for Tier 2 of the three-tier extensibility
model described in [COMPARISON.md](../../COMPARISON.md).

In practice, the domain body — not AOUSD — would author, maintain, and
distribute these schemas. The files here exist solely to make the
three-tier model concrete and testable.

## Contents

- `ifc/schema.usda` — IFC companion schema (`SourceIdIfcAPI`)
- `ifc/plugInfo.json` — plugin registration for IFC companion
- `aas/schema.usda` — AAS/DPP companion schema (`SourceIdAasAPI`)
- `aas/plugInfo.json` — plugin registration for AAS companion

## How codeless schemas work

A codeless schema requires two files:

1. **`schema.usda`** — the schema definition with `skipCodeGeneration = true`
2. **`plugInfo.json`** — plugin metadata pointing to `generatedSchema.usda`

Running `usdGenSchema schema.usda .` produces `generatedSchema.usda` and
updates `plugInfo.json`. Adding the output directory to
`PXR_PLUGINPATH_NAME` registers the schema with `UsdSchemaRegistry`.

No C++, no Python, no compilation required.
