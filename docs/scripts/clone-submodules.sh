#!/bin/bash
# Clone UnderTheRock submodules using the right transport per host:
#   github.com     -> SSH (git@github.com:...)
#   github.amd.com -> HTTPS + PAT (stored in ~/.git-credentials)
#   er.github.amd.com -> HTTPS + PAT
#   gitlab.sysip.amd.com -> HTTPS
#   gerritgit -> SKIP (SSH only, no HTTPS equivalent)
#
# Prerequisites:
#   git config --global credential.helper store
#   echo "https://<user>:<PAT>@github.amd.com" >> ~/.git-credentials
#   echo "https://<user>:<PAT>@er.github.amd.com" >> ~/.git-credentials
#   SSH key registered on github.com

set -euo pipefail
cd "$(dirname "$0")/../../under-the-rock-main"

RESULTS="${1:-/tmp/submodule_clone_results.txt}"
> "$RESULTS"

while IFS= read -r sm_name; do
    url=$(git config -f .gitmodules --get "submodule.${sm_name}.url" 2>/dev/null)
    path=$(git config -f .gitmodules --get "submodule.${sm_name}.path" 2>/dev/null)
    branch=$(git config -f .gitmodules --get "submodule.${sm_name}.branch" 2>/dev/null)

    [ -z "$url" ] || [ -z "$path" ] && continue

    clone_url=""
    method=""

    if echo "$url" | grep -q '^ssh://gerritgit'; then
        echo "SKIP|${sm_name}|${url}|${path}|${branch}|Gerrit SSH only" >> "$RESULTS"
        continue
    elif echo "$url" | grep -q 'git@github\.com:'; then
        clone_url="$url"
        method="ssh"
    elif echo "$url" | grep -q 'git@github\.amd\.com:'; then
        repo_path=$(echo "$url" | sed 's/git@github\.amd\.com://')
        clone_url="https://github.amd.com/${repo_path}"
        method="https+token"
    elif echo "$url" | grep -q 'git@er\.github\.amd\.com:'; then
        repo_path=$(echo "$url" | sed 's/git@er\.github\.amd\.com://')
        clone_url="https://er.github.amd.com/${repo_path}"
        method="https+token"
    elif echo "$url" | grep -q 'git@gitlab\.sysip\.amd\.com:'; then
        repo_path=$(echo "$url" | sed 's/git@gitlab\.sysip\.amd\.com://')
        clone_url="https://gitlab.sysip.amd.com/${repo_path}"
        method="https"
    else
        clone_url="$url"
        method="unknown"
    fi

    mkdir -p "$(dirname "$path")"
    rm -rf "$path" 2>/dev/null

    clone_cmd="git clone --depth 1"
    [ -n "$branch" ] && clone_cmd="$clone_cmd --branch $branch"
    clone_cmd="$clone_cmd $clone_url $path"

    echo ">>> [$method] $sm_name: $clone_url (branch=${branch:-default})"
    output=$(timeout 120 bash -c "$clone_cmd" 2>&1)
    rc=$?

    if [ $rc -eq 0 ]; then
        file_count=$(find "$path" -type f | wc -l)
        echo "OK|${sm_name}|${clone_url}|${path}|${branch}|${file_count} files" >> "$RESULTS"
    elif [ $rc -eq 124 ]; then
        echo "TIMEOUT|${sm_name}|${clone_url}|${path}|${branch}|Timeout 120s" >> "$RESULTS"
        rm -rf "$path" 2>/dev/null
    else
        errmsg=$(echo "$output" | grep -i -E 'fatal|error|denied|not found|403|404|Authentication|Could not' | head -1)
        [ -z "$errmsg" ] && errmsg=$(echo "$output" | tail -1)
        echo "FAIL|${sm_name}|${clone_url}|${path}|${branch}|${errmsg}" >> "$RESULTS"
        rm -rf "$path" 2>/dev/null
    fi
done < <(grep -E '^\[submodule' .gitmodules | sed 's/\[submodule "\(.*\)"\]/\1/')

echo ""
echo "========================================="
ok=$(grep -c '^OK|' "$RESULTS"); fail=$(grep -c '^FAIL|' "$RESULTS")
timeout=$(grep -c '^TIMEOUT|' "$RESULTS"); skip=$(grep -c '^SKIP|' "$RESULTS")
echo "DONE: OK=$ok  Fail=$fail  Timeout=$timeout  Skip=$skip"
echo "Results: $RESULTS"
