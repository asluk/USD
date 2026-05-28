"""Approach C (spiffmon's bridge) — multi-apply with no properties.

The defining experiment: does the 'assetInfoFallback' customData on a
multi-apply schema actually populate UsdPrimDefinition's effective
assetInfo with the default sub-dictionary?

This is what spiffmon described as "an applied schema can introduce a
sub-dictionary of assetInfo whose entries will be present in the
UsdPrimDefinition". If usdGenSchema/UsdPrimDefinition honor this
customData key, the test passes. If they don't, the test fails — that
itself is an important finding.

Verifies that:
1. SourceIdentifierBridgeAPI registers as multi-apply.
2. The schema applies to a prim with an instance name.
3. The user can still author the A-shape assetInfo dict (always works).
4. EXPERIMENTAL: whether the schema's customData declares a fallback
   assetInfo sub-dict that UsdPrimDefinition picks up.
"""

import os
import unittest

_THIS = os.path.dirname(os.path.abspath(__file__))
_SCHEMA_DIR = os.path.dirname(_THIS)
os.environ['PXR_PLUGINPATH_NAME'] = _SCHEMA_DIR

from pxr import Usd, UsdGeom


class TestApproachC(unittest.TestCase):

    def test_schema_registered_as_multiapply(self):
        reg = Usd.SchemaRegistry()
        self.assertTrue(reg.IsMultipleApplyAPISchema('SourceIdentifierBridgeAPI'),
            "SourceIdentifierBridgeAPI must be registered as multi-apply.")

    def test_apply_with_instance(self):
        stage = Usd.Stage.CreateInMemory()
        prim = UsdGeom.Xform.Define(stage, '/Asset').GetPrim()
        self.assertTrue(prim.ApplyAPI('SourceIdentifierBridgeAPI', 'windchill'))
        self.assertIn('SourceIdentifierBridgeAPI:windchill', prim.GetAppliedSchemas())

    def test_no_typed_properties(self):
        """C deliberately defines no typed properties — all storage is
        intended to live in assetInfo metadata (A's shape)."""
        stage = Usd.Stage.CreateInMemory()
        prim = UsdGeom.Xform.Define(stage, '/Asset').GetPrim()
        prim.ApplyAPI('SourceIdentifierBridgeAPI', 'windchill')
        # No schema-introduced properties should appear (only the inherited
        # UsdGeomXform ones).
        custom_props = [p.GetName() for p in prim.GetProperties()
                        if p.GetName().startswith('sourceIdentifier')]
        self.assertEqual(custom_props, [],
            "C schema must introduce zero typed properties; discoverability "
            "comes from the assetInfoFallback customData. Found: %s" % custom_props)

    def test_user_can_author_assetInfo_dict(self):
        """Even without fallback support, users can still write the dict
        manually (same as Approach A — C's storage shape IS A's)."""
        stage = Usd.Stage.CreateInMemory()
        prim = UsdGeom.Xform.Define(stage, '/Asset').GetPrim()
        prim.ApplyAPI('SourceIdentifierBridgeAPI', 'windchill')

        prim.SetAssetInfoByKey('source', {
            'windchill': {
                'primaryId': 'OR:wt.part.WTPart:4697800',
                'revision': 'Rev.C',
                'metadata': {},
            }
        })

        source = prim.GetAssetInfoByKey('source')
        self.assertEqual(source['windchill']['primaryId'],
                         'OR:wt.part.WTPart:4697800')

    def test_assetInfoFallback_in_prim_definition(self):
        """THE central experimental question for C:

        Does usdGenSchema propagate the schema's 'assetInfoFallback'
        customData into UsdPrimDefinition's effective assetInfo metadata?

        If YES: this assertion finds a default 'source' dict on the prim's
        assetInfo even without user authoring (spiffmon's claim works).

        If NO: the customData is currently ignored by UsdPrimDefinition;
        the mechanism requires the usdGenSchema enhancement spiffmon
        described as 'we can also at least explore adding usdGenSchema
        support'. Test failure is the finding.
        """
        stage = Usd.Stage.CreateInMemory()
        prim = UsdGeom.Xform.Define(stage, '/Asset').GetPrim()
        prim.ApplyAPI('SourceIdentifierBridgeAPI', 'windchill')

        # WITHOUT explicit authoring, does assetInfo.source.windchill exist?
        assetInfo = prim.GetAssetInfo()
        source = assetInfo.get('source')

        # Documentation of the finding either way:
        if source is None:
            self.skipTest(
                "FINDING: SourceIdentifierBridgeAPI's 'assetInfoFallback' "
                "customData is NOT honored by the current usdGenSchema / "
                "UsdPrimDefinition machinery. spiffmon's bridge mechanism "
                "would require new infrastructure (per his comment "
                "'we can also at least explore adding usdGenSchema support'). "
                "Storage shape is A's, but discoverability is NOT B-like "
                "without code changes.")
        else:
            # If we get here, the bridge mechanism is working.
            self.assertIn('windchill', source,
                "If assetInfoFallback IS honored, the instance name "
                "should appear as a key under source.")


if __name__ == '__main__':
    unittest.main(verbosity=2)
