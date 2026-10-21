#!/bin/bash
# Print the bump main's head needs: patch, minor, major, or nothing.
#
# It is the largest release label among every pull request merged into main
# since the latest tag, not just the one whose merge started this run: runs are
# serialized but merges are not, so one run can release several merges. A
# commit on main with no pull request counts as patch.
#
# A head that is already tagged has nothing since the latest tag and prints
# nothing (release.yml's sync-dev job still finishes any sync an earlier run
# left). If the latest tag has no GitHub Release, an earlier run stopped
# partway, and this fails with what is left to do by hand.
#
# Expects main to be checked out with full history and tags, and GH_TOKEN to be
# set.

set -euo pipefail

rank() {
  case "$1" in
    release:major) echo 3 ;;
    release:minor) echo 2 ;;
    release:patch) echo 1 ;;
    *) echo 0 ;;
  esac
}

# Checked wherever main's head is: a pull request merged after an earlier run
# pushed its tag would otherwise hide that run's missing release.
PREVIOUS_TAG=$(git tag -l 'v*' --sort=-version:refname | head -n 1)
if ! gh release view "$PREVIOUS_TAG" > /dev/null 2>&1; then
  echo "The latest tag ${PREVIOUS_TAG} has no GitHub Release: an earlier run stopped partway." >&2
  echo "Finish by hand: create the release (gh release create ${PREVIOUS_TAG}), then re-run this workflow." >&2
  exit 1
fi

BEST=norelease
for sha in $(git rev-list --first-parent "${PREVIOUS_TAG}..HEAD"); do
  labels=$(gh api "repos/{owner}/{repo}/commits/${sha}/pulls" \
    --jq '[.[] | select(.base.ref == "main" and .merged_at != null)][0] | if . == null then "release:patch" else ([.labels[].name] | join(" ")) end')
  for label in $labels; do
    if [ "$(rank "$label")" -gt "$(rank "$BEST")" ]; then
      BEST=$label
    fi
  done
  echo "${sha:0:8}: ${labels:-no release label}" >&2
done

case "$BEST" in
  release:*) echo "${BEST#release:}" ;;
esac
