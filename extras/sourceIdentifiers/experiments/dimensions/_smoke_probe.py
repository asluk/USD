"""Smoke probe for the harness — verifies subprocess isolation works.

Argv: <approach>

Emits JSON {approach, schemas_registered} where schemas_registered lists
the schema class names the loaded plugin exports. The expectation is each
approach reports a distinct set, no leakage from other approaches.
"""
import json
import sys

from pxr import Plug, Usd


def main():
    approach = sys.argv[1]
    reg = Usd.SchemaRegistry()
    # Enumerate the schemas in this approach's plugInfo by querying the
    # plugin directly (more reliable than scanning the global registry for
    # known names).
    plugins = [p for p in Plug.Registry().GetAllPlugins()
               if 'sourceIdentifiers' in p.name]
    schemas_by_plugin = {}
    for p in plugins:
        # Plug.Plugin exposes metadata; pull the Types section if present.
        meta = p.metadata or {}
        types = meta.get('Types', {})
        schemas_by_plugin[p.name] = sorted(types.keys())

    out = {
        'approach': approach,
        'plugins_loaded': schemas_by_plugin,
        'is_multiple_apply_SourceIdentifiersAPI': reg.IsMultipleApplyAPISchema('SourceIdentifiersAPI'),
        'is_single_apply_SourceIdentifiersAPI': reg.IsAppliedAPISchema('SourceIdentifiersAPI') and not reg.IsMultipleApplyAPISchema('SourceIdentifiersAPI'),
    }
    print(json.dumps(out))


if __name__ == '__main__':
    main()
