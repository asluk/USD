# Registry-as-Spec: Could the Governance Registry Close Approach A's Interoperability Gap?

← [Back to COMPARISON.md](../COMPARISON.md)

## 1. The Claim Under Examination

The hybrid recommendation (§7.1) makes the following assertion about Approach A:

> **Approach A alone** repeats the `customData` pattern: technically capable,
> but practically un-interoperable because every consumer must know every
> vendor's ad-hoc dictionary structure. No `apiSchemas` declaration, no
> schema validation, no GUI discoverability.

This assumes that Approach A's dictionary structures are inherently opaque —
that no mechanism exists (or could exist) to make them discoverable and
validatable. But vendors must register in the AOUSD Domains Registry
regardless of which approach is adopted (see [governance.md §6.2](governance.md)).
What if that registry also included a **structural specification** for each
vendor's dictionary format?

This section examines whether a "registry-as-spec" mechanism could close
Approach A's interoperability gaps, and what that would actually require.

---

## 2. What Interoperability Actually Requires

Four capabilities define practical interoperability for source identifiers:

| # | Capability | Question | Approach A | Approach B |
|---|-----------|----------|------------|------------|
| 1 | **Enumeration** | Which vendor IDs exist on this prim? | ✅ Scan `assetInfo["sourceIds"]` dict keys | ✅ `apiSchemas` list / `GetAll()` |
| 2 | **Validation** | Is the dictionary structure correct? | ❌ None | ✅ Schema-enforced types |
| 3 | **GUI discoverability** | Can tools auto-render identifier fields? | ❌ Requires custom code per vendor | ✅ Automatic from schema |
| 4 | **Round-trip preservation** | Does data survive read-modify-write? | ✅ Native dict preservation | ✅ Native property preservation |

Approach A already handles enumeration (#1) and round-trip (#4).
The real gaps are **validation (#2)** and **GUI discoverability (#3)**.
The question is whether a registry-spec mechanism could close them.

---

## 3. The Registry-as-Spec Mechanism

### Current registry structure (per governance.md §6.2)

The proposed AOUSD Domains Registry maps domain keys to organizations:

```
domain_key:   "com.ptc.windchill"
organization: "PTC Inc."
contact:      "windchill-usd@ptc.com"
status:       "vendor"
description:  "Windchill PLM part and document identifiers"
```

### Extended registry with structural specification

The registry could additionally include a **field specification** for each
domain's dictionary structure:

```yaml
domain_key: "com.ptc.windchill"
organization: "PTC Inc."
contact: "windchill-usd@ptc.com"
status: "vendor"
description: "Windchill PLM part and document identifiers"
spec:
  version: "1.0"
  fields:
    - name: "primaryId"
      type: "string"
      required: true
      doc: "Windchill persistent object identifier (OID)"
      example: "VR:wt.part.WTPart:23639563"
    - name: "revision"
      type: "string"
      required: false
      doc: "Part revision designator"
      example: "Rev.C"
    - name: "displayNumber"
      type: "string"
      required: false
      doc: "Human-readable part number"
    - name: "navigationType"
      type: "string"
      required: false
      doc: "Windchill navigation criteria URI"
    - name: "state"
      type: "string"
      required: false
      doc: "Lifecycle state (In Work, Released, Obsolete)"
      enum: ["In Work", "Released", "Obsolete"]
    - name: "organization"
      type: "string"
      required: false
      doc: "Reverse-DNS identifier of the authoring organization"
```

This is essentially **JSON Schema for `assetInfo` dictionary entries**,
declared out-of-band in the governance registry rather than in USD's
schema infrastructure.

Each domain's spec could live as a standalone YAML or JSON file in the
registry repository — similar to how glTF extensions each have a README
defining their JSON structure.

---

## 4. Gap Analysis: What Registry-Spec Buys and What It Doesn't

| Capability | A (dict only) | A + registry spec | B (schema) |
|------------|---------------|-------------------|------------|
| Enumeration | Dict key scan | Dict key scan | `GetAppliedSchemas()` |
| **Offline/CI validation** | ❌ None | ✅ Read spec, validate dict | ✅ Schema + `UsdValidation` |
| **Runtime validation** | ❌ None | ⚠️ Requires new USD plugin* | ✅ USD-native |
| **GUI auto-rendering** | ❌ None | ⚠️ Requires new plugin infra* | ✅ Free from schema |
| Round-trip preservation | ✅ Native | ✅ Native | ✅ Native |
| Zero-code vendor onboarding | ✅ Yes | ✅ Yes (spec is declarative) | ❌ Needs `usdGenSchema` |
| Works with existing USD tools | ✅ (opaque) | ⚠️ Only with new tooling | ✅ Immediately |

**⚠️ = requires infrastructure that does not exist today.**

The critical insight: **registry-spec fully closes the offline/CI validation
gap**, but the **runtime validation** and **GUI auto-rendering** gaps require
new USD infrastructure — a plugin that reads registry specs at runtime and
translates them into property panels or validation hooks. This infrastructure
is non-trivial to build and would need adoption across every major USD
consumer (Omniverse, Houdini, Maya, usdview).

---

## 5. Precedent Scan

### glTF extension specifications

Each glTF extension includes a README defining its JSON structure — field
names, types, required/optional status, and examples. This **is** a
registry-spec pattern. However, consumers still need extension-aware code
to parse and act on extension data. The spec enables *validation* but not
*automatic GUI rendering* — exactly the split we see here.

### W3C `data-*` attributes

HTML `data-*` attributes are completely freeform with no registry. The HTML
validator checks syntax (valid attribute name) but not semantics (what the
data means). This is Approach A without even a registry — the floor case.

### OpenAPI / JSON Schema

The gold standard for "spec outside the runtime." Works for REST APIs
because a rich tooling ecosystem exists (Swagger UI auto-generates
interactive documentation, validators enforce schemas at request time).
**No equivalent USD tooling exists today.** Building it would be the
primary investment required.

### IANA registries

Some IANA registries include formal syntax definitions (ABNF grammars for
media types, URI schemes). This proves the pattern works at scale for
*validation* — but IANA registries don't drive GUI rendering. Consumers
must still implement format-specific handling.

**Pattern across all precedents:** Registry-with-spec consistently enables
validation and documentation, but never automatically drives runtime GUI
rendering. That capability always requires either (a) format-native schema
infrastructure (USD schemas, JSON Schema + Swagger UI) or (b) custom
tooling per consumer.

---

## 6. What It Would Take to Build

| Component | Difficulty | Effort | Comparison to Schema Approach |
|-----------|-----------|--------|-------------------------------|
| 1. **Registry spec format** (YAML/JSON schema dialect for dict entries) | Easy | ~1–2 weeks to define | N/A (new) |
| 2. **CI validator** (Python tool that reads specs + validates `assetInfo` dicts) | Medium | ~2–4 weeks | Already exists: `UsdValidation` framework |
| 3. **Runtime USD plugin** (reads specs, exposes fields to property panels) | Hard | Months; deep USD integration | Already exists: USD schema system |
| 4. **Consumer adoption** (Omniverse, Houdini, Maya, usdview support the spec reader) | Very hard | Requires buy-in from each DCC vendor | Already done: all USD-aware apps render schema properties |

The fundamental asymmetry: **Approach B gets components 1–4 for free from
the existing USD schema system.** A registry-spec mechanism would need to
build them from scratch, and the hardest parts (runtime plugin, consumer
adoption) are the same ones that take years in any standards ecosystem.

---

## 7. Impact on the Claim

### What the claim gets right

- **"No schema validation"** — True today. External validators could be
  built, but they do not exist and are not part of the USD ecosystem.
- **"No GUI discoverability"** — True today, and the hardest gap to close.
  Requires new infrastructure with no clear path to universal adoption.
- **"No `apiSchemas` declaration"** — True by design. A consumer cannot
  know which identifier domains exist without parsing all `assetInfo`
  dictionaries across all prims.

### What the claim overstates

- **"Practically un-interoperable"** is too strong. With a registry-spec
  mechanism:
  - **CI/offline validation** is fully achievable with modest tooling investment.
  - **Documentation and field discovery** (reading the spec to understand a
    vendor's dict structure) is immediate — it's just a file in the registry.
  - **Programmatic consumers** (pipeline scripts, ETL tools) can read the
    spec and parse dicts correctly without vendor-specific code.

- The correct framing: Approach A's interoperability gap is a **tooling gap**,
  not an **architectural impossibility**. The dictionary structure is not
  inherently opaque if a specification exists alongside it. But closing the
  runtime/GUI tooling gap requires building infrastructure that Approach B
  already provides for free.

### Suggested revised language

The current §7.1 text:

> Approach A alone repeats the `customData` pattern: technically capable,
> but practically un-interoperable because every consumer must know every
> vendor's ad-hoc dictionary structure. No `apiSchemas` declaration, no
> schema validation, no GUI discoverability.

Suggested revision:

> Approach A alone provides no built-in mechanism for validation or GUI
> discoverability. While a registry-spec mechanism could partially close
> these gaps (see [registry_spec_analysis.md](details/registry_spec_analysis.md)),
> runtime validation and automatic property-panel rendering would require
> new USD infrastructure that does not exist today — infrastructure that
> Approach B provides natively through the existing schema system. Without
> such infrastructure, consumers must implement vendor-specific dictionary
> parsing, echoing the `customData` fragmentation pattern the proposal
> aims to resolve.

---

## 8. Implications for Hybrid C

The registry-spec analysis **strengthens the case for Hybrid C** rather
than undermining it:

1. **Governed common fields get native schema benefits now.** The four
   common properties (`primaryId`, `revision`, `domain`, `label`) benefit
   immediately from schema validation, GUI rendering, and `apiSchemas`
   discoverability. No new infrastructure needed.

2. **Overflow dict fields can gain registry-spec validation later.** As
   the AOUSD ecosystem matures, a registry-spec mechanism for the
   `assetInfo["sourceIds"]` overflow dictionaries becomes a natural
   extension — not a replacement for the schema, but a complement to it.

3. **Natural evolution path.** The governance model already describes
   promoting overflow fields to schema properties when they stabilize
   (§7.5). Registry-spec provides an intermediate step:

   ```
   Freeform overflow → Registry-spec validated → Promoted to schema property
        (day 1)          (ecosystem matures)        (field stabilizes)
   ```

4. **Complementary, not competing.** Registry-spec doesn't argue against
   schemas for common fields — it argues that the *overflow* portion of
   Hybrid C need not remain permanently opaque. The two mechanisms layer
   naturally.

---

## 9. Summary

| Question | Answer |
|----------|--------|
| Could a registry-spec mechanism close Approach A's validation gap? | **Partially.** Offline/CI validation: yes. Runtime validation: requires new infra. |
| Could it close the GUI discoverability gap? | **Only with significant new infrastructure** that would need adoption across all major USD consumers. |
| Does this invalidate the recommendation for schemas (B/C)? | **No.** Schemas provide these capabilities today, for free, through existing USD tooling. |
| Does this change anything about Hybrid C? | **Yes — positively.** It shows the overflow dict has a path to becoming less opaque over time, strengthening the hybrid's long-term viability. |
| Should the claim language be revised? | **Yes.** "Practically un-interoperable" overstates the case. The gap is real but is a tooling gap, not an architectural impossibility. |
