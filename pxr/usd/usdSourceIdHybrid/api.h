//
// Copyright 2026 NVIDIA Corporation
//
// Licensed under the terms set forth in the LICENSE.txt file available at
// https://openusd.org/license.
//
#ifndef PXR_USD_USD_SOURCE_ID_HYBRID_API_H
#define PXR_USD_USD_SOURCE_ID_HYBRID_API_H

#include "pxr/base/arch/export.h"

#if defined(PXR_STATIC)
#   define USDSOURCEIDHYBRID_API
#   define USDSOURCEIDHYBRID_API_TEMPLATE_CLASS(...)
#   define USDSOURCEIDHYBRID_API_TEMPLATE_STRUCT(...)
#   define USDSOURCEIDHYBRID_LOCAL
#else
#   if defined(USDSOURCEIDHYBRID_EXPORTS)
#       define USDSOURCEIDHYBRID_API ARCH_EXPORT
#       define USDSOURCEIDHYBRID_API_TEMPLATE_CLASS(...) ARCH_EXPORT_TEMPLATE(class, __VA_ARGS__)
#       define USDSOURCEIDHYBRID_API_TEMPLATE_STRUCT(...) ARCH_EXPORT_TEMPLATE(struct, __VA_ARGS__)
#   else
#       define USDSOURCEIDHYBRID_API ARCH_IMPORT
#       define USDSOURCEIDHYBRID_API_TEMPLATE_CLASS(...) ARCH_IMPORT_TEMPLATE(class, __VA_ARGS__)
#       define USDSOURCEIDHYBRID_API_TEMPLATE_STRUCT(...) ARCH_IMPORT_TEMPLATE(struct, __VA_ARGS__)
#   endif
#   define USDSOURCEIDHYBRID_LOCAL ARCH_HIDDEN
#endif

#endif // PXR_USD_USD_SOURCE_ID_HYBRID_API_H
