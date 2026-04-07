//
// Copyright 2016 Pixar
//
// Licensed under the terms set forth in the LICENSE.txt file available at
// https://openusd.org/license.
//
#ifndef USDSOURCEIDHYBRID_TOKENS_H
#define USDSOURCEIDHYBRID_TOKENS_H

/// \file usdSourceIdHybrid/tokens.h

// XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
// 
// This is an automatically generated file (by usdGenSchema.py).
// Do not hand-edit!
// 
// XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

#include "pxr/pxr.h"
#include "pxr/usd/usdSourceIdHybrid/api.h"
#include "pxr/base/tf/staticData.h"
#include "pxr/base/tf/token.h"
#include <vector>

PXR_NAMESPACE_OPEN_SCOPE


/// \class UsdSourceIdHybridTokensType
///
/// \link UsdSourceIdHybridTokens \endlink provides static, efficient
/// \link TfToken TfTokens\endlink for use in all public USD API.
///
/// These tokens are auto-generated from the module's schema, representing
/// property names, for when you need to fetch an attribute or relationship
/// directly by name, e.g. UsdPrim::GetAttribute(), in the most efficient
/// manner, and allow the compiler to verify that you spelled the name
/// correctly.
///
/// UsdSourceIdHybridTokens also contains all of the \em allowedTokens values
/// declared for schema builtin attributes of 'token' scene description type.
/// Use UsdSourceIdHybridTokens like so:
///
/// \code
///     gprim.GetMyTokenValuedAttr().Set(UsdSourceIdHybridTokens->sourceIdentifier);
/// \endcode
struct UsdSourceIdHybridTokensType {
    USDSOURCEIDHYBRID_API UsdSourceIdHybridTokensType();
    /// \brief "sourceIdentifier"
    /// 
    /// Property namespace prefix for the UsdSourceIdHybridSourceIdHybridAPI schema.
    const TfToken sourceIdentifier;
    /// \brief "sourceIdentifier:__INSTANCE_NAME__:domain"
    /// 
    /// UsdSourceIdHybridSourceIdHybridAPI
    const TfToken sourceIdentifier_MultipleApplyTemplate_Domain;
    /// \brief "sourceIdentifier:__INSTANCE_NAME__:label"
    /// 
    /// UsdSourceIdHybridSourceIdHybridAPI
    const TfToken sourceIdentifier_MultipleApplyTemplate_Label;
    /// \brief "sourceIdentifier:__INSTANCE_NAME__:primaryId"
    /// 
    /// UsdSourceIdHybridSourceIdHybridAPI
    const TfToken sourceIdentifier_MultipleApplyTemplate_PrimaryId;
    /// \brief "sourceIdentifier:__INSTANCE_NAME__:revision"
    /// 
    /// UsdSourceIdHybridSourceIdHybridAPI
    const TfToken sourceIdentifier_MultipleApplyTemplate_Revision;
    /// \brief "SourceIdHybridAPI"
    /// 
    /// Schema identifer and family for UsdSourceIdHybridSourceIdHybridAPI
    const TfToken SourceIdHybridAPI;
    /// A vector of all of the tokens listed above.
    const std::vector<TfToken> allTokens;
};

/// \var UsdSourceIdHybridTokens
///
/// A global variable with static, efficient \link TfToken TfTokens\endlink
/// for use in all public USD API.  \sa UsdSourceIdHybridTokensType
extern USDSOURCEIDHYBRID_API TfStaticData<UsdSourceIdHybridTokensType> UsdSourceIdHybridTokens;

PXR_NAMESPACE_CLOSE_SCOPE

#endif
