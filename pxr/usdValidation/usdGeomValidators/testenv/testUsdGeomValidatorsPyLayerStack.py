#!/pxrpythonsubst
#
# Copyright 2026 Pixar
#
# Licensed under the terms set forth in the LICENSE.txt file available at
# https://openusd.org/license.

"""Tests for a Python-implemented layer-stack metadata consistency validator.

The validator registered here supplements the C++ StageMetadataChecker: where
StageMetadataChecker flags a stage that is missing metersPerUnit or upAxis
entirely, this validator flags a stage whose layers *disagree* on those values.
"""

import unittest

from pxr import Sdf, Usd, UsdGeom, UsdValidation


# ---------------------------------------------------------------------------
# Validator implementation
#
# Python validators cannot be declared in plugInfo.json, so they must be
# registered explicitly.  This module registers the validator once, at import
# time.  Because the registry is a process-wide singleton, any test process
# that imports this module will have the validator available immediately.

_VALIDATOR_NAME = "usdGeomValidators:LayerStackMetadataConsistencyChecker"


def _check_layer_stack_metadata(stage, timeRange):
    """Report metersPerUnit and upAxis disagreements across the layer stack.

    USD resolves stage-level metadata by "strongest opinion wins" (the root
    layer's value takes effect), so a mismatch does not cause a hard failure
    at runtime.  It is nonetheless a common authoring mistake: a sublayer may
    have been created under different unit or orientation assumptions, and the
    disagreement can silently affect content that relies on those defaults.
    This validator surfaces the conflict as a warning.

    Note: this checks all layers returned by GetUsedLayers(), not just the
    root stage's direct sublayer stack.  A referenced or payloaded asset can
    author its own metersPerUnit or upAxis, and that disagreement is just as
    dangerous as a sublayer conflict — the root stage's value silently wins.
    """
    # GetUsedLayers covers every layer that contributes to the stage,
    # including referenced and payloaded asset files.  GetLayerStack would
    # only see direct sublayers of the root, missing the case where a newly
    # added referenced asset was authored under different units or orientation.
    used_layers = stage.GetUsedLayers()

    # Collect the value authored in each layer, preserving stack order so
    # the diagnostic message lists layers from strongest to weakest.
    mpu_by_layer = {}   # {identifier: float}
    axis_by_layer = {}  # {identifier: str}

    for layer in used_layers:
        pseudo_root = layer.GetPrimAtPath(Sdf.Path.absoluteRootPath)
        if pseudo_root is None:
            continue
        if pseudo_root.HasInfo(UsdGeom.Tokens.metersPerUnit):
            mpu_by_layer[layer.identifier] = pseudo_root.GetInfo(
                UsdGeom.Tokens.metersPerUnit
            )
        if pseudo_root.HasInfo(UsdGeom.Tokens.upAxis):
            # upAxis is a token; convert to str for set comparison.
            axis_by_layer[layer.identifier] = str(
                pseudo_root.GetInfo(UsdGeom.Tokens.upAxis)
            )

    errors = []
    site = UsdValidation.ValidationErrorSite(stage, Sdf.Path.absoluteRootPath)

    if len(set(mpu_by_layer.values())) > 1:
        detail = "; ".join(
            f"{lid}={v}" for lid, v in mpu_by_layer.items()
        )
        errors.append(
            UsdValidation.ValidationError(
                "MetersPerUnitMismatch",
                UsdValidation.ValidationErrorType.Warn,
                [site],
                f"Layer stack has conflicting metersPerUnit values: {detail}",
            )
        )

    if len(set(axis_by_layer.values())) > 1:
        detail = "; ".join(
            f"{lid}={v}" for lid, v in axis_by_layer.items()
        )
        errors.append(
            UsdValidation.ValidationError(
                "UpAxisMismatch",
                UsdValidation.ValidationErrorType.Warn,
                [site],
                f"Layer stack has conflicting upAxis values: {detail}",
            )
        )

    return errors


def _register_validator():
    registry = UsdValidation.ValidationRegistry()
    # Guard against re-registration if this module is imported more than once
    # in a process (the registry is a singleton and does not allow duplicate
    # names).
    if registry.HasValidator(_VALIDATOR_NAME):
        return
    metadata = UsdValidation.ValidatorMetadata(
        name=_VALIDATOR_NAME,
        doc=(
            "Checks all layers in the composed layer stack for conflicting "
            "metersPerUnit or upAxis values.  USD silently resolves these by "
            "taking the strongest opinion, so a mismatch can mask authoring "
            "errors in sublayers."
        ),
        keywords=["UsdGeomValidators"],
    )
    registry.RegisterStageValidator(metadata, _check_layer_stack_metadata)


_register_validator()


# ---------------------------------------------------------------------------
# Tests

class TestLayerStackMetadataConsistencyChecker(unittest.TestCase):

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

    def test_ValidatorIsRegistered(self):
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
