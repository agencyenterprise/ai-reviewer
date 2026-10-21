#!/bin/bash
# Open or update the release pull request (dev -> main).
#
# Its label is the largest release label among the pull requests merged into dev
# since main (major > minor > patch > norelease); a pull request without one,
# and a commit pushed to dev directly, counts as patch. A label someone set by
# hand on the release pull request wins over the computed one.
#
# Expects origin/main and origin/dev to be fetched with full history and tags,
# and GH_TOKEN to be set.
#
# Usage:
#   ./sync-release-pr.sh [--dry-run]

set -euo pipefail

DRY_RUN=false
if [ "${1:-}" = "--dry-run" ]; then
  DRY_RUN=true
fi

RELEASE_LABELS="release:major release:minor release:patch norelease"

rank() {
  case "$1" in
    release:major) echo 3 ;;
    release:minor) echo 2 ;;
    release:patch) echo 1 ;;
    *) echo 0 ;;
  esac
}

# The first release label among a list of label names, empty if none.
release_label_of() {
  for label in $1; do
    if echo " $RELEASE_LABELS " | grep -q " $label "; then
      echo "$label"
      return
    fi
  done
}

next_version() {
  local major minor patch
  IFS=. read -r major minor patch <<< "$1"
  case "$2" in
    release:major) echo "$((major + 1)).0.0" ;;
    release:minor) echo "${major}.$((minor + 1)).0" ;;
    release:patch) echo "${major}.${minor}.$((patch + 1))" ;;
  esac
}

# Merge commits alone are what syncing main back into dev leaves behind; only
# commits of their own mean dev has something to ship.
if [ "$(git rev-list --count --no-merges origin/main..origin/dev)" = "0" ]; then
  echo "dev has nothing main lacks; no release pull request needed"
  exit 0
fi

# Pull requests merged into dev, found through GitHub's commit associations so
# merge, squash and rebase merges all count. A first-parent commit with no pull
# request was pushed to dev directly.
PR_NUMBERS=""
DIRECT_COMMITS=0
for sha in $(git rev-list --first-parent origin/main..origin/dev); do
  # Merges that brought main back into dev carry nothing to release.
  second_parent=$(git rev-parse -q --verify "${sha}^2" || true)
  if [ -n "$second_parent" ] && git merge-base --is-ancestor "$second_parent" origin/main; then
    continue
  fi
  number=$(gh api "repos/{owner}/{repo}/commits/${sha}/pulls" \
    --jq '[.[] | select(.base.ref == "dev" and .merged_at != null)][0].number // empty')
  if [ -z "$number" ]; then
    DIRECT_COMMITS=$((DIRECT_COMMITS + 1))
  elif ! echo " $PR_NUMBERS " | grep -q " $number "; then
    PR_NUMBERS="$PR_NUMBERS $number"
  fi
done

COMPUTED=norelease
PR_LINES=""
for number in $PR_NUMBERS; do
  info=$(gh pr view "$number" --json title,labels --jq '[.title, ([.labels[].name] | join(" "))] | @tsv')
  title=$(echo "$info" | cut -f1)
  label=$(release_label_of "$(echo "$info" | cut -f2)")
  label=${label:-release:patch}
  if [ "$(rank "$label")" -gt "$(rank "$COMPUTED")" ]; then
    COMPUTED=$label
  fi
  PR_LINES="${PR_LINES}- #${number} ${title} (\`${label}\`)"$'\n'
done
if [ "$DIRECT_COMMITS" -gt 0 ]; then
  # No pull request carried a label for these, so they ship as at least a patch.
  if [ "$(rank release:patch)" -gt "$(rank "$COMPUTED")" ]; then
    COMPUTED=release:patch
  fi
  PR_LINES="${PR_LINES}- ${DIRECT_COMMITS} commit(s) pushed to dev directly (\`release:patch\`)"$'\n'
fi

# The body records what this script computed and any label set by hand. A
# release label that differs from the one this script last applied was set by
# hand, and it stays until someone changes the label again.
EXISTING=$(gh pr list --base main --head dev --state open --json number,labels,body --jq '.[0] // empty')
OVERRIDE=""
if [ -n "$EXISTING" ]; then
  PR_NUMBER=$(echo "$EXISTING" | jq -r .number)
  CURRENT=$(release_label_of "$(echo "$EXISTING" | jq -r '[.labels[].name] | join(" ")')")
  BODY=$(echo "$EXISTING" | jq -r .body)
  LAST_COMPUTED=$(echo "$BODY" | sed -nE 's/^<!-- computed-label: (.*) -->$/\1/p')
  OVERRIDE=$(echo "$BODY" | sed -nE 's/^<!-- override-label: (.*) -->$/\1/p')
  LAST_APPLIED=${OVERRIDE:-$LAST_COMPUTED}
  if [ -n "$CURRENT" ] && [ "$CURRENT" != "$LAST_APPLIED" ]; then
    OVERRIDE=$CURRENT
  fi
fi
KIND=${OVERRIDE:-$COMPUTED}
if [ -n "$OVERRIDE" ]; then
  echo "label set by hand to ${OVERRIDE}; keeping it"
fi

LAST_TAG=$(git tag -l 'v*' --sort=-version:refname | head -n 1)
CURRENT_VERSION=${LAST_TAG#v}
if [ "$KIND" = "norelease" ]; then
  TITLE="chore(release): dev to main, no release"
  OUTCOME="Merging brings dev into main without cutting a release (\`norelease\`)."
else
  NEXT_VERSION=$(next_version "$CURRENT_VERSION" "$KIND")
  TITLE="chore(release): v${NEXT_VERSION}"
  OUTCOME="Merging releases **v${NEXT_VERSION}** (\`${KIND}\` from v${CURRENT_VERSION}): release.yml bumps the version, writes the changelog, tags and publishes the GitHub Release."
fi

BODY_FILE=$(mktemp)
cat > "$BODY_FILE" <<EOF
${OUTCOME}

This pull request is kept up to date by \`release-pr.yml\` on every push to dev. Its label is the largest release label among the pull requests below; change it here to override, and later updates keep your choice.

## Pull requests

${PR_LINES}
<!-- computed-label: ${COMPUTED} -->
<!-- override-label: ${OVERRIDE} -->
EOF

echo "Title: ${TITLE}"
echo "Label: ${KIND} (computed: ${COMPUTED})"
cat "$BODY_FILE"

if [ "$DRY_RUN" = true ]; then
  echo "DRY RUN: no pull request created or changed"
  exit 0
fi

if [ -z "$EXISTING" ]; then
  gh pr create --base main --head dev --title "$TITLE" --body-file "$BODY_FILE" --label "$KIND"
  exit 0
fi

gh pr edit "$PR_NUMBER" --title "$TITLE" --body-file "$BODY_FILE"
APPLIED=$(echo "$EXISTING" | jq -r '[.labels[].name] | join(" ")')
for label in $RELEASE_LABELS; do
  if [ "$label" != "$KIND" ] && echo " $APPLIED " | grep -q " $label "; then
    gh pr edit "$PR_NUMBER" --remove-label "$label"
  fi
done
if ! echo " $APPLIED " | grep -q " $KIND "; then
  gh pr edit "$PR_NUMBER" --add-label "$KIND"
fi
