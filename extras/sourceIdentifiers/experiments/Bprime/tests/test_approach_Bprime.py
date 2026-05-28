"""Approach B' — Single-apply base + per-vendor single-applies.

Verifies that:
1. All three schemas (base + Windchill + IFC) register.
2. Vendor schemas, when applied, also bring base properties (via
   'prepend apiSchemas = ["SourceIdentifierBaseAPI"]').
3. Vendor-specific properties exist alongside base properties.
4. Each vendor's schema applies independently to different prims.

EXPERIMENTAL FINDING captured in schema.usda docstring: USD's schema
language does NOT allow direct inheritance among applied schemas (i.e.
'inherits = </SourceIdentifierBaseAPI>' fails usdGenSchema validation).
The 'prepend apiSchemas' workaround is the closest USD-native expression
of PR #105's B' variant.
"""

import os
import unittest

_THIS = os.path.dirname(os.path.abspath(__file__))
_SCHEMA_DIR = os.path.dirname(_THIS)
os.environ['PXR_PLUGINPATH_NAME'] = _SCHEMA_DIR

from pxr import Usd, UsdGeom


class TestApproachBprime(unittest.TestCase):

    def test_three_schemas_registered(self):
        reg = Usd.SchemaRegistry()
        self.assertIsNotNone(reg.FindAppliedAPIPrimDefinition('SourceIdentifierBaseAPI'))
        self.assertIsNotNone(reg.FindAppliedAPIPrimDefinition('WindchillSourceIdAPI'))
        self.assertIsNotNone(reg.FindAppliedAPIPrimDefinition('IFCSourceIdAPI'))

    def test_base_schema_alone(self):
        """Base schema applies; provides only the common fields."""
        stage = Usd.Stage.CreateInMemory()
        prim = UsdGeom.Xform.Define(stage, '/Asset').GetPrim()
        prim.ApplyAPI('SourceIdentifierBaseAPI')

        prop_names = set(p.GetName() for p in prim.GetProperties())
        self.assertIn('sourceId:primaryId', prop_names)
        self.assertIn('sourceId:revision', prop_names)
        # No vendor-specific props on plain base
        self.assertNotIn('sourceId:windchill:navigationCriteria', prop_names)
        self.assertNotIn('sourceId:ifc:ifcType', prop_names)

    def test_windchill_brings_base_via_prepend(self):
        """Applying WindchillSourceIdAPI should also include base properties
        because schema.usda declares 'prepend apiSchemas = [\"SourceIdentifierBaseAPI\"]'.
        """
        stage = Usd.Stage.CreateInMemory()
        prim = UsdGeom.Xform.Define(stage, '/Asset').GetPrim()
        prim.ApplyAPI('WindchillSourceIdAPI')

        applied = prim.GetAppliedSchemas()
        self.assertIn('WindchillSourceIdAPI', applied)
        # 'prepend apiSchemas' brings the base schema into the applied list
        self.assertIn('SourceIdentifierBaseAPI', applied,
            "B' uses 'prepend apiSchemas' to include base behavior; "
            "applied schema list should include SourceIdentifierBaseAPI.")

        prop_names = set(p.GetName() for p in prim.GetProperties())
        # Base props
        self.assertIn('sourceId:primaryId', prop_names)
        self.assertIn('sourceId:revision', prop_names)
        # Vendor-specific props
        self.assertIn('sourceId:windchill:navigationCriteria', prop_names)
        self.assertIn('sourceId:windchill:displayNumber', prop_names)

    def test_ifc_brings_base_via_prepend(self):
        stage = Usd.Stage.CreateInMemory()
        prim = UsdGeom.Xform.Define(stage, '/Asset').GetPrim()
        prim.ApplyAPI('IFCSourceIdAPI')

        applied = prim.GetAppliedSchemas()
        self.assertIn('IFCSourceIdAPI', applied)
        self.assertIn('SourceIdentifierBaseAPI', applied)

        prop_names = set(p.GetName() for p in prim.GetProperties())
        self.assertIn('sourceId:primaryId', prop_names)
        self.assertIn('sourceId:ifc:ifcType', prop_names)
        self.assertIn('sourceId:ifc:schema', prop_names)

    def test_property_round_trip(self):
        stage = Usd.Stage.CreateInMemory()
        prim = UsdGeom.Xform.Define(stage, '/Asset').GetPrim()
        prim.ApplyAPI('WindchillSourceIdAPI')

        prim.GetAttribute('sourceId:primaryId').Set('OR:wt.part.WTPart:4697800')
        prim.GetAttribute('sourceId:revision').Set('Rev.C')
        prim.GetAttribute('sourceId:windchill:navigationCriteria').Set(
            'OR:wt.filter.NavigationCriteria:7608531')
        prim.GetAttribute('sourceId:windchill:displayNumber').Set('A-0000-12345')

        # Round-trip
        usda = stage.GetRootLayer().ExportToString()
        stage2 = Usd.Stage.CreateInMemory()
        stage2.GetRootLayer().ImportFromString(usda)
        prim2 = stage2.GetPrimAtPath('/Asset')

        self.assertEqual(prim2.GetAttribute('sourceId:primaryId').Get(),
                         'OR:wt.part.WTPart:4697800')
        self.assertEqual(prim2.GetAttribute('sourceId:windchill:navigationCriteria').Get(),
                         'OR:wt.filter.NavigationCriteria:7608531')

    def test_two_vendor_schemas_on_same_prim_collide(self):
        """B's single-apply nature: applying TWO vendor schemas to the same
        prim is technically allowed, but base properties (sourceId:primaryId)
        are SHARED between them — only one identifier can be authored.

        This is one of B's known trade-offs vs B.
        """
        stage = Usd.Stage.CreateInMemory()
        prim = UsdGeom.Xform.Define(stage, '/Asset').GetPrim()
        prim.ApplyAPI('WindchillSourceIdAPI')
        prim.ApplyAPI('IFCSourceIdAPI')

        applied = prim.GetAppliedSchemas()
        self.assertIn('WindchillSourceIdAPI', applied)
        self.assertIn('IFCSourceIdAPI', applied)

        # Single shared base property name; setting it commits to one value.
        prim.GetAttribute('sourceId:primaryId').Set('SHARED_ID')
        self.assertEqual(prim.GetAttribute('sourceId:primaryId').Get(), 'SHARED_ID',
            "B' has only ONE 'sourceId:primaryId' property per prim regardless "
            "of how many vendor schemas are applied. This is a real trade-off "
            "vs B's multi-apply (where each vendor gets its own namespaced primaryId).")


if __name__ == '__main__':
    unittest.main(verbosity=2)
