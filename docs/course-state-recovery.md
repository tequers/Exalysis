# Course state and interruption recovery

The storage module owns `taxonomy.json`, accepted paper records in `parsed/`,
and candidate records in `candidates/`. The existing folder layout and paper IDs
stay the same. It does not decide whether a candidate is eligible for acceptance.
The current `add-exam` command still saves candidates only.

## Read and commit interface

Pass an explicit `CoursePaths` to `CourseStore` and hold its session around the
whole read, modify, and commit operation. The folder must already exist.

```python
from exam_roi.storage import CoursePaths, CourseStore

with CourseStore(CoursePaths(course_folder)) as store:
    snapshot = store.load()
    # Acceptance policy supplies the chosen paper and its resulting taxonomy.
    store.commit(papers={paper_id: accepted_paper}, taxonomy=updated_taxonomy)
```

`load()` returns taxonomy, papers, and candidates from one consistent state.
`commit()` replaces only the records supplied to it. It accepts taxonomy, paper,
and candidate updates together, so a paper and its taxonomy changes can use one
commit. Existing records omitted from the call remain unchanged. `load_record()`
supports identity checks within the same session. All three methods require an
open session. After a failed commit, close and reopen it before further reads or
writes. There is no deletion or candidate-promotion policy in this interface.

## One command per course

Each mutating command holds an operating-system lock for its entire operation,
including model requests and export. `status` locks while loading its snapshot.
Commands for different course folders can run together. Input-selection dry runs
do not acquire a storage lock or recover state.

The persistent `.course.lock` file contains a locked byte and diagnostic metadata
with the process ID, host, and acquisition time. A second command fails promptly
with that information and instructions to wait or stop the first command. Windows
uses a nonblocking byte-range lock; POSIX systems use `flock`.

The operating system releases the lock when the process exits, including when it
is killed. Metadata left behind is harmless. A new command must acquire the kernel
lock before replacing the metadata or recovering state. It never guesses that a
lock is stale from its age, host name, or process ID. Do not delete `.course.lock`:
on systems that allow deleting an open file, a replacement file could let two
writers lock different files under the same name.

## Commit protocol

This protocol requires a local filesystem with working operating-system locks
and atomic same-directory replacement. It is not supported on cloud-sync folders
or network filesystems whose locking and replacement semantics are unknown.

1. Under the course lock, validate every existing saved record and all proposed
   records. Reject malformed JSON, duplicate keys, non-finite numbers, incompatible
   versions, invalid record shapes, mismatched paper IDs, and redirected paths.
2. Write a version 1 journal to a temporary file, flush it with `fsync`, and
   atomically replace `.course-transaction.json`. Its phase is `prepared`. It holds
   the exact previous bytes and new bytes for every target, with SHA-256 checksums.
   A missing previous file has a null before-image. No target changes before this
   journal is in place.
3. For each target, write a temporary file in its own directory, flush it with
   `fsync`, and atomically replace the target with `os.replace`.
4. Flush and atomically replace the journal with phase `committed`. This is the
   commit point. Before it, the saved before-images are the last committed state.
   After it, the after-images are the committed state.
5. Remove the journal. A crash during cleanup does not undo a completed commit.

On POSIX systems the module also flushes the containing directory after each
replacement or deletion. Python does not expose the same directory flush on
Windows. The tests prove recovery from process interruption. Guarantees against
machine power loss still depend on the filesystem and hardware honoring flushes
and atomic replacement.

Raw files can briefly contain a mixture during step 3. Every pipeline reader
acquires the same lock and completes recovery before returning a snapshot, so it
cannot observe that mixture. Other tools must not edit or consume the raw state
while a command is active. Manual taxonomy edits remain supported between
commands, when no recovery journal is present.

## What happens after interruption

The next storage session validates the journal, its checksums, and all its targets
before changing anything. A `prepared` journal restores every before-image,
including deleting records that did not previously exist. A `committed` journal
keeps or restores every after-image. Recovery is repeatable if it is interrupted
again. It removes the journal only after all target files match the chosen state.

An operation interrupted after the commit marker can have committed even if its
caller did not receive success. Run `status` to recover and inspect the saved
state before deciding whether to reprocess. `rebuild` regenerates exports from
that state. Temporary `.course-write-*.tmp` files left by a killed process are
never treated as records or recovery instructions. They may be removed after all
commands using that course have stopped. Do not remove the transaction journal.

If a target differs from both journal images, or a record or journal is corrupt,
recovery stops and names the path. It does not guess which content to trust or
overwrite the damaged file. Keep the course folder intact, make a backup, then
restore the named file from a known-good backup or repair it explicitly. Run
`status` again. `--force` does not bypass these checks.

## Legacy accepted records

Unversioned historical records remain readable if their structure is valid.
An optional `storage_schema_version` must be integer `1`. Evaluation versions
`1.0.0`, `1.1.0`, `1.2.0`, and `legacy-unversioned` remain recognized.

Older accepted records may lack the topic judgments or dependency evidence that the
current evaluation contract requires. Aggregation excludes judgments from prior
contracts and identifies excluded records and conflicts in the report review notes.
`rebuild` recalculates reports from compatible accepted evidence. It does not migrate
or reinterpret older judgments.

`add-exam --force` can reprocess the source and save a current candidate. It does not
replace the record in `parsed/`. The current CLI cannot promote that candidate into
accepted state.

## State failures and exports

Course-state failures return CLI exit code `5`, with the lock or record identity
and recovery instructions. Export failures keep exit code `4`. Exports run after
the state commit and cannot change accepted papers or taxonomy. If XLSX or JSON
export fails, close any application locking the output, address the reported
filesystem error, and run `rebuild`. The two export files are derived outputs;
they are not part of the state transaction and one may be older than the other
until a rebuild succeeds.

## Verification

`pipeline/tests/test_storage.py` kills real child processes at all eleven commit
boundaries: before and after replacing the prepared journal, each of three target
files, and the committed journal, then after cleanup. Each case asserts an exact
old state or a complete new state, and successfully commits again after recovery.
It also interrupts six recovery boundaries, runs competing processes, checks
stale metadata, rejects corrupt records and journals, and distinguishes state
failures from export failures. Existing identity tests still check redirected
directories, file links, and destination changes during analysis.
