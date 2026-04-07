//
// Copyright 2016 Pixar
//
// Licensed under the terms set forth in the LICENSE.txt file available at
// https://openusd.org/license.
//
#ifndef USDSOURCEIDHYBRID_GENERATED_SOURCEIDHYBRIDAPI_H
#define USDSOURCEIDHYBRID_GENERATED_SOURCEIDHYBRIDAPI_H

/// \file usdSourceIdHybrid/sourceIdHybridAPI.h

#include "pxr/pxr.h"
#include "pxr/usd/usdSourceIdHybrid/api.h"
#include "pxr/usd/usd/apiSchemaBase.h"
#include "pxr/usd/usd/prim.h"
#include "pxr/usd/usd/stage.h"
#include "pxr/usd/usdSourceIdHybrid/tokens.h"

#include "pxr/base/vt/value.h"

#include "pxr/base/gf/vec3d.h"
#include "pxr/base/gf/vec3f.h"
#include "pxr/base/gf/matrix4d.h"

#include "pxr/base/tf/token.h"
#include "pxr/base/tf/type.h"

PXR_NAMESPACE_OPEN_SCOPE

class SdfAssetPath;

// -------------------------------------------------------------------------- //
// SOURCEIDHYBRIDAPI                                                          //
// -------------------------------------------------------------------------- //

/// \class UsdSourceIdHybridSourceIdHybridAPI
///
/// UsdSourceIdHybridAPI is a multi-apply API schema for expressing
/// external source identifiers as typed properties on a prim, with
/// domain-specific metadata stored in assetInfo sub-dictionaries.
/// 
/// This schema implements the hybrid approach (Approach C) from the
/// 'Separation of Concerns for Identifiers' comparison: each external
/// system gets a schema instance with typed common properties, plus
/// an assetInfo["sourceIds"][<instance_name>] dictionary for freeform
/// domain-specific metadata.
/// 
/// ## Schema properties (typed, validated, GUI-visible)
/// 
/// - **primaryId** (string): Main linkage key in the external system.
/// - **revision** (string): Version/revision designator.
/// - **domain** (token): Formal reverse-DNS domain identifier.
/// - **label** (string): Human-readable description.
/// 
/// ## Domain-specific metadata (freeform, in assetInfo)
/// 
/// Additional domain-specific fields are stored in
/// assetInfo["sourceIds"][<instance_name>] as a freeform dictionary.
/// The instance name links the schema properties to the metadata dict.
/// 
/// This follows the UsdMediaAssetPreviewsAPI precedent: the schema
/// provides a described spec and convenience API, while structured
/// data lives in composed assetInfo metadata.
/// 
/// ## Example USD
/// 
/// ```usda
/// def Xform "Chiller_01" (
/// prepend apiSchemas = [
/// "SourceIdHybridAPI:windchill",
/// "SourceIdHybridAPI:opcua"
/// ]
/// assetInfo = {
/// dictionary sourceIds = {
/// dictionary windchill = {
/// string displayNumber = "CH-7500-A"
/// string navigationType = "OR:wt.filter.NavigationCriteria:7608531"
/// string state = "Released"
/// }
/// dictionary opcua = {
/// string nodeClass = "Object"
/// string serverUri = "opc.tcp://bms.example.com:4840"
/// }
/// }
/// }
/// )
/// {
/// string sourceIdentifier:windchill:primaryId = "VR:wt.part.WTPart:23639563"
/// string sourceIdentifier:windchill:revision = "Rev.C"
/// token sourceIdentifier:windchill:domain = "com.ptc.windchill"
/// string sourceIdentifier:windchill:label = "Windchill Part OID"
/// 
/// string sourceIdentifier:opcua:primaryId = "ns=4;s=Building.HVAC.Chiller01"
/// token sourceIdentifier:opcua:domain = "org.opcfoundation.ua"
/// string sourceIdentifier:opcua:label = "OPC UA NodeId"
/// }
/// ```
/// 
/// ## Key Characteristics
/// 
/// - Common fields are schema-backed: typed, validated, GUI-visible,
/// per-property composition.
/// - Domain-specific metadata is freeform: no schema changes needed,
/// element-wise composition via assetInfo.
/// - apiSchemas list declares which domains are present (discoverability).
/// - Instance name links schema properties to assetInfo sub-dictionary.
/// 
///
/// For any described attribute \em Fallback \em Value or \em Allowed \em Values below
/// that are text/tokens, the actual token is published and defined in \ref UsdSourceIdHybridTokens.
/// So to set an attribute to the value "rightHanded", use UsdSourceIdHybridTokens->rightHanded
/// as the value.
///
class UsdSourceIdHybridSourceIdHybridAPI : public UsdAPISchemaBase
{
public:
    /// Compile time constant representing what kind of schema this class is.
    ///
    /// \sa UsdSchemaKind
    static const UsdSchemaKind schemaKind = UsdSchemaKind::MultipleApplyAPI;

    /// Construct a UsdSourceIdHybridSourceIdHybridAPI on UsdPrim \p prim with
    /// name \p name . Equivalent to
    /// UsdSourceIdHybridSourceIdHybridAPI::Get(
    ///    prim.GetStage(),
    ///    prim.GetPath().AppendProperty(
    ///        "sourceIdentifier:name"));
    ///
    /// for a \em valid \p prim, but will not immediately throw an error for
    /// an invalid \p prim
    explicit UsdSourceIdHybridSourceIdHybridAPI(
        const UsdPrim& prim=UsdPrim(), const TfToken &name=TfToken())
        : UsdAPISchemaBase(prim, /*instanceName*/ name)
    { }

    /// Construct a UsdSourceIdHybridSourceIdHybridAPI on the prim held by \p schemaObj with
    /// name \p name.  Should be preferred over
    /// UsdSourceIdHybridSourceIdHybridAPI(schemaObj.GetPrim(), name), as it preserves
    /// SchemaBase state.
    explicit UsdSourceIdHybridSourceIdHybridAPI(
        const UsdSchemaBase& schemaObj, const TfToken &name)
        : UsdAPISchemaBase(schemaObj, /*instanceName*/ name)
    { }

    /// Destructor.
    USDSOURCEIDHYBRID_API
    virtual ~UsdSourceIdHybridSourceIdHybridAPI();

    /// Return a vector of names of all pre-declared attributes for this schema
    /// class and all its ancestor classes.  Does not include attributes that
    /// may be authored by custom/extended methods of the schemas involved.
    USDSOURCEIDHYBRID_API
    static const TfTokenVector &
    GetSchemaAttributeNames(bool includeInherited=true);

    /// Return a vector of names of all pre-declared attributes for this schema
    /// class and all its ancestor classes for a given instance name.  Does not
    /// include attributes that may be authored by custom/extended methods of
    /// the schemas involved. The names returned will have the proper namespace
    /// prefix.
    USDSOURCEIDHYBRID_API
    static TfTokenVector
    GetSchemaAttributeNames(bool includeInherited, const TfToken &instanceName);

    /// Returns the name of this multiple-apply schema instance
    TfToken GetName() const {
        return _GetInstanceName();
    }

    /// Return a UsdSourceIdHybridSourceIdHybridAPI holding the prim adhering to this
    /// schema at \p path on \p stage.  If no prim exists at \p path on
    /// \p stage, or if the prim at that path does not adhere to this schema,
    /// return an invalid schema object.  \p path must be of the format
    /// <path>.sourceIdentifier:name .
    ///
    /// This is shorthand for the following:
    ///
    /// \code
    /// TfToken name = SdfPath::StripNamespace(path.GetToken());
    /// UsdSourceIdHybridSourceIdHybridAPI(
    ///     stage->GetPrimAtPath(path.GetPrimPath()), name);
    /// \endcode
    ///
    USDSOURCEIDHYBRID_API
    static UsdSourceIdHybridSourceIdHybridAPI
    Get(const UsdStagePtr &stage, const SdfPath &path);

    /// Return a UsdSourceIdHybridSourceIdHybridAPI with name \p name holding the
    /// prim \p prim. Shorthand for UsdSourceIdHybridSourceIdHybridAPI(prim, name);
    USDSOURCEIDHYBRID_API
    static UsdSourceIdHybridSourceIdHybridAPI
    Get(const UsdPrim &prim, const TfToken &name);

    /// Return a vector of all named instances of UsdSourceIdHybridSourceIdHybridAPI on the 
    /// given \p prim.
    USDSOURCEIDHYBRID_API
    static std::vector<UsdSourceIdHybridSourceIdHybridAPI>
    GetAll(const UsdPrim &prim);

    /// Checks if the given name \p baseName is the base name of a property
    /// of SourceIdHybridAPI.
    USDSOURCEIDHYBRID_API
    static bool
    IsSchemaPropertyBaseName(const TfToken &baseName);

    /// Checks if the given path \p path is of an API schema of type
    /// SourceIdHybridAPI. If so, it stores the instance name of
    /// the schema in \p name and returns true. Otherwise, it returns false.
    USDSOURCEIDHYBRID_API
    static bool
    IsSourceIdHybridAPIPath(const SdfPath &path, TfToken *name);

    /// Returns true if this <b>multiple-apply</b> API schema can be applied,
    /// with the given instance name, \p name, to the given \p prim. If this 
    /// schema can not be a applied the prim, this returns false and, if 
    /// provided, populates \p whyNot with the reason it can not be applied.
    /// 
    /// Note that if CanApply returns false, that does not necessarily imply
    /// that calling Apply will fail. Callers are expected to call CanApply
    /// before calling Apply if they want to ensure that it is valid to 
    /// apply a schema.
    /// 
    /// \sa UsdPrim::GetAppliedSchemas()
    /// \sa UsdPrim::HasAPI()
    /// \sa UsdPrim::CanApplyAPI()
    /// \sa UsdPrim::ApplyAPI()
    /// \sa UsdPrim::RemoveAPI()
    ///
    USDSOURCEIDHYBRID_API
    static bool 
    CanApply(const UsdPrim &prim, const TfToken &name, 
             std::string *whyNot=nullptr);

    /// Applies this <b>multiple-apply</b> API schema to the given \p prim 
    /// along with the given instance name, \p name. 
    /// 
    /// This information is stored by adding "SourceIdHybridAPI:<i>name</i>" 
    /// to the token-valued, listOp metadata \em apiSchemas on the prim.
    /// For example, if \p name is 'instance1', the token 
    /// 'SourceIdHybridAPI:instance1' is added to 'apiSchemas'.
    /// 
    /// \return A valid UsdSourceIdHybridSourceIdHybridAPI object is returned upon success. 
    /// An invalid (or empty) UsdSourceIdHybridSourceIdHybridAPI object is returned upon 
    /// failure. See \ref UsdPrim::ApplyAPI() for 
    /// conditions resulting in failure. 
    /// 
    /// \sa UsdPrim::GetAppliedSchemas()
    /// \sa UsdPrim::HasAPI()
    /// \sa UsdPrim::CanApplyAPI()
    /// \sa UsdPrim::ApplyAPI()
    /// \sa UsdPrim::RemoveAPI()
    ///
    USDSOURCEIDHYBRID_API
    static UsdSourceIdHybridSourceIdHybridAPI 
    Apply(const UsdPrim &prim, const TfToken &name);

protected:
    /// Returns the kind of schema this class belongs to.
    ///
    /// \sa UsdSchemaKind
    USDSOURCEIDHYBRID_API
    UsdSchemaKind _GetSchemaKind() const override;

private:
    // needs to invoke _GetStaticTfType.
    friend class UsdSchemaRegistry;
    USDSOURCEIDHYBRID_API
    static const TfType &_GetStaticTfType();

    static bool _IsTypedSchema();

    // override SchemaBase virtuals.
    USDSOURCEIDHYBRID_API
    const TfType &_GetTfType() const override;

public:
    // --------------------------------------------------------------------- //
    // PRIMARYID 
    // --------------------------------------------------------------------- //
    /// The primary identifier for this entity in the external system.
    ///
    /// | ||
    /// | -- | -- |
    /// | Declaration | `string primaryId = ""` |
    /// | C++ Type | std::string |
    /// | \ref Usd_Datatypes "Usd Type" | SdfValueTypeNames->String |
    USDSOURCEIDHYBRID_API
    UsdAttribute GetPrimaryIdAttr() const;

    /// See GetPrimaryIdAttr(), and also 
    /// \ref Usd_Create_Or_Get_Property for when to use Get vs Create.
    /// If specified, author \p defaultValue as the attribute's default,
    /// sparsely (when it makes sense to do so) if \p writeSparsely is \c true -
    /// the default for \p writeSparsely is \c false.
    USDSOURCEIDHYBRID_API
    UsdAttribute CreatePrimaryIdAttr(VtValue const &defaultValue = VtValue(), bool writeSparsely=false) const;

public:
    // --------------------------------------------------------------------- //
    // REVISION 
    // --------------------------------------------------------------------- //
    /// Version or revision designator in the external system.
    ///
    /// | ||
    /// | -- | -- |
    /// | Declaration | `string revision = ""` |
    /// | C++ Type | std::string |
    /// | \ref Usd_Datatypes "Usd Type" | SdfValueTypeNames->String |
    USDSOURCEIDHYBRID_API
    UsdAttribute GetRevisionAttr() const;

    /// See GetRevisionAttr(), and also 
    /// \ref Usd_Create_Or_Get_Property for when to use Get vs Create.
    /// If specified, author \p defaultValue as the attribute's default,
    /// sparsely (when it makes sense to do so) if \p writeSparsely is \c true -
    /// the default for \p writeSparsely is \c false.
    USDSOURCEIDHYBRID_API
    UsdAttribute CreateRevisionAttr(VtValue const &defaultValue = VtValue(), bool writeSparsely=false) const;

public:
    // --------------------------------------------------------------------- //
    // DOMAIN 
    // --------------------------------------------------------------------- //
    /// Formal domain identifier using reverse-DNS convention.
    ///
    /// | ||
    /// | -- | -- |
    /// | Declaration | `token domain = ""` |
    /// | C++ Type | TfToken |
    /// | \ref Usd_Datatypes "Usd Type" | SdfValueTypeNames->Token |
    USDSOURCEIDHYBRID_API
    UsdAttribute GetDomainAttr() const;

    /// See GetDomainAttr(), and also 
    /// \ref Usd_Create_Or_Get_Property for when to use Get vs Create.
    /// If specified, author \p defaultValue as the attribute's default,
    /// sparsely (when it makes sense to do so) if \p writeSparsely is \c true -
    /// the default for \p writeSparsely is \c false.
    USDSOURCEIDHYBRID_API
    UsdAttribute CreateDomainAttr(VtValue const &defaultValue = VtValue(), bool writeSparsely=false) const;

public:
    // --------------------------------------------------------------------- //
    // LABEL 
    // --------------------------------------------------------------------- //
    /// Human-readable label for this identifier.
    ///
    /// | ||
    /// | -- | -- |
    /// | Declaration | `string label = ""` |
    /// | C++ Type | std::string |
    /// | \ref Usd_Datatypes "Usd Type" | SdfValueTypeNames->String |
    USDSOURCEIDHYBRID_API
    UsdAttribute GetLabelAttr() const;

    /// See GetLabelAttr(), and also 
    /// \ref Usd_Create_Or_Get_Property for when to use Get vs Create.
    /// If specified, author \p defaultValue as the attribute's default,
    /// sparsely (when it makes sense to do so) if \p writeSparsely is \c true -
    /// the default for \p writeSparsely is \c false.
    USDSOURCEIDHYBRID_API
    UsdAttribute CreateLabelAttr(VtValue const &defaultValue = VtValue(), bool writeSparsely=false) const;

public:
    // ===================================================================== //
    // Feel free to add custom code below this line, it will be preserved by 
    // the code generator. 
    //
    // Just remember to: 
    //  - Close the class declaration with }; 
    //  - Close the namespace with PXR_NAMESPACE_CLOSE_SCOPE
    //  - Close the include guard with #endif
    // ===================================================================== //
    // --(BEGIN CUSTOM CODE)--
};

PXR_NAMESPACE_CLOSE_SCOPE

#endif
