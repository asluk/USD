//
// Copyright 2026 NVIDIA Corporation
//
// Licensed under the terms set forth in the LICENSE.txt file available at
// https://openusd.org/license.
//
#ifndef PXR_USD_USD_SOURCE_ID_SCHEMA_TOKENS_H
#define PXR_USD_USD_SOURCE_ID_SCHEMA_TOKENS_H

/// \file usdSourceIdSchema/tokens.h

#include "pxr/pxr.h"
#include "pxr/usd/usdSourceIdSchema/api.h"
#include "pxr/base/tf/staticTokens.h"

PXR_NAMESPACE_OPEN_SCOPE

/// \hideinitializer
#define USDSOURCEIDSCHEMA_TOKENS \
    ((sourceIdentifier, "sourceIdentifier")) \
    (primaryId) \
    (revision) \
    (domain) \
    (label)

TF_DECLARE_PUBLIC_TOKENS(UsdSourceIdSchemaTokens, USDSOURCEIDSCHEMA_API,
    USDSOURCEIDSCHEMA_TOKENS);

PXR_NAMESPACE_CLOSE_SCOPE

#endif // PXR_USD_USD_SOURCE_ID_SCHEMA_TOKENS_H
