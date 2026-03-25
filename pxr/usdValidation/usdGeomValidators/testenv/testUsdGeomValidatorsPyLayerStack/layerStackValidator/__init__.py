#
# Copyright 2026 Pixar
#
# Licensed under the terms set forth in the LICENSE.txt file available at
# https://openusd.org/license.
#

"""Python plugin that checks layer-stack metadata consistency.

When the Plug registry loads this module (triggered by
GetOrLoadValidatorByName for the validator declared in this plugin's
plugInfo.json), the top-level registration code below runs and
registers the Python task function with the ValidationRegistry.

This supplements the C++ StageMetadataChecker: where that validator
flags a stage missing metersPerUnit or upAxis entirely, this one flags
a stage whose layers *disagree* on those values.
"""

from pxr import Sdf, UsdGeom, UsdValidation

_PLUGIN_NAME = "layerStackValidator"
_VALIDATOR_NAME = _PLUGIN_NAME + ":LayerStackMetadataConsistencyChecker"


def _check_layer_stack_metadata(stage, timeRange):
    """Report metersPerUnit and upAxis disagreements across the layer stack.

    USD resolves stage-level metadata by "strongest opinion wins" (the root
    layer's value takes effect), so a mismatch does not cause a hard failure
    at runtime.  It is nonetheless a common authoring mistake: a sublayer may
    have been created under different unit or orientation assumptions, and the
    disagreement can silently affect content that relies on those defaults.

    Note: this checks all layers returned by GetUsedLayers(), not just the
    root stage's direct sublayer stack.  A referenced or payloaded asset can
    author its own metersPerUnit or upAxis, and that disagreement is just as
    dangerous as a sublayer conflict — the root stage's value silently wins.
    """
    used_layers = stage.GetUsedLayers()

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


# --- Registration at import time (equivalent to TF_REGISTRY_FUNCTION) ---
_registry = UsdValidation.ValidationRegistry()
_registry.RegisterPluginStageValidator(
    _VALIDATOR_NAME, _check_layer_stack_metadata)
