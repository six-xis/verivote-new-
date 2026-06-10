# VeriVote Testing Guide

The primary backend test target is now `apps/api_py`, using pytest and httpx. The Node API remains a legacy baseline during the Python migration.

## Install Python Backend Dependencies

```bash
cd apps/api_py
python -m pip install -e .[dev]
```

## Run Python API Tests

From `apps/api_py`:

```bash
python -m pytest
```

From the repository root:

```bash
pnpm run test:py-api
```

On Windows PowerShell, if `pnpm.ps1` is blocked by the execution policy, use:

```bash
pnpm.cmd run test:py-api
```

## Run Ruff

From `apps/api_py`:

```bash
python -m ruff check app
```

From the repository root:

```bash
pnpm run lint:py-api
```

On Windows PowerShell, if `pnpm.ps1` is blocked by the execution policy, use:

```bash
pnpm.cmd run lint:py-api
```

## Targeted Migration Commands

During the Python migration, prefer targeted checks:

```bash
cd apps/api_py && python -m pytest
cd apps/api_py && python -m ruff check app
pnpm.cmd run test:py-api
pnpm.cmd run lint:py-api
pnpm.cmd run build:web
```

The root `pnpm test` aggregation can time out in the current Windows/Vitest migration environment. If that happens, run the targeted Python commands above and the legacy Node subcommands individually instead of reporting a false aggregate pass.

There is currently no dedicated `lint:web` script or ESLint configuration. Use
`pnpm.cmd run build:web` for the React/Vite TypeScript build check until a real
frontend linter is added.

## Current Python Test Layers

- `test_health.py`: health and legacy health.
- `test_basic_flow.py`: election, candidate, demo credential, legacy cast, duplicate reject, audit report.
- `test_attack_detection.py`: normal audit, tamper commitment, inject duplicate.
- `test_abp_models.py`: ABP v2 Pydantic privacy and public signal models.
- `test_hash_utils.py`: canonical JSON and reference hash helpers.
- `test_commitment_v2.py`: vote vector validation and reference commitment.
- `test_sealed_vote.py`: sealed vote package and sealed package hash.
- `test_abp_cast_ballot.py`: Phase 3 ABP v2 cast API, public bulletin board, nullifier duplicate rejection, and receipt chain reference hash.
- `test_eligibility.py`: Phase 4 credential commitment, eligibility root, Merkle proof, and nullifier reference helpers.
- `test_eligibility_api.py`: Phase 4 demo credential issuer, public credentials, demo nullifier helper, bulletin-board privacy, and `/ballots/cast` integration.
- `test_private_valid_vote_interface.py`: Phase 5 proof public signal schema, mock verifier guard, and ZK status endpoint.
- `test_private_valid_vote_real_wrapper.py`: Phase 5 / M6C real verifier artifact detection, status fields, no mock fallback in competition/production, proof schema private-field rejection, and real snarkjs verify behavior.
- `test_abp_cast_with_proof.py`: Phase 5 `/ballots/cast` proof binding checks and mock proof integration.
- `test_frontend_v2_integration.py`: frontend-facing Python API v2 list/detail, development CORS, and sanitized migration vote response.

## ZK Private Valid Vote Commands

The M6C circuit scripts require:

- Circom 2 available as `circom`.
- `snarkjs` available directly or through `pnpm.cmd exec snarkjs`.
- `circomlib` installed under `node_modules/circomlib`.
- `circomlibjs` available for Poseidon input generation.

If `circomlib` is missing:

```bash
pnpm add -D circomlib circomlibjs
```

Generate Poseidon-consistent inputs:

```bash
node scripts/zk/generate_private_valid_vote_input.mjs
```

Build the fixed 4-candidate, depth-8 demo circuit:

```bash
bash scripts/zk/build_private_valid_vote.sh
```

Generate proof/public artifacts:

```bash
bash scripts/zk/prove_private_valid_vote.sh
```

Verify artifacts:

```bash
bash scripts/zk/verify_private_valid_vote.sh
```

The build script writes to `artifacts/zk/private_valid_vote/` and uses a
development-only unsafe trusted setup. It is not for production and not for a
competition final trusted setup.

The generated JSON inputs under `circuits/inputs/` are Poseidon-consistent with
`circuits/private_valid_vote.circom`.

The Python test
`app/tests/test_private_valid_vote_real_wrapper.py::test_real_verify_runs_when_snarkjs_and_artifacts_are_present`
skips when `verification_key.json`, `proof.json`, `public.json`, or `snarkjs`
are missing. After real artifacts exist, run it with:

```bash
cd apps/api_py
python -m pytest app/tests/test_private_valid_vote_real_wrapper.py -k real_verify
```

Windows PowerShell commands:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/zk/build_private_valid_vote.ps1
powershell -ExecutionPolicy Bypass -File scripts/zk/prove_private_valid_vote.ps1
powershell -ExecutionPolicy Bypass -File scripts/zk/verify_private_valid_vote.ps1
```

## Future Test Layers

- unit: crypto/hash/merkle/receipt/nullifier.
- api: FastAPI route and service integration.
- zk: proof adapter and circuit smoke tests.
- contract: on-chain bound audit verifier.
- adversarial: root, tally, audit bundle, and proof reuse attack corpus.
- benchmark: RQ performance evaluation.

`legacy-cast` is a migration simple endpoint. It is not the final ABP privacy-preserving cast API.
