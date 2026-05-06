# Governance, Validation & Deployment

← [Back to COMPARISON.md](../COMPARISON.md)

## 6.1 How other standards bodies govern vendor extensions

Source identifier domain registration is a **data-format governance**
problem, not a runtime mechanism. Unlike USD's plugin system (which
registers schemas at application startup), identifier domains are
declared in USD content and must be governed outside the runtime.

Six precedents from other standards bodies inform this design:

| Body | Mechanism | Tiers | Registration | Collision Prevention |
|------|-----------|-------|-------------|---------------------|
| **Khronos glTF** | `Prefixes.md` on GitHub | `VENDOR_` → `EXT_` → `KHR_` | GitHub issue to reserve prefix | Prefix uniqueness in registry |
| **Khronos OpenGL/Vulkan** | Extension registry | `GL_NV_` → `GL_EXT_` → `GL_ARB_` → core | Formal registry at registry.khronos.org | Registered prefixes |
| **IETF/IANA** | RFC 8126 registration policies | Private Use → First Come First Served → Expert Review → Standards Action | IANA registry with designated expert | Unique registration per entry |
| **W3C** | WICG incubation | Community Group → Working Group → Recommendation | Community Group proposal | `data-*` for freeform; standard attrs governed |
| **buildingSMART** | bSDD data dictionary | Organization-published dictionaries hosted centrally | Online portal + REST API | Centralized namespace |
| **Java/XML** | Reverse-DNS convention | Single tier (by convention) | None (self-service) | Domain name ownership |

**Relationship to buildingSMART bSDD.** The buildingSMART Data Dictionary
(bSDD) is a centralized data dictionary for building industry property
definitions — it defines what properties mean (e.g., "fire resistance
rating" with units, allowed values, and translations). The proposed AOUSD
Domains Registry serves a different purpose: it coordinates **namespace
ownership** for identifier domains (e.g., "the key `org.buildingsmart.ifc`
belongs to buildingSMART"). The two systems are complementary, not
competing: bSDD defines property semantics; the AOUSD registry prevents
namespace collisions. A buildingSMART stakeholder would register their
domain prefix in the AOUSD registry and publish their identifier field
definitions in bSDD (or their own specification), just as a Khronos vendor
registers an extension prefix and publishes the extension specification
separately.

**Key insight:** Two models bracket the design space for what AOUSD would
need for source identifiers:

**Khronos glTF** is the closest structural analog:

- **Low barrier:** Any vendor can request a prefix by filing a GitHub
  issue. No membership required.
- **Three-tier:** Vendor-specific (ship independently) → multi-vendor
  (`EXT_`, proven interop) → ratified (`KHR_`, Khronos IP framework).
- **Declarative:** Each glTF file lists `extensionsUsed` and
  `extensionsRequired` — consumers know what to expect without parsing
  the full file. This is analogous to Approach B's `apiSchemas` list.
- **Not a runtime mechanism:** The registry is a Markdown file in a
  GitHub repo. Enforcement is by convention and community review.

**W3C WICG** provides the closest *process* analog:

- **Community-first:** Any group can propose an incubation via WICG
  (Web Incubator Community Group) with no upfront membership barrier.
- **Three-tier:** Community Group (experiment freely) → Working Group
  (formal spec development) → W3C Recommendation (ratified standard).
- **Freeform escape hatch:** HTML `data-*` attributes let any author
  attach custom metadata without standardization — directly analogous
  to `assetInfo`/`customData` in USD.
- **Governed attrs replace vendor prefixes:** CSS vendor prefixes
  (`-webkit-`, `-moz-`) are deprecated in favor of unprefixed standard
  properties once ratified — analogous to vendor domain → AOUSD standard
  domain promotion.

The proposed AOUSD model draws from both: glTF's lightweight GitHub-based
registry mechanism and W3C's community-driven incubation-to-standard path.

## 6.2 What a governance model would look like for source identifiers

Regardless of which approach is chosen, AOUSD would maintain a registry
of identifier domain prefixes. The proposed model:

1. **AOUSD maintains a Domains Registry** (analogous to glTF's
   `Prefixes.md` or W3C's Community Group registry) — a list mapping
   domain keys/prefixes to organizations, with contact information
   and status.

2. **Three tiers:**
   - **Vendor domains** (`com.ptc.windchill`, `com.nvidia.omniverse`):
     self-service registration, First Come First Served.
   - **Multi-vendor domains** (`ext.simready`, `ext.digitaltwins`):
     requires demonstrated multi-vendor implementation.
   - **AOUSD standard domains** (`aousd.ifc`, `aousd.plm`):
     ratified by AOUSD TAC, covered by AOUSD IP framework.

3. **Registration requires:** domain key, organization name, contact,
   URL, brief description of the identifier scheme. No code, no schema
   plugin, no membership fee.

4. **Promotion path:** Vendor → multi-vendor (demonstrated adoption by
   2+ organizations) → standard (TAC ratification).

## 6.3 How each approach interacts with governance

**Governance is symmetric across the four approaches: no mechanism
enforces anything by itself; a registry-spec validator must run against
authored content under any approach.** What differs is *where the
validator looks* and how easily it can do its job.

**Approach A:**
- Domain keys are freeform strings in `assetInfo` dictionaries.
- A consumer must parse `assetInfo["sourceIds"]` on each prim to discover
  the domain set. There is no structural inventory.
- A validator iterates dict keys per prim and checks them against the
  AOUSD Domains Registry. Unregistered keys are detectable, just not
  without traversal.

**Approach B:**
- Domain instances are declared in the `apiSchemas` list.
- A consumer reads `apiSchemas` to discover which identifier domains are
  present without parsing property values.
- This is structurally analogous to glTF's `extensionsUsed` array.
- Governance violations are detectable from the `apiSchemas` list — but
  detection still requires the validator to run; nothing prevents an
  author from listing arbitrary strings in `apiSchemas`. The `domain`
  property provides a secondary disambiguation.

**Approach C:**
- Same as B for the schema instances; same as A for overflow keys.
- Validator combines both checks.

**Approach D:**
- Per-facet `SemanticsLabelsAPI:<system>:<facet>` instances declared in
  the `apiSchemas` list — both the system *and* the facet are visible
  on the schemas list itself.
- Identity strings live in `assetInfo["source"][<system>]`; system keys
  there should match an apiSchema instance prefix on the same prim
  (validator rule).
- Validators check both the system prefix and the facet suffix against
  the Domains Registry from a single pass over `apiSchemas`. Arguably
  the easiest validator to implement.

## 6.4 Validator designs

Both approaches can be validated, but the implementation difficulty
differs significantly.

**Approach A validator (pseudocode):**

```python
def validate_source_ids_a(stage, registry):
    """Validate Approach A source identifiers against a domain registry."""
    errors = []
    for prim in stage.Traverse():
        source_ids = prim.GetAssetInfoByKey("sourceIds")
        if not source_ids:
            continue
        if not isinstance(source_ids, dict):
            errors.append(f"{prim.GetPath()}: sourceIds is not a dictionary")
            continue
        for domain_key, domain_data in source_ids.items():
            # Check domain is registered
            if domain_key not in registry:
                errors.append(
                    f"{prim.GetPath()}: unregistered domain '{domain_key}'")
            # Check required fields
            if not isinstance(domain_data, dict):
                errors.append(
                    f"{prim.GetPath()}: domain '{domain_key}' is not a dict")
                continue
            if "primaryId" not in domain_data:
                errors.append(
                    f"{prim.GetPath()}: domain '{domain_key}' missing primaryId")
            # Type checking is manual - no schema enforcement
            primary = domain_data.get("primaryId")
            if primary is not None and not isinstance(primary, str):
                errors.append(
                    f"{prim.GetPath()}: primaryId in '{domain_key}' is not a string")
    return errors
```

**Approach B validator (pseudocode):**

```python
def validate_source_ids_b(stage, registry):
    """Validate Approach B source identifiers against a domain registry."""
    errors = []
    for prim in stage.Traverse():
        instances = UsdSourceIdSchemaAPI.GetAll(prim)
        for instance_name in instances:
            api = UsdSourceIdSchemaAPI.Get(prim, instance_name)
            # Check domain is registered
            domain = api.GetDomainAttr().Get()
            if domain and domain not in registry:
                errors.append(
                    f"{prim.GetPath()}: unregistered domain '{domain}'")
            # Check primaryId is authored (not just fallback)
            if not api.GetPrimaryIdAttr().HasAuthoredValue():
                errors.append(
                    f"{prim.GetPath()}: instance '{instance_name}' "
                    f"has no authored primaryId")
            # Type checking is automatic - schema enforces types
            # Fallback detection is built in
            # No manual isinstance() checks needed
    return errors
```

**Approach D validator (pseudocode):**

```python
def validate_source_ids_d(stage, registry):
    """Validate Approach D source identifiers against a domain registry."""
    errors = []
    for prim in stage.Traverse():
        # Inventory from apiSchemas list — exposes (system, facet) pairs
        applied = prim.GetAppliedSchemas()
        labels_instances = [
            s.split(":", 2) for s in applied
            if s.startswith("SemanticsLabelsAPI:")
        ]
        for parts in labels_instances:
            if len(parts) != 3:
                continue
            _, system, facet = parts
            if system not in registry:
                errors.append(
                    f"{prim.GetPath()}: unregistered system '{system}'")
            elif facet not in registry[system].get("facets", {}):
                errors.append(
                    f"{prim.GetPath()}: unregistered facet '{system}:{facet}'")

        # Identity strings: validate that any system key in
        # assetInfo["source"] has at least one corresponding apiSchema instance,
        # or is a system that registers identity-only.
        source_dict = prim.GetAssetInfoByKey("source") or {}
        applied_systems = {parts[1] for parts in labels_instances if len(parts) == 3}
        for system, payload in source_dict.items():
            if system not in registry:
                errors.append(
                    f"{prim.GetPath()}: unregistered system '{system}' in assetInfo")
            if "identifier" not in payload:
                errors.append(
                    f"{prim.GetPath()}: source['{system}'] missing 'identifier'")
    return errors
```

**Comparison:**

| Validator Aspect | A | B | C | D |
|-----------------|---|---|---|---|
| Discovery | Parse all `assetInfo` dicts | `GetAll()` returns instances | `GetAll()` + walk overflow | `GetAppliedSchemas()` per facet |
| Type safety | Manual `isinstance()` | Schema-enforced | Schema (common) + manual (overflow) | Schema-enforced (token arrays) |
| Missing fields | Manual key check | `HasAuthoredValue()` | Mixed | `HasAuthoredValue()` per label property |
| Domain resolution | Dict key only | `domain` token | `domain` token | apiSchema instance system + facet |
| Facet resolution | Dict key | N/A (no facets) | Overflow dict key | apiSchema instance suffix |
| Lines of validation code | ~30 | ~15 | ~25 | ~20 |
| Can run without USD API | Yes (dict parsing) | Requires USD schema system | Requires USD schema system | Requires USD schema system |

## 6.5 Validator development and deployment per identifier extension

OpenUSD's `UsdValidation` framework (introduced 2024) provides a
plugin-based system for registering validators that run against stages.
Validators are registered via `plugInfo.json` with metadata including
`doc`, `keywords`, and critically `schemaTypes` - which lets a
validator declare which schema types it targets.

Each identifier "extension" (domain) has two layers of validation:

1. **Structural validation:** Are the common fields present and
   well-formed? (primaryId is a non-empty string, domain is a
   registered token, revision is present if required by the domain.)

2. **Domain-specific validation:** Are the domain's values semantically
   correct? (Is this a valid IFC GlobalId? Is this Windchill OID
   resolvable? Does this STEP entity ID conform to AP242?)

**Approach A validator deployment:**

```
# What a domain stakeholder must produce:

1. plugInfo.json declaring the validator
2. Validator implementation (C++ or Python)
   - Must manually parse assetInfo["sourceIds"] dictionaries
   - Cannot target a specific schemaType (no schema to target)
   - Must iterate all prims and inspect assetInfo on each
   - Domain-specific field validation is manual dict key checking
```

Because Approach A has no schema, validators cannot use the
`schemaTypes` targeting mechanism. A validator wanting to check
IFC identifiers must register as a generic stage validator and
filter prims manually by inspecting their `assetInfo["sourceIds"]`
dictionaries for the `"ifc"` key. There is no way to declare
"run this validator only on prims that carry IFC identifiers."

**Approach B/C validator deployment:**

```
# What a domain stakeholder must produce:

1. plugInfo.json declaring the validator with:
   - schemaTypes: ["SourceIdSchemaAPI"]
   - keywords: ["sourceIdentifier", "ifc"]
2. Validator implementation (C++ or Python)
   - Can target SourceIdSchemaAPI schema type directly
   - Uses typed API: GetPrimaryIdAttr(), GetDomainAttr()
   - Domain filtering via GetDomainAttr().Get() == "org.buildingsmart.ifc"
   - Domain-specific validation is still custom but benefits from
     typed property access
```

**With the hybrid (Approach C)**, domain-specific metadata in
`assetInfo` requires the same manual dict parsing as Approach A for
the overflow fields. But the common fields (primaryId, revision,
domain, label) are schema-validated automatically, and the validator
can use `schemaTypes` targeting to run only on prims with the schema
applied.

**Comparison of validator development cost per domain extension:**

| Dimension | Approach A | Approach B | Approach C (Hybrid) |
|-----------|-----------|-----------|--------------------|
| Schema targeting | ❌ None | ✅ schemaTypes | ✅ schemaTypes |
| Common field validation | Manual dict parsing | Built-in (schema types) | Built-in (schema types) |
| Domain-specific validation | Manual dict parsing | Manual (custom attrs or companion schema) | Manual dict parsing (assetInfo) |
| Prim filtering | Full stage traverse + dict inspect | Schema-targeted (efficient) | Schema-targeted (efficient) |
| Validator registration | plugInfo.json | plugInfo.json | plugInfo.json |
| Total validator code (domain) | ~50-100 lines | ~30-50 lines | ~40-70 lines |

The validation framework advantage of B/C is real but moderate -
the main win is schema-targeted prim filtering (skip prims without
the schema applied) and typed common field access. Domain-specific
validation is equally custom across all approaches.

## 6.6 Deployment friction for identifier stakeholders

An "identifier stakeholder" is an organization that wants their
identifier scheme to be expressible in USD content: a PLM vendor
(PTC, Siemens), a standards body (buildingSMART, ISO), a DCC vendor
(Autodesk, SideFX), or an end-user enterprise.

**What a stakeholder must do under each approach:**

| Step | Approach A | Approach B |
|------|-----------|------------|
| 1. Register domain | Register key in AOUSD Domains Registry | Register instance name in AOUSD Domains Registry |
| 2. Document scheme | Write specification for their sub-dictionary structure | Write specification for which properties they use |
| 3. Start authoring | Write `assetInfo["sourceIds"]["<key>"]` in any tool that can author `assetInfo` | Apply schema instance + author 4 properties in any USD-aware tool |
| 4. Add domain-specific metadata | Just add keys to their dictionary - no coordination | Must register companion schema OR use custom attributes |
| 5. Validate content | Run external validator against their spec | Schema validation covers base fields; domain-specific fields need external validator |
| 6. Ship to consumers | Consumers parse their dict structure per their spec | Consumers use standard schema API; domain-specific metadata needs their spec |

**Net assessment:**

- **Steps 1-3** are equivalent in both approaches. Initial adoption
  friction is near-zero for both.

- **Step 4** is where the approaches diverge sharply. Approach A lets
  stakeholders evolve their metadata independently and immediately.
  Approach B forces a choice: live with the 4 common properties
  (insufficient for most industrial use cases), or invest in companion
  schema work.

- **Steps 5-6** favor Approach B for the common fields (schema-driven)
  but still require Approach A-style work for domain-specific metadata
  regardless.

## 6.7 The real cost of schema registration

The friction of "just register a companion schema" is often
underestimated. Consider what a domain stakeholder (e.g., PTC wanting
a `WindchillIdentifierAPI`) must actually produce:

For reference, `UsdSemanticsLabelsAPI` - one of the *simplest*
multi-apply schemas in the OpenUSD codebase - requires **~1,150 lines
across 16 files** (excluding tests and the optional `LabelsQuery`
helper):

| File category | Files | Lines | Notes |
|--------------|-------|-------|-------|
| `schema.usda` | 1 | 36 | Schema definition |
| `generatedSchema.usda` | 1 | 19 | Auto-generated by `usdGenSchema` |
| `plugInfo.json` | 1 | 29 | Plugin registration |
| `CMakeLists.txt` | 1 | 42 | Build system |
| C++ implementation | 3 | 327 | `labelsAPI.cpp` (285), `tokens.cpp` (25), `module.cpp` (17) |
| C++ headers | 5 | 466 | `api.h`, `labelsAPI.h`, `tokens.h`, `pch.h`, `generatedSchema.module.h` |
| Python wrappers | 2 | 204 | `wrapLabelsAPI.cpp` (181), `wrapTokens.cpp` (23) |
| Module init | 1 | 8 | `__init__.py` |
| Generated class list | 1 | 15 | `generatedSchema.classes.txt` |
| **Total** | **16** | **~1,146** | |

A domain stakeholder who wants typed properties beyond the common
4 (primaryId, revision, domain, label) must either:

1. **Build a full schema plugin** (Approach B's path): ~1,150+ lines,
   16 files, familiarity with `usdGenSchema`, CMake, PXR build system,
   Boost.Python wrapping, and the `plugInfo.json` registration mechanism.
   Must rebuild when OpenUSD updates. Must distribute the plugin to all
   consumers.

2. **Use custom attributes** (ad-hoc escape hatch): Author
   `custom string windchill:displayNumber = "CH-7500-A"` alongside the
   schema properties. No schema registration needed, but also no
   validation, no fallback values, no discoverability, and the `custom`
   prefix marks them as untyped - exactly the `customData` fragmentation
   the proposal aims to solve.

3. **Use `assetInfo` sub-dictionaries** (Approach C's path): Author
   domain-specific metadata in `assetInfo["sourceIds"]["windchill"]`.
   Zero schema work. Zero files to touch. Element-wise composition.
   Not schema-validated, but this is the *domain-specific overflow*
   case - the common fields that need validation are already covered
   by the multi-apply schema.

Option 3 is why the hybrid (Approach C) exists: it eliminates the
schema registration burden for domain-specific metadata while
preserving schema-backed validation for the common fields.

**Important correction: codeless schemas change the calculus.**
OpenUSD supports `skipCodeGeneration = true` in `usdGenSchema`,
producing **codeless schemas** that require only:

1. `schema.usda` (the schema definition - ~30-100 lines)
2. Run `usdGenSchema` → produces `generatedSchema.usda` + `plugInfo.json`
3. Drop these files into a USD plugin path

No C++, no Python wrappers, no `CMakeLists.txt`, no compilation.
The schema is available at runtime for property creation, introspection,
and validation - but without convenience C++/Python API methods.
Access is through the generic `UsdPrim::GetAttribute()` and
`UsdPrim::ApplyAPI()` interfaces.

This dramatically lowers the barrier for domain-specific schemas in
Approach B/C. A domain stakeholder (e.g., buildingSMART) could produce
a codeless `IfcSourceIdSchemaAPI` schema with typed properties for
ifcType, schema, and classification in ~50 lines of `schema.usda` +
a single `usdGenSchema` run. No C++ expertise required.

The full ~1,150-line / 16-file cost applies only when the stakeholder
wants **compiled C++/Python convenience APIs** (typed getters/setters
like `GetPrimaryIdAttr()`). For many stakeholders, codeless schemas
are sufficient.

| Deployment tier | Files | Lines | C++ needed? | Approach |
|----------------|-------|-------|-------------|----------|
| Codeless schema | 3 | ~80 | No | B/C domain extension |
| Compiled schema | 16+ | ~1,150+ | Yes | B/C with convenience API |
| assetInfo only | 0 | 0 | No | A, or C metadata overflow |

**Note on prototype fidelity:** All three schema implementations have
been processed through `usdGenSchema`, producing full generated output
in `pxr/usd/<module>/generated/` directories. Codeless (runtime-only)
versions are installed in `extras/sourceIdentifiers/installed_schemas/`
and verified to load at runtime. The hand-written C++ source files in
each module directory show the convenience API patterns; the generated
files are the authoritative output.

**The usdGenSchema barrier is especially significant for non-M&E
stakeholders.** AECO firms, PLM vendors, and standards bodies like
buildingSMART or ASHRAE do not typically have C++ USD expertise on
staff. Asking them to produce a schema plugin is a non-starter for
initial adoption. The hybrid's `assetInfo` overflow lets them ship
immediately; a schema plugin can come later if their metadata fields
stabilize and warrant formal typing.

## 6.8 Why Approach D collapses most of this section

Most of §6.5–§6.7 wrestles with the cost of producing schemas for domain
extensions: codegen, plugin distribution, the `usdGenSchema` barrier,
codeless schemas as a partial fix. **Approach D sidesteps the entire
discussion** for classification metadata: domains use
`UsdSemanticsLabelsAPI` (already shipping), so there is no per-domain
schema to produce, distribute, or maintain. Stakeholders register a
system key and a list of facets in the AOUSD Domains Registry — a
GitHub PR against a Markdown file — and start authoring.

What remains for D is:

1. **An AOUSD Domains Registry.** Same shape as the registry that any
   of A/B/C also needs. The registry recommendation in §6.2 is
   mechanism-independent.
2. **A registry-spec validator.** Implementable in ~20 lines (see
   pseudocode in §6.4). The same validator pattern works against
   either an `apiSchemas` list (D) or `assetInfo` keys (A).
3. **Per-domain identifier-content validators (optional).** A domain
   that wants to validate "is this a valid IFC GlobalId?" still needs
   their own validator, regardless of mechanism. D doesn't help or
   hurt this case.

The codeless companion schema path (§6.7) becomes a fallback for the
rare domain that surfaces classification fields requiring typed
non-token-array structure (numeric tolerances, date ranges, structured
records) which `SemanticsLabelsAPI` cannot represent. Across the four
verticals exercised in §3.4 of COMPARISON.md, no such field has been
identified.
