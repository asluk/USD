#!/usr/bin/env python3
"""Phase 3: Registry-spec validator for 'scope' in overflow dictionaries.

This validator reads assetInfo["sourceIds"] overflow dictionaries and checks
the 'scope' field against the registry-spec definition:
  - Allowed values: "type", "instance"
  - If present, must be a string
  - Warns on unknown values (forward-compatible; new values may be added)

This demonstrates the intermediate validation step: scope is still in the
overflow dict (not a schema property), but the registry-spec allows CI
pipelines to enforce correctness.

Usage:
    python3 phase3_validator.py phase2_cross_domain.usda
"""

import sys
import json

# ── Registry spec (normally loaded from AOUSD Domains Registry) ───────────

SCOPE_REGISTRY_SPEC = {
    "field": "scope",
    "type": "string",
    "required": False,
    "allowed_values": ["type", "instance"],
    "doc": "Classifies identifier as type-level (product family, model "
           "definition) or instance-level (serial number, deployed unit). "
           "Adopted by AAS/DPP, PTC Windchill, ROS/URDF communities.",
    "version": "1.0",
    "adopted_by": [
        "org.idta.dpp",
        "com.ptc.windchill",
        "org.ros.urdf",
    ],
}

# ── Simulated stage data (from phase2_cross_domain.usda) ─────────────────
# In production, this would use the USD Python API:
#   from pxr import Usd
#   stage = Usd.Stage.Open(filepath)
#   for prim in stage.Traverse():
#       source_ids = prim.GetAssetInfoByKey("sourceIds")

SIMULATED_STAGE = {
    "/BatteryPack_SN42": {
        "domain": "org.idta.dpp",
        "overflow": {"scope": "instance", "batteryModel": "LFP-280Ah-48V"},
    },
    "/Chiller_Series7500": {
        "domain": "com.ptc.windchill",
        "overflow": {"scope": "type", "displayNumber": "CH-7500"},
    },
    "/Chiller_01": {
        "domain": "com.ptc.windchill",
        "overflow": {"scope": "instance", "displayNumber": "CH-7500-A"},
    },
    "/UR10e_ModelDef": {
        "domain": "org.ros.urdf",
        "overflow": {"scope": "type", "sourceFormat": "URDF"},
    },
    "/UR10e_Cell3_Unit7": {
        "domain": "org.ros.urdf",
        "overflow": {"scope": "instance", "frameId": "cell3_ur10e_7_base_link"},
    },
    # ── Deliberately broken entries for validation demo ──
    "/BadPrim_Typo": {
        "domain": "org.idta.dpp",
        "overflow": {"scope": "instnace"},  # Typo!
    },
    "/BadPrim_WrongType": {
        "domain": "com.ptc.windchill",
        "overflow": {"scope": 42},  # Wrong type!
    },
    "/Column_C14": {
        "domain": "org.buildingsmart.ifc",
        "overflow": {"ifcType": "IfcColumn"},  # No scope — that's fine
    },
}


def validate_scope(stage_data, spec):
    """Validate 'scope' field in overflow dicts against registry-spec.

    Returns:
        list of (prim_path, severity, message) tuples
    """
    results = []

    for prim_path, data in stage_data.items():
        overflow = data.get("overflow", {})
        domain = data.get("domain", "unknown")
        scope_value = overflow.get(spec["field"])

        # No scope field: OK (it's optional)
        if scope_value is None:
            continue

        # Type check
        if not isinstance(scope_value, str):
            results.append((
                prim_path, "ERROR",
                f"'{spec['field']}' in domain '{domain}' must be a string, "
                f"got {type(scope_value).__name__}: {scope_value!r}"
            ))
            continue

        # Value check
        if scope_value not in spec["allowed_values"]:
            results.append((
                prim_path, "WARNING",
                f"'{spec['field']}' in domain '{domain}' has unrecognized "
                f"value '{scope_value}' (allowed: {spec['allowed_values']}). "
                f"This may be a typo or a forward-compatible extension."
            ))
        else:
            results.append((
                prim_path, "OK",
                f"'{spec['field']}' = '{scope_value}' in domain '{domain}'"
            ))

    return results


def main():
    print("=" * 70)
    print("AOUSD Source Identifier Validator — scope field (registry-spec v1.0)")
    print("=" * 70)
    print()
    print(f"Spec: {SCOPE_REGISTRY_SPEC['doc']}")
    print(f"Allowed values: {SCOPE_REGISTRY_SPEC['allowed_values']}")
    print(f"Adopted by: {', '.join(SCOPE_REGISTRY_SPEC['adopted_by'])}")
    print()

    results = validate_scope(SIMULATED_STAGE, SCOPE_REGISTRY_SPEC)

    errors = 0
    warnings = 0
    passed = 0

    for prim_path, severity, message in results:
        icon = {"OK": "✅", "WARNING": "⚠️ ", "ERROR": "❌"}[severity]
        print(f"  {icon} {prim_path}: {message}")
        if severity == "ERROR":
            errors += 1
        elif severity == "WARNING":
            warnings += 1
        else:
            passed += 1

    print()
    print(f"Results: {passed} passed, {warnings} warnings, {errors} errors")
    print()

    if errors > 0:
        print("VALIDATION FAILED — fix errors before merging.")
        return 1
    elif warnings > 0:
        print("VALIDATION PASSED with warnings — review before merging.")
        return 0
    else:
        print("VALIDATION PASSED.")
        return 0


if __name__ == "__main__":
    sys.exit(main())
