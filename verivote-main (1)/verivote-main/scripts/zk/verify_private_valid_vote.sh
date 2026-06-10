#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
ARTIFACT_DIR="$ROOT_DIR/artifacts/zk/private_valid_vote"
VK="${1:-$ARTIFACT_DIR/verification_key.json}"
PUBLIC="${2:-$ARTIFACT_DIR/public.json}"
PROOF="${3:-$ARTIFACT_DIR/proof.json}"

if ! command -v snarkjs >/dev/null 2>&1; then
  if command -v pnpm >/dev/null 2>&1; then
    SNARKJS=(pnpm exec snarkjs)
  else
    echo "Missing snarkjs. Install with 'pnpm add -D snarkjs' or expose snarkjs on PATH." >&2
    exit 1
  fi
else
  SNARKJS=(snarkjs)
fi

for path in "$VK" "$PUBLIC" "$PROOF"; do
  if [[ ! -f "$path" ]]; then
    echo "Missing required file: $path" >&2
    exit 1
  fi
done

"${SNARKJS[@]}" groth16 verify "$VK" "$PUBLIC" "$PROOF"
