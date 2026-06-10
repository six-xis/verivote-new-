# VeriVote-ABP

Audit-Bound Partition Proof for privacy-preserving, publicly auditable electronic voting.

VeriVote-ABP is a research and competition prototype. It combines a Python/FastAPI primary backend, a React/Vite frontend, and a Circom/snarkjs/Groth16 `private_valid_vote` proof pipeline. The legacy Node/Express backend remains in `apps/api` for migration compatibility, but new backend work targets `apps/api_py`.

This repository is not production-ready and is not a final secure election system.

## Current Status

- M1 Python/FastAPI baseline is in place.
- M2 ABP v2 Pydantic models are defined.
- M3 `commitmentV2` and `sealedVotePackage` helpers exist.
- M4 ABP cast API exists at `/api/v2/elections/{election_id}/ballots/cast`.
- M5 `eligibilityRoot`, `credentialCommitment`, and `nullifierHash` demo helpers exist.
- M6A proof interface and mock guard are in place.
- M6B/M6C real `private_valid_vote` build/prove/verify pipeline passed.
- Frontend API access is configured for Python API v2 by default.

## Architecture

- `apps/api_py`: primary Python/FastAPI backend.
- `apps/web`: React/Vite frontend.
- `apps/api`: legacy Node/Express backend retained during migration.
- `circuits`: Circom circuits, including `private_valid_vote.circom`.
- `scripts/zk`: input generation and PowerShell/bash ZK scripts.
- `artifacts/zk/private_valid_vote`: development proof artifacts.
- `docs`: ABP protocol, threat model, roadmap, testing, and API notes.

## Frontend and Backend

The frontend reads one environment variable:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

If the variable is missing, the frontend defaults to `http://127.0.0.1:8000` and prefixes relative API requests with `/api/v2`. It no longer defaults to the legacy Node API port.

Run the Python backend:

```powershell
cd apps/api_py
python -m uvicorn app.main:create_app --factory --host 127.0.0.1 --port 8000 --log-level debug --access-log
```

Run the frontend:

```powershell
$env:VITE_API_BASE_URL="http://127.0.0.1:8000"
pnpm.cmd run dev:web
```

Open:

```text
http://localhost:5173
```

## API Overview

Health:

- `GET /health`
- `GET /api/v2/health`

Elections:

- `GET /api/v2/elections`
- `POST /api/v2/elections`
- `GET /api/v2/elections/{election_id}`
- `POST /api/v2/elections/{election_id}/candidates`

Credentials:

- `POST /api/v2/elections/{election_id}/users/demo-register`
- `POST /api/v2/elections/{election_id}/credentials/demo-issue`
- `GET /api/v2/elections/{election_id}/credentials/public`
- `POST /api/v2/elections/{election_id}/credentials/derive-nullifier`

Ballots:

- `POST /api/v2/elections/{election_id}/ballots/legacy-cast`
- `POST /api/v2/elections/{election_id}/vote`
- `POST /api/v2/elections/{election_id}/ballots/cast`
- `GET /api/v2/elections/{election_id}/bulletin-board`

Audit and ZK:

- `GET /api/v2/elections/{election_id}/audit/report`
- `GET /api/v2/elections/{election_id}/tally`
- `GET /api/v2/elections/{election_id}/result`
- `GET /api/v2/zk/private-valid-vote/status`

The `/vote` endpoint is a sanitized migration adapter over the legacy baseline flow. It does not return `candidate_id`, `vote_vector`, `randomness`, `credential_secret`, or a full sealed vote package. The final private proof cast integration is still planned for M7.

## ZK Status

The current real ZK pipeline state:

- `private_valid_vote.circom` exists.
- Circom/snarkjs/Groth16 build, prove, and verify passed.
- `snarkjs groth16 verify` returned OK.
- Artifacts are under `artifacts/zk/private_valid_vote/`.

Run the pipeline:

```powershell
node scripts/zk/generate_private_valid_vote_input.mjs
powershell -ExecutionPolicy Bypass -File scripts/zk/build_private_valid_vote.ps1
powershell -ExecutionPolicy Bypass -File scripts/zk/prove_private_valid_vote.ps1
powershell -ExecutionPolicy Bypass -File scripts/zk/verify_private_valid_vote.ps1
```

## Testing

Python API:

```powershell
cd apps/api_py
python -m pytest
python -m ruff check app
```

Repository root wrappers:

```powershell
pnpm.cmd run test:py-api
pnpm.cmd run lint:py-api
```

Frontend build:

```powershell
pnpm.cmd run build:web
```

There is currently no dedicated `lint:web` script or ESLint configuration.

## Current Limits

- Powers of Tau and zkey artifacts are development-only unsafe setup artifacts.
- Python SHA256 reference helpers and the Poseidon circuit profile are not fully unified.
- `legacy-cast` and `/vote` are migration-only paths.
- M7 real proof-backed cast API integration is not complete.
- Batch tally proof is not complete.
- On-chain bound verifier is not complete.
- Strong coercion resistance is outside the current security claim.
- Demo credential issuer and demo tally helpers are not production eligibility or key-management systems.

## Roadmap

- M7 cast API connects to the real private valid vote proof.
- M8 cast-or-challenge and receipt chain hardening.
- M9 `AuditBundleV2`.
- M10 batch tally reference checker.
- M11 `batch_tally_bound.circom`.
- M12 tally service with proof.
- M13 Solidity `BoundAudit`.
- M14 web3.py submit-chain integration.
- M15 adversarial corpus.
- M16 benchmark and ablation.
- M17 frontend ABP demo polish.
- M18 production guard and final report.

## Manual Smoke Checks

```powershell
curl.exe -v --max-time 5 http://127.0.0.1:8000/health
curl.exe -v --max-time 5 http://127.0.0.1:8000/api/v2/health
curl.exe -v --max-time 5 http://127.0.0.1:8000/api/v2/elections
curl.exe -v --max-time 5 http://127.0.0.1:8000/api/v2/zk/private-valid-vote/status
```
