"""Dim 6 probe — scope-of-applicability per approach.

PR #105 Open Question 4: model roots only, or any prim? This probe asks
each approach's schema to apply across a range of prim types and records:

  - apply_succeeded for each prim type
  - the schema's apiSchemaCanOnlyApplyTo declaration (if any)
  - approximate cost per prim (bytes added to the .usda layer)

Argv: <approach>

Emits JSON {approach, can_only_apply_to, by_prim_type, cost_bytes_per_prim}.
"""
import io
import json
import sys

from pxr import Sdf, Usd, UsdGeom


# (prim_type_name, define_fn). define_fn takes (stage, path) and returns
# the resulting UsdPrim. For typeless Over we use stage.OverridePrim.
PRIM_TYPES = [
    ('Over_typeless',  lambda s, p: s.OverridePrim(p)),
    ('Scope',          lambda s, p: UsdGeom.Scope.Define(s, p).GetPrim()),
    ('Xform',          lambda s, p: UsdGeom.Xform.Define(s, p).GetPrim()),
    ('Xform_kind_component',
        lambda s, p: _set_kind(UsdGeom.Xform.Define(s, p).GetPrim(), 'component')),
    ('Mesh_leaf',      lambda s, p: UsdGeom.Mesh.Define(s, p).GetPrim()),
]


def _set_kind(prim, kind):
    """Helper: apply Kind to a prim, returning the prim for chaining."""
    from pxr import Kind, Usd as _Usd  # local import to keep top tidy
    model = Usd.ModelAPI(prim)
    model.SetKind(kind)
    return prim


def apply_for_approach(prim, approach):
    """Apply this approach's schema to the prim using a 'windchill' vendor.
    Returns dict {applied: bool, error: str?, applied_schemas: [..]}."""
    out = {}
    try:
        if approach == 'A':
            applied = prim.ApplyAPI('SourceIdentifiersAPI')
            prim.SetAssetInfoByKey('source', {'windchill': {'primaryId': 'X'}})
        elif approach == 'B':
            applied = prim.ApplyAPI('SourceIdentifierAPI', 'windchill')
            prim.GetAttribute('sourceIdentifier:windchill:primaryId').Set('X')
        elif approach == 'Bprime':
            applied = prim.ApplyAPI('WindchillSourceIdAPI')
            prim.GetAttribute('sourceId:primaryId').Set('X')
        elif approach == 'C':
            applied = prim.ApplyAPI('SourceIdentifierBridgeAPI', 'windchill')
            prim.SetAssetInfoByKey('source', {'windchill': {'primaryId': 'X'}})
        elif approach == 'D':
            applied = prim.ApplyAPI('SourceIdentifiersAPI')
            prim.SetAssetInfoByKey('source', {'windchill': {'primaryId': 'X'}})
        else:
            raise ValueError(approach)
        out['applied'] = bool(applied)
        out['applied_schemas'] = list(prim.GetAppliedSchemas())
    except Exception as e:
        out['applied'] = False
        out['error'] = f'{type(e).__name__}: {e}'
    return out


def get_can_only_apply_to(approach):
    """Read the schema's apiSchemaCanOnlyApplyTo declaration if any."""
    reg = Usd.SchemaRegistry()
    candidates = {
        'A': ['SourceIdentifiersAPI'],
        'B': ['SourceIdentifierAPI'],
        'Bprime': ['SourceIdentifierBaseAPI', 'WindchillSourceIdAPI', 'IFCSourceIdAPI'],
        'C': ['SourceIdentifierBridgeAPI'],
        'D': ['SourceIdentifiersAPI', 'SemanticLabelsAPI'],
    }[approach]
    out = {}
    for name in candidates:
        try:
            allowed = reg.GetAPISchemaCanOnlyApplyToTypeNames(name)
            out[name] = list(allowed) if allowed else []
        except Exception as e:
            out[name] = f'error: {type(e).__name__}: {e}'
    return out


def measure_cost_per_prim(approach):
    """Author the schema on 10 typeless prims, measure layer-size delta."""
    stage_empty = Usd.Stage.CreateInMemory()
    for i in range(10):
        UsdGeom.Xform.Define(stage_empty, f'/A_{i}')
    empty_size = len(stage_empty.GetRootLayer().ExportToString().encode('utf-8'))

    stage_full = Usd.Stage.CreateInMemory()
    for i in range(10):
        prim = UsdGeom.Xform.Define(stage_full, f'/A_{i}').GetPrim()
        apply_for_approach(prim, approach)
    full_size = len(stage_full.GetRootLayer().ExportToString().encode('utf-8'))

    delta = full_size - empty_size
    return {
        'empty_bytes_for_10_prims': empty_size,
        'with_identifier_bytes_for_10_prims': full_size,
        'delta_bytes': delta,
        'bytes_per_prim': delta / 10.0,
    }


def main():
    approach = sys.argv[1]
    by_prim_type = {}
    for type_name, fn in PRIM_TYPES:
        stage = Usd.Stage.CreateInMemory()
        try:
            prim = fn(stage, '/Asset')
            by_prim_type[type_name] = apply_for_approach(prim, approach)
        except Exception as e:
            by_prim_type[type_name] = {
                'applied': False,
                'error': f'define-failed: {type(e).__name__}: {e}',
            }

    out = {
        'approach': approach,
        'can_only_apply_to': get_can_only_apply_to(approach),
        'by_prim_type': by_prim_type,
        'cost_per_prim': measure_cost_per_prim(approach),
    }
    print(json.dumps(out, ensure_ascii=False))


if __name__ == '__main__':
    main()
