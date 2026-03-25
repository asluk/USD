#!/pxrpythonsubst
#
# Copyright 2026 Pixar
#
# Licensed under the terms set forth in the LICENSE.txt file available at
# https://openusd.org/license.

"""Tests for a Python-plugin layer-stack metadata consistency validator.

This test exercises the full plugin lazy-load path:

1. plugInfo.json ("Type": "python") declares validator metadata.
2. Plug.Registry().RegisterPlugins() discovers the plugin; the
   ValidationRegistry parses its Validators metadata.
3. GetOrLoadValidatorByName() triggers plugin->Load(), which does
   ``import layerStackValidator``.
4. The module's top-level code calls RegisterPluginStageValidator.
5. The validator is returned and can be invoked.

The validator itself supplements the C++ StageMetadataChecker: where that
validator flags a stage missing metersPerUnit or upAxis entirely, this one
flags a stage whose layers *disagree* on those values.
"""

import os
import sys
import unittest

from pxr import Plug, Sdf, Usd, UsdGeom, UsdValidation


_PLUGIN_NAME = "layerStackValidator"
_VALIDATOR_NAME = _PLUGIN_NAME + ":LayerStackMetadataConsistencyChecker"


class TestLayerStackMetadataConsistencyChecker(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # The plugin directory must be discoverable by PlugRegistry
        # BEFORE the ValidationRegistry singleton is created, so that
        # plugInfo.json metadata is parsed during registry initialization.
        pluginDir = os.path.join(os.getcwd(), _PLUGIN_NAME)
        if not os.path.isdir(pluginDir):
            # Fallback for manual invocation outside ctest.
            pluginDir = os.path.join(os.path.dirname(__file__),
                                     "testUsdGeomValidatorsPyLayerStack",
                                     _PLUGIN_NAME)
        # Add the parent of the plugin package to sys.path so that
        # ``import layerStackValidator`` resolves correctly when the
        # Plug system does TfPyRunSimpleString("import ...").
        parentDir = os.path.dirname(pluginDir)
        if parentDir not in sys.path:
            sys.path.insert(0, parentDir)
        plugins = Plug.Registry().RegisterPlugins(pluginDir + "/")
        assert plugins, (
            f"Failed to register plugin from {pluginDir}")
        assert any(p.name == _PLUGIN_NAME for p in plugins), (
            f"Plugin {_PLUGIN_NAME} not found in {plugins}")

    def _get_validator(self):
        registry = UsdValidation.ValidationRegistry()
        return registry.GetOrLoadValidatorByName(_VALIDATOR_NAME)

    @staticmethod
    def _make_two_layer_stage(
        root_mpu=None, root_axis=None, sub_mpu=None, sub_axis=None
    ):
        """Return a stage whose root layer has the given metadata, with a
        sublayer that authors the sub_* values.

        Any value left as None is not authored in the corresponding layer.
        """
        sub_layer = Sdf.Layer.CreateAnonymous(".usda")
        root_layer = Sdf.Layer.CreateAnonymous(".usda")

        if sub_mpu is not None or sub_axis is not None:
            lines = ["#usda 1.0", "("]
            if sub_mpu is not None:
                lines.append(f"    metersPerUnit = {sub_mpu}")
            if sub_axis is not None:
                lines.append(f'    upAxis = "{sub_axis}"')
            lines.append(")")
            sub_layer.ImportFromString("\n".join(lines))

        root_lines = ["#usda 1.0", "("]
        if root_mpu is not None:
            root_lines.append(f"    metersPerUnit = {root_mpu}")
        if root_axis is not None:
            root_lines.append(f'    upAxis = "{root_axis}"')
        root_lines.append(")")
        root_layer.ImportFromString("\n".join(root_lines))

        # Add the sublayer after ImportFromString; subLayerPaths is a mutable
        # proxy and appending to it does not disturb the rest of the spec.
        root_layer.subLayerPaths.append(sub_layer.identifier)
        return Usd.Stage.Open(root_layer)

    def test_MetadataDiscoverableBeforeLoad(self):
        """Validator metadata from plugInfo.json is available before the
        plugin module is imported."""
        registry = UsdValidation.ValidationRegistry()
        meta = registry.GetValidatorMetadata(_VALIDATOR_NAME)
        self.assertIsNotNone(meta)
        self.assertEqual(
            meta.doc,
            "Checks all layers for conflicting metersPerUnit or upAxis values.")
        self.assertIn("UsdGeomValidators", meta.GetKeywords())

    def test_DiscoverableByKeyword(self):
        """Plugin validator appears in keyword queries."""
        registry = UsdValidation.ValidationRegistry()
        metadatas = registry.GetValidatorMetadataForKeyword(
            "UsdGeomValidators")
        names = [m.name for m in metadatas]
        self.assertIn(_VALIDATOR_NAME, names)

    def test_ValidatorIsRegistered(self):
        """GetOrLoadValidatorByName triggers plugin load and registration."""
        registry = UsdValidation.ValidationRegistry()
        self.assertTrue(registry.HasValidator(_VALIDATOR_NAME))

    def test_NoErrors_WhenNoMetadataAuthored(self):
        # A stage with no metadata authored at all: nothing to disagree on.
        stage = Usd.Stage.CreateInMemory()
        errors = self._get_validator().Validate(stage)
        self.assertEqual(len(errors), 0)

    def test_NoErrors_WhenSingleLayer(self):
        # A single-layer stage cannot have inter-layer conflicts.
        stage = Usd.Stage.CreateInMemory()
        UsdGeom.SetStageMetersPerUnit(stage, 1.0)
        UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.y)
        errors = self._get_validator().Validate(stage)
        self.assertEqual(len(errors), 0)

    def test_NoErrors_WhenAllLayersAgree(self):
        # Both layers author the same values; no conflict.
        stage = self._make_two_layer_stage(
            root_mpu=0.01, root_axis="Z", sub_mpu=0.01, sub_axis="Z"
        )
        errors = self._get_validator().Validate(stage)
        self.assertEqual(len(errors), 0)

    def test_MetersPerUnitMismatch(self):
        # Root layer is meters (1.0); sublayer was authored in centimeters
        # (0.01).  Expect exactly one warning naming the mismatch.
        stage = self._make_two_layer_stage(
            root_mpu=1.0, root_axis="Y", sub_mpu=0.01, sub_axis="Y"
        )
        errors = self._get_validator().Validate(stage)
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0].GetName(), "MetersPerUnitMismatch")
        self.assertEqual(
            errors[0].GetType(), UsdValidation.ValidationErrorType.Warn
        )

    def test_UpAxisMismatch(self):
        # Root layer is Y-up; sublayer is Z-up.  Expect exactly one warning.
        stage = self._make_two_layer_stage(
            root_mpu=1.0, root_axis="Y", sub_mpu=1.0, sub_axis="Z"
        )
        errors = self._get_validator().Validate(stage)
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0].GetName(), "UpAxisMismatch")
        self.assertEqual(
            errors[0].GetType(), UsdValidation.ValidationErrorType.Warn
        )

    def test_BothMismatch(self):
        # Both metersPerUnit and upAxis conflict; expect two separate warnings.
        stage = self._make_two_layer_stage(
            root_mpu=1.0, root_axis="Y", sub_mpu=0.01, sub_axis="Z"
        )
        errors = self._get_validator().Validate(stage)
        self.assertEqual(len(errors), 2)
        error_names = {e.GetName() for e in errors}
        self.assertIn("MetersPerUnitMismatch", error_names)
        self.assertIn("UpAxisMismatch", error_names)


if __name__ == "__main__":
    unittest.main()
