# Source-identifier dimension experiments

Seven empirical experiments comparing the five source-identifier candidate
mechanisms (A, B, B', C, D) from PR #105 along the dimensions surfaced by
the proposal's principles and open questions.

## Layout

Each dimension lives in its own subdirectory:

```
dimensions/
  _harness.py            shared subprocess runner
  dim1_composition/      composition behavior (P4)
  dim2_discoverability/  discoverability (P5)
  dim3_queryability/     external queryability (P6, OQ1)
  dim4_roundtrip/        round-trip fidelity, narrow (P7)
  dim5_distribution/     schema/plugin distribution (P3)
  dim6_scope/            scope-of-applicability (OQ4)
  dim7_lexical/          vendor-name lexical scope (P3 + OQ5)
```

Per dimension:

- `experiment.py` — driver invoked from the activated shell; loops over
  approaches and writes results
- `probe.py` — runs once per approach inside an isolated subprocess
- `report.json` — uniform `{approach: {observation_key: value}}` payload
- `summary.md` — human-readable observation table (no comparative
  verdicts — those live in COMPARISON.md, authored separately after all
  seven dimensions land)

## Isolation

Approaches A and D both export a schema named `SourceIdentifiersAPI`
(intentional collision: PR #105 proposes the same public name for both).
The five approaches therefore cannot share a TfType registry. The harness
runs each approach in a fresh `USD_PYTHON` subprocess with
`PXR_PLUGINPATH_NAME` overridden to point at that approach's experiment
directory only.

## Running

```powershell
. C:\git\aarUSD\_install\activate.ps1
& $env:USD_PYTHON extras\sourceIdentifiers\experiments\dimensions\dim4_roundtrip\experiment.py
```

Authoritative criteria for what each dimension exercises:
`_pr105_snapshot/CRITERIA_FROM_PR105.md`.
