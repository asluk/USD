# Composition Behavior

← [Back to COMPARISON.md](../COMPARISON.md)

Composition behavior is one of the most consequential differences between the
two approaches. It governs what happens when source identifiers are authored
across multiple layers - a common scenario when a base asset (authored by a
design team) is overridden by a downstream consumer (e.g., a construction
coordinator updating a revision, or an operational system adding telemetry
bindings).

## Test scenario

Both approaches were tested with the same scenario:

- **Base layer:** A chiller prim carries identifiers from three systems
  (Windchill, SAP, IFC). The Windchill entry includes `primaryId`,
  `revision`, and a `metadata` sub-dict with `displayNumber` and `state`.

- **Override layer:** References the base and makes two changes:
  1. Updates the Windchill `revision` from "Rev.B" to "Rev.C" and
     `state` from "In Work" to "Released"
  2. Adds a new OPC UA domain binding

## Approach A: Element-wise dictionary composition

```usda
# Override layer (Approach A)
def Xform "Chiller" (
    prepend references = @./composition_test_a_base.usda@
    assetInfo = {
        dictionary sourceIds = {
            dictionary windchill = {
                string revision = "Rev.C"
                dictionary metadata = {
                    string state = "Released"
                }
            }
            dictionary opcua = {
                string primaryId = "ns=4;s=Building.HVAC.Chiller01"
            }
        }
    }
)
```

**Composed result for `windchill`:**

`assetInfo` composes element-wise at each dictionary nesting level. The
override provides `revision` and `metadata.state`; the base provides
`primaryId` and `metadata.displayNumber`. Because composition merges per
key at each level:

- `primaryId` = `"VR:wt.part.WTPart:23639563"` ✅ (from base - preserved)
- `revision` = `"Rev.C"` ✅ (from override - updated)
- `metadata.displayNumber` = `"CH-7500-A"` ✅ (from base - preserved)
- `metadata.state` = `"Released"` ✅ (from override - updated)

This works correctly **in this case** because both layers structured their
dictionaries at the same granularity. However, the behavior is subtle:

**Risk scenario:** If the override layer had authored the entire `windchill`
dictionary with only `revision` (omitting `primaryId`), the composed result
would still contain `primaryId` from the base - because `assetInfo` merges
per key. But if a tool *serializes* the override by first reading the
composed value and writing it back (a common pattern), it would write the
full dictionary including `primaryId`, which would then shadow the base
layer's value. This round-trip hazard is inherent to dictionary-based
composition and requires discipline from authoring tools.

**SAP and IFC:** Completely untouched. The override layer's `sourceIds`
merges at the domain level, so domains not mentioned in the override
are preserved from the base.

**OPC UA:** Added cleanly as a new key in `sourceIds`.

## Approach B: Per-property composition

```usda
# Override layer (Approach B)
def Xform "Chiller" (
    prepend references = @./composition_test_b_base.usda@
    prepend apiSchemas = ["SourceIdSchemaAPI:opcua"]
)
{
    string sourceIdentifier:windchill:revision = "Rev.C"

    string sourceIdentifier:opcua:primaryId = "ns=4;s=Building.HVAC.Chiller01"
    token sourceIdentifier:opcua:domain = "org.opcfoundation.ua"
    string sourceIdentifier:opcua:label = "OPC UA NodeId"
}
```

**Composed result for `windchill`:**

Each property composes independently. The override authors only
`sourceIdentifier:windchill:revision`; every other `windchill` property
retains its value from the base:

- `primaryId` = `"VR:wt.part.WTPart:23639563"` ✅ (from base)
- `revision` = `"Rev.C"` ✅ (from override)
- `domain` = `"com.ptc.windchill"` ✅ (from base)
- `label` = `"Windchill Part OID"` ✅ (from base)

There is **no risk of unintentional side effects**. Overriding one property
cannot disturb another property, even within the same instance. This is
the standard USD property composition model that all schema-based data
follows.

**SAP and IFC:** Completely untouched. Their properties are separate
attributes with their own opinion stacks.

**OPC UA:** Added via `prepend apiSchemas` (list editing), which appends
to the existing schema list without disturbing other entries.

## Composition comparison

| Aspect | Approach A | Approach B |
|--------|-----------|------------|
| Override granularity | Per dictionary key at each nesting level | Per individual property |
| Risk of unintentional data loss | Medium (round-trip serialization hazard) | None |
| Adding a new domain | Add key to `sourceIds` dict | `prepend apiSchemas` + author properties |
| Removing a domain | Delete key (requires authoring empty or using `ClearDomain()`) | Remove from `apiSchemas` list |
| Partial field update | Works if structured correctly; subtle | Always works; no subtlety |
| Tool author burden | Must understand dict merge semantics | Standard property authoring |

**Verdict:** Approach B's per-property composition is strictly safer and
more predictable. Approach A's element-wise dictionary composition works
correctly but requires more discipline from tool authors and has a
round-trip serialization hazard that could cause subtle data corruption
in careless implementations.
