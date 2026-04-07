//
// Copyright 2016 Pixar
//
// Licensed under the terms set forth in the LICENSE.txt file available at
// https://openusd.org/license.
//
#include "pxr/usd/usdSourceId/sourceIdAPI.h"
#include "pxr/usd/usd/schemaRegistry.h"
#include "pxr/usd/usd/typed.h"

#include "pxr/usd/sdf/types.h"
#include "pxr/usd/sdf/assetPath.h"

PXR_NAMESPACE_OPEN_SCOPE

// Register the schema with the TfType system.
TF_REGISTRY_FUNCTION(TfType)
{
    TfType::Define<UsdSourceIdSourceIdAPI,
        TfType::Bases< UsdAPISchemaBase > >();
    
}

/* virtual */
UsdSourceIdSourceIdAPI::~UsdSourceIdSourceIdAPI()
{
}

/* static */
UsdSourceIdSourceIdAPI
UsdSourceIdSourceIdAPI::Get(const UsdStagePtr &stage, const SdfPath &path)
{
    if (!stage) {
        TF_CODING_ERROR("Invalid stage");
        return UsdSourceIdSourceIdAPI();
    }
    return UsdSourceIdSourceIdAPI(stage->GetPrimAtPath(path));
}


/* virtual */
UsdSchemaKind UsdSourceIdSourceIdAPI::_GetSchemaKind() const
{
    return UsdSourceIdSourceIdAPI::schemaKind;
}

/* static */
bool
UsdSourceIdSourceIdAPI::CanApply(
    const UsdPrim &prim, std::string *whyNot)
{
    return prim.CanApplyAPI<UsdSourceIdSourceIdAPI>(whyNot);
}

/* static */
UsdSourceIdSourceIdAPI
UsdSourceIdSourceIdAPI::Apply(const UsdPrim &prim)
{
    if (prim.ApplyAPI<UsdSourceIdSourceIdAPI>()) {
        return UsdSourceIdSourceIdAPI(prim);
    }
    return UsdSourceIdSourceIdAPI();
}

/* static */
const TfType &
UsdSourceIdSourceIdAPI::_GetStaticTfType()
{
    static TfType tfType = TfType::Find<UsdSourceIdSourceIdAPI>();
    return tfType;
}

/* static */
bool 
UsdSourceIdSourceIdAPI::_IsTypedSchema()
{
    static bool isTyped = _GetStaticTfType().IsA<UsdTyped>();
    return isTyped;
}

/* virtual */
const TfType &
UsdSourceIdSourceIdAPI::_GetTfType() const
{
    return _GetStaticTfType();
}

/*static*/
const TfTokenVector&
UsdSourceIdSourceIdAPI::GetSchemaAttributeNames(bool includeInherited)
{
    static TfTokenVector localNames;
    static TfTokenVector allNames =
        UsdAPISchemaBase::GetSchemaAttributeNames(true);

    if (includeInherited)
        return allNames;
    else
        return localNames;
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
