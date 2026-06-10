# ZK Scripts

These scripts are the M6C reproducible path for the fixed
`private_valid_vote_4_8` demo circuit.

## Environment

Required tools:

- Circom 2 on `PATH` as `circom`.
- `snarkjs`, either on `PATH` or available through `pnpm.cmd exec snarkjs` on Windows.
- `circomlib` installed at `node_modules/circomlib`.
- `circomlibjs` for Poseidon-consistent input generation.

Current install suggestion when `circomlib` is missing:

```bash
pnpm add -D circomlib circomlibjs
```

The circuit imports Poseidon as `circomlib/circuits/poseidon.circom`; build
scripts pass `-l node_modules` to `circom`.

## Generate Inputs

```bash
node scripts/zk/generate_private_valid_vote_input.mjs
```

This writes Poseidon-consistent inputs:

- `circuits/inputs/private_valid_vote.valid.json`
- `circuits/inputs/private_valid_vote.invalid_overvote.json`
- `circuits/inputs/private_valid_vote.invalid_membership.json`
- `artifacts/zk/private_valid_vote/public_signals_expected.json`

## Build

```bash
bash scripts/zk/build_private_valid_vote.sh
```

Windows PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/zk/build_private_valid_vote.ps1
```

The build script writes to `artifacts/zk/private_valid_vote/`:

- `private_valid_vote.r1cs`
- `private_valid_vote.sym`
- `private_valid_vote_js/`
- `private_valid_vote_0000.zkey`
- `private_valid_vote.zkey`
- `verification_key.json`

The setup is explicitly DEV ONLY. It generates a local unsafe Powers of Tau and
zkey contribution. It is not for production and not for a competition final
trusted setup.

## Prove

```bash
bash scripts/zk/prove_private_valid_vote.sh
```

Windows PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/zk/prove_private_valid_vote.ps1
```

The default input is `circuits/inputs/private_valid_vote.valid.json`. The script
regenerates Poseidon-consistent inputs before witness generation.

Expected outputs:

- `witness.wtns`
- `proof.json`
- `public.json`

## Verify

```bash
bash scripts/zk/verify_private_valid_vote.sh
```

Windows PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/zk/verify_private_valid_vote.ps1
```

This calls:

```bash
snarkjs groth16 verify verification_key.json public.json proof.json
```

The verifier wrapper in `apps/api_py/app/zk/private_valid_vote.py` uses the same
`verification_key.json` artifact and converts
`PrivateValidVotePublicSignalsV1.as_ordered_list()` into snarkjs `public.json`
format.
