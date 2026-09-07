---
name: maestro-prompt-designer
description: >-
  Turn an idea or requirements conversation into an approved, persistent task
  specification for Maestro. Use before routing when scope, current phase,
  constraints or acceptance criteria need clarification; works with grilling
  in the same conversation. Does not select skills or implement the task.
---

# Maestro Prompt Designer

Prepare the complete user's objective for Maestro. Use the user's language.
Capture decisions rather than optimizing a prompt for keyword matching.

## Work with the conversation

Read relevant earlier decisions before asking anything. When `grilling` is active,
it owns the interview: ask one selection-changing question at a time, recommend an
answer and wait. Consolidate each answer instead of starting a second interview.
If grilling is unavailable, conduct that same focused interview yourself.
Resolve facts from targeted project inspection; leave product decisions to the user.
Do not read credentials or unrelated projects to establish context.

Distinguish confirmed decisions, verified facts (with file references), preferences,
assumptions, rejected alternatives and unresolved questions. Never silently turn an
assumption into approval. Reuse answers and authorizations already given. Revisit
them only when a new fact makes them materially inconsistent or insufficient.

## Build the specification

Identify the requested outcome, present state, current development phase, required
capabilities, dependencies, constraints, deliverables and observable acceptance
criteria. Describe capabilities, not skill names, unless the user explicitly picks
a skill. Do not impose a technology or remove a user's choice without discussion.

For a full project, retain the entire outcome. Break work into phases with clear
inputs, deliverables, validation and completion status. Do not replace a full-project
request with only a foundation prompt. Mark decisions that can wait for a later
phase; ask now only when the answer affects the specification materially.

Use [references/task-spec-template.md](references/task-spec-template.md) as a
starting point, keeping only relevant sections. Scale detail to the task.

## Persist and approve

Save the draft at `<project>/.maestro/specs/<task-slug>.md`, or the user's chosen
location. Use a filesystem-safe, non-sensitive slug. Inspect an existing file before
updating it; preserve other tasks. Save only task-relevant decisions, never secrets,
raw conversation transcripts or private source dumps.

Treat this directory as local task data. When in a Git repository, exclude the spec
directory locally with `.git/info/exclude` unless the user explicitly requests it
tracked. For a linked worktree resolve the actual Git exclude path first. Do not
change shared ignore rules merely to store another project's private brief.
Task specs must never enter npm release archives.

Present the concrete draft and ask for final agreement only if it has not already
been given. Record `draft` or `approved` truthfully, the revision and which scope
was approved. After changes, only changed decisions need new confirmation.

If there is no project or writing is unavailable, give the specification in the
conversation and say it was not saved. Do not claim a file exists when it does not.

## Hand off in the same conversation

Give a short summary, the saved path and this invocation (as text, not a tool call):

```text
$maestro execute the approved specification at <path>.
Use the decisions and authorizations already recorded in this conversation.
Select skills using project evidence, show the graph, and continue through the
approved phases after graph approval until the complete objective is satisfied.
```

Do not require the user to paste the specification again. When they invoke Maestro,
the interview's prohibition on implementation ends for the approved execution
scope. Specification approval authorizes only the effects it actually records;
it is not blanket permission for installation, publication or unrelated changes.

Do not invoke Maestro, route skills, build its final graph, install other skills,
spawn agents or implement the product while acting as Prompt Designer. Once the
user explicitly transitions to execution, let Maestro own that phase.

Completion means a usable specification, truthful approval status, visible
remaining questions and a handoff that preserves the full objective.
