#!/usr/bin/env bash
set -euo pipefail

event_name=$1
base_sha=$2
head_sha=$3
before_sha=$4
sha=$5

if [ "$event_name" = "pull_request" ]; then
  git diff --name-only --no-renames "${base_sha}...${head_sha}"
  exit 0
fi

[ "$event_name" = "push" ]
[ -n "$before_sha" ]
[[ ! "$before_sha" =~ ^0+$ ]]
git cat-file -e "${before_sha}^{commit}" 2>/dev/null
git merge-base --is-ancestor "$before_sha" "$sha"
git diff --name-only --no-renames "$before_sha" "$sha"
