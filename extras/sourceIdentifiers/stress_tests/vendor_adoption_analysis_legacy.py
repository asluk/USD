#!/usr/bin/env python3
"""
RETRACTED. PRESERVED FOR REGRESSION INSPECTION ONLY.

This file scores Approaches A, B, C, and D along eight dimensions
that Claude (acting as the AI assistant during this PR's development)
invented while the comparison work was in flight. These dimensions
were NOT derived from proposal 105's eight authorized design
principles (separation of concerns, industry agnosticism, vendor
extensibility, composability, discoverability, external queryability,
round-trip fidelity, minimal disruption). They were constructed
post-hoc, during the same window that a leaning toward Approach D
had already taken shape, and they biased toward D along axes D
happens to lead on by construction (per-facet discoverability,
distribution friction with "no new schema = higher" framing).

The principle-derived rebuild is in `vendor_adoption_analysis.py`.

The eight invented dimensions in this file:
  - Initial adoption friction
  - Distribution friction (no new schema = higher)
  - Per-prim discoverability (which systems on this prim)
  - Per-facet discoverability (which facet of which system)
  - Metadata heterogeneity (carries arbitrary domain data)
  - Validator implementability
  - Composition for typical edits (non-timevarying strings)
  - File size cost (smaller = higher)

The two specific issues that the field experiment surfaced against
this scoring (and that the rebuild addresses):

  1. "Metadata heterogeneity" scored D=4 despite D's `token[]`
     label values + identifier strings being unable to carry the
     heterogeneous typed surface (timestamps, numeric measures with
     units, composite typed references, polymorphic XSD-typed AAS
     Property values) that the field census documents in every
     vertical surveyed.
  2. "Distribution friction" was scored unconditionally on the "no
     new schema = higher" framing. Whether and how heavily that
     should weigh is itself a load-bearing call, resolved in the
     rebuild as conditional (currently elevated, trending lighter
     as the AOUSD Build IG epic lands).
"""

import json
import os
import textwrap

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))


def analyze_approach_a():
    """Analyze what a new vendor must do to add identifiers via Approach A."""
    return {
        "name": "Approach A: assetInfo sub-dictionaries",

        "files_touched_by_new_vendor": {
            "count": 0,
            "description": (
                "Zero OpenUSD source files need to be modified. "
                "A vendor simply writes assetInfo['sourceIds']['<domain>'] "
                "in their USD content. No schema registration, no plugin, "
                "no codegen."
            ),
        },

        "boilerplate_lines_new_vendor": {
            "to_start_writing_identifiers": 0,
            "for_convenience_api": "~50 lines Python wrapper (optional)",
            "for_full_cpp_api": "~200 lines C++ schema + wrapper (optional, like UsdMediaAssetPreviewsAPI)",
            "description": (
                "Zero boilerplate to start. Any tool that can write assetInfo "
                "can add source identifiers immediately. A convenience API is "
                "optional and can come later."
            ),
        },

        "coordination_required": {
            "level": "NONE for initial adoption, LOW for conventions",
            "description": (
                "Vendors can ship independently with zero coordination. "
                "Key naming is freeform — no registration required. "
                "Convention (e.g., reverse-DNS keys) is recommended but not enforced. "
                "Coordination becomes needed only when promoting to a standard."
            ),
        },

        "collision_risk": {
            "level": "MEDIUM",
            "description": (
                "Collision happens when two vendors pick the same top-level key in "
                "sourceIds (e.g., both use 'tracker'). Collision is SILENT — "
                "strongest opinion wins per standard assetInfo composition. "
                "No schema system detects or warns about the conflict. "
                "Mitigation: reverse-DNS keys ('com.vendor.tracker'), but "
                "this is convention, not enforcement."
            ),
            "detection": "None (silent overwrite)",
            "mitigation": "Naming convention (reverse-DNS recommended)",
        },

        "heterogeneous_metadata": {
            "flexibility": "FULL",
            "description": (
                "Each domain's sub-dictionary is freeform. Windchill can store "
                "displayNumber, navigationType, organization; IFC can store "
                "ifcType, schema, classification. No common denominator needed. "
                "Domains evolve independently."
            ),
        },

        "promotion_lifecycle": {
            "effort": "MEDIUM — data migration required",
            "steps": [
                "1. Agree on new standard key name",
                "2. Migrate all existing content (rename dictionary key in assetInfo)",
                "3. Update all querying tools to use new key",
                "4. No schema versioning to help track the migration",
            ],
            "description": (
                "Promotion requires renaming dictionary keys in all existing content. "
                "Since keys are strings with no schema backing, there is no versioning "
                "mechanism. Tools must be updated to query the new key. "
                "Migration tooling is straightforward (dictionary key rename) but "
                "must touch every layer that carries the old key."
            ),
        },

        "scale_at_20_vendors_5_schemes_each": {
            "namespace_entries": "100 dictionary keys (20 × 5) per prim",
            "description": (
                "Each vendor adds 5 sub-dictionaries under sourceIds. "
                "100 top-level keys in one dictionary. Dictionary nesting keeps "
                "each vendor's data isolated, but the sourceIds dict becomes large. "
                "Discovery requires iterating all keys — no typed query mechanism."
            ),
            "manageability": "MODERATE — large dicts but contained",
        },

        "gui_presentation": {
            "level": "MANUAL",
            "description": (
                "assetInfo sub-dictionaries do not contribute to UsdPrimDefinition. "
                "GUI tools must explicitly know about the sourceIds convention to "
                "present identifier data. Unauthored identifiers are invisible — "
                "there are no fallback values to display."
            ),
        },
    }


def analyze_approach_b():
    """Analyze what a new vendor must do to add identifiers via Approach B."""
    return {
        "name": "Approach B: Multi-apply schema with typed properties",

        "files_touched_by_new_vendor": {
            "count": "0-1 (with a common base schema already in core)",
            "description": (
                "If using only the common SourceIdSchemaAPI properties "
                "(primaryId, revision, domain, label), zero files — just apply "
                "the schema with a new instance name. If the vendor needs "
                "additional typed properties beyond the common set, they must "
                "register their own schema plugin (1+ files: schema.usda, "
                "plugInfo.json, optional C++/Python wrapper)."
            ),
        },

        "boilerplate_lines_new_vendor": {
            "to_start_writing_identifiers": 0,
            "for_domain_specific_properties": "~100-200 lines (schema.usda + plugInfo.json)",
            "for_full_domain_api": "~400-600 lines (schema + C++ + Python + codegen)",
            "description": (
                "Zero boilerplate to start using the common properties. "
                "Domain-specific extensions require schema authoring and plugin "
                "registration — a familiar but non-trivial process."
            ),
        },

        "coordination_required": {
            "level": "LOW for common properties, MEDIUM for domain extensions",
            "description": (
                "Using common properties (primaryId, revision, domain, label) "
                "requires no coordination — just pick a unique instance name. "
                "Adding domain-specific properties requires either extending "
                "the base schema (requires agreement) or registering a new "
                "companion schema (independent but creates schema sprawl)."
            ),
        },

        "collision_risk": {
            "level": "LOW",
            "description": (
                "Instance name collision (two vendors both using 'tracker') is "
                "DETECTABLE — the apiSchemas list shows all applied schemas, and "
                "schema registration can warn about conflicting definitions. "
                "The 'domain' property provides secondary disambiguation via "
                "reverse-DNS. However, actual data collision is still possible "
                "if two layers both author the same instance's properties."
            ),
            "detection": "Schema registry warnings; apiSchemas list inspection",
            "mitigation": "Instance naming convention + domain attribute",
        },

        "heterogeneous_metadata": {
            "flexibility": "LIMITED by common property set",
            "description": (
                "The base schema provides only primaryId, revision, domain, label. "
                "Domain-specific fields (Windchill's navigationType, IFC's ifcType) "
                "require either: (a) a companion domain-specific schema, (b) custom "
                "attributes alongside schema properties, or (c) encoding metadata "
                "in the primaryId string (lossy). This tension between uniformity "
                "and domain flexibility is the central trade-off."
            ),
            "workaround": (
                "A domain-specific companion schema (e.g., WindchillIdentifierAPI) "
                "that includes SourceIdSchemaAPI as a built-in and adds typed "
                "properties for domain-specific metadata."
            ),
        },

        "promotion_lifecycle": {
            "effort": "LOW-MEDIUM — domain attribute migration",
            "steps": [
                "1. Agree on new standard instance name (or keep existing)",
                "2. Migrate domain attribute value (e.g., 'com.nvidia.simready' → 'org.aousd.simready')",
                "3. Optionally register new schema instance under standard name",
                "4. Schema versioning tracks the migration",
                "5. Old instance can be deprecated with clear successor path",
            ],
            "description": (
                "Promotion can be as simple as updating the domain token value, "
                "since tools can query by domain rather than instance name. "
                "Schema versioning provides a mechanism for tracking the migration. "
                "If the instance name also changes, content migration is needed "
                "but the schema system makes the change explicit and trackable."
            ),
        },

        "scale_at_20_vendors_5_schemes_each": {
            "namespace_entries": "400 properties (20 × 5 × 4 props each) + 100 apiSchemas entries",
            "description": (
                "Each vendor instance adds 4 properties (primaryId, revision, domain, "
                "label). 100 instances × 4 = 400 property names in the prim's property "
                "namespace, plus 100 entries in the apiSchemas list. "
                "Properties are individually addressable and typed, but the "
                "property namespace becomes crowded."
            ),
            "manageability": "MODERATE — more entries but typed and queryable",
        },

        "gui_presentation": {
            "level": "AUTOMATIC",
            "description": (
                "Applied schemas contribute to UsdPrimDefinition. Properties "
                "appear in GUI property panels automatically. Fallback values "
                "(empty strings) mean unauthored properties are still visible "
                "and editable. Schema-aware tools can present source identifiers "
                "without any custom knowledge of the convention."
            ),
        },
    }


def analyze_approach_c():
    """Approach C — Hybrid (B's typed schema + A's assetInfo overflow)."""
    return {
        "name": "Approach C: Hybrid (multi-apply schema + assetInfo overflow)",
        "structure": (
            "Multi-apply SourceIdHybridAPI:<system> with the four common "
            "fields (primaryId, revision, domain, label), plus "
            "assetInfo['sourceIds'][<system>] for domain-specific metadata."
        ),
        "what_a_new_vendor_does": (
            "Apply the schema instance, author the four typed properties, "
            "and add any domain-specific metadata to the assetInfo overflow "
            "dict under the matching system key."
        ),
        "distribution_dependency": (
            "Requires SourceIdHybridAPI to ship — a new ratified multi-apply "
            "schema in OpenUSD or as a distributed plugin."
        ),
        "discoverability": (
            "apiSchemas list shows which systems are on the prim. To know "
            "which domain-specific fields are present, consumers parse the "
            "assetInfo overflow dict — same as A for that tier."
        ),
    }


def analyze_approach_d():
    """Approach D — Labels + Identity (the recommended mechanism)."""
    return {
        "name": "Approach D: Labels + Identity (SemanticsLabelsAPI + assetInfo)",
        "structure": (
            "Identity -> assetInfo['source'][<system>] with `identifier` and "
            "optional `version` keys. Classification -> "
            "SemanticsLabelsAPI:<system>:<facet> instances with token[] "
            "semantics:labels:<system>:<facet> properties."
        ),
        "what_a_new_vendor_does": (
            "Author assetInfo['source'][<system>] with the identifier string. "
            "Apply SemanticsLabelsAPI:<system>:<facet> for each classification "
            "facet and author the corresponding token[] property. No new "
            "applied schema required — UsdSemanticsLabelsAPI ships in 24.11."
        ),
        "distribution_dependency": (
            "None. UsdSemanticsLabelsAPI is already in OpenUSD core (24.11+). "
            "An AOUSD Domains Registry is recommended for namespace "
            "coordination but is administrative, not enforcement."
        ),
        "discoverability": (
            "Per-facet apiSchemas instances expose both the system and the "
            "facet — finer-grained than B/C's per-system instances. A consumer "
            "asking 'what facets does Revit carry on this prim?' can answer "
            "from the apiSchemas list alone, without parsing properties or "
            "dictionaries."
        ),
    }


def compare():
    """Generate side-by-side comparison across A, B, C, D."""
    a = analyze_approach_a()
    b = analyze_approach_b()
    c = analyze_approach_c()
    d = analyze_approach_d()

    comparison = {
        "approach_a": a,
        "approach_b": b,
        "approach_c": c,
        "approach_d": d,
        "summary": {},
    }

    # Scoring (1-5, higher = better for ecosystem adoption).
    # Dimensions match COMPARISON.md §3.6.
    # Honest scoring: collision detection / governance enforcement / composition
    # for non-timevarying strings are treated as symmetric across mechanisms
    # (the differences are in what a registry-spec validator must parse).
    scores = {
        "approach_a": {
            "initial_adoption_friction":     5,  # zero coordination, just write dict
            "distribution_friction":         5,  # no new schema needed
            "per_prim_discoverability":      2,  # must parse assetInfo
            "per_facet_discoverability":     2,  # must parse assetInfo
            "metadata_heterogeneity":        5,  # freeform dicts handle anything
            "validator_implementability":    2,  # full traversal + dict parsing
            "composition_typical_edits":     4,  # equivalent for non-timevarying
            "file_size_cost":                4,  # 109.4 MB / 100K prims
        },
        "approach_b": {
            "initial_adoption_friction":     4,  # apply schema instance
            "distribution_friction":         2,  # new SourceIdSchemaAPI to ship
            "per_prim_discoverability":      4,  # apiSchemas list (per-system)
            "per_facet_discoverability":     2,  # no facet structure
            "metadata_heterogeneity":        2,  # 4 fixed properties; companion schemas needed
            "validator_implementability":    4,  # GetAll() + typed access
            "composition_typical_edits":     4,  # equivalent for non-timevarying
            "file_size_cost":                5,  # 93.1 MB — smallest
        },
        "approach_c": {
            "initial_adoption_friction":     4,  # apply schema + author overflow
            "distribution_friction":         2,  # new SourceIdHybridAPI to ship
            "per_prim_discoverability":      4,  # apiSchemas list (per-system)
            "per_facet_discoverability":     3,  # apiSchemas + overflow walk
            "metadata_heterogeneity":        5,  # overflow dicts handle anything
            "validator_implementability":    4,  # schema-targeted + overflow check
            "composition_typical_edits":     4,  # equivalent for non-timevarying
            "file_size_cost":                3,  # 147.1 MB — largest
        },
        "approach_d": {
            "initial_adoption_friction":     4,  # apply per-facet schemas + author labels
            "distribution_friction":         5,  # no new schema; uses shipping SemanticsLabelsAPI
            "per_prim_discoverability":      5,  # apiSchemas list shows facets per system
            "per_facet_discoverability":     5,  # per-facet instances expose structure
            "metadata_heterogeneity":        4,  # token labels + assetInfo strings
            "validator_implementability":    5,  # apiSchemas list shows system+facet directly
            "composition_typical_edits":     4,  # equivalent for non-timevarying
            "file_size_cost":                4,  # 115.8 MB — between A and C
        },
    }

    comparison["scores"] = scores
    for key in ("approach_a", "approach_b", "approach_c", "approach_d"):
        comparison["scores"][f"{key}_total"] = sum(scores[key].values())

    return comparison


def main():
    comparison = compare()

    output_path = os.path.join(OUTPUT_DIR, "vendor_adoption_analysis.json")
    with open(output_path, "w") as f:
        json.dump(comparison, f, indent=2)

    print("=" * 72)
    print("VENDOR ADOPTION ANALYSIS (A/B/C/D)")
    print("=" * 72)

    print("\n--- Approach A: assetInfo sub-dictionaries ---")
    a = comparison["approach_a"]
    print(f"  Files to touch: {a['files_touched_by_new_vendor']['count']}")
    print(f"  Metadata flexibility: {a['heterogeneous_metadata']['flexibility']}")

    print("\n--- Approach B: Multi-apply schema ---")
    b = comparison["approach_b"]
    print(f"  Files to touch: {b['files_touched_by_new_vendor']['count']}")
    print(f"  Metadata flexibility: {b['heterogeneous_metadata']['flexibility']}")

    print("\n--- Approach C: Hybrid (B + assetInfo overflow) ---")
    c = comparison["approach_c"]
    print(f"  {c['structure']}")
    print(f"  Distribution dependency: {c['distribution_dependency']}")

    print("\n--- Approach D: Labels + Identity ---")
    d = comparison["approach_d"]
    print(f"  {d['structure']}")
    print(f"  Distribution dependency: {d['distribution_dependency']}")

    print("\n--- Scoring (1-5 per dimension, higher = better) ---")
    dims = list(comparison["scores"]["approach_a"].keys())
    header = f"  {'dimension':35s}  A   B   C   D"
    print(header)
    print(f"  {'-'*35}  --  --  --  --")
    for dim in dims:
        a_score = comparison["scores"]["approach_a"][dim]
        b_score = comparison["scores"]["approach_b"][dim]
        c_score = comparison["scores"]["approach_c"][dim]
        d_score = comparison["scores"]["approach_d"][dim]
        print(f"  {dim:35s}  {a_score}   {b_score}   {c_score}   {d_score}")

    totals = comparison["scores"]
    print(f"\n  {'TOTAL':35s}  {totals['approach_a_total']}  {totals['approach_b_total']}  "
          f"{totals['approach_c_total']}  {totals['approach_d_total']}")
    print(f"\nResults saved to {output_path}")


if __name__ == "__main__":
    main()
