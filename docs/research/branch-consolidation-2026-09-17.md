# Branch consolidation on 17 September 2026

This is the evidence for ticket 26. It records the decisions before branch deletion and will record the observed result afterward. Ticket 25 remains blocked until a person reviews this evidence and ticket 26 is complete.

The working branch is `codex/mvp-two-stage`, in `C:/Users/alber/Claude/Projects/0_Projects/Exams_Analysis_AI_pipeline-mvp-two-stage`. Its original creation entry is `codex/mvp-two-stage <- codex/developer-tooling @ 97d4451846eeb8e30f0f071776e7ed8894d1c104`. This cleanup starts at `a8b364ba66b0c6f7c9ec743e726511a7d51a687c`, including the prerequisite ticket-reference repair and ticket-26 start commits. Another implementation branch would not isolate work on the integration branch itself.

## Baseline and method

`git status --short --branch` showed a clean working tree and the expected upstream. `git fetch origin --prune` completed before this inventory. Both the local and origin MVP refs pointed to `a8b364b`.

The baseline has 19 local branches, 15 actual origin branches, six worktrees, and three stashes. `origin/HEAD` is a symbolic reference to `origin/main`, not a sixteenth origin branch. The older ticket estimate of five worktrees is superseded by this inventory.

The inventory uses these read-only commands:

```powershell
git for-each-ref --sort=refname --format='%(refname)|%(objectname)|%(upstream)|%(upstream:track)|%(worktreepath)' refs/heads refs/remotes/origin
git worktree list --porcelain
git rev-list --left-right --count a8b364ba66b0c6f7c9ec743e726511a7d51a687c...REF
git merge-base a8b364ba66b0c6f7c9ec743e726511a7d51a687c REF
git log --format='%H %s' a8b364ba66b0c6f7c9ec743e726511a7d51a687c..REF
git reflog show --format='%H %gs' REF
git stash list --format='%gd|%H|%gs'
```

For each worktree, `git -C PATH status --porcelain=v1 --untracked-files=normal` established whether local work remained. No other worktree was edited.

The GitHub CLI was not authenticated and an anonymous API read returned 404. A read through the existing Git credential helper returned HTTP 200 with `[]` from `GET /repos/tequers/exam-roi-pipeline/pulls?state=open&per_page=100`, without a pagination link. There were no open pull requests. The credential stayed in memory and was not written to this report or the repository. Repeat that query immediately before deletion.

## Before inventory

`Ahead/behind` counts commits relative to the fixed MVP baseline, not relative to an upstream. `Ancestor` means every commit at that ref is reachable from the MVP. For an ancestor, its tip is also its merge base with the MVP. Short commit IDs below map to full IDs in the commit key.

In the upstream column, `same origin name, 0/0` means the local branch tracks the identically named origin branch and both point to the listed tip. `None` means no configured upstream. Worktree IDs refer to the next table. Every local branch appears below, including backup branches.

| Local branch | Local tip | Origin tip of same name | Upstream state | Ahead/behind MVP | Ancestry | Worktree | Decision before deletion |
|---|---|---|---|---|---|---|---|
| `backup/mvp-two-stage-pre-help-20260917` | `28c5d34` | Absent | None | 0/8 | Ancestor | None | Retain existing recovery history. |
| `backup/mvp-two-stage-pre-unorouter-merge-20260917` | `6c99977` | Absent | None | 0/27 | Ancestor | None | Retain existing recovery history. |
| `backup/pre-split-3bc78bd` | `3bc78bd` | Absent | None | 18/46 | Unrelated roots | None | Retain original pre-rewrite history. |
| `codex/22-parse-cli-paths` | `095f39e` | `095f39e` | Same origin name, 0/0 | 0/22 | Ancestor | W5 | Integrated; retain local and origin refs for its worktree. |
| `codex/23-compact-pdf-layout` | `1b83849` | `1b83849` | Same origin name, 0/0 | 0/16 | Ancestor | None | Delete local and origin refs after checks. |
| `codex/24-print-llm-settings` | `e771c1b` | `e771c1b` | Same origin name, 0/0 | 0/10 | Ancestor | W6 | Integrated; retain local and origin refs for its worktree. |
| `codex/candidate-evaluation-cli` | `19ac9f2` | `19ac9f2` | Same origin name, 0/0 | 0/36 | Ancestor | None | Delete local and origin refs after checks. |
| `codex/developer-tooling` | `97d4451` | `97d4451` | Same origin name, 0/0 | 0/28 | Ancestor | None | Delete local and origin refs after checks. |
| `codex/general-git-workflow-template` | `982a5ca` | `65154f8` | Same origin name, ahead 1 | 2/39 | Diverged at `551b7cf` | None | Retain local unique work. Delete redundant origin ref after proving it is an ancestor of this local branch. Unset its deleted upstream. |
| `codex/mvp-help-update` | `3fc774e` | Absent | `origin/codex/mvp-two-stage`, behind 7 | 0/7 | Ancestor | W3 | Integrated; retain for its worktree. |
| `codex/mvp-two-stage` | `a8b364b` | `a8b364b` | Same origin name, 0/0 | 0/0 | Baseline | W4 | Retain as the priority integration branch. |
| `codex/reconcile-repository-history` | `58f345c` | `58f345c` | Same origin name, 0/0 | 0/38 | Ancestor | None | Delete local and origin refs after checks. |
| `codex/recoverable-storage` | `51eccfc` | `51eccfc` | Same origin name, 0/0 | 0/34 | Ancestor | None | Delete local and origin refs after checks. |
| `codex/reporting-and-scoring` | `3370c34` | `3370c34` | Same origin name, 0/0 | 0/33 | Ancestor | None | Delete local and origin refs after checks. |
| `codex/staged-evaluation` | `93971b9` | `93971b9` | Same origin name, 0/0 | 0/32 | Ancestor | None | Delete local and origin refs after checks. |
| `codex/ticket-workflow` | `063c1a3` | `063c1a3` | Same origin name, 0/0 | 0/31 | Ancestor | None | Delete local and origin refs after checks. |
| `codex/unorouter-stream-retries` | `28c5d34` | `28c5d34` | Same origin name, 0/0 | 0/8 | Ancestor | W1 | Integrated; retain local and origin refs for its dirty worktree. |
| `main` | `a819798` | `551b7cf` | None | 7/46 | Unrelated roots | None | Retain unchanged. Do not rewrite local or origin `main`. |
| `split-pipeline-and-prompts` | `3bc78bd` | `8887b6f` | Same origin name, ahead 6 | 18/46 | Unrelated roots | None | Delete local and origin refs. Both tips are reachable from `backup/pre-split-3bc78bd`. |

The origin refs in rows with matching local and origin tips have the same ancestry and counts. The three differing origin refs are:

| Origin branch | Ahead/behind MVP | Ancestry and unique commits |
|---|---|---|
| `origin/codex/general-git-workflow-template` | 1/39 | Diverged at `551b7cf`; only `65154f8` is unique. |
| `origin/main` | 0/39 | Ancestor; no unique commits. It is the remote default. |
| `origin/split-pipeline-and-prompts` | 12/46 | Unrelated roots; the oldest 12 commits of the original history below. |

### Attached worktrees

`PROJECTS` below means `C:/Users/alber/Claude/Projects/0_Projects`.

| ID | Path | Branch or detached tip | State at inventory | Why retained |
|---|---|---|---|---|
| W1 | `PROJECTS/Exams_Analysis_AI_pipeline` | `codex/unorouter-stream-retries` at `28c5d34` | Eight tracked edits and two untracked course directories | Contains active, uncommitted source and documentation work plus private course material. |
| W2 | `C:/Users/alber/.codex/worktrees/d957/Exams_Analysis_AI_pipeline` | Detached at `0b0412f` | Four tracked agent-tooling edits | Contains the parent task and unrelated tooling changes. |
| W3 | `C:/Users/alber/AppData/Local/Temp/ExamPipeline-mvp-help-update` | `codex/mvp-help-update` at `3fc774e` | Clean | Attached worktree; removal is outside ticket authority. |
| W4 | `PROJECTS/Exams_Analysis_AI_pipeline-mvp-two-stage` | `codex/mvp-two-stage` at `a8b364b` | Clean | This ticket's integration worktree. |
| W5 | `PROJECTS/Exams_Analysis_AI_pipeline-ticket-22-path-args` | `codex/22-parse-cli-paths` at `095f39e` | One untracked course directory | Holds private local material. |
| W6 | `PROJECTS/Exams_Analysis_AI_pipeline-ticket-23-pdf-padding` | `codex/24-print-llm-settings` at `e771c1b` | Clean | Attached worktree; its directory name does not identify the branch currently in it. |

Worktree removal is not needed for the justified final set. All six worktrees stay in place, including the two clean worktrees. Removing any later requires a separate approval naming its exact path.

### Recorded branch sources

Creation reflogs, where available, provide these sources. The source of a remote ref cannot be inferred from its name; its exact fetched tip is the inventory's authority.

| Branch | Recorded source and source commit |
|---|---|
| `backup/mvp-two-stage-pre-help-20260917` | `codex/mvp-two-stage @ 28c5d34` |
| `backup/mvp-two-stage-pre-unorouter-merge-20260917` | `codex/mvp-two-stage @ 6c99977` |
| `backup/pre-split-3bc78bd` | Explicit commit `3bc78bd` |
| `codex/22-parse-cli-paths` | `origin/codex/mvp-two-stage @ 6c99977` |
| `codex/23-compact-pdf-layout` | `origin/codex/22-parse-cli-paths @ 095f39e` |
| `codex/24-print-llm-settings` | `origin/codex/23-compact-pdf-layout @ 1b83849` |
| `codex/candidate-evaluation-cli` | Explicit commit `58f345c` |
| `codex/developer-tooling` | `codex/reconcile-repository-history @ 58f345c` |
| `codex/general-git-workflow-template` | `origin/main @ 551b7cf` |
| `codex/mvp-help-update` | `origin/codex/mvp-two-stage @ 28c5d34` |
| `codex/mvp-two-stage` | `codex/developer-tooling @ 97d4451` |
| `codex/reconcile-repository-history` | Oldest available entry is `58f345c`; creation source is unavailable. |
| `codex/recoverable-storage` | `HEAD @ 73cdbd8` |
| `codex/reporting-and-scoring` | `HEAD @ 19ac9f2` |
| `codex/staged-evaluation` | `HEAD @ 3370c34` |
| `codex/ticket-workflow` | `HEAD @ 93971b9` |
| `codex/unorouter-stream-retries` | `codex/24-print-llm-settings @ e771c1b` |
| `main` | No local branch reflog; creation source is unavailable. |
| `split-pipeline-and-prompts` | Oldest available entry is an amended commit `25e93ae`; creation source is unavailable. |

## Unique-history review and integration decision

No source branch has a missing production change that belongs in the current two-stage MVP. The dependency chain is already reachable from `a8b364b`: repository reconciliation, candidate validation and CLI, recoverable storage, reporting/scoring, staged evaluation, ticket tooling, developer tooling, the two-stage MVP, tickets 22 through 24, provider retries, then MVP help and branch policy. No merge, cherry-pick, or conflict resolution is required by this cleanup.

The current contracts remain the tests' authority. Stage 1 extracts full questions. Stage 2 tags and scores them. Python validates the responses and calculates metrics. `add-exam` saves a candidate without promoting it or changing accepted taxonomy and reports. Independent model review and OCR remain outside the MVP.

### Generic workflow and local-only material

`codex/general-git-workflow-template` has exactly two unique commits:

- `65154f82c3515b2ce57edaa13e4e8f4226ba1c22`, `docs: add reusable Git workflow template`. Its complete diff adds 130 lines at `docs/templates/agents-git-workflow.md`. It is a reusable template, not this project's current instructions. Its unconditional branch-creation instruction also predates this project's optional-branch policy. Preserve it as separate work rather than replace the current policy.
- `982a5ca3befe23b9bfa0c453adeb9c1c5e5eb108`, `Ignore regenerable graft graph cache`. The title does not describe the whole commit: it modifies one file and adds 2,108 files, for 366,934 inserted lines. It includes downloaded dependencies, private source papers, generated course output, scratch evidence, and two dataset documents. Its `.gitignore` and `.ignore` changes already exist in the MVP. The two dataset documents describe future corpus decisions and local data that are not part of the checked-out MVP. They do not require a pipeline integration for ticket 26.

The small configuration and documentation diffs were read in full. The large data additions were classified from the complete path/status inventory and aggregate counts; their private contents were not adopted as product changes. Preserve this exact local tip. Do not merge or push it wholesale. Deleting the origin ref at `65154f8` is safe because that commit remains reachable from the retained local branch at `982a5ca`. This is a local preservation decision, not a claim that the material has another remote backup.

### Original history before repository reconciliation

`backup/pre-split-3bc78bd` preserves all 18 original-history commits below, in oldest-first order. Local `main` contains the first seven. The old origin split branch contains the first 12. The local split branch is identical to the backup tip. These roots are unrelated by Git ancestry to the rewritten current history; a nonzero unique count is not proof of missing MVP behavior.

```text
23fe2a9764c776f3801f3a874db140da58b09fbd Initial commit: Academic pipeline
a12f0ab8ce29d5a6bc4857248f02f6988c713a64 refactor(pipeline): split model config into per-stage constants
b2ae8f6809747dd994d055994a5ee1902c800266 repo(structure): reorganize project into domain-based directory layout
5914167a6a6ee0240b8b5df2de32d25ffeed8bec feat(pipeline,tutor): multi-provider LLM support, tutor system v7, aicommit helper
177265b0ec6450b41b735536a340c4078af16ced repo(structure): Courses/<Course>/<Exam> hierarchy, generalize pipeline paths
9e5d4a3c39f0ec473f87ff26350aa8de0466760b repo(structure): per-course assets folder, archive superseded tutor prompts
a81979843565cb10d8424b1667ba88428209f5ea chore(repo): gitignore copyrighted course material, add tutor skills v2
6999289ccf8f5a2aa1410975bee3bf0c9cb3ce9c refactor(repo)!: split into pipeline/ + prompts/, archive the deep tutor
c1e6389ed488a45b49a34e569b15a20c71897e86 feat(pipeline): emit ranked JSON output, generalize beyond CS
25e93ae55c50689561d5859b2c77e2baa6aa622a repo(scope): pipeline-only portfolio repo, drop personal/superseded content, add README+LICENSE
5ce34026f71e3c9ec1a38dd271d0a63259b5a459 Clarify SPS formula prompt
8887b6f7e84749f285329124e474d3acb4ad7141 refactor(pipeline): rename ROI formula variables to human-readable names
c9c913db0a093b48dabe46de281c4c879af2a22a feat(pipeline): validate exam analyses and protect question context and record paths
f84b4828768f6daa6b65a678aaa08bbcac41bf07 feat(pipeline): report CLI outcomes with exit codes, independent review, and input selection
b47553b889193067151621a9f9631204ffb9192b docs(backlog): add a shared ticket status file and record current ticket states
b4156c4e4e08430bb6c925710043282b341b6026 refactor(pipeline): move report rendering into an exam_roi.reports module
b0dec34a18d51af266f73848c35c641fe353d10f docs(backlog): mark ticket 18 done and unblock tickets 19 and 20
3bc78bddb1c0d1541aaeddcc7310d9495b400069 feat: add reliable exam evaluation and ticket workflow
```

The full product-path diff between `3bc78bd` and the already-integrated `063c1a3` was reviewed over `pipeline`, `docs`, `scripts`, the ticket backlog, `AGENTS.md`, `README.md`, and `.gitignore`. It changes only five files. The pipeline difference is the intentional rejection of OCR in MVP help and its matching test. The remaining differences concern README/ADR wording and the graft ignore entry, which later MVP/developer-tooling commits already address. Merging the old root would reintroduce superseded private material and obsolete behavior. Keep the recovery history instead.

## Smallest justified final set

Retain ten local branches: `main`, `codex/mvp-two-stage`, the four other branches attached to worktrees, the three existing backup branches, and `codex/general-git-workflow-template` for its unique local history.

Retain five origin branches: `main`, `codex/mvp-two-stage`, `codex/22-parse-cli-paths`, `codex/24-print-llm-settings`, and `codex/unorouter-stream-retries`. The last three remain the upstreams of retained worktrees. Do not delete `origin/HEAD`.

Delete nine local branch names and ten origin branch names exactly as classified in the before table. A deleted name is recoverable from the recorded source commit and the retained branch that contains it. No commit objects, files, worktrees, stashes, or existing backup refs are removed.

Before deletion, create a local audit recovery ref with this lineage:

```text
refs/backup/ticket-26-before-cleanup-20260917 <- codex/mvp-two-stage @ a8b364ba66b0c6f7c9ec743e726511a7d51a687c
```

This ref records the integration base. It is not a new topic branch and contains no new private material. Existing recovery refs stay unchanged:

- `refs/heads/backup/mvp-two-stage-pre-help-20260917` at `28c5d34aa6ca4f0ce8acc55e8ac1c72f49bef3f9`.
- `refs/heads/backup/mvp-two-stage-pre-unorouter-merge-20260917` at `6c99977af017e1a3ecf903392543c51318a734bb`.
- `refs/heads/backup/pre-split-3bc78bd` at `3bc78bddb1c0d1541aaeddcc7310d9495b400069`.
- `refs/backup/pre-split-1789570153` at `311b070adb26d407a09f401cabaf63988461326d`.

The three protected stash tips are `cd6edfb2176298e2e6aeea38c4e6ee3807a993ac`, `735df351111a2367510b1639dcca1e793273e46f`, and `e36ac0c9ac8fca02f193f9436c9f116c08767aef`.

## Verification and execution record

The full checks and the impact report against `a8b364b` must finish before deleting any source ref. Recheck the exact source tips, their reachability from the retained branches, the worktree attachments, and the empty open-PR list immediately before deletion. The deletion commands must name only the classified refs. Do not change either `main` ref or push local-only `982a5ca`.

Completed before any source deletion:

- `$env:PYTHONIOENCODING='utf-8'; python -m unittest discover -s pipeline/tests -p 'test_*.py'` exited 0. It ran 231 tests in 17.174 seconds. The malformed-PDF messages, rejected live invocation without `--allow-live`, and rejected evaluation outputs came from negative tests; no provider calls ran.
- `$env:PYTHONIOENCODING='utf-8'; python scripts/check_tickets.py` exited 0. It ran 35 tests in 44.872 seconds, then reported 26 tickets, 0 errors, and 6 warnings. The warnings concern historical unreviewed closures for tickets 01, 02, 05, 07, 10, and 18. Those review items remain unchanged.
- `git diff --check` exited 0 with no output.

The impact report, ref changes, and observed after inventory are pending. This report does not yet claim that deletion happened.

## Commit key

```text
0b0412f 0b0412f080c5a9e6935adae034a23bc071ef1246
063c1a3 063c1a38f554aaa11b8d9c9e9ec3cefd6beff76e
095f39e 095f39e8a1acca9dcf8cf5f215effe845c146245
19ac9f2 19ac9f242b98176ccb3bc0bcc462ff30461d7e2f
1b83849 1b83849019fdadcac928b606f8b919c97798a5f9
28c5d34 28c5d34aa6ca4f0ce8acc55e8ac1c72f49bef3f9
3370c34 3370c34fd78efc8a1c16c01e011e9f83c9906c84
3bc78bd 3bc78bddb1c0d1541aaeddcc7310d9495b400069
3fc774e 3fc774efcdefddb59aa1e7575c3d0dba732473b9
51eccfc 51eccfce528555a1e3550a91c07c3f7696089f69
551b7cf 551b7cf44f14e07f3504c132018f6bc2be074fa8
58f345c 58f345c8b911269d282c641c30c8071b3a2743e0
65154f8 65154f82c3515b2ce57edaa13e4e8f4226ba1c22
6c99977 6c99977af017e1a3ecf903392543c51318a734bb
73cdbd8 73cdbd810fd9750bb6f20f11b77c9f08f520ce57
8887b6f 8887b6f7e84749f285329124e474d3acb4ad7141
93971b9 93971b9c9d1ae03483e39e3ae8d05c1c088a37b2
97d4451 97d4451846eeb8e30f0f071776e7ed8894d1c104
982a5ca 982a5ca3befe23b9bfa0c453adeb9c1c5e5eb108
a819798 a81979843565cb10d8424b1667ba88428209f5ea
a8b364b a8b364ba66b0c6f7c9ec743e726511a7d51a687c
e771c1b e771c1b5ad8ba9d058bd64612c024abcccddcded
```
