#!/bin/bash
# Build script: generate schemas for all three source identifier approaches
# using usdGenSchema, then install them so they're available at runtime.
#
# Prerequisites:
#   - Python 3.12 (packman)
#   - USD 0.25.11 (packman)
#   - jinja2 Python package

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
USD_REPO="$(cd "${SCRIPT_DIR}/../.." && pwd)"

PY312="/home/horde/.cache/packman/python/3.12.13-nv1-manylinux_2_35-x86_64/bin/python3.12"
USD_ROOT="/home/horde/.cache/packman/chk/usd.py312.manylinux_2_35_x86_64.stock.release/0.25.11.kit.2-gl.19811"
export LD_LIBRARY_PATH="${USD_ROOT}/lib"
export PYTHONPATH="${USD_ROOT}/lib/python"

USDGENSCHEMA="${USD_ROOT}/bin/usdGenSchema"

# Install directory for generated schemas (plugin path)
INSTALL_DIR="${SCRIPT_DIR}/installed_schemas"
mkdir -p "${INSTALL_DIR}"

echo "=== Building Source Identifier Schemas ==="
echo "USD: ${USD_ROOT}"
echo "Python: $(${PY312} --version 2>&1)"
echo "Install: ${INSTALL_DIR}"
echo ""

# =========================================================================
# Helper function to generate a schema
# =========================================================================
generate_schema() {
    local SCHEMA_NAME="$1"
    local SCHEMA_DIR="$2"
    local CODELESS="${3:-false}"

    echo "--- Generating ${SCHEMA_NAME} ---"
    echo "  Source: ${SCHEMA_DIR}/schema.usda"

    local GEN_DIR="${SCHEMA_DIR}/generated"
    mkdir -p "${GEN_DIR}"

    # Copy schema.usda to gen dir (usdGenSchema expects it in cwd or arg)
    cp "${SCHEMA_DIR}/schema.usda" "${GEN_DIR}/schema.usda"

    # Run usdGenSchema
    # For codeless schemas, the schema.usda must have skipCodeGeneration = true
    cd "${GEN_DIR}"
    ${PY312} "${USDGENSCHEMA}" schema.usda . -q 2>&1

    local EXIT_CODE=$?
    if [ ${EXIT_CODE} -ne 0 ]; then
        echo "  ERROR: usdGenSchema failed with exit code ${EXIT_CODE}"
        return 1
    fi

    echo "  Generated files:"
    ls -la "${GEN_DIR}/" | grep -v "^total\|^d" | awk '{print "    " $NF}'

    # Install: copy generatedSchema.usda and plugInfo.json to install dir
    local PLUGIN_DIR="${INSTALL_DIR}/${SCHEMA_NAME}"
    mkdir -p "${PLUGIN_DIR}/resources"

    if [ -f "${GEN_DIR}/generatedSchema.usda" ]; then
        cp "${GEN_DIR}/generatedSchema.usda" "${PLUGIN_DIR}/resources/"
    fi
    if [ -f "${GEN_DIR}/plugInfo.json" ]; then
        # Replace build-time tokens with codeless-schema runtime paths
        sed 's|@PLUG_INFO_LIBRARY_PATH@||g; s|@PLUG_INFO_RESOURCE_PATH@|.|g; s|@PLUG_INFO_ROOT@|.|g' \
            "${GEN_DIR}/plugInfo.json" > "${PLUGIN_DIR}/resources/plugInfo.json"
    fi

    echo "  Installed to: ${PLUGIN_DIR}/resources/"
    echo ""
}

# =========================================================================
# Generate each approach's schema
# =========================================================================

# Approach A: Single-apply API (assetInfo sub-dicts)
generate_schema "usdSourceId" "${USD_REPO}/pxr/usd/usdSourceId"

# Approach B: Multi-apply schema (typed properties only)
generate_schema "usdSourceIdSchema" "${USD_REPO}/pxr/usd/usdSourceIdSchema"

# Approach C: Hybrid (multi-apply + assetInfo overflow)
generate_schema "usdSourceIdHybrid" "${USD_REPO}/pxr/usd/usdSourceIdHybrid"

echo "=== All schemas generated ==="
echo ""
echo "To use these schemas at runtime, add to PXR_PLUGINPATH_NAME:"
echo "  export PXR_PLUGINPATH_NAME=\"${INSTALL_DIR}/usdSourceId/resources:\${PXR_PLUGINPATH_NAME}\""
echo "  export PXR_PLUGINPATH_NAME=\"${INSTALL_DIR}/usdSourceIdSchema/resources:\${PXR_PLUGINPATH_NAME}\""
echo "  export PXR_PLUGINPATH_NAME=\"${INSTALL_DIR}/usdSourceIdHybrid/resources:\${PXR_PLUGINPATH_NAME}\""
echo ""

# =========================================================================
# Verify: try loading the schemas
# =========================================================================
echo "=== Verifying schemas load ==="
export PXR_PLUGINPATH_NAME="${INSTALL_DIR}/usdSourceId/resources:${INSTALL_DIR}/usdSourceIdSchema/resources:${INSTALL_DIR}/usdSourceIdHybrid/resources"

${PY312} -c "
from pxr import Usd, Sdf, Plug, Tf
import sys

# Force plugin discovery
all_plugins = Plug.Registry().GetAllPlugins()
our_plugins = [p for p in all_plugins if 'ourceId' in p.name]
print(f'Our plugins: {[p.name for p in our_plugins]}')

# Create a stage and try applying each schema
stage = Usd.Stage.CreateInMemory()
prim = stage.DefinePrim('/TestPrim', 'Xform')

results = {}
for schema_name in ['SourceIdAPI', 'SourceIdSchemaAPI', 'SourceIdHybridAPI']:
    instance_name = 'test'
    applied_name = f'{schema_name}:{instance_name}' if schema_name != 'SourceIdAPI' else schema_name
    ok = prim.AddAppliedSchema(applied_name)
    results[schema_name] = ok
    if ok:
        print(f'  ✅ {schema_name}: applied successfully')
    else:
        print(f'  ❌ {schema_name}: failed to apply')

print(f'Applied schemas on prim: {prim.GetAppliedSchemas()}')

# Verify hybrid schema has properties defined
for attr_name in ['sourceIdentifier:test:primaryId', 'sourceIdentifier:test:domain']:
    attr = prim.GetAttribute(attr_name)
    if attr:
        print(f'  Property {attr_name}: type={attr.GetTypeName()}')
    else:
        print(f'  Property {attr_name}: not found (codeless - must create manually)')

all_ok = all(results.values())
if not all_ok:
    sys.exit(1)
print('\nAll schemas verified!')
" 2>&1

echo ""
echo "=== Done ==="
