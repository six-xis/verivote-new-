# VeriVote-ABP

The active project lives in:

```text
verivote-main (1)/verivote-main
```

VeriVote-ABP is an Audit-Bound Partition Proof prototype for privacy-preserving, publicly auditable electronic voting. The current primary backend is Python/FastAPI (`apps/api_py`), the frontend is React/Vite (`apps/web`), and the real `private_valid_vote` Circom/snarkjs/Groth16 build-prove-verify pipeline has passed for the M6C milestone.

This is a research and competition prototype, not a production-ready election system.

## Quick Start

Run the Python backend:

```powershell
cd "C:\Users\23380\Desktop\verivote()\verivote-main (1)\verivote-main\apps\api_py"
python -m uvicorn app.main:create_app --factory --host 127.0.0.1 --port 8000 --log-level debug --access-log
```

Run the frontend:

```powershell
cd "C:\Users\23380\Desktop\verivote()\verivote-main (1)\verivote-main"
$env:VITE_API_BASE_URL="http://127.0.0.1:8000"
pnpm.cmd run dev:web
```

Open:

```text
http://localhost:5173
```

## Current M6C State

- M1 Python/FastAPI baseline complete.
- M2 ABP v2 models complete.
- M3 `commitmentV2` and `sealedVotePackage` helpers complete.
- M4 ABP cast API present.
- M5 `eligibilityRoot` and `nullifierHash` helpers present.
- M6A proof interface and mock guard present.
- M6B/M6C real `private_valid_vote` build/prove-verify pipeline passed.
- Frontend defaults to Python API v2 via `VITE_API_BASE_URL=http://127.0.0.1:8000`.

See `verivote-main (1)/verivote-main/README.md` for the full API, ZK, test, and roadmap notes.
