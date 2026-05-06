#!/usr/bin/env python3
"""
Generate a 100K-prim stage using Approach D (Labels + Identity) and compare
file size / verbosity against the existing A, B, and C results.

Approach D splits the problem into two axes:
  - identity      → assetInfo["source"][<system>] = { identifier, [version] }
  - classification → SemanticsLabelsAPI:<system>:<facet> + token[] semantics:labels:...

The DOMAINS table classifies each domain's metadata into "label_facets"
(controlled-vocabulary terms that ride SemanticsLabelsAPI) and "id_extras"
(identity-adjacent strings that stay in assetInfo with the identifier).
"""

import os
import sys
import time
import json
import random
import string

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
NUM_PRIMS = 100_000

# Same eight domains as A/B/C, with metadata split into labels vs. id-extras.
# label_facets → SemanticsLabelsAPI instances + token[] properties.
# id_extras    → string keys alongside `identifier` in assetInfo["source"][system].
DOMAINS = [
    {"key": "windchill", "domain": "com.ptc.windchill", "label": "Windchill Part OID",
     "id_prefix": "VR:wt.part.WTPart:", "has_revision": True,
     "label_facets": [], "id_extras": ["displayNumber", "navigationType"]},
    {"key": "ifc", "domain": "org.buildingsmart.ifc", "label": "IFC GlobalId",
     "id_prefix": "ASHRAE205:", "id_gen": "ifc_guid", "has_revision": False,
     "label_facets": ["type", "schema"], "id_extras": []},
    {"key": "revit", "domain": "com.autodesk.revit", "label": "Revit ElementId",
     "id_prefix": "ASHRAE205:", "id_gen": "numeric", "has_revision": True,
     "label_facets": ["category", "familyType"], "id_extras": []},
    {"key": "nvidia", "domain": "com.nvidia.omniverse", "label": "Omniverse Nucleus Asset",
     "id_prefix": "omniverse://nucleus.nvidia.com/assets/", "has_revision": True,
     "label_facets": ["creator"], "id_extras": ["checkpoint"]},
    {"key": "sap", "domain": "com.sap.s4hana", "label": "SAP Material Number",
     "id_prefix": "0000000000", "has_revision": True,
     "label_facets": ["materialType", "plant"], "id_extras": []},
    {"key": "adobe", "domain": "com.adobe.substance3d", "label": "Substance 3D Asset ID",
     "id_prefix": "urn:adobe:sub3d:", "has_revision": True,
     "label_facets": ["collection"], "id_extras": []},
    {"key": "step", "domain": "org.iso.step", "label": "STEP Entity ID",
     "id_prefix": "STEP-FILE-ID:#", "has_revision": True,
     "label_facets": ["entityType", "standard"], "id_extras": []},
    {"key": "opcua", "domain": "org.opcfoundation.ua", "label": "OPC UA NodeId",
     "id_prefix": "ns=4;s=Plant.", "has_revision": False,
     "label_facets": ["nodeClass"], "id_extras": ["browseName"]},
]

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

def gen_facet_value(facet):
    vals = {
        "type": random.choice(["IfcColumn", "IfcBeam", "IfcSlab", "IfcWall"]),
        "schema": random.choice(["IFC4x3", "IFC4", "IFC2x3"]),
        "category": random.choice(["Structural Columns", "Walls", "Floors"]),
        "familyType": random.choice(["W14x90", "W12x65", "HSS8x8x1/2"]),
        "creator": random.choice(["NVIDIA SimReady", "Auto-gen"]),
        "materialType": random.choice(["HAWA", "FERT", "HALB"]),
        "plant": random.choice(["NYC1", "SFO2", "AUS3"]),
        "collection": random.choice(["Aerospace", "Automotive"]),
        "entityType": random.choice(["PRODUCT_DEFINITION", "SHAPE_REPRESENTATION"]),
        "standard": "ISO 10303-242:2022",
        "nodeClass": random.choice(["Object", "Variable"]),
    }
    return vals.get(facet, f"value_{random.randint(1,1000)}")

def gen_id_extra_value(key):
    vals = {
        "displayNumber": f"PART-{random.randint(1000,9999)}",
        "navigationType": f"OR:wt.filter.NavigationCriteria:{random.randint(1000000,9999999)}",
        "checkpoint": f"cp_{random.randint(20260101,20261231)}",
        "browseName": f"Node_{random.randint(1,10000)}",
    }
    return vals.get(key, f"value_{random.randint(1,1000)}")


def generate_approach_d(num_prims, output_path):
    start_time = time.time()

    with open(output_path, "w") as f:
        f.write('#usda 1.0\n(\n')
        f.write(f'    """Approach D (Labels + Identity) stress test: {num_prims:,} prims."""\n')
        f.write('    defaultPrim = "Root"\n    metersPerUnit = 1.0\n)\n\n')
        f.write('def Xform "Root" (\n    kind = "assembly"\n)\n{\n')

        for i in range(num_prims):
            num_ids = random.randint(1, 5)
            selected = random.sample(DOMAINS, min(num_ids, len(DOMAINS)))
            prim_name = f"Prim_{i:06d}"

            # apiSchemas: one SemanticsLabelsAPI:<system>:<facet> per label facet
            schemas = []
            for d in selected:
                for facet in d["label_facets"]:
                    schemas.append(f'"SemanticsLabelsAPI:{d["key"]}:{facet}"')

            f.write(f'    def Xform "{prim_name}" (\n')
            if schemas:
                schemas_str = ",\n            ".join(schemas)
                f.write(f'        prepend apiSchemas = [\n            {schemas_str}\n        ]\n')

            # assetInfo["source"][<system>] = identity strings (identifier + extras)
            f.write(f'        assetInfo = {{\n')
            f.write(f'            dictionary source = {{\n')
            for d in selected:
                key = d["key"]
                pid = gen_primary_id(d, i)
                f.write(f'                dictionary {key} = {{\n')
                f.write(f'                    string identifier = "{pid}"\n')
                if d["has_revision"]:
                    f.write(f'                    string version = "{gen_revision()}"\n')
                for ek in d["id_extras"]:
                    f.write(f'                    string {ek} = "{gen_id_extra_value(ek)}"\n')
                f.write(f'                }}\n')
            f.write(f'            }}\n')
            f.write(f'        }}\n')

            f.write(f'    )\n    {{\n')

            # token[] semantics:labels:<system>:<facet> properties
            for d in selected:
                key = d["key"]
                for facet in d["label_facets"]:
                    val = gen_facet_value(facet)
                    f.write(f'        token[] semantics:labels:{key}:{facet} = ["{val}"]\n')

            f.write(f'    }}\n')

        f.write('}\n')

    elapsed = time.time() - start_time
    file_size = os.path.getsize(output_path)
    return elapsed, file_size


def main():
    random.seed(42)

    print(f"Generating Approach D (Labels + Identity) stage ({NUM_PRIMS:,} prims)...")
    d_path = os.path.join(OUTPUT_DIR, "stress_approach_d.usda")
    d_time, d_size = generate_approach_d(NUM_PRIMS, d_path)
    d_lines = sum(1 for _ in open(d_path))

    print(f"  Generated in {d_time:.2f}s, {d_size/1024/1024:.1f} MB, {d_lines:,} lines")

    # Load existing A/B (and C if present) results for comparison
    results_path = os.path.join(OUTPUT_DIR, "stress_test_results.json")
    with open(results_path) as f:
        existing = json.load(f)

    a_size = existing["approach_a"]["file_size_bytes"]
    a_lines = existing["line_count"]["approach_a"]
    b_size = existing["approach_b"]["file_size_bytes"]
    b_lines = existing["line_count"]["approach_b"]

    print(f"\n--- File Size Comparison ---")
    print(f"Approach A: {a_size/1024/1024:.2f} MB")
    print(f"Approach B: {b_size/1024/1024:.2f} MB")
    if "approach_c" in existing:
        c_size = existing["approach_c"]["file_size_bytes"]
        print(f"Approach C: {c_size/1024/1024:.2f} MB")
    print(f"Approach D: {d_size/1024/1024:.2f} MB")

    print(f"\n--- Line Count Comparison ---")
    print(f"Approach A: {a_lines:,} lines")
    print(f"Approach B: {b_lines:,} lines")
    if "line_count" in existing and "approach_c" in existing["line_count"]:
        print(f"Approach C: {existing['line_count']['approach_c']:,} lines")
    print(f"Approach D: {d_lines:,} lines")

    # Count unique apiSchema instance names + dict keys for D
    d_schema_instances = set()
    d_label_props = set()
    d_dict_keys = set()
    in_apischemas = False
    with open(d_path) as fp:
        for line in fp:
            s = line.strip()
            if "prepend apiSchemas = [" in s:
                in_apischemas = True
                continue
            if in_apischemas:
                if s.startswith('"SemanticsLabelsAPI:'):
                    inst = s.strip('",')
                    d_schema_instances.add(inst)
                if "]" in s:
                    in_apischemas = False
            if s.startswith("dictionary ") and "= {" in s:
                d_dict_keys.add(s.split()[1])
            if s.startswith("token[] semantics:labels:"):
                prop = s.split("=")[0].strip().split()[-1]
                d_label_props.add(prop)

    print(f"\n--- Namespace Footprint ---")
    print(f"Approach A: {existing['namespace_footprint']['approach_a_unique_keys']} dict keys")
    print(f"Approach B: {existing['namespace_footprint']['approach_b_unique_properties']} property names")
    if "approach_c_unique_properties" in existing.get("namespace_footprint", {}):
        nfc = existing["namespace_footprint"]
        print(f"Approach C: {nfc['approach_c_unique_properties']} property names + "
              f"{nfc['approach_c_unique_dict_keys']} dict keys")
    print(f"Approach D: {len(d_schema_instances)} apiSchema instances + "
          f"{len(d_label_props)} label properties + {len(d_dict_keys)} dict keys")

    # Save
    existing["approach_d"] = {
        "generation_time_sec": round(d_time, 3),
        "file_size_bytes": d_size,
        "file_size_mb": round(d_size / 1024 / 1024, 2),
        "num_prims": NUM_PRIMS,
    }
    existing.setdefault("line_count", {})["approach_d"] = d_lines
    existing.setdefault("namespace_footprint", {})
    existing["namespace_footprint"]["approach_d_unique_apischema_instances"] = len(d_schema_instances)
    existing["namespace_footprint"]["approach_d_unique_label_properties"] = len(d_label_props)
    existing["namespace_footprint"]["approach_d_unique_dict_keys"] = len(d_dict_keys)

    with open(results_path, "w") as f:
        json.dump(existing, f, indent=2)
    print(f"\nResults saved to {results_path}")

    # Clean up large file
    os.remove(d_path)
    print(f"Removed {d_path} (gitignored)")


if __name__ == "__main__":
    main()
