#
# Copyright 2026 Pixar
#
# Licensed under the terms set forth in the LICENSE.txt file available at
# https://openusd.org/license.
#

"""Python plugin validators for layer-stack metadata.

Registers two validators:

1. **LayerStackMetadataConsistencyChecker** (detect-only) -- flags layers
   that *disagree* on metersPerUnit or upAxis.  No fixer is provided
   because silently rewriting metadata without rescaling geometry or
   adjusting orientation would make the metadata lie about the data.

2. **LayerMetadataFallbackChecker** -- flags layers that do not explicitly
   author metersPerUnit or upAxis (relying on implicit fallback values).
   Provides fixers that write the OpenUSD fallback values
   (metersPerUnit = 0.01 / centimeters, upAxis = "Y") so the intent is
   explicit rather than implied.
"""

from pxr import Sdf, UsdGeom, UsdValidation

_PLUGIN_NAME = "layerStackValidator"

# ---------------------------------------------------------------------------
# Validator 1: cross-layer mismatch detection (no fixers)
# ---------------------------------------------------------------------------

_CONSISTENCY_NAME = _PLUGIN_NAME + ":LayerStackMetadataConsistencyChecker"


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
    dangerous as a sublayer conflict; the root stage's value silently wins.
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
# Validator 2: missing metadata with safe fixers
# ---------------------------------------------------------------------------

_FALLBACK_NAME = _PLUGIN_NAME + ":LayerMetadataFallbackChecker"

# OpenUSD fallback values (what the runtime assumes when nothing is authored)
_FALLBACK_MPU = 0.01           # centimeters
_FALLBACK_AXIS = "Y"


def _check_missing_metadata(stage, timeRange):
    """Flag layers that rely on implicit fallback values for metersPerUnit
    or upAxis instead of authoring them explicitly.

    Explicit metadata makes the layer's intent clear to every tool and
    human reader; relying on fallback defaults is a common source of
    silent unit or orientation bugs when layers move between pipelines.
    """
    used_layers = stage.GetUsedLayers()
    errors = []

    for layer in used_layers:
        # Skip session layers; they are transient and should not carry
        # persistent stage metadata.
        if layer.anonymous and "-session" in layer.identifier:
            continue

        pseudo_root = layer.GetPrimAtPath(Sdf.Path.absoluteRootPath)
        if pseudo_root is None:
            continue

        site = UsdValidation.ValidationErrorSite(layer,
                                                  Sdf.Path.absoluteRootPath)

        if not pseudo_root.HasInfo(UsdGeom.Tokens.metersPerUnit):
            errors.append(
                UsdValidation.ValidationError(
                    "MissingMetersPerUnit",
                    UsdValidation.ValidationErrorType.Warn,
                    [site],
                    f"Layer '{layer.identifier}' does not author "
                    f"metersPerUnit (fallback: {_FALLBACK_MPU}).",
                )
            )

        if not pseudo_root.HasInfo(UsdGeom.Tokens.upAxis):
            errors.append(
                UsdValidation.ValidationError(
                    "MissingUpAxis",
                    UsdValidation.ValidationErrorType.Warn,
                    [site],
                    f"Layer '{layer.identifier}' does not author "
                    f"upAxis (fallback: \"{_FALLBACK_AXIS}\").",
                )
            )

    return errors


# ---------------------------------------------------------------------------
# Fixers: write the fallback values explicitly
#
# These are safe because they make explicit what the runtime already assumes.
# No geometry is rescaled, no orientation is changed; only the metadata
# is written so the layer's intent is self-documenting.
# ---------------------------------------------------------------------------

def _can_set_mpu_fallback(error, editTarget, timeCode):
    layer = editTarget.GetLayer()
    pseudo_root = layer.GetPrimAtPath(Sdf.Path.absoluteRootPath)
    return (pseudo_root is not None
            and not pseudo_root.HasInfo(UsdGeom.Tokens.metersPerUnit))


def _set_mpu_fallback(error, editTarget, timeCode):
    layer = editTarget.GetLayer()
    pseudo_root = layer.GetPrimAtPath(Sdf.Path.absoluteRootPath)
    if pseudo_root is None:
        return False
    pseudo_root.SetInfo(UsdGeom.Tokens.metersPerUnit, _FALLBACK_MPU)
    return True


def _can_set_axis_fallback(error, editTarget, timeCode):
    layer = editTarget.GetLayer()
    pseudo_root = layer.GetPrimAtPath(Sdf.Path.absoluteRootPath)
    return (pseudo_root is not None
            and not pseudo_root.HasInfo(UsdGeom.Tokens.upAxis))


def _set_axis_fallback(error, editTarget, timeCode):
    layer = editTarget.GetLayer()
    pseudo_root = layer.GetPrimAtPath(Sdf.Path.absoluteRootPath)
    if pseudo_root is None:
        return False
    pseudo_root.SetInfo(UsdGeom.Tokens.upAxis, _FALLBACK_AXIS)
    return True


_mpu_fixer = UsdValidation.ValidationFixer(
    name="SetMetersPerUnitFallback",
    description=(
        f"Explicitly author metersPerUnit = {_FALLBACK_MPU} (centimeters), "
        f"the OpenUSD fallback value."),
    fixerImplFn=_set_mpu_fallback,
    canApplyFn=_can_set_mpu_fallback,
    errorName="MissingMetersPerUnit",
)

_axis_fixer = UsdValidation.ValidationFixer(
    name="SetUpAxisFallback",
    description=(
        f"Explicitly author upAxis = \"{_FALLBACK_AXIS}\", "
        f"the OpenUSD fallback value."),
    fixerImplFn=_set_axis_fallback,
    canApplyFn=_can_set_axis_fallback,
    errorName="MissingUpAxis",
)


# --- Registration at import time (equivalent to TF_REGISTRY_FUNCTION) ---
_registry = UsdValidation.ValidationRegistry()

_registry.RegisterPluginStageValidator(
    _CONSISTENCY_NAME, _check_layer_stack_metadata)

_registry.RegisterPluginStageValidator(
    _FALLBACK_NAME, _check_missing_metadata,
    fixers=[_mpu_fixer, _axis_fixer])
