//
// Copyright 2016 Pixar
//
// Licensed under the terms set forth in the LICENSE.txt file available at
// https://openusd.org/license.
//
#ifndef USDSOURCEID_TOKENS_H
#define USDSOURCEID_TOKENS_H

/// \file usdSourceId/tokens.h

// XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
// 
// This is an automatically generated file (by usdGenSchema.py).
// Do not hand-edit!
// 
// XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

#include "pxr/pxr.h"
#include "pxr/usd/usdSourceId/api.h"
#include "pxr/base/tf/staticData.h"
#include "pxr/base/tf/token.h"
#include <vector>

PXR_NAMESPACE_OPEN_SCOPE


/// \class UsdSourceIdTokensType
///
/// \link UsdSourceIdTokens \endlink provides static, efficient
/// \link TfToken TfTokens\endlink for use in all public USD API.
///
/// These tokens are auto-generated from the module's schema, representing
/// property names, for when you need to fetch an attribute or relationship
/// directly by name, e.g. UsdPrim::GetAttribute(), in the most efficient
/// manner, and allow the compiler to verify that you spelled the name
/// correctly.
///
/// UsdSourceIdTokens also contains all of the \em allowedTokens values
/// declared for schema builtin attributes of 'token' scene description type.
/// Use UsdSourceIdTokens like so:
///
/// \code
///     gprim.GetMyTokenValuedAttr().Set(UsdSourceIdTokens->metadata);
/// \endcode
struct UsdSourceIdTokensType {
    USDSOURCEID_API UsdSourceIdTokensType();
    /// \brief "metadata"
    /// 
    /// Key within a domain's source identifier dictionary for additional metadata.
    const TfToken metadata;
    /// \brief "primaryId"
    /// 
    /// Key within a domain's source identifier dictionary for the primary identifier string.
    const TfToken primaryId;
    /// \brief "revision"
    /// 
    /// Key within a domain's source identifier dictionary for the revision string.
    const TfToken revision;
    /// \brief "sourceIds"
    /// 
    /// Dictionary key in assetInfo for the source identifiers sub-dictionary.
    const TfToken sourceIds;
    /// \brief "SourceIdAPI"
    /// 
    /// Schema identifer and family for UsdSourceIdSourceIdAPI
    const TfToken SourceIdAPI;
    /// A vector of all of the tokens listed above.
    const std::vector<TfToken> allTokens;
};

/// \var UsdSourceIdTokens
///
/// A global variable with static, efficient \link TfToken TfTokens\endlink
/// for use in all public USD API.  \sa UsdSourceIdTokensType
extern USDSOURCEID_API TfStaticData<UsdSourceIdTokensType> UsdSourceIdTokens;

PXR_NAMESPACE_CLOSE_SCOPE

#endif
