//
// Copyright 2026 NVIDIA Corporation
//
// Licensed under the terms set forth in the LICENSE.txt file available at
// https://openusd.org/license.
//
#include "pxr/usd/usdSourceIdHybrid/sourceIdentifierAPI.h"
#include "pxr/usd/usd/schemaRegistry.h"
#include "pxr/usd/usd/typed.h"
#include "pxr/usd/usd/prim.h"
#include "pxr/usd/usd/attribute.h"
#include "pxr/usd/sdf/types.h"

#include "pxr/base/tf/staticTokens.h"

PXR_NAMESPACE_OPEN_SCOPE

TF_DEFINE_PRIVATE_TOKENS(
    _tokens,
    ((schemaPrefix, "sourceIdentifier"))
    (primaryId)
    (revision)
    (domain)
    (label)
    (sourceIds)
);

TF_REGISTRY_FUNCTION(TfType)
{
    TfType::Define<UsdSourceIdentifierAPI,
        TfType::Bases< UsdAPISchemaBase > >();
}

/* virtual */
UsdSourceIdentifierAPI::~UsdSourceIdentifierAPI()
{
}

/* static */
UsdSourceIdentifierAPI
UsdSourceIdentifierAPI::Get(const UsdStagePtr &stage, const SdfPath &path,
                             const TfToken &name)
{
    if (!stage) {
        TF_CODING_ERROR("Invalid stage");
        return UsdSourceIdentifierAPI();
    }
    return UsdSourceIdentifierAPI(stage->GetPrimAtPath(path), name);
}

/* static */
UsdSourceIdentifierAPI
UsdSourceIdentifierAPI::Get(const UsdPrim &prim, const TfToken &name)
{
    return UsdSourceIdentifierAPI(prim, name);
}

/* virtual */
UsdSchemaKind UsdSourceIdentifierAPI::_GetSchemaKind() const
{
    return UsdSourceIdentifierAPI::schemaKind;
}

/* static */
bool
UsdSourceIdentifierAPI::CanApply(const UsdPrim &prim, const TfToken &name,
                                  std::string *whyNot)
{
    return prim.CanApplyAPI<UsdSourceIdentifierAPI>(name, whyNot);
}

/* static */
UsdSourceIdentifierAPI
UsdSourceIdentifierAPI::Apply(const UsdPrim &prim, const TfToken &name)
{
    if (prim.ApplyAPI<UsdSourceIdentifierAPI>(name)) {
        return UsdSourceIdentifierAPI(prim, name);
    }
    return UsdSourceIdentifierAPI();
}

/* static */
std::vector<TfToken>
UsdSourceIdentifierAPI::GetAll(const UsdPrim &prim)
{
    std::vector<TfToken> result;
    const TfTokenVector &appliedSchemas = prim.GetAppliedSchemas();
    const std::string prefix = "SourceIdentifierAPI:";
    for (const auto &schema : appliedSchemas) {
        const std::string &s = schema.GetString();
        if (s.substr(0, prefix.size()) == prefix) {
            result.push_back(TfToken(s.substr(prefix.size())));
        }
    }
    return result;
}

/* static */
const TfType &
UsdSourceIdentifierAPI::_GetStaticTfType()
{
    static TfType tfType = TfType::Find<UsdSourceIdentifierAPI>();
    return tfType;
}

/* static */
bool
UsdSourceIdentifierAPI::_IsTypedSchema()
{
    static bool isTyped = _GetStaticTfType().IsA<UsdTyped>();
    return isTyped;
}

TfToken
UsdSourceIdentifierAPI::_GetNamespacedPropertyName(
    const TfToken &suffix) const
{
    const TfToken &instanceName = GetName();
    return TfToken(_tokens->schemaPrefix.GetString() + ":" +
                   instanceName.GetString() + ":" +
                   suffix.GetString());
}

// ========================================================================= //
// Schema Property Accessors
// ========================================================================= //

UsdAttribute
UsdSourceIdentifierAPI::GetPrimaryIdAttr() const
{
    return GetPrim().GetAttribute(
        _GetNamespacedPropertyName(_tokens->primaryId));
}

UsdAttribute
UsdSourceIdentifierAPI::CreatePrimaryIdAttr(
    const VtValue &defaultValue, bool writeSparsely) const
{
    return UsdSchemaBase::_CreateAttr(
        _GetNamespacedPropertyName(_tokens->primaryId),
        SdfValueTypeNames->String,
        /* custom = */ false,
        SdfVariabilityUniform,
        defaultValue,
        writeSparsely);
}

UsdAttribute
UsdSourceIdentifierAPI::GetRevisionAttr() const
{
    return GetPrim().GetAttribute(
        _GetNamespacedPropertyName(_tokens->revision));
}

UsdAttribute
UsdSourceIdentifierAPI::CreateRevisionAttr(
    const VtValue &defaultValue, bool writeSparsely) const
{
    return UsdSchemaBase::_CreateAttr(
        _GetNamespacedPropertyName(_tokens->revision),
        SdfValueTypeNames->String,
        /* custom = */ false,
        SdfVariabilityUniform,
        defaultValue,
        writeSparsely);
}

UsdAttribute
UsdSourceIdentifierAPI::GetDomainAttr() const
{
    return GetPrim().GetAttribute(
        _GetNamespacedPropertyName(_tokens->domain));
}

UsdAttribute
UsdSourceIdentifierAPI::CreateDomainAttr(
    const VtValue &defaultValue, bool writeSparsely) const
{
    return UsdSchemaBase::_CreateAttr(
        _GetNamespacedPropertyName(_tokens->domain),
        SdfValueTypeNames->Token,
        /* custom = */ false,
        SdfVariabilityUniform,
        defaultValue,
        writeSparsely);
}

UsdAttribute
UsdSourceIdentifierAPI::GetLabelAttr() const
{
    return GetPrim().GetAttribute(
        _GetNamespacedPropertyName(_tokens->label));
}

UsdAttribute
UsdSourceIdentifierAPI::CreateLabelAttr(
    const VtValue &defaultValue, bool writeSparsely) const
{
    return UsdSchemaBase::_CreateAttr(
        _GetNamespacedPropertyName(_tokens->label),
        SdfValueTypeNames->String,
        /* custom = */ false,
        SdfVariabilityUniform,
        defaultValue,
        writeSparsely);
}

// ========================================================================= //
// AssetInfo Metadata Accessors
// ========================================================================= //

bool
UsdSourceIdentifierAPI::GetDomainMetadata(VtDictionary *metadata) const
{
    const TfToken &instanceName = GetName();
    VtValue sourceIdsVal = GetPrim().GetAssetInfoByKey(_tokens->sourceIds);
    if (!sourceIdsVal.IsHolding<VtDictionary>()) {
        return false;
    }
    const VtDictionary &sourceIds =
        sourceIdsVal.UncheckedGet<VtDictionary>();
    auto it = sourceIds.find(instanceName.GetString());
    if (it == sourceIds.end() ||
        !it->second.IsHolding<VtDictionary>()) {
        return false;
    }
    *metadata = it->second.UncheckedGet<VtDictionary>();
    return true;
}

void
UsdSourceIdentifierAPI::SetDomainMetadata(
    const VtDictionary &metadata) const
{
    const TfToken &instanceName = GetName();
    VtValue sourceIdsVal = GetPrim().GetAssetInfoByKey(_tokens->sourceIds);
    VtDictionary sourceIds;
    if (sourceIdsVal.IsHolding<VtDictionary>()) {
        sourceIds = sourceIdsVal.UncheckedGet<VtDictionary>();
    }
    sourceIds[instanceName.GetString()] = VtValue(metadata);
    GetPrim().SetAssetInfoByKey(_tokens->sourceIds, VtValue(sourceIds));
}

VtValue
UsdSourceIdentifierAPI::GetDomainMetadataByKey(const TfToken &key) const
{
    VtDictionary metadata;
    if (!GetDomainMetadata(&metadata)) {
        return VtValue();
    }
    auto it = metadata.find(key.GetString());
    if (it == metadata.end()) {
        return VtValue();
    }
    return it->second;
}

void
UsdSourceIdentifierAPI::SetDomainMetadataByKey(
    const TfToken &key, const VtValue &value) const
{
    VtDictionary metadata;
    GetDomainMetadata(&metadata);  // OK if empty
    metadata[key.GetString()] = value;
    SetDomainMetadata(metadata);
}

void
UsdSourceIdentifierAPI::ClearDomainMetadata() const
{
    const TfToken &instanceName = GetName();
    VtValue sourceIdsVal = GetPrim().GetAssetInfoByKey(_tokens->sourceIds);
    if (!sourceIdsVal.IsHolding<VtDictionary>()) {
        return;
    }
    VtDictionary sourceIds = sourceIdsVal.UncheckedGet<VtDictionary>();
    sourceIds.erase(instanceName.GetString());
    if (sourceIds.empty()) {
        VtDictionary assetInfo = GetPrim().GetAssetInfo();
        assetInfo.erase(_tokens->sourceIds.GetString());
        GetPrim().SetAssetInfo(assetInfo);
    } else {
        GetPrim().SetAssetInfoByKey(_tokens->sourceIds, VtValue(sourceIds));
    }
}

PXR_NAMESPACE_CLOSE_SCOPE
