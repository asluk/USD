//
// Copyright 2016 Pixar
//
// Licensed under the terms set forth in the LICENSE.txt file available at
// https://openusd.org/license.
//
#include "pxr/usd/usdSourceId/tokens.h"

PXR_NAMESPACE_OPEN_SCOPE

UsdSourceIdTokensType::UsdSourceIdTokensType() :
    metadata("metadata", TfToken::Immortal),
    primaryId("primaryId", TfToken::Immortal),
    revision("revision", TfToken::Immortal),
    sourceIds("sourceIds", TfToken::Immortal),
    SourceIdAPI("SourceIdAPI", TfToken::Immortal),
    allTokens({
        metadata,
        primaryId,
        revision,
        sourceIds,
        SourceIdAPI
    })
{
}

TfStaticData<UsdSourceIdTokensType> UsdSourceIdTokens;

PXR_NAMESPACE_CLOSE_SCOPE
