//
// geospatialSceneIndex.cpp -- implementation.
//
#include "geospatialSceneIndex.h"
#include "geoResolver.h"

#include <pxr/usd/usd/prim.h>
#include <pxr/imaging/hd/xformSchema.h>
#include <pxr/imaging/hd/retainedDataSource.h>
#include <pxr/imaging/hd/overlayContainerDataSource.h>
#include <pxr/imaging/hd/dataSource.h>

PXR_NAMESPACE_OPEN_SCOPE

// ---------------------------------------------------------------------------
// A matrix data source that returns GeoResolver's computed world (ECEF) xform
// for `primPath`, resolved on demand.
// ---------------------------------------------------------------------------
namespace {

class _GeoMatrixDataSource final : public HdMatrixDataSource
{
public:
    HD_DECLARE_DATASOURCE(_GeoMatrixDataSource);

    VtValue GetValue(Time t) override { return VtValue(GetTypedValue(t)); }

    GfMatrix4d GetTypedValue(Time /*t*/) override
    {
        GfMatrix4d world(1.0);
        SdfPath anchor;
        if (_resolver && _resolver->ResolveWithInjection(_prim, &world, &anchor)) {
            return world;
        }
        // fall back to the original matrix if present
        if (_fallback) return _fallback->GetTypedValue(0.0f);
        return GfMatrix4d(1.0);
    }

    bool GetContributingSampleTimesForInterval(
        Time, Time, std::vector<Time>*) override { return false; }

private:
    _GeoMatrixDataSource(const std::shared_ptr<GeoResolver>& resolver,
                         const UsdPrim& prim,
                         const HdMatrixDataSourceHandle& fallback)
        : _resolver(resolver), _prim(prim), _fallback(fallback) {}

    std::shared_ptr<GeoResolver> _resolver;
    UsdPrim _prim;
    HdMatrixDataSourceHandle _fallback;
};

// Wrap a prim's data source so the xform.matrix locator returns our computed
// matrix; resetXformStack is forced true (the georef IS the world transform,
// not composed under parents in Hydra's flattened sense -- we already composed
// ancestors in GeoResolver). Everything else passes through.
HdContainerDataSourceHandle
_WrapXform(const std::shared_ptr<GeoResolver>& resolver,
           const UsdPrim& prim,
           const HdContainerDataSourceHandle& input)
{
    HdXformSchema xs = HdXformSchema::GetFromParent(input);
    HdMatrixDataSourceHandle fallback = xs.IsDefined() ? xs.GetMatrix() : nullptr;

    HdContainerDataSourceHandle xformOverride =
        HdXformSchema::Builder()
            .SetMatrix(_GeoMatrixDataSource::New(resolver, prim, fallback))
            .SetResetXformStack(
                HdRetainedTypedSampledDataSource<bool>::New(true))
            .Build();

    HdContainerDataSourceHandle overlayNamed =
        HdRetainedContainerDataSource::New(
            HdXformSchemaTokens->xform, xformOverride);

    return HdOverlayContainerDataSource::New(overlayNamed, input);
}

} // namespace

UsdGeospatialSceneIndexRefPtr UsdGeospatialSceneIndex::New(
    const HdSceneIndexBaseRefPtr& inputSceneIndex,
    const HdContainerDataSourceHandle& inputArgs)
{
    return TfCreateRefPtr(new UsdGeospatialSceneIndex(inputSceneIndex, inputArgs));
}

UsdGeospatialSceneIndex::UsdGeospatialSceneIndex(
    const HdSceneIndexBaseRefPtr& inputSceneIndex,
    const HdContainerDataSourceHandle& /*inputArgs*/)
    : HdSingleInputFilteringSceneIndexBase(inputSceneIndex)
{
}

UsdGeospatialSceneIndex::~UsdGeospatialSceneIndex() = default;

void UsdGeospatialSceneIndex::SetStage(const UsdStagePtr& stage)
{
    _stage = stage;
    _resolver = std::make_shared<GeoResolver>(stage);
}

HdSceneIndexPrim UsdGeospatialSceneIndex::GetPrim(const SdfPath& primPath) const
{
    HdSceneIndexPrim prim = _GetInputSceneIndex()->GetPrim(primPath);
    if (!_resolver || !_stage) return prim;
    if (!prim.dataSource) return prim;

    UsdPrim usdPrim = _stage->GetPrimAtPath(primPath);
    if (!usdPrim || !usdPrim.IsValid()) return prim;

    // only wrap if this prim resolves to a geospatial anchor up its chain
    UsdPrim anchor = _resolver->NearestAnchor(usdPrim);
    if (!anchor || !anchor.IsValid()) return prim;

    prim.dataSource = _WrapXform(_resolver, usdPrim, prim.dataSource);
    return prim;
}

SdfPathVector UsdGeospatialSceneIndex::GetChildPrimPaths(const SdfPath& primPath) const
{
    return _GetInputSceneIndex()->GetChildPrimPaths(primPath);
}

void UsdGeospatialSceneIndex::_PrimsAdded(const HdSceneIndexBase&,
    const HdSceneIndexObserver::AddedPrimEntries& entries)
{
    _SendPrimsAdded(entries);
}

void UsdGeospatialSceneIndex::_PrimsRemoved(const HdSceneIndexBase&,
    const HdSceneIndexObserver::RemovedPrimEntries& entries)
{
    _SendPrimsRemoved(entries);
}

void UsdGeospatialSceneIndex::_PrimsDirtied(const HdSceneIndexBase&,
    const HdSceneIndexObserver::DirtiedPrimEntries& entries)
{
    // If an anchor's xform/position dirties, all descendants riding it must be
    // re-resolved. We conservatively forward and additionally dirty the xform
    // locator on the subtree of any dirtied prim.
    HdSceneIndexObserver::DirtiedPrimEntries extra;
    for (const auto& e : entries) {
        if (e.dirtyLocators.Intersects(HdXformSchema::GetDefaultLocator())) {
            // descendants of e.primPath need xform re-pull
            for (const SdfPath& child :
                 _GetInputSceneIndex()->GetChildPrimPaths(e.primPath)) {
                extra.emplace_back(child, HdXformSchema::GetDefaultLocator());
            }
        }
    }
    _SendPrimsDirtied(entries);
    if (!extra.empty()) _SendPrimsDirtied(extra);
}

PXR_NAMESPACE_CLOSE_SCOPE
