set(PXR_PREFIX pxr/usd)
set(PXR_PACKAGE usdSourceIdSchema)

pxr_library(usdSourceIdSchema
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
