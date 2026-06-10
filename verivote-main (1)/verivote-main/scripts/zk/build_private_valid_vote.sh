#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
ARTIFACT_DIR="$ROOT_DIR/artifacts/zk/private_valid_vote"
CIRCUIT="$ROOT_DIR/circuits/private_valid_vote_4_8.circom"
NODE_MODULES="$ROOT_DIR/node_modules"
CIRCOMLIB_POSEIDON="$ROOT_DIR/node_modules/circomlib/circuits/poseidon.circom"
INPUT_GENERATOR="$ROOT_DIR/scripts/zk/generate_private_valid_vote_input.mjs"
PTAU_POWER="${PTAU_POWER:-15}"

if ! command -v circom >/dev/null 2>&1; then
  echo "Missing circom. Install Circom 2 and ensure 'circom' is on PATH." >&2
  exit 1
fi

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

if [[ ! -f "$CIRCOMLIB_POSEIDON" ]]; then
  echo "Missing circomlib Poseidon circuit at $CIRCOMLIB_POSEIDON" >&2
  echo "Install suggestion: pnpm add -D circomlib circomlibjs" >&2
  exit 1
fi
if [[ ! -f "$INPUT_GENERATOR" ]]; then
  echo "Missing input generator: $INPUT_GENERATOR" >&2
  exit 1
fi

mkdir -p "$ARTIFACT_DIR"

node "$INPUT_GENERATOR"

echo "Compiling private_valid_vote_4_8.circom..."
circom "$CIRCUIT" --r1cs --wasm --sym -l "$NODE_MODULES" -o "$ARTIFACT_DIR"

if [[ -f "$ARTIFACT_DIR/private_valid_vote_4_8.r1cs" ]]; then
  mv "$ARTIFACT_DIR/private_valid_vote_4_8.r1cs" "$ARTIFACT_DIR/private_valid_vote.r1cs"
fi
if [[ -f "$ARTIFACT_DIR/private_valid_vote_4_8.sym" ]]; then
  mv "$ARTIFACT_DIR/private_valid_vote_4_8.sym" "$ARTIFACT_DIR/private_valid_vote.sym"
fi
if [[ -d "$ARTIFACT_DIR/private_valid_vote_4_8_js" ]]; then
  rm -rf "$ARTIFACT_DIR/private_valid_vote_js"
  mv "$ARTIFACT_DIR/private_valid_vote_4_8_js" "$ARTIFACT_DIR/private_valid_vote_js"
fi

echo "DEV ONLY: generating an unsafe local Powers of Tau and Groth16 zkey."
echo "DEV ONLY: not for production or a competition final trusted setup."

"${SNARKJS[@]}" powersoftau new bn128 "$PTAU_POWER" "$ARTIFACT_DIR/pot${PTAU_POWER}_0000.ptau" -v
"${SNARKJS[@]}" powersoftau contribute \
  "$ARTIFACT_DIR/pot${PTAU_POWER}_0000.ptau" \
  "$ARTIFACT_DIR/pot${PTAU_POWER}_0001.ptau" \
  --name="VeriVote M6B dev unsafe contribution" \
  -e="verivote-m6b-dev-unsafe" \
  -v
"${SNARKJS[@]}" powersoftau prepare phase2 \
  "$ARTIFACT_DIR/pot${PTAU_POWER}_0001.ptau" \
  "$ARTIFACT_DIR/pot${PTAU_POWER}_final.ptau" \
  -v

"${SNARKJS[@]}" groth16 setup \
  "$ARTIFACT_DIR/private_valid_vote.r1cs" \
  "$ARTIFACT_DIR/pot${PTAU_POWER}_final.ptau" \
  "$ARTIFACT_DIR/private_valid_vote_0000.zkey"
"${SNARKJS[@]}" zkey contribute \
  "$ARTIFACT_DIR/private_valid_vote_0000.zkey" \
  "$ARTIFACT_DIR/private_valid_vote.zkey" \
  --name="VeriVote M6B dev unsafe zkey contribution" \
  -e="verivote-m6b-dev-unsafe-zkey" \
  -v
"${SNARKJS[@]}" zkey export verificationkey \
  "$ARTIFACT_DIR/private_valid_vote.zkey" \
  "$ARTIFACT_DIR/verification_key.json"

echo "Artifacts written to $ARTIFACT_DIR"
