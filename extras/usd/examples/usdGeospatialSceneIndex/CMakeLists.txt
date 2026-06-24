# usdGeospatialSceneIndex -- in-tree plugin CMake (pxr_plugin pattern).
#
# Mirrors extras/imaging/examples/hdParticleField/CMakeLists.txt, but builds an
# HdSceneIndexPlugin (a FILTER that rewrites xforms) rather than an
# HdRendererPlugin, and links PROJ (the CRS engine; WKT stays opaque to USD).
#
# Requires PROJ (find_package(PROJ) or -lproj). Build inside the OpenUSD tree
# with --examples, OR out-of-tree against an installed USD (see build_standalone.sh).

set(PXR_PACKAGE usdGeospatialSceneIndex)

find_package(PROJ QUIET)

pxr_plugin(${PXR_PACKAGE}
    LIBRARIES
        tf
        gf
        sdf
        vt
        work
        plug
        usd
        usdGeom
        hd
        hf
        usdImaging
        ${PROJ_LIBRARIES}

    INCLUDE_DIRS
        ${PROJ_INCLUDE_DIRS}

    PUBLIC_CLASSES
        crsEngine
        geoResolver
        geospatialSceneIndex
        geospatialSceneIndexPlugin

    PUBLIC_HEADERS
        api.h

    RESOURCE_FILES
        plugInfo.json
)

if (NOT PROJ_FOUND)
    target_link_libraries(${PXR_PACKAGE} proj)
endif()
