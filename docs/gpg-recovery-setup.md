# GPG-Signed Recovery Tag Setup

The `prevention-arch-vN` recovery tags are currently **unsigned annotated tags** (convention-based immutability). For solo-developer workflows on a local-only repo this is sufficient. For teams, public repos, or cross-machine recovery scenarios, GPG-sign the tags for cryptographic integrity.

## Procedure (one-time, ~15 minutes user-interactive)

### 1. Generate GPG key

    gpg --full-generate-key

Choose:
- Kind: `(1) RSA and RSA`
- Size: `4096` bits
- Expiration: `0` (never expires) or your preferred horizon
- Name + email: match your `git config user.name` and `git config user.email` exactly
- Passphrase: choose a strong passphrase you can remember (you will type it on every signed commit/tag)

### 2. Find your key ID

    gpg --list-secret-keys --keyid-format=long

Output looks like:

    sec   rsa4096/ABC123DEF456GHIJ 2026-04-28 [SC]

The `ABC123DEF456GHIJ` part is your key ID.

### 3. Configure git to use the key

    git config --global user.signingkey ABC123DEF456GHIJ
    git config --global commit.gpgsign true   # optional: sign every commit
    git config --global tag.gpgsign true      # optional: sign every new tag

### 4. Re-sign existing prevention-arch-v* tags

    bash tools/gpg-sign-tags.sh

This script re-signs every existing `prevention-arch-v*` tag at its current commit. Idempotent: safe to re-run.

### 5. Verify

    git tag -v prevention-arch-v6

Expected: `gpg: Good signature from "<your name> <your email>"`. If you see `Can't check signature: No public key`, your local GPG keyring is missing the public key (you regenerated it elsewhere); re-import or re-create.

## Future tags

After step 3 completes, future `git tag -a <name>` commands you run will need `-s` to be signed:

    git tag -s prevention-arch-v8 -m "..."

Or set `tag.gpgsign true` (step 3) so all annotated tags auto-sign.

## Recovery use case

If a remote force-push ever rewrites a `prevention-arch-vN` tag, the GPG signature will catch the tampering: `git tag -v <name>` will fail. Re-fetch + re-verify is the recovery surface.

## Status as of 2026-04-28

Tags `prevention-arch-v3`, `v4`, `v5`, `v6` exist as unsigned annotated tags. Run `tools/gpg-sign-tags.sh` after completing steps 1-3 to upgrade.
