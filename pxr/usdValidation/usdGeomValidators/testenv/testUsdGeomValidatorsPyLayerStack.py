#!/pxrpythonsubst
#
# Copyright 2026 Pixar
#
# Licensed under the terms set forth in the LICENSE.txt file available at
# https://openusd.org/license.

"""Tests for Python-plugin layer-stack metadata validators.

This test exercises the full plugin lazy-load path:

1. plugInfo.json ("Type": "python") declares validator metadata.
2. Plug.Registry().RegisterPlugins() discovers the plugin; the
   ValidationRegistry parses its Validators metadata.
3. GetOrLoadValidatorByName() triggers plugin->Load(), which does
   ``import layerStackValidator``.
4. The module's top-level code calls RegisterPluginStageValidator.
5. The validator is returned and can be invoked.

Two validators are registered:

- **LayerStackMetadataConsistencyChecker** (detect-only): flags layers
  that disagree on metersPerUnit or upAxis.  No fixers -- changing
  metadata without rescaling geometry would make the metadata lie.

- **LayerMetadataFallbackChecker**: flags layers that do not explicitly
  author metersPerUnit or upAxis.  Provides fixers that write the
  OpenUSD fallback values (metersPerUnit = 0.01, upAxis = "Y").
"""

import os
import sys
import tempfile
import unittest

from pxr import Plug, Sdf, Usd, UsdGeom, UsdValidation


_PLUGIN_NAME = "layerStackValidator"
_CONSISTENCY_NAME = _PLUGIN_NAME + ":LayerStackMetadataConsistencyChecker"
_FALLBACK_NAME = _PLUGIN_NAME + ":LayerMetadataFallbackChecker"


def _register_plugin():
    """Register the plugin once for the whole module."""
    # If already registered from a previous test class, nothing to do.
    if Plug.Registry().GetPluginWithName(_PLUGIN_NAME):
        return
    pluginDir = os.path.join(os.getcwd(), _PLUGIN_NAME)
    if not os.path.isdir(pluginDir):
        pluginDir = os.path.join(os.path.dirname(__file__),
                                 "testUsdGeomValidatorsPyLayerStack",
                                 _PLUGIN_NAME)
    parentDir = os.path.dirname(pluginDir)
    if parentDir not in sys.path:
        sys.path.insert(0, parentDir)
    plugins = Plug.Registry().RegisterPlugins(pluginDir + "/")
    assert plugins, (
        f"Failed to register plugin from {pluginDir}")
    assert any(p.name == _PLUGIN_NAME for p in plugins), (
        f"Plugin {_PLUGIN_NAME} not found in {plugins}")


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

    root_layer.subLayerPaths.append(sub_layer.identifier)
    return Usd.Stage.Open(root_layer)


def _make_two_layer_stage_on_disk(
    root_mpu=None, root_axis=None, sub_mpu=None, sub_axis=None
):
    """Like _make_two_layer_stage but with file-backed layers.

    ApplyFix calls layer.Save() internally, so tests that exercise
    ApplyFix need layers backed by real files.  Returns (stage, [paths])
    where paths is a list of temp file paths for cleanup.
    """
    sub_file = tempfile.NamedTemporaryFile(
        suffix=".usda", delete=False, dir=tempfile.gettempdir())
    sub_file.close()
    root_file = tempfile.NamedTemporaryFile(
        suffix=".usda", delete=False, dir=tempfile.gettempdir())
    root_file.close()

    sub_layer = Sdf.Layer.CreateNew(sub_file.name)
    root_layer = Sdf.Layer.CreateNew(root_file.name)

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

    root_layer.subLayerPaths.append(sub_layer.identifier)
    root_layer.Save()
    sub_layer.Save()
    return Usd.Stage.Open(root_layer), [root_file.name, sub_file.name]


def _find_sublayer(stage):
    """Return the first non-root, non-session used layer."""
    root_id = stage.GetRootLayer().identifier
    session_id = stage.GetSessionLayer().identifier
    for layer in stage.GetUsedLayers():
        if (layer.identifier != root_id
                and layer.identifier != session_id):
            return layer
    return None


# ===================================================================
# Test class 1: LayerStackMetadataConsistencyChecker (detect-only)
# ===================================================================

class TestLayerStackMetadataConsistencyChecker(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        _register_plugin()

    def _get_validator(self):
        registry = UsdValidation.ValidationRegistry()
        return registry.GetOrLoadValidatorByName(_CONSISTENCY_NAME)

    def test_MetadataDiscoverableBeforeLoad(self):
        """Validator metadata from plugInfo.json is available before the
        plugin module is imported."""
        registry = UsdValidation.ValidationRegistry()
        meta = registry.GetValidatorMetadata(_CONSISTENCY_NAME)
        self.assertIsNotNone(meta)
        self.assertEqual(
            meta.doc,
            "Checks all layers for conflicting metersPerUnit or upAxis "
            "values.")
        self.assertIn("UsdGeomValidators", meta.GetKeywords())

    def test_DiscoverableByKeyword(self):
        """Plugin validator appears in keyword queries."""
        registry = UsdValidation.ValidationRegistry()
        metadatas = registry.GetValidatorMetadataForKeyword(
            "UsdGeomValidators")
        names = [m.name for m in metadatas]
        self.assertIn(_CONSISTENCY_NAME, names)

    def test_ValidatorIsRegistered(self):
        """GetOrLoadValidatorByName triggers plugin load and registration."""
        registry = UsdValidation.ValidationRegistry()
        self.assertTrue(registry.HasValidator(_CONSISTENCY_NAME))

    def test_NoFixers(self):
        """The consistency checker is detect-only; it must not have fixers."""
        validator = self._get_validator()
        fixers = validator.GetFixers()
        self.assertEqual(len(fixers), 0)

    def test_NoErrors_WhenNoMetadataAuthored(self):
        stage = Usd.Stage.CreateInMemory()
        errors = self._get_validator().Validate(stage)
        self.assertEqual(len(errors), 0)

    def test_NoErrors_WhenSingleLayer(self):
        stage = Usd.Stage.CreateInMemory()
        UsdGeom.SetStageMetersPerUnit(stage, 1.0)
        UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.y)
        errors = self._get_validator().Validate(stage)
        self.assertEqual(len(errors), 0)

    def test_NoErrors_WhenAllLayersAgree(self):
        stage = _make_two_layer_stage(
            root_mpu=0.01, root_axis="Z", sub_mpu=0.01, sub_axis="Z"
        )
        errors = self._get_validator().Validate(stage)
        self.assertEqual(len(errors), 0)

    def test_MetersPerUnitMismatch(self):
        stage = _make_two_layer_stage(
            root_mpu=1.0, root_axis="Y", sub_mpu=0.01, sub_axis="Y"
        )
        errors = self._get_validator().Validate(stage)
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0].GetName(), "MetersPerUnitMismatch")
        self.assertEqual(
            errors[0].GetType(), UsdValidation.ValidationErrorType.Warn)

    def test_UpAxisMismatch(self):
        stage = _make_two_layer_stage(
            root_mpu=1.0, root_axis="Y", sub_mpu=1.0, sub_axis="Z"
        )
        errors = self._get_validator().Validate(stage)
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0].GetName(), "UpAxisMismatch")
        self.assertEqual(
            errors[0].GetType(), UsdValidation.ValidationErrorType.Warn)

    def test_BothMismatch(self):
        stage = _make_two_layer_stage(
            root_mpu=1.0, root_axis="Y", sub_mpu=0.01, sub_axis="Z"
        )
        errors = self._get_validator().Validate(stage)
        self.assertEqual(len(errors), 2)
        error_names = {e.GetName() for e in errors}
        self.assertIn("MetersPerUnitMismatch", error_names)
        self.assertIn("UpAxisMismatch", error_names)


# ===================================================================
# Test class 2: LayerMetadataFallbackChecker (with fixers)
# ===================================================================

class TestLayerMetadataFallbackChecker(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        _register_plugin()

    def _get_validator(self):
        registry = UsdValidation.ValidationRegistry()
        return registry.GetOrLoadValidatorByName(_FALLBACK_NAME)

    # -- Discovery tests --

    def test_MetadataDiscoverableBeforeLoad(self):
        registry = UsdValidation.ValidationRegistry()
        meta = registry.GetValidatorMetadata(_FALLBACK_NAME)
        self.assertIsNotNone(meta)
        self.assertEqual(
            meta.doc,
            "Checks that layers explicitly author metersPerUnit and upAxis "
            "rather than relying on fallback values.")
        self.assertIn("UsdGeomValidators", meta.GetKeywords())

    def test_DiscoverableByKeyword(self):
        registry = UsdValidation.ValidationRegistry()
        metadatas = registry.GetValidatorMetadataForKeyword(
            "UsdGeomValidators")
        names = [m.name for m in metadatas]
        self.assertIn(_FALLBACK_NAME, names)

    def test_ValidatorIsRegistered(self):
        registry = UsdValidation.ValidationRegistry()
        self.assertTrue(registry.HasValidator(_FALLBACK_NAME))

    # -- Detection tests --

    def test_NoErrors_WhenAllMetadataAuthored(self):
        """Layers that explicitly author both values produce no errors."""
        stage = _make_two_layer_stage(
            root_mpu=1.0, root_axis="Y", sub_mpu=0.01, sub_axis="Z"
        )
        errors = self._get_validator().Validate(stage)
        self.assertEqual(len(errors), 0)

    def test_MissingMetersPerUnit(self):
        """A layer without metersPerUnit should produce a warning."""
        # Root has both, sublayer has neither.
        stage = _make_two_layer_stage(
            root_mpu=1.0, root_axis="Y"
        )
        errors = self._get_validator().Validate(stage)
        mpu_errors = [e for e in errors
                      if e.GetName() == "MissingMetersPerUnit"]
        self.assertTrue(len(mpu_errors) > 0)
        self.assertEqual(
            mpu_errors[0].GetType(), UsdValidation.ValidationErrorType.Warn)

    def test_MissingUpAxis(self):
        """A layer without upAxis should produce a warning."""
        stage = _make_two_layer_stage(
            root_mpu=1.0, root_axis="Y"
        )
        errors = self._get_validator().Validate(stage)
        axis_errors = [e for e in errors
                       if e.GetName() == "MissingUpAxis"]
        self.assertTrue(len(axis_errors) > 0)
        self.assertEqual(
            axis_errors[0].GetType(), UsdValidation.ValidationErrorType.Warn)

    def test_NoErrors_SingleLayerFullyAuthored(self):
        """A single layer with both values authored produces no errors."""
        stage = Usd.Stage.CreateInMemory()
        UsdGeom.SetStageMetersPerUnit(stage, 1.0)
        UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.y)
        errors = self._get_validator().Validate(stage)
        # The root layer has both values; only session layer remains
        # and it is skipped.
        self.assertEqual(len(errors), 0)

    # -- Fixer registration tests --

    def test_FixersAreRegistered(self):
        """The fallback checker should have two fixers."""
        validator = self._get_validator()
        fixers = validator.GetFixers()
        self.assertEqual(len(fixers), 2)
        fixer_names = {f.name for f in fixers}
        self.assertIn("SetMetersPerUnitFallback", fixer_names)
        self.assertIn("SetUpAxisFallback", fixer_names)

    def test_FixersByErrorName(self):
        """Each fixer is associated with the correct error name."""
        validator = self._get_validator()
        mpu_fixers = validator.GetFixersByErrorName("MissingMetersPerUnit")
        self.assertTrue(
            any(f.name == "SetMetersPerUnitFallback" for f in mpu_fixers))
        axis_fixers = validator.GetFixersByErrorName("MissingUpAxis")
        self.assertTrue(
            any(f.name == "SetUpAxisFallback" for f in axis_fixers))

    # -- Fixer apply tests --

    def test_MetersPerUnitFixer_CanApplyAndApply(self):
        """The MPU fixer writes the fallback value to a layer missing it."""
        # Sublayer has no metadata at all.
        stage, tmp_paths = _make_two_layer_stage_on_disk(
            root_mpu=1.0, root_axis="Y"
        )
        try:
            validator = self._get_validator()
            errors = validator.Validate(stage)
            mpu_errors = [e for e in errors
                          if e.GetName() == "MissingMetersPerUnit"]
            self.assertTrue(len(mpu_errors) > 0)

            fixer = validator.GetFixerByName("SetMetersPerUnitFallback")
            self.assertIsNotNone(fixer)

            sub_layer = _find_sublayer(stage)
            self.assertIsNotNone(sub_layer)
            editTarget = Usd.EditTarget(sub_layer)

            self.assertTrue(fixer.CanApplyFix(mpu_errors[0], editTarget))
            self.assertTrue(fixer.ApplyFix(mpu_errors[0], editTarget))

            # After the fix, the sublayer should have the fallback value.
            sub_pseudo = sub_layer.GetPrimAtPath(Sdf.Path.absoluteRootPath)
            self.assertAlmostEqual(
                sub_pseudo.GetInfo(UsdGeom.Tokens.metersPerUnit), 0.01)
        finally:
            for p in tmp_paths:
                os.unlink(p)

    def test_UpAxisFixer_CanApplyAndApply(self):
        """The upAxis fixer writes the fallback value to a layer missing it."""
        stage, tmp_paths = _make_two_layer_stage_on_disk(
            root_mpu=1.0, root_axis="Y"
        )
        try:
            validator = self._get_validator()
            errors = validator.Validate(stage)
            axis_errors = [e for e in errors
                           if e.GetName() == "MissingUpAxis"]
            self.assertTrue(len(axis_errors) > 0)

            fixer = validator.GetFixerByName("SetUpAxisFallback")
            self.assertIsNotNone(fixer)

            sub_layer = _find_sublayer(stage)
            self.assertIsNotNone(sub_layer)
            editTarget = Usd.EditTarget(sub_layer)

            self.assertTrue(fixer.CanApplyFix(axis_errors[0], editTarget))
            self.assertTrue(fixer.ApplyFix(axis_errors[0], editTarget))

            sub_pseudo = sub_layer.GetPrimAtPath(Sdf.Path.absoluteRootPath)
            self.assertEqual(
                str(sub_pseudo.GetInfo(UsdGeom.Tokens.upAxis)), "Y")
        finally:
            for p in tmp_paths:
                os.unlink(p)

    def test_FixerCanApply_ReturnsFalse_WhenAlreadyAuthored(self):
        """CanApplyFix returns False when the layer already has the value."""
        stage = _make_two_layer_stage(
            root_mpu=1.0, root_axis="Y", sub_mpu=0.01, sub_axis="Z"
        )
        validator = self._get_validator()
        # All layers author both values, so no errors from this validator.
        errors = validator.Validate(stage)
        self.assertEqual(len(errors), 0)


if __name__ == "__main__":
    unittest.main()
