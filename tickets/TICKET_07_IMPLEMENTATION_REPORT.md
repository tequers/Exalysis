# Ticket 07 implementation report

Implemented course persistence in `pipeline/exam_roi/storage.py` and connected
the existing CLI workflows to explicit storage sessions. No ticket status or
blocker fields were edited by the implementation agent.

## Acceptance criteria

| Criterion | Implementation and evidence |
| --- | --- |
| Serialize course writers | A persistent OS lock covers each complete command. Contention names the course, process ID, host, and acquisition time, with retry instructions. Tests use two real processes and independent course folders. |
| Atomic related updates | `CourseStore.commit(taxonomy=..., papers=..., candidates=...)` uses flushed temporary files, atomic replacement, and a journal containing checked before-images and after-images. The committed journal is the commit point. |
| Detect damaged or incompatible records | Strict JSON parsing, format/version checks, filename-ID checks, and existing evaluation-evidence validation raise `RecordError` with the path. Existing records are checked before force, skip, or commit. Damaged records and journals stay untouched. |
| Recover interrupted work and stale locks | Prepared transactions roll back; committed transactions keep the new state. Recovery can itself be interrupted and repeated. Kernel locks are released on process death. Stale metadata does not authorize lock deletion. |
| Distinguish export and state failures | State failures return exit 5. Export failures retain exit 4 and cannot change accepted state. `edit-topic` confirms changes only after its commit succeeds. |
| Test boundaries and recovery | Tests terminate child processes at 11 commit boundaries and six recovery boundaries. They also cover competing writers, corrupt records/journals, bad checksums, forced reprocessing, CLI commit I/O failures, and successful subsequent commits. |

All criteria are met for the documented local-filesystem, process-interruption
contract. The Windows branch was exercised on this host. POSIX locking and
directory flushing were implemented but not executed here. Machine power loss
still depends on filesystem and hardware guarantees. Network and cloud-sync
folders with unknown locking semantics are outside the supported contract.
See the [course state recovery guide](../docs/guides/course-state-recovery.md) for the protocol and recovery procedure. Historical commands below retain their paths at the time of implementation.

## Verification commands and results

All commands ran from the repository root. The bundled interpreter is
`C:/Users/alber/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe`.

1. `python -m unittest discover -s pipeline/tests -v`
   Exit 1. Ran 178 tests in 5.446s. One failure, 52 errors, three skips.
   System Python lacked `openpyxl` and used CP1252 for the existing Unicode CLI
   output. This was the first attempted run.
2. `rg --files -g 'python.exe' -g '*venv*' -g '!graft/**' -g '!Exams/**'; $env:PYTHONUTF8 = '1'; python -m unittest discover -s pipeline/tests -p 'test_exam_identity.py' -v`
   Exit 1. Ran 18 tests in 0.687s, four errors. Three involved deliberately
   incomplete identity-test records, which were updated to include valid IDs and
   `per_topic`. Windows prevented the fourth test from renaming a folder with an
   open lock file. The test now accepts that earlier containment protection.
3. `$env:PYTHONUTF8 = '1'; & 'C:/Users/alber/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' -m unittest discover -s pipeline/tests -q`
   First invocation: exit 0, 178 tests in 24.969s, OK.
   Second invocation, after stronger format validation and the first storage
   tests: exit 1, 189 tests in 19.111s, one failure and ten errors. The new check
   incorrectly treated `automatic_summary` as an object. It is a boolean; fixed.
4. `$env:PYTHONUTF8 = '1'; & 'C:/Users/alber/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' -m unittest discover -s pipeline/tests -p 'test_storage.py' -v`
   First invocation: exit 0, 11 tests in 3.828s, OK.
   Second invocation: exit 0, 11 tests in 4.588s, OK.
   Final focused invocation: exit 0, 13 tests in 4.692s, OK.
5. `$env:PYTHONUTF8 = '1'; & 'C:/Users/alber/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' -m unittest discover -s pipeline/tests -p 'test_report_rendering.py' -q`
   Exit 0, 19 tests in 1.920s, OK.
6. `$env:PYTHONUTF8 = '1'; & 'C:/Users/alber/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' -m unittest discover -s pipeline/tests -q -b`
   Final full invocation: exit 0, 191 tests in 23.538s, OK. No failures or skips.
7. `git diff --check; git status --short`
   Exit 0. No whitespace errors. Git reported existing CRLF conversion and
   inaccessible global-ignore warnings. Existing unrelated changes remained.
8. `git diff --check -- pipeline/pipeline.py pipeline/tests/test_candidate_validation.py pipeline/tests/test_exam_identity.py; rg -n '^class CourseStore|^class RecordError|^    def (load|commit|_recover|__enter__)|EXIT_STATE_FAILURE|^def (process_exam_file|cmd_add_exam|cmd_rebuild|cmd_edit_topic)|^#' pipeline/exam_roi/storage.py docs/course-state-recovery.md pipeline/pipeline.py`
   Exit 0. No whitespace errors; line lookup succeeded.

## Inspection commands

These were read-only. Each command below exited 0 unless its result is stated
otherwise. The final status of combined PowerShell statements is reported,
including nonterminating read errors where relevant.

```powershell
Get-Content -Raw '.agents/skills/graft/SKILL.md'
Get-Content -Raw 'C:/Users/alber/.codex/skills/unslop/SKILL.md'
Get-Content -Raw '.scratch/reliable-exam-analysis/issues/TO_REVIEW/07-make-course-state-updates-recoverable-and-serialize-writers.md'
Get-Content -Raw 'AGENTS.md'; git status --short
Get-Content -Raw 'docs/adr/0008-modular-pipeline-architecture.md'
rg --files -g 'AGENTS.md' -g '*toml' -g 'requirements*' -g 'pytest.ini'
Get-Content -Raw 'pipeline/exam_roi/storage.py'; Get-Content -Raw 'pipeline/requirements.txt'
$lines = Get-Content 'pipeline/pipeline.py'; $lines[80..270]; $lines[360..380]; $lines[820..1040]; $lines[1090..1220]; $lines[1300..1390]
$lines = Get-Content 'pipeline/tests/test_exam_identity.py'; $lines[75..240]; $lines = Get-Content 'pipeline/tests/test_candidate_validation.py'; $lines[158..208]; $lines = Get-Content 'pipeline/tests/test_independent_review.py'; $lines[177..211]; $lines = Get-Content 'pipeline/tests/test_evaluation.py'; $lines[186..230]; $lines = Get-Content 'pipeline/tests/test_cli_outcomes.py'; $lines[0..205]
git diff --stat -- pipeline/pipeline.py pipeline/exam_roi/storage.py; $lines=Get-Content 'pipeline/tests/test_cli_outcomes.py'; $lines[235..335]
rg -n 'import math|finite_float|format_distribution|interrupted transaction|type\(journal' 'pipeline/exam_roi/storage.py'
Get-Content -Raw 'pipeline/exam_roi/storage.py'; $lines = Get-Content 'pipeline/pipeline.py'; $lines[1125..1255]
$lines=Get-Content 'pipeline/exam_roi/taxonomy.py'; $lines[102..128]; $lines=Get-Content 'pipeline/exam_roi/evaluation.py'; $lines[282..369]
$lines=Get-Content 'pipeline/tests/test_report_rendering.py'; $lines[50..145]; $lines=Get-Content 'pipeline/exam_roi/evaluation.py'; $lines[246..282]
```

The following inspection commands had missing-command or missing-file results:

```powershell
graft ask "where are course records papers and taxonomy loaded saved and exported" --source
```

Exit 1. The graft CLI was not installed on PATH. The available graft MCP tools
were then used successfully for all graph queries.

```powershell
$lines = Get-Content 'pipeline/pipeline.py'; $lines[1040..1090]; Get-Command python | Select-Object Source; rg --files 'docs' -g '*storage*' -g '*recovery*'
```

Exit 1. Source and Python-path reads succeeded; the final file search had no
matches because the recovery guide did not yet exist.

```powershell
Get-Content -Raw 'docs/evaluation-contract.md'; $lines=Get-Content 'pipeline/exam_roi/evaluation.py'; $lines[500..526]; $lines=Get-Content 'pipeline/tests/test_exam_identity.py'; $lines[238..290]; rg --files 'pipeline/tests'
```

Exit 0 overall. The first file did not exist and produced a nonterminating
PowerShell error. The named source-range reads and test inventory succeeded.

```powershell
Get-Content -Raw 'docs/adr/0006-course-folder-as-cli-argument.md'; rg -n 'exit code|Exit code|rebuild|taxonomy.json' 'HOW_TO_USE_PIPELINE_WITH_GLM_API.md'
```

Exit 1. The ADR read succeeded; the final text search returned no matches.

Graft MCP queries covered persistence locations, callers of `load_taxonomy`, the
pipeline API, persistence-related tests, saved versions, scoring inputs, and
`automatic_summary`. All succeeded. Together they reported approximately 114,922
tokens saved, about $0.19. The bundled-runtime lookup also succeeded. File edits
used `apply_patch`. One patch failed context verification before making changes;
the corrected patch succeeded.
