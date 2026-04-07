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
    // Query all applied API schemas and filter for our instances.
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

// ========================================================================= //
// Property Name Helper
// ========================================================================= //

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
// Typed Property Accessors
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

/* static */
const TfTokenVector &
UsdSourceIdentifierAPI::GetSchemaAttributeNames(
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
