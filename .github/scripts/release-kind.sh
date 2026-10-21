#!/bin/bash
# Print the bump main's head needs: patch, minor, major, or nothing.
#
# It is the largest release label among every pull request merged into main
# since the latest tag, not just the one whose merge started this run: runs are
# serialized but merges are not, so one run can release several merges. A
# commit on main with no pull request counts as patch.
#
# A head that is already tagged was released by an earlier run, which prints
# nothing (release.yml's sync-dev job still finishes any sync that run left);
# if that run stopped before creating the GitHub Release, this fails and says
# what is left to do by hand.
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

if TAG=$(git describe --exact-match --tags --match 'v*' HEAD 2>/dev/null); then
  if gh release view "$TAG" > /dev/null 2>&1; then
    echo "main's head is already released as ${TAG}" >&2
    exit 0
  fi
  echo "main's head is tagged ${TAG} but has no GitHub Release: an earlier run stopped partway." >&2
  echo "Finish by hand: create the release (gh release create ${TAG}), then re-run this workflow to sync dev." >&2
  exit 1
fi

PREVIOUS_TAG=$(git tag -l 'v*' --sort=-version:refname | head -n 1)
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
