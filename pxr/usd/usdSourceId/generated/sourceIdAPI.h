//
// Copyright 2016 Pixar
//
// Licensed under the terms set forth in the LICENSE.txt file available at
// https://openusd.org/license.
//
#ifndef USDSOURCEID_GENERATED_SOURCEIDAPI_H
#define USDSOURCEID_GENERATED_SOURCEIDAPI_H

/// \file usdSourceId/sourceIdAPI.h

#include "pxr/pxr.h"
#include "pxr/usd/usdSourceId/api.h"
#include "pxr/usd/usd/apiSchemaBase.h"
#include "pxr/usd/usd/prim.h"
#include "pxr/usd/usd/stage.h"
#include "pxr/usd/usdSourceId/tokens.h"

#include "pxr/base/vt/value.h"

#include "pxr/base/gf/vec3d.h"
#include "pxr/base/gf/vec3f.h"
#include "pxr/base/gf/matrix4d.h"

#include "pxr/base/tf/token.h"
#include "pxr/base/tf/type.h"

PXR_NAMESPACE_OPEN_SCOPE

class SdfAssetPath;

// -------------------------------------------------------------------------- //
// SOURCEIDAPI                                                                //
// -------------------------------------------------------------------------- //

/// \class UsdSourceIdSourceIdAPI
///
/// UsdSourceIdAPI provides a convenience interface for authoring and
/// querying external source identifiers stored as sub-dictionaries within
/// a prim's assetInfo metadata.
/// 
/// This schema implements Approach A from the 'Separation of Concerns for
/// Identifiers in USD' proposal: source identifiers are expressed as
/// stratified sub-dictionaries within assetInfo, with this applied API
/// schema providing typed convenience access.
/// 
/// The data layout in assetInfo follows this structure:
/// 
/// ```
/// assetInfo = {
/// dictionary sourceIds = {
/// dictionary <domain> = {
/// string primaryId = "..."
/// string revision  = "..."
/// dictionary metadata = { ... }
/// }
/// }
/// }
/// ```
/// 
/// Where <domain> is a vendor or standards-body identifier such as
/// "windchill", "ifc", "revit", "nvidia", etc.
/// 
/// Multiple domains can coexist on a single prim. The sourceIds
/// sub-dictionary is composed element-wise following standard assetInfo
/// composition semantics (strongest opinion wins per key).
/// 
/// This schema can be applied to any prim, not just model roots. While
/// assetInfo's convenience API on UsdModelAPI is scoped to model roots,
/// the underlying assetInfo metadata is registered in SdfSchema for all
/// prims and properties.
/// 
/// Example usage (Python):
/// ```python
/// api = UsdSourceId.SourceIdAPI.Apply(prim)
/// api.SetSourceId("windchill", "VR:wt.part.WTPart:23639563", revision="Rev.C")
/// api.SetSourceId("ifc", "2O2Fr$t4X7Zf8NOew3FNr2")
/// 
/// # Query
/// ids = api.GetAllSourceIds()  # {"windchill": {...}, "ifc": {...}}
/// primary = api.GetPrimaryId("windchill")  # "VR:wt.part.WTPart:23639563"
/// ```
/// 
///
class UsdSourceIdSourceIdAPI : public UsdAPISchemaBase
{
public:
    /// Compile time constant representing what kind of schema this class is.
    ///
    /// \sa UsdSchemaKind
    static const UsdSchemaKind schemaKind = UsdSchemaKind::SingleApplyAPI;

    /// Construct a UsdSourceIdSourceIdAPI on UsdPrim \p prim .
    /// Equivalent to UsdSourceIdSourceIdAPI::Get(prim.GetStage(), prim.GetPath())
    /// for a \em valid \p prim, but will not immediately throw an error for
    /// an invalid \p prim
    explicit UsdSourceIdSourceIdAPI(const UsdPrim& prim=UsdPrim())
        : UsdAPISchemaBase(prim)
    {
    }

    /// Construct a UsdSourceIdSourceIdAPI on the prim held by \p schemaObj .
    /// Should be preferred over UsdSourceIdSourceIdAPI(schemaObj.GetPrim()),
    /// as it preserves SchemaBase state.
    explicit UsdSourceIdSourceIdAPI(const UsdSchemaBase& schemaObj)
        : UsdAPISchemaBase(schemaObj)
    {
    }

    /// Destructor.
    USDSOURCEID_API
    virtual ~UsdSourceIdSourceIdAPI();

    /// Return a vector of names of all pre-declared attributes for this schema
    /// class and all its ancestor classes.  Does not include attributes that
    /// may be authored by custom/extended methods of the schemas involved.
    USDSOURCEID_API
    static const TfTokenVector &
    GetSchemaAttributeNames(bool includeInherited=true);

    /// Return a UsdSourceIdSourceIdAPI holding the prim adhering to this
    /// schema at \p path on \p stage.  If no prim exists at \p path on
    /// \p stage, or if the prim at that path does not adhere to this schema,
    /// return an invalid schema object.  This is shorthand for the following:
    ///
    /// \code
    /// UsdSourceIdSourceIdAPI(stage->GetPrimAtPath(path));
    /// \endcode
    ///
    USDSOURCEID_API
    static UsdSourceIdSourceIdAPI
    Get(const UsdStagePtr &stage, const SdfPath &path);


    /// Returns true if this <b>single-apply</b> API schema can be applied to 
    /// the given \p prim. If this schema can not be a applied to the prim, 
    /// this returns false and, if provided, populates \p whyNot with the 
    /// reason it can not be applied.
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
    USDSOURCEID_API
    static bool 
    CanApply(const UsdPrim &prim, std::string *whyNot=nullptr);

    /// Applies this <b>single-apply</b> API schema to the given \p prim.
    /// This information is stored by adding "SourceIdAPI" to the 
    /// token-valued, listOp metadata \em apiSchemas on the prim.
    /// 
    /// \return A valid UsdSourceIdSourceIdAPI object is returned upon success. 
    /// An invalid (or empty) UsdSourceIdSourceIdAPI object is returned upon 
    /// failure. See \ref UsdPrim::ApplyAPI() for conditions 
    /// resulting in failure. 
    /// 
    /// \sa UsdPrim::GetAppliedSchemas()
    /// \sa UsdPrim::HasAPI()
    /// \sa UsdPrim::CanApplyAPI()
    /// \sa UsdPrim::ApplyAPI()
    /// \sa UsdPrim::RemoveAPI()
    ///
    USDSOURCEID_API
    static UsdSourceIdSourceIdAPI 
    Apply(const UsdPrim &prim);

protected:
    /// Returns the kind of schema this class belongs to.
    ///
    /// \sa UsdSchemaKind
    USDSOURCEID_API
    UsdSchemaKind _GetSchemaKind() const override;

private:
    // needs to invoke _GetStaticTfType.
    friend class UsdSchemaRegistry;
    USDSOURCEID_API
    static const TfType &_GetStaticTfType();

    static bool _IsTypedSchema();

    // override SchemaBase virtuals.
    USDSOURCEID_API
    const TfType &_GetTfType() const override;

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
