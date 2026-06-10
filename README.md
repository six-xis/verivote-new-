# VeriVote-ABP

**Audit-Bound Partition Proof for Privacy-Preserving, Publicly Auditable Electronic Voting**  
审计绑定分区计票证明：面向隐私保护、公开可审计电子投票的研究型系统原型。

> 当前实际工程目录是 `verivote-main (1)/verivote-main`。仓库根目录 README 用于 GitHub 首页展示；实际工程目录中的 README 也同步维护同一套最新说明。

## 项目简介

VeriVote-ABP 是 VeriVote 从早期 TypeScript/Express demo 演进而来的新版本。ABP 指 **Audit-Bound Partition Proof**，核心目标是把投票系统中的公开审计对象绑定到统一证明和审计材料中，降低 proof 复用、root 替换、tally 替换和审计包篡改风险。

本项目不是普通投票网站，而是一个面向信息安全竞赛和研究展示的安全系统原型。当前重点包括：

- 隐私保护的 cast ballot 数据流；
- 可公开验证的 bulletin board；
- election-scoped eligibility root；
- nullifier 防重复投票；
- sealed vote package；
- private valid vote 零知识合法性证明；
- FastAPI API v2；
- React/Vite 前端；
- Circom/snarkjs/Groth16 真实 proof pipeline。

当前主后端是 `apps/api_py` 中的 Python/FastAPI。`apps/api` 中的 Node/Express 后端已经降级为 legacy demo，不再作为新功能主开发对象。

本项目仍处于研究原型阶段，不能直接用于真实生产选举。

## 当前项目状态

截至 M6C，项目已经完成以下阶段。

### M1：Python/FastAPI backend baseline

已完成：

- `apps/api_py` Python/FastAPI 主后端；
- health endpoint；
- API v1/v2 路由结构；
- service/repository 分层；
- memory repository baseline；
- pytest 基线；
- ruff lint 基线；
- legacy Node/Express 后端保留。

### M2：ABP v2 models

已完成核心 Pydantic 模型：

- `ElectionManifestV2`
- `CandidateV2`
- `CredentialV2`
- `DemoCredentialIssueResponse`
- `CastBallotRecordV2`
- `ChallengeBallotRecordV2`
- `AuditRootsV2`
- `AuditBundleV2`
- `BatchTallyPublicSignalsV2`

重要边界：

- `CastBallotRecordV2` 禁止 `candidate_id`、`vote_vector`、`randomness`；
- `CredentialV2` 禁止 `credential_secret`；
- batch tally public signals 固定顺序已经文档化。

### M3：commitmentV2 + sealedVotePackage

已完成：

- canonical JSON；
- `field_hash_v2`；
- `commitmentV2`；
- one-hot vote vector 校验；
- `sealedVotePackage`；
- `sealedVotePackageHash`；
- sealed package 不公开 vote vector / randomness；
- Python hash helper 当前是 SHA256-to-BN254 reference/demo profile。

### M4：ABP cast API

已完成正式 ABP v2 cast endpoint：

```http
POST /api/v2/elections/{election_id}/ballots/cast
```

已完成：

- request/response 不暴露 `candidate_id`、`vote_vector`、`randomness`、`credential_secret`；
- sealed package hash 重算；
- nullifier 防重复；
- bulletin-board public projection；
- public bulletin-board 不返回完整 sealed package。

### M5：eligibilityRoot + nullifierHash

已完成：

- Merkle helper；
- `credential_secret` demo 发行；
- `credential_commitment`；
- `eligibility_root`；
- demo credential issuer；
- `nullifier_hash = H(election_id_hash, credential_secret)`；
- public credentials / bulletin-board / cast record 不返回 credential secret；
- 同一 election 下相同 nullifier 不能重复 cast。

### M6A：proof interface + mock guard

已完成：

- `PrivateValidVotePublicSignalsV1`；
- `PrivateValidVoteProofV1`；
- private valid vote public signals 固定顺序；
- public signals 禁止包含 `vote_vector`、`randomness`、`candidate_id`、`credential_secret`；
- mock verifier guard；
- `competition` / `production` 模式禁止 mock fallback。

Private valid vote public signals 顺序：

```text
0 election_id_hash
1 eligibility_root
2 nullifier_hash
3 commitment
4 rule_hash
```

### M6B/M6C：真实 private_valid_vote Circom/snarkjs/Groth16 pipeline

已完成：

- `circuits/private_valid_vote.circom`；
- `circuits/private_valid_vote_4_8.circom`；
- Poseidon input generator；
- PowerShell build/prove/verify scripts；
- 真实 build/prove/verify 已跑通；
- `snarkjs groth16 verify` 输出 `OK!`；
- Python wrapper 可以识别真实 verifier artifacts；
- artifacts 位于 `artifacts/zk/private_valid_vote/`；
- 当前 circuit demo 参数为 `candidateCount=4`、`merkleDepth=8`。

## 核心功能

### privacy-preserving cast ballot

正式 ABP cast public record 不包含明文投票选择：

- 不包含 `candidate_id`；
- 不包含 `vote_vector`；
- 不包含 `randomness`；
- 不包含 `credential_secret`。

### sealedVotePackage

cast 阶段保存加密封装后的投票 opening。public response 和 bulletin-board 默认只返回 `sealed_vote_package_hash`，不返回完整 sealed package。

### eligibilityRoot

系统使用 `credential_commitment` 构建 election-scoped eligibility Merkle root。当前 demo issuer 可以生成 credential secret 和 public commitment，但生产设计中 credential secret 不应由普通后端长期持有。

### nullifierHash

nullifier 用于防重复投票：

```text
nullifier_hash = H(election_id_hash, credential_secret)
```

同一 election 中相同 nullifier 只能 cast 一次。

### bulletin-board public projection

bulletin-board 只公开可审计字段，例如 commitment、nullifier hash、sealed package hash、receipt chain hash、proof metadata，不公开投票 opening 和 voter secret。

### private valid vote proof

当前已完成真实 Circom/snarkjs/Groth16 最小 pipeline。proof public signals 绑定 election、eligibility root、nullifier、commitment 和 rule hash；private witness 中包含 vote vector、randomness、credential secret 和 Merkle path。

### Python real verifier wrapper

Python 后端可以检测真实 verifier artifacts，并通过 ZK status API 报告：

- verifier artifact 是否存在；
- snarkjs 是否可用；
- mock mode 是否启用；
- real verifier 是否可用。

## 架构说明

主要目录：

- `apps/api_py`：当前主后端，Python/FastAPI；
- `apps/api`：legacy Node/Express demo；
- `apps/web`：React/Vite 前端；
- `circuits`：Circom 电路；
- `scripts/zk`：ZK input/build/prove/verify 脚本；
- `artifacts/zk/private_valid_vote`：当前 private valid vote proof artifacts；
- `docs`：协议、API、ZK、威胁模型、测试和路线图文档；
- `contracts`：Solidity/Hardhat 链上审计相关代码。

目录结构：

```text
apps/
  api_py/
  api/
  web/
circuits/
scripts/
  zk/
artifacts/
  zk/
    private_valid_vote/
docs/
contracts/
packages/
tests/
package.json
pnpm-workspace.yaml
```

## 环境要求

推荐环境：

- Windows PowerShell；
- Node.js 20+；
- pnpm 10+；
- Python 3.11+；
- FastAPI / uvicorn；
- Circom 2.2+；
- snarkjs 0.7+；
- circomlib；
- circomlibjs；
- Rust / cargo，用于安装 Circom。

## 安装依赖

在实际工程目录运行：

```powershell
cd "C:\Users\23380\Desktop\verivote()\verivote-main (1)\verivote-main"
pnpm.cmd install
```

安装 Python 后端开发依赖：

```powershell
cd apps/api_py
python -m pip install -e ".[dev]"
cd ..\..
```

安装 ZK 依赖：

```powershell
pnpm.cmd add -D snarkjs circomlib circomlibjs
```

如果需要安装到 workspace root：

```powershell
pnpm.cmd add -Dw snarkjs circomlib circomlibjs
```

## 启动后端

绝对路径版本：

```powershell
cd "C:\Users\23380\Desktop\verivote()\verivote-main (1)\verivote-main\apps\api_py"
python -m uvicorn app.main:create_app --factory --host 127.0.0.1 --port 8000 --log-level debug --access-log
```

相对路径版本：

```powershell
cd apps/api_py
python -m uvicorn app.main:create_app --factory --host 127.0.0.1 --port 8000 --log-level debug --access-log
```

健康检查：

```powershell
curl.exe -v --max-time 5 http://127.0.0.1:8000/health
curl.exe -v --max-time 5 http://127.0.0.1:8000/api/v2/health
curl.exe -v --max-time 5 http://127.0.0.1:8000/docs
```

## 启动前端

另开一个 PowerShell 窗口，保持后端窗口不要关闭：

```powershell
cd "C:\Users\23380\Desktop\verivote()\verivote-main (1)\verivote-main"
$env:VITE_API_BASE_URL="http://127.0.0.1:8000"
pnpm.cmd run dev:web
```

浏览器访问：

```text
http://localhost:5173
```

说明：

- 前端需要连接 Python API；
- `VITE_API_BASE_URL` 默认应指向 `http://127.0.0.1:8000`；
- 如果后端未启动，前端会出现连接错误；
- 当前 memory repository 重启后数据会丢失，首页可能显示空 election list。

## 运行测试

Python API：

```powershell
cd apps/api_py
python -m pytest
python -m ruff check app
cd ..\..
```

根目录 wrapper：

```powershell
pnpm.cmd run test:py-api
pnpm.cmd run lint:py-api
```

legacy / workspace targeted tests：

```powershell
pnpm.cmd run test:api
pnpm.cmd run test:crypto
pnpm.cmd run test:zk
pnpm.cmd run test:contract
```

前端构建检查：

```powershell
pnpm.cmd run build:web
```

当前没有独立的 `lint:web` script；不要把不存在的 lint 命令伪装成通过。

## 运行 ZK pipeline

生成 Poseidon-consistent inputs：

```powershell
node scripts/zk/generate_private_valid_vote_input.mjs
```

build/prove/verify：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/zk/build_private_valid_vote.ps1
powershell -ExecutionPolicy Bypass -File scripts/zk/prove_private_valid_vote.ps1
powershell -ExecutionPolicy Bypass -File scripts/zk/verify_private_valid_vote.ps1
```

成功时：

- build 生成 `.r1cs`、`.wasm` 或 witness JS 目录、`.zkey`、`verification_key.json`；
- prove 生成 `witness.wtns`、`proof.json`、`public.json`；
- verify 输出 `snarkJS: OK!`。

## API Overview

Health：

```http
GET /health
GET /api/v2/health
```

Election：

```http
POST /api/v2/elections
GET  /api/v2/elections
GET  /api/v2/elections/{election_id}
POST /api/v2/elections/{election_id}/candidates
```

Credentials：

```http
POST /api/v2/elections/{election_id}/credentials/demo-issue
GET  /api/v2/elections/{election_id}/credentials/public
POST /api/v2/elections/{election_id}/credentials/derive-nullifier
```

Ballots：

```http
POST /api/v2/elections/{election_id}/ballots/legacy-cast
POST /api/v2/elections/{election_id}/ballots/cast
```

Bulletin board：

```http
GET /api/v2/elections/{election_id}/bulletin-board
```

ZK status：

```http
GET /api/v2/zk/private-valid-vote/status
```

## 安全边界

当前已经明确区分 completed、demo/reference、unsafe 和 pending 内容。

已完成的安全边界：

- cast public record 不包含 `candidate_id`；
- cast public record 不包含 `vote_vector`；
- cast public record 不包含 `randomness`；
- public credentials 不包含 `credential_secret`；
- bulletin-board 不返回 sealed package 全量内容；
- mock verifier 不能用于 production / competition；
- true private valid vote proof 已经可以 build/prove/verify；
- nullifier 防重复 cast 已实现。

重要说明：

- demo credential issuer 只用于开发和演示；
- `legacy-cast` 只用于迁移期 baseline；
- proofless cast path 不应被解释为最终安全 cast 流程。

## 当前限制

当前仍然 pending / demo / unsafe 的内容：

- 本地 Powers of Tau / zkey 是 development unsafe setup；
- Python SHA256-to-BN254 reference profile 与 Circom Poseidon profile 尚未完全统一；
- proofless `/ballots/cast` path 仍是 migration-only；
- M7 real-proof cast API 尚未完成；
- sealed package opening 与 proof witness 的动态绑定仍待 M7/M8 完善；
- batch tally proof 尚未完成；
- Solidity on-chain verifier 尚未完成；
- web3.py submit-chain 尚未完成；
- adversarial corpus / benchmark / ablation 尚未完成；
- coercion-resistance 不在当前版本安全声明范围内；
- 项目不能直接用于真实生产选举。

## Roadmap

后续计划：

- M7：cast API 接入真实 private valid vote proof；
- M8：cast-or-challenge + receipt chain 完整化；
- M9：AuditBundleV2 + offline verifier；
- M10：batch tally reference checker；
- M11：`batch_tally_bound.circom`；
- M12：tally service with proof；
- M13：Solidity BoundAudit；
- M14：Python web3.py submit-chain；
- M15：adversarial election corpus；
- M16：RQ benchmark / ablation；
- M17：frontend ABP v2 demo polish；
- M18：production guard and final report。

## 相关文档

建议阅读：

- `docs/VERIVOTE_ABP_SPEC.md`
- `docs/API_V2.md`
- `docs/ZK_PRIVATE_VALID_VOTE.md`
- `docs/THREAT_MODEL_V2.md`
- `docs/TESTING.md`
- `docs/PY_BACKEND_MIGRATION.md`
- `scripts/zk/README.md`
- `circuits/README.md`

## License

License is not finalized yet. Add a LICENSE file before public reuse.
