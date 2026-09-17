# 26: Consolidate project branches around the two-stage MVP

```json
{
  "schema_version": 1,
  "id": "26",
  "priority": "P1",
  "queue_order": 25,
  "areas": [],
  "depends_on": [],
  "related_to": [
    "25"
  ],
  "references": [
    "AGENTS.md",
    "docs/research/git-and-pull-requests-for-ai-development.md",
    ".scratch/reliable-exam-analysis/issues/BLOCKED/25-publish-an-accurate-developer-onboarding-and-project-guide.md"
  ],
  "verification": null,
  "closure": null
}
```

**What to build:** Reduce the project to the smallest justified set of local and remote branches while preserving every needed change and recovery path. Treat `codex/mvp-two-stage` as the priority integration branch. Apply the branch policy in `AGENTS.md` throughout the cleanup, including explicit branch lineage before any new branch is created.

- [ ] Fetch and prune remote references, then record every local branch, origin branch, upstream, attached worktree, source commit, ahead or behind state, ancestry relationship, and unique commit relative to `codex/mvp-two-stage`.
- [ ] Classify every branch as already integrated, required for active work, a source of changes that belong in the two-stage MVP, intentionally retained recovery history, or safe to delete. Record the evidence for each classification before changing refs.
- [ ] Define the smallest justified final branch set. Retain `main`, prioritize `codex/mvp-two-stage`, and retain another branch only when it has reviewed unique work, an active pull request, or a required worktree.
- [ ] Integrate every reviewed change that belongs in the current MVP into `codex/mvp-two-stage` in dependency order. Use fast-forward integration when ancestry permits. For other histories, review the full unique diff and choose a merge or cherry-pick that preserves the current two-stage MVP behavior.
- [ ] Create a named recovery ref before each non-fast-forward integration or conflict resolution. Record the integration target, source branch, source commit, chosen method, conflicts, and verification result.
- [ ] Resolve conflicts against the current MVP contracts, tests, and CLI behavior. Do not restore superseded architecture or planned acceptance behavior as if it were implemented.
- [ ] Run focused checks after each integration. Run the full pipeline tests, ticket checks, diff checks, and ticket-impact report against the actual integration base before deleting any source branch.
- [ ] Delete a local or remote branch only after proving that its required commits are reachable from a retained branch and that no active pull request or worktree still needs it.
- [ ] Do not delete stashes, backup refs, or worktrees as part of branch cleanup. Ask for separate approval naming the exact target when removing one is necessary to finish consolidation.
- [ ] Finish with `codex/mvp-two-stage` tracking its origin branch, a clean working tree, no redundant topic branches, and a written before-and-after branch inventory.
- [ ] Move ticket 25 back to `OPEN` only after the consolidation evidence has been reviewed and ticket 26 is complete.

**Architecture:** Branch cleanup must preserve the checked-out two-stage MVP as the current product. A branch name or old ticket closure is not proof that its commits belong in the MVP. Establish ancestry, inspect unique diffs, and run the relevant behavior before integration.

## Scope boundaries

- Do not rewrite `main`, force-push, use `git reset --hard`, or discard unique commits.
- Do not implement documentation ticket 25 during this work.
- Do not change pipeline behavior except when a reviewed branch integration is already required for the current MVP.
- Do not remove private course data, generated course outputs, stashes, backup refs, or worktrees.

## Evidence and history

The initial inventory on 2026-09-17 found 19 local branches, 16 origin branches, and five worktrees. Many older topic branches are ancestors of `codex/mvp-two-stage`, while other refs have unique history or remain attached to a worktree. Recompute this inventory after fetching because branch state can change.

This ticket applies the branch policy added in commit `7892b23`. It blocks ticket 25 so documentation work starts from the consolidated project state and documents the branch model that actually remains.
