//
// Copyright 2016 Pixar
//
// Licensed under the terms set forth in the LICENSE.txt file available at
// https://openusd.org/license.
//
#include "pxr/usd/usdSourceIdHybrid/sourceIdHybridAPI.h"
#include "pxr/usd/usd/schemaRegistry.h"
#include "pxr/usd/usd/typed.h"

#include "pxr/usd/sdf/types.h"
#include "pxr/usd/sdf/assetPath.h"

PXR_NAMESPACE_OPEN_SCOPE

// Register the schema with the TfType system.
TF_REGISTRY_FUNCTION(TfType)
{
    TfType::Define<UsdSourceIdHybridSourceIdHybridAPI,
        TfType::Bases< UsdAPISchemaBase > >();
    
}

/* virtual */
UsdSourceIdHybridSourceIdHybridAPI::~UsdSourceIdHybridSourceIdHybridAPI()
{
}

/* static */
UsdSourceIdHybridSourceIdHybridAPI
UsdSourceIdHybridSourceIdHybridAPI::Get(const UsdStagePtr &stage, const SdfPath &path)
{
    if (!stage) {
        TF_CODING_ERROR("Invalid stage");
        return UsdSourceIdHybridSourceIdHybridAPI();
    }
    TfToken name;
    if (!IsSourceIdHybridAPIPath(path, &name)) {
        TF_CODING_ERROR("Invalid sourceIdentifier path <%s>.", path.GetText());
        return UsdSourceIdHybridSourceIdHybridAPI();
    }
    return UsdSourceIdHybridSourceIdHybridAPI(stage->GetPrimAtPath(path.GetPrimPath()), name);
}

UsdSourceIdHybridSourceIdHybridAPI
UsdSourceIdHybridSourceIdHybridAPI::Get(const UsdPrim &prim, const TfToken &name)
{
    return UsdSourceIdHybridSourceIdHybridAPI(prim, name);
}

/* static */
std::vector<UsdSourceIdHybridSourceIdHybridAPI>
UsdSourceIdHybridSourceIdHybridAPI::GetAll(const UsdPrim &prim)
{
    std::vector<UsdSourceIdHybridSourceIdHybridAPI> schemas;
    
    for (const auto &schemaName :
         UsdAPISchemaBase::_GetMultipleApplyInstanceNames(prim, _GetStaticTfType())) {
        schemas.emplace_back(prim, schemaName);
    }

    return schemas;
}


/* static */
bool 
UsdSourceIdHybridSourceIdHybridAPI::IsSchemaPropertyBaseName(const TfToken &baseName)
{
    static TfTokenVector attrsAndRels = {
        UsdSchemaRegistry::GetMultipleApplyNameTemplateBaseName(
            UsdSourceIdHybridTokens->sourceIdentifier_MultipleApplyTemplate_PrimaryId),
        UsdSchemaRegistry::GetMultipleApplyNameTemplateBaseName(
            UsdSourceIdHybridTokens->sourceIdentifier_MultipleApplyTemplate_Revision),
        UsdSchemaRegistry::GetMultipleApplyNameTemplateBaseName(
            UsdSourceIdHybridTokens->sourceIdentifier_MultipleApplyTemplate_Domain),
        UsdSchemaRegistry::GetMultipleApplyNameTemplateBaseName(
            UsdSourceIdHybridTokens->sourceIdentifier_MultipleApplyTemplate_Label),
    };

    return find(attrsAndRels.begin(), attrsAndRels.end(), baseName)
            != attrsAndRels.end();
}

/* static */
bool
UsdSourceIdHybridSourceIdHybridAPI::IsSourceIdHybridAPIPath(
    const SdfPath &path, TfToken *name)
{
    if (!path.IsPropertyPath()) {
        return false;
    }

    std::string propertyName = path.GetName();
    TfTokenVector tokens = SdfPath::TokenizeIdentifierAsTokens(propertyName);

    // The baseName of the  path can't be one of the 
    // schema properties. We should validate this in the creation (or apply)
    // API.
    TfToken baseName = *tokens.rbegin();
    if (IsSchemaPropertyBaseName(baseName)) {
        return false;
    }

    if (tokens.size() >= 2
        && tokens[0] == UsdSourceIdHybridTokens->sourceIdentifier) {
        *name = TfToken(propertyName.substr(
           UsdSourceIdHybridTokens->sourceIdentifier.GetString().size() + 1));
        return true;
    }

    return false;
}

/* virtual */
UsdSchemaKind UsdSourceIdHybridSourceIdHybridAPI::_GetSchemaKind() const
{
    return UsdSourceIdHybridSourceIdHybridAPI::schemaKind;
}

/* static */
bool
UsdSourceIdHybridSourceIdHybridAPI::CanApply(
    const UsdPrim &prim, const TfToken &name, std::string *whyNot)
{
    return prim.CanApplyAPI<UsdSourceIdHybridSourceIdHybridAPI>(name, whyNot);
}

/* static */
UsdSourceIdHybridSourceIdHybridAPI
UsdSourceIdHybridSourceIdHybridAPI::Apply(const UsdPrim &prim, const TfToken &name)
{
    if (prim.ApplyAPI<UsdSourceIdHybridSourceIdHybridAPI>(name)) {
        return UsdSourceIdHybridSourceIdHybridAPI(prim, name);
    }
    return UsdSourceIdHybridSourceIdHybridAPI();
}

/* static */
const TfType &
UsdSourceIdHybridSourceIdHybridAPI::_GetStaticTfType()
{
    static TfType tfType = TfType::Find<UsdSourceIdHybridSourceIdHybridAPI>();
    return tfType;
}

/* static */
bool 
UsdSourceIdHybridSourceIdHybridAPI::_IsTypedSchema()
{
    static bool isTyped = _GetStaticTfType().IsA<UsdTyped>();
    return isTyped;
}

/* virtual */
const TfType &
UsdSourceIdHybridSourceIdHybridAPI::_GetTfType() const
{
    return _GetStaticTfType();
}

/// Returns the property name prefixed with the correct namespace prefix, which
/// is composed of the the API's propertyNamespacePrefix metadata and the
/// instance name of the API.
static inline
TfToken
_GetNamespacedPropertyName(const TfToken instanceName, const TfToken propName)
{
    return UsdSchemaRegistry::MakeMultipleApplyNameInstance(propName, instanceName);
}

UsdAttribute
UsdSourceIdHybridSourceIdHybridAPI::GetPrimaryIdAttr() const
{
    return GetPrim().GetAttribute(
        _GetNamespacedPropertyName(
            GetName(),
            UsdSourceIdHybridTokens->sourceIdentifier_MultipleApplyTemplate_PrimaryId));
}

UsdAttribute
UsdSourceIdHybridSourceIdHybridAPI::CreatePrimaryIdAttr(VtValue const &defaultValue, bool writeSparsely) const
{
    return UsdSchemaBase::_CreateAttr(
                       _GetNamespacedPropertyName(
                            GetName(),
                           UsdSourceIdHybridTokens->sourceIdentifier_MultipleApplyTemplate_PrimaryId),
                       SdfValueTypeNames->String,
                       /* custom = */ false,
                       SdfVariabilityVarying,
                       defaultValue,
                       writeSparsely);
}

UsdAttribute
UsdSourceIdHybridSourceIdHybridAPI::GetRevisionAttr() const
{
    return GetPrim().GetAttribute(
        _GetNamespacedPropertyName(
            GetName(),
            UsdSourceIdHybridTokens->sourceIdentifier_MultipleApplyTemplate_Revision));
}

UsdAttribute
UsdSourceIdHybridSourceIdHybridAPI::CreateRevisionAttr(VtValue const &defaultValue, bool writeSparsely) const
{
    return UsdSchemaBase::_CreateAttr(
                       _GetNamespacedPropertyName(
                            GetName(),
                           UsdSourceIdHybridTokens->sourceIdentifier_MultipleApplyTemplate_Revision),
                       SdfValueTypeNames->String,
                       /* custom = */ false,
                       SdfVariabilityVarying,
                       defaultValue,
                       writeSparsely);
}

UsdAttribute
UsdSourceIdHybridSourceIdHybridAPI::GetDomainAttr() const
{
    return GetPrim().GetAttribute(
        _GetNamespacedPropertyName(
            GetName(),
            UsdSourceIdHybridTokens->sourceIdentifier_MultipleApplyTemplate_Domain));
}

UsdAttribute
UsdSourceIdHybridSourceIdHybridAPI::CreateDomainAttr(VtValue const &defaultValue, bool writeSparsely) const
{
    return UsdSchemaBase::_CreateAttr(
                       _GetNamespacedPropertyName(
                            GetName(),
                           UsdSourceIdHybridTokens->sourceIdentifier_MultipleApplyTemplate_Domain),
                       SdfValueTypeNames->Token,
                       /* custom = */ false,
                       SdfVariabilityVarying,
                       defaultValue,
                       writeSparsely);
}

UsdAttribute
UsdSourceIdHybridSourceIdHybridAPI::GetLabelAttr() const
{
    return GetPrim().GetAttribute(
        _GetNamespacedPropertyName(
            GetName(),
            UsdSourceIdHybridTokens->sourceIdentifier_MultipleApplyTemplate_Label));
}

UsdAttribute
UsdSourceIdHybridSourceIdHybridAPI::CreateLabelAttr(VtValue const &defaultValue, bool writeSparsely) const
{
    return UsdSchemaBase::_CreateAttr(
                       _GetNamespacedPropertyName(
                            GetName(),
                           UsdSourceIdHybridTokens->sourceIdentifier_MultipleApplyTemplate_Label),
                       SdfValueTypeNames->String,
                       /* custom = */ false,
                       SdfVariabilityVarying,
                       defaultValue,
                       writeSparsely);
}

namespace {
static inline TfTokenVector
_ConcatenateAttributeNames(const TfTokenVector& left,const TfTokenVector& right)
{
    TfTokenVector result;
    result.reserve(left.size() + right.size());
    result.insert(result.end(), left.begin(), left.end());
    result.insert(result.end(), right.begin(), right.end());
    return result;
}
}

/*static*/
const TfTokenVector&
UsdSourceIdHybridSourceIdHybridAPI::GetSchemaAttributeNames(bool includeInherited)
{
    static TfTokenVector localNames = {
        UsdSourceIdHybridTokens->sourceIdentifier_MultipleApplyTemplate_PrimaryId,
        UsdSourceIdHybridTokens->sourceIdentifier_MultipleApplyTemplate_Revision,
        UsdSourceIdHybridTokens->sourceIdentifier_MultipleApplyTemplate_Domain,
        UsdSourceIdHybridTokens->sourceIdentifier_MultipleApplyTemplate_Label,
    };
    static TfTokenVector allNames =
        _ConcatenateAttributeNames(
            UsdAPISchemaBase::GetSchemaAttributeNames(true),
            localNames);

    if (includeInherited)
        return allNames;
    else
        return localNames;
}

/*static*/
TfTokenVector
UsdSourceIdHybridSourceIdHybridAPI::GetSchemaAttributeNames(
    bool includeInherited, const TfToken &instanceName)
{
    const TfTokenVector &attrNames = GetSchemaAttributeNames(includeInherited);
    if (instanceName.IsEmpty()) {
        return attrNames;
    }
    TfTokenVector result;
    result.reserve(attrNames.size());
    for (const TfToken &attrName : attrNames) {
        result.push_back(
            UsdSchemaRegistry::MakeMultipleApplyNameInstance(attrName, instanceName));
    }
    return result;
}

PXR_NAMESPACE_CLOSE_SCOPE

// ===================================================================== //
// Feel free to add custom code below this line. It will be preserved by
// the code generator.
//
// Just remember to wrap code in the appropriate delimiters:
// 'PXR_NAMESPACE_OPEN_SCOPE', 'PXR_NAMESPACE_CLOSE_SCOPE'.
// ===================================================================== //
// --(BEGIN CUSTOM CODE)--
