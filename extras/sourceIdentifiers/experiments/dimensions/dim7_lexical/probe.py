"""Dim 7 probe — vendor-name lexical scope per approach.

The vendor name is the operational unit of the vendor-extension paradigm
the proposal is built around (PR #105 Principle 3: vendor extensibility,
plus OQ5: namespacing of identifiers). This probe records, per approach,
what character classes the approach's vendor slot can carry, and what
the failure mode is when it can't.

Per approach, the slot is:
  - A             : assetInfo.source.<vendor> dict key (runtime only)
  - B             : ApplyAPI instance name + property segment
                    (sourceIdentifier:<vendor>:primaryId)
  - Bprime        : per-vendor schema CLASS NAME (authoring time)
  - C             : ApplyAPI instance name (bridge unimplemented;
                    storage shape reduces to A)
  - D-identifier  : assetInfo.source.<vendor> dict key (same as A)
  - D-label       : ApplyAPI instance + property segment
                    (semantics:labels:<vendor>:<labelKind>:labels)

D has TWO vendor slots; we probe both and record each row.

Argv: <approach>

Emits JSON {approach, slot_kind, by_value: {label: {observation}}}.
"""
import json
import sys

from pxr import Sdf, Tf, Usd, UsdGeom


PROBES = [
    ('ascii_baseline', 'autodesk'),
    ('underscore', 'auto_desk'),
    ('hyphen', 'auto-desk'),
    ('space', 'Auto Desk'),
    ('leading_digit', '123industries'),
    ('dot', 'siemens.nx'),
    ('colon', 'siemens:nx'),
    ('slash', 'siemens/nx'),
    ('unicode_letter', 'ünicode'),
]


def probe_dict_slot(vendor):
    """A/C/D-identifier — vendor lives as a VtDictionary key under
    assetInfo.source.<vendor>. No ApplyAPI step gates the vendor name."""
    stage = Usd.Stage.CreateInMemory()
    prim = UsdGeom.Xform.Define(stage, '/Asset').GetPrim()
    result = {
        'slot': 'dict_key',
        'apply_succeeded': None,  # no apply step for the vendor itself
        'authoring_succeeded': None,
        'round_trips': None,
    }
    try:
        prim.SetAssetInfoByKey('source', {vendor: {'primaryId': 'X'}})
        info = prim.GetAssetInfo()
        result['authoring_succeeded'] = vendor in info.get('source', {})

        usda = stage.GetRootLayer().ExportToString()
        stage2 = Usd.Stage.CreateInMemory()
        stage2.GetRootLayer().ImportFromString(usda)
        info2 = stage2.GetPrimAtPath('/Asset').GetAssetInfo()
        result['round_trips'] = vendor in info2.get('source', {})
    except Exception as e:
        result['error'] = f'{type(e).__name__}: {e}'
    return result


def probe_b_property_slot(test_vendor, schema_name, prop_prefix, value_prop,
                          value_type, instance_name=None):
    """B / D-label — vendor is an ApplyAPI instance name segment AND a
    property name segment. Apply is permissive; property name must satisfy
    Sdf.Path.IsValidNamespacedIdentifier per segment.

    ``test_vendor`` is the variable under test (the lexical content the
    vendor would write). ``instance_name`` is what we actually pass to
    ApplyAPI; defaults to test_vendor. D-label uses
    instance_name = f'{test_vendor}:<labelKind>' because Matt's design
    encodes vendor + labelKind in the instance.

    Silent renamespace signals on whether the *test_vendor* segment
    contains unintended structural characters (colon = extra namespace
    segment, dot = invalid in identifier), not on the combined instance
    string."""
    stage = Usd.Stage.CreateInMemory()
    prim = UsdGeom.Xform.Define(stage, '/Asset').GetPrim()
    instance = instance_name if instance_name is not None else test_vendor
    result = {
        'slot': 'apply_instance_and_property',
        'test_vendor': test_vendor,
        'apply_instance': instance,
        'apply_succeeded': None,
        'authoring_succeeded': None,
        'round_trips': None,
        'silent_renamespace': None,
        'expected_prop_name': f'{prop_prefix}:{instance}:{value_prop}',
    }
    try:
        applied = prim.ApplyAPI(schema_name, instance)
        result['apply_succeeded'] = bool(applied)
        if applied:
            result['applied_schemas'] = list(prim.GetAppliedSchemas())
        else:
            return result

        propname = result['expected_prop_name']
        try:
            attr = prim.CreateAttribute(propname, value_type)
            test_val = ['TEST'] if value_type == Sdf.ValueTypeNames.TokenArray else 'TEST'
            attr.Set(test_val)
            recovered = attr.Get()
            recovered_list = list(recovered) if value_type == Sdf.ValueTypeNames.TokenArray else recovered
            result['authoring_succeeded'] = recovered_list == test_val
        except Exception as e:
            result['authoring_succeeded'] = False
            result['authoring_error'] = f'{type(e).__name__}: {e}'

        usda = stage.GetRootLayer().ExportToString()
        stage2 = Usd.Stage.CreateInMemory()
        stage2.GetRootLayer().ImportFromString(usda)
        prim2 = stage2.GetPrimAtPath('/Asset')

        applied2 = list(prim2.GetAppliedSchemas())
        expected_apply = f'{schema_name}:{instance}'
        result['round_trip_applied_schemas'] = applied2

        # Silent renamespace: the *test_vendor* segment contains a colon,
        # which Sdf will parse into extra namespace segments — yielding a
        # property path with more segments than the schema template intends.
        # (For D-label, the labelKind colon is part of the template and
        # does NOT count; only colons inside test_vendor itself do.)
        result['silent_renamespace'] = ':' in test_vendor

        result['round_trips'] = (
            expected_apply in applied2
            and result['authoring_succeeded'] is True
            and not result['silent_renamespace'])
    except Exception as e:
        result['error'] = f'{type(e).__name__}: {e}'
    return result


def probe_bprime_class_slot(vendor):
    """Bprime — vendor is encoded in the schema CLASS NAME. This is an
    authoring-time constraint enforced at .usda parse time (prim-name
    rules) and at usdGenSchema time (Tf.IsValidIdentifier). At runtime,
    nothing happens — the schema is either registered or not.

    We probe synthetically:
      - tf_isvalid_identifier on the class name we'd construct
      - sdf_isvalid_namespaced on the class name (parser gate)
    """
    class_name = f'{vendor}SourceIdAPI'
    return {
        'slot': 'schema_class_name',
        'apply_succeeded': None,
        'authoring_succeeded': None,
        'class_name_under_test': class_name,
        'tf_isvalid_identifier': bool(Tf.IsValidIdentifier(class_name)),
        'sdf_isvalid_identifier_class_name': bool(
            Sdf.Path.IsValidIdentifier(class_name)),
        'note': ('class-name validity is the gate; runtime apply not '
                 'applicable until a per-vendor schema is registered'),
    }


def main():
    approach = sys.argv[1]
    out = {'approach': approach, 'by_value': {}}

    for label, vendor in PROBES:
        if approach in ('A',):
            out['by_value'][label] = probe_dict_slot(vendor)
            out['slot_kind'] = 'dict_key'
        elif approach == 'C':
            out['by_value'][label] = probe_dict_slot(vendor)
            out['slot_kind'] = 'dict_key (apply-instance also permissive; bridge unimplemented)'
        elif approach == 'B':
            out['by_value'][label] = probe_b_property_slot(
                vendor, 'SourceIdentifierAPI', 'sourceIdentifier',
                'primaryId', Sdf.ValueTypeNames.String)
            out['slot_kind'] = 'apply_instance_and_property'
        elif approach == 'Bprime':
            out['by_value'][label] = probe_bprime_class_slot(vendor)
            out['slot_kind'] = 'schema_class_name'
        elif approach == 'D':
            # D has TWO slots; probe both and present them as nested rows.
            # For the label slot, Matt's design encodes vendor + labelKind
            # in the instance name (e.g. 'autodesk:partCategory'). The
            # labelKind colon is part of the template; only colons inside
            # *test_vendor* count as silent renamespace.
            out['by_value'][label] = {
                'identifier_slot': probe_dict_slot(vendor),
                'label_slot': probe_b_property_slot(
                    test_vendor=vendor,
                    schema_name='SemanticLabelsAPI',
                    prop_prefix='semantics:labels',
                    value_prop='labels',
                    value_type=Sdf.ValueTypeNames.TokenArray,
                    instance_name=f'{vendor}:material'),
            }
            out['slot_kind'] = 'split (identifier: dict_key; labels: apply_instance_and_property)'
        else:
            out['by_value'][label] = {'error': f'unknown approach {approach}'}

    print(json.dumps(out, ensure_ascii=False))


if __name__ == '__main__':
    main()
