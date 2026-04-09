set(PXR_PREFIX pxr/usd)
set(PXR_PACKAGE usdSourceIdHybrid)

pxr_library(usdSourceIdHybrid
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
