//
// geoResolver.h -- C++ port of the Python reference runtime's stage-level
// geospatial resolution (resolve_runtime.py), built on the proven GeoCrsEngine.
//
// This is the implementation-under-test for parity: it reads a CRS-neutral
// authored UsdStage and computes the world (ECEF) transform for georeferenced
// prims WITHOUT baking anything back. It reproduces, in C++, exactly:
//   crs_of_prim          -> ResolveBinding   (MaterialBinding-style strength)
//   anchor_frame         -> AnchorFrame      (ENU->ECEF rigid frame)
//   nearest_anchor       -> NearestAnchor
//   resolve_with_injection -> ResolveWithInjection (inject-don't-bake compose)
//   resolve_world_translation -> ResolveWorldTranslation
//
// The Hydra scene index is a thin shell over this resolver; testing this against
// the Python oracle + closed-form geodesy on the real dataset stages IS the
// parity proof.
//
// AXIS-ORDER CONTRACT: crs:position is always (x=lon/E, y=lat/N, z=h).
// WKT STAYS OPAQUE: only GeoCrsEngine consumes the WKT string.
//
#ifndef USDGEOSPATIAL_GEO_RESOLVER_H
#define USDGEOSPATIAL_GEO_RESOLVER_H

#include <pxr/pxr.h>
#include <pxr/usd/usd/stage.h>
#include <pxr/usd/usd/prim.h>
#include <pxr/usd/usdGeom/xformCache.h>
#include <pxr/base/gf/matrix4d.h>
#include <pxr/base/gf/vec3d.h>

#include <string>
#include <mutex>

PXR_NAMESPACE_OPEN_SCOPE

class GeoCrsEngine;

class GeoResolver
{
public:
    /// targetIsEcef: when true, the render/target CRS is WGS84 ECEF (EPSG:4978)
    /// and anchor injection (orientation) applies. (Matches the suite which
    /// always resolves to ECEF.)
    explicit GeoResolver(const UsdStagePtr& stage);

    /// Resolve a prim's binding to its source CRS WKT, honouring
    /// MaterialBindingAPI-style strength/purpose semantics (nearest wins unless
    /// an ancestor is strongerThanDescendants). Returns true + fills srcWkt and
    /// boundPrimPath; false if no resolvable binding.
    bool ResolveBinding(const UsdPrim& prim, std::string* srcWkt,
                        SdfPath* crsPrimPath, SdfPath* boundPrimPath,
                        const std::string& purpose = "") const;

    /// The nearest anchor prim (self-or-ancestor with crs:position + a
    /// resolvable binding), or an invalid prim.
    UsdPrim NearestAnchor(const UsdPrim& prim, const std::string& purpose = "") const;

    /// Rigid local-frame -> ECEF transform for an anchor prim (ENU basis at the
    /// anchor footprint + ECEF origin). Returns identity + false if not an
    /// anchor. (port of anchor_frame)
    bool AnchorFrame(const UsdPrim& prim, GfMatrix4d* frame,
                     const std::string& purpose = "") const;

    /// World (ECEF) transform under inject-don't-bake semantics.
    /// (port of resolve_with_injection)
    ///   - prim IS the anchor   -> frame
    ///   - prim is a descendant -> localToAnchor * frame
    /// Returns false if no anchor up the chain.
    bool ResolveWithInjection(const UsdPrim& prim, GfMatrix4d* world,
                              SdfPath* anchorPath,
                              const std::string& purpose = "") const;

    /// World (ECEF) position for a georeferenced prim:
    ///   world = ancestorL2W . reproject(crs:position)
    /// (port of resolve_world_translation; compose_ancestors=true)
    bool ResolveWorldTranslation(const UsdPrim& prim, GfVec3d* world,
                                 const std::string& purpose = "") const;

private:
    // binding-relationship discovery (port of _binding_rel_for_purpose):
    // returns the winning binding relationship on `prim` for `purpose`/resolving
    // prim, or an invalid relationship.
    UsdRelationship _BindingRelForPurpose(const UsdPrim& prim,
                                          const std::string& purpose,
                                          const UsdPrim& resolvingPrim) const;
    // crs prim target of a binding relationship (port of _crs_target_of)
    UsdPrim _CrsTargetOf(const UsdRelationship& rel) const;
    bool _RelIsStronger(const UsdRelationship& rel) const;
    double _CrsEpoch(const SdfPath& crsPrimPath) const;

    UsdStagePtr _stage;
    GeoCrsEngine& _engine;
    mutable UsdGeomXformCache _xformCache;
    // UsdGeomXformCache is NOT thread-safe; Storm syncs rprims (and thus pulls
    // our xform data source) across TBB worker threads in parallel. Guard all
    // xform-cache access to prevent concurrent cache mutation (double-free).
    mutable std::mutex _xformCacheMutex;
};

PXR_NAMESPACE_CLOSE_SCOPE

#endif
