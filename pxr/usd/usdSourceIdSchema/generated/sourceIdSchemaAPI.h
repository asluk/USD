//
// Copyright 2016 Pixar
//
// Licensed under the terms set forth in the LICENSE.txt file available at
// https://openusd.org/license.
//
#ifndef USDSOURCEIDSCHEMA_GENERATED_SOURCEIDSCHEMAAPI_H
#define USDSOURCEIDSCHEMA_GENERATED_SOURCEIDSCHEMAAPI_H

/// \file usdSourceIdSchema/sourceIdSchemaAPI.h

#include "pxr/pxr.h"
#include "pxr/usd/usdSourceIdSchema/api.h"
#include "pxr/usd/usd/apiSchemaBase.h"
#include "pxr/usd/usd/prim.h"
#include "pxr/usd/usd/stage.h"
#include "pxr/usd/usdSourceIdSchema/tokens.h"

#include "pxr/base/vt/value.h"

#include "pxr/base/gf/vec3d.h"
#include "pxr/base/gf/vec3f.h"
#include "pxr/base/gf/matrix4d.h"

#include "pxr/base/tf/token.h"
#include "pxr/base/tf/type.h"

PXR_NAMESPACE_OPEN_SCOPE

class SdfAssetPath;

// -------------------------------------------------------------------------- //
// SOURCEIDSCHEMAAPI                                                          //
// -------------------------------------------------------------------------- //

/// \class UsdSourceIdSchemaSourceIdSchemaAPI
///
/// UsdSourceIdSchemaAPI is a multi-apply API schema for expressing
/// external source identifiers as typed properties on a prim.
/// 
/// This schema implements Approach B from the 'Separation of Concerns for
/// Identifiers in USD' proposal: each external system's identifiers are
/// represented as a schema instance with typed properties.
/// 
/// Each instance is named after a domain (vendor or standards body), e.g.:
/// - sourceIdentifier:windchill
/// - sourceIdentifier:ifc
/// - sourceIdentifier:revit
/// - sourceIdentifier:nvidia
/// 
/// ## Properties per instance
/// 
/// - **primaryId** (string): The primary identifier in the external system.
/// This is the main linkage key. Could be a part number, GUID, asset ID,
/// or opaque system handle.
/// - **revision** (string): Version or revision designator in the external
/// system (e.g., "Rev.C", "v2.1", "OR:wt.part.WTPart:4697800").
/// - **domain** (token): Formal domain identifier, useful when instance
/// names are abbreviated (e.g., instance "wc" with domain "com.ptc.windchill").
/// - **label** (string): Human-readable label for this identifier
/// (e.g., "Windchill Part Number", "IFC GlobalId").
/// 
/// ## Example USD
/// 
/// ```usda
/// def Mesh "Column_C14" (
/// prepend apiSchemas = [
/// "SourceIdSchemaAPI:ifc",
/// "SourceIdSchemaAPI:revit",
/// "SourceIdSchemaAPI:uniclass"
/// ]
/// )
/// {
/// string sourceIdentifier:ifc:primaryId = "2O2Fr$t4X7Zf8NOew3FNr2"
/// token sourceIdentifier:ifc:domain = "org.buildingsmart.ifc"
/// string sourceIdentifier:ifc:label = "IFC GlobalId"
/// 
/// string sourceIdentifier:revit:primaryId = "847562"
/// string sourceIdentifier:revit:revision = "2026.1"
/// token sourceIdentifier:revit:domain = "com.autodesk.revit"
/// string sourceIdentifier:revit:label = "Revit ElementId"
/// 
/// string sourceIdentifier:uniclass:primaryId = "Ss_25_10_30"
/// token sourceIdentifier:uniclass:domain = "uk.thenbs.uniclass2015"
/// string sourceIdentifier:uniclass:label = "Uniclass 2015 Code"
/// }
/// ```
/// 
/// ## Key Characteristics
/// 
/// - Properties contribute to UsdPrimDefinition and are discoverable
/// through schema introspection.
/// - Fallback values enable GUI presentation of unauthored properties.
/// - Schema versioning and validation are built in.
/// - Each instance is independently authorable across layers.
/// - Multi-apply instances compose per-property (strongest opinion wins).
/// 
///
/// For any described attribute \em Fallback \em Value or \em Allowed \em Values below
/// that are text/tokens, the actual token is published and defined in \ref UsdSourceIdSchemaTokens.
/// So to set an attribute to the value "rightHanded", use UsdSourceIdSchemaTokens->rightHanded
/// as the value.
///
class UsdSourceIdSchemaSourceIdSchemaAPI : public UsdAPISchemaBase
{
public:
    /// Compile time constant representing what kind of schema this class is.
    ///
    /// \sa UsdSchemaKind
    static const UsdSchemaKind schemaKind = UsdSchemaKind::MultipleApplyAPI;

    /// Construct a UsdSourceIdSchemaSourceIdSchemaAPI on UsdPrim \p prim with
    /// name \p name . Equivalent to
    /// UsdSourceIdSchemaSourceIdSchemaAPI::Get(
    ///    prim.GetStage(),
    ///    prim.GetPath().AppendProperty(
    ///        "sourceIdentifier:name"));
    ///
    /// for a \em valid \p prim, but will not immediately throw an error for
    /// an invalid \p prim
    explicit UsdSourceIdSchemaSourceIdSchemaAPI(
        const UsdPrim& prim=UsdPrim(), const TfToken &name=TfToken())
        : UsdAPISchemaBase(prim, /*instanceName*/ name)
    { }

    /// Construct a UsdSourceIdSchemaSourceIdSchemaAPI on the prim held by \p schemaObj with
    /// name \p name.  Should be preferred over
    /// UsdSourceIdSchemaSourceIdSchemaAPI(schemaObj.GetPrim(), name), as it preserves
    /// SchemaBase state.
    explicit UsdSourceIdSchemaSourceIdSchemaAPI(
        const UsdSchemaBase& schemaObj, const TfToken &name)
        : UsdAPISchemaBase(schemaObj, /*instanceName*/ name)
    { }

    /// Destructor.
    USDSOURCEIDSCHEMA_API
    virtual ~UsdSourceIdSchemaSourceIdSchemaAPI();

    /// Return a vector of names of all pre-declared attributes for this schema
    /// class and all its ancestor classes.  Does not include attributes that
    /// may be authored by custom/extended methods of the schemas involved.
    USDSOURCEIDSCHEMA_API
    static const TfTokenVector &
    GetSchemaAttributeNames(bool includeInherited=true);

    /// Return a vector of names of all pre-declared attributes for this schema
    /// class and all its ancestor classes for a given instance name.  Does not
    /// include attributes that may be authored by custom/extended methods of
    /// the schemas involved. The names returned will have the proper namespace
    /// prefix.
    USDSOURCEIDSCHEMA_API
    static TfTokenVector
    GetSchemaAttributeNames(bool includeInherited, const TfToken &instanceName);

    /// Returns the name of this multiple-apply schema instance
    TfToken GetName() const {
        return _GetInstanceName();
    }

    /// Return a UsdSourceIdSchemaSourceIdSchemaAPI holding the prim adhering to this
    /// schema at \p path on \p stage.  If no prim exists at \p path on
    /// \p stage, or if the prim at that path does not adhere to this schema,
    /// return an invalid schema object.  \p path must be of the format
    /// <path>.sourceIdentifier:name .
    ///
    /// This is shorthand for the following:
    ///
    /// \code
    /// TfToken name = SdfPath::StripNamespace(path.GetToken());
    /// UsdSourceIdSchemaSourceIdSchemaAPI(
    ///     stage->GetPrimAtPath(path.GetPrimPath()), name);
    /// \endcode
    ///
    USDSOURCEIDSCHEMA_API
    static UsdSourceIdSchemaSourceIdSchemaAPI
    Get(const UsdStagePtr &stage, const SdfPath &path);

    /// Return a UsdSourceIdSchemaSourceIdSchemaAPI with name \p name holding the
    /// prim \p prim. Shorthand for UsdSourceIdSchemaSourceIdSchemaAPI(prim, name);
    USDSOURCEIDSCHEMA_API
    static UsdSourceIdSchemaSourceIdSchemaAPI
    Get(const UsdPrim &prim, const TfToken &name);

    /// Return a vector of all named instances of UsdSourceIdSchemaSourceIdSchemaAPI on the 
    /// given \p prim.
    USDSOURCEIDSCHEMA_API
    static std::vector<UsdSourceIdSchemaSourceIdSchemaAPI>
    GetAll(const UsdPrim &prim);

    /// Checks if the given name \p baseName is the base name of a property
    /// of SourceIdSchemaAPI.
    USDSOURCEIDSCHEMA_API
    static bool
    IsSchemaPropertyBaseName(const TfToken &baseName);

    /// Checks if the given path \p path is of an API schema of type
    /// SourceIdSchemaAPI. If so, it stores the instance name of
    /// the schema in \p name and returns true. Otherwise, it returns false.
    USDSOURCEIDSCHEMA_API
    static bool
    IsSourceIdSchemaAPIPath(const SdfPath &path, TfToken *name);

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
    USDSOURCEIDSCHEMA_API
    static bool 
    CanApply(const UsdPrim &prim, const TfToken &name, 
             std::string *whyNot=nullptr);

    /// Applies this <b>multiple-apply</b> API schema to the given \p prim 
    /// along with the given instance name, \p name. 
    /// 
    /// This information is stored by adding "SourceIdSchemaAPI:<i>name</i>" 
    /// to the token-valued, listOp metadata \em apiSchemas on the prim.
    /// For example, if \p name is 'instance1', the token 
    /// 'SourceIdSchemaAPI:instance1' is added to 'apiSchemas'.
    /// 
    /// \return A valid UsdSourceIdSchemaSourceIdSchemaAPI object is returned upon success. 
    /// An invalid (or empty) UsdSourceIdSchemaSourceIdSchemaAPI object is returned upon 
    /// failure. See \ref UsdPrim::ApplyAPI() for 
    /// conditions resulting in failure. 
    /// 
    /// \sa UsdPrim::GetAppliedSchemas()
    /// \sa UsdPrim::HasAPI()
    /// \sa UsdPrim::CanApplyAPI()
    /// \sa UsdPrim::ApplyAPI()
    /// \sa UsdPrim::RemoveAPI()
    ///
    USDSOURCEIDSCHEMA_API
    static UsdSourceIdSchemaSourceIdSchemaAPI 
    Apply(const UsdPrim &prim, const TfToken &name);

protected:
    /// Returns the kind of schema this class belongs to.
    ///
    /// \sa UsdSchemaKind
    USDSOURCEIDSCHEMA_API
    UsdSchemaKind _GetSchemaKind() const override;

private:
    // needs to invoke _GetStaticTfType.
    friend class UsdSchemaRegistry;
    USDSOURCEIDSCHEMA_API
    static const TfType &_GetStaticTfType();

    static bool _IsTypedSchema();

    // override SchemaBase virtuals.
    USDSOURCEIDSCHEMA_API
    const TfType &_GetTfType() const override;

public:
    // --------------------------------------------------------------------- //
    // PRIMARYID 
    // --------------------------------------------------------------------- //
    /// The primary identifier for this entity in the external system.
    /// This is the main linkage key used for cross-system resolution.
    /// Examples: "VR:wt.part.WTPart:23639563", "2O2Fr$t4X7Zf8NOew3FNr2",
    /// "847562", "A-0000-12345".
    /// 
    ///
    /// | ||
    /// | -- | -- |
    /// | Declaration | `string primaryId = ""` |
    /// | C++ Type | std::string |
    /// | \ref Usd_Datatypes "Usd Type" | SdfValueTypeNames->String |
    USDSOURCEIDSCHEMA_API
    UsdAttribute GetPrimaryIdAttr() const;

    /// See GetPrimaryIdAttr(), and also 
    /// \ref Usd_Create_Or_Get_Property for when to use Get vs Create.
    /// If specified, author \p defaultValue as the attribute's default,
    /// sparsely (when it makes sense to do so) if \p writeSparsely is \c true -
    /// the default for \p writeSparsely is \c false.
    USDSOURCEIDSCHEMA_API
    UsdAttribute CreatePrimaryIdAttr(VtValue const &defaultValue = VtValue(), bool writeSparsely=false) const;

public:
    // --------------------------------------------------------------------- //
    // REVISION 
    // --------------------------------------------------------------------- //
    /// Version or revision designator in the external system.
    /// Examples: "Rev.C", "v2.1", "OR:wt.part.WTPart:4697800".
    /// This is the version/revision of the source entity, not the USD layer.
    /// 
    ///
    /// | ||
    /// | -- | -- |
    /// | Declaration | `string revision = ""` |
    /// | C++ Type | std::string |
    /// | \ref Usd_Datatypes "Usd Type" | SdfValueTypeNames->String |
    USDSOURCEIDSCHEMA_API
    UsdAttribute GetRevisionAttr() const;

    /// See GetRevisionAttr(), and also 
    /// \ref Usd_Create_Or_Get_Property for when to use Get vs Create.
    /// If specified, author \p defaultValue as the attribute's default,
    /// sparsely (when it makes sense to do so) if \p writeSparsely is \c true -
    /// the default for \p writeSparsely is \c false.
    USDSOURCEIDSCHEMA_API
    UsdAttribute CreateRevisionAttr(VtValue const &defaultValue = VtValue(), bool writeSparsely=false) const;

public:
    // --------------------------------------------------------------------- //
    // DOMAIN 
    // --------------------------------------------------------------------- //
    /// Formal domain identifier using reverse-DNS or equivalent
    /// convention. This provides an unambiguous, collision-resistant
    /// identifier for the external system, separate from the instance name
    /// which may be an abbreviation.
    /// Examples: "com.ptc.windchill", "org.buildingsmart.ifc",
    /// "com.autodesk.revit", "com.nvidia.omniverse".
    /// 
    ///
    /// | ||
    /// | -- | -- |
    /// | Declaration | `token domain = ""` |
    /// | C++ Type | TfToken |
    /// | \ref Usd_Datatypes "Usd Type" | SdfValueTypeNames->Token |
    USDSOURCEIDSCHEMA_API
    UsdAttribute GetDomainAttr() const;

    /// See GetDomainAttr(), and also 
    /// \ref Usd_Create_Or_Get_Property for when to use Get vs Create.
    /// If specified, author \p defaultValue as the attribute's default,
    /// sparsely (when it makes sense to do so) if \p writeSparsely is \c true -
    /// the default for \p writeSparsely is \c false.
    USDSOURCEIDSCHEMA_API
    UsdAttribute CreateDomainAttr(VtValue const &defaultValue = VtValue(), bool writeSparsely=false) const;

public:
    // --------------------------------------------------------------------- //
    // LABEL 
    // --------------------------------------------------------------------- //
    /// Human-readable label describing what this identifier
    /// represents in the external system.
    /// Examples: "Windchill Part Number", "IFC GlobalId",
    /// "Revit ElementId", "Uniclass 2015 Classification Code".
    /// 
    ///
    /// | ||
    /// | -- | -- |
    /// | Declaration | `string label = ""` |
    /// | C++ Type | std::string |
    /// | \ref Usd_Datatypes "Usd Type" | SdfValueTypeNames->String |
    USDSOURCEIDSCHEMA_API
    UsdAttribute GetLabelAttr() const;

    /// See GetLabelAttr(), and also 
    /// \ref Usd_Create_Or_Get_Property for when to use Get vs Create.
    /// If specified, author \p defaultValue as the attribute's default,
    /// sparsely (when it makes sense to do so) if \p writeSparsely is \c true -
    /// the default for \p writeSparsely is \c false.
    USDSOURCEIDSCHEMA_API
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
