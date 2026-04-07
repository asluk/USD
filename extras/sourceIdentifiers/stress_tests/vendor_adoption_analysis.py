#!/usr/bin/env python3
"""
Vendor Adoption Analysis for Source Identifier Approaches A and B.

Measures the friction of adding a new vendor's identifier scheme to each
approach, simulating the experience of a standards body or vendor team
integrating with OpenUSD.

Metrics:
1. Files touched per new vendor
2. Boilerplate lines per new vendor
3. Coordination required (can vendors work independently?)
4. Collision risk surface
5. Domain-specific metadata flexibility
6. Promotion lifecycle effort
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
                "If using only the common SourceIdentifierAPI properties "
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
                "that includes SourceIdentifierAPI as a built-in and adds typed "
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


def compare():
    """Generate side-by-side comparison."""
    a = analyze_approach_a()
    b = analyze_approach_b()
    
    dimensions = [
        ("files_touched_by_new_vendor", "Files Touched by New Vendor"),
        ("boilerplate_lines_new_vendor", "Boilerplate for New Vendor"),
        ("coordination_required", "Coordination Required"),
        ("collision_risk", "Collision Risk"),
        ("heterogeneous_metadata", "Heterogeneous Metadata"),
        ("promotion_lifecycle", "Promotion Lifecycle"),
        ("scale_at_20_vendors_5_schemes_each", "Scale (20 vendors × 5 schemes)"),
        ("gui_presentation", "GUI Presentation"),
    ]
    
    comparison = {
        "approach_a": a,
        "approach_b": b,
        "summary": {},
    }
    
    # Scoring (1-5, higher = better for ecosystem adoption)
    scores = {
        "approach_a": {
            "ease_of_initial_adoption": 5,
            "collision_safety": 2,
            "metadata_flexibility": 5,
            "gui_integration": 2,
            "promotion_lifecycle": 3,
            "scale_manageability": 3,
            "discoverability": 2,
            "schema_validation": 1,
        },
        "approach_b": {
            "ease_of_initial_adoption": 4,
            "collision_safety": 4,
            "metadata_flexibility": 3,
            "gui_integration": 5,
            "promotion_lifecycle": 4,
            "scale_manageability": 3,
            "discoverability": 5,
            "schema_validation": 5,
        },
    }
    
    comparison["scores"] = scores
    comparison["scores"]["approach_a_total"] = sum(scores["approach_a"].values())
    comparison["scores"]["approach_b_total"] = sum(scores["approach_b"].values())
    
    return comparison


def main():
    comparison = compare()
    
    output_path = os.path.join(OUTPUT_DIR, "vendor_adoption_analysis.json")
    with open(output_path, "w") as f:
        json.dump(comparison, f, indent=2)
    
    print("=" * 72)
    print("VENDOR ADOPTION ANALYSIS")
    print("=" * 72)
    
    print("\n--- Approach A: assetInfo sub-dictionaries ---")
    a = comparison["approach_a"]
    print(f"  Files to touch: {a['files_touched_by_new_vendor']['count']}")
    print(f"  Collision risk: {a['collision_risk']['level']}")
    print(f"  Metadata flexibility: {a['heterogeneous_metadata']['flexibility']}")
    print(f"  GUI presentation: {a['gui_presentation']['level']}")
    
    print("\n--- Approach B: Multi-apply schema ---")
    b = comparison["approach_b"]
    print(f"  Files to touch: {b['files_touched_by_new_vendor']['count']}")
    print(f"  Collision risk: {b['collision_risk']['level']}")
    print(f"  Metadata flexibility: {b['heterogeneous_metadata']['flexibility']}")
    print(f"  GUI presentation: {b['gui_presentation']['level']}")
    
    print("\n--- Scoring (1-5 per dimension, higher = better) ---")
    for dim in comparison["scores"]["approach_a"]:
        a_score = comparison["scores"]["approach_a"][dim]
        b_score = comparison["scores"]["approach_b"][dim]
        winner = "A" if a_score > b_score else ("B" if b_score > a_score else "=")
        print(f"  {dim:35s}  A={a_score}  B={b_score}  [{winner}]")
    
    print(f"\n  TOTAL: A={comparison['scores']['approach_a_total']}  B={comparison['scores']['approach_b_total']}")
    
    print(f"\nResults saved to {output_path}")


if __name__ == "__main__":
    main()
