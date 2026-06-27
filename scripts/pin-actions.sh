#!/usr/bin/env bash
#
# pin-actions.sh — convert `uses: org/action@tag` to verified SHA pins.
#
# Supply-chain hardening: mutable tags (v4, main) can be repointed at malicious code
# (cf. the tj-actions/changed-files compromise). Pinning to an immutable commit SHA
# removes that attack surface — but ONLY if the SHA is verified against the action's
# real release, which is the whole point of this script. A pin to the wrong SHA looks
# safe and isn't.
#
# Requires: gh (GitHub CLI, authenticated) and standard coreutils.
# Usage:   ./scripts/pin-actions.sh .github/workflows/security.yml
#
set -euo pipefail

FILE="${1:?Usage: pin-actions.sh <workflow.yml>}"
[[ -f "$FILE" ]] || { echo "No such file: $FILE" >&2; exit 1; }

echo "Resolving action tags to verified SHAs in: $FILE"

# Match: uses: org/repo@tag   (skip ones already pinned to a 40-char SHA)
grep -oE 'uses:[[:space:]]+[A-Za-z0-9._-]+/[A-Za-z0-9._-]+@[A-Za-z0-9._/-]+' "$FILE" \
  | sed -E 's/uses:[[:space:]]+//' \
  | sort -u \
  | while read -r ref; do
      action="${ref%@*}"
      tag="${ref##*@}"

      # Already a SHA? leave it.
      if [[ "$tag" =~ ^[0-9a-f]{40}$ ]]; then
        echo "  ok   $action already pinned ($tag)"
        continue
      fi

      # Resolve tag -> commit SHA via the GitHub API (source-verified).
      sha="$(gh api "repos/${action}/git/refs/tags/${tag}" \
              --jq '.object.sha' 2>/dev/null || true)"

      # Annotated tags resolve to a tag object; dereference to the commit.
      if [[ -n "${sha:-}" ]]; then
        type="$(gh api "repos/${action}/git/tags/${sha}" --jq '.object.sha' 2>/dev/null || true)"
        [[ -n "$type" ]] && sha="$type"
      fi

      if [[ -z "${sha:-}" || ! "$sha" =~ ^[0-9a-f]{40}$ ]]; then
        echo "  FAIL could not verify SHA for $action@$tag — refusing to pin" >&2
        exit 2   # fail loudly: never silently leave an unverified pin
      fi

      # Pin in place, keeping the tag as a trailing comment for readability.
      sed -i -E "s|${action}@${tag}([^A-Za-z0-9._/-]\|\$)|${action}@${sha} # ${tag}\1|g" "$FILE"
      echo "  pin  $action@$tag -> $sha"
    done

echo "Done. Review the diff before committing."
