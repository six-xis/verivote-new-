# VeriVote-ABP Threat Model V2

This threat model targets the Python primary backend in `apps/api_py`. The Node backend in `apps/api` is legacy demo infrastructure.

## Security Goals

- Cast ballots do not reveal plaintext vote choices to public observers.
- Public audit artifacts bind election, manifest, roots, tally, and audit bundle hashes.
- Duplicate voting, root replacement, tally replacement, and audit bundle tampering are detectable.
- Mock/demo verifier and encryption modes are clearly separated from production claims.

## Current Phase 4 Privacy Boundary

The current Python reference implementation introduces `SealedVotePackageV1` using demo AESGCM encryption. This protects the opening from public observers and the bulletin board in tests, but it is not the final production public-key tally encryption scheme.

The tally authority can decrypt sealed packages during tally/proof generation. Public observers and bulletin boards should only see ciphertext/package metadata and hashes, not `vote_vector`, `randomness`, or plaintext candidate choices.

Phase 4 also introduces demo credential issuance, `credential_commitment`,
`eligibility_root`, Merkle proofs, and `nullifier_hash`. Public observers can see
`credential_commitment`, Merkle proofs, `eligibility_root`, and cast `nullifier_hash`; they must
not see `credential_secret`.

In demo mode, the Python backend temporarily stores `credential_secret` to support test
issuance and demo nullifier derivation. Production should avoid backend custody of credential
secrets and should use an independent eligibility issuer plus client-side nullifier derivation.

Phase 5 / M6C introduces a real Circom/snarkjs build, prove, and verify pipeline for the
fixed `private_valid_vote_4_8` demo circuit. The mock verifier remains only for
test/development with mock mode enabled, and it is forbidden in competition/production.
The generated Powers of Tau and zkey are development-only unsafe artifacts, not production
trusted setup material.

The demo key or any future tally private key must not be placed in:

- sealed vote packages;
- audit bundles;
- public chain records;
- public response schemas.

`credential_secret` must not be placed in:

- bulletin-board responses;
- public credential lists;
- cast ballot records;
- audit public data;
- chain records.

## Threat Actors

### malicious voter

May replay requests, submit invalid vote vectors, overvote, undervote, or try to reuse credentials. Mitigations are eligibility roots, nullifier hashes, vote-vector validation, and later private valid vote proofs.

### malicious bulletin board

May delete, reorder, or replace cast records. Mitigations are receipt chains, commitment roots, nullifier roots, receipt roots, sealed package hashes, and audit bundle hashes.

### malicious aggregator

May selectively tally ballots, swap tally results, or reuse old proofs. Mitigation is the future batch tally bound proof binding roots, `tally_hash`, and `audit_bundle_hash`.

### malicious backend

May try to persist plaintext cast choices, expose sealed openings, or leak credential secrets. The ABP path must reject public cast records containing `candidate_id`, `vote_vector`, or `randomness`; challenge records are the only records allowed to reveal openings, and they must not count toward tally. Demo credential secrets are a migration risk and must not appear in public APIs.

### malicious chain submitter

May submit a valid proof with mismatched audit fields or use a mock verifier. The chain path must compare public signals with submitted audit fields before accepting a proof.

### malicious proof submitter

May try to submit a proof whose public signals bind a different election, eligibility root,
nullifier, or commitment. The backend rejects mismatched public signals before accepting a cast.
When real artifacts are configured, the Python wrapper calls `snarkjs groth16 verify`; when mock
mode is enabled, that mock result is not a security assumption.

### curious public observer

Can read bulletin board records, public credential commitments, eligibility roots, public audit bundles, and chain summaries. They must not be able to directly read cast vote vectors, randomness, or credential secrets from those artifacts.

## Out of Scope For Current Phase

- Strong coercion-resistance.
- Fully compromised voter devices.
- Vote buying or offline coercion.
- Production public-key tally encryption.
- Production eligibility issuer flow.
- Production trusted setup for private valid vote proof.
- Dynamic cast API generation of real private valid vote witnesses.
- Threshold tally authority.
- Large-scale denial-of-service resistance.
- Chain-level censorship or consensus failures.

The current sealed vote implementation is a demo/reference privacy layer for backend and audit-flow tests, not a final production voting privacy protocol.
