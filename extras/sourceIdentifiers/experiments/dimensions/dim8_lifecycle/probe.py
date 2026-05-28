"""Dim 8 probe — within-approach lifecycle behavior.

PR #105 Principle 3 ("Vendor extensibility... tiered lifecycle: vendor →
multi-vendor → core"). Three sub-scenarios that all reduce to "rewrite
layer content, measure what changed in layers / schemas / plugins."

  8.1 promotion: rewrite vendor name `windchill` → `multiVendor` across
      N prims. Measure layer text size before/after + whether the
      approach's schema or plugin must also change for the rewrite to be
      meaningful (i.e. recognized by the schema registry).

  8.2 coexistence: same stage with some prims under `windchill` and some
      under `multiVendor`. Measure whether both names resolve on a read
      pass over the stage.

  8.3 within-vendor versioning: windchill v1 (canonical field
      `primaryId`) coexisting with windchill v2 (field renamed to `oid`)
      on the same stage. Measure: does the rename live inside the
      approach's schema-declared properties, or outside as a custom
      attribute, for each approach?

Notes:
- "Schema diff" / "plugin diff" measure whether the approach's schema
  registration (schema.usda + plugInfo.json) must be edited to make the
  rewrite recognized. They are not normative.
- D is probed on the identifier half only (matching dim1). For the
  labels half, promotion and versioning behave like B (instance name +
  property segment); coexistence behaves like A on the identifier dict.
  Captured in summary.

Argv: <approach>

Emits JSON {approach, scenarios: {8.1: {...}, 8.2: {...}, 8.3: {...}}}.
"""
import json
import os
import sys
import tempfile

from pxr import Sdf, Usd, UsdGeom


N_PRIMS = 3


def author_identifier(prim, approach, vendor, primary_id):
    """Author (vendor, primaryId) on prim using the approach's idiom.

    Mirrors dim1_composition.probe.author_identifier so observations are
    comparable across dimensions. For Bprime, vendors other than
    'windchill'/'ifc' have no schema in the experiment's plugInfo — the
    probe records that fact rather than fabricating a schema.
    """
    if approach == 'A':
        prim.ApplyAPI('SourceIdentifiersAPI')
        info = dict(prim.GetAssetInfo() or {})
        source = dict(info.get('source', {}))
        source[vendor] = {'primaryId': primary_id}
        info['source'] = source
        prim.SetAssetInfo(info)
    elif approach == 'B':
        prim.ApplyAPI('SourceIdentifierAPI', vendor)
        prim.GetAttribute(f'sourceIdentifier:{vendor}:primaryId').Set(primary_id)
    elif approach == 'Bprime':
        if vendor == 'windchill':
            prim.ApplyAPI('WindchillSourceIdAPI')
            prim.GetAttribute('sourceId:primaryId').Set(primary_id)
        elif vendor == 'ifc':
            prim.ApplyAPI('IFCSourceIdAPI')
            prim.GetAttribute('sourceId:primaryId').Set(primary_id)
        else:
            # No schema exists for this vendor in Bprime's plugInfo. The
            # closest mechanism affordance is to apply the base directly
            # and author the primaryId there, with no vendor identity at
            # the schema level. Record this branch separately.
            prim.ApplyAPI('SourceIdentifierBaseAPI')
            prim.GetAttribute('sourceId:primaryId').Set(primary_id)
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


def read_identifier(prim, approach, vendor):
    """Read back this vendor's primaryId."""
    if approach in ('A', 'C', 'D'):
        info = prim.GetAssetInfo()
        if info is None:
            return None
        src = info.get('source', {})
        if hasattr(src, 'get'):
            vendor_dict = src.get(vendor, {})
            if hasattr(vendor_dict, 'get'):
                return vendor_dict.get('primaryId')
        return None
    elif approach == 'B':
        attr = prim.GetAttribute(f'sourceIdentifier:{vendor}:primaryId')
        return attr.Get() if attr else None
    elif approach == 'Bprime':
        # Bprime collapses primaryId for windchill/ifc/<other> onto the
        # same property name. With multi-vendor schemas absent, this is
        # the only path; report the read as-is.
        attr = prim.GetAttribute('sourceId:primaryId')
        return attr.Get() if attr else None
    return None


def read_vendors_visible(prim, approach):
    """Enumerate vendors visible on the prim (best-effort per approach)."""
    vendors = set()
    if approach in ('A', 'C', 'D'):
        info = prim.GetAssetInfo()
        if info:
            src = info.get('source', {})
            if hasattr(src, 'keys'):
                vendors.update(src.keys())
    if approach == 'B':
        for prop in prim.GetProperties():
            name = prop.GetName()
            parts = name.split(':')
            if (len(parts) == 3 and parts[0] == 'sourceIdentifier'
                    and parts[2] == 'primaryId'):
                vendors.add(parts[1])
    if approach == 'Bprime':
        for s in prim.GetAppliedSchemas():
            if s == 'WindchillSourceIdAPI':
                vendors.add('windchill')
            elif s == 'IFCSourceIdAPI':
                vendors.add('ifc')
            elif s == 'SourceIdentifierBaseAPI':
                # No vendor identity at the schema level when only base
                # is applied. Recorded as a sentinel.
                vendors.add('<base-only:no-schema-vendor-identity>')
    return sorted(vendors)


# ---------- 8.1 promotion ---------------------------------------------------

def scenario_promotion(td, approach):
    """Author N prims under `windchill`, rewrite layer with vendor renamed
    to `multiVendor`. Return measurements."""
    stage1_path = os.path.join(td, 'stage_v1.usda')
    stage2_path = os.path.join(td, 'stage_v2.usda')

    # Build stage1: N prims, all under windchill.
    s1 = Usd.Stage.CreateNew(stage1_path)
    for i in range(N_PRIMS):
        p = UsdGeom.Xform.Define(s1, f'/Asset{i}').GetPrim()
        author_identifier(p, approach, 'windchill', f'WC-{i}')
    s1.GetRootLayer().Save()

    # Build stage2: same prim shapes, vendor renamed to multiVendor.
    s2 = Usd.Stage.CreateNew(stage2_path)
    for i in range(N_PRIMS):
        p = UsdGeom.Xform.Define(s2, f'/Asset{i}').GetPrim()
        author_identifier(p, approach, 'multiVendor', f'WC-{i}')
    s2.GetRootLayer().Save()

    with open(stage1_path, 'r', encoding='utf-8') as f:
        t1 = f.read()
    with open(stage2_path, 'r', encoding='utf-8') as f:
        t2 = f.read()

    layer_v1_lines = t1.count('\n')
    layer_v2_lines = t2.count('\n')

    # Schema / plugin diff: would the approach's registered schemas have
    # to change for the rewritten layer to be recognized? Answers are
    # mechanism-level facts derived from the schema location of the
    # vendor identity, captured as descriptive strings (not scored).
    vendor_identity_location = {
        'A':       'assetInfo dict key (data)',
        'B':       'multi-apply instance name (data)',
        'Bprime':  'schema class identifier (registered type)',
        'C':       'multi-apply instance name + assetInfo dict key (data)',
        'D':       'assetInfo dict key (data); labels half = instance name',
    }[approach]

    if approach == 'Bprime':
        # Renaming WindchillSourceIdAPI → MultiVendorSourceIdAPI requires
        # editing schema.usda (class rename) and plugInfo.json (TfType
        # rename). We don't physically perform the rename in the probe;
        # we report what would be needed.
        schema_change_required = True
        plugin_change_required = True
    else:
        schema_change_required = False
        plugin_change_required = False

    # Verify v2 reads back as authored.
    s2_read = Usd.Stage.Open(stage2_path)
    v2_readable_count = 0
    for i in range(N_PRIMS):
        prim = s2_read.GetPrimAtPath(f'/Asset{i}')
        if prim and read_identifier(prim, approach, 'multiVendor') == f'WC-{i}':
            v2_readable_count += 1

    return {
        'layer_v1_lines': layer_v1_lines,
        'layer_v2_lines': layer_v2_lines,
        'layer_line_delta': layer_v2_lines - layer_v1_lines,
        'prims_rewritten': N_PRIMS,
        'v2_readable_prims': v2_readable_count,
        'vendor_identity_location': vendor_identity_location,
        'schema_change_required': schema_change_required,
        'plugin_change_required': plugin_change_required,
    }


# ---------- 8.2 coexistence -------------------------------------------------

def scenario_coexistence(td, approach):
    """Half prims under windchill, half under multiVendor, same stage.
    Measure: do both names resolve on a single read pass?"""
    stage_path = os.path.join(td, 'stage_coexist.usda')
    s = Usd.Stage.CreateNew(stage_path)

    half = N_PRIMS  # author N prims of each vendor for clarity
    for i in range(half):
        p = UsdGeom.Xform.Define(s, f'/Old{i}').GetPrim()
        author_identifier(p, approach, 'windchill', f'WC-{i}')
    for i in range(half):
        p = UsdGeom.Xform.Define(s, f'/New{i}').GetPrim()
        author_identifier(p, approach, 'multiVendor', f'MV-{i}')
    s.GetRootLayer().Save()

    read = Usd.Stage.Open(stage_path)
    windchill_read = 0
    multivendor_read = 0
    for i in range(half):
        op = read.GetPrimAtPath(f'/Old{i}')
        if op and read_identifier(op, approach, 'windchill') == f'WC-{i}':
            windchill_read += 1
        np_ = read.GetPrimAtPath(f'/New{i}')
        if np_ and read_identifier(np_, approach, 'multiVendor') == f'MV-{i}':
            multivendor_read += 1

    # What vendor names appear on the stage as observable identifiers?
    all_vendors = set()
    for prim in read.Traverse():
        all_vendors.update(read_vendors_visible(prim, approach))

    return {
        'authored_windchill_prims': half,
        'authored_multivendor_prims': half,
        'windchill_readable': windchill_read,
        'multivendor_readable': multivendor_read,
        'vendors_observable_on_stage': sorted(all_vendors),
        'both_resolve_on_one_stage':
            windchill_read == half and multivendor_read == half,
    }


# ---------- 8.3 within-vendor versioning ------------------------------------

def author_v2_field(prim, approach, vendor, oid_value):
    """Author the renamed v2 field (`primaryId` → `oid`) for this approach.

    Returns a tag describing where the v2 field lives relative to the
    approach's schema-declared properties: 'inside-dict-shape',
    'custom-attribute', 'inside-dict-shape-with-bridge', or
    'custom-attribute-no-vendor-identity' for the Bprime base-only branch.
    """
    if approach == 'A':
        prim.ApplyAPI('SourceIdentifiersAPI')
        info = dict(prim.GetAssetInfo() or {})
        source = dict(info.get('source', {}))
        vendor_dict = dict(source.get(vendor, {}))
        vendor_dict['oid'] = oid_value
        source[vendor] = vendor_dict
        info['source'] = source
        prim.SetAssetInfo(info)
        return 'inside-dict-shape'

    if approach == 'B':
        # Schema declares primaryId/revision/domain/label. 'oid' is not
        # in the schema. Author it as a custom attribute in the
        # vendor's property namespace.
        prim.ApplyAPI('SourceIdentifierAPI', vendor)
        attr = prim.CreateAttribute(
            f'sourceIdentifier:{vendor}:oid', Sdf.ValueTypeNames.String,
            custom=True)
        attr.Set(oid_value)
        return 'custom-attribute'

    if approach == 'Bprime':
        # Schema declares sourceId:primaryId. The shared property name
        # forces the 'oid' field to live on the vendor's existing
        # schema namespace. Author as a custom attribute.
        if vendor == 'windchill':
            prim.ApplyAPI('WindchillSourceIdAPI')
            attr = prim.CreateAttribute(
                'sourceId:windchill:oid', Sdf.ValueTypeNames.String,
                custom=True)
            attr.Set(oid_value)
            return 'custom-attribute'
        # No schema for this vendor.
        prim.ApplyAPI('SourceIdentifierBaseAPI')
        attr = prim.CreateAttribute(
            'sourceId:oid', Sdf.ValueTypeNames.String, custom=True)
        attr.Set(oid_value)
        return 'custom-attribute-no-vendor-identity'

    if approach == 'C':
        prim.ApplyAPI('SourceIdentifierBridgeAPI', vendor)
        info = dict(prim.GetAssetInfo() or {})
        source = dict(info.get('source', {}))
        vendor_dict = dict(source.get(vendor, {}))
        vendor_dict['oid'] = oid_value
        source[vendor] = vendor_dict
        info['source'] = source
        prim.SetAssetInfo(info)
        return 'inside-dict-shape-with-bridge'

    if approach == 'D':
        prim.ApplyAPI('SourceIdentifiersAPI')
        info = dict(prim.GetAssetInfo() or {})
        source = dict(info.get('source', {}))
        vendor_dict = dict(source.get(vendor, {}))
        vendor_dict['oid'] = oid_value
        source[vendor] = vendor_dict
        info['source'] = source
        prim.SetAssetInfo(info)
        return 'inside-dict-shape'

    return 'unknown'


def read_v2_field(prim, approach, vendor):
    """Read the v2-renamed field ('oid') for this approach."""
    if approach in ('A', 'C', 'D'):
        info = prim.GetAssetInfo()
        if info is None:
            return None
        src = info.get('source', {})
        if hasattr(src, 'get'):
            vd = src.get(vendor, {})
            if hasattr(vd, 'get'):
                return vd.get('oid')
        return None
    if approach == 'B':
        attr = prim.GetAttribute(f'sourceIdentifier:{vendor}:oid')
        return attr.Get() if attr else None
    if approach == 'Bprime':
        if vendor == 'windchill':
            attr = prim.GetAttribute('sourceId:windchill:oid')
            return attr.Get() if attr else None
        attr = prim.GetAttribute('sourceId:oid')
        return attr.Get() if attr else None
    return None


def schema_knows_field(approach, field_name):
    """Is the field declared by the approach's schema (would have a
    fallback in UsdPrimDefinition)?

    For A/C/D the 'schema' is a documented dict contract — no schema
    properties — so neither primaryId nor oid is schema-declared in the
    property sense. Reported as 'documented-dict-shape' rather than
    True/False to avoid misclassification.
    """
    if approach == 'A' or approach == 'D':
        return 'documented-dict-shape (no typed properties)'
    if approach == 'C':
        return 'documented-dict-shape (assetInfoFallback via customData)'
    if approach == 'B':
        # Schema declares primaryId, revision, domain, label.
        return field_name in {'primaryId', 'revision', 'domain', 'label'}
    if approach == 'Bprime':
        # Base declares sourceId:primaryId, sourceId:revision. Windchill
        # adds sourceId:windchill:navigationCriteria, displayNumber.
        if field_name == 'primaryId':
            return True
        return False
    return None


def scenario_versioning(td, approach):
    """v1 prim with `primaryId`, v2 prim with `oid` (renamed field),
    coexisting on one stage."""
    stage_path = os.path.join(td, 'stage_versioning.usda')
    s = Usd.Stage.CreateNew(stage_path)

    # v1 prim — canonical primaryId field.
    p1 = UsdGeom.Xform.Define(s, '/V1Asset').GetPrim()
    author_identifier(p1, approach, 'windchill', 'P-1')

    # v2 prim — renamed field 'oid'.
    p2 = UsdGeom.Xform.Define(s, '/V2Asset').GetPrim()
    v2_location = author_v2_field(p2, approach, 'windchill', 'O-2')

    s.GetRootLayer().Save()

    read = Usd.Stage.Open(stage_path)
    p1r = read.GetPrimAtPath('/V1Asset')
    p2r = read.GetPrimAtPath('/V2Asset')

    v1_value = read_identifier(p1r, approach, 'windchill') if p1r else None
    v2_value = read_v2_field(p2r, approach, 'windchill') if p2r else None

    return {
        'v1_field': 'primaryId',
        'v2_field': 'oid',
        'v1_readable': v1_value == 'P-1',
        'v2_readable': v2_value == 'O-2',
        'v1_value': v1_value,
        'v2_value': v2_value,
        'v2_field_location': v2_location,
        'v2_field_in_schema': schema_knows_field(approach, 'oid'),
        'v1_field_in_schema': schema_knows_field(approach, 'primaryId'),
    }


# ---------- driver ----------------------------------------------------------

def main():
    approach = sys.argv[1]
    out = {'approach': approach, 'scenarios': {}}

    scenarios = [
        ('8.1_promotion', scenario_promotion),
        ('8.2_coexistence', scenario_coexistence),
        ('8.3_versioning', scenario_versioning),
    ]
    for name, fn in scenarios:
        with tempfile.TemporaryDirectory() as td:
            try:
                out['scenarios'][name] = fn(td, approach)
            except Exception as e:
                out['scenarios'][name] = {
                    'error': f'{type(e).__name__}: {e}',
                }
    print(json.dumps(out, ensure_ascii=False))


if __name__ == '__main__':
    main()
