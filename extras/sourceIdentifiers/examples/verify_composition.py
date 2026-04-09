#!/usr/bin/env python3
"""
Verify composition expectations for source identifier approaches.

This script performs structural verification on the .usda example files
to confirm that the composition scenarios described in COMPARISON.md
are correctly expressed. It parses .usda text directly and does NOT
require a built OpenUSD environment.

For full USD API verification (actual composed values via UsdStage),
a built OpenUSD environment is required. This script verifies that:
1. Override layers reference their base layers correctly
2. Override layers author only the fields they intend to change
3. New domain additions are structurally correct
4. Schema instance declarations are present where expected

Run: python3 verify_composition.py
"""

import os
import re
import sys

EXAMPLES_DIR = os.path.dirname(os.path.abspath(__file__))
PASS = 0
FAIL = 0


def check(condition, description):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  PASS: {description}")
    else:
        FAIL += 1
        print(f"  FAIL: {description}")


def read_file(filename):
    path = os.path.join(EXAMPLES_DIR, filename)
    if not os.path.exists(path):
        print(f"  SKIP: {filename} not found")
        return None
    with open(path) as f:
        return f.read()


def verify_approach_a_composition():
    """Verify Approach A override layer structure."""
    print("\n--- Approach A: Composition ---")

    base = read_file("composition_test_a_base.usda")
    override = read_file("composition_test_a_override.usda")
    if not base or not override:
        return

    # Base should have windchill, sap, ifc domains
    check("dictionary windchill" in base, "Base has windchill domain")
    check("dictionary sap" in base, "Base has sap domain")
    check("dictionary ifc" in base, "Base has ifc domain")
    check('string revision = "Rev.B"' in base, "Base windchill revision is Rev.B")

    # Override should reference base
    check("references = @./composition_test_a_base.usda@" in override,
          "Override references base layer")

    # Override should update windchill revision
    check('string revision = "Rev.C"' in override,
          "Override updates windchill revision to Rev.C")

    # Override should NOT re-author windchill primaryId (would shadow base)
    override_windchill = override[override.find("dictionary windchill"):
                                   override.find("dictionary opcua")]
    check("primaryId" not in override_windchill,
          "Override does NOT re-author windchill primaryId (avoids shadow)")

    # Override should add opcua domain
    check("dictionary opcua" in override, "Override adds opcua domain")

    # Override should NOT mention sap or ifc (untouched domains)
    check("dictionary sap" not in override, "Override does not touch sap domain")
    check("dictionary ifc" not in override, "Override does not touch ifc domain")


def verify_approach_b_composition():
    """Verify Approach B override layer structure."""
    print("\n--- Approach B: Composition ---")

    base = read_file("composition_test_b_base.usda")
    override = read_file("composition_test_b_override.usda")
    if not base or not override:
        return

    # Base should have three schema instances
    check("SourceIdSchemaAPI:windchill" in base, "Base has windchill schema")
    check("SourceIdSchemaAPI:sap" in base, "Base has sap schema")
    check("SourceIdSchemaAPI:ifc" in base, "Base has ifc schema")
    check('sourceIdentifier:windchill:revision = "Rev.B"' in base,
          "Base windchill revision is Rev.B")

    # Override should reference base
    check("references = @./composition_test_b_base.usda@" in override,
          "Override references base layer")

    # Override should update ONLY windchill revision
    check('sourceIdentifier:windchill:revision = "Rev.C"' in override,
          "Override updates windchill revision to Rev.C")

    # Override should NOT re-author windchill primaryId (check for property
    # assignment, not docstring mentions)
    check('sourceIdentifier:windchill:primaryId =' not in override,
          "Override does NOT re-author windchill primaryId (per-property safe)")

    # Override should NOT re-author windchill domain or label
    check('sourceIdentifier:windchill:domain =' not in override,
          "Override does NOT re-author windchill domain")
    check('sourceIdentifier:windchill:label =' not in override,
          "Override does NOT re-author windchill label")

    # Override should add opcua via prepend apiSchemas
    check('prepend apiSchemas = ["SourceIdSchemaAPI:opcua"]' in override,
          "Override adds opcua via prepend apiSchemas")

    # Override should author opcua properties
    check("sourceIdentifier:opcua:primaryId" in override,
          "Override authors opcua primaryId")
    check("sourceIdentifier:opcua:domain" in override,
          "Override authors opcua domain")

    # Override should NOT mention sap or ifc properties
    check("sourceIdentifier:sap:" not in override,
          "Override does not touch sap properties")
    check("sourceIdentifier:ifc:" not in override,
          "Override does not touch ifc properties")


def verify_approach_c_composition():
    """Verify Approach C override layer structure (if files exist)."""
    print("\n--- Approach C: Composition ---")

    base = read_file("composition_test_c_base.usda")
    override = read_file("composition_test_c_override.usda")
    if not base or not override:
        return

    # Base should have schema instances AND assetInfo overflow
    check("SourceIdHybridAPI:windchill" in base or
          "SourceIdSchemaAPI:windchill" in base,
          "Base has windchill schema instance")
    check("dictionary sourceIds" in base, "Base has assetInfo sourceIds dict")

    # Override should reference base
    check("composition_test_c_base.usda" in override,
          "Override references base layer")


def verify_industry_examples():
    """Verify industry example files are structurally valid."""
    print("\n--- Industry Examples: Structural Checks ---")

    pairs = [
        ("approach_a_assetinfo.usda", "approach_b_schema.usda", "AECO"),
        ("manufacturing_a.usda", "manufacturing_b.usda", "Manufacturing"),
        ("robotics_a.usda", "robotics_b.usda", "Robotics"),
    ]

    for a_file, b_file, label in pairs:
        a = read_file(a_file)
        b = read_file(b_file)
        if not a or not b:
            continue

        # Both should have the same defaultPrim
        a_default = re.search(r'defaultPrim = "(\w+)"', a)
        b_default = re.search(r'defaultPrim = "(\w+)"', b)
        if a_default and b_default:
            check(a_default.group(1) == b_default.group(1),
                  f"{label}: A and B have same defaultPrim")

        # B should use apiSchemas
        check("apiSchemas" in b, f"{label}: B uses apiSchemas declarations")

        # A should use assetInfo sourceIds
        check("dictionary sourceIds" in a, f"{label}: A uses assetInfo sourceIds")


def main():
    print("Source Identifier Composition Verification")
    print("=" * 50)
    print(f"Examples directory: {EXAMPLES_DIR}")
    print("\nNote: This verifies .usda structure, not USD-composed values.")
    print("Full API verification requires a built OpenUSD environment.")

    verify_approach_a_composition()
    verify_approach_b_composition()
    verify_approach_c_composition()
    verify_industry_examples()

    print(f"\n{'=' * 50}")
    print(f"Results: {PASS} passed, {FAIL} failed")
    if FAIL > 0:
        print("VERIFICATION FAILED")
        sys.exit(1)
    else:
        print("ALL CHECKS PASSED")
        sys.exit(0)


if __name__ == "__main__":
    main()
