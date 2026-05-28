"""Approach A — SourceIdentifiersAPI (single-apply, no properties).

Verifies that:
1. Schema registers with SchemaRegistry (codeless schema discoverable).
2. Schema applies to a prim.
3. assetInfo.source.<vendor>.{primaryId, revision, metadata} round-trips
   through SetAssetInfoByKey / GetAssetInfo.
4. Round-trip through usda text serialization preserves the dict shape.

A defines no properties; storage lives entirely in assetInfo metadata.
"""

import os
import sys
import unittest

# Set plugin path BEFORE importing pxr so Plug.Registry sees this schema only.
_THIS = os.path.dirname(os.path.abspath(__file__))
_SCHEMA_DIR = os.path.dirname(_THIS)
os.environ['PXR_PLUGINPATH_NAME'] = _SCHEMA_DIR

from pxr import Usd, UsdGeom, Sdf, Vt


class TestApproachA(unittest.TestCase):

    def test_schema_registered(self):
        registry = Usd.SchemaRegistry()
        api_def = registry.FindAppliedAPIPrimDefinition('SourceIdentifiersAPI')
        self.assertIsNotNone(api_def,
            "SourceIdentifiersAPI must be findable in SchemaRegistry "
            "(plugInfo.json + generatedSchema.usda discovered).")

    def test_apply_schema_to_prim(self):
        stage = Usd.Stage.CreateInMemory()
        prim = UsdGeom.Xform.Define(stage, '/Asset').GetPrim()
        self.assertTrue(prim.ApplyAPI('SourceIdentifiersAPI'),
            "Single-apply schema applies without an instance name.")
        self.assertIn('SourceIdentifiersAPI', prim.GetAppliedSchemas())

    def test_assetInfo_round_trip(self):
        stage = Usd.Stage.CreateInMemory()
        prim = UsdGeom.Xform.Define(stage, '/Asset').GetPrim()
        prim.ApplyAPI('SourceIdentifiersAPI')

        # Author the A-shape: assetInfo.source.windchill.{primaryId, revision, metadata}
        source = {
            'windchill': {
                'primaryId': 'OR:wt.part.WTPart:4697800',
                'revision': 'Rev.C',
                'metadata': {
                    'navigationCriteria': 'OR:wt.filter.NavigationCriteria:7608531',
                    'displayNumber': 'A-0000-12345',
                }
            }
        }
        prim.SetAssetInfoByKey('source', source)

        # Read it back
        read = prim.GetAssetInfoByKey('source')
        self.assertEqual(read['windchill']['primaryId'], 'OR:wt.part.WTPart:4697800')
        self.assertEqual(read['windchill']['revision'], 'Rev.C')
        self.assertEqual(read['windchill']['metadata']['displayNumber'], 'A-0000-12345')

    def test_multiple_vendors_per_prim(self):
        """Per PR #105 emerging consensus: multiple systems per prim."""
        stage = Usd.Stage.CreateInMemory()
        prim = UsdGeom.Xform.Define(stage, '/Asset').GetPrim()
        prim.ApplyAPI('SourceIdentifiersAPI')

        prim.SetAssetInfoByKey('source', {
            'windchill': {'primaryId': 'OR:wt.part.WTPart:4697800'},
            'ifc':       {'primaryId': 'Bs43BRT3PrSvZ0KshZJRhD'},
            'adobe':     {'primaryId': 'urn:adobe:sub3d:00000001'},
        })

        source = prim.GetAssetInfoByKey('source')
        self.assertEqual(set(source.keys()), {'windchill', 'ifc', 'adobe'})
        self.assertEqual(source['ifc']['primaryId'], 'Bs43BRT3PrSvZ0KshZJRhD')

    def test_usda_text_round_trip(self):
        """Verify the dict survives serialization to usda text."""
        stage = Usd.Stage.CreateInMemory()
        prim = UsdGeom.Xform.Define(stage, '/Asset').GetPrim()
        prim.ApplyAPI('SourceIdentifiersAPI')
        prim.SetAssetInfoByKey('source', {
            'windchill': {'primaryId': 'X', 'revision': 'v1'}
        })

        usda = stage.GetRootLayer().ExportToString()
        self.assertIn('SourceIdentifiersAPI', usda)
        self.assertIn('windchill', usda)
        self.assertIn('OR:wt.part.WTPart:', usda) if False else self.assertIn('"X"', usda)

        # Reload it
        stage2 = Usd.Stage.CreateInMemory()
        stage2.GetRootLayer().ImportFromString(usda)
        prim2 = stage2.GetPrimAtPath('/Asset')
        self.assertIn('SourceIdentifiersAPI', prim2.GetAppliedSchemas())
        source = prim2.GetAssetInfoByKey('source')
        self.assertEqual(source['windchill']['primaryId'], 'X')
        self.assertEqual(source['windchill']['revision'], 'v1')

    def test_no_properties_introduced(self):
        """A intentionally defines no properties. Verify."""
        registry = Usd.SchemaRegistry()
        api_def = registry.FindAppliedAPIPrimDefinition('SourceIdentifiersAPI')
        props = api_def.GetPropertyNames()
        self.assertEqual(list(props), [],
            "Approach A schema must declare zero properties "
            "(precedent: UsdMediaAssetPreviewsAPI). Found: %s" % list(props))


if __name__ == '__main__':
    unittest.main(verbosity=2)
