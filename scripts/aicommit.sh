# --- Custom Claude AI Commands ---
# aicommit — draft a Conventional Commit message from the staged diff using Claude,
# then open it in your editor to confirm before committing.
#
# Install: copy this function into ~/.bashrc (or `source` this file from it), then
#          `source ~/.bashrc`. Bash only (Git Bash / WSL) — needs the `claude` CLI on PATH.
#
# Improvements over the original:
#   - Adaptive context: sends a compact --stat for large diffs, full diff only when small,
#     so big commits don't overflow the model's context or cost a fortune.
#   - Validates Claude returned a non-empty message before committing (no blank commits).
#   - Asks for a VALID Conventional Commit type (feat/fix/docs/refactor/chore/...).
#   - Optional pinned model via AICOMMIT_MODEL for reproducible behavior.
#   - Safer temp file (mktemp) with cleanup; aborts cleanly on Ctrl-C.
#   - Confirms a git repo and the presence of the `claude` CLI before doing anything.

aicommit() {
    # Tunables (override in your environment if you like)
    local DIFF_LINE_BUDGET="${AICOMMIT_DIFF_BUDGET:-600}"   # full diff used only under this many lines
    local MODEL_FLAG=()
    [ -n "${AICOMMIT_MODEL:-}" ] && MODEL_FLAG=(--model "$AICOMMIT_MODEL")

    # Preconditions
    if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
        echo "Not inside a git repository."
        return 1
    fi
    if ! command -v claude >/dev/null 2>&1; then
        echo "The 'claude' CLI was not found on PATH."
        return 1
    fi
    if git diff --staged --quiet; then
        echo "No staged changes found. Run 'git add <files>' first."
        return 1
    fi

    # Decide how much context to send. Large diffs -> stat-only (filenames + churn);
    # small diffs -> full patch. This keeps big commits within context and cheap.
    local DIFF_LINES CONTEXT CONTEXT_KIND
    DIFF_LINES=$(git diff --staged --numstat | wc -l)
    local TOTAL_PATCH_LINES
    TOTAL_PATCH_LINES=$(git diff --staged --unified=0 | wc -l)

    if [ "$TOTAL_PATCH_LINES" -le "$DIFF_LINE_BUDGET" ]; then
        CONTEXT=$(git diff --staged)
        CONTEXT_KIND="full patch"
    else
        # Compact view: per-file churn + the new-file list, no full bodies.
        CONTEXT=$'FILE CHANGES (name + lines added/removed):\n'
        CONTEXT+=$(git diff --staged --stat)
        CONTEXT+=$'\n\nSTATUS (A=added, M=modified, D=deleted, R=renamed):\n'
        CONTEXT+=$(git diff --staged --name-status)
        CONTEXT_KIND="summary (large diff: ${DIFF_LINES} files, ${TOTAL_PATCH_LINES} patch lines)"
    fi

    echo "Claude is analyzing your staged changes... [${CONTEXT_KIND}]"

    local PROMPT
    PROMPT="Analyze these staged git changes and write a Conventional Commit message.

Rules:
- First line: <type>(<scope>): <summary>
  - <type> MUST be one of: feat, fix, docs, style, refactor, perf, test, build, ci, chore, revert
  - <scope> is the area touched (e.g. pipeline, tutor, loci, repo). Keep it short.
  - <summary> is imperative mood, lower-case, no trailing period, <= 72 chars.
- Blank line, then 2-5 bullet points starting with '- ' explaining WHY the change was made
  (not just what). If the diff was provided as a summary rather than a full patch, base the
  bullets on the file groups and do not invent specific line-level details.
- Output ONLY the raw commit message. No markdown code fences, no preamble, no commentary.

Changes:
$CONTEXT"

    local MSG
    MSG=$(claude "${MODEL_FLAG[@]}" "$PROMPT")

    # Validate non-empty (and not just whitespace) before committing.
    if [ -z "${MSG//[[:space:]]/}" ]; then
        echo "Claude returned an empty message — aborting. Nothing was committed."
        return 1
    fi

    # Strip accidental ``` fences if the model added them despite instructions.
    MSG=$(printf '%s\n' "$MSG" | sed '/^```/d')

    local MSGFILE
    MSGFILE=$(mktemp "${TMPDIR:-/tmp}/aicommit.XXXXXX") || return 1
    # shellcheck disable=SC2064
    trap "rm -f '$MSGFILE'" RETURN
    printf '%s\n' "$MSG" > "$MSGFILE"

    # -e opens the message in your editor so you always review/edit before it lands.
    git commit -e -F "$MSGFILE"
}
