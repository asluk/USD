//
// Copyright 2026 NVIDIA Corporation
//
// Licensed under the terms set forth in the LICENSE.txt file available at
// https://openusd.org/license.
//
#ifndef PXR_USD_USD_SOURCE_ID_HYBRID_SOURCE_IDENTIFIER_API_H
#define PXR_USD_USD_SOURCE_ID_HYBRID_SOURCE_IDENTIFIER_API_H

/// \file usdSourceIdHybrid/sourceIdentifierAPI.h

#include "pxr/pxr.h"
#include "pxr/usd/usdSourceIdHybrid/api.h"
#include "pxr/usd/usd/apiSchemaBase.h"
#include "pxr/usd/usd/prim.h"
#include "pxr/usd/usd/stage.h"
#include "pxr/usd/usd/attribute.h"

#include "pxr/base/vt/dictionary.h"
#include "pxr/base/vt/value.h"
#include "pxr/base/tf/token.h"
#include "pxr/base/tf/type.h"

#include <string>
#include <vector>

PXR_NAMESPACE_OPEN_SCOPE

/// \class UsdSourceIdHybridAPI
///
/// Hybrid approach (Approach C): Multi-apply schema with typed common
/// properties for discoverability and validation, plus assetInfo
/// sub-dictionaries for domain-specific metadata overflow.
///
/// Each external system is a schema instance with typed properties
/// (primaryId, revision, domain, label) and an optional freeform
/// metadata dictionary in assetInfo["sourceIds"][<instance_name>].
///
/// The convenience API bridges both mechanisms: typed getters/setters
/// for schema properties, plus dictionary getters/setters for the
/// assetInfo metadata.
///
class UsdSourceIdHybridAPI : public UsdAPISchemaBase
{
public:
    static const UsdSchemaKind schemaKind = UsdSchemaKind::MultipleApplyAPI;

    explicit UsdSourceIdHybridAPI(
        const UsdPrim &prim=UsdPrim(),
        const TfToken &name=TfToken())
        : UsdAPISchemaBase(prim, name)
    {
    }

    explicit UsdSourceIdHybridAPI(
        const UsdSchemaBase &schemaObj,
        const TfToken &name=TfToken())
        : UsdAPISchemaBase(schemaObj, name)
    {
    }

    USDSOURCEIDHYBRID_API
    virtual ~UsdSourceIdHybridAPI();

    USDSOURCEIDHYBRID_API
    static UsdSourceIdHybridAPI
    Get(const UsdStagePtr &stage, const SdfPath &path, const TfToken &name);

    USDSOURCEIDHYBRID_API
    static UsdSourceIdHybridAPI
    Get(const UsdPrim &prim, const TfToken &name);

    USDSOURCEIDHYBRID_API
    static bool
    CanApply(const UsdPrim &prim, const TfToken &name,
             std::string *whyNot = nullptr);

    USDSOURCEIDHYBRID_API
    static UsdSourceIdHybridAPI
    Apply(const UsdPrim &prim, const TfToken &name);

    USDSOURCEIDHYBRID_API
    static std::vector<TfToken>
    GetAll(const UsdPrim &prim);

    // --------------------------------------------------------------------- //
    // SCHEMA PROPERTY ACCESSORS (typed, validated, GUI-visible)
    // --------------------------------------------------------------------- //

    USDSOURCEIDHYBRID_API
    UsdAttribute GetPrimaryIdAttr() const;

    USDSOURCEIDHYBRID_API
    UsdAttribute CreatePrimaryIdAttr(
        const VtValue &defaultValue = VtValue(),
        bool writeSparsely = false) const;

    USDSOURCEIDHYBRID_API
    UsdAttribute GetRevisionAttr() const;

    USDSOURCEIDHYBRID_API
    UsdAttribute CreateRevisionAttr(
        const VtValue &defaultValue = VtValue(),
        bool writeSparsely = false) const;

    USDSOURCEIDHYBRID_API
    UsdAttribute GetDomainAttr() const;

    USDSOURCEIDHYBRID_API
    UsdAttribute CreateDomainAttr(
        const VtValue &defaultValue = VtValue(),
        bool writeSparsely = false) const;

    USDSOURCEIDHYBRID_API
    UsdAttribute GetLabelAttr() const;

    USDSOURCEIDHYBRID_API
    UsdAttribute CreateLabelAttr(
        const VtValue &defaultValue = VtValue(),
        bool writeSparsely = false) const;

    // --------------------------------------------------------------------- //
    // ASSETINFO METADATA ACCESSORS (freeform, element-wise composed)
    // --------------------------------------------------------------------- //

    /// Returns the domain-specific metadata dictionary from
    /// assetInfo["sourceIds"][<instance_name>].
    USDSOURCEIDHYBRID_API
    bool GetDomainMetadata(VtDictionary *metadata) const;

    /// Sets the domain-specific metadata dictionary in
    /// assetInfo["sourceIds"][<instance_name>].
    USDSOURCEIDHYBRID_API
    void SetDomainMetadata(const VtDictionary &metadata) const;

    /// Returns a single value from the domain metadata by key.
    USDSOURCEIDHYBRID_API
    VtValue GetDomainMetadataByKey(const TfToken &key) const;

    /// Sets a single value in the domain metadata by key.
    USDSOURCEIDHYBRID_API
    void SetDomainMetadataByKey(const TfToken &key,
                                 const VtValue &value) const;

    /// Clears the domain-specific metadata dictionary.
    USDSOURCEIDHYBRID_API
    void ClearDomainMetadata() const;

protected:
    USDSOURCEIDHYBRID_API
    UsdSchemaKind _GetSchemaKind() const override;

private:
    static const TfType &_GetStaticTfType();
    static bool _IsTypedSchema();
    TfToken _GetNamespacedPropertyName(const TfToken &suffix) const;
};

PXR_NAMESPACE_CLOSE_SCOPE

#endif // PXR_USD_USD_SOURCE_ID_HYBRID_SOURCE_IDENTIFIER_API_H
