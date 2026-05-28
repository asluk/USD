"""Approach D (Matt Kuruc's semantic labels) — Split-by-concern.

Two schemas, applied independently:
  1. SourceIdentifiersAPI (single-apply, A-style) for identifiers
  2. SemanticLabelsAPI (multi-apply, B-style) for vendor labels

Verifies that:
1. Both schemas register.
2. The identifier half behaves exactly like A (same shape).
3. The labels half works as multi-apply with nested instance names
   like 'windchill:partCategory' producing token[] properties at
   'semantics:labels:windchill:partCategory'.
4. Both schemas coexist on one prim without conflict.
5. Multi-segment instance names work (the colon-in-instance is
   D's design choice per Matt's strawman).
"""

import os
import unittest

_THIS = os.path.dirname(os.path.abspath(__file__))
_SCHEMA_DIR = os.path.dirname(_THIS)
os.environ['PXR_PLUGINPATH_NAME'] = _SCHEMA_DIR

from pxr import Usd, UsdGeom, Vt


class TestApproachD(unittest.TestCase):

    def test_both_schemas_registered(self):
        reg = Usd.SchemaRegistry()
        # Identifier half is single-apply -> registry has prim def
        self.assertIsNotNone(reg.FindAppliedAPIPrimDefinition('SourceIdentifiersAPI'))
        # Labels half is multi-apply -> check via IsMultipleApplyAPISchema
        self.assertTrue(reg.IsMultipleApplyAPISchema('SemanticLabelsAPI'),
            "SemanticLabelsAPI must be registered as multi-apply.")

    def test_identifier_half_like_A(self):
        """SourceIdentifiersAPI (D's id half) behaves like Approach A:
        no properties, assetInfo.source.<vendor> dict is the contract."""
        stage = Usd.Stage.CreateInMemory()
        prim = UsdGeom.Xform.Define(stage, '/Asset').GetPrim()
        prim.ApplyAPI('SourceIdentifiersAPI')

        prim.SetAssetInfoByKey('source', {
            'windchill': {
                'primaryId': 'OR:wt.part.WTPart:4697800',
                'revision': 'Rev.C',
            }
        })

        self.assertEqual(
            prim.GetAssetInfoByKey('source')['windchill']['primaryId'],
            'OR:wt.part.WTPart:4697800')

    def test_labels_half_multi_apply(self):
        stage = Usd.Stage.CreateInMemory()
        prim = UsdGeom.Xform.Define(stage, '/Asset').GetPrim()

        prim.ApplyAPI('SemanticLabelsAPI', 'windchill:partCategory')
        self.assertIn('SemanticLabelsAPI:windchill:partCategory',
                      prim.GetAppliedSchemas())

        prop_names = set(p.GetName() for p in prim.GetProperties())
        self.assertIn('semantics:labels:windchill:partCategory', prop_names,
            "Multi-segment instance name 'windchill:partCategory' should "
            "produce a property at 'semantics:labels:windchill:partCategory'.")

    def test_labels_round_trip(self):
        stage = Usd.Stage.CreateInMemory()
        prim = UsdGeom.Xform.Define(stage, '/Asset').GetPrim()
        prim.ApplyAPI('SemanticLabelsAPI', 'windchill:partCategory')

        attr = prim.GetAttribute('semantics:labels:windchill:partCategory')
        self.assertIsNotNone(attr)
        attr.Set(Vt.TokenArray(['Frame', 'Structural', 'Load-Bearing']))

        result = list(attr.Get())
        self.assertEqual(result, ['Frame', 'Structural', 'Load-Bearing'])

    def test_multiple_label_kinds(self):
        """A prim can carry labels in multiple taxonomies — one per
        SemanticLabelsAPI instance."""
        stage = Usd.Stage.CreateInMemory()
        prim = UsdGeom.Xform.Define(stage, '/Asset').GetPrim()

        prim.ApplyAPI('SemanticLabelsAPI', 'windchill:partCategory')
        prim.ApplyAPI('SemanticLabelsAPI', 'ifc:entityType')
        prim.ApplyAPI('SemanticLabelsAPI', 'simready:objectClass')

        applied = prim.GetAppliedSchemas()
        self.assertIn('SemanticLabelsAPI:windchill:partCategory', applied)
        self.assertIn('SemanticLabelsAPI:ifc:entityType', applied)
        self.assertIn('SemanticLabelsAPI:simready:objectClass', applied)

        prim.GetAttribute('semantics:labels:windchill:partCategory').Set(
            Vt.TokenArray(['Frame']))
        prim.GetAttribute('semantics:labels:ifc:entityType').Set(
            Vt.TokenArray(['IfcBeam']))
        prim.GetAttribute('semantics:labels:simready:objectClass').Set(
            Vt.TokenArray(['Conveyor', 'Movable']))

        self.assertEqual(
            list(prim.GetAttribute('semantics:labels:ifc:entityType').Get()),
            ['IfcBeam'])

    def test_two_halves_coexist(self):
        """D's defining property: identifiers and labels apply to the same
        prim without interference (split-by-concern)."""
        stage = Usd.Stage.CreateInMemory()
        prim = UsdGeom.Xform.Define(stage, '/Asset').GetPrim()

        # Identifier half (A-style)
        prim.ApplyAPI('SourceIdentifiersAPI')
        prim.SetAssetInfoByKey('source', {
            'windchill': {'primaryId': 'OR:wt.part.WTPart:4697800'}
        })

        # Label half (B-style multi-apply)
        prim.ApplyAPI('SemanticLabelsAPI', 'windchill:partCategory')
        prim.GetAttribute('semantics:labels:windchill:partCategory').Set(
            Vt.TokenArray(['Frame', 'Structural']))

        # Both visible together
        applied = prim.GetAppliedSchemas()
        self.assertIn('SourceIdentifiersAPI', applied)
        self.assertIn('SemanticLabelsAPI:windchill:partCategory', applied)

        # Identifier dict round-trip
        self.assertEqual(
            prim.GetAssetInfoByKey('source')['windchill']['primaryId'],
            'OR:wt.part.WTPart:4697800')

        # Labels round-trip
        self.assertEqual(
            list(prim.GetAttribute('semantics:labels:windchill:partCategory').Get()),
            ['Frame', 'Structural'])

    def test_usda_round_trip_both_halves(self):
        stage = Usd.Stage.CreateInMemory()
        prim = UsdGeom.Xform.Define(stage, '/Asset').GetPrim()
        prim.ApplyAPI('SourceIdentifiersAPI')
        prim.ApplyAPI('SemanticLabelsAPI', 'windchill:partCategory')
        prim.SetAssetInfoByKey('source', {'windchill': {'primaryId': 'X'}})
        prim.GetAttribute('semantics:labels:windchill:partCategory').Set(
            Vt.TokenArray(['Frame']))

        usda = stage.GetRootLayer().ExportToString()
        stage2 = Usd.Stage.CreateInMemory()
        stage2.GetRootLayer().ImportFromString(usda)
        prim2 = stage2.GetPrimAtPath('/Asset')

        self.assertEqual(prim2.GetAssetInfoByKey('source')['windchill']['primaryId'], 'X')
        self.assertEqual(
            list(prim2.GetAttribute('semantics:labels:windchill:partCategory').Get()),
            ['Frame'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
