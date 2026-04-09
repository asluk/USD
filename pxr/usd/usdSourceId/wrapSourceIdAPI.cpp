//
// Copyright 2026 NVIDIA Corporation
//
// Licensed under the terms set forth in the LICENSE.txt file available at
// https://openusd.org/license.
//
#include "pxr/usd/usdSourceId/sourceIdAPI.h"
#include "pxr/usd/usd/schemaBase.h"

#include "pxr/usd/sdf/primSpec.h"

#include "pxr/usd/usd/pyConversions.h"
#include "pxr/base/tf/pyContainerConversions.h"
#include "pxr/base/tf/pyResultConversions.h"
#include "pxr/base/tf/pyUtils.h"
#include "pxr/base/tf/wrapTypeHelpers.h"

#include "pxr/external/boost/python.hpp"

#include <string>

PXR_NAMESPACE_USING_DIRECTIVE

using namespace pxr_boost::python;

namespace {

static std::string
_Repr(const UsdSourceIdAPI &self)
{
    std::string primRepr = TfPyRepr(self.GetPrim());
    return TfStringPrintf(
        "UsdSourceId.SourceIdAPI(%s)",
        primRepr.c_str());
}

static object
_GetPrimaryId(const UsdSourceIdAPI &self, const TfToken &domain)
{
    std::string result;
    if (self.GetPrimaryId(domain, &result)) {
        return object(result);
    }
    return object();
}

static object
_GetRevision(const UsdSourceIdAPI &self, const TfToken &domain)
{
    std::string result;
    if (self.GetRevision(domain, &result)) {
        return object(result);
    }
    return object();
}

static object
_GetDomainMetadata(const UsdSourceIdAPI &self, const TfToken &domain)
{
    VtDictionary result;
    if (self.GetDomainMetadata(domain, &result)) {
        return object(result);
    }
    return object();
}

static object
_GetDomainData(const UsdSourceIdAPI &self, const TfToken &domain)
{
    VtDictionary result;
    if (self.GetDomainData(domain, &result)) {
        return object(result);
    }
    return object();
}

static object
_GetAllSourceIds(const UsdSourceIdAPI &self)
{
    VtDictionary result;
    if (self.GetAllSourceIds(&result)) {
        return object(result);
    }
    return object();
}

} // anonymous namespace

void wrapUsdSourceIdAPI()
{
    typedef UsdSourceIdAPI This;

    class_<This, bases<UsdAPISchemaBase> >
        cls("SourceIdAPI");

    cls
        .def(init<UsdPrim>(arg("prim")))
        .def(init<UsdSchemaBase const&>(arg("schemaObj")))
        .def(TfTypePythonClass())

        .def("Get", &This::Get, (arg("stage"), arg("path")))
        .staticmethod("Get")

        .def("_GetStaticTfType", (TfType const &(*)()) TfType::Find<This>,
             return_value_policy<return_by_value>())
        .staticmethod("_GetStaticTfType")

        .def(!self)

        // Convenience accessors
        .def("GetDomains", &This::GetDomains,
             return_value_policy<TfPySequenceToList>())
        .def("GetPrimaryId", &_GetPrimaryId, arg("domain"))
        .def("GetRevision", &_GetRevision, arg("domain"))
        .def("GetDomainMetadata", &_GetDomainMetadata, arg("domain"))
        .def("GetDomainData", &_GetDomainData, arg("domain"))
        .def("GetAllSourceIds", &_GetAllSourceIds)

        .def("SetSourceId", &This::SetSourceId,
             (arg("domain"), arg("primaryId"), arg("revision")=""))
        .def("SetDomainMetadata", &This::SetDomainMetadata,
             (arg("domain"), arg("metadata")))
        .def("SetDomainData", &This::SetDomainData,
             (arg("domain"), arg("data")))
        .def("ClearDomain", &This::ClearDomain, arg("domain"))
        .def("ClearAllSourceIds", &This::ClearAllSourceIds)

        .def("__repr__", ::_Repr)
    ;
}
