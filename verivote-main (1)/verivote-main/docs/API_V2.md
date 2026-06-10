# VeriVote API V2

The Python/FastAPI backend in `apps/api_py` is the primary backend for ABP v2 work. The Node backend in `apps/api` is legacy.

## Current Baseline Endpoints

- `GET /health`
- `GET /api/v1/legacy/health`
- `GET /api/v2/health`
- `GET /api/v2/elections`
- `POST /api/v2/elections`
- `GET /api/v2/elections/{election_id}`
- `POST /api/v2/elections/{election_id}/candidates`
- `POST /api/v2/elections/{election_id}/users/demo-register`
- `POST /api/v2/elections/{election_id}/credentials/demo-issue`
- `GET /api/v2/elections/{election_id}/credentials/public`
- `POST /api/v2/elections/{election_id}/credentials/derive-nullifier`
- `POST /api/v2/elections/{election_id}/ballots/legacy-cast`
- `POST /api/v2/elections/{election_id}/vote`
- `POST /api/v2/elections/{election_id}/ballots/cast`
- `GET /api/v2/elections/{election_id}/bulletin-board`
- `GET /api/v2/elections/{election_id}/audit/report`
- `GET /api/v2/elections/{election_id}/result`
- `GET /api/v2/zk/private-valid-vote/status`
- `POST /api/v2/attacks/elections/{election_id}/tamper-commitment`
- `POST /api/v2/attacks/elections/{election_id}/inject-duplicate`

## ABP V2 Models

The Phase 1 model layer defines:

- `CandidateV2`
- `ElectionManifestV2`
- `CredentialV2`
- `DemoCredentialIssueResponse`
- `CastBallotRecordV2`
- `ChallengeBallotRecordV2`
- `AuditRootsV2`
- `BatchTallyPublicSignalsV2`
- `AuditBundleV2`

These models are defined in `apps/api_py/app/models/abp.py` and exposed through schema wrappers in `apps/api_py/app/schemas/abp.py`.

## Legacy Cast

`POST /api/v2/elections/{election_id}/ballots/legacy-cast` is a migration endpoint. It exists so the Python backend can keep a working health/basic-flow/attack-detection baseline while ABP v2 is built.

It is not the final privacy-preserving cast endpoint.

`POST /api/v2/elections/{election_id}/vote` is a frontend migration adapter over
the same baseline flow. Its response is sanitized for UI use and does not return
`candidate_id`, `vote_vector`, `randomness`, `credential_secret`, or a full
`sealed_vote_package`. M7 is still required before the frontend cast flow is
connected to a real private valid vote proof.

`GET /api/v2/elections` and `GET /api/v2/elections/{election_id}` are public
frontend support endpoints. They return election summaries/details and
candidates by public `id` only; they do not return credentials, sealed vote
packages, or cast ballot openings.

## ABP V2 Demo Credentials

`POST /api/v2/elections/{election_id}/credentials/demo-issue` issues one demo ABP v2
credential for an election.

Response body:

```json
{
  "credential_id": "credential_v2_1",
  "credential_secret": "...",
  "credential_commitment": "...",
  "eligibility_root": "...",
  "warning": "demo only credential secret; do not publish; not for production eligibility issuance"
}
```

`credential_secret` appears only in this demo issue response. It must not appear in the
bulletin board, audit public data, cast ballot records, or public credential list. In a
production design, credentials should be issued by an independent eligibility issuer and the
backend should not hold voter secrets.

`GET /api/v2/elections/{election_id}/credentials/public` returns the public credential set:

```json
{
  "eligibility_root": "...",
  "credentials": [
    {
      "credential_id": "credential_v2_1",
      "credential_commitment": "...",
      "eligibility_merkle_path": [
        {
          "sibling": "...",
          "position": "right"
        }
      ]
    }
  ]
}
```

This response never returns `credential_secret`.

`POST /api/v2/elections/{election_id}/credentials/derive-nullifier` is a demo/dev helper:

```json
{
  "credential_secret": "..."
}
```

Response:

```json
{
  "nullifier_hash": "...",
  "warning": "demo/dev helper only; production clients should derive the nullifier locally without sending the credential secret to the backend"
}
```

Production clients should derive `nullifier_hash` locally. This endpoint exists only to wire
Phase 4 tests and demos before the private valid vote proof is implemented.

## ABP V2 Cast

`POST /api/v2/elections/{election_id}/ballots/cast` is the Phase 3 ABP v2 cast endpoint.

Request body:

```json
{
  "commitment": "...",
  "nullifier_hash": "...",
  "sealed_vote_package": {
    "version": "sealed-vote-v1",
    "algorithm": "AESGCM-SHA256-DEMO",
    "ciphertext": "...",
    "nonce": "...",
    "key_id": "demo",
    "opening_hash": "...",
    "created_at": "2026-01-01T00:00:00Z"
  },
  "sealed_vote_package_hash": "...",
  "receipt_code": "...",
  "validity_proof_hash": "placeholder-proof-hash",
  "validity_proof": {
    "proof": {
      "pi_a": ["..."]
    },
    "public_signals": {
      "election_id_hash": "...",
      "eligibility_root": "...",
      "nullifier_hash": "...",
      "commitment": "...",
      "rule_hash": "..."
    },
    "proof_system": "mock-groth16",
    "artifact_hash": "...",
    "mock": true
  }
}
```

Response body:

```json
{
  "ballot_id": "cast_ballot_v2_1",
  "election_id_hash": "...",
  "commitment": "...",
  "nullifier_hash": "...",
  "sealed_vote_package_hash": "...",
  "validity_proof_hash": "placeholder-proof-hash",
  "receipt_code": "...",
  "receipt_chain_hash": "...",
  "status": "cast",
  "created_at": "2026-01-01T00:00:00Z"
}
```

The request, response, stored public record, and bulletin board must not expose:

- `candidate_id`
- `vote_vector`
- `randomness`

The response intentionally returns only `sealed_vote_package_hash`; it does not return the full `sealed_vote_package`.

Error conditions:

- election does not exist: `404`;
- empty `commitment`, `nullifier_hash`, `receipt_code`, or `sealed_vote_package_hash`: `400` or `422`;
- top-level `candidate_id`, `vote_vector`, or `randomness`: `422`;
- those plaintext fields inside `sealed_vote_package`: `422`;
- `sealed_vote_package_hash` mismatch: `400` or `422`;
- duplicate `nullifier_hash` within the same election: `409`.

`validity_proof_hash` is currently a migration placeholder boundary for the future private valid vote proof. M6A does not implement or claim a real ZK verifier.

`validity_proof` is optional during the migration window. If provided, the backend checks that `public_signals` bind the current election hash, current `eligibility_root`, request `nullifier_hash`, request `commitment`, and matching `rule_hash` when present. Mock proof verification is accepted only in test/development mock mode. When artifacts are present and mock mode is disabled, the Python wrapper calls the real snarkjs verifier. The proofless path remains for migration tests and should become invalid in M7.

`validity_proof.public_signals` must use this order:

0. `election_id_hash`
1. `eligibility_root`
2. `nullifier_hash`
3. `commitment`
4. `rule_hash`

`public_signals` must not include `vote_vector`, `randomness`, `candidate_id`, or `credential_secret`.

Challenge records use `ChallengeBallotRecordV2`; they may expose openings but must not be counted in tally.

## Bulletin Board

`GET /api/v2/elections/{election_id}/bulletin-board` returns:

```json
{
  "election_id": "election_1",
  "election_id_hash": "...",
  "manifest": {},
  "cast_ballots_public": [],
  "challenge_records": [],
  "roots": null
}
```

Each `cast_ballots_public` item contains the same public fields as `CastBallotResponseV2`. It does not contain the full `sealed_vote_package`, decrypted openings, `candidate_id`, `vote_vector`, or `randomness`.

The bulletin board manifest publicly includes `eligibility_root`. It does not include
`credential_secret`.

## Private Valid Vote ZK Status

`GET /api/v2/zk/private-valid-vote/status` returns:

```json
{
  "configured": true,
  "zk_profile": "poseidon-v1",
  "circuit": "private_valid_vote_4_8",
  "verifier_artifact_present": true,
  "snarkjs_available": true,
  "mock_mode": false,
  "real_verifier_available": true,
  "warning": "SHA reference hash and Poseidon circuit profile alignment is pending"
}
```

`verifier_artifact_present` is true when the configured `verification_key.json`
exists. The default artifact directory is
`artifacts/zk/private_valid_vote/`, configurable with
`VERIVOTE_ZK_PRIVATE_VALID_VOTE_ARTIFACTS_DIR`.

`snarkjs_available` checks the configured command, defaulting to
`pnpm exec snarkjs`. `real_verifier_available` is true only when both the
verification key and snarkjs are available.

Verifier priority:

1. If `zk_mock_mode=true`, mock verification is allowed only in `test` or
   `development`.
2. If `zk_mock_mode=false`, the real snarkjs verifier path is used.
3. `competition` and `production` never fall back to mock verification.

When mock mode is enabled in test/development, `warning` states that mock is not
a real proof. The warning also keeps the current M6B hash-profile caveat:
Python reference hashes are SHA256-to-BN254 while the real circuit profile is
  Poseidon.

The M6C scripts generate the current development artifacts with:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/zk/build_private_valid_vote.ps1
powershell -ExecutionPolicy Bypass -File scripts/zk/prove_private_valid_vote.ps1
powershell -ExecutionPolicy Bypass -File scripts/zk/verify_private_valid_vote.ps1
```

## Sealed Vote Package

`/ballots/cast` stores a sealed package shaped like:

```json
{
  "version": "sealed-vote-v1",
  "algorithm": "AESGCM-SHA256-DEMO",
  "ciphertext": "...",
  "nonce": "...",
  "key_id": "demo",
  "opening_hash": "...",
  "created_at": "2026-01-01T00:00:00Z"
}
```

The package must not contain plaintext `candidate_id`, `vote_vector`, or `randomness`.

`sealed_vote_package_hash` is computed as a canonical JSON hash of the sealed package and will be used to bind cast records into audit artifacts and later proof statements.

`legacy-cast` remains a migration endpoint and does not use this final ABP cast shape.

## Batch Tally Public Signal Order

The circuit and Solidity verifier path must use this stable order:

0. `election_id_hash`
1. `manifest_hash`
2. `commitment_root`
3. `nullifier_root`
4. `receipt_root`
5. `tally_hash`
6. `batch_index`
7. `batch_size`
