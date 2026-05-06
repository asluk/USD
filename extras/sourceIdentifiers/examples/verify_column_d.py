#!/usr/bin/env python3
"""
Verify examples/column_d.usda parses against a built USD with
UsdSemanticsLabelsAPI and that the expected schemas/values are present.

Usage (from repo root with a built USD install at ./_install):

    python3 examples/verify_column_d.py [--install-dir <path-to-install>]

If you run via a Python interpreter that is not the one OpenUSD was built
against (e.g., LibreOffice's bundled python on Windows), this script adds
the install's bin/ and lib/ directories to the DLL search path before
importing pxr.

The verifier checks:
  1. column_d.usda opens without errors.
  2. /Column_C14 is a valid Mesh prim.
  3. All 10 SemanticsLabelsAPI:<system>:<facet> instances are applied.
  4. Each token[] semantics:labels:<system>:<facet> attribute returns
     the expected value when read via UsdSemantics.LabelsAPI.
  5. assetInfo["source"][<system>] dictionaries match expected identifier
     and version values.

Exits 0 on success, non-zero on any failure. Prints a per-instance
OK/FAIL line for diagnostic clarity.
"""

import argparse
import os
import sys


def add_install_paths(install_dir):
    """Make a USD install discoverable to the current Python interpreter."""
    bin_dir = os.path.join(install_dir, "bin")
    lib_dir = os.path.join(install_dir, "lib")
    py_dir = os.path.join(lib_dir, "python")
    if hasattr(os, "add_dll_directory"):
        if os.path.isdir(bin_dir):
            os.add_dll_directory(bin_dir)
        if os.path.isdir(lib_dir):
            os.add_dll_directory(lib_dir)
    if os.path.isdir(py_dir):
        sys.path.insert(0, py_dir)


EXPECTED_LABELS = {
    ("ifc", "type"): "IfcColumn",
    ("ifc", "objectType"): "W14x90",
    ("revit", "category"): "Structural Columns",
    ("revit", "familyType"): "W14x90",
    ("revit", "mark"): "C-14",
    ("revit", "level"): "Level 3",
    ("uniclass", "system"): "Uniclass 2015",
    ("uniclass", "title"): "Column systems",
    ("omniclass", "system"): "OmniClass",
    ("omniclass", "title"): "Structural Steel Columns",
}

EXPECTED_IDENTITY = {
    "ifc": {"identifier": "2O2Fr$t4X7Zf8NOew3FNr2"},
    "revit": {"identifier": "847562", "version": "2026.1"},
    "uniclass": {"identifier": "Ss_25_10_30"},
    "omniclass": {},
}


def verify(stage_path):
    from pxr import Usd, UsdSemantics

    stage = Usd.Stage.Open(stage_path)
    if not stage:
        print(f"FAIL: could not open {stage_path}")
        return 1

    prim = stage.GetPrimAtPath("/Column_C14")
    if not prim or not prim.IsValid():
        print("FAIL: /Column_C14 not found or invalid")
        return 1
    if prim.GetTypeName() != "Mesh":
        print(f"FAIL: /Column_C14 is {prim.GetTypeName()}, expected Mesh")
        return 1

    fails = 0
    print(f"Stage opened: {stage_path}")
    print(f"Prim /Column_C14: type=Mesh valid=True")
    print(f"Applied schemas: {len(prim.GetAppliedSchemas())}")
    print()

    print("SemanticsLabelsAPI per (system, facet):")
    for (system, facet), expected_value in EXPECTED_LABELS.items():
        instance = f"{system}:{facet}"
        api = UsdSemantics.LabelsAPI.Get(prim, instance)
        if not api:
            print(f"  FAIL {instance}: API not applied")
            fails += 1
            continue
        val = api.GetLabelsAttr().Get()
        if not val or val[0] != expected_value:
            print(f"  FAIL {instance}: got {list(val) if val else None}, "
                  f"expected ['{expected_value}']")
            fails += 1
        else:
            print(f"  OK   {instance} = {list(val)}")

    print()
    print('assetInfo["source"][<system>]:')
    source = prim.GetAssetInfoByKey("source") or {}
    for system, expected_fields in EXPECTED_IDENTITY.items():
        actual = dict(source.get(system, {}))
        if actual != expected_fields:
            print(f"  FAIL {system}: got {actual}, expected {expected_fields}")
            fails += 1
        else:
            print(f"  OK   {system} = {actual}")

    print()
    print(f"FAILURES: {fails}")
    return 0 if fails == 0 else 1


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--install-dir",
                        default=os.environ.get("USD_INSTALL_DIR", ""),
                        help="Path to a built USD install (root containing "
                             "bin/, lib/, lib/python/)")
    parser.add_argument("--stage",
                        default=os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                             "column_d.usda"),
                        help="Path to column_d.usda (default: alongside this script)")
    args = parser.parse_args()

    if args.install_dir:
        add_install_paths(args.install_dir)

    return verify(args.stage)


if __name__ == "__main__":
    sys.exit(main())
