# Agentic Development: Lessons from the Source Identifiers Comparison

*A retrospective on building a technical analysis document with an AI agent.*

> **Note on currency.** This retrospective documents the April 7–8,
> 2026 work that produced the original three-approach comparison
> (A / B / C) with a recommendation toward Approach C. The work was
> subsequently expanded to four approaches (adding D), then re-anchored
> in 2026-05-06→07 around an empirical field census and a
> principle-derived scoring rebuild that retracted any single-mechanism
> leaning. The PR-level methodology retrospective at
> `https://github.com/asluk/USD/pull/7` (issue comment) covers that
> later journey. The references below to "the recommended approach"
> describe the state of the comparison at the time this document was
> written, not the current state.

## 1. Project Scope

This document was produced through human-agent collaboration over approximately
26 hours across two sessions on April 7–8, 2026. The deliverable: a comparison
of three approaches for adding source identifiers to OpenUSD, intended for
review by the AOUSD Technical Advisory Council.

**What was built:**
- `COMPARISON.md` — a ~470-line review guide with executive summary and recommendation
- 8 detail files covering approach descriptions, composition behavior, industry scenarios, governance, hybrid analysis, stress tests, registry-spec analysis, and scope promotion simulation
- 3 schema implementations (non-applied, applied, hybrid) built and validated with `usdGenSchema`
- `.usda` examples across 4 industry verticals (AECO, manufacturing, robotics, M&E)
- Python stress tests and a 5-phase scope promotion simulation
- 37 commits on branch `aluk/source-identifiers-comparison`

**Scale:**
- Session 1: 19 hours, 79 user messages, 27 context compactions, 18 prompt errors
- Session 2: 7+ hours, 24+ user messages, 6 LLM idle timeouts
- Total: ~103 human messages guiding the work

## 2. What the Agent Did Autonomously

The human said "I'll leave you running overnight — good luck!" at 04:23 UTC
and checked back at 08:39. During those ~4 hours unsupervised, the agent:

- Implemented Approach A (assetInfo dictionaries) and Approach B (applied schemas)
  with schema definitions, `.usda` examples, and `plugInfo.json` registration
- Built stress tests generating thousands of prims with identifiers
- Created vendor simulation examples (Windchill PLM, AAS digital twins)
- Added composition tests (sublayer override, reference resolution)
- Ran benchmarks comparing authoring verbosity and query performance
- Made 6 commits and pushed to remote

This worked well. The agent is good at volume work with clear specs: generate
examples, run tests, commit results. No human judgment calls were needed.

**What the agent could not do autonomously:**
- Decide *what matters* to the reviewers
- Detect its own hallucinations about external standards
- Manage its own context window
- Recover from compaction without losing its place

## 3. The Compaction Crisis

Between 13:25 and 14:22 UTC — a 57-minute period — the human gave the same
instruction four times: "write the comparison document."

Each time, the agent acknowledged the instruction, began reading source files
to prepare, and then hit a context window limit. The system compacted the
conversation (replacing older messages with a summary), and the agent woke up
without memory of the instruction. It re-read the same files, preparing to do
work it had already been told to do, and overflowed again.

The agent could not self-diagnose this loop. From its perspective, each
post-compaction turn was a fresh start. The human had to identify the pattern:

> "I've given you the same instructions 4x now — I really need you to diagnose
> what is going wrong."

**The fix came from the human, not the agent:** write a strategy document to
disk *first*, then execute from the file in small phases, committing after each
one. This became `COMPARISON_PLAN.md` and later the `TASK.md` pattern used in
Session 2.

**Why this matters:** The agent's failure mode was invisible to itself. Context
compaction is not like human forgetting — there is no sense of "I think I was
doing something." The summary may or may not capture the current task. Without
an external checkpoint (a file on disk), the agent has no way to distinguish
"I haven't started yet" from "I've been told four times and failed four times."

The `TASK.md` pattern — write the full plan to a file, track progress with
checkboxes, check the file after every compaction — eliminated this failure
mode entirely. Every subsequent multi-step task in Session 2 completed without
a single compaction-related loss.

## 4. Hallucinations Caught by the Human

At 16:00 UTC, the human sent a five-word message that prevented a credibility
damaging error from reaching reviewers:

> "Khronos does not govern MaterialX."

The agent had attributed MaterialX to the Khronos Group in a vendor simulation
example. MaterialX is governed by the Academy Software Foundation (ASWF), not
Khronos. The agent had also fabricated an identifier format for MaterialX that
does not exist in the specification.

The human followed up: "Is that identifier really a MaterialX identifier? What
does it mean?" — forcing the agent to verify rather than confabulate. The
identifier was replaced with an ASHRAE equipment classification (a real standard
with real identifier formats).

This was not an isolated incident. A later self-directed fact-check found:

- **IFC GlobalId** described as "always instance-level" — wrong. Both
  `IfcTypeObject` and `IfcObject` inherit `GloballyUniqueId` from `IfcRoot`.
- **glTF and MaterialX** lumped together as having similar identifier models —
  wrong. glTF uses integer indices within a file; MaterialX uses hierarchical
  named paths. They have fundamentally different type-vs-instance semantics.
- **bSDD** described with incorrect tier structure for its classification system.

**Pattern:** The agent hallucinates most confidently about external standards.
It generates plausible-sounding URIs, governance claims, and identifier formats
that do not exist. The more obscure the standard, the higher the hallucination
risk. Every external identifier, URI scheme, and governance claim in the final
document was verified against primary sources — but only after the human caught
the first one.

## 5. External Reviewer Impact

Three interventions from outside the human-agent pair changed the document:

**A USD core team member** relayed feedback at 18:06 UTC: "Curious why
Approach A is a single apply schema instead of an unapplied schema like
ModelAPI." This changed Approach A's design from an applied schema to a
non-applied schema — a fundamental architectural difference that affects how
identifiers compose across layers. The agent updated all examples, simulations,
and analysis within 10 minutes. The speed of propagating a design change across
dozens of files is where the agent earned its keep.

**An upstream OpenUSD pull request** about reducing review burden for large
documents motivated restructuring `COMPARISON.md` from 1,375 lines to a
470-line review guide with 8 linked detail files. Reviewers who want depth can
follow the links; those who want the summary can read the main document in 15
minutes.

**Reviewer persona analysis:** In Session 2, the agent mined 37 commits of git
history to build profiles of 7 likely reviewers — their concerns, their
commit patterns, their known positions. This led to targeted revisions:
connecting the schema design to specific USD internals for one reviewer,
emphasizing round-trip fidelity for another, naming specific PLM vendors for
a third, and elevating the scope promotion simulation for reviewers from the
digital twin community. This was the agent's idea, executed autonomously, and
the human approved every resulting edit.

## 6. Infrastructure Failures

**Subagent crash (20:15 UTC):** The human approved using a sub-process to
parallelize the document restructure. The subprocess was killed with SIGKILL
15 minutes later — orphaned output during a context compaction crashed the
gateway. From this point forward, all work was done in the main session.

**LLM idle timeouts (Session 2, 23:37–23:59 UTC):** Six consecutive prompt
errors in 22 minutes. The agent was re-reading files after each timeout,
consuming its context budget on reads instead of writes, and timing out before
producing output. The human's intervention — "make a strategy for writing
the analysis" — broke the cycle by giving the agent a small, concrete first
task (write TASK.md) instead of a large, context-heavy one (write the analysis).

**Context compaction during writes (Session 2, this document):** Even with
TASK.md, writing this retrospective failed three times — the document was
too large to write in a single output. The fix: chunk the write into 3–4
phases, committing after each one. The file on disk becomes the checkpoint.

**Pre-compaction memory flushes:** The system periodically triggers a memory
flush before compaction, asking the agent to save important context to files.
These flushes competed with in-progress work — the agent would stop mid-task
to write memory files, then lose its place in the original task after
compaction. In Session 2, the `TASK.md` pattern made flushes harmless: the
task state was already on disk.

## 7. Patterns That Worked

**Durable work plans (`TASK.md` / `COMPARISON_PLAN.md`):** Writing the full
strategy to disk before starting work was the single most impactful process
change. It survived compactions, provided a checklist for progress tracking,
and gave the agent a concrete "what to do next" after every context loss.

**One commit per phase:** Atomic commits after each logical unit of work meant
that progress was never lost. Even when the agent's context was wiped, `git log`
showed exactly what had been done.

**Fact-checking against primary sources:** After the MaterialX incident, every
external claim was verified. The agent read the actual IFC specification, the
actual bSDD API documentation, the actual `UsdSemanticsLabelsAPI` source code
(1,146 lines across 16 files). This caught 4 additional errors that would have
undermined the document's credibility.

**Reviewer persona analysis from git history:** Mining commit messages and
review comments to understand what each TAC member cares about allowed targeted
revisions. This is tedious work that humans rarely do — the agent did it in
one pass and the human approved the resulting edits.

**Amended commit messages:** One early commit message contained internal process
details (agent strategy notes). The human caught it: commit messages on a
public-facing branch should describe *what changed*, not the agent's internal
thought process. The commit was amended before push.

**Honest tradeoff acknowledgment:** Rather than papering over weaknesses in the
recommended approach, the document names them explicitly — the centralization
risk of a registry, the additional complexity of a hybrid schema, the real
limitations of dictionary-based overflow. A TAC member who reads the tradeoffs
section should think "they thought about this" rather than "they're selling me
something."

## 8. Anti-Patterns

**Re-reading files already in context:** The agent re-read the same source files
3+ times across compaction boundaries, consuming context budget on input rather
than output. After the `TASK.md` pivot, the rule became: capture all needed data
in the plan file, then never re-read the originals.

**"I'll keep going" without committing:** Early in Session 1, the agent would
write multiple files before committing. If compaction hit mid-batch, uncommitted
work was lost. The one-commit-per-phase rule eliminated this.

**"Always" claims about external specifications:** Statements like "IFC
GlobalId is always instance-level" and "glTF and MaterialX share similar
identifier models" were confidently stated and factually wrong. The pattern:
the more absolute the claim about an external standard, the more likely it is
hallucinated. Hedging language ("in typical usage", "as of version X") forces
the agent to think about whether it actually knows.

**Filler language:** Early drafts contained phrases like "significantly
enhances", "dramatically reduces", and "robust framework." These are
credibility-destroying in a technical document for expert reviewers. The
human's standard: if you can't put a number on it, don't use an intensifier.

**Papering over tradeoffs:** The first draft of the governance section
presented the registry as purely beneficial. The human pushed for naming the
centralization risk explicitly. The final version names the tradeoff honestly
and cites established precedents to show it is a well-understood pattern.

## 9. Human-Agent Division of Labor

What emerged was not "human directs, agent executes" but something more
nuanced:

**The human provided:**
- Social context: who the reviewers are, what they care about, what their
  technical priorities are
- Quality gates: catching hallucinations, rejecting filler language, demanding
  honest tradeoff analysis
- Process discipline: the `TASK.md` pattern, checkpointing strategy, context
  budgeting
- External connections: relaying core team feedback, pointing to upstream
  readability PRs, naming the "overflow is not customData" distinction
- Strategic judgment: when to stop researching and start writing, what level of
  detail is appropriate for the audience

**The agent provided:**
- Volume: 37 commits, 8 detail files, 3 schema implementations, examples
  across 4 verticals, all in ~26 hours
- Cross-referencing: finding connections between USD composition semantics and
  identifier lifecycle that would take a human hours of code-reading
- Tireless execution: overnight autonomous work, fact-checking every external
  claim against primary sources, propagating a design change across dozens of
  files in minutes
- Consistent formatting: maintaining document structure, cross-references, and
  terminology across thousands of lines

**The critical handoff:** The human catches errors the agent cannot see —
fabricated identifiers, audience missteps, process failures. The agent catches
errors that are tedious for humans — inconsistent terminology, stale
cross-references, unchecked factual claims that can be verified against
primary sources.

Neither could have produced this document alone in the same timeframe. The
human without the agent would have written a shorter, less thoroughly
researched document. The agent without the human would have produced a longer,
more confidently wrong one.

## 10. Recommendations

For anyone attempting similar agentic development work:

1. **Write the plan to disk before starting.** The agent's context window is
   not reliable storage. Files on disk are. Every multi-step task should begin
   with a plan file that tracks progress.

2. **Commit after every logical unit.** Uncommitted work does not survive
   context loss. Treat `git commit` as a save point.

3. **Verify all external claims.** LLMs hallucinate most confidently about
   things they know least about. URI schemes, governance structures, and
   identifier formats for domain-specific standards are especially unreliable.
   Budget time for verification against primary sources.

4. **Name your audience.** The reviewer persona analysis changed how every
   section was written. "Write a comparison document" produces generic output.
   "Write for the reviewer who will check `UsdPrimDefinition` integration"
   produces targeted output.

5. **Expect infrastructure failures.** Context compaction, idle timeouts,
   subprocess crashes, and memory flushes are not edge cases — they are the
   normal operating environment. Design the workflow to tolerate them.

6. **The human's most valuable contribution is judgment, not direction.** The
   five words "Khronos does not govern MaterialX" were worth more than any
   amount of detailed instruction. The human's job is to spot what the agent
   cannot: social context, audience awareness, and confident nonsense.

---

*This document was itself written using the patterns it describes: a `TASK.md`
outline with all data points captured up front, chunked into 3 phases with a
commit after each, after three failed attempts to write it in a single pass.*
