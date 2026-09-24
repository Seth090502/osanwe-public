#!/usr/bin/env bash
# Re-sign existing prevention-arch-v* tags with GPG.
# Prerequisites:
#   1. GPG key generated: `gpg --full-generate-key` (RSA 4096 recommended)
#   2. Git configured: `git config --global user.signingkey <KEY-ID>`
#
# Run once after configuring the key. Idempotent: re-running on already-signed tags re-signs them.

set -euo pipefail

if [ -z "$(git config --global user.signingkey)" ]; then
    echo "ERROR: git config --global user.signingkey is not set."
    echo "Configure GPG key first per docs/gpg-recovery-setup.md"
    exit 1
fi

for tag in $(git tag -l 'prevention-arch-v*'); do
    commit=$(git rev-list -n 1 "$tag")
    msg=$(git tag -l --format='%(contents)' "$tag")
    git tag -d "$tag"
    git tag -s "$tag" "$commit" -m "$msg"
    echo "Re-signed $tag at $commit"
done

echo ""
echo "All prevention-arch-v* tags now GPG-signed. Verify with:"
echo "  git tag -v prevention-arch-v6  # expect 'Good signature'"
