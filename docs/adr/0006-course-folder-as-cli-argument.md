# COURSE_FOLDER as the first argument of every command

**Status:** accepted — supersedes [ADR 0003](./0003-active-exam-resolution.md)

[ADR 0003](./0003-active-exam-resolution.md) had commands auto-detect the active Exam folder under the repo's own `Courses/` directory, and fall back to `--course`/`--exam` flags once a second one existed. Two problems surfaced as soon as the pipeline was pointed at a second body of exams (`EXAMS_EVAU/Historia`, a folder of past papers sitting outside `Courses/`):

- **The working folder was not expressible.** The pipeline could only ever act on `Courses/<Course>/<Exam>/` inside the repo. A folder of papers anywhere else on disk — the normal case for someone using the tool on their own material — had no way to be named at all.
- **Where the work landed was invisible at the call site.** `python pipeline.py add exam.pdf` names an input and never names a destination; whether it was right depended on how many folders happened to exist under `Courses/`, and the disambiguating flags trailed at the end of the line, where they are easiest to forget.

We decided that **every command takes the course folder as its first positional argument** — `python pipeline.py COURSE_FOLDER COMMAND [data]` — and that this folder is the pipeline's entire state boundary: `taxonomy.json`, `parsed/`, and the two ranked outputs live in it and nowhere else. It may be any path on disk. It is created if it does not exist, so a first run on an empty or absent folder writes the files and every later run updates those same files in place. Nothing is auto-detected and nothing is remembered between runs: the destination is read straight off the command the user typed.

The same move collapsed `add` and `add-folder` into one `add-exam` command that accepts files, folders, or nothing at all (in which case it reads the course folder itself, then its `exams/` subfolder). Two commands that differed only in whether their argument had a file extension were a distinction the user had to make on the tool's behalf.

We rejected keeping auto-detection as a convenience for the single-folder case: it is precisely the case where typing the folder is cheapest, and the rule "sometimes the folder is implied" is what made the multi-folder case surprising. We rejected a flag (`--folder`) because an option reads as optional, and this argument never is. We rejected a pointer file recording the active folder for the reason ADR 0003 already gave for rejecting it: it is one more piece of state to keep in sync and forget to update.

The consequence for [ADR 0001](./0001-course-exam-hierarchy.md) is that `Courses/<Course>/<Exam>/` becomes a convention for arranging folders, not a structure the CLI knows anything about. The decision that ADR records — one Exam's state is atomic and never merged with another's — is unchanged and is now enforced by the folder argument itself: two exams are two folders, and the pipeline can only ever be looking at one of them.
