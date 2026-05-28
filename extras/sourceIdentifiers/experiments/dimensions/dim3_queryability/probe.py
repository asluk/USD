"""Dim 3 probe — external queryability per approach.

PR #105 Principle 6 ("External queryability") + Open Question 1
(Cross-system resolution and indexing): "Mechanism must make it tractable
to build external indexes (given identifier X, which layers/prims
reference it?)".

Per approach, this probe:

  1. Builds a synthetic project — 30 prims across 3 vendors
     (windchill, ifc, adobe), with some prims carrying multiple vendors,
     authored using the approach's idiomatic mechanism.
  2. Saves the project as a `.usda` text layer.
  3. Walks the saved layer at the Sdf level — NO Usd.Stage composition,
     NO schema knowledge beyond the approach's storage convention — and
     recovers the (prim_path, vendor, primaryId) triples.
  4. Reports recall (did the indexer find every authored identifier),
     vendor-discovery (did it find vendors without prior knowledge),
     and indexer lines-of-code.

Argv: <approach>

Emits JSON {approach, indexer_loc, authored_count, recovered_count,
            recall_pct, vendors_authored, vendors_discovered,
            sample_recovered}.
"""
import inspect
import json
import os
import sys
import tempfile

from pxr import Sdf, Usd, UsdGeom


VENDORS = ['windchill', 'ifc', 'adobe']

# (prim_index_modulo, vendors_to_author) — designs a deterministic mix
# so we get prims with 1 vendor and prims with 2-3 vendors.
def vendors_for_prim(i):
    if i % 7 == 0:
        return VENDORS  # all three
    if i % 3 == 0:
        return ['windchill', 'ifc']
    if i % 5 == 0:
        return ['ifc', 'adobe']
    return [VENDORS[i % 3]]


def author_project(stage, approach, n_prims=30):
    """Build the synthetic project. Returns list of (prim_path, vendor,
    primary_id) authored."""
    authored = []
    for i in range(n_prims):
        path = f'/Project/Asset_{i:03d}'
        prim = UsdGeom.Xform.Define(stage, path).GetPrim()
        for vendor in vendors_for_prim(i):
            primary_id = f'{vendor.upper()}-{i:04d}'
            authored.append((path, vendor, primary_id))
            if approach == 'A':
                prim.ApplyAPI('SourceIdentifiersAPI')
                info = dict(prim.GetAssetInfo() or {})
                source = dict(info.get('source', {}))
                source[vendor] = {'primaryId': primary_id}
                info['source'] = source
                # SetAssetInfo replaces the whole dict
                prim.SetAssetInfo(info)
            elif approach == 'B':
                prim.ApplyAPI('SourceIdentifierAPI', vendor)
                prim.GetAttribute(
                    f'sourceIdentifier:{vendor}:primaryId').Set(primary_id)
            elif approach == 'Bprime':
                # Bprime requires per-vendor schemas. Our experiment plugin
                # ships Windchill and IFC. For 'adobe' we have no schema
                # available — author what we can; the recall computation
                # below accounts for this by only counting authored items.
                if vendor == 'windchill':
                    prim.ApplyAPI('WindchillSourceIdAPI')
                    prim.GetAttribute('sourceId:primaryId').Set(primary_id)
                    prim.GetAttribute('sourceId:windchill:displayNumber').Set(
                        f'PN-{i:04d}')
                elif vendor == 'ifc':
                    prim.ApplyAPI('IFCSourceIdAPI')
                    prim.GetAttribute('sourceId:primaryId').Set(primary_id)
                    prim.GetAttribute('sourceId:ifc:ifcType').Set('IfcBeam')
                else:
                    # Skip — adobe schema not shipped in our experiment
                    # plugin; this models the "vendor must ship a plugin"
                    # cost of Bprime.
                    authored.pop()  # remove from authored list
                    continue
            elif approach == 'C':
                prim.ApplyAPI('SourceIdentifierBridgeAPI', vendor)
                info = dict(prim.GetAssetInfo() or {})
                source = dict(info.get('source', {}))
                source[vendor] = {'primaryId': primary_id}
                info['source'] = source
                prim.SetAssetInfo(info)
            elif approach == 'D':
                prim.ApplyAPI('SourceIdentifiersAPI')
                info = dict(prim.GetAssetInfo() or {})
                source = dict(info.get('source', {}))
                source[vendor] = {'primaryId': primary_id}
                info['source'] = source
                prim.SetAssetInfo(info)
    return authored


# -----------------------------------------------------------------------------
# Indexers — one per approach. Each takes a layer path, returns a list of
# (prim_path, vendor, primaryId) tuples recovered from Sdf-level walk only
# (no Usd.Stage composition). The LoC count is reported via inspect.
# -----------------------------------------------------------------------------

def indexer_A(layer_path):
    """Indexer for Approach A: walk assetInfo.source dict per prim."""
    layer = Sdf.Layer.FindOrOpen(layer_path)
    found = []
    def visit(p):
        spec = layer.GetPrimAtPath(p)
        if spec:
            ai = spec.GetInfo('assetInfo')
            if ai:
                src = ai.get('source', {})
                for vendor, payload in src.items():
                    pid = payload.get('primaryId')
                    if pid:
                        found.append((str(p), vendor, pid))
    layer.Traverse('/', visit)
    return found


def indexer_B(layer_path):
    """Indexer for Approach B: walk attributes matching the
    sourceIdentifier:<vendor>:primaryId namespace template."""
    layer = Sdf.Layer.FindOrOpen(layer_path)
    found = []
    def visit(p):
        spec = layer.GetPrimAtPath(p)
        if spec:
            for attr in spec.attributes:
                name = attr.name
                parts = name.split(':')
                if (len(parts) == 3 and parts[0] == 'sourceIdentifier'
                        and parts[2] == 'primaryId'):
                    vendor = parts[1]
                    val = attr.default
                    if val is not None:
                        found.append((str(p), vendor, val))
    layer.Traverse('/', visit)
    return found


def indexer_Bprime(layer_path):
    """Indexer for Approach B': scan applied apiSchemas for class names
    matching the *SourceIdAPI pattern; on each match, fetch sourceId:primaryId.
    Vendor identity comes from the schema class name."""
    layer = Sdf.Layer.FindOrOpen(layer_path)
    found = []
    def visit(p):
        spec = layer.GetPrimAtPath(p)
        if not spec:
            return
        applied = spec.GetInfo('apiSchemas')
        if not applied:
            return
        # apiSchemas is a Sdf.TokenListOp
        items = list(applied.explicitItems) + list(applied.prependedItems) + \
                list(applied.appendedItems) + list(applied.addedItems)
        for cls in items:
            if cls.endswith('SourceIdAPI') and cls != 'SourceIdentifierBaseAPI':
                vendor = cls[:-len('SourceIdAPI')].lower()
                # Find the shared sourceId:primaryId attribute
                attr = next((a for a in spec.attributes
                            if a.name == 'sourceId:primaryId'), None)
                if attr and attr.default is not None:
                    found.append((str(p), vendor, attr.default))
    layer.Traverse('/', visit)
    return found


def indexer_C(layer_path):
    """Indexer for Approach C: storage shape is A's; same walk."""
    return indexer_A(layer_path)


def indexer_D(layer_path):
    """Indexer for Approach D's IDENTIFIER half: same walk as A.
    (D's label half lives separately and is out of scope for the
    identifier index.)"""
    return indexer_A(layer_path)


INDEXERS = {
    'A': indexer_A,
    'B': indexer_B,
    'Bprime': indexer_Bprime,
    'C': indexer_C,
    'D': indexer_D,
}


def count_loc(fn):
    """Lines of code in the indexer function (excluding docstring + blank).

    Toggles a doc-flag based on `\"\"\"` count per line, so multi-line
    docstrings are handled correctly regardless of where the closing
    triple-quote sits.
    """
    src = inspect.getsource(fn)
    lines = src.splitlines()
    body = []
    in_doc = False
    for i, ln in enumerate(lines):
        if i == 0:  # def signature line
            continue
        s = ln.strip()
        if not s:
            continue
        triples = s.count('"""')
        if triples:
            in_doc = bool((int(in_doc) + triples) % 2)
            continue  # line is part of the docstring
        if in_doc:
            continue
        body.append(ln)
    return len(body)


def main():
    approach = sys.argv[1]
    with tempfile.TemporaryDirectory() as td:
        layer_path = os.path.join(td, 'project.usda')

        stage = Usd.Stage.CreateNew(layer_path)
        authored = author_project(stage, approach)
        stage.GetRootLayer().Save()

        indexer = INDEXERS[approach]
        recovered = indexer(layer_path)

        authored_set = set(authored)
        recovered_set = set(recovered)
        matches = authored_set & recovered_set

        out = {
            'approach': approach,
            'indexer_loc': count_loc(indexer),
            'authored_count': len(authored),
            'recovered_count': len(recovered),
            'matched_count': len(matches),
            'recall_pct': (100.0 * len(matches) / len(authored)
                            if authored else 0.0),
            'vendors_authored': sorted({v for _, v, _ in authored}),
            'vendors_discovered': sorted({v for _, v, _ in recovered}),
            'sample_recovered': sorted(list(recovered_set))[:5],
            'missed': sorted(list(authored_set - recovered_set))[:5],
            'spurious': sorted(list(recovered_set - authored_set))[:5],
        }
        print(json.dumps(out, ensure_ascii=False))


if __name__ == '__main__':
    main()
