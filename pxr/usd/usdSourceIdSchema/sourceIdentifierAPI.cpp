//
// Copyright 2026 NVIDIA Corporation
//
// Licensed under the terms set forth in the LICENSE.txt file available at
// https://openusd.org/license.
//
#include "pxr/usd/usdSourceIdSchema/sourceIdentifierAPI.h"
#include "pxr/usd/usd/schemaRegistry.h"
#include "pxr/usd/usd/typed.h"
#include "pxr/usd/usd/prim.h"
#include "pxr/usd/usd/attribute.h"
#include "pxr/usd/sdf/types.h"

#include "pxr/base/tf/staticTokens.h"
#include "pxr/base/tf/token.h"

PXR_NAMESPACE_OPEN_SCOPE

TF_DEFINE_PRIVATE_TOKENS(
    _tokens,
    ((schemaPrefix, "sourceIdentifier"))
    (primaryId)
    (revision)
    (domain)
    (label)
);

// Register the schema with the TfType system.
TF_REGISTRY_FUNCTION(TfType)
{
    TfType::Define<UsdSourceIdSchemaAPI,
        TfType::Bases< UsdAPISchemaBase > >();
}

/* virtual */
UsdSourceIdSchemaAPI::~UsdSourceIdSchemaAPI()
{
}

/* static */
UsdSourceIdSchemaAPI
UsdSourceIdSchemaAPI::Get(const UsdStagePtr &stage, const SdfPath &path,
                             const TfToken &name)
{
    if (!stage) {
        TF_CODING_ERROR("Invalid stage");
        return UsdSourceIdSchemaAPI();
    }
    return UsdSourceIdSchemaAPI(stage->GetPrimAtPath(path), name);
}

/* static */
UsdSourceIdSchemaAPI
UsdSourceIdSchemaAPI::Get(const UsdPrim &prim, const TfToken &name)
{
    return UsdSourceIdSchemaAPI(prim, name);
}

/* virtual */
UsdSchemaKind UsdSourceIdSchemaAPI::_GetSchemaKind() const
{
    return UsdSourceIdSchemaAPI::schemaKind;
}

/* static */
bool
UsdSourceIdSchemaAPI::CanApply(const UsdPrim &prim, const TfToken &name,
                                  std::string *whyNot)
{
    return prim.CanApplyAPI<UsdSourceIdSchemaAPI>(name, whyNot);
}

/* static */
UsdSourceIdSchemaAPI
UsdSourceIdSchemaAPI::Apply(const UsdPrim &prim, const TfToken &name)
{
    if (prim.ApplyAPI<UsdSourceIdSchemaAPI>(name)) {
        return UsdSourceIdSchemaAPI(prim, name);
    }
    return UsdSourceIdSchemaAPI();
}

/* static */
std::vector<TfToken>
UsdSourceIdSchemaAPI::GetAll(const UsdPrim &prim)
{
    // Query all applied API schemas and filter for our instances.
    std::vector<TfToken> result;
    const TfTokenVector &appliedSchemas = prim.GetAppliedSchemas();
    const std::string prefix = "SourceIdSchemaAPI:";
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
UsdSourceIdSchemaAPI::_GetStaticTfType()
{
    static TfType tfType = TfType::Find<UsdSourceIdSchemaAPI>();
    return tfType;
}

/* static */
bool
UsdSourceIdSchemaAPI::_IsTypedSchema()
{
    static bool isTyped = _GetStaticTfType().IsA<UsdTyped>();
    return isTyped;
}

// ========================================================================= //
// Property Name Helper
// ========================================================================= //

TfToken
UsdSourceIdSchemaAPI::_GetNamespacedPropertyName(
    const TfToken &suffix) const
{
    const TfToken &instanceName = GetName();
    return TfToken(_tokens->schemaPrefix.GetString() + ":" +
                   instanceName.GetString() + ":" +
                   suffix.GetString());
}

// ========================================================================= //
// Typed Property Accessors
// ========================================================================= //

UsdAttribute
UsdSourceIdSchemaAPI::GetPrimaryIdAttr() const
{
    return GetPrim().GetAttribute(
        _GetNamespacedPropertyName(_tokens->primaryId));
}

UsdAttribute
UsdSourceIdSchemaAPI::CreatePrimaryIdAttr(
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
UsdSourceIdSchemaAPI::GetRevisionAttr() const
{
    return GetPrim().GetAttribute(
        _GetNamespacedPropertyName(_tokens->revision));
}

UsdAttribute
UsdSourceIdSchemaAPI::CreateRevisionAttr(
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
UsdSourceIdSchemaAPI::GetDomainAttr() const
{
    return GetPrim().GetAttribute(
        _GetNamespacedPropertyName(_tokens->domain));
}

UsdAttribute
UsdSourceIdSchemaAPI::CreateDomainAttr(
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
UsdSourceIdSchemaAPI::GetLabelAttr() const
{
    return GetPrim().GetAttribute(
        _GetNamespacedPropertyName(_tokens->label));
}

UsdAttribute
UsdSourceIdSchemaAPI::CreateLabelAttr(
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

/* static */
const TfTokenVector &
UsdSourceIdSchemaAPI::GetSchemaAttributeNames(
    bool includeInherited, const TfToken &instanceName)
{
    static TfTokenVector names = {
        TfToken("primaryId"),
        TfToken("revision"),
        TfToken("domain"),
        TfToken("label")
    };
    // In a real codegen this would handle instanceName prefixing.
    // For now, return the base attribute names.
    return names;
}

PXR_NAMESPACE_CLOSE_SCOPE
