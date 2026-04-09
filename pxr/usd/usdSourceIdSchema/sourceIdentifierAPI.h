//
// Copyright 2026 NVIDIA Corporation
//
// Licensed under the terms set forth in the LICENSE.txt file available at
// https://openusd.org/license.
//
#ifndef PXR_USD_USD_SOURCE_ID_SCHEMA_SOURCE_IDENTIFIER_API_H
#define PXR_USD_USD_SOURCE_ID_SCHEMA_SOURCE_IDENTIFIER_API_H

/// \file usdSourceIdSchema/sourceIdentifierAPI.h

#include "pxr/pxr.h"
#include "pxr/usd/usdSourceIdSchema/api.h"
#include "pxr/usd/usd/apiSchemaBase.h"
#include "pxr/usd/usd/prim.h"
#include "pxr/usd/usd/stage.h"

#include "pxr/base/vt/value.h"
#include "pxr/base/tf/token.h"
#include "pxr/base/tf/type.h"

#include <string>
#include <vector>

PXR_NAMESPACE_OPEN_SCOPE

/// \class UsdSourceIdSchemaAPI
///
/// Approach B: Multi-apply API schema for source identifiers with typed
/// properties.
///
/// Each external system is represented as a schema instance:
/// - `SourceIdSchemaAPI:windchill`
/// - `SourceIdSchemaAPI:ifc`
/// - `SourceIdSchemaAPI:revit`
///
/// Each instance provides typed properties:
/// - `primaryId` (string): Main identifier in the external system
/// - `revision` (string): Version/revision designator
/// - `domain` (token): Formal reverse-DNS domain identifier
/// - `label` (string): Human-readable description
///
/// ## Data Layout (USD)
///
/// ```usda
/// def Mesh "Column" (
///     prepend apiSchemas = ["SourceIdSchemaAPI:ifc",
///                           "SourceIdSchemaAPI:windchill"]
/// )
/// {
///     string sourceIdentifier:ifc:primaryId = "2O2Fr$t4X7Zf8NOew3FNr2"
///     token sourceIdentifier:ifc:domain = "org.buildingsmart.ifc"
///
///     string sourceIdentifier:windchill:primaryId = "VR:wt.part.WTPart:23639563"
///     string sourceIdentifier:windchill:revision = "Rev.C"
///     token sourceIdentifier:windchill:domain = "com.ptc.windchill"
/// }
/// ```
///
/// ## Composition Behavior
///
/// Properties compose per standard USD rules: strongest opinion wins per
/// property. Each instance's properties are independent, so a stronger
/// layer can override one system's identifier without affecting another's.
///
/// ## Usage
///
/// ```cpp
/// // Apply for a specific domain
/// auto api = UsdSourceIdSchemaAPI::Apply(prim, TfToken("windchill"));
///
/// // Set properties
/// api.GetPrimaryIdAttr().Set(std::string("VR:wt.part.WTPart:23639563"));
/// api.GetRevisionAttr().Set(std::string("Rev.C"));
/// api.GetDomainAttr().Set(TfToken("com.ptc.windchill"));
///
/// // Query
/// std::string id;
/// api.GetPrimaryIdAttr().Get(&id);
///
/// // Get all applied instances
/// auto instances = UsdSourceIdSchemaAPI::GetSchemaAttributeNames(false);
/// ```
///
class UsdSourceIdSchemaAPI : public UsdAPISchemaBase
{
public:
    /// Compile time constant representing what kind of schema this class is.
    static const UsdSchemaKind schemaKind = UsdSchemaKind::MultipleApplyAPI;

    /// Construct a UsdSourceIdSchemaAPI on UsdPrim \p prim with
    /// instance name \p name.
    explicit UsdSourceIdSchemaAPI(
        const UsdPrim &prim=UsdPrim(),
        const TfToken &name=TfToken())
        : UsdAPISchemaBase(prim, name)
    {
    }

    /// Construct a UsdSourceIdSchemaAPI on the prim held by
    /// \p schemaObj with instance name \p name.
    explicit UsdSourceIdSchemaAPI(
        const UsdSchemaBase &schemaObj,
        const TfToken &name=TfToken())
        : UsdAPISchemaBase(schemaObj, name)
    {
    }

    /// Returns the name of this multiple-apply schema instance.
    TfToken GetName() const {
        return _GetInstanceName();
    }

    /// Destructor.
    USDSOURCEIDSCHEMA_API
    virtual ~UsdSourceIdSchemaAPI();

    /// Return a UsdSourceIdSchemaAPI with instance name \p name
    /// holding the prim at \p path on \p stage.
    USDSOURCEIDSCHEMA_API
    static UsdSourceIdSchemaAPI
    Get(const UsdStagePtr &stage, const SdfPath &path,
        const TfToken &name);

    /// Return a UsdSourceIdSchemaAPI with instance name \p name
    /// attached to the given prim.
    USDSOURCEIDSCHEMA_API
    static UsdSourceIdSchemaAPI
    Get(const UsdPrim &prim, const TfToken &name);

    /// Returns true if this schema can be applied with \p name to \p prim.
    USDSOURCEIDSCHEMA_API
    static bool
    CanApply(const UsdPrim &prim, const TfToken &name,
             std::string *whyNot = nullptr);

    /// Applies this multi-apply API schema with instance \p name.
    USDSOURCEIDSCHEMA_API
    static UsdSourceIdSchemaAPI
    Apply(const UsdPrim &prim, const TfToken &name);

    /// Returns all instance names of applied SourceIdSchemaAPI schemas
    /// on \p prim.
    USDSOURCEIDSCHEMA_API
    static std::vector<TfToken>
    GetAll(const UsdPrim &prim);

    // --------------------------------------------------------------------- //
    // PROPERTY ACCESSORS
    // --------------------------------------------------------------------- //

    /// \name Typed Property Access
    /// @{

    /// Return the primaryId attribute for this instance.
    USDSOURCEIDSCHEMA_API
    UsdAttribute GetPrimaryIdAttr() const;

    /// Create the primaryId attribute for this instance.
    USDSOURCEIDSCHEMA_API
    UsdAttribute CreatePrimaryIdAttr(
        const VtValue &defaultValue = VtValue(),
        bool writeSparsely = false) const;

    /// Return the revision attribute for this instance.
    USDSOURCEIDSCHEMA_API
    UsdAttribute GetRevisionAttr() const;

    /// Create the revision attribute for this instance.
    USDSOURCEIDSCHEMA_API
    UsdAttribute CreateRevisionAttr(
        const VtValue &defaultValue = VtValue(),
        bool writeSparsely = false) const;

    /// Return the domain attribute for this instance.
    USDSOURCEIDSCHEMA_API
    UsdAttribute GetDomainAttr() const;

    /// Create the domain attribute for this instance.
    USDSOURCEIDSCHEMA_API
    UsdAttribute CreateDomainAttr(
        const VtValue &defaultValue = VtValue(),
        bool writeSparsely = false) const;

    /// Return the label attribute for this instance.
    USDSOURCEIDSCHEMA_API
    UsdAttribute GetLabelAttr() const;

    /// Create the label attribute for this instance.
    USDSOURCEIDSCHEMA_API
    UsdAttribute CreateLabelAttr(
        const VtValue &defaultValue = VtValue(),
        bool writeSparsely = false) const;

    /// @}

    /// Return a vector of names of all pre-declared attributes for this
    /// schema class and all its ancestor classes for the given instance name.
    USDSOURCEIDSCHEMA_API
    static const TfTokenVector &
    GetSchemaAttributeNames(
        bool includeInherited = true,
        const TfToken &instanceName = TfToken());

protected:
    USDSOURCEIDSCHEMA_API
    UsdSchemaKind _GetSchemaKind() const override;

private:
    // needs to invoke _GetStaticTfType.
    friend class UsdSchemaRegistry;

    static const TfType &_GetStaticTfType();
    static bool _IsTypedSchema();

    // Returns the property name for a given instance and property suffix.
    TfToken _GetNamespacedPropertyName(const TfToken &suffix) const;
};

PXR_NAMESPACE_CLOSE_SCOPE

#endif // PXR_USD_USD_SOURCE_ID_SCHEMA_SOURCE_IDENTIFIER_API_H
