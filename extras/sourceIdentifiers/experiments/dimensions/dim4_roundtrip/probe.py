"""Dim 4 probe — round-trip fidelity of identifier VALUES through .usda
and .usdc.

For each approach, set a primary identifier to each test value, export
the layer to .usda and .usdc, re-import, and byte-compare the recovered
value to the original.

Argv: <approach>

Emits JSON {approach, by_value: {label: {usda: bool, usdc: bool, ...}}}.
"""
import json
import os
import sys
import tempfile

from pxr import Sdf, Usd, UsdGeom


# Test values — each labelled. Picked to exercise characters that would
# be invalid in USD prim names but should pass through string values.
TEST_VALUES = [
    ('ascii_simple', 'OR:wt.part.WTPart:4697800'),
    ('slashes', 'file/path/to/part'),
    ('with_space', 'a value with spaces'),
    ('unicode', 'ünicödé'),
    ('cyrillic', 'файл'),
    ('newline_tab', 'line1\nline2\tcol'),
    ('escaped_quote', 'has "quotes" inside'),
    ('ifc_globalid', 'Bs43BRT3PrSvZ0KshZJRhD'),
    ('colons', 'urn:adobe:sub3d:1:2:3'),
    ('empty', ''),
]


def set_identifier(prim, approach, value):
    """Author the identifier value for one approach + one vendor (windchill)."""
    if approach in ('A', 'C', 'D'):
        # Storage is assetInfo.source.<vendor>.primaryId
        if approach == 'A':
            prim.ApplyAPI('SourceIdentifiersAPI')
        elif approach == 'C':
            prim.ApplyAPI('SourceIdentifierBridgeAPI', 'windchill')
        else:  # D
            prim.ApplyAPI('SourceIdentifiersAPI')
        prim.SetAssetInfoByKey('source',
            {'windchill': {'primaryId': value}})
    elif approach == 'B':
        prim.ApplyAPI('SourceIdentifierAPI', 'windchill')
        prim.GetAttribute('sourceIdentifier:windchill:primaryId').Set(value)
    elif approach == 'Bprime':
        prim.ApplyAPI('WindchillSourceIdAPI')
        prim.GetAttribute('sourceId:primaryId').Set(value)
    else:
        raise ValueError(f'unknown approach {approach}')


def get_identifier(prim, approach):
    """Read the identifier back."""
    if approach in ('A', 'C', 'D'):
        info = prim.GetAssetInfo()
        return info.get('source', {}).get('windchill', {}).get('primaryId')
    elif approach == 'B':
        return prim.GetAttribute('sourceIdentifier:windchill:primaryId').Get()
    elif approach == 'Bprime':
        return prim.GetAttribute('sourceId:primaryId').Get()
    raise ValueError(f'unknown approach {approach}')


def round_trip(approach, value, fmt):
    """Author -> export -> reimport -> compare. Returns dict with pass + details."""
    with tempfile.TemporaryDirectory() as td:
        path = os.path.join(td, f'asset.{fmt}')

        stage = Usd.Stage.CreateNew(path)
        prim = UsdGeom.Xform.Define(stage, '/Asset').GetPrim()
        try:
            set_identifier(prim, approach, value)
        except Exception as e:
            return {'pass': False, 'set_failed': True, 'error': str(e)}
        stage.GetRootLayer().Save()

        stage2 = Usd.Stage.Open(path)
        prim2 = stage2.GetPrimAtPath('/Asset')
        if not prim2:
            return {'pass': False, 'reopen_failed': True}
        try:
            recovered = get_identifier(prim2, approach)
        except Exception as e:
            return {'pass': False, 'get_failed': True, 'error': str(e)}
        return {
            'pass': recovered == value,
            'recovered': recovered if recovered != value else '__match__',
            'recovered_type': type(recovered).__name__,
        }


def main():
    approach = sys.argv[1]
    by_value = {}
    for label, value in TEST_VALUES:
        by_value[label] = {
            'value_repr': repr(value),
            'usda': round_trip(approach, value, 'usda'),
            'usdc': round_trip(approach, value, 'usdc'),
        }
    print(json.dumps({'approach': approach, 'by_value': by_value}))


if __name__ == '__main__':
    main()
