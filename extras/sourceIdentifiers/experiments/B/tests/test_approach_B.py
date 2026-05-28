"""Approach B — SourceIdentifierAPI multi-apply with typed properties.

Verifies that:
1. Schema registers with SchemaRegistry (codeless).
2. Multi-apply with instance names works (sourceIdentifier:<vendor>:*).
3. Typed properties round-trip via attribute Set/Get.
4. Multiple instances on one prim coexist.
5. Round-trip through usda text.
"""

import os
import unittest

_THIS = os.path.dirname(os.path.abspath(__file__))
_SCHEMA_DIR = os.path.dirname(_THIS)
os.environ['PXR_PLUGINPATH_NAME'] = _SCHEMA_DIR

from pxr import Usd, UsdGeom, Sdf


class TestApproachB(unittest.TestCase):

    def test_schema_registered(self):
        registry = Usd.SchemaRegistry()
        # Multi-apply: the schema type is registered; we verify via the
        # multi-apply-specific accessor (FindAppliedAPIPrimDefinition is
        # only meaningful for single-apply / instantiated schemas).
        self.assertTrue(registry.IsMultipleApplyAPISchema('SourceIdentifierAPI'),
            "SourceIdentifierAPI must be registered as a multi-apply schema.")

    def test_apply_with_instance_name(self):
        stage = Usd.Stage.CreateInMemory()
        prim = UsdGeom.Xform.Define(stage, '/Asset').GetPrim()
        self.assertTrue(prim.ApplyAPI('SourceIdentifierAPI', 'windchill'))
        self.assertIn('SourceIdentifierAPI:windchill', prim.GetAppliedSchemas())

    def test_properties_namespaced_by_instance(self):
        stage = Usd.Stage.CreateInMemory()
        prim = UsdGeom.Xform.Define(stage, '/Asset').GetPrim()
        prim.ApplyAPI('SourceIdentifierAPI', 'windchill')

        # Properties: sourceIdentifier:windchill:{primaryId,revision,domain,label}
        prop_names = [p.GetName() for p in prim.GetProperties()]
        self.assertIn('sourceIdentifier:windchill:primaryId', prop_names)
        self.assertIn('sourceIdentifier:windchill:revision', prop_names)
        self.assertIn('sourceIdentifier:windchill:domain', prop_names)
        self.assertIn('sourceIdentifier:windchill:label', prop_names)

    def test_property_round_trip(self):
        stage = Usd.Stage.CreateInMemory()
        prim = UsdGeom.Xform.Define(stage, '/Asset').GetPrim()
        prim.ApplyAPI('SourceIdentifierAPI', 'windchill')

        prim.GetAttribute('sourceIdentifier:windchill:primaryId').Set('OR:wt.part.WTPart:4697800')
        prim.GetAttribute('sourceIdentifier:windchill:revision').Set('Rev.C')
        prim.GetAttribute('sourceIdentifier:windchill:domain').Set('com.ptc.windchill')

        self.assertEqual(prim.GetAttribute('sourceIdentifier:windchill:primaryId').Get(),
                         'OR:wt.part.WTPart:4697800')
        self.assertEqual(prim.GetAttribute('sourceIdentifier:windchill:domain').Get(),
                         'com.ptc.windchill')

    def test_multiple_instances(self):
        """One prim can carry identifiers from multiple external systems."""
        stage = Usd.Stage.CreateInMemory()
        prim = UsdGeom.Xform.Define(stage, '/Asset').GetPrim()
        prim.ApplyAPI('SourceIdentifierAPI', 'windchill')
        prim.ApplyAPI('SourceIdentifierAPI', 'ifc')
        prim.ApplyAPI('SourceIdentifierAPI', 'adobe')

        applied = prim.GetAppliedSchemas()
        self.assertIn('SourceIdentifierAPI:windchill', applied)
        self.assertIn('SourceIdentifierAPI:ifc', applied)
        self.assertIn('SourceIdentifierAPI:adobe', applied)

        prim.GetAttribute('sourceIdentifier:windchill:primaryId').Set('W1')
        prim.GetAttribute('sourceIdentifier:ifc:primaryId').Set('Bs43BRT3PrSvZ0KshZJRhD')
        prim.GetAttribute('sourceIdentifier:adobe:primaryId').Set('urn:adobe:sub3d:1')

        # All three coexist without interference
        self.assertEqual(prim.GetAttribute('sourceIdentifier:windchill:primaryId').Get(), 'W1')
        self.assertEqual(prim.GetAttribute('sourceIdentifier:ifc:primaryId').Get(),
                         'Bs43BRT3PrSvZ0KshZJRhD')

    def test_default_value_empty_string(self):
        """Unauthored properties return the schema fallback (empty string)."""
        stage = Usd.Stage.CreateInMemory()
        prim = UsdGeom.Xform.Define(stage, '/Asset').GetPrim()
        prim.ApplyAPI('SourceIdentifierAPI', 'ifc')
        # IFC GlobalId set, but no revision authored
        prim.GetAttribute('sourceIdentifier:ifc:primaryId').Set('Bs43BRT3PrSvZ0KshZJRhD')
        # Fallback should be empty string for revision
        self.assertEqual(prim.GetAttribute('sourceIdentifier:ifc:revision').Get(), '')

    def test_usda_round_trip(self):
        stage = Usd.Stage.CreateInMemory()
        prim = UsdGeom.Xform.Define(stage, '/Asset').GetPrim()
        prim.ApplyAPI('SourceIdentifierAPI', 'windchill')
        prim.GetAttribute('sourceIdentifier:windchill:primaryId').Set('X')

        usda = stage.GetRootLayer().ExportToString()
        self.assertIn('SourceIdentifierAPI:windchill', usda)
        self.assertIn('sourceIdentifier:windchill:primaryId', usda)

        stage2 = Usd.Stage.CreateInMemory()
        stage2.GetRootLayer().ImportFromString(usda)
        prim2 = stage2.GetPrimAtPath('/Asset')
        self.assertEqual(prim2.GetAttribute('sourceIdentifier:windchill:primaryId').Get(), 'X')


if __name__ == '__main__':
    unittest.main(verbosity=2)
