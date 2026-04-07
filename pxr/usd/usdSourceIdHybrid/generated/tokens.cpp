//
// Copyright 2016 Pixar
//
// Licensed under the terms set forth in the LICENSE.txt file available at
// https://openusd.org/license.
//
#include "pxr/usd/usdSourceIdHybrid/tokens.h"

PXR_NAMESPACE_OPEN_SCOPE

UsdSourceIdHybridTokensType::UsdSourceIdHybridTokensType() :
    sourceIdentifier("sourceIdentifier", TfToken::Immortal),
    sourceIdentifier_MultipleApplyTemplate_Domain("sourceIdentifier:__INSTANCE_NAME__:domain", TfToken::Immortal),
    sourceIdentifier_MultipleApplyTemplate_Label("sourceIdentifier:__INSTANCE_NAME__:label", TfToken::Immortal),
    sourceIdentifier_MultipleApplyTemplate_PrimaryId("sourceIdentifier:__INSTANCE_NAME__:primaryId", TfToken::Immortal),
    sourceIdentifier_MultipleApplyTemplate_Revision("sourceIdentifier:__INSTANCE_NAME__:revision", TfToken::Immortal),
    SourceIdentifierAPI("SourceIdentifierAPI", TfToken::Immortal),
    allTokens({
        sourceIdentifier,
        sourceIdentifier_MultipleApplyTemplate_Domain,
        sourceIdentifier_MultipleApplyTemplate_Label,
        sourceIdentifier_MultipleApplyTemplate_PrimaryId,
        sourceIdentifier_MultipleApplyTemplate_Revision,
        SourceIdentifierAPI
    })
{
}

TfStaticData<UsdSourceIdHybridTokensType> UsdSourceIdHybridTokens;

PXR_NAMESPACE_CLOSE_SCOPE
