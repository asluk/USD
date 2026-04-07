# Plan: Writing the Comparison Document

## Problem diagnosed
I've failed to write this document 3+ times because:
1. The comparison doc is large — writing it in one shot risks context overflow mid-write
2. I was re-reading too much context each attempt instead of just writing
3. I wasn't committing partial progress

## Strategy
Write COMPARISON.md in **7 independent sections**, each as its own commit. Each section should be writable from memory + minimal file reads. **Commit and push after EVERY section.**

## Sections (in order)

### Section 1: Header + Executive Summary (~200 lines)
- Needs: stress_test_results.json, vendor_adoption_analysis.json (already memorized)
- Key data points are in memory/2026-04-07.md
- NO reads needed — write from memory

### Section 2: Approach Descriptions (~150 lines)
- Brief description of each approach + code snippets
- Needs: quick glance at schema.usda files (both small)
- Reads: pxr/usd/usdSourceId/schema.usda, pxr/usd/usdSourceIdSchema/schema.usda

### Section 3: Composition Behavior (~150 lines)
- How each approach composes across layers
- Needs: composition_test examples
- Reads: examples/composition_test_a_override.usda, examples/composition_test_b_override.usda

### Section 4: Industry Scenario Analysis (~200 lines)
- Manufacturing, AECO, robotics findings
- Key finding: domain-specific metadata flexibility
- NO reads needed — findings are in memory

### Section 5: Ecosystem Simulation & Stress Tests (~200 lines)
- Empirical data from stress tests
- Vendor adoption scoring
- Reads: stress_test_results.json (one small file)

### Section 6: Governance & Validator Design (~250 lines)
- How standards bodies handle this (from governance research in memory)
- Concrete validator pseudocode for both approaches
- Deployment friction for identifier stakeholders
- NO reads needed — governance findings in memory/2026-04-07.md

### Section 7: Hybrid Analysis & Recommendation (~200 lines)
- Approach C: combine A+B
- Final recommendation with nuance
- NO reads needed — synthesis from prior sections

## Rules for myself
1. Write ONE section per turn
2. Commit + push immediately after writing each section
3. Send Aaron a message after each push
4. If I need to read a file, read it BEFORE starting to write (not mid-write)
5. Don't re-read the proposal or STATUS.md — I already know the content
6. Target: all 7 sections done in 7 turns
