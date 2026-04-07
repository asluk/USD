//
// Copyright 2016 Pixar
//
// Licensed under the terms set forth in the LICENSE.txt file available at
// https://openusd.org/license.
//
#ifndef USDSOURCEIDSCHEMA_TOKENS_H
#define USDSOURCEIDSCHEMA_TOKENS_H

/// \file usdSourceIdSchema/tokens.h

// XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
// 
// This is an automatically generated file (by usdGenSchema.py).
// Do not hand-edit!
// 
// XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

#include "pxr/pxr.h"
#include "pxr/usd/usdSourceIdSchema/api.h"
#include "pxr/base/tf/staticData.h"
#include "pxr/base/tf/token.h"
#include <vector>

PXR_NAMESPACE_OPEN_SCOPE


/// \class UsdSourceIdSchemaTokensType
///
/// \link UsdSourceIdSchemaTokens \endlink provides static, efficient
/// \link TfToken TfTokens\endlink for use in all public USD API.
///
/// These tokens are auto-generated from the module's schema, representing
/// property names, for when you need to fetch an attribute or relationship
/// directly by name, e.g. UsdPrim::GetAttribute(), in the most efficient
/// manner, and allow the compiler to verify that you spelled the name
/// correctly.
///
/// UsdSourceIdSchemaTokens also contains all of the \em allowedTokens values
/// declared for schema builtin attributes of 'token' scene description type.
/// Use UsdSourceIdSchemaTokens like so:
///
/// \code
///     gprim.GetMyTokenValuedAttr().Set(UsdSourceIdSchemaTokens->sourceIdentifier);
/// \endcode
struct UsdSourceIdSchemaTokensType {
    USDSOURCEIDSCHEMA_API UsdSourceIdSchemaTokensType();
    /// \brief "sourceIdentifier"
    /// 
    /// Property namespace prefix for the UsdSourceIdSchemaSourceIdentifierAPI schema.
    const TfToken sourceIdentifier;
    /// \brief "sourceIdentifier:__INSTANCE_NAME__:domain"
    /// 
    /// UsdSourceIdSchemaSourceIdentifierAPI
    const TfToken sourceIdentifier_MultipleApplyTemplate_Domain;
    /// \brief "sourceIdentifier:__INSTANCE_NAME__:label"
    /// 
    /// UsdSourceIdSchemaSourceIdentifierAPI
    const TfToken sourceIdentifier_MultipleApplyTemplate_Label;
    /// \brief "sourceIdentifier:__INSTANCE_NAME__:primaryId"
    /// 
    /// UsdSourceIdSchemaSourceIdentifierAPI
    const TfToken sourceIdentifier_MultipleApplyTemplate_PrimaryId;
    /// \brief "sourceIdentifier:__INSTANCE_NAME__:revision"
    /// 
    /// UsdSourceIdSchemaSourceIdentifierAPI
    const TfToken sourceIdentifier_MultipleApplyTemplate_Revision;
    /// \brief "SourceIdentifierAPI"
    /// 
    /// Schema identifer and family for UsdSourceIdSchemaSourceIdentifierAPI
    const TfToken SourceIdentifierAPI;
    /// A vector of all of the tokens listed above.
    const std::vector<TfToken> allTokens;
};

/// \var UsdSourceIdSchemaTokens
///
/// A global variable with static, efficient \link TfToken TfTokens\endlink
/// for use in all public USD API.  \sa UsdSourceIdSchemaTokensType
extern USDSOURCEIDSCHEMA_API TfStaticData<UsdSourceIdSchemaTokensType> UsdSourceIdSchemaTokens;

PXR_NAMESPACE_CLOSE_SCOPE

#endif
