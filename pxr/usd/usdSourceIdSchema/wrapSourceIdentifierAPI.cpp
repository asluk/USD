//
// Copyright 2026 NVIDIA Corporation
//
// Licensed under the terms set forth in the LICENSE.txt file available at
// https://openusd.org/license.
//
#include "pxr/usd/usdSourceIdSchema/sourceIdentifierAPI.h"
#include "pxr/usd/usd/schemaBase.h"

#include "pxr/usd/sdf/primSpec.h"

#include "pxr/usd/usd/pyConversions.h"
#include "pxr/base/tf/pyAnnotatedBoolResult.h"
#include "pxr/base/tf/pyContainerConversions.h"
#include "pxr/base/tf/pyResultConversions.h"
#include "pxr/base/tf/pyUtils.h"
#include "pxr/base/tf/wrapTypeHelpers.h"

#include "pxr/external/boost/python.hpp"

#include <string>

PXR_NAMESPACE_USING_DIRECTIVE

using namespace pxr_boost::python;

namespace {

static UsdAttribute
_CreatePrimaryIdAttr(UsdSourceIdSchemaAPI &self,
                     object defaultVal, bool writeSparsely) {
    return self.CreatePrimaryIdAttr(
        UsdPythonToSdfType(defaultVal, SdfValueTypeNames->String),
        writeSparsely);
}

static UsdAttribute
_CreateRevisionAttr(UsdSourceIdSchemaAPI &self,
                    object defaultVal, bool writeSparsely) {
    return self.CreateRevisionAttr(
        UsdPythonToSdfType(defaultVal, SdfValueTypeNames->String),
        writeSparsely);
}

static UsdAttribute
_CreateDomainAttr(UsdSourceIdSchemaAPI &self,
                  object defaultVal, bool writeSparsely) {
    return self.CreateDomainAttr(
        UsdPythonToSdfType(defaultVal, SdfValueTypeNames->Token),
        writeSparsely);
}

static UsdAttribute
_CreateLabelAttr(UsdSourceIdSchemaAPI &self,
                 object defaultVal, bool writeSparsely) {
    return self.CreateLabelAttr(
        UsdPythonToSdfType(defaultVal, SdfValueTypeNames->String),
        writeSparsely);
}

static std::string
_Repr(const UsdSourceIdSchemaAPI &self)
{
    std::string primRepr = TfPyRepr(self.GetPrim());
    std::string instanceName = self.GetName().GetString();
    return TfStringPrintf(
        "UsdSourceIdSchema.SourceIdSchemaAPI(%s, '%s')",
        primRepr.c_str(), instanceName.c_str());
}

struct UsdSourceIdSchemaAPI_CanApplyResult :
    public TfPyAnnotatedBoolResult<std::string>
{
    UsdSourceIdSchemaAPI_CanApplyResult(bool val, std::string const &msg) :
        TfPyAnnotatedBoolResult<std::string>(val, msg) {}
};

static UsdSourceIdSchemaAPI_CanApplyResult
_WrapCanApply(const UsdPrim& prim, const TfToken& name)
{
    std::string whyNot;
    bool result = UsdSourceIdSchemaAPI::CanApply(prim, name, &whyNot);
    return UsdSourceIdSchemaAPI_CanApplyResult(result, whyNot);
}

} // anonymous namespace

void wrapUsdSourceIdSchemaAPI()
{
    typedef UsdSourceIdSchemaAPI This;

    UsdSourceIdSchemaAPI_CanApplyResult::Wrap<
        UsdSourceIdSchemaAPI_CanApplyResult>(
        "_CanApplyResult", "whyNot");

    class_<This, bases<UsdAPISchemaBase> >
        cls("SourceIdSchemaAPI");

    cls
        .def(init<UsdPrim, TfToken>((arg("prim"), arg("name"))))
        .def(init<UsdSchemaBase const&, TfToken>((arg("schemaObj"), arg("name"))))
        .def(TfTypePythonClass())

        .def("Get",
            (UsdSourceIdSchemaAPI(*)(const UsdStagePtr &stage,
                                     const SdfPath &path,
                                     const TfToken &name))
               &This::Get,
            (arg("stage"), arg("path"), arg("name")))
        .def("Get",
            (UsdSourceIdSchemaAPI(*)(const UsdPrim &prim,
                                     const TfToken &name))
               &This::Get,
            (arg("prim"), arg("name")))
        .staticmethod("Get")

        .def("GetAll", &This::GetAll,
            arg("prim"),
            return_value_policy<TfPySequenceToList>())
        .staticmethod("GetAll")

        .def("CanApply", &_WrapCanApply, (arg("prim"), arg("name")))
        .staticmethod("CanApply")

        .def("Apply", &This::Apply, (arg("prim"), arg("name")))
        .staticmethod("Apply")

        .def("GetSchemaAttributeNames",
             &This::GetSchemaAttributeNames,
             (arg("includeInherited")=true,
              arg("instanceName")=TfToken()),
             return_value_policy<TfPySequenceToList>())
        .staticmethod("GetSchemaAttributeNames")

        .def("_GetStaticTfType", (TfType const &(*)()) TfType::Find<This>,
             return_value_policy<return_by_value>())
        .staticmethod("_GetStaticTfType")

        .def(!self)

        .def("GetPrimaryIdAttr",
             &This::GetPrimaryIdAttr)
        .def("CreatePrimaryIdAttr",
             &_CreatePrimaryIdAttr,
             (arg("defaultValue")=object(),
              arg("writeSparsely")=false))

        .def("GetRevisionAttr",
             &This::GetRevisionAttr)
        .def("CreateRevisionAttr",
             &_CreateRevisionAttr,
             (arg("defaultValue")=object(),
              arg("writeSparsely")=false))

        .def("GetDomainAttr",
             &This::GetDomainAttr)
        .def("CreateDomainAttr",
             &_CreateDomainAttr,
             (arg("defaultValue")=object(),
              arg("writeSparsely")=false))

        .def("GetLabelAttr",
             &This::GetLabelAttr)
        .def("CreateLabelAttr",
             &_CreateLabelAttr,
             (arg("defaultValue")=object(),
              arg("writeSparsely")=false))

        .def("__repr__", ::_Repr)
    ;
}
