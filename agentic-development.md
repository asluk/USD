# Agentic Development in aarUSD

This document captures how to work effectively with an AI coding agent on the
aarUSD codebase, based on practical experience adding Python validator
registration to the `usdValidation` framework.  The second half describes how
this workflow could evolve into a remote, asynchronous model where the
contributor checks in periodically rather than staying at the keyboard.

---

## What We Built

Over two sessions, an AI agent and a contributor implemented the ability to
register `usdValidation` validators written in Python:

- `wrapRegistry.cpp` — three GIL-safe wrapper functions
  (`_WrapLayerTaskFn`, `_WrapStageTaskFn`, `_WrapPrimTaskFn`) plus four
  `RegisterXxxValidator` Python methods on `ValidationRegistry`
- `testUsdValidationRegistryPyRegister.py` — six tests covering all three
  task types, validator suites, context-driven validation, and empty-return
  handling
- README documentation aimed at Python developers new to the framework
- A proof-of-concept validator (`testUsdGeomValidatorsPyLayerStack.py`) that
  walks `GetUsedLayers()` to catch `metersPerUnit`/`upAxis` disagreements
  across the full composition graph

---

## Session Learnings

### 1  Read before writing

The agent's first action on each new file was to read nearby examples.  For
the bindings, it read `wrapValidator.cpp` before touching `wrapRegistry.cpp`.
For the test, it read `testUsdValidationRegistryPyRegister.py` (an existing
Python test) and `testUsdGeomValidators.cpp` (the C++ counterpart) before
writing a single line.

**Pattern:** always read at least one adjacent file of the same kind before
writing.  The agent should also read `CONTRIBUTING.md` and the relevant
`README.md` at the start of any task that involves new files.

### 2  Let the compiler and test runner guide you

The agent ran `cmake --install` and `ctest` early and often.  The first full
run surfaced 590 stale-DLL failures that had nothing to do with the new code —
but finding them early prevented false confidence.  The new usdValidation tests
all passed immediately; that was the meaningful signal.

**Pattern:** run tests after each logical chunk of work, not only at the end.
A green test suite for adjacent tests is a prerequisite before declaring a
feature complete.

### 3  Coding conventions belong in memory, not in every prompt

Over the course of the session, the contributor corrected the agent on several
points:

- Use `Tf` (not `TF`) when referring to the library in prose
- No em-dashes in comments; use semicolons instead
- Prefer token constants (`UsdGeom.Tokens.upAxis`) over raw strings
- Inline single-use error strings; do not promote them to named constants

Each correction was saved to a persistent memory file
(`memory/feedback_style.md`).  In future sessions, the agent loads that file
at the start and does not repeat the same mistakes.

**Pattern:** every style or convention correction should be written to memory
immediately, with a "why" and a "how to apply" note so the agent can judge
edge cases rather than applying the rule blindly.

### 4  Humans catch design-level issues agents miss

The most important design decision in the session was not made by the agent.
The initial validator used `GetLayerStack()`, which covers only direct
sublayers of the root stage.  The contributor pointed out that the real risk
is a newly *referenced* or *payloaded* asset with mismatched metadata — and
that requires `GetUsedLayers()`.  The agent validated this empirically on the
Kitchen_set (230 used layers, 1 local stack layer) and confirmed the fix.

**Pattern:** agents are good at implementing what is asked; humans are better
at asking the right question.  Design reviews should be a checkpoint, not an
afterthought.

### 5  Branch discipline maps to PR discipline

Because experimental work (the geometry validator) went on a `poc/` branch
rather than the feature branch, the PR for the core registration feature stays
clean and reviewable.  The POC branch demonstrates the capability without
coupling it to the reviewed API change.

**Pattern:**
- `feature/<name>` — PR-ready implementation
- `poc/<name>` — proof of concept, branches from the feature branch if it
  depends on it, otherwise from `dev`
- Commit messages written for a human reviewer, not for the agent's own
  reference

### 6  Test the work on real data before calling it done

Running the validator on Kitchen_set took five minutes and taught more than
another hour of unit-test design would have.  The clean result (no conflicts)
was informative; the structural insight (one local layer, 229 referenced
layers) directly motivated the `GetUsedLayers()` change.

**Pattern:** for any validator, schema change, or tool, run it against a
non-trivial real asset before submitting the PR.

---

## Toward a Remote, Asynchronous Workflow

The session above was synchronous: the contributor sat at the keyboard and
reviewed each step.  A more scalable model lets the agent work autonomously
for blocks of time while the contributor checks in remotely — from a phone, a
different timezone, or between meetings.

### Core idea

The agent publishes a live status document and pauses at defined checkpoints.
The contributor reads the status document, leaves guidance in a simple reply
file, and the agent resumes.  No real-time presence is required.

### Artifacts

| Artifact | Location | Purpose |
|---|---|---|
| `TASK.md` | repo root (gitignored) | The task the agent is executing; written by the contributor |
| `STATUS.md` | repo root (gitignored) | Continuously updated by the agent; the contributor reads this to catch up |
| `GUIDANCE.md` | repo root (gitignored) | The contributor writes guidance here when checking in; agent reads and clears it |
| `memory/` | `~/.claude/projects/.../memory/` | Persistent facts that survive across sessions |
| feature branch | `feature/<name>` | All work stays on a branch; `dev` is never touched directly |

### Task file format

```markdown
## Task
Add Python validator registration to UsdValidation.

## Scope
- wrapRegistry.cpp bindings
- Python tests
- README documentation
- No changes to C++ validator interfaces

## Checkpoints (pause here and update STATUS.md)
1. After reading existing code, before writing anything: summarise the
   approach and flag any concerns.
2. After first passing test run.
3. Before any PR-related git operations.

## Autonomous decisions (no pause needed)
- Coding style choices within existing conventions
- Test case additions
- Comment wording

## Escalate if
- The approach requires changing a public API
- Tests fail in a way that suggests a design problem, not a bug
- A file you expected to exist does not
```

### Status file format

The agent rewrites `STATUS.md` after each meaningful action:

```markdown
## Status  2026-03-13 14:32

**Phase:** implementation
**Branch:** feature/usdvalidation-py
**Last commit:** "Add _WrapLayerTaskFn and _WrapStageTaskFn"
**Tests:** 9/9 usdValidation tests passing

### What I did
Read wrapValidator.cpp, wrapContext.cpp, and the Python test for
ValidationContext.  Implemented the three wrapper functions and the four
Register* shims.  Tests pass.

### What I am doing next
Writing the README documentation section for Python developers.

### Checkpoint needed?
No — documentation is within autonomous scope.

### Open questions (non-blocking)
- Should the README example use a real UsdGeom schema check or a trivial
  placeholder?  I will use a real check (upAxis) for now; easy to simplify.
```

### Guidance file format

The contributor writes a short reply — a sentence or a few bullets is enough:

```markdown
Use a real upAxis check.  Also add a note that Python validators are
explicit-registration only, not plugin-discoverable.  No other changes needed.
```

The agent reads, acts, clears the file, and updates STATUS.md.

### Checkpoint categories

| Category | What happens |
|---|---|
| **Design gate** | Agent pauses, writes full design summary in STATUS.md, waits for explicit approval before writing code |
| **Build/test failure** | Agent pauses immediately, writes failure details and attempted fixes to STATUS.md |
| **API surface change** | Always escalate; never change a public C++ interface autonomously |
| **Git operations** | Agent may commit and push branches; never touches `dev` or `main`; confirms before creating a PR |
| **New file creation** | Agent may create test files and documentation autonomously; escalates for new public headers |

### What the contributor does at check-in

1. `cat STATUS.md` — 30 seconds to understand where things stand
2. `git log --oneline feature/<name>` — verify commits are sensible
3. `cat GUIDANCE.md` — see if there is anything already waiting (usually empty)
4. Write a brief reply to `GUIDANCE.md` if direction is needed, or nothing if the agent should continue
5. The agent picks up the guidance on its next cycle

Total check-in time is typically under five minutes for a well-structured
task.

### What changes compared with synchronous work

| Synchronous (this session) | Asynchronous |
|---|---|
| Human reviews every file before commit | Human reviews STATUS.md summary; reads diffs at checkpoints |
| Corrections applied immediately in chat | Corrections written to GUIDANCE.md; persistent corrections go to memory |
| Human caught GetLayerStack vs GetUsedLayers in real time | Agent would have reached a design checkpoint before writing the validator; design review happens there |
| Single continuous session | Work proceeds across hours or days; agent resumes from memory + STATUS.md |
| Human manages git manually | Agent manages the feature branch; human reviews at PR time |

### Risks and mitigations

**Risk: agent proceeds past a bad design decision while contributor is away.**
Mitigation: design gates are checkpoints, not suggestions.  The task file
should be explicit about what triggers an escalation.

**Risk: status document drifts from reality.**
Mitigation: the agent rewrites STATUS.md from scratch after every commit, not
appends to it.  Stale information does not accumulate.

**Risk: context window compression loses important details.**
Mitigation: atomic commits with descriptive messages.  The agent can always
reconstruct state from `git log`, the code itself, and the memory files.

**Risk: the contributor cannot interrupt a bad action once it starts.**
Mitigation: long-running or irreversible operations (full rebuilds, PR
creation, force-push) are always checkpoints, never autonomous.

---

## Quick Reference for New Contributors

```
# Start an agentic task
# 1. Write TASK.md with scope, checkpoints, and escalation criteria
# 2. The agent reads existing code, writes STATUS.md summary, and pauses (checkpoint 1)
# 3. Review STATUS.md and write guidance to GUIDANCE.md if needed
# 4. Agent implements; check in by reading STATUS.md and git log
# 5. At the PR checkpoint, review diffs; agent creates the PR on approval

# Coding conventions enforced by memory (agent loads these automatically)
# - Tf, not TF, in prose
# - No em-dashes; use semicolons
# - Token constants over raw strings (UsdGeom.Tokens.upAxis, not "upAxis")
# - Inline single-use error strings; no named constants for them
# - Copyright year = current year in new files; leave existing years alone
# - 80-char line limit, K&R braces, PXR_NAMESPACE_USING_DIRECTIVE

# Branch naming
# feature/<name>   PR-ready work
# poc/<name>       proof of concept; branches from the feature branch it depends on
# fix/<name>       isolated bug fix
```
