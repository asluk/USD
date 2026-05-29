"""Dim 5 probe — schema/plugin distribution per approach.

PR #105 Principle 3 (vendor extensibility): "any vendor or standards body
can declare their own identifier scheme without central approval. Tiered
lifecycle (vendor → multi-vendor → core). Vendor extensions are
data-model-level, not plugin-architecture-level."

This probe records, per approach:

  - artifact_shipped       : what a new vendor needs to ship to register
                             a new identifier scheme ('data only' /
                             'schema + data' / 'plugin + schema + data')
  - registers_with_core    : whether the vendor's data plugs into a
                             core-shipped schema (no per-vendor schema
                             needed)
  - vendor_collision_mode  : how two vendors avoid stepping on each
                             other ('dict key namespace' / 'apply
                             instance name' / 'class name allocation')
  - two_vendors_coexist    : empirical — apply two different vendor
                             identifiers to one prim, verify both
                             round-trip independently

For Bprime, an additional check: confirm that the experiment's plugin
already ships TWO vendor schemas (Windchill + IFC) — concrete evidence
of the per-vendor schema requirement.

Argv: <approach>

Emits JSON {approach, artifact_shipped, registers_with_core,
            vendor_collision_mode, two_vendors_coexist,
            per_vendor_schemas_shipped (Bprime only)}.
"""
import json
import sys

from pxr import Sdf, Usd, UsdGeom


def two_vendors_apply(approach):
    """Apply two different vendor identifiers to one prim, round-trip.
    Returns dict {windchill_round_trip, ifc_round_trip, applied_schemas_after_rt}."""
    stage = Usd.Stage.CreateInMemory()
    prim = UsdGeom.Xform.Define(stage, '/Asset').GetPrim()
    expected_windchill = 'OR:wt.part.WTPart:4697800'
    expected_ifc = 'Bs43BRT3PrSvZ0KshZJRhD'

    try:
        if approach == 'A':
            prim.ApplyAPI('SourceIdentifiersAPI')
            prim.SetAssetInfoByKey('source', {
                'windchill': {'primaryId': expected_windchill},
                'ifc': {'primaryId': expected_ifc},
            })
        elif approach == 'B':
            prim.ApplyAPI('SourceIdentifierAPI', 'windchill')
            prim.ApplyAPI('SourceIdentifierAPI', 'ifc')
            prim.GetAttribute('sourceIdentifier:windchill:primaryId').Set(expected_windchill)
            prim.GetAttribute('sourceIdentifier:ifc:primaryId').Set(expected_ifc)
        elif approach == 'Bprime':
            prim.ApplyAPI('WindchillSourceIdAPI')
            prim.ApplyAPI('IFCSourceIdAPI')
            # Bprime uses 'prepend apiSchemas' for the base; per the
            # v3-findings memory, the base sourceId:primaryId is SHARED
            # across vendor schemas applied to the same prim. So setting
            # both gives the LAST one's value, not one-per-vendor. We
            # document this rather than expecting independent storage.
            prim.GetAttribute('sourceId:primaryId').Set(expected_windchill)
            # Vendor-specific fields preserve their identity, though:
            prim.GetAttribute('sourceId:windchill:navigationCriteria').Set('nav')
            prim.GetAttribute('sourceId:ifc:ifcType').Set('IfcWall')
        elif approach == 'C':
            prim.ApplyAPI('SourceIdentifierBridgeAPI', 'windchill')
            prim.ApplyAPI('SourceIdentifierBridgeAPI', 'ifc')
            prim.SetAssetInfoByKey('source', {
                'windchill': {'primaryId': expected_windchill},
                'ifc': {'primaryId': expected_ifc},
            })
        elif approach == 'D':
            prim.ApplyAPI('SourceIdentifiersAPI')
            prim.SetAssetInfoByKey('source', {
                'windchill': {'primaryId': expected_windchill},
                'ifc': {'primaryId': expected_ifc},
            })
        else:
            raise ValueError(approach)

        usda = stage.GetRootLayer().ExportToString()
        stage2 = Usd.Stage.CreateInMemory()
        stage2.GetRootLayer().ImportFromString(usda)
        prim2 = stage2.GetPrimAtPath('/Asset')

        applied = list(prim2.GetAppliedSchemas())

        if approach in ('A', 'C', 'D'):
            info = prim2.GetAssetInfo()
            wc = info.get('source', {}).get('windchill', {}).get('primaryId')
            ifc = info.get('source', {}).get('ifc', {}).get('primaryId')
        elif approach == 'B':
            wc = prim2.GetAttribute('sourceIdentifier:windchill:primaryId').Get()
            ifc = prim2.GetAttribute('sourceIdentifier:ifc:primaryId').Get()
        elif approach == 'Bprime':
            # Shared base property — both vendors apply but the property
            # is one slot. Record what the round-trip recovered.
            shared = prim2.GetAttribute('sourceId:primaryId').Get()
            wc = (f'shared base property; recovered={shared!r}; '
                  f'(both vendor schemas applied but base is shared)')
            ifc = wc  # same observation
        else:
            wc = ifc = None

        return {
            'windchill_round_trip': wc,
            'windchill_matches': wc == expected_windchill if approach != 'Bprime' else None,
            'ifc_round_trip': ifc,
            'ifc_matches': ifc == expected_ifc if approach != 'Bprime' else None,
            'applied_schemas_after_round_trip': applied,
            'distinct_vendor_storage': approach != 'Bprime',
        }
    except Exception as e:
        return {'error': f'{type(e).__name__}: {e}'}


def bprime_vendor_schemas():
    """Bprime-specific: confirm the plugin ships per-vendor schemas."""
    reg = Usd.SchemaRegistry()
    candidates = ['SourceIdentifierBaseAPI', 'WindchillSourceIdAPI', 'IFCSourceIdAPI']
    return {c: bool(reg.IsAppliedAPISchema(c)) for c in candidates}


# Per-approach structural facts, derived from the schema design and the
# v3-findings memory. These don't change between runs.
ARTIFACT_FACTS = {
    'A': {
        'artifact_shipped': 'data only',
        'registers_with_core': True,
        'vendor_collision_mode': 'dict key namespace (assetInfo.source.<vendor>)',
        'registration_steps': [
            'author assetInfo.source.<vendor> entries — no schema work',
        ],
    },
    'B': {
        'artifact_shipped': 'data only',
        'registers_with_core': True,
        'vendor_collision_mode': 'ApplyAPI instance name (multi-apply schema)',
        'registration_steps': [
            'ApplyAPI("SourceIdentifierAPI", "<vendor>") — no schema work',
            'author typed sourceIdentifier:<vendor>:* properties',
        ],
    },
    'Bprime': {
        'artifact_shipped': 'plugin + schema + data',
        'registers_with_core': False,
        'vendor_collision_mode': 'class-name allocation (TfType global namespace)',
        'registration_steps': [
            'author schema.usda declaring <Vendor>SourceIdAPI inheriting from '
            'APISchemaBase and prepending SourceIdentifierBaseAPI',
            'run usdGenSchema (codeless or full)',
            'publish plugInfo.json + generatedSchema.usda',
            'add plugin dir to PXR_PLUGINPATH_NAME',
        ],
    },
    'C': {
        'artifact_shipped': 'data only (bridge mechanism not yet implemented)',
        'registers_with_core': True,
        'vendor_collision_mode': 'ApplyAPI instance name + dict key namespace',
        'registration_steps': [
            'ApplyAPI("SourceIdentifierBridgeAPI", "<vendor>") — no schema work',
            'author assetInfo.source.<vendor> entries',
            'NOTE: the assetInfoFallback customData mechanism that gives C its '
            'distinguishing behavior did not surface in UsdPrimDefinition in '
            'this run (see implementation findings in COMPARISON.md). Storage '
            'shape resolves to A in current OpenUSD.',
        ],
    },
    'D': {
        'artifact_shipped': 'data only',
        'registers_with_core': True,
        'vendor_collision_mode': 'identifier: dict key namespace; labels: ApplyAPI instance (vendor:labelKind)',
        'registration_steps': [
            'identifier half: author assetInfo.source.<vendor> entries',
            'label half: ApplyAPI("SemanticLabelsAPI", "<vendor>:<labelKind>") and set tokens',
            'no schema work for either half',
        ],
    },
}


def d_labels_two_vendors_coexist():
    """D label half: apply two SemanticLabelsAPI instances on one prim,
    set token[] labels, round-trip via USDA, verify both recovered.

    Mirrors the shape of two_vendors_apply but for the label half so that
    Dim 5's "two-vendor coexistence" question has a measurement for both
    sides of D's split mechanism.
    """
    stage = Usd.Stage.CreateInMemory()
    prim = UsdGeom.Xform.Define(stage, '/Asset').GetPrim()
    expected_wc = ['Frame', 'Structural']
    expected_ifc = ['IfcBeam']

    try:
        prim.ApplyAPI('SemanticLabelsAPI', 'windchill:partCategory')
        prim.ApplyAPI('SemanticLabelsAPI', 'ifc:entityType')
        prim.GetAttribute('semantics:labels:windchill:partCategory').Set(expected_wc)
        prim.GetAttribute('semantics:labels:ifc:entityType').Set(expected_ifc)

        usda = stage.GetRootLayer().ExportToString()
        stage2 = Usd.Stage.CreateInMemory()
        stage2.GetRootLayer().ImportFromString(usda)
        prim2 = stage2.GetPrimAtPath('/Asset')

        applied = list(prim2.GetAppliedSchemas())
        wc_attr = prim2.GetAttribute('semantics:labels:windchill:partCategory')
        ifc_attr = prim2.GetAttribute('semantics:labels:ifc:entityType')
        wc_val = list(wc_attr.Get()) if wc_attr and wc_attr.Get() is not None else None
        ifc_val = list(ifc_attr.Get()) if ifc_attr and ifc_attr.Get() is not None else None

        return {
            'windchill_round_trip': wc_val,
            'windchill_matches': wc_val == expected_wc,
            'ifc_round_trip': ifc_val,
            'ifc_matches': ifc_val == expected_ifc,
            'applied_schemas_after_round_trip': applied,
            'distinct_vendor_storage': True,
        }
    except Exception as e:
        return {'error': f'{type(e).__name__}: {e}'}


def main():
    approach = sys.argv[1]
    out = dict(ARTIFACT_FACTS[approach])
    out['approach'] = approach
    out['two_vendors_coexist'] = two_vendors_apply(approach)
    if approach == 'Bprime':
        out['per_vendor_schemas_shipped'] = bprime_vendor_schemas()
    if approach == 'D':
        out['label_half'] = {
            'two_vendors_coexist': d_labels_two_vendors_coexist(),
        }
    print(json.dumps(out, ensure_ascii=False))


if __name__ == '__main__':
    main()
