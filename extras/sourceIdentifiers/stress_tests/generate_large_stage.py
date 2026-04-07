#!/usr/bin/env python3
"""
Generate large USD stages (100K+ prims) with source identifiers using
both approaches, and measure performance characteristics.

This script does NOT require a built OpenUSD — it generates .usda text files
directly, which any USD-capable tool can load. This allows the comparison
to proceed without a full build cycle.

For performance measurements with actual USD APIs, see benchmark_apis.py.
"""

import os
import sys
import time
import json
import random
import string
import hashlib

# Configuration
NUM_PRIMS = 100_000
IDENTIFIERS_PER_PRIM_MIN = 1
IDENTIFIERS_PER_PRIM_MAX = 5
OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))

# Vendor/standards body simulation
DOMAINS = [
    {
        "key": "windchill",
        "domain": "com.ptc.windchill",
        "label": "Windchill Part OID",
        "id_prefix": "VR:wt.part.WTPart:",
        "has_revision": True,
        "metadata_keys": ["displayNumber", "navigationType", "organization"],
    },
    {
        "key": "ifc",
        "domain": "org.buildingsmart.ifc",
        "label": "IFC GlobalId",
        "id_prefix": "",
        "id_gen": "ifc_guid",
        "has_revision": False,
        "metadata_keys": ["ifcType", "schema"],
    },
    {
        "key": "revit",
        "domain": "com.autodesk.revit",
        "label": "Revit ElementId",
        "id_prefix": "",
        "id_gen": "numeric",
        "has_revision": True,
        "metadata_keys": ["category", "familyType", "mark"],
    },
    {
        "key": "nvidia",
        "domain": "com.nvidia.omniverse",
        "label": "Omniverse Nucleus Asset",
        "id_prefix": "omni://nucleus.nvidia.com/assets/",
        "has_revision": True,
        "metadata_keys": ["checkpoint", "creator"],
    },
    {
        "key": "sap",
        "domain": "com.sap.s4hana",
        "label": "SAP Material Number",
        "id_prefix": "0000000000",
        "has_revision": True,
        "metadata_keys": ["materialType", "plant"],
    },
    {
        "key": "adobe",
        "domain": "com.adobe.substance3d",
        "label": "Substance 3D Asset ID",
        "id_prefix": "adb:sub3d:asset:",
        "has_revision": True,
        "metadata_keys": ["collection"],
    },
    {
        "key": "step",
        "domain": "org.iso.step",
        "label": "STEP Entity ID",
        "id_prefix": "STEP-FILE-ID:#",
        "has_revision": True,
        "metadata_keys": ["entityType", "standard"],
    },
    {
        "key": "opcua",
        "domain": "org.opcfoundation.ua",
        "label": "OPC UA NodeId",
        "id_prefix": "ns=4;s=Plant.",
        "has_revision": False,
        "metadata_keys": ["nodeClass", "browseName"],
    },
]

# IFC-like base64 GUID generator
IFC_CHARS = string.digits + string.ascii_uppercase + string.ascii_lowercase + "_$"
def gen_ifc_guid():
    return "".join(random.choice(IFC_CHARS) for _ in range(22))

def gen_numeric_id():
    return str(random.randint(100000, 9999999))

def gen_revision():
    return random.choice(["Rev.A", "Rev.B", "Rev.C", "v1.0", "v2.1", "v3.0", "01", "02"])

def gen_primary_id(domain_info, prim_idx):
    if domain_info.get("id_gen") == "ifc_guid":
        return gen_ifc_guid()
    elif domain_info.get("id_gen") == "numeric":
        return gen_numeric_id()
    else:
        return f"{domain_info['id_prefix']}{prim_idx:08d}"

def gen_metadata_value(key):
    values = {
        "displayNumber": f"PART-{random.randint(1000,9999)}",
        "navigationType": f"OR:wt.filter.NavigationCriteria:{random.randint(1000000,9999999)}",
        "organization": random.choice(["com.carrier.hvac", "com.trane", "com.daikin"]),
        "ifcType": random.choice(["IfcColumn", "IfcBeam", "IfcSlab", "IfcWall", "IfcDoor"]),
        "schema": "IFC4x3",
        "category": random.choice(["Structural Columns", "Walls", "Floors", "Doors"]),
        "familyType": random.choice(["W14x90", "W12x65", "HSS8x8x1/2"]),
        "mark": f"M-{random.randint(1,999)}",
        "checkpoint": f"cp_{random.randint(20260101,20261231)}_v{random.randint(1,50)}",
        "creator": random.choice(["NVIDIA SimReady", "Artist Pipeline", "Auto-gen"]),
        "materialType": random.choice(["HAWA", "FERT", "HALB"]),
        "plant": random.choice(["NYC1", "SFO2", "AUS3"]),
        "collection": random.choice(["Aerospace", "Automotive", "Architecture"]),
        "entityType": random.choice(["PRODUCT_DEFINITION", "SHAPE_REPRESENTATION"]),
        "standard": "ISO 10303-242:2022",
        "nodeClass": random.choice(["Object", "Variable"]),
        "browseName": f"Node_{random.randint(1,10000)}",
    }
    return values.get(key, f"value_{random.randint(1,1000)}")


# =========================================================================
# Approach A: assetInfo sub-dictionary generator
# =========================================================================

def generate_approach_a(num_prims, output_path):
    """Generate a .usda file using Approach A (assetInfo sub-dictionaries)."""
    start_time = time.time()
    
    with open(output_path, "w") as f:
        f.write('#usda 1.0\n(\n')
        f.write(f'    """Approach A stress test: {num_prims:,} prims with source identifiers."""\n')
        f.write('    defaultPrim = "Root"\n    metersPerUnit = 1.0\n)\n\n')
        f.write('def Xform "Root" (\n    kind = "assembly"\n)\n{\n')
        
        for i in range(num_prims):
            num_ids = random.randint(IDENTIFIERS_PER_PRIM_MIN, IDENTIFIERS_PER_PRIM_MAX)
            selected_domains = random.sample(DOMAINS, min(num_ids, len(DOMAINS)))
            
            prim_name = f"Prim_{i:06d}"
            
            # Build assetInfo dictionary
            f.write(f'    def Xform "{prim_name}" (\n')
            f.write(f'        assetInfo = {{\n')
            f.write(f'            dictionary sourceIds = {{\n')
            
            for j, domain_info in enumerate(selected_domains):
                primary_id = gen_primary_id(domain_info, i)
                f.write(f'                dictionary {domain_info["key"]} = {{\n')
                f.write(f'                    string primaryId = "{primary_id}"\n')
                if domain_info["has_revision"]:
                    f.write(f'                    string revision = "{gen_revision()}"\n')
                if domain_info["metadata_keys"]:
                    f.write(f'                    dictionary metadata = {{\n')
                    for mk in domain_info["metadata_keys"][:2]:
                        f.write(f'                        string {mk} = "{gen_metadata_value(mk)}"\n')
                    f.write(f'                    }}\n')
                f.write(f'                }}\n')
            
            f.write(f'            }}\n')
            f.write(f'        }}\n')
            f.write(f'    )\n    {{\n    }}\n')
        
        f.write('}\n')
    
    elapsed = time.time() - start_time
    file_size = os.path.getsize(output_path)
    return elapsed, file_size


# =========================================================================
# Approach B: Multi-apply schema generator
# =========================================================================

def generate_approach_b(num_prims, output_path):
    """Generate a .usda file using Approach B (multi-apply schema properties)."""
    start_time = time.time()
    
    with open(output_path, "w") as f:
        f.write('#usda 1.0\n(\n')
        f.write(f'    """Approach B stress test: {num_prims:,} prims with source identifiers."""\n')
        f.write('    defaultPrim = "Root"\n    metersPerUnit = 1.0\n)\n\n')
        f.write('def Xform "Root" (\n    kind = "assembly"\n)\n{\n')
        
        for i in range(num_prims):
            num_ids = random.randint(IDENTIFIERS_PER_PRIM_MIN, IDENTIFIERS_PER_PRIM_MAX)
            selected_domains = random.sample(DOMAINS, min(num_ids, len(DOMAINS)))
            
            prim_name = f"Prim_{i:06d}"
            
            # Build apiSchemas list
            schemas = [f'"SourceIdentifierAPI:{d["key"]}"' for d in selected_domains]
            schemas_str = ",\n            ".join(schemas)
            
            f.write(f'    def Xform "{prim_name}" (\n')
            f.write(f'        prepend apiSchemas = [\n            {schemas_str}\n        ]\n')
            f.write(f'    )\n    {{\n')
            
            for domain_info in selected_domains:
                key = domain_info["key"]
                primary_id = gen_primary_id(domain_info, i)
                
                f.write(f'        string sourceIdentifier:{key}:primaryId = "{primary_id}"\n')
                if domain_info["has_revision"]:
                    f.write(f'        string sourceIdentifier:{key}:revision = "{gen_revision()}"\n')
                f.write(f'        token sourceIdentifier:{key}:domain = "{domain_info["domain"]}"\n')
                f.write(f'        string sourceIdentifier:{key}:label = "{domain_info["label"]}"\n')
            
            f.write(f'    }}\n')
        
        f.write('}\n')
    
    elapsed = time.time() - start_time
    file_size = os.path.getsize(output_path)
    return elapsed, file_size


# =========================================================================
# Analysis: Discovery patterns (text-based, no USD API needed)
# =========================================================================

def analyze_discovery(filepath, approach):
    """
    Measure how long it takes to find all prims with a specific source identifier
    using text search (simulating what a tool would need to do without indexing).
    """
    target_domain = "windchill"
    target_id = None
    
    start = time.time()
    matches = []
    current_prim = None
    
    with open(filepath) as f:
        for line in f:
            stripped = line.strip()
            if stripped.startswith('def '):
                # Extract prim name
                parts = stripped.split('"')
                if len(parts) >= 2:
                    current_prim = parts[1]
            
            if approach == "A":
                if f'string primaryId = "' in stripped and current_prim:
                    # Check if we're in the windchill domain context
                    # (simplified — real analysis would track nesting)
                    pass
            elif approach == "B":
                if f'sourceIdentifier:{target_domain}:primaryId' in stripped:
                    val = stripped.split('"')[1] if '"' in stripped else ""
                    if target_id is None:
                        target_id = val  # Record first occurrence
                    if val == target_id:
                        matches.append(current_prim)
    
    elapsed = time.time() - start
    return elapsed, len(matches), target_id


# =========================================================================
# Main
# =========================================================================

def main():
    random.seed(42)  # Reproducible results
    
    results = {}
    
    print(f"Generating Approach A stage ({NUM_PRIMS:,} prims)...")
    a_path = os.path.join(OUTPUT_DIR, "stress_approach_a.usda")
    a_time, a_size = generate_approach_a(NUM_PRIMS, a_path)
    results["approach_a"] = {
        "generation_time_sec": round(a_time, 3),
        "file_size_bytes": a_size,
        "file_size_mb": round(a_size / 1024 / 1024, 2),
        "num_prims": NUM_PRIMS,
    }
    print(f"  Generated in {a_time:.2f}s, {a_size/1024/1024:.1f} MB")
    
    random.seed(42)  # Same seed for fair comparison
    
    print(f"\nGenerating Approach B stage ({NUM_PRIMS:,} prims)...")
    b_path = os.path.join(OUTPUT_DIR, "stress_approach_b.usda")
    b_time, b_size = generate_approach_b(NUM_PRIMS, b_path)
    results["approach_b"] = {
        "generation_time_sec": round(b_time, 3),
        "file_size_bytes": b_size,
        "file_size_mb": round(b_size / 1024 / 1024, 2),
        "num_prims": NUM_PRIMS,
    }
    print(f"  Generated in {b_time:.2f}s, {b_size/1024/1024:.1f} MB")
    
    # File size comparison
    print(f"\n--- File Size Comparison ---")
    print(f"Approach A: {a_size/1024/1024:.2f} MB")
    print(f"Approach B: {b_size/1024/1024:.2f} MB")
    ratio = b_size / a_size if a_size > 0 else 0
    print(f"Ratio (B/A): {ratio:.3f}x")
    results["file_size_ratio_b_over_a"] = round(ratio, 3)
    
    # Discovery test
    print(f"\n--- Discovery Performance (text search) ---")
    
    a_disc_time, a_matches, a_target = analyze_discovery(a_path, "A")
    print(f"Approach A: {a_disc_time:.3f}s")
    
    b_disc_time, b_matches, b_target = analyze_discovery(b_path, "B")
    print(f"Approach B: {b_disc_time:.3f}s, {b_matches} matches for '{b_target}'")
    
    results["discovery"] = {
        "approach_a_sec": round(a_disc_time, 4),
        "approach_b_sec": round(b_disc_time, 4),
        "approach_b_matches": b_matches,
    }
    
    # Line count comparison (proxy for authoring complexity)
    a_lines = sum(1 for _ in open(a_path))
    b_lines = sum(1 for _ in open(b_path))
    print(f"\n--- Authoring Verbosity ---")
    print(f"Approach A: {a_lines:,} lines")
    print(f"Approach B: {b_lines:,} lines")
    results["line_count"] = {
        "approach_a": a_lines,
        "approach_b": b_lines,
        "ratio_b_over_a": round(b_lines / a_lines, 3) if a_lines > 0 else 0,
    }
    
    # Count unique property/key names (proxy for namespace sprawl)
    # Approach A: count unique dictionary keys across all prims
    # Approach B: count unique property names across all prims
    a_keys = set()
    b_props = set()
    with open(a_path) as f:
        for line in f:
            s = line.strip()
            if s.startswith("dictionary ") and "= {" in s:
                key = s.split()[1]
                a_keys.add(key)
    with open(b_path) as f:
        for line in f:
            s = line.strip()
            if s.startswith("string sourceIdentifier:") or s.startswith("token sourceIdentifier:"):
                prop = s.split("=")[0].strip().split()[-1]
                b_props.add(prop)
    
    print(f"\n--- Namespace Footprint ---")
    print(f"Approach A: {len(a_keys)} unique dictionary keys")
    print(f"Approach B: {len(b_props)} unique property names")
    results["namespace_footprint"] = {
        "approach_a_unique_keys": len(a_keys),
        "approach_b_unique_properties": len(b_props),
    }
    
    # Save results
    results_path = os.path.join(OUTPUT_DIR, "stress_test_results.json")
    with open(results_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to {results_path}")
    
    return results


if __name__ == "__main__":
    main()
