# -
投票
# VeriVote

隐私保护可验证电子投票与审计平台

## 1. 项目简介

VeriVote 是一个面向高校、社团、企业内部投票等低信任组织场景的隐私保护可验证电子投票系统。

它不是一个简单投票网站，而是围绕投票主流程、公开验证、聚合审计、链上留痕和 ZK 合法性证明构建的可验证审计平台。当前系统把以下能力放在一个可运行、可演示、可继续扩展的 TypeScript 工程中：

- 投票主流程
- `commitment` / `receiptCode`
- `receipt chain`
- 公告板 Bulletin Board
- Merkle Root / Merkle Proof
- 聚合器 Aggregator
- 审计报告
- 异常 / 攻击检测
- Hardhat 链上审计
- Benchmark 性能评估
- Mock / Real ZK 合法性证明
- cast-or-challenge 挑战审计

VeriVote 的定位是比赛原型与研究型工程实现：优先把可验证投票的关键机制做成可以实际操作、可以解释、可以被审计的系统，而不是声称完整复现任何一篇论文或生产级电子投票系统。

## 2. 项目当前状态

当前已经完成：

- TypeScript monorepo 项目结构
- React / Vite 前端
- Node.js / Express API 后端
- 投票端 / 审计管理端双门户 UI
- 创建投票
- 添加候选人
- 用户注册
- 投票
- 回执查询
- 查看结果
- `commitment` / `receiptCode`
- `receipt chain` 连续性验证
- 公告板
- Merkle Root / Merkle Proof
- 聚合器
- 审计报告
- 异常 / 攻击检测实验室
- Hardhat 智能合约链上审计
- Benchmark 性能评估页面
- Mock ZK validity proof
- Real Groth16 ZK proof
- cast-or-challenge 挑战审计

## 3. 双门户设计

当前前端 UI 已整理成两个入口：投票端和审计管理端。这样可以让普通用户先看到简单投票流程，也让评委、审计员和开发者集中查看安全机制、密码学验证和工程审计能力。

### 投票端 Voter Portal

面向普通投票用户，包含：

- 用户注册 / 身份登记
- 投票
- 回执查询
- 查看结果
- Merkle 验证 / 我的验证

特点：

- 低门槛
- 简洁
- 面向普通用户
- 不暴露过多密码学细节

### 审计管理端 Admin & Audit Console

面向管理员、审计员、评委和开发者，包含：

- 创建投票
- 用户管理
- 公告板
- 聚合器
- 审计报告
- 异常 / 攻击检测
- 链上审计
- ZK 验证
- 性能评估
- 挑战审计

特点：

- 展示安全机制
- 展示密码学能力
- 展示审计流程
- 展示攻击检测和性能数据

## 4. 与三篇论文的关系

VeriVote 采用“论文机制融合 + 工程系统实现”的路线，并不是对三篇论文的逐字复现。项目会持续区分三类内容：

- 论文原版机制
- 当前工程实现
- 后续增强方向

### 613 / Haechi 方向

当前项目吸收：

- `voteVector`
- `commitment`
- `receiptCode`
- `receipt chain`
- Bulletin Board
- cast-or-challenge
- challenge opening verification
- tally consistency 思想

当前实现边界：

- 主流程仍使用 SHA-256 风格的 hash commitment。
- Pedersen-style vector commitment 将作为后续增强模块，不直接替换当前主流程。
- 当前 cast-or-challenge 是工程化演示，用于展示挑战审计思想，不是完整 Haechi 复现。

### 565 / Zeeperio 方向

当前项目吸收：

- public audit
- `proofHash` / `auditHash`
- 链上审计摘要
- Hardhat smart contract audit
- Real Groth16 ZK proof

当前实现边界：

- 当前 Real ZK 证明的是单张 `voteVector` 的 one-hot 合法性。
- 尚未实现完整 tally correctness proof。
- 尚未实现链上 ZK verifier。
- 链上审计保存的是摘要，不是明文选票。

### 545 / Aggios 方向

当前项目吸收：

- Aggregator
- `voteTokenHash`
- duplicate detection
- invalid vote detection
- batch tally
- audit report

当前实现边界：

- 当前 Aggregator 是工程化聚合审计模块。
- 尚未实现完整 Extended Partition Argument。
- 尚未实现完整密码学聚合证明。

## 5. 与朋友项目的融合关系

朋友项目是一个偏 `613 / Haechi` 的 Python 原型，包含：

- `prepare -> cast/challenge`
- Pedersen 风格向量承诺
- confirmation code chain
- public election record
- verifier
- security tests
- Zeeperio-style artifact export

VeriVote 没有直接复制朋友项目代码，而是吸收机制思想并用 TypeScript 重写。这样可以保持当前 React / Vite / Express / Circom / Hardhat 架构一致，也避免把参考原型的 Python 数据模型直接混入主项目。

当前已融合：

- cast-or-challenge 挑战审计
- receipt chain / confirmation code chain 思想
- 双门户 UI 结构

后续计划融合：

- Pedersen-style commitment 实验模块
- `SECURITY_TESTS.md` 安全测试矩阵
- Zeeperio-style artifact export

## 6. 核心技术亮点

### 1. 多层可验证审计

- `receipt chain` 验证正式投票记录连续性。
- Merkle proof 验证单票包含性。
- Aggregator 验证聚合统计一致性。
- Hardhat 链上审计锚定最终摘要。

### 2. ZK 合法性证明

- Mock 模式用于快速演示。
- Real 模式基于 Circom / snarkjs / Groth16。
- 当前证明 `voteVector` 是 one-hot 向量。
- 合法票通过，非法票失败。

### 3. cast-or-challenge 挑战审计

- prepare pending ballot。
- cast 后计入正式投票。
- challenge 后公开 opening，不计入 tally。
- 用于证明 commitment 按用户选择生成。

### 4. 聚合器审计

- `voteTokenHash`
- `duplicateVotes`
- `invalidVotes`
- tally consistency
- `auditHash`

### 5. 链上审计

- 提交 `merkleRoot`、`commitmentRoot`、`receiptRoot`、`auditHash`、`tallyHash`。
- 展示 `transactionHash` 和 `contractAddress`。
- 支持本地 Hardhat 链验证。

### 6. 性能评估

- benchmark 脚本。
- 性能评估页面。
- 100 / 1000 / 5000 / 10000 votes 测试。

## 7. 技术栈

- TypeScript
- React
- Vite
- Node.js API / Express
- pnpm workspace
- Circom 2
- snarkjs
- Groth16
- Hardhat
- Solidity
- PowerShell / Windows 本地开发环境

## 8. 项目结构

主要目录：

- `apps/api`：后端 API。
- `apps/web`：前端 Web。
- `packages/crypto`：哈希、commitment、Merkle、receipt chain 等工具。
- `packages/shared`：前后端共享 TypeScript 类型。
- `packages/zk`：Mock / Real ZK proof adapter。
- `contracts`：Hardhat / Solidity 链上审计合约。
- `circuits`：Circom 电路。
- `scripts`：benchmark、ZK setup、ZK demo 等脚本。
- `docs`：项目文档、论文映射、ZK、benchmark、融合路线等。

```text
verivote/
├─ apps/
│  ├─ api/
│  └─ web/
├─ packages/
│  ├─ crypto/
│  ├─ shared/
│  └─ zk/
├─ contracts/
├─ circuits/
├─ scripts/
├─ docs/
├─ package.json
├─ pnpm-workspace.yaml
└─ tsconfig.base.json
```

## 9. 快速开始

安装依赖：

```bash
pnpm install
```

启动后端：

```bash
pnpm dev:api
```

启动前端：

```bash
pnpm dev:web -- --port 18340
```

访问：

```text
http://localhost:18340
```

说明：

- 后端默认端口是 `3001`。
- 前端建议使用 `18340`。
- 如果 Vite 自动切换端口，请以终端实际输出为准。

健康检查：

```bash
curl http://localhost:3001/health
```

## 10. 常用验证命令

```bash
pnpm typecheck
pnpm build
pnpm benchmark
pnpm zk:setup
pnpm zk:demo
pnpm contract:compile
pnpm contract:test
```

## 11. ZK 使用说明

VeriVote 当前 ZK 模块用于证明单张 `voteVector` 是合法 one-hot 向量：每个元素为 `0/1`，且所有元素之和为 `1`。

### Mock ZK

Mock ZK 无需 Circom，也无需本地 ZK artifacts。启动 API 和 Web 后，在前端 `ZK 验证` 页面选择：

```text
Mock ZK Validity Proof
```

Mock proof 会检查 one-hot 规则，但它不是密码学意义上的零知识证明，主要用于快速演示接口、失败路径和前端流程。

### Real Groth16 ZK

Real 模式需要先安装 Circom 2，并确保命令行可以执行：

```bash
circom --version
```

生成本地 ZK artifacts：

```bash
pnpm zk:setup
```

运行命令行 demo：

```bash
pnpm zk:demo
```

再启动：

```bash
pnpm dev:api
pnpm dev:web -- --port 18340
```

在前端选择：

```text
Real Groth16 ZK Proof
```

当前 Real Groth16 电路位于 `circuits/valid_vote.circom`，约束固定长度为 4 的 `voteVector`：

```text
vi * (vi - 1) = 0
v0 + v1 + v2 + v3 = 1
```

说明：当前 Real ZK 证明的是 `voteVector` one-hot 合法性，不是完整 tally proof，也没有生成或部署 Solidity verifier。

## 12. 链上审计说明

系统支持两种链上审计模式。

### Mock Chain Audit

Mock Chain Audit 可以直接在页面使用，用于快速演示链上审计摘要的提交和查询流程，不需要启动本地链。

### Hardhat Audit

准备 Hardhat 合约和本地链：

```bash
pnpm contract:compile
pnpm contract:test
pnpm contract:node
pnpm contract:deploy
```

然后根据部署输出配置 API 环境变量：

```bash
BLOCKCHAIN_AUDIT_MODE=hardhat
HARDHAT_RPC_URL=http://127.0.0.1:8545
AUDIT_CONTRACT_ADDRESS=部署输出的合约地址
```

再启动 API 和 Web：

```bash
pnpm dev:api
pnpm dev:web -- --port 18340
```

说明：

- 当前是本地 Hardhat 链，不是主网部署。
- 链上审计提交的是 `merkleRoot`、`commitmentRoot`、`receiptRoot`、`auditHash`、`tallyHash` 等摘要。
- 不会上链明文选票，也不等同于完整 zk-SNARK 链上 verifier。

## 13. Benchmark 性能评估

运行：

```bash
pnpm benchmark
```

会生成或更新：

- `benchmark-results.json`
- `benchmark-results.csv`
- `docs/BENCHMARK.md`

前端性能评估页面展示：

- `totalMs` 趋势
- 模块耗时对比
- 100 / 1000 / 5000 / 10000 votes 测试结果

当前 benchmark 主要覆盖本地内存流程，包括 commitment 生成、Merkle Root 构建、Merkle proof 抽样生成与验证、聚合器统计和审计哈希生成。它不包含 API、Web、智能合约链上交易或 ZK proof 的真实耗时。

## 14. 当前边界

需要明确的是，VeriVote 仍是比赛原型和工程验证项目，当前边界包括：

- 当前后端默认仍是内存模式，可通过 `VERIVOTE_PERSISTENCE=sqlite` 切换到 SQLite 持久化。
- Real ZK 已支持 **单票合法性** 和 **批次计票正确性 (8x4)** 两个电路。更大批次和链上 Solidity verifier 仍待办。
- Pedersen-style commitment 作为实验模块提供（`/crypto/pedersen/*`），不替换主流程的 SHA-256 承诺。
- `zk-artifacts/` 不提交到 Git，需要本地运行 `pnpm zk:setup` 生成（含 valid_vote + tally_correctness）。
- Hardhat 链上审计是本地测试链，不是主网部署。
- 异常 / 攻击检测模块用于审计验证和防御演示，不用于真实攻击。
- 当前 Aggregator 是工程化聚合审计；`tally_correctness` ZK 证明可通过 `submitAuditWithTallyProof` 走链上 Groth16 verifier 验证，但还不是完整 Aggios EPA proof。
- 当前项目是比赛原型，不是生产级电子投票系统。

## 15. 后续计划

本轮已落地的子项已从计划移到对应文档（见「相关文档」小节）。

### 已落地（本轮）

- **Pedersen 承诺实验模块**：独立的 opening verification / aggregate verification，不替换 SHA-256 主流程（`docs/PEDERSEN_EXPERIMENT.md`）。
- **SECURITY_TESTS.md 安全测试矩阵**：八大威胁 + 横向项（`docs/SECURITY_TESTS.md`）。
- **Zeeperio 风格 artifact export**：`bulletin_board.json` / `aggregator_report.json` / `zk_summary.json` / `chain_audit.json` / `public_inputs.json` 分文件下载，以及合并 `bundle.json`。
- **批次计票正确性 ZK 证明**：`tally_correctness.circom` + `createTallyCorrectnessProof` + `/zk/prove-tally-correctness`（`docs/TALLY_CORRECTNESS_PROOF.md`）。
- **SQLite 可选持久化**：通过环境变量 `VERIVOTE_PERSISTENCE=auto|memory|sqlite` 切换。
- **Docker / docker-compose 一键启动**：`Dockerfile.api` + `Dockerfile.web` + `docker-compose.yml`。
- **GitHub Actions**：`.github/workflows/ci.yml`（typecheck + build + hardhat test + benchmark）和 `.github/workflows/zk.yml`（circom/snarkjs smoke test）。
- **服务化部署文档**：`docs/DEPLOYMENT.md`（Docker / systemd / Nginx / Kubernetes）。
- **Solidity verifier 挂链**：`VeriVoteAudit.submitAuditWithTallyProof` + auto-generated `TallyVerifier.sol` + `MockTallyVerifier`（见 `docs/ON_CHAIN_VERIFIER.md`），评委可看到真正的链上 Groth16 验证。

### 仍待办

1. **把 `electionIdHash` 绑进 ZK 电路 publicSignals**，消除 API 层和链上 verifier 之间的 proof 绑定缝。
2. **`valid_vote` 单票电路也导出 Solidity verifier**，提供 per-ballot 上链验证路径；`tally_correctness` 路径已完成（见 `docs/ON_CHAIN_VERIFIER.md`）。
3. **SECURITY_TESTS 自动化**（vitest / playwright）。
4. **选民身份白名单 + 签名**，堵「随机注册 userId → 绕过 tokenHash」。
5. **更大批次 / 动态候选人数**：`TallyCorrectness(N, C)` 模板化 + padding。
6. **报告 / PPT / 演示脚本**：单独产出 `docs/DEMO_SCRIPT.md` 和架构图 / 论文关系图。

## 16. 开发注意事项

每完成一个阶段后，建议：

1. `pnpm typecheck`
2. `pnpm build`
3. `git commit`
4. `git push origin main`
5. 关闭后端 `3001` 和前端 `18340`

关闭本地服务可以使用 PowerShell：

```powershell
$ports = @(3001, 18340, 5173)

foreach ($port in $ports) {
  $listeners = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
  foreach ($conn in $listeners) {
    if ($conn.OwningProcess -ne 0) {
      Stop-Process -Id $conn.OwningProcess -Force
    }
  }
}
```

## 相关文档

- `docs/PAPER_MAPPING.md`：三篇论文与 VeriVote 工程模块的映射。
- `docs/FRIEND_PROJECT_ANALYSIS.md`：朋友项目机制分析与融合边界。
- `docs/FUSION_ROADMAP.md`：后续分阶段融合路线。
- `docs/ZK_VALIDITY_PROOF.md`：Mock / Real ZK validity proof 说明。
- `docs/REAL_ZK_DEMO.md`：Real Groth16 ZK demo 使用说明。
- `docs/BENCHMARK.md`：benchmark 结果与指标解释。
- `docs/SECURITY_TESTS.md`：安全测试矩阵（8 大威胁 + 横向项）。
- `docs/PEDERSEN_EXPERIMENT.md`：Pedersen 风格承诺实验模块说明。
- `docs/TALLY_CORRECTNESS_PROOF.md`：批次计票正确性 ZK 证明（8 x 4 电路）。
- `docs/ON_CHAIN_VERIFIER.md`：Solidity verifier 挂链说明（真 Groth16 + MockTallyVerifier）。
- `docs/DEPLOYMENT.md`：Docker、systemd、Nginx、Kubernetes 部署指南。
