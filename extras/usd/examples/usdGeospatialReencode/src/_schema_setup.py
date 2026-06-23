"""
_schema_setup.py -- register the codeless geospatial-CRS schema at import time.

Importing this module makes `CoordinateReferenceSystem` and `CRSBindingAPI`
available so that crs:* properties authored with custom=False are recognised as
schema-defined (review fix #3a). Equivalent to setting
    PXR_PLUGINPATH_NAME=<example>/schema
before launching, but self-contained so the example "just works".
"""
import os
from pxr import Plug

_HERE = os.path.dirname(os.path.abspath(__file__))
_SCHEMA_DIR = os.path.normpath(os.path.join(_HERE, "..", "schema"))


def register():
    pi = os.path.join(_SCHEMA_DIR, "plugInfo.json")
    if os.path.isfile(pi):
        Plug.Registry().RegisterPlugins(_SCHEMA_DIR)
    return _SCHEMA_DIR


register()
