//
// Copyright 2026 NVIDIA Corporation
//
// Licensed under the terms set forth in the LICENSE.txt file available at
// https://openusd.org/license.
//
#ifndef PXR_USD_USD_SOURCE_ID_SOURCE_ID_API_H
#define PXR_USD_USD_SOURCE_ID_SOURCE_ID_API_H

/// \file usdSourceId/sourceIdAPI.h

#include "pxr/pxr.h"
#include "pxr/usd/usdSourceId/api.h"
#include "pxr/usd/usd/apiSchemaBase.h"
#include "pxr/usd/usd/prim.h"
#include "pxr/usd/usd/stage.h"

#include "pxr/base/vt/dictionary.h"
#include "pxr/base/vt/value.h"
#include "pxr/base/tf/token.h"
#include "pxr/base/tf/type.h"

#include <string>
#include <vector>

PXR_NAMESPACE_OPEN_SCOPE

/// \class UsdSourceIdAPI
///
/// Approach A: Convenience API for source identifiers stored as
/// sub-dictionaries within assetInfo["sourceIds"].
///
/// This is a **non-applied** API schema, following the precedent set by
/// UsdModelAPI: it wraps assetInfo metadata without requiring explicit
/// application. Any prim that carries assetInfo["sourceIds"] data can
/// be queried through this API. There is no Apply() method and no
/// apiSchemas listing — the data's presence in assetInfo IS the signal.
///
/// The schema itself defines no properties; all data lives in the
/// composed assetInfo dictionary.
///
/// ## Data Layout
///
/// ```
/// assetInfo = {
///     dictionary sourceIds = {
///         dictionary windchill = {
///             string primaryId = "VR:wt.part.WTPart:23639563"
///             string revision = "Rev.C"
///             dictionary metadata = {
///                 string displayNumber = "A-0000-12345"
///                 string navigationType = "OR:wt.filter.NavigationCriteria:7608531"
///             }
///         }
///         dictionary ifc = {
///             string primaryId = "2O2Fr$t4X7Zf8NOew3FNr2"
///         }
///     }
/// }
/// ```
///
/// ## Composition Behavior
///
/// Source identifiers inherit the composition semantics of assetInfo:
/// element-wise composition with strongest opinion winning per key.
/// This means that a stronger layer can override a single domain's
/// identifiers without affecting other domains.
///
/// ## Usage
///
/// ```cpp
/// // Non-applied: construct directly, no Apply() needed
/// UsdSourceIdAPI api(prim);
///
/// // Set identifiers
/// api.SetSourceId("windchill", "VR:wt.part.WTPart:23639563", "Rev.C");
/// api.SetSourceId("ifc", "2O2Fr$t4X7Zf8NOew3FNr2");
///
/// // Query
/// std::string id;
/// api.GetPrimaryId("windchill", &id);
///
/// // Get all domains
/// std::vector<TfToken> domains = api.GetDomains();
///
/// // Get full domain dictionary
/// VtDictionary domainDict;
/// api.GetDomainData("windchill", &domainDict);
/// ```
///
class UsdSourceIdAPI : public UsdAPISchemaBase
{
public:
    /// Compile time constant representing what kind of schema this class is.
    static const UsdSchemaKind schemaKind = UsdSchemaKind::NonAppliedAPI;

    /// Construct a UsdSourceIdAPI on UsdPrim \p prim.
    explicit UsdSourceIdAPI(const UsdPrim& prim = UsdPrim())
        : UsdAPISchemaBase(prim)
    {
    }

    /// Construct a UsdSourceIdAPI on the prim held by \p schemaObj.
    explicit UsdSourceIdAPI(const UsdSchemaBase& schemaObj)
        : UsdAPISchemaBase(schemaObj)
    {
    }

    /// Destructor.
    USDSOURCEID_API
    virtual ~UsdSourceIdAPI();

    /// Return a UsdSourceIdAPI holding the prim adhering to this
    /// schema at \p path on \p stage.
    USDSOURCEID_API
    static UsdSourceIdAPI
    Get(const UsdStagePtr &stage, const SdfPath &path);

    // Non-applied schemas have no Apply() or CanApply() methods.
    // Construct directly on any prim, like UsdModelAPI.

    // --------------------------------------------------------------------- //
    // SOURCE IDENTIFIER ACCESSORS
    // --------------------------------------------------------------------- //

    /// \name Source Identifier Access
    /// @{

    /// Returns all domain names that have source identifiers on this prim.
    ///
    /// Domains are the top-level keys within assetInfo["sourceIds"].
    /// For example, if the prim carries identifiers from "windchill" and
    /// "ifc", this returns {"windchill", "ifc"}.
    USDSOURCEID_API
    std::vector<TfToken> GetDomains() const;

    /// Returns the primary identifier for the given \p domain.
    ///
    /// Returns true if the domain exists and has a primaryId.
    USDSOURCEID_API
    bool GetPrimaryId(const TfToken &domain, std::string *primaryId) const;

    /// Returns the revision string for the given \p domain.
    ///
    /// Returns true if the domain exists and has a revision.
    USDSOURCEID_API
    bool GetRevision(const TfToken &domain, std::string *revision) const;

    /// Returns the full metadata dictionary for the given \p domain.
    ///
    /// This includes all key-value pairs within the domain's "metadata"
    /// sub-dictionary.
    USDSOURCEID_API
    bool GetDomainMetadata(const TfToken &domain,
                           VtDictionary *metadata) const;

    /// Returns the complete data dictionary for the given \p domain.
    ///
    /// This includes primaryId, revision, metadata, and any other keys.
    USDSOURCEID_API
    bool GetDomainData(const TfToken &domain, VtDictionary *data) const;

    /// Returns the entire sourceIds dictionary.
    USDSOURCEID_API
    bool GetAllSourceIds(VtDictionary *sourceIds) const;

    /// Sets the primary identifier (and optionally revision) for \p domain.
    ///
    /// This merges into the existing assetInfo["sourceIds"] dictionary
    /// without disturbing other domains.
    USDSOURCEID_API
    void SetSourceId(const TfToken &domain,
                     const std::string &primaryId,
                     const std::string &revision = std::string()) const;

    /// Sets additional metadata for \p domain.
    ///
    /// Merges the provided dictionary into the domain's metadata
    /// sub-dictionary.
    USDSOURCEID_API
    void SetDomainMetadata(const TfToken &domain,
                           const VtDictionary &metadata) const;

    /// Sets the complete data dictionary for \p domain.
    ///
    /// Replaces the entire domain entry in sourceIds.
    USDSOURCEID_API
    void SetDomainData(const TfToken &domain,
                       const VtDictionary &data) const;

    /// Removes all source identifiers for \p domain.
    USDSOURCEID_API
    void ClearDomain(const TfToken &domain) const;

    /// Removes all source identifiers from this prim.
    USDSOURCEID_API
    void ClearAllSourceIds() const;

    /// @}

protected:
    USDSOURCEID_API
    UsdSchemaKind _GetSchemaKind() const override;

private:
    static const TfType &_GetStaticTfType();
    static bool _IsTypedSchema();

    // Helper to get the sourceIds sub-dictionary from assetInfo.
    VtDictionary _GetSourceIdsDict() const;

    // Helper to set a value within assetInfo["sourceIds"].
    void _SetSourceIdsDict(const VtDictionary &sourceIds) const;
};

PXR_NAMESPACE_CLOSE_SCOPE

#endif // PXR_USD_USD_SOURCE_ID_SOURCE_ID_API_H
