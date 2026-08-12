#!/bin/sh
# Activates the bundled git hooks (.githooks/) for this clone.
#
#   scripts/install-hooks.sh
#
# pre-commit: keeps your own sources/texts/cards out of the repo.
# pre-push:   blocks direct pushes to main (changes go through pull requests).

set -e

root=$(git rev-parse --show-toplevel)
chmod +x "$root"/.githooks/* 2>/dev/null || true
git -C "$root" config core.hooksPath .githooks

echo "Hooks active: $(git -C "$root" config core.hooksPath)"
echo "Disable with: git config --unset core.hooksPath"
