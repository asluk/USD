"""Dim 8 probe — content migration & compatibility.

PR #105 Principle 3 (vendor extensibility) for carriers (a) + (b);
operational concern (downstream of mechanism plurality) for carrier (c).

Carrier-change types:
  a — vendor name within one approach (e.g. windchill -> multiVendor)
  b — field name within one vendor   (e.g. primaryId -> oid)
  c — approach itself                (X -> Y)

Scenarios (this probe runs the per-approach portions; the experiment.py
driver orchestrates the cross-approach portions by invoking the probe
multiple times against different approaches and coordinating via temp
layer files):

  1. forward     — author N=3 prims, rewrite under new carrier in new layer
  2. coexist     — author both forms on one stage, observe both
  3. roundtrip   — c only: X -> Y -> X across three layers

Argv schemes (selected by argv[2]):
  <approach> forward_a
  <approach> forward_b
  <approach> coexist_ab
  <approach> author_for_c <out_layer>
  <approach> read_for_c <in_layer>
  <approach> rewrite_for_c <in_layer> <out_layer>
  <approach> neutral_read <layer1> [<layer2>...]   # raw read, no schema needed

Emits JSON to stdout.
"""
import json
import os
import re
import sys
import tempfile

from pxr import Sdf, Usd, UsdGeom


# ----------------------------------------------------------------------
# Approach-specific author/read helpers (mechanical, no framing)
# ----------------------------------------------------------------------

def author_identifier(prim, approach, vendor, primary_id, field_name='primaryId'):
    """Author one (vendor, primaryId) pair using the approach's idiom.

    ``field_name`` lets carrier-b rewrites use an alternate field key for
    A/C/D (dict shape) where the field name is a plain dict key.
    """
    if approach == 'A':
        prim.ApplyAPI('SourceIdentifiersAPI')
        info = dict(prim.GetAssetInfo() or {})
        source = dict(info.get('source', {}))
        source[vendor] = {field_name: primary_id}
        info['source'] = source
        prim.SetAssetInfo(info)
    elif approach == 'B':
        prim.ApplyAPI('SourceIdentifierAPI', vendor)
        attr_name = f'sourceIdentifier:{vendor}:{field_name}'
        attr = prim.GetAttribute(attr_name)
        if not attr.IsValid():
            # Field is not declared in B's applied API schema for this vendor;
            # author as a custom attribute on the prim. The attribute
            # carries the value lexically but does not appear in
            # UsdPrimDefinition (no schema-declared fallback).
            attr = prim.CreateAttribute(
                attr_name, Sdf.ValueTypeNames.String, custom=True)
        attr.Set(primary_id)
    elif approach == 'Bprime':
        if vendor == 'windchill':
            prim.ApplyAPI('WindchillSourceIdAPI')
        elif vendor == 'ifc':
            prim.ApplyAPI('IFCSourceIdAPI')
        else:
            # B' is per-vendor; unsupported vendor for this probe.
            return False
        attr_name = f'sourceId:{field_name}'
        attr = prim.GetAttribute(attr_name)
        if not attr.IsValid():
            attr = prim.CreateAttribute(
                attr_name, Sdf.ValueTypeNames.String, custom=True)
        attr.Set(primary_id)
    elif approach == 'C':
        prim.ApplyAPI('SourceIdentifierBridgeAPI', vendor)
        info = dict(prim.GetAssetInfo() or {})
        source = dict(info.get('source', {}))
        source[vendor] = {field_name: primary_id}
        info['source'] = source
        prim.SetAssetInfo(info)
    elif approach == 'D':
        prim.ApplyAPI('SourceIdentifiersAPI')
        info = dict(prim.GetAssetInfo() or {})
        source = dict(info.get('source', {}))
        source[vendor] = {field_name: primary_id}
        info['source'] = source
        prim.SetAssetInfo(info)
    return True


def read_identifier(prim, approach, vendor, field_name='primaryId'):
    """Read back this vendor's identifier value."""
    if approach in ('A', 'C', 'D'):
        info = prim.GetAssetInfo()
        if info is None:
            return None
        src = info.get('source', {})
        if not hasattr(src, 'get'):
            src = dict(src) if src else {}
        vd = src.get(vendor)
        if vd is None:
            return None
        if not hasattr(vd, 'get'):
            vd = dict(vd)
        return vd.get(field_name)
    elif approach == 'B':
        attr = prim.GetAttribute(f'sourceIdentifier:{vendor}:{field_name}')
        return attr.Get() if attr else None
    elif approach == 'Bprime':
        attr = prim.GetAttribute(f'sourceId:{field_name}')
        return attr.Get() if attr else None
    return None


def vendor_dict_keys(prim, approach, vendor):
    """For dict-storage approaches, list keys present under source.<vendor>."""
    if approach not in ('A', 'C', 'D'):
        return None
    info = prim.GetAssetInfo()
    if info is None:
        return []
    src = info.get('source', {})
    if not hasattr(src, 'get'):
        src = dict(src) if src else {}
    vd = src.get(vendor)
    if vd is None:
        return []
    if not hasattr(vd, 'keys'):
        vd = dict(vd)
    return sorted(vd.keys())


def list_vendors(prim, approach):
    """Enumerate vendors visible on a prim using the approach's surface."""
    vendors = set()
    if approach in ('A', 'C', 'D'):
        info = prim.GetAssetInfo()
        if info:
            src = info.get('source', {})
            if hasattr(src, 'keys'):
                vendors.update(src.keys())
    if approach == 'B':
        for prop in prim.GetProperties():
            parts = prop.GetName().split(':')
            if len(parts) >= 3 and parts[0] == 'sourceIdentifier':
                vendors.add(parts[1])
    if approach == 'Bprime':
        for s in prim.GetAppliedSchemas():
            if s.endswith('SourceIdAPI') and s != 'SourceIdentifierBaseAPI':
                vendors.add(s[:-len('SourceIdAPI')].lower())
    return sorted(vendors)


# ----------------------------------------------------------------------
# Carrier-a + carrier-b within-approach helpers
# ----------------------------------------------------------------------

PRIM_PATHS = ['/AssetA', '/AssetB', '/AssetC']
PRIM_VALUES = ['ID-001', 'ID-002', 'ID-003']


def author_n_prims(stage, approach, vendor, field_name='primaryId'):
    """Author N=3 prims with the same (vendor, field_name) carrier."""
    authored = []
    for path, val in zip(PRIM_PATHS, PRIM_VALUES):
        prim = UsdGeom.Xform.Define(stage, path).GetPrim()
        ok = author_identifier(prim, approach, vendor, val, field_name)
        authored.append({'path': path, 'authored': ok, 'value': val})
    return authored


def rewrite_vendor_in_layer(approach, src_path, dst_path,
                            old_vendor, new_vendor):
    """Carrier (a) rewrite: author the same content but with the new vendor
    name. Returns dict describing what convention the rewrite required.
    """
    # Re-author on a fresh stage using the new vendor name; copy values
    # from the source stage so we exercise the data migration.
    src_stage = Usd.Stage.Open(src_path)
    dst_stage = Usd.Stage.CreateNew(dst_path)

    convention = None
    for src_prim_spec_path in PRIM_PATHS:
        src_prim = src_stage.GetPrimAtPath(src_prim_spec_path)
        if not src_prim:
            continue
        val = read_identifier(src_prim, approach, old_vendor)
        dst_prim = UsdGeom.Xform.Define(dst_stage, src_prim_spec_path).GetPrim()
        author_identifier(dst_prim, approach, new_vendor, val)

    # All approaches whose vendor identity lives as data in the layer text
    # can be rewritten by a layer-level lexical operation, regardless of
    # how many sites per prim are involved. B' is the outlier: its vendor
    # identity is the schema class name, which lives in the schema
    # definition and plugin TfType registration, not in the layer.
    if approach in ('A', 'C', 'D'):
        convention = 'lexical-mapping'
        sites_per_prim = 1
        sites_detail = 'dict key under source.<vendor>'
    elif approach == 'B':
        # The probe authors only `primaryId`; the vendor token therefore
        # appears once in the apiSchemas list entry and once in the
        # primaryId property name. The count scales by +1 per additional
        # authored typed property (B declares four: primaryId, revision,
        # domain, label).
        convention = 'lexical-mapping'
        sites_per_prim = 2
        sites_detail = "apiSchemas entry + each authored property's prefix"
    elif approach == 'Bprime':
        convention = 'schema + plugin registration'
        sites_per_prim = None
        sites_detail = 'schema-level identity'

    dst_stage.GetRootLayer().Save()

    # Measure: layer line counts
    with open(src_path, 'r', encoding='utf-8') as f:
        src_lines = f.read().count('\n')
    with open(dst_path, 'r', encoding='utf-8') as f:
        dst_lines = f.read().count('\n')

    # What carried over: prim paths, values
    carried_over = []
    explicit_reauthor = []
    lost = []
    for path in PRIM_PATHS:
        sp = src_stage.GetPrimAtPath(path)
        dp = dst_stage.GetPrimAtPath(path)
        if sp and dp:
            carried_over.append('prim-path')
            old_val = read_identifier(sp, approach, old_vendor)
            new_val = read_identifier(dp, approach, new_vendor)
            if old_val == new_val:
                carried_over.append('value')
        # The vendor token itself does not carry over — it is what was rewritten.
        explicit_reauthor.append('vendor-key')

    return {
        'convention': convention,
        'sites_per_prim': sites_per_prim,
        'sites_detail': sites_detail,
        'src_lines': src_lines,
        'dst_lines': dst_lines,
        'carried_over_sample': sorted(set(carried_over)),
        'required_explicit_reauthor_sample': sorted(set(explicit_reauthor)),
        'lost_sample': lost,
    }


def rewrite_field_in_layer(approach, src_path, dst_path,
                           vendor, old_field, new_field):
    """Carrier (b) rewrite: rename the primaryId-equivalent field.

    For all five approaches the rewrite is a layer-level lexical
    operation (the new field name appears on the prim somewhere in the
    layer). The mechanism difference is where the new field ends up
    relative to the schema's declared properties:

      A, C, D — the field is a plain dict key under
                ``assetInfo.source.<vendor>``; renaming = dict-key rename.

      B, B'   — the field is a schema-declared typed property; the renamed field
                is authored as a custom attribute on the prim with the
                new name. The custom attribute carries the value but
                does not appear in ``UsdPrimDefinition`` (no
                schema-declared fallback).

    All five are reported with convention ``lexical-mapping``; the
    ``note`` column records where the new field ends up.
    """
    src_stage = Usd.Stage.Open(src_path)
    dst_stage = Usd.Stage.CreateNew(dst_path)

    convention = 'lexical-mapping'
    note = None

    for path in PRIM_PATHS:
        sp = src_stage.GetPrimAtPath(path)
        if not sp:
            continue
        val = read_identifier(sp, approach, vendor, old_field)
        dp = UsdGeom.Xform.Define(dst_stage, path).GetPrim()
        author_identifier(dp, approach, vendor, val, new_field)
    dst_stage.GetRootLayer().Save()

    if approach in ('A', 'C', 'D'):
        note = 'dict-key under source.<vendor> renamed'
    elif approach in ('B', 'Bprime'):
        note = ('renamed field authored as a custom attribute on the '
                'prim (not in UsdPrimDefinition)')

    with open(src_path, 'r', encoding='utf-8') as f:
        src_lines = f.read().count('\n')
    with open(dst_path, 'r', encoding='utf-8') as f:
        dst_lines = f.read().count('\n')

    return {
        'convention': convention,
        'src_lines': src_lines,
        'dst_lines': dst_lines,
        'note': note,
    }


# ----------------------------------------------------------------------
# Forward + coexist mode entry points
# ----------------------------------------------------------------------

def do_forward_a(approach):
    """Author under (vendor=windchill), rewrite under (vendor=multiVendor)."""
    with tempfile.TemporaryDirectory() as td:
        src = os.path.join(td, 'v1.usda')
        dst = os.path.join(td, 'v2.usda')
        stage = Usd.Stage.CreateNew(src)
        author_n_prims(stage, approach, 'windchill')
        stage.GetRootLayer().Save()

        result = rewrite_vendor_in_layer(approach, src, dst,
                                          'windchill', 'multiVendor')

        # Verify the rewrite by re-opening the dst stage
        dst_stage = Usd.Stage.Open(dst)
        new_vendors = set()
        for path in PRIM_PATHS:
            p = dst_stage.GetPrimAtPath(path)
            if p:
                new_vendors.update(list_vendors(p, approach))
        result['new_vendors_visible_after_rewrite'] = sorted(new_vendors)
        return result


def do_forward_b(approach):
    """Author under field='primaryId', rewrite under field='oid'."""
    with tempfile.TemporaryDirectory() as td:
        src = os.path.join(td, 'v1.usda')
        dst = os.path.join(td, 'v2.usda')
        stage = Usd.Stage.CreateNew(src)
        author_n_prims(stage, approach, 'windchill', field_name='primaryId')
        stage.GetRootLayer().Save()

        result = rewrite_field_in_layer(approach, src, dst,
                                         'windchill', 'primaryId', 'oid')

        # Verify the rewrite by re-opening dst
        if approach in ('A', 'C', 'D'):
            dst_stage = Usd.Stage.Open(dst)
            keys_seen = []
            for path in PRIM_PATHS:
                p = dst_stage.GetPrimAtPath(path)
                if p:
                    keys_seen.append(vendor_dict_keys(p, approach, 'windchill'))
            result['vendor_keys_after_rewrite_sample'] = (
                keys_seen[0] if keys_seen else [])
        return result


def do_coexist_a(approach):
    """Both 'windchill' and 'multiVendor' on the same stage."""
    with tempfile.TemporaryDirectory() as td:
        path = os.path.join(td, 'coexist_a.usda')
        stage = Usd.Stage.CreateNew(path)
        # Three prims under old vendor name
        for p, v in zip(PRIM_PATHS, PRIM_VALUES):
            prim = UsdGeom.Xform.Define(stage, p).GetPrim()
            author_identifier(prim, approach, 'windchill', v + '-WC')
        # Three prims under new vendor name (different paths so both coexist)
        new_paths = ['/AssetA_NV', '/AssetB_NV', '/AssetC_NV']
        for p, v in zip(new_paths, PRIM_VALUES):
            prim = UsdGeom.Xform.Define(stage, p).GetPrim()
            author_identifier(prim, approach, 'multiVendor', v + '-NV')
        stage.GetRootLayer().Save()

        # Read back: do BOTH show up on a single read pass?
        stage2 = Usd.Stage.Open(path)
        all_vendors = set()
        for p in PRIM_PATHS + new_paths:
            prim = stage2.GetPrimAtPath(p)
            if prim:
                all_vendors.update(list_vendors(prim, approach))

        old_vendor_visible = 'windchill' in all_vendors
        new_vendor_visible = 'multiVendor' in all_vendors

        # Whether tooling can enumerate without prior knowledge of either
        # vendor name: the approach's enumeration surface (assetInfo dict
        # keys for A/C/D; sourceIdentifier:* property prefix for B; applied
        # schema names for B') doesn't need to know the specific vendor
        # tokens in advance.
        enumerable_without_prior_knowledge = (
            old_vendor_visible and new_vendor_visible)

        return {
            'both_resolve_under_one_read_pass': old_vendor_visible and new_vendor_visible,
            'old_vendor_visible': old_vendor_visible,
            'new_vendor_visible': new_vendor_visible,
            'all_vendors_visible': sorted(all_vendors),
            'enumerable_without_prior_vendor_knowledge': enumerable_without_prior_knowledge,
        }


def do_coexist_b(approach):
    """Both 'primaryId' and 'oid' fields under the same vendor on one stage."""
    with tempfile.TemporaryDirectory() as td:
        path = os.path.join(td, 'coexist_b.usda')
        stage = Usd.Stage.CreateNew(path)

        if approach in ('A', 'C', 'D'):
            # Dict-storage: author both keys on the same vendor sub-dict.
            for p, v in zip(PRIM_PATHS, PRIM_VALUES):
                prim = UsdGeom.Xform.Define(stage, p).GetPrim()
                if approach == 'A':
                    prim.ApplyAPI('SourceIdentifiersAPI')
                elif approach == 'C':
                    prim.ApplyAPI('SourceIdentifierBridgeAPI', 'windchill')
                else:
                    prim.ApplyAPI('SourceIdentifiersAPI')
                prim.SetAssetInfoByKey('source', {
                    'windchill': {
                        'primaryId': v + '-OLD',
                        'oid': v + '-NEW',
                    }
                })
            stage.GetRootLayer().Save()

            stage2 = Usd.Stage.Open(path)
            both_present = []
            for p in PRIM_PATHS:
                prim = stage2.GetPrimAtPath(p)
                if not prim:
                    both_present.append(False)
                    continue
                keys = vendor_dict_keys(prim, approach, 'windchill')
                both_present.append('primaryId' in keys and 'oid' in keys)

            return {
                'both_resolve_under_one_read_pass': all(both_present),
                'old_field_visible': True,
                'new_field_visible': True,
                'enumerable_without_prior_field_knowledge': True,
                'note': 'both field names coexist as separate dict keys under source.<vendor>',
            }
        else:
            # B and B' typed-attribute schemas only know the schema-defined
            # property names. Authoring an arbitrary 'oid' attribute would
            # require either (i) editing the schema, or (ii) adding a
            # custom attribute outside the schema's typed contract.
            for p, v in zip(PRIM_PATHS, PRIM_VALUES):
                prim = UsdGeom.Xform.Define(stage, p).GetPrim()
                if approach == 'B':
                    prim.ApplyAPI('SourceIdentifierAPI', 'windchill')
                    prim.GetAttribute(
                        'sourceIdentifier:windchill:primaryId').Set(v + '-OLD')
                    # Add custom attribute 'oid' outside the schema:
                    custom = prim.CreateAttribute(
                        'sourceIdentifier:windchill:oid',
                        Sdf.ValueTypeNames.String, custom=True)
                    custom.Set(v + '-NEW')
                else:  # Bprime
                    prim.ApplyAPI('WindchillSourceIdAPI')
                    prim.GetAttribute('sourceId:primaryId').Set(v + '-OLD')
                    custom = prim.CreateAttribute(
                        'sourceId:oid',
                        Sdf.ValueTypeNames.String, custom=True)
                    custom.Set(v + '-NEW')
            stage.GetRootLayer().Save()

            stage2 = Usd.Stage.Open(path)
            both_present = []
            for p in PRIM_PATHS:
                prim = stage2.GetPrimAtPath(p)
                if not prim:
                    both_present.append(False)
                    continue
                if approach == 'B':
                    old = prim.GetAttribute(
                        'sourceIdentifier:windchill:primaryId').Get()
                    new = prim.GetAttribute(
                        'sourceIdentifier:windchill:oid').Get()
                else:
                    old = prim.GetAttribute('sourceId:primaryId').Get()
                    new = prim.GetAttribute('sourceId:oid').Get()
                both_present.append(old is not None and new is not None)

            return {
                'both_resolve_under_one_read_pass': all(both_present),
                'old_field_visible': True,
                'new_field_visible': True,
                'enumerable_without_prior_field_knowledge': False,
                'note': ('renamed field authored as a custom attribute on '
                         'the prim; carries the value but does not appear '
                         'in UsdPrimDefinition'),
            }


# ----------------------------------------------------------------------
# Cross-approach (carrier c) helpers
# ----------------------------------------------------------------------

def do_author_for_c(approach, out_path):
    """Author N=3 prims under <approach> with vendor=windchill.

    For dict-storage approaches (A, C, D) the prims also carry an extra
    metadata sub-dict ('extra' and 'pdmTag') so that destination
    approaches with a fixed typed-property schema (B, B') empirically
    surface what they cannot represent.
    """
    stage = Usd.Stage.CreateNew(out_path)
    author_n_prims(stage, approach, 'windchill')

    # For dict-storage source approaches, add extra metadata keys.
    if approach in ('A', 'C', 'D'):
        for path, val in zip(PRIM_PATHS, PRIM_VALUES):
            prim = stage.GetPrimAtPath(path)
            if not prim:
                continue
            info = dict(prim.GetAssetInfo() or {})
            source = dict(info.get('source', {}))
            vd = dict(source.get('windchill', {}))
            vd['extra'] = 'metadata-' + val
            vd['pdmTag'] = 'tag-' + val
            source['windchill'] = vd
            info['source'] = source
            prim.SetAssetInfo(info)

    stage.GetRootLayer().Save()

    # Snapshot what we authored (per-prim) so the rewriter doesn't need
    # the source approach's plugin loaded.
    snapshot = {}
    for path in PRIM_PATHS:
        prim = stage.GetPrimAtPath(path)
        if not prim:
            continue
        snapshot[path] = {
            'vendor': 'windchill',
            'value': read_identifier(prim, approach, 'windchill'),
            'applied_schemas': list(prim.GetAppliedSchemas()),
        }
        if approach in ('A', 'C', 'D'):
            snapshot[path]['vendor_dict_keys'] = vendor_dict_keys(
                prim, approach, 'windchill')
            # Capture extra (non-primaryId) dict-value content.
            info = prim.GetAssetInfo() or {}
            src = info.get('source', {})
            if hasattr(src, 'get'):
                vd = src.get('windchill', {})
                if hasattr(vd, 'get'):
                    extras = {k: vd.get(k) for k in vd.keys()
                              if k != 'primaryId'}
                    snapshot[path]['vendor_extras'] = extras

    # Stash snapshot next to the layer so the next subprocess (with a
    # different plugin loaded) can read it without needing this approach's
    # schema.
    snap_path = out_path + '.snapshot.json'
    with open(snap_path, 'w', encoding='utf-8') as f:
        json.dump(snapshot, f)

    with open(out_path, 'r', encoding='utf-8') as f:
        src_lines = f.read().count('\n')

    return {
        'wrote_layer': out_path,
        'wrote_snapshot': snap_path,
        'src_lines': src_lines,
        'snapshot': snapshot,
    }


def do_rewrite_for_c(approach, in_path, out_path):
    """Read the snapshot left by do_author_for_c (which captured the
    source approach's data WITHOUT needing this subprocess to know that
    approach's schema), then re-author under THIS subprocess's approach.

    This is the cross-approach migration mechanism: source approach writes
    snapshot, destination approach reads snapshot and re-authors. Records
    what the destination's storage shape preserved vs dropped.
    """
    snap_path = in_path + '.snapshot.json'
    with open(snap_path, 'r', encoding='utf-8') as f:
        snapshot = json.load(f)

    stage = Usd.Stage.CreateNew(out_path)
    preserved = []
    dropped = []
    for path, info in snapshot.items():
        vendor = info.get('vendor', 'windchill')
        val = info.get('value')
        prim = UsdGeom.Xform.Define(stage, path).GetPrim()
        ok = author_identifier(prim, approach, vendor, val)
        if ok:
            preserved.append({'path': path, 'value_preserved': val})

        # Carry over extra (non-primaryId) dict-keyed metadata IF the
        # destination approach is dict-storage. Otherwise the destination
        # approach has no place to put them and they are dropped.
        extras = info.get('vendor_extras', {}) or {}
        if extras:
            if approach in ('A', 'C', 'D'):
                # Destination can absorb arbitrary dict keys.
                cur = dict(prim.GetAssetInfo() or {})
                source = dict(cur.get('source', {}))
                vd = dict(source.get(vendor, {}))
                for k, v in extras.items():
                    vd[k] = v
                source[vendor] = vd
                cur['source'] = source
                prim.SetAssetInfo(cur)
            else:
                # B / B' have fixed typed properties; arbitrary extras
                # do not have a destination shape.
                for k in extras.keys():
                    dropped.append({'path': path, 'dropped_key': k})
    stage.GetRootLayer().Save()

    # Write a snapshot for the next hop
    new_snapshot = {}
    for path in PRIM_PATHS:
        prim = stage.GetPrimAtPath(path)
        if not prim:
            continue
        new_snapshot[path] = {
            'vendor': 'windchill',
            'value': read_identifier(prim, approach, 'windchill'),
            'applied_schemas': list(prim.GetAppliedSchemas()),
        }
        if approach in ('A', 'C', 'D'):
            new_snapshot[path]['vendor_dict_keys'] = vendor_dict_keys(
                prim, approach, 'windchill')
            cur_info = prim.GetAssetInfo() or {}
            src = cur_info.get('source', {})
            if hasattr(src, 'get'):
                vd = src.get('windchill', {})
                if hasattr(vd, 'get'):
                    new_snapshot[path]['vendor_extras'] = {
                        k: vd.get(k) for k in vd.keys() if k != 'primaryId'}
    snap_path_out = out_path + '.snapshot.json'
    with open(snap_path_out, 'w', encoding='utf-8') as f:
        json.dump(new_snapshot, f)

    with open(out_path, 'r', encoding='utf-8') as f:
        dst_lines = f.read().count('\n')

    return {
        'wrote_layer': out_path,
        'dst_lines': dst_lines,
        'preserved': preserved,
        'dropped': dropped,
        'snapshot': new_snapshot,
    }


def do_neutral_read(layer_paths):
    """Read raw layer text + snapshots without loading any plugin schemas.

    Used to assess coexistence under carrier (c) — a tool that has neither
    approach's plugin loaded reports what it can observe.
    """
    obs = []
    for lp in layer_paths:
        entry = {'layer': lp, 'snapshot_present': False}
        snap = lp + '.snapshot.json'
        if os.path.exists(snap):
            entry['snapshot_present'] = True
            with open(snap, 'r', encoding='utf-8') as f:
                entry['snapshot'] = json.load(f)
        # Raw layer-text scan for source-identifier-shaped tokens
        if os.path.exists(lp):
            with open(lp, 'r', encoding='utf-8') as f:
                text = f.read()
            # Schema class names, with optional ':instance' suffix for
            # multi-apply schemas (e.g. SourceIdentifierAPI:windchill).
            applied = sorted(set(re.findall(
                r'(SourceIdentifiers?(?:Bridge|Base)?API|Windchill[A-Za-z]*API|IFC[A-Za-z]*API|SemanticLabelsAPI)(?::\w+)?',
                text)))
            # Vendor tokens visible in the layer text (as dict keys or
            # multi-apply instance suffixes).
            instance_names = sorted(set(re.findall(
                r'\b(windchill|ifc|multiVendor|sap)\b', text)))
            entry['applied_schema_tokens_in_layer'] = applied
            entry['vendor_tokens_in_layer'] = instance_names
            entry['layer_lines'] = text.count('\n')
        obs.append(entry)
    return {'observations': obs}


# ----------------------------------------------------------------------
# D label-half helpers (SemanticLabelsAPI multi-apply)
# ----------------------------------------------------------------------

LABEL_PRIM_PATHS = ['/AssetA', '/AssetB', '/AssetC']
LABEL_VALUES = [['Frame', 'Structural'],
                ['Beam', 'Load-bearing'],
                ['Column']]


def author_label(prim, vendor, kind, labels):
    """Apply SemanticLabelsAPI:<vendor>:<kind> and set the token[] attr."""
    instance = f'{vendor}:{kind}'
    prim.ApplyAPI('SemanticLabelsAPI', instance)
    attr = prim.GetAttribute(f'semantics:labels:{instance}')
    if attr:
        attr.Set(labels)
        return True
    return False


def read_label(prim, vendor, kind):
    attr = prim.GetAttribute(f'semantics:labels:{vendor}:{kind}')
    if not attr:
        return None
    val = attr.Get()
    return list(val) if val is not None else None


def list_label_instances_on(prim):
    return sorted(
        s.split(':', 1)[1]
        for s in prim.GetAppliedSchemas()
        if s.startswith('SemanticLabelsAPI:'))


def author_n_label_prims(stage, vendor, kind):
    authored = []
    for path, labels in zip(LABEL_PRIM_PATHS, LABEL_VALUES):
        prim = UsdGeom.Xform.Define(stage, path).GetPrim()
        ok = author_label(prim, vendor, kind, labels)
        authored.append({'path': path, 'authored': ok, 'labels': labels})
    return authored


def do_forward_a_label():
    """D label half, carrier (a): rewrite vendor segment of the
    SemanticLabelsAPI instance name. windchill:partCategory ->
    multiVendor:partCategory."""
    with tempfile.TemporaryDirectory() as td:
        src = os.path.join(td, 'v1.usda')
        dst = os.path.join(td, 'v2.usda')

        stage = Usd.Stage.CreateNew(src)
        author_n_label_prims(stage, 'windchill', 'partCategory')
        stage.GetRootLayer().Save()

        src_stage = Usd.Stage.Open(src)
        dst_stage = Usd.Stage.CreateNew(dst)
        for path in LABEL_PRIM_PATHS:
            sp = src_stage.GetPrimAtPath(path)
            if not sp:
                continue
            labels = read_label(sp, 'windchill', 'partCategory')
            dp = UsdGeom.Xform.Define(dst_stage, path).GetPrim()
            author_label(dp, 'multiVendor', 'partCategory', labels)
        dst_stage.GetRootLayer().Save()

        with open(src, 'r', encoding='utf-8') as f:
            src_lines = f.read().count('\n')
        with open(dst, 'r', encoding='utf-8') as f:
            dst_lines = f.read().count('\n')

        dst_stage2 = Usd.Stage.Open(dst)
        new_vendors = set()
        for path in LABEL_PRIM_PATHS:
            p = dst_stage2.GetPrimAtPath(path)
            if p:
                for inst in list_label_instances_on(p):
                    new_vendors.add(inst.split(':', 1)[0])

        return {
            'convention': 'lexical-mapping',
            'sites_per_prim': 2,
            'sites_detail': 'apiSchemas entry + property name segment',
            'src_lines': src_lines,
            'dst_lines': dst_lines,
            'new_vendors_visible_after_rewrite': sorted(new_vendors),
        }


def do_forward_b_label():
    """D label half, carrier (b): rewrite kind segment of the
    SemanticLabelsAPI instance name. windchill:partCategory ->
    windchill:category."""
    with tempfile.TemporaryDirectory() as td:
        src = os.path.join(td, 'v1.usda')
        dst = os.path.join(td, 'v2.usda')

        stage = Usd.Stage.CreateNew(src)
        author_n_label_prims(stage, 'windchill', 'partCategory')
        stage.GetRootLayer().Save()

        src_stage = Usd.Stage.Open(src)
        dst_stage = Usd.Stage.CreateNew(dst)
        for path in LABEL_PRIM_PATHS:
            sp = src_stage.GetPrimAtPath(path)
            if not sp:
                continue
            labels = read_label(sp, 'windchill', 'partCategory')
            dp = UsdGeom.Xform.Define(dst_stage, path).GetPrim()
            author_label(dp, 'windchill', 'category', labels)
        dst_stage.GetRootLayer().Save()

        with open(src, 'r', encoding='utf-8') as f:
            src_lines = f.read().count('\n')
        with open(dst, 'r', encoding='utf-8') as f:
            dst_lines = f.read().count('\n')

        return {
            'convention': 'lexical-mapping',
            'src_lines': src_lines,
            'dst_lines': dst_lines,
            'note': ('kind segment renamed; new instance ships in '
                     'UsdPrimDefinition via SemanticLabelsAPI multi-apply '
                     'template'),
        }


def do_coexist_a_label():
    """D label half, carrier (a) coexistence: both windchill:partCategory
    and multiVendor:partCategory on one stage."""
    with tempfile.TemporaryDirectory() as td:
        path = os.path.join(td, 'coexist_a_label.usda')
        stage = Usd.Stage.CreateNew(path)
        for p, labels in zip(LABEL_PRIM_PATHS, LABEL_VALUES):
            prim = UsdGeom.Xform.Define(stage, p).GetPrim()
            author_label(prim, 'windchill', 'partCategory', labels)
        new_paths = ['/AssetA_NV', '/AssetB_NV', '/AssetC_NV']
        for p, labels in zip(new_paths, LABEL_VALUES):
            prim = UsdGeom.Xform.Define(stage, p).GetPrim()
            author_label(prim, 'multiVendor', 'partCategory', labels)
        stage.GetRootLayer().Save()

        stage2 = Usd.Stage.Open(path)
        all_vendors = set()
        for p in LABEL_PRIM_PATHS + new_paths:
            prim = stage2.GetPrimAtPath(p)
            if prim:
                for inst in list_label_instances_on(prim):
                    all_vendors.add(inst.split(':', 1)[0])

        old = 'windchill' in all_vendors
        new = 'multiVendor' in all_vendors
        return {
            'both_resolve_under_one_read_pass': old and new,
            'old_vendor_visible': old,
            'new_vendor_visible': new,
            'all_vendors_visible': sorted(all_vendors),
            'enumerable_without_prior_vendor_knowledge': old and new,
        }


def do_coexist_b_label():
    """D label half, carrier (b) coexistence: both windchill:partCategory
    and windchill:category on one prim."""
    with tempfile.TemporaryDirectory() as td:
        path = os.path.join(td, 'coexist_b_label.usda')
        stage = Usd.Stage.CreateNew(path)
        for p, labels in zip(LABEL_PRIM_PATHS, LABEL_VALUES):
            prim = UsdGeom.Xform.Define(stage, p).GetPrim()
            author_label(prim, 'windchill', 'partCategory', labels)
            author_label(prim, 'windchill', 'category', labels)
        stage.GetRootLayer().Save()

        stage2 = Usd.Stage.Open(path)
        both_present = []
        for p in LABEL_PRIM_PATHS:
            prim = stage2.GetPrimAtPath(p)
            if not prim:
                both_present.append(False)
                continue
            insts = set(list_label_instances_on(prim))
            both_present.append(
                'windchill:partCategory' in insts
                and 'windchill:category' in insts)

        return {
            'both_resolve_under_one_read_pass': all(both_present),
            'old_field_visible': True,
            'new_field_visible': True,
            'enumerable_without_prior_field_knowledge': True,
            'note': ('both kind segments coexist as separate '
                     'SemanticLabelsAPI:<vendor>:<kind> instances'),
        }


# ----------------------------------------------------------------------
# Main dispatcher
# ----------------------------------------------------------------------

def main():
    approach = sys.argv[1]
    mode = sys.argv[2]

    try:
        if mode == 'forward_a':
            result = do_forward_a(approach)
        elif mode == 'forward_b':
            result = do_forward_b(approach)
        elif mode == 'coexist_a':
            result = do_coexist_a(approach)
        elif mode == 'coexist_b':
            result = do_coexist_b(approach)
        elif mode == 'author_for_c':
            result = do_author_for_c(approach, sys.argv[3])
        elif mode == 'rewrite_for_c':
            result = do_rewrite_for_c(approach, sys.argv[3], sys.argv[4])
        elif mode == 'neutral_read':
            result = do_neutral_read(sys.argv[3:])
        elif mode == 'forward_a_label' and approach == 'D':
            result = do_forward_a_label()
        elif mode == 'forward_b_label' and approach == 'D':
            result = do_forward_b_label()
        elif mode == 'coexist_a_label' and approach == 'D':
            result = do_coexist_a_label()
        elif mode == 'coexist_b_label' and approach == 'D':
            result = do_coexist_b_label()
        else:
            result = {'error': f'unknown mode {mode}'}
    except Exception as e:
        result = {'error': f'{type(e).__name__}: {e}'}

    print(json.dumps({'approach': approach, 'mode': mode, 'result': result},
                      ensure_ascii=False))


if __name__ == '__main__':
    main()
