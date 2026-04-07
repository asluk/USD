//
// Copyright 2026 NVIDIA Corporation
//
// Licensed under the terms set forth in the LICENSE.txt file available at
// https://openusd.org/license.
//
#include "pxr/usd/usdSourceId/sourceIdAPI.h"
#include "pxr/usd/usd/schemaRegistry.h"
#include "pxr/usd/usd/typed.h"
#include "pxr/usd/usd/prim.h"

#include "pxr/base/tf/token.h"
#include "pxr/base/vt/dictionary.h"
#include "pxr/base/vt/value.h"

PXR_NAMESPACE_OPEN_SCOPE

TF_DEFINE_PRIVATE_TOKENS(
    _tokens,
    (sourceIds)
    (primaryId)
    (revision)
    (metadata)
);

// Register the schema with the TfType system.
TF_REGISTRY_FUNCTION(TfType)
{
    TfType::Define<UsdSourceIdAPI,
        TfType::Bases< UsdAPISchemaBase > >();
}

/* virtual */
UsdSourceIdAPI::~UsdSourceIdAPI()
{
}

/* static */
UsdSourceIdAPI
UsdSourceIdAPI::Get(const UsdStagePtr &stage, const SdfPath &path)
{
    if (!stage) {
        TF_CODING_ERROR("Invalid stage");
        return UsdSourceIdAPI();
    }
    return UsdSourceIdAPI(stage->GetPrimAtPath(path));
}

/* virtual */
UsdSchemaKind UsdSourceIdAPI::_GetSchemaKind() const
{
    return UsdSourceIdAPI::schemaKind;
}

/* static */
bool
UsdSourceIdAPI::CanApply(const UsdPrim &prim, std::string *whyNot)
{
    return prim.CanApplyAPI<UsdSourceIdAPI>(whyNot);
}

/* static */
UsdSourceIdAPI
UsdSourceIdAPI::Apply(const UsdPrim &prim)
{
    if (prim.ApplyAPI<UsdSourceIdAPI>()) {
        return UsdSourceIdAPI(prim);
    }
    return UsdSourceIdAPI();
}

/* static */
const TfType &
UsdSourceIdAPI::_GetStaticTfType()
{
    static TfType tfType = TfType::Find<UsdSourceIdAPI>();
    return tfType;
}

/* static */
bool
UsdSourceIdAPI::_IsTypedSchema()
{
    static bool isTyped = _GetStaticTfType().IsA<UsdTyped>();
    return isTyped;
}

// ========================================================================= //
// Private Helpers
// ========================================================================= //

VtDictionary
UsdSourceIdAPI::_GetSourceIdsDict() const
{
    VtValue val = GetPrim().GetAssetInfoByKey(_tokens->sourceIds);
    if (val.IsHolding<VtDictionary>()) {
        return val.UncheckedGet<VtDictionary>();
    }
    return VtDictionary();
}

void
UsdSourceIdAPI::_SetSourceIdsDict(const VtDictionary &sourceIds) const
{
    GetPrim().SetAssetInfoByKey(_tokens->sourceIds, VtValue(sourceIds));
}

// ========================================================================= //
// Source Identifier Accessors
// ========================================================================= //

std::vector<TfToken>
UsdSourceIdAPI::GetDomains() const
{
    std::vector<TfToken> domains;
    VtDictionary sourceIds = _GetSourceIdsDict();
    domains.reserve(sourceIds.size());
    for (const auto &entry : sourceIds) {
        domains.push_back(TfToken(entry.first));
    }
    return domains;
}

bool
UsdSourceIdAPI::GetPrimaryId(const TfToken &domain,
                              std::string *primaryId) const
{
    VtDictionary sourceIds = _GetSourceIdsDict();
    auto domainIt = sourceIds.find(domain.GetString());
    if (domainIt == sourceIds.end() ||
        !domainIt->second.IsHolding<VtDictionary>()) {
        return false;
    }
    const VtDictionary &domainDict =
        domainIt->second.UncheckedGet<VtDictionary>();
    auto idIt = domainDict.find(_tokens->primaryId.GetString());
    if (idIt == domainDict.end() ||
        !idIt->second.IsHolding<std::string>()) {
        return false;
    }
    *primaryId = idIt->second.UncheckedGet<std::string>();
    return true;
}

bool
UsdSourceIdAPI::GetRevision(const TfToken &domain,
                             std::string *revision) const
{
    VtDictionary sourceIds = _GetSourceIdsDict();
    auto domainIt = sourceIds.find(domain.GetString());
    if (domainIt == sourceIds.end() ||
        !domainIt->second.IsHolding<VtDictionary>()) {
        return false;
    }
    const VtDictionary &domainDict =
        domainIt->second.UncheckedGet<VtDictionary>();
    auto revIt = domainDict.find(_tokens->revision.GetString());
    if (revIt == domainDict.end() ||
        !revIt->second.IsHolding<std::string>()) {
        return false;
    }
    *revision = revIt->second.UncheckedGet<std::string>();
    return true;
}

bool
UsdSourceIdAPI::GetDomainMetadata(const TfToken &domain,
                                   VtDictionary *metadata) const
{
    VtDictionary sourceIds = _GetSourceIdsDict();
    auto domainIt = sourceIds.find(domain.GetString());
    if (domainIt == sourceIds.end() ||
        !domainIt->second.IsHolding<VtDictionary>()) {
        return false;
    }
    const VtDictionary &domainDict =
        domainIt->second.UncheckedGet<VtDictionary>();
    auto metaIt = domainDict.find(_tokens->metadata.GetString());
    if (metaIt == domainDict.end() ||
        !metaIt->second.IsHolding<VtDictionary>()) {
        return false;
    }
    *metadata = metaIt->second.UncheckedGet<VtDictionary>();
    return true;
}

bool
UsdSourceIdAPI::GetDomainData(const TfToken &domain,
                               VtDictionary *data) const
{
    VtDictionary sourceIds = _GetSourceIdsDict();
    auto domainIt = sourceIds.find(domain.GetString());
    if (domainIt == sourceIds.end() ||
        !domainIt->second.IsHolding<VtDictionary>()) {
        return false;
    }
    *data = domainIt->second.UncheckedGet<VtDictionary>();
    return true;
}

bool
UsdSourceIdAPI::GetAllSourceIds(VtDictionary *sourceIds) const
{
    VtDictionary dict = _GetSourceIdsDict();
    if (dict.empty()) {
        return false;
    }
    *sourceIds = dict;
    return true;
}

void
UsdSourceIdAPI::SetSourceId(const TfToken &domain,
                             const std::string &primaryId,
                             const std::string &revision) const
{
    VtDictionary sourceIds = _GetSourceIdsDict();

    VtDictionary domainDict;
    auto it = sourceIds.find(domain.GetString());
    if (it != sourceIds.end() && it->second.IsHolding<VtDictionary>()) {
        domainDict = it->second.UncheckedGet<VtDictionary>();
    }

    domainDict[_tokens->primaryId.GetString()] = VtValue(primaryId);
    if (!revision.empty()) {
        domainDict[_tokens->revision.GetString()] = VtValue(revision);
    }

    sourceIds[domain.GetString()] = VtValue(domainDict);
    _SetSourceIdsDict(sourceIds);
}

void
UsdSourceIdAPI::SetDomainMetadata(const TfToken &domain,
                                   const VtDictionary &metadata) const
{
    VtDictionary sourceIds = _GetSourceIdsDict();

    VtDictionary domainDict;
    auto it = sourceIds.find(domain.GetString());
    if (it != sourceIds.end() && it->second.IsHolding<VtDictionary>()) {
        domainDict = it->second.UncheckedGet<VtDictionary>();
    }

    domainDict[_tokens->metadata.GetString()] = VtValue(metadata);

    sourceIds[domain.GetString()] = VtValue(domainDict);
    _SetSourceIdsDict(sourceIds);
}

void
UsdSourceIdAPI::SetDomainData(const TfToken &domain,
                               const VtDictionary &data) const
{
    VtDictionary sourceIds = _GetSourceIdsDict();
    sourceIds[domain.GetString()] = VtValue(data);
    _SetSourceIdsDict(sourceIds);
}

void
UsdSourceIdAPI::ClearDomain(const TfToken &domain) const
{
    VtDictionary sourceIds = _GetSourceIdsDict();
    sourceIds.erase(domain.GetString());
    if (sourceIds.empty()) {
        ClearAllSourceIds();
    } else {
        _SetSourceIdsDict(sourceIds);
    }
}

void
UsdSourceIdAPI::ClearAllSourceIds() const
{
    // Remove the sourceIds key from assetInfo entirely.
    // We do this by setting it to an empty dict, then clearing.
    VtDictionary assetInfo = GetPrim().GetAssetInfo();
    assetInfo.erase(_tokens->sourceIds.GetString());
    GetPrim().SetAssetInfo(assetInfo);
}

PXR_NAMESPACE_CLOSE_SCOPE
