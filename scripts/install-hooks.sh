#!/bin/sh
# Aktiviert die mitgelieferten Git-Hooks (.githooks/) für dieses Klon.
#
#   scripts/install-hooks.sh
#
# pre-commit: verhindert, dass eigene Quellen/Texte/Karten eingecheckt werden.
# pre-push:   blockt direkte Pushes auf main (dort gilt: nur via Pull Request).

set -e

wurzel=$(git rev-parse --show-toplevel)
chmod +x "$wurzel"/.githooks/* 2>/dev/null || true
git -C "$wurzel" config core.hooksPath .githooks

echo "Hooks aktiv: $(git -C "$wurzel" config core.hooksPath)"
echo "Deaktivieren mit: git config --unset core.hooksPath"
