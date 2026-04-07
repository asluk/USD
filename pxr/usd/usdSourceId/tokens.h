//
// Copyright 2026 NVIDIA Corporation
//
// Licensed under the terms set forth in the LICENSE.txt file available at
// https://openusd.org/license.
//
#ifndef PXR_USD_USD_SOURCE_ID_TOKENS_H
#define PXR_USD_USD_SOURCE_ID_TOKENS_H

/// \file usdSourceId/tokens.h

#include "pxr/pxr.h"
#include "pxr/usd/usdSourceId/api.h"
#include "pxr/base/tf/staticTokens.h"

PXR_NAMESPACE_OPEN_SCOPE

/// \hideinitializer
#define USDSOURCEID_TOKENS \
    (sourceIds) \
    (primaryId) \
    (revision) \
    ((metadata_, "metadata"))

TF_DECLARE_PUBLIC_TOKENS(UsdSourceIdTokens, USDSOURCEID_API,
    USDSOURCEID_TOKENS);

PXR_NAMESPACE_CLOSE_SCOPE

#endif // PXR_USD_USD_SOURCE_ID_TOKENS_H
