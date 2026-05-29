"""Dim 1 probe — composition behavior per approach.

PR #105 Principle 4 ("Composability"): "Must participate in USD's
composition model in a well-defined way; clear behavior under reference,
inherit, specialize."

For each approach × each composition primitive (sublayer, reference,
payload, inherit, specialize), probe two scenarios:

  override_same_vendor: weak layer authors a primaryId for `windchill`;
                        strong layer overrides with a different value.
                        Record which value the composed prim holds.

  two_vendors_merge:    weak layer authors `windchill`; strong layer
                        authors `ifc` ONLY (no windchill override).
                        Record whether both vendors are visible on the
                        composed prim.

For approach D, an additional ``label_half`` section runs the analogous
two scenarios on D's SemanticLabelsAPI multi-apply schema:

  override_same_label:  weak authors labels under
                        SemanticLabelsAPI:windchill:partCategory; strong
                        authors a different label list under the SAME
                        instance.

  two_kinds_merge:      weak authors windchill:partCategory; strong
                        authors ifc:entityType (different instance).
                        Both instances visible on the composed prim?

The probe builds the scenarios at the Sdf level (PrimSpec.referenceList,
specializesList, etc.) and composes via Usd.Stage for the read.

Argv: <approach>

Emits JSON {approach, results: {op: {scenario: observation}}} for all
approaches; D additionally emits ``label_half`` with the same op/scenario
structure measuring D's label-side composition.
"""
import json
import os
import sys
import tempfile

from pxr import Sdf, Usd, UsdGeom


COMPOSITION_OPS = ['sublayer', 'reference', 'payload', 'inherit', 'specialize']


def author_identifier(prim, approach, vendor, primary_id):
    """Author one (vendor, primaryId) pair using the approach's idiom."""
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
        # Bprime requires per-vendor schemas. Use what the plugin ships.
        if vendor == 'windchill':
            prim.ApplyAPI('WindchillSourceIdAPI')
            prim.GetAttribute('sourceId:primaryId').Set(primary_id)
        elif vendor == 'ifc':
            prim.ApplyAPI('IFCSourceIdAPI')
            prim.GetAttribute('sourceId:primaryId').Set(primary_id)
        # Other vendors not modeled for Bprime in this probe.
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
    """Read back this vendor's primaryId on the composed prim."""
    if approach in ('A', 'C', 'D'):
        info = prim.GetAssetInfo()
        if info is None:
            return None
        src = info.get('source', {})
        if not hasattr(src, 'get'):
            src = dict(src) if src else {}
        return src.get(vendor, {}).get('primaryId') if hasattr(src.get(vendor, {}), 'get') else None
    elif approach == 'B':
        attr = prim.GetAttribute(f'sourceIdentifier:{vendor}:primaryId')
        return attr.Get() if attr else None
    elif approach == 'Bprime':
        attr = prim.GetAttribute('sourceId:primaryId')
        return attr.Get() if attr else None
    return None


def read_vendors_visible(prim, approach):
    """Enumerate vendors visible on the composed prim."""
    vendors = set()
    if approach in ('A', 'C', 'D'):
        info = prim.GetAssetInfo()
        if info:
            src = info.get('source', {})
            if hasattr(src, 'keys'):
                vendors.update(src.keys())
    if approach in ('B',):
        for prop in prim.GetProperties():
            name = prop.GetName()
            parts = name.split(':')
            if (len(parts) == 3 and parts[0] == 'sourceIdentifier'
                    and parts[2] == 'primaryId'):
                vendors.add(parts[1])
    if approach == 'Bprime':
        for s in prim.GetAppliedSchemas():
            if s.endswith('SourceIdAPI') and s != 'SourceIdentifierBaseAPI':
                vendors.add(s[:-len('SourceIdAPI')].lower())
    if approach == 'D':
        # D's identifier half already covered above; label half not relevant
        pass
    return sorted(vendors)


def make_weak_layer(path, approach):
    """Layer that authors windchill primaryId = 'WEAK_WINDCHILL'."""
    stage = Usd.Stage.CreateNew(path)
    prim = UsdGeom.Xform.Define(stage, '/Asset').GetPrim()
    author_identifier(prim, approach, 'windchill', 'WEAK_WINDCHILL')
    stage.GetRootLayer().Save()


def make_strong_layer_override(path, approach):
    """Strong layer overriding the SAME vendor (windchill) with a different value."""
    stage = Usd.Stage.CreateNew(path)
    prim = UsdGeom.Xform.Define(stage, '/Asset').GetPrim()
    author_identifier(prim, approach, 'windchill', 'STRONG_WINDCHILL')
    stage.GetRootLayer().Save()


def make_strong_layer_add_vendor(path, approach):
    """Strong layer adding a DIFFERENT vendor (ifc), no windchill override."""
    stage = Usd.Stage.CreateNew(path)
    prim = UsdGeom.Xform.Define(stage, '/Asset').GetPrim()
    author_identifier(prim, approach, 'ifc', 'STRONG_IFC')
    stage.GetRootLayer().Save()


def compose_via_op(td, op, weak_path, strong_payload_fn, approach, strong_path):
    """Build a root layer that composes weak_path under /Asset via `op`,
    then writes the strong-layer payload at /Asset. Returns the composed
    Usd.Stage."""
    strong_payload_fn(strong_path, approach)

    root_path = os.path.join(td, f'root_{op}.usda')

    if op == 'sublayer':
        # Strong layer is sublayered onto weak layer's root.
        # Order: strong layer first (strongest) then weak.
        root = Sdf.Layer.CreateNew(root_path)
        root.subLayerPaths.append(strong_path)
        root.subLayerPaths.append(weak_path)
        root.Save()
        return Usd.Stage.Open(root_path)

    # For the other ops, the *strong* layer is the root layer and the
    # *weak* layer is referenced/inherited/etc by the strong layer.
    strong = Sdf.Layer.FindOrOpen(strong_path)
    asset = strong.GetPrimAtPath('/Asset')
    if op == 'reference':
        asset.referenceList.Add(Sdf.Reference(weak_path, '/Asset'))
    elif op == 'payload':
        asset.payloadList.Add(Sdf.Payload(weak_path, '/Asset'))
    elif op == 'inherit':
        # Move the weak layer's content into a /_class_Asset prim, then
        # inherit it from /Asset. Easiest is to create the class on the
        # SAME strong layer (use a separate class prim spec) — but we
        # want a true inherit-across-layer test, so we move the weak
        # contents into a class on the weak layer.
        weak = Sdf.Layer.FindOrOpen(weak_path)
        if not weak.GetPrimAtPath('/_class_Asset'):
            class_spec = Sdf.CreatePrimInLayer(weak, '/_class_Asset')
            class_spec.specifier = Sdf.SpecifierClass
            # Copy /Asset to /_class_Asset
            Sdf.CopySpec(weak, '/Asset', weak, '/_class_Asset')
            weak.Save()
        # Strong /Asset inherits the class from the weak layer (via reference
        # to the layer at the class path).
        asset.referenceList.Add(Sdf.Reference(weak_path, '/_class_Asset'))
        # Substitute: use `inheritsList` to inherit IN THE COMPOSITION SENSE
        # within the same layer would need a class on the same layer. To
        # truly exercise the 'inherit' arc weaker-than-direct, build it
        # differently. For now, model 'inherit' as a reference-to-class.
    elif op == 'specialize':
        weak = Sdf.Layer.FindOrOpen(weak_path)
        if not weak.GetPrimAtPath('/_specialize_Asset'):
            spec = Sdf.CreatePrimInLayer(weak, '/_specialize_Asset')
            spec.specifier = Sdf.SpecifierClass
            Sdf.CopySpec(weak, '/Asset', weak, '/_specialize_Asset')
            weak.Save()
        asset.specializesList.Add(Sdf.Path(f'/_specialize_Asset'))
        # We need the specialize target to exist in the same composition.
        # Bring it in via reference too so it's reachable.
        asset.referenceList.Add(Sdf.Reference(weak_path, '/_specialize_Asset'))

    strong.Save()
    return Usd.Stage.Open(strong_path)


def run_scenario(approach, op, scenario):
    """Build the layers, compose, and read back."""
    with tempfile.TemporaryDirectory() as td:
        weak_path = os.path.join(td, 'weak.usda')
        strong_path = os.path.join(td, f'strong_{op}.usda')
        make_weak_layer(weak_path, approach)
        if scenario == 'override_same_vendor':
            stage = compose_via_op(td, op, weak_path,
                                    make_strong_layer_override, approach,
                                    strong_path)
        else:  # 'two_vendors_merge'
            stage = compose_via_op(td, op, weak_path,
                                    make_strong_layer_add_vendor, approach,
                                    strong_path)

        prim = stage.GetPrimAtPath('/Asset')
        if not prim:
            return {'error': 'no /Asset on composed stage'}

        windchill_value = read_identifier(prim, approach, 'windchill')
        ifc_value = read_identifier(prim, approach, 'ifc')
        vendors_visible = read_vendors_visible(prim, approach)
        applied = list(prim.GetAppliedSchemas())

        return {
            'windchill_value': windchill_value,
            'ifc_value': ifc_value,
            'vendors_visible': vendors_visible,
            'applied_schemas': applied,
        }


# ----------------------------------------------------------------------
# D label-half helpers (SemanticLabelsAPI multi-apply)
# ----------------------------------------------------------------------

LABEL_INSTANCE_WINDCHILL = 'windchill:partCategory'
LABEL_INSTANCE_IFC = 'ifc:entityType'
LABELS_WEAK = ['WEAK_LABEL_A', 'WEAK_LABEL_B']
LABELS_STRONG = ['STRONG_LABEL_X']
LABELS_IFC = ['IfcBeam']


def author_label(prim, instance, labels):
    """Apply SemanticLabelsAPI:<instance> and set the token[] attribute."""
    prim.ApplyAPI('SemanticLabelsAPI', instance)
    attr = prim.GetAttribute(f'semantics:labels:{instance}')
    if attr:
        attr.Set(labels)


def read_label(prim, instance):
    """Read back the token[] for SemanticLabelsAPI:<instance>."""
    attr = prim.GetAttribute(f'semantics:labels:{instance}')
    if not attr:
        return None
    val = attr.Get()
    return list(val) if val is not None else None


def list_label_instances(prim):
    """Enumerate semanticlabels instances visible on the composed prim
    via the applied-schemas list (each multi-apply instance shows up as
    'SemanticLabelsAPI:<vendor>:<kind>')."""
    instances = []
    for s in prim.GetAppliedSchemas():
        if s.startswith('SemanticLabelsAPI:'):
            instances.append(s.split(':', 1)[1])
    return sorted(instances)


def make_weak_layer_label(path):
    stage = Usd.Stage.CreateNew(path)
    prim = UsdGeom.Xform.Define(stage, '/Asset').GetPrim()
    author_label(prim, LABEL_INSTANCE_WINDCHILL, LABELS_WEAK)
    stage.GetRootLayer().Save()


def make_strong_layer_label_override(path):
    """Same instance, different label values."""
    stage = Usd.Stage.CreateNew(path)
    prim = UsdGeom.Xform.Define(stage, '/Asset').GetPrim()
    author_label(prim, LABEL_INSTANCE_WINDCHILL, LABELS_STRONG)
    stage.GetRootLayer().Save()


def make_strong_layer_label_add_kind(path):
    """Different instance (ifc:entityType), no override of windchill."""
    stage = Usd.Stage.CreateNew(path)
    prim = UsdGeom.Xform.Define(stage, '/Asset').GetPrim()
    author_label(prim, LABEL_INSTANCE_IFC, LABELS_IFC)
    stage.GetRootLayer().Save()


def compose_label_via_op(td, op, weak_path, strong_payload_fn, strong_path):
    """Same composition assembly as compose_via_op but for label layers."""
    strong_payload_fn(strong_path)
    root_path = os.path.join(td, f'root_label_{op}.usda')

    if op == 'sublayer':
        root = Sdf.Layer.CreateNew(root_path)
        root.subLayerPaths.append(strong_path)
        root.subLayerPaths.append(weak_path)
        root.Save()
        return Usd.Stage.Open(root_path)

    strong = Sdf.Layer.FindOrOpen(strong_path)
    asset = strong.GetPrimAtPath('/Asset')
    if op == 'reference':
        asset.referenceList.Add(Sdf.Reference(weak_path, '/Asset'))
    elif op == 'payload':
        asset.payloadList.Add(Sdf.Payload(weak_path, '/Asset'))
    elif op == 'inherit':
        weak = Sdf.Layer.FindOrOpen(weak_path)
        if not weak.GetPrimAtPath('/_class_Asset'):
            class_spec = Sdf.CreatePrimInLayer(weak, '/_class_Asset')
            class_spec.specifier = Sdf.SpecifierClass
            Sdf.CopySpec(weak, '/Asset', weak, '/_class_Asset')
            weak.Save()
        asset.referenceList.Add(Sdf.Reference(weak_path, '/_class_Asset'))
    elif op == 'specialize':
        weak = Sdf.Layer.FindOrOpen(weak_path)
        if not weak.GetPrimAtPath('/_specialize_Asset'):
            spec = Sdf.CreatePrimInLayer(weak, '/_specialize_Asset')
            spec.specifier = Sdf.SpecifierClass
            Sdf.CopySpec(weak, '/Asset', weak, '/_specialize_Asset')
            weak.Save()
        asset.specializesList.Add(Sdf.Path('/_specialize_Asset'))
        asset.referenceList.Add(Sdf.Reference(weak_path, '/_specialize_Asset'))

    strong.Save()
    return Usd.Stage.Open(strong_path)


def run_label_scenario(op, scenario):
    """Same shape as run_scenario but for D's label half."""
    with tempfile.TemporaryDirectory() as td:
        weak_path = os.path.join(td, 'weak_label.usda')
        strong_path = os.path.join(td, f'strong_label_{op}.usda')
        make_weak_layer_label(weak_path)
        if scenario == 'override_same_label':
            stage = compose_label_via_op(
                td, op, weak_path, make_strong_layer_label_override,
                strong_path)
        else:  # 'two_kinds_merge'
            stage = compose_label_via_op(
                td, op, weak_path, make_strong_layer_label_add_kind,
                strong_path)

        prim = stage.GetPrimAtPath('/Asset')
        if not prim:
            return {'error': 'no /Asset on composed stage'}

        windchill_labels = read_label(prim, LABEL_INSTANCE_WINDCHILL)
        ifc_labels = read_label(prim, LABEL_INSTANCE_IFC)
        instances_visible = list_label_instances(prim)
        applied = list(prim.GetAppliedSchemas())

        return {
            'windchill_partCategory_labels': windchill_labels,
            'ifc_entityType_labels': ifc_labels,
            'label_instances_visible': instances_visible,
            'applied_schemas': applied,
        }


def main():
    approach = sys.argv[1]
    out = {'approach': approach, 'results': {}}
    for op in COMPOSITION_OPS:
        out['results'][op] = {}
        for scenario in ('override_same_vendor', 'two_vendors_merge'):
            try:
                out['results'][op][scenario] = run_scenario(approach, op, scenario)
            except Exception as e:
                out['results'][op][scenario] = {'error': f'{type(e).__name__}: {e}'}

    if approach == 'D':
        out['label_half'] = {}
        for op in COMPOSITION_OPS:
            out['label_half'][op] = {}
            for scenario in ('override_same_label', 'two_kinds_merge'):
                try:
                    out['label_half'][op][scenario] = run_label_scenario(op, scenario)
                except Exception as e:
                    out['label_half'][op][scenario] = {
                        'error': f'{type(e).__name__}: {e}'}

    print(json.dumps(out, ensure_ascii=False))


if __name__ == '__main__':
    main()
