#!/usr/bin/env zsh

[[ -f pom.xml ]] || exit 1
[[ -d src/main/scala ]] || exit 1

version=$(grep -E '<scala(\.binary)?\.version>' pom.xml | sed 's/.*<[^>]*>\([^<]*\)<.*/\1/' | head -1)
[[ -n "$version" ]] || exit 1

echo "v$version"
