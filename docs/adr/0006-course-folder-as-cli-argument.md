# Course folder as the first command argument

**Status:** accepted. This decision supersedes [ADR 0003](./SUPPRESSED/0003-active-exam-resolution.md).

## Context

[ADR 0001](./0001-course-exam-hierarchy.md) defines one Course folder as the state boundary for one exam type. The CLI therefore needs the Course folder for every operation.

Before this decision, commands tried to find an active Exam folder under the repository's `Courses/` directory. That design could not use a folder elsewhere on disk. It also made the destination depend on other folders in the repository instead of the command the user typed.

## Decision

Every command takes `COURSE_FOLDER` as its first positional argument:

```text
python pipeline/pipeline.py COURSE_FOLDER COMMAND [arguments]
```

`COURSE_FOLDER` can be any path. The CLI creates the folder when needed. The folder contains past papers for exactly one exam type and owns that type's `taxonomy.json`, candidate records, parsed records, and ranked outputs. Every command reads and writes state only within the named Course folder.

A different exam type requires a separate Course folder. The pipeline does not detect an active folder, merge Course folders, or remember a previous selection.

`add-exam` accepts files, folders, or no input path. With no input path, it reads supported papers from the Course folder and its `exams/` subfolder.

## Consequences

The command always shows which Course owns the operation. The MVP needs no active-exam selection rule or nested exam-type hierarchy. `Courses/` remains an optional convention for organizing folders, not a location the CLI requires.

Separate Course folders isolate different exam types. Each folder can contain multiple past papers of its one exam type.

## Considered options

- Auto-detecting one Course folder was rejected because the destination changed when another folder appeared and because folders outside the repository were unavailable.
- An optional `--folder` flag was rejected because the Course folder is required for every command.
- A persistent active-folder file was rejected because it could become stale and send work to the wrong Course.
