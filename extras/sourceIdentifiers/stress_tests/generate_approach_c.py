#!/usr/bin/env python3
"""
Generate a 100K-prim stage using Approach C (hybrid) and compare
file size / verbosity against the existing A and B results.
"""

import os
import sys
import time
import json
import random

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
NUM_PRIMS = 100_000

DOMAINS = [
    {"key": "windchill", "domain": "com.ptc.windchill", "label": "Windchill Part OID",
     "id_prefix": "VR:wt.part.WTPart:", "has_revision": True,
     "metadata_keys": ["displayNumber", "navigationType"]},
    {"key": "ifc", "domain": "org.buildingsmart.ifc", "label": "IFC GlobalId",
     "id_prefix": "", "id_gen": "ifc_guid", "has_revision": False,
     "metadata_keys": ["ifcType", "schema"]},
    {"key": "revit", "domain": "com.autodesk.revit", "label": "Revit ElementId",
     "id_prefix": "", "id_gen": "numeric", "has_revision": True,
     "metadata_keys": ["category", "familyType"]},
    {"key": "nvidia", "domain": "com.nvidia.omniverse", "label": "Omniverse Nucleus Asset",
     "id_prefix": "omni://nucleus.nvidia.com/assets/", "has_revision": True,
     "metadata_keys": ["checkpoint", "creator"]},
    {"key": "sap", "domain": "com.sap.s4hana", "label": "SAP Material Number",
     "id_prefix": "0000000000", "has_revision": True,
     "metadata_keys": ["materialType", "plant"]},
    {"key": "adobe", "domain": "com.adobe.substance3d", "label": "Substance 3D Asset ID",
     "id_prefix": "adb:sub3d:asset:", "has_revision": True,
     "metadata_keys": ["collection"]},
    {"key": "step", "domain": "org.iso.step", "label": "STEP Entity ID",
     "id_prefix": "STEP-FILE-ID:#", "has_revision": True,
     "metadata_keys": ["entityType", "standard"]},
    {"key": "opcua", "domain": "org.opcfoundation.ua", "label": "OPC UA NodeId",
     "id_prefix": "ns=4;s=Plant.", "has_revision": False,
     "metadata_keys": ["nodeClass", "browseName"]},
]

import string
IFC_CHARS = string.digits + string.ascii_uppercase + string.ascii_lowercase + "_$"

def gen_ifc_guid():
    return "".join(random.choice(IFC_CHARS) for _ in range(22))

def gen_numeric_id():
    return str(random.randint(100000, 9999999))

def gen_revision():
    return random.choice(["Rev.A", "Rev.B", "Rev.C", "v1.0", "v2.1", "v3.0", "01", "02"])

def gen_primary_id(d, i):
    if d.get("id_gen") == "ifc_guid":
        return gen_ifc_guid()
    elif d.get("id_gen") == "numeric":
        return gen_numeric_id()
    return f"{d['id_prefix']}{i:08d}"

def gen_meta_value(key):
    vals = {
        "displayNumber": f"PART-{random.randint(1000,9999)}",
        "navigationType": f"OR:wt.filter.NavigationCriteria:{random.randint(1000000,9999999)}",
        "ifcType": random.choice(["IfcColumn", "IfcBeam", "IfcSlab", "IfcWall"]),
        "schema": "IFC4x3",
        "category": random.choice(["Structural Columns", "Walls", "Floors"]),
        "familyType": random.choice(["W14x90", "W12x65", "HSS8x8x1/2"]),
        "checkpoint": f"cp_{random.randint(20260101,20261231)}",
        "creator": random.choice(["NVIDIA SimReady", "Auto-gen"]),
        "materialType": random.choice(["HAWA", "FERT", "HALB"]),
        "plant": random.choice(["NYC1", "SFO2", "AUS3"]),
        "collection": random.choice(["Aerospace", "Automotive"]),
        "entityType": random.choice(["PRODUCT_DEFINITION", "SHAPE_REPRESENTATION"]),
        "standard": "ISO 10303-242:2022",
        "nodeClass": random.choice(["Object", "Variable"]),
        "browseName": f"Node_{random.randint(1,10000)}",
    }
    return vals.get(key, f"value_{random.randint(1,1000)}")


def generate_approach_c(num_prims, output_path):
    start_time = time.time()

    with open(output_path, "w") as f:
        f.write('#usda 1.0\n(\n')
        f.write(f'    """Approach C (hybrid) stress test: {num_prims:,} prims."""\n')
        f.write('    defaultPrim = "Root"\n    metersPerUnit = 1.0\n)\n\n')
        f.write('def Xform "Root" (\n    kind = "assembly"\n)\n{\n')

        for i in range(num_prims):
            num_ids = random.randint(1, 5)
            selected = random.sample(DOMAINS, min(num_ids, len(DOMAINS)))
            prim_name = f"Prim_{i:06d}"

            # apiSchemas list
            schemas = [f'"SourceIdentifierAPI:{d["key"]}"' for d in selected]
            schemas_str = ",\n            ".join(schemas)

            # assetInfo metadata
            f.write(f'    def Xform "{prim_name}" (\n')
            f.write(f'        prepend apiSchemas = [\n            {schemas_str}\n        ]\n')

            # Only write assetInfo if there's metadata
            has_metadata = any(d["metadata_keys"] for d in selected)
            if has_metadata:
                f.write(f'        assetInfo = {{\n')
                f.write(f'            dictionary sourceIds = {{\n')
                for d in selected:
                    if d["metadata_keys"]:
                        f.write(f'                dictionary {d["key"]} = {{\n')
                        for mk in d["metadata_keys"][:2]:
                            f.write(f'                    string {mk} = "{gen_meta_value(mk)}"\n')
                        f.write(f'                }}\n')
                f.write(f'            }}\n')
                f.write(f'        }}\n')

            f.write(f'    )\n    {{\n')

            # Schema properties
            for d in selected:
                key = d["key"]
                pid = gen_primary_id(d, i)
                f.write(f'        string sourceIdentifier:{key}:primaryId = "{pid}"\n')
                if d["has_revision"]:
                    f.write(f'        string sourceIdentifier:{key}:revision = "{gen_revision()}"\n')
                f.write(f'        token sourceIdentifier:{key}:domain = "{d["domain"]}"\n')
                f.write(f'        string sourceIdentifier:{key}:label = "{d["label"]}"\n')

            f.write(f'    }}\n')

        f.write('}\n')

    elapsed = time.time() - start_time
    file_size = os.path.getsize(output_path)
    return elapsed, file_size


def main():
    random.seed(42)

    print(f"Generating Approach C (hybrid) stage ({NUM_PRIMS:,} prims)...")
    c_path = os.path.join(OUTPUT_DIR, "stress_approach_c.usda")
    c_time, c_size = generate_approach_c(NUM_PRIMS, c_path)
    c_lines = sum(1 for _ in open(c_path))

    print(f"  Generated in {c_time:.2f}s, {c_size/1024/1024:.1f} MB, {c_lines:,} lines")

    # Load existing A and B results for comparison
    results_path = os.path.join(OUTPUT_DIR, "stress_test_results.json")
    with open(results_path) as f:
        existing = json.load(f)

    a_size = existing["approach_a"]["file_size_bytes"]
    a_lines = existing["line_count"]["approach_a"]
    b_size = existing["approach_b"]["file_size_bytes"]
    b_lines = existing["line_count"]["approach_b"]

    print(f"\n--- Three-way File Size Comparison ---")
    print(f"Approach A: {a_size/1024/1024:.2f} MB")
    print(f"Approach B: {b_size/1024/1024:.2f} MB")
    print(f"Approach C: {c_size/1024/1024:.2f} MB")

    print(f"\n--- Three-way Line Count Comparison ---")
    print(f"Approach A: {a_lines:,} lines")
    print(f"Approach B: {b_lines:,} lines")
    print(f"Approach C: {c_lines:,} lines")

    # Count unique names
    c_keys = set()
    c_props = set()
    with open(c_path) as fp:
        for line in fp:
            s = line.strip()
            if s.startswith("dictionary ") and "= {" in s:
                c_keys.add(s.split()[1])
            if s.startswith("string sourceIdentifier:") or s.startswith("token sourceIdentifier:"):
                prop = s.split("=")[0].strip().split()[-1]
                c_props.add(prop)

    print(f"\n--- Namespace Footprint ---")
    print(f"Approach A: {existing['namespace_footprint']['approach_a_unique_keys']} dict keys")
    print(f"Approach B: {existing['namespace_footprint']['approach_b_unique_properties']} property names")
    print(f"Approach C: {len(c_props)} property names + {len(c_keys)} dict keys")

    # Save combined results
    existing["approach_c"] = {
        "generation_time_sec": round(c_time, 3),
        "file_size_bytes": c_size,
        "file_size_mb": round(c_size / 1024 / 1024, 2),
        "num_prims": NUM_PRIMS,
    }
    existing["line_count"]["approach_c"] = c_lines
    existing["namespace_footprint"]["approach_c_unique_properties"] = len(c_props)
    existing["namespace_footprint"]["approach_c_unique_dict_keys"] = len(c_keys)

    with open(results_path, "w") as f:
        json.dump(existing, f, indent=2)
    print(f"\nResults saved to {results_path}")

    # Clean up large file
    os.remove(c_path)
    print(f"Removed {c_path} (gitignored)")


if __name__ == "__main__":
    main()
