//
// Copyright 2016 Pixar
//
// Licensed under the terms set forth in the LICENSE.txt file available at
// https://openusd.org/license.
//
// GENERATED FILE.  DO NOT EDIT.
#include "pxr/external/boost/python/class.hpp"
#include "pxr/usd/usdSourceIdHybrid/tokens.h"

PXR_NAMESPACE_USING_DIRECTIVE

#define _ADD_TOKEN(cls, name) \
    cls.add_static_property(#name, +[]() { return UsdSourceIdHybridTokens->name.GetString(); });

void wrapUsdSourceIdHybridTokens()
{
    pxr_boost::python::class_<UsdSourceIdHybridTokensType, pxr_boost::python::noncopyable>
        cls("Tokens", pxr_boost::python::no_init);
    _ADD_TOKEN(cls, sourceIdentifier);
    _ADD_TOKEN(cls, sourceIdentifier_MultipleApplyTemplate_Domain);
    _ADD_TOKEN(cls, sourceIdentifier_MultipleApplyTemplate_Label);
    _ADD_TOKEN(cls, sourceIdentifier_MultipleApplyTemplate_PrimaryId);
    _ADD_TOKEN(cls, sourceIdentifier_MultipleApplyTemplate_Revision);
    _ADD_TOKEN(cls, SourceIdentifierAPI);
}
