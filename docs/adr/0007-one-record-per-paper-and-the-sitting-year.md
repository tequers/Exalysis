# Require year-prefixed exam filenames for the MVP

**Status:** accepted

## Context

The MVP needs one predictable way to identify an exam and determine its year. Supporting several
filename conventions would add inference and ambiguity that the MVP does not need.

A course can have more than one exam in the same year. The year alone therefore cannot identify an
exam.

## Decision

Every exam filename must use this format before the file extension:

```text
YEAR_name_of_the_exam
```

`YEAR` is the four-digit year in which the exam took place. An underscore must follow the year.
The rest of the filename is a nonempty name for that exam.

For example, these names are valid:

```text
2025_networks
2025_INFO_ENERO
2025_info_febrero
```

This name is invalid because it does not start with the four-digit exam year:

```text
enero_26_info
```

The pipeline uses the full filename stem as the exam identifier. Exams may share the same year as
long as their full filename stems differ. For example, `2025_INFO_ENERO` and
`2025_info_febrero` are two different exams from 2025.

The pipeline reads the exam year from the required prefix. It does not infer the year from another
part of the filename, the containing folder, the document contents, or the current date.

## Consequences

- Users must rename source exams that do not follow `YEAR_name_of_the_exam` before processing them.
- The pipeline can identify several exams from the same year without numbering or merging them.
- Names after the first underscore may use any wording that the filesystem and the pipeline already
  support. The MVP does not impose a language, letter case, or naming vocabulary.
- Two files with the same complete filename stem represent the same exam identifier, even if they
  are stored in different folders or use different supported file extensions.
