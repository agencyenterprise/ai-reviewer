#!/bin/bash
# Open or update the release pull request (dev -> main).
#
# Its label is the largest release label among the pull requests merged into dev
# since main (major > minor > patch > norelease); a pull request without one
# counts as patch. A label someone set by hand on the release pull request wins:
# the label this script last computed is kept in the body, and a different one
# applied there means someone overrode it.
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

# Pull requests merged into dev, minus the ones that brought main back into it.
PR_NUMBERS=$(git log --first-parent --format=%s origin/main..origin/dev \
  | grep -vE '^Merge pull request #[0-9]+ from [^ ]+/main$' \
  | sed -nE 's/^Merge pull request #([0-9]+) from .*/\1/p')

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
if [ -z "$PR_NUMBERS" ]; then
  # Commits pushed to dev directly, with no pull request to carry a label.
  COMPUTED=release:patch
  PR_LINES="- Commits pushed to dev directly (no pull requests)"$'\n'
fi

EXISTING=$(gh pr list --base main --head dev --state open --json number,labels,body --jq '.[0] // empty')
KIND=$COMPUTED
if [ -n "$EXISTING" ]; then
  PR_NUMBER=$(echo "$EXISTING" | jq -r .number)
  CURRENT=$(release_label_of "$(echo "$EXISTING" | jq -r '[.labels[].name] | join(" ")')")
  LAST_COMPUTED=$(echo "$EXISTING" | jq -r .body | sed -nE 's/^<!-- computed-label: (.*) -->$/\1/p')
  if [ -n "$CURRENT" ] && [ "$CURRENT" != "$LAST_COMPUTED" ]; then
    echo "label overridden by hand to ${CURRENT}; keeping it"
    KIND=$CURRENT
  fi
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
