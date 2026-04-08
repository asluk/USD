#!/usr/bin/env python3
"""Phase 5: Migration script — move 'scope' from overflow dict to schema property.

After TAC promotes scope to a schema property, existing stages may have scope
values in both places:
  - Old: assetInfo["sourceIds"]["<domain>"]["scope"] (overflow dict)
  - New: sourceIdentifier:<domain>:scope (schema property)

This script demonstrates the migration:
  1. For each prim with SourceIdHybridAPI applied
  2. Check if scope exists in the overflow dict
  3. If schema property is unset, copy overflow value to schema property
  4. Remove scope from overflow dict
  5. Report what changed

In production, this would use the USD Python API (Usd.Stage, UsdSourceIdHybridAPI).
This simulation uses dictionaries for demonstration.

Usage:
    python3 phase5_migration.py
"""

import sys
import copy
import json

# ── Simulated stage: mixed old (overflow) and new (schema) scope values ───

SIMULATED_STAGE = {
    "/BatteryPack_SN42": {
        "apiSchemas": ["SourceIdHybridAPI:dpp"],
        "schema_props": {
            "sourceIdentifier:dpp:primaryId": "urn:idta:dpp:battery:SN42:2025",
            "sourceIdentifier:dpp:domain": "org.idta.dpp",
            "sourceIdentifier:dpp:scope": "",  # Not yet migrated
        },
        "overflow": {
            "dpp": {
                "scope": "instance",  # OLD: still in overflow
                "batteryModel": "LFP-280Ah-48V",
                "chemistry": "LFP",
            },
        },
    },
    "/Chiller_01": {
        "apiSchemas": ["SourceIdHybridAPI:windchill"],
        "schema_props": {
            "sourceIdentifier:windchill:primaryId": "VR:wt.part.WTPart:23639563",
            "sourceIdentifier:windchill:domain": "com.ptc.windchill",
            "sourceIdentifier:windchill:scope": "instance",  # Already migrated
        },
        "overflow": {
            "windchill": {
                # scope already removed from here
                "displayNumber": "CH-7500-A",
                "serialNumber": "SN-2025-04-0042",
            },
        },
    },
    "/UR10e_ModelDef": {
        "apiSchemas": ["SourceIdHybridAPI:ros"],
        "schema_props": {
            "sourceIdentifier:ros:primaryId": "package://ur_description/urdf/ur10e",
            "sourceIdentifier:ros:domain": "org.ros.urdf",
            "sourceIdentifier:ros:scope": "",  # Not yet migrated
        },
        "overflow": {
            "ros": {
                "scope": "type",  # OLD: still in overflow
                "sourceFormat": "URDF",
                "packageName": "ur_description",
            },
        },
    },
    "/Column_C14": {
        "apiSchemas": ["SourceIdHybridAPI:ifc"],
        "schema_props": {
            "sourceIdentifier:ifc:primaryId": "2O2Fr$t4X7Zf8NOew3FNr2",
            "sourceIdentifier:ifc:domain": "org.buildingsmart.ifc",
            "sourceIdentifier:ifc:scope": "",  # Never had scope — leave empty
        },
        "overflow": {
            "ifc": {
                "ifcType": "IfcColumn",
                "objectType": "W14x90",
            },
        },
    },
}


def migrate_scope(stage_data):
    """Migrate scope from overflow dicts to schema properties.

    Returns:
        (migrated_stage, actions) where actions is a list of strings
        describing what changed.
    """
    result = copy.deepcopy(stage_data)
    actions = []

    for prim_path, data in result.items():
        for api in data.get("apiSchemas", []):
            if not api.startswith("SourceIdHybridAPI:"):
                continue
            instance = api.split(":")[1]
            scope_prop = f"sourceIdentifier:{instance}:scope"
            overflow = data.get("overflow", {}).get(instance, {})

            overflow_scope = overflow.get("scope")
            schema_scope = data["schema_props"].get(scope_prop, "")

            if overflow_scope is None:
                # No scope in overflow — nothing to migrate
                actions.append(
                    f"  ⏭️  {prim_path} ({instance}): "
                    f"no scope in overflow — skipped"
                )
                continue

            if schema_scope and schema_scope != "":
                # Schema property already set — just clean up overflow
                del result[prim_path]["overflow"][instance]["scope"]
                actions.append(
                    f"  🧹 {prim_path} ({instance}): "
                    f"schema already has scope='{schema_scope}' — "
                    f"removed duplicate from overflow"
                )
                continue

            # Migrate: copy overflow → schema, remove from overflow
            result[prim_path]["schema_props"][scope_prop] = overflow_scope
            del result[prim_path]["overflow"][instance]["scope"]
            actions.append(
                f"  ✅ {prim_path} ({instance}): "
                f"migrated scope='{overflow_scope}' from overflow to schema"
            )

    return result, actions


def main():
    print("=" * 70)
    print("Scope Migration: overflow dict → schema property")
    print("=" * 70)
    print()

    migrated, actions = migrate_scope(SIMULATED_STAGE)

    print("Actions:")
    for action in actions:
        print(action)
    print()

    # Summary
    migrated_count = sum(1 for a in actions if "migrated" in a)
    cleaned_count = sum(1 for a in actions if "removed duplicate" in a)
    skipped_count = sum(1 for a in actions if "skipped" in a)

    print(f"Summary: {migrated_count} migrated, {cleaned_count} cleaned, "
          f"{skipped_count} skipped")
    print()

    # Show before/after for one prim
    print("Before (BatteryPack_SN42):")
    orig = SIMULATED_STAGE["/BatteryPack_SN42"]
    print(f"  schema scope: '{orig['schema_props']['sourceIdentifier:dpp:scope']}'")
    print(f"  overflow:     {json.dumps(orig['overflow']['dpp'], indent=2, sort_keys=True)}")
    print()
    print("After (BatteryPack_SN42):")
    after = migrated["/BatteryPack_SN42"]
    print(f"  schema scope: '{after['schema_props']['sourceIdentifier:dpp:scope']}'")
    print(f"  overflow:     {json.dumps(after['overflow']['dpp'], indent=2, sort_keys=True)}")
    print()

    print("Migration complete. All scope values now live in schema properties.")
    print("Overflow dicts retain only domain-specific metadata.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
