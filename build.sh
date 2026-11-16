#!/bin/sh
set -eu
cd "$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
case "${1:-all}" in all|arm32|arm64|test|sanitize|airplay-test) target=${1:-all};; *) echo 'Usage: ./build.sh [all|arm32|arm64|test|sanitize|airplay-test]' >&2; exit 2;; esac
docker info >/dev/null
docker build --platform linux/amd64 -t mpcairlink-build:bookworm .
docker run --rm --platform linux/amd64 --user "$(id -u):$(id -g)" -v "$PWD:/work" mpcairlink-build:bookworm make "$target"
