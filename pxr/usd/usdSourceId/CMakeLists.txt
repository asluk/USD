set(PXR_PREFIX pxr/usd)
set(PXR_PACKAGE usdSourceId)

pxr_library(usdSourceId
    INCLUDE_SCHEMA_FILES

    LIBRARIES
        tf
        vt
        sdf
        usd

    PUBLIC_HEADERS
        api.h

    PYMODULE_FILES
        __init__.py
)
