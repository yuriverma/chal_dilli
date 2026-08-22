#!/usr/bin/env bash
#
# Deploy to the Hugging Face Space.
#
# Why this is not just `git push space main`
# ------------------------------------------
# The Space's pre-receive hook rejects any file over 10MB that is not tracked
# by Git LFS, and it inspects every blob in the pushed history -- not just the
# current tree. This repo used to carry three large GTFS files:
#
#     data/GTFS/stop_times.csv        76.0 MB
#     data/GTFS/fare_attributes.csv   34.6 MB
#     data/GTFS/fare_rules.csv        29.9 MB
#
# All three are deleted now, and nothing in the working tree comes close to
# 10MB. But they still exist in earlier commits, so a normal push offers them
# to the hook and is refused.
#
# Rewriting the GitHub history to purge them would mean rewriting commits that
# are already merged and shared, to fix a constraint that only applies to the
# deploy target. So instead this pushes a single parentless commit containing
# just the current tree. The Space gets exactly the files it needs to run and
# no history at all, which is all a deploy target wants.
#
# `git commit-tree` builds that commit directly from an existing tree object,
# so nothing here touches your working tree, your index, or your branches.
#
# Usage:
#     scripts/deploy_space.sh [ref]        # ref defaults to origin/main
#
# Requires a Hugging Face token with write access, already stored:
#     hf auth login --add-to-git-credential

set -euo pipefail

REMOTE="${SPACE_REMOTE:-space}"
REF="${1:-origin/main}"

if ! git remote get-url "$REMOTE" >/dev/null 2>&1; then
    echo "No '$REMOTE' remote. Add it with:" >&2
    echo "  git remote add $REMOTE https://huggingface.co/spaces/<user>/<space>" >&2
    exit 1
fi

if ! git rev-parse --verify "$REF" >/dev/null 2>&1; then
    echo "Cannot resolve ref: $REF" >&2
    exit 1
fi

SOURCE=$(git rev-parse --short "$REF")
FULL_TREE=$(git rev-parse "${REF}^{tree}")

# Paths the Space has no use for. The Space runs the Python backend only; the
# frontend deploys to Netlify separately, exactly as .dockerignore already
# assumes for the container image.
#
# Excluding it is also load-bearing, not just tidiness. A second Space hook
# rejects binary files outright unless they are stored via Xet/LFS, and every
# binary in this repo is a frontend asset -- the background video, its poster,
# the images, the audio. Everything outside frontend/ is text.
EXCLUDE=(frontend tests)

# Build the filtered tree in a throwaway index so the real index, working tree
# and branches are all left alone.
TMP_INDEX=$(mktemp)
trap 'rm -f "$TMP_INDEX"' EXIT
GIT_INDEX_FILE="$TMP_INDEX" git read-tree "$FULL_TREE"
GIT_INDEX_FILE="$TMP_INDEX" git rm -r --cached -q --ignore-unmatch "${EXCLUDE[@]}"
TREE=$(GIT_INDEX_FILE="$TMP_INDEX" git write-tree)

# Refuse to deploy a tree that would be rejected anyway, with a message that
# says which file rather than leaving you to read the hook's output.
# ls-tree -l emits "<mode> <type> <object> <size>\t<path>", so split on the tab:
# paths here contain spaces ("data/DMRC_GTFS (1)/...") and awk's default
# whitespace split would truncate them.
OVERSIZE=$(
    git ls-tree -r -l "$TREE" |
    awk -F'\t' '{
        split($1, meta, " ")
        if (meta[4] > 10485760) printf "  %.1f MB  %s\n", meta[4]/1048576, $2
    }'
)
if [ -n "$OVERSIZE" ]; then
    echo "These files exceed the Space's 10MB non-LFS limit:" >&2
    echo "$OVERSIZE" >&2
    echo >&2
    echo "Shrink them, or set up Git LFS on the Space, before deploying." >&2
    exit 1
fi

echo "Deploying tree of $REF ($SOURCE) to remote '$REMOTE'..."
echo "  excluding: ${EXCLUDE[*]}"
echo "  files:     $(GIT_INDEX_FILE="$TMP_INDEX" git ls-files | wc -l | tr -d ' ')"

COMMIT=$(
    git commit-tree "$TREE" -m "Deploy $SOURCE

Single-commit snapshot of $REF, backend only. History is intentionally
omitted: the Space rejects the large GTFS blobs that older commits still
contain, and it needs only the current files to run. The frontend is excluded
because it deploys to Netlify and its binary assets are rejected too. See
scripts/deploy_space.sh."
)

# --force because each deploy is a fresh parentless commit, so it is never a
# fast-forward of what is already there.
git push "$REMOTE" "$COMMIT:refs/heads/main" --force

echo
echo "Pushed. The Space will rebuild; watch the logs on its page."
