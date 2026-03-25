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

The validator also provides fixers that resolve mismatches by
propagating the root layer's value to all disagreeing layers.
"""

from pxr import Sdf, Usd, UsdGeom, UsdValidation

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


# ---------------------------------------------------------------------------
# Fixers
# ---------------------------------------------------------------------------

def _can_apply_mpu_fix(error, editTarget, timeCode):
    """Return True if the edit target's layer has a metersPerUnit value
    that differs from the root layer's value.  The error's sites list
    contains the stage; we use it to find the root layer's authoritative
    value."""
    sites = error.GetSites()
    if not sites:
        return False
    stage = sites[0].GetStage()
    if stage is None:
        return False
    root_pseudo = stage.GetRootLayer().GetPrimAtPath(
        Sdf.Path.absoluteRootPath)
    if root_pseudo is None or not root_pseudo.HasInfo(
            UsdGeom.Tokens.metersPerUnit):
        return False
    target_layer = editTarget.GetLayer()
    target_pseudo = target_layer.GetPrimAtPath(Sdf.Path.absoluteRootPath)
    if target_pseudo is None or not target_pseudo.HasInfo(
            UsdGeom.Tokens.metersPerUnit):
        return False
    return (target_pseudo.GetInfo(UsdGeom.Tokens.metersPerUnit)
            != root_pseudo.GetInfo(UsdGeom.Tokens.metersPerUnit))


def _apply_mpu_fix(error, editTarget, timeCode):
    """Set metersPerUnit on the edit target's layer to match the root layer."""
    sites = error.GetSites()
    if not sites:
        return False
    stage = sites[0].GetStage()
    if stage is None:
        return False
    root_pseudo = stage.GetRootLayer().GetPrimAtPath(
        Sdf.Path.absoluteRootPath)
    root_mpu = root_pseudo.GetInfo(UsdGeom.Tokens.metersPerUnit)
    target_layer = editTarget.GetLayer()
    target_pseudo = target_layer.GetPrimAtPath(Sdf.Path.absoluteRootPath)
    target_pseudo.SetInfo(UsdGeom.Tokens.metersPerUnit, root_mpu)
    return True


def _can_apply_axis_fix(error, editTarget, timeCode):
    """Return True if the edit target's layer has an upAxis value that
    differs from the root layer's value."""
    sites = error.GetSites()
    if not sites:
        return False
    stage = sites[0].GetStage()
    if stage is None:
        return False
    root_pseudo = stage.GetRootLayer().GetPrimAtPath(
        Sdf.Path.absoluteRootPath)
    if root_pseudo is None or not root_pseudo.HasInfo(
            UsdGeom.Tokens.upAxis):
        return False
    target_layer = editTarget.GetLayer()
    target_pseudo = target_layer.GetPrimAtPath(Sdf.Path.absoluteRootPath)
    if target_pseudo is None or not target_pseudo.HasInfo(
            UsdGeom.Tokens.upAxis):
        return False
    return (str(target_pseudo.GetInfo(UsdGeom.Tokens.upAxis))
            != str(root_pseudo.GetInfo(UsdGeom.Tokens.upAxis)))


def _apply_axis_fix(error, editTarget, timeCode):
    """Set upAxis on the edit target's layer to match the root layer."""
    sites = error.GetSites()
    if not sites:
        return False
    stage = sites[0].GetStage()
    if stage is None:
        return False
    root_pseudo = stage.GetRootLayer().GetPrimAtPath(
        Sdf.Path.absoluteRootPath)
    root_axis = root_pseudo.GetInfo(UsdGeom.Tokens.upAxis)
    target_layer = editTarget.GetLayer()
    target_pseudo = target_layer.GetPrimAtPath(Sdf.Path.absoluteRootPath)
    target_pseudo.SetInfo(UsdGeom.Tokens.upAxis, root_axis)
    return True


_mpu_fixer = UsdValidation.ValidationFixer(
    name="MetersPerUnitFixer",
    description="Set metersPerUnit to match the root layer's value.",
    fixerImplFn=_apply_mpu_fix,
    canApplyFn=_can_apply_mpu_fix,
    errorName="MetersPerUnitMismatch",
)

_axis_fixer = UsdValidation.ValidationFixer(
    name="UpAxisFixer",
    description="Set upAxis to match the root layer's value.",
    fixerImplFn=_apply_axis_fix,
    canApplyFn=_can_apply_axis_fix,
    errorName="UpAxisMismatch",
)

# --- Registration at import time (equivalent to TF_REGISTRY_FUNCTION) ---
_registry = UsdValidation.ValidationRegistry()
_registry.RegisterPluginStageValidator(
    _VALIDATOR_NAME, _check_layer_stack_metadata,
    fixers=[_mpu_fixer, _axis_fixer])
