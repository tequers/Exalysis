# Active-exam resolution: auto-detect when unambiguous, require explicit selection otherwise

**Status:** suppressed. [ADR 0006](../0006-course-folder-as-cli-argument.md) replaced this decision. Every command now names its Course folder explicitly.

With `Courses/<Course>/<Exam>/` (see [ADR 0001](../0001-course-exam-hierarchy.md)) able to hold more than one Exam, both `pipeline.py` and the `/continue-study-session` skill need a rule for which Exam a given command or session applies to.

We decided commands **auto-detect the active Exam when exactly one exists anywhere under `Courses/`**, and **require an explicit `--course`/`--exam` (or equivalent) the moment a second Exam folder exists** — ambiguity is never silently guessed. This keeps today's single-exam (Computer Vision) usage exactly as simple as it is now, with zero new syntax, while guaranteeing that adding a second exam can't cause a command to silently act on the wrong one.

We rejected always-explicit (stable command shape, but adds required arguments to every invocation for a case — a single active exam — that is and will likely remain the common one) and a persistent "active exam" pointer file (works, but is one more piece of state to keep in sync and forget to update — `.study-run.json`'s already-stale `method` field, discovered during this same session, is a live example of exactly that failure mode).
