#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
ARTIFACT_DIR="$ROOT_DIR/artifacts/zk/private_valid_vote"
INPUT_JSON="${1:-$ROOT_DIR/circuits/inputs/private_valid_vote.valid.json}"
INPUT_GENERATOR="$ROOT_DIR/scripts/zk/generate_private_valid_vote_input.mjs"
WITNESS_JS="$ARTIFACT_DIR/private_valid_vote_js/generate_witness.js"
WASM="$ARTIFACT_DIR/private_valid_vote_js/private_valid_vote_4_8.wasm"
WITNESS="$ARTIFACT_DIR/witness.wtns"
PROOF="$ARTIFACT_DIR/proof.json"
PUBLIC="$ARTIFACT_DIR/public.json"

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

if [[ ! -f "$WITNESS_JS" || ! -f "$WASM" || ! -f "$ARTIFACT_DIR/private_valid_vote.zkey" ]]; then
  echo "Missing build artifacts. Run scripts/zk/build_private_valid_vote.sh first." >&2
  exit 1
fi

if [[ ! -f "$INPUT_GENERATOR" ]]; then
  echo "Missing input generator: $INPUT_GENERATOR" >&2
  exit 1
fi

node "$INPUT_GENERATOR"

if grep -qi '"_placeholder"[[:space:]]*:[[:space:]]*true' "$INPUT_JSON"; then
  echo "Input file is marked placeholder and is not a Poseidon-valid witness." >&2
  echo "Regenerate inputs after installing circomlib/circomlibjs before proving." >&2
  exit 1
fi

node "$WITNESS_JS" "$WASM" "$INPUT_JSON" "$WITNESS"
"${SNARKJS[@]}" groth16 prove \
  "$ARTIFACT_DIR/private_valid_vote.zkey" \
  "$WITNESS" \
  "$PROOF" \
  "$PUBLIC"

echo "Proof written to $PROOF"
echo "Public signals written to $PUBLIC"
