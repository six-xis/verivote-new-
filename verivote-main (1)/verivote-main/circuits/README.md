# VeriVote Circuits

This directory contains demo Circom circuits for VeriVote.

## `valid_vote.circom`

`valid_vote.circom` proves that a fixed-length `voteVector` with four entries is a legal one-hot vote:

1. Every element is a bit: `vi * (vi - 1) = 0`.
2. The sum is exactly one: `v0 + v1 + v2 + v3 = 1`.

The current demo marks `voteVector` as a public input so the command-line verifier proves that this specific vector is legal. A later privacy-preserving integration should make the vote private and expose a commitment instead.

Run the demo from the repository root:

```bash
pnpm zk:demo
```

The demo requires:

1. `snarkjs`, installed through the workspace dev dependencies.
2. A Circom 2 compiler available as `circom` on `PATH`.

## `private_valid_vote.circom`

`private_valid_vote.circom` is the Phase 5 / M6B private valid vote circuit
source. It uses the ZK hash profile `poseidon-v1` through
`circomlib/circuits/poseidon.circom`.

Public signals are fixed to the M6A order:

0. `election_id_hash`
1. `eligibility_root`
2. `nullifier_hash`
3. `commitment`
4. `rule_hash`

Private inputs are:

- `vote_vector`
- `randomness`
- `credential_secret`
- `merkle_path_elements`
- `merkle_path_indices`

The circuit constrains the vote vector to be one-hot, derives the nullifier
from `election_id_hash` and `credential_secret`, checks eligibility membership
from a Poseidon credential commitment and Merkle path, and binds the public
commitment to the public header, private vote vector, and private randomness.

`private_valid_vote_4_8.circom` is a fixed demo instance with
`candidateCount = 4` and `depth = 8`. Real deployments can compile other
instances for different candidate counts and eligibility tree depths.

The files under `circuits/inputs/private_valid_vote.*.json` are placeholder
inputs until Poseidon-consistent values are generated with `circomlibjs` or an
equivalent helper. They must not be used as proof-success fixtures while
`_placeholder` is `true`.

Build/prove/verify scripts live under `scripts/zk/`. The build script uses a
local development-only unsafe trusted setup and must not be used for production
or a competition final trusted setup.
