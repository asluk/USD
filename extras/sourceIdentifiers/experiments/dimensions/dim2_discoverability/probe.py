"""Dim 2 probe — discoverability per approach.

PR #105 Principle 5 ("Discoverability"): "tools can discover a prim
carries source identifiers without prior pipeline-specific knowledge."

For each approach, on a prim with ONE vendor identifier (windchill)
authored, probe four surfaces:

  1. applied_schemas         — does the apiSchemas list surface the
                               vendor identity?
  2. prim_def_metadata       — does UsdPrimDefinition.GetMetadata('assetInfo')
                               surface any source-identifier shape without
                               the user authoring metadata?
  3. prim_def_properties     — are typed property fallbacks discoverable
                               from the registry (no scene needed)?
  4. generic_gui_walk        — can a tool that knows ONLY "look for
                               source identifiers" enumerate vendors and
                               values on this prim?

Argv: <approach>

Emits JSON {approach, surfaces: {surface_name: observation}}.
"""
import json
import sys

from pxr import Sdf, Usd, UsdGeom


def author_one_vendor(prim, approach):
    if approach == 'A':
        prim.ApplyAPI('SourceIdentifiersAPI')
        prim.SetAssetInfoByKey('source',
            {'windchill': {'primaryId': 'OR:wt.part.WTPart:4697800'}})
    elif approach == 'B':
        prim.ApplyAPI('SourceIdentifierAPI', 'windchill')
        prim.GetAttribute('sourceIdentifier:windchill:primaryId').Set('OR:wt.part.WTPart:4697800')
    elif approach == 'Bprime':
        prim.ApplyAPI('WindchillSourceIdAPI')
        prim.GetAttribute('sourceId:primaryId').Set('OR:wt.part.WTPart:4697800')
    elif approach == 'C':
        prim.ApplyAPI('SourceIdentifierBridgeAPI', 'windchill')
        prim.SetAssetInfoByKey('source',
            {'windchill': {'primaryId': 'OR:wt.part.WTPart:4697800'}})
    elif approach == 'D':
        prim.ApplyAPI('SourceIdentifiersAPI')
        prim.SetAssetInfoByKey('source',
            {'windchill': {'primaryId': 'OR:wt.part.WTPart:4697800'}})


def probe_applied_schemas(prim, approach):
    """Surface 1: does GetAppliedSchemas() reveal vendor identity?"""
    schemas = list(prim.GetAppliedSchemas())
    vendor_visible = any('windchill' in s.lower() for s in schemas)
    return {
        'applied_schemas': schemas,
        'vendor_visible_in_applied_schemas': vendor_visible,
    }


def probe_prim_def_metadata(prim, approach):
    """Surface 2: does UsdPrimDefinition.GetMetadata('assetInfo') surface
    source-identifier shape without scene authoring?"""
    prim_def = prim.GetPrimDefinition()
    try:
        ai = prim_def.GetMetadata('assetInfo')
    except Exception as e:
        return {'error': f'{type(e).__name__}: {e}'}
    has_source_key = bool(ai and 'source' in dict(ai))
    return {
        'prim_def_assetInfo': dict(ai) if ai else None,
        'has_source_key_without_authoring': has_source_key,
    }


def probe_prim_def_properties(approach):
    """Surface 3: are typed fallbacks discoverable from the registry?"""
    reg = Usd.SchemaRegistry()
    schema_names = {
        'A': ['SourceIdentifiersAPI'],
        'B': ['SourceIdentifierAPI'],
        'Bprime': ['SourceIdentifierBaseAPI', 'WindchillSourceIdAPI', 'IFCSourceIdAPI'],
        'C': ['SourceIdentifierBridgeAPI'],
        'D': ['SourceIdentifiersAPI', 'SemanticLabelsAPI'],
    }[approach]
    out = {}
    for name in schema_names:
        is_multi = reg.IsMultipleApplyAPISchema(name)
        kind = 'multi-apply' if is_multi else 'single-apply'
        try:
            # For multi-apply schemas the template prim definition uses
            # __INSTANCE_NAME__ placeholders; for single-apply schemas the
            # property names are concrete.
            prim_def = reg.FindAppliedAPIPrimDefinition(name)
            if prim_def is None:
                out[name] = {
                    'kind': kind,
                    'error': f'FindAppliedAPIPrimDefinition({name!r}) returned None',
                }
                continue
            props = list(prim_def.GetPropertyNames())
            key = 'property_template' if is_multi else 'properties'
            out[name] = {'kind': kind, key: props}
        except Exception as e:
            out[name] = {'kind': kind, 'error': f'{type(e).__name__}: {e}'}
    return out


def probe_generic_gui_walk(prim, approach):
    """Surface 4: can a tool that knows nothing about the specific schema
    discover vendors + identifiers? Implements two generic strategies:

      (a) walk applied_schemas, looking for known SCHEMA-PREFIX patterns
      (b) walk assetInfo, looking for 'source' sub-dict

    The probe reports what each generic strategy recovers for this approach.
    """
    out = {}

    # Strategy (a): scan applied_schemas for schema-prefix conventions.
    # Known prefixes from PR #105 plus 'SemanticLabels' for D. A tool that
    # was told ONLY about the discoverability convention (not specific
    # schema names) couldn't realistically use this — but we record what
    # comes out per approach.
    schemas = list(prim.GetAppliedSchemas())
    out['applied_schemas_seen'] = schemas

    # Strategy (b): scan assetInfo for 'source' key with sub-dicts.
    info = prim.GetAssetInfo()
    source = info.get('source', {}) if info else {}
    out['assetInfo_source_keys'] = list(source.keys()) if hasattr(source, 'keys') else []
    out['assetInfo_source_values'] = (
        {k: dict(v) if hasattr(v, 'keys') else v for k, v in source.items()}
        if hasattr(source, 'items') else {})

    # Net signal: can a generic walker find at least the vendor name?
    vendor_found_via_apply = any('windchill' in s.lower() for s in schemas)
    vendor_found_via_assetInfo = 'windchill' in out['assetInfo_source_keys']
    out['vendor_found_via_apply_schemas'] = vendor_found_via_apply
    out['vendor_found_via_assetInfo_source'] = vendor_found_via_assetInfo
    return out


def main():
    approach = sys.argv[1]
    stage = Usd.Stage.CreateInMemory()
    prim = UsdGeom.Xform.Define(stage, '/Asset').GetPrim()
    author_one_vendor(prim, approach)

    out = {
        'approach': approach,
        'surfaces': {
            'applied_schemas': probe_applied_schemas(prim, approach),
            'prim_def_metadata': probe_prim_def_metadata(prim, approach),
            'prim_def_properties': probe_prim_def_properties(approach),
            'generic_gui_walk': probe_generic_gui_walk(prim, approach),
        },
    }
    print(json.dumps(out, ensure_ascii=False))


if __name__ == '__main__':
    main()
