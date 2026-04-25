#!/usr/bin/env bash

[[ -f pom.xml ]] || exit 1
[[ -d src/main/scala ]] || exit 1

version=$(grep -oP '(?<=<scala(?:\.binary)?\.version>)[^<]+' pom.xml | head -1)
[[ -n "$version" ]] || exit 1

echo "v$version"
