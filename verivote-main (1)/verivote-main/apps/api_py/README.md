# VeriVote Python API

`apps/api_py` is the primary backend path for future VeriVote-ABP work. The existing Node/Express backend in `apps/api` is kept as a legacy demo backend and should not be used as the main target for new backend features.

## Install

```bash
cd apps/api_py
python -m pip install -e .[dev]
```

## Run

```bash
python -m uvicorn app.main:create_app --factory --reload
```

## Test

```bash
python -m pytest
python -m ruff check app
```

The current `/api/v2/elections/{election_id}/ballots/legacy-cast` endpoint is a transitional baseline endpoint. It is not the final private ABP cast endpoint.

