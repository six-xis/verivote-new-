\# VeriVote-ABP



\*\*Audit-Bound Partition Proof for Privacy-Preserving, Publicly Auditable Electronic Voting\*\*



VeriVote-ABP 是一个面向低信任组织场景的隐私保护、可验证、可审计电子投票系统。项目目标不是做一个普通投票网站，而是构建一个围绕 \*\*资格凭证、隐私投票、公开公告板、零知识合法性证明、审计绑定和后续链上验证\*\* 的研究型安全系统原型。



当前版本已经从早期 TypeScript/Express demo 迁移到以 \*\*Python/FastAPI\*\* 为主后端的 ABP v2 架构，并完成了真实 `private\_valid\_vote` Circom/snarkjs/Groth16 证明流水线的最小可运行版本。



> 当前项目仍处于比赛原型和研究工程阶段。部分模块使用 demo/reference/unsafe setup，不能直接视为生产级电子投票系统。



\---



\## 目录



\* \[项目定位](#项目定位)

\* \[当前完成状态](#当前完成状态)

\* \[核心能力](#核心能力)

\* \[系统架构](#系统架构)

\* \[目录结构](#目录结构)

\* \[快速开始](#快速开始)

\* \[Python/FastAPI 主后端](#pythonfastapi-主后端)

\* \[ABP v2 投票流程](#abp-v2-投票流程)

\* \[Private Valid Vote ZK Proof](#private-valid-vote-zk-proof)

\* \[API 概览](#api-概览)

\* \[测试与验证](#测试与验证)

\* \[ZK 本地运行命令](#zk-本地运行命令)

\* \[安全边界与当前限制](#安全边界与当前限制)

\* \[后续路线图](#后续路线图)

\* \[相关文档](#相关文档)



\---



\## 项目定位



VeriVote-ABP 的全称是：



```text

VeriVote Audit-Bound Partition Proof

```



系统核心目标是将电子投票中的多个公开审计对象绑定到统一证明与审计材料中：



\* `election\_id\_hash`

\* `manifest\_hash`

\* `eligibility\_root`

\* `commitment\_root`

\* `nullifier\_root`

\* `receipt\_root`

\* `tally\_hash`

\* `audit\_bundle\_hash`



最终希望形成：



```text

资格凭证 -> 隐私投票 -> 公告板 -> ZK 合法性证明 -> 审计包 -> 链上绑定

```



本项目当前重点解决以下问题：



1\. 投票内容不应在 cast 阶段明文暴露；

2\. 系统应能公开验证某张票被正确记录；

3\. 同一资格在同一 election 中不能重复投票；

4\. 用户投票合法性应由零知识证明约束；

5\. 审计材料应能被离线复验，并可后续提交链上锚定；

6\. mock/demo/reference 代码必须与真实安全路径清晰区分。



\---



\## 当前完成状态



截至当前版本，项目已经完成以下阶段。



\### M1：Python/FastAPI 主后端迁移



已新增主后端：



```text

apps/api\_py/

```



原 Node/Express 后端：



```text

apps/api/

```



保留为 legacy demo，不再作为新核心功能的主开发对象。



已完成：



\* FastAPI 应用入口；

\* API v1/v2 路由结构；

\* service/repository 分层；

\* pytest 测试基线；

\* ruff lint 基线；

\* legacy Node 后端保留。



\---



\### M2：ABP v2 数据模型



已定义 ABP v2 核心模型：



\* `CandidateV2`

\* `ElectionManifestV2`

\* `CredentialV2`

\* `DemoCredentialIssueResponse`

\* `CastBallotRecordV2`

\* `ChallengeBallotRecordV2`

\* `AuditRootsV2`

\* `BatchTallyPublicSignalsV2`

\* `AuditBundleV2`



安全边界：



\* `CastBallotRecordV2` 禁止出现：



&#x20; \* `candidate\_id`

&#x20; \* `vote\_vector`

&#x20; \* `randomness`

\* `CredentialV2` 禁止出现：



&#x20; \* `credential\_secret`

\* `BatchTallyPublicSignalsV2` 固定 public signal 顺序，为后续 circuit / Solidity verifier 对齐做准备。



\---



\### M3：commitmentV2 与 sealedVotePackage



已完成：



\* canonical JSON；

\* `field\_hash\_v2`；

\* `commitmentV2`；

\* vote vector one-hot 校验；

\* `sealedVotePackage`；

\* `sealedVotePackageHash`；

\* AESGCM demo tally encryption；

\* sealed package 不泄露明文 vote vector / randomness。



当前注意事项：



\* Python `field\_hash\_v2` 是 SHA256-to-BN254 reference/demo hash；

\* 它不是最终生产 Poseidon commitment；

\* 真实 ZK circuit 使用 Poseidon profile。



\---



\### M4：ABP v2 cast ballot API



已完成正式 cast endpoint：



```http

POST /api/v2/elections/{election\_id}/ballots/cast

```



该接口接收：



\* `commitment`

\* `nullifier\_hash`

\* `sealed\_vote\_package`

\* `sealed\_vote\_package\_hash`

\* `receipt\_code`

\* `validity\_proof\_hash`

\* 可选 `validity\_proof`



该接口拒绝：



\* `candidate\_id`

\* `vote\_vector`

\* `randomness`

\* `credential\_secret`



已完成：



\* sealed package hash 重算校验；

\* nullifier 防重复；

\* receipt chain hash 最小实现；

\* bulletin board public projection；

\* public response 不返回完整 sealed package。



\---



\### M5：eligibilityRoot 与 nullifierHash



已完成资格凭证基础设施：



\* `credential\_secret`

\* `credential\_commitment`

\* `eligibility\_root`

\* Merkle proof

\* `nullifier\_hash`

\* demo credential issuer



相关 API：



```http

POST /api/v2/elections/{election\_id}/credentials/demo-issue

GET  /api/v2/elections/{election\_id}/credentials/public

POST /api/v2/elections/{election\_id}/credentials/derive-nullifier

```



安全边界：



\* `credential\_secret` 只在 demo issue response 中返回；

\* public credentials 不返回 secret；

\* bulletin board 不返回 secret；

\* cast record 不保存 secret；

\* nullifier 由 `election\_id\_hash + credential\_secret` 推导；

\* 同一 election 下相同 nullifier 不能重复 cast。



\---



\### M6A：Private Valid Vote Proof 接口与 mock guard



已完成：



\* `PrivateValidVotePublicSignalsV1`

\* `PrivateValidVoteProofV1`

\* proof public signal 安全边界；

\* mock verifier guard；

\* production / competition 禁止 mock fallback；

\* cast API 可选接入 `validity\_proof`；

\* ZK status API。



public signals 固定顺序：



```text

0 election\_id\_hash

1 eligibility\_root

2 nullifier\_hash

3 commitment

4 rule\_hash

```



public signals 禁止包含：



\* `vote\_vector`

\* `randomness`

\* `candidate\_id`

\* `credential\_secret`



\---



\### M6B/M6C：真实 private\_valid\_vote Circom/snarkjs/Groth16 pipeline



已完成真实最小 ZK pipeline：



\* `circuits/private\_valid\_vote.circom`

\* `circuits/private\_valid\_vote\_4\_8.circom`

\* Poseidon input generator

\* PowerShell build/prove/verify scripts

\* `verification\_key.json`

\* `proof.json`

\* `public.json`

\* `witness.wtns`

\* Python real verifier wrapper

\* ZK status artifact detection



真实 pipeline 已跑通：



```text

build\_private\_valid\_vote.ps1   passed

prove\_private\_valid\_vote.ps1   passed

verify\_private\_valid\_vote.ps1  passed

snarkjs groth16 verify         OK

```



当前 demo circuit 固定参数：



```text

candidateCount = 4

merkleDepth    = 8

```



电路约束包括：



\* vote vector 每项为 0/1；

\* vote vector 之和为 1；

\* `credential\_commitment = Poseidon(\[credential\_secret])`；

\* `nullifier\_hash = Poseidon(\[election\_id\_hash, credential\_secret])`；

\* `eligibility\_root` 由 credential commitment 和 Merkle path 重新计算；

\* `commitment` 绑定 election、eligibility root、nullifier、rule hash、vote vector、randomness。



\---



\## 核心能力



\### 1. 隐私 cast ballot



正式 cast ballot 不保存明文候选人选择：



```text

candidate\_id  不保存

vote\_vector   不公开

randomness    不公开

```



公开记录只包含：



\* commitment

\* nullifier hash

\* sealed vote package hash

\* receipt code

\* receipt chain hash

\* proof hash / proof metadata



\---



\### 2. eligibilityRoot 资格集合



系统使用 credential commitment 构建 election-scoped eligibility Merkle root。



当前 demo issuer 会生成：



```text

credential\_secret

credential\_commitment

eligibility\_root

```



生产设计中，credential 应由独立资格发行方发放，后端不应持有 voter secret。



\---



\### 3. nullifier 防重复投票



每个 election 中，用户通过：



```text

nullifier\_hash = H(election\_id\_hash, credential\_secret)

```



生成 election-scoped nullifier。



同一个 `nullifier\_hash` 在同一个 election 中只能 cast 一次。



\---



\### 4. sealedVotePackage



投票 opening 被封装为 sealed package：



```json

{

&#x20; "version": "sealed-vote-v1",

&#x20; "algorithm": "AESGCM-SHA256-DEMO",

&#x20; "ciphertext": "...",

&#x20; "nonce": "...",

&#x20; "key\_id": "demo",

&#x20; "opening\_hash": "...",

&#x20; "created\_at": "..."

}

```



public response 和 bulletin board 默认只返回：



```text

sealed\_vote\_package\_hash

```



不返回完整 sealed package。



\---



\### 5. Private Valid Vote ZK Proof



真实 Circom 电路使用 Poseidon profile：



```text

credential\_commitment = Poseidon(\[credential\_secret])

nullifier\_hash        = Poseidon(\[election\_id\_hash, credential\_secret])

eligibility\_root      = Poseidon Merkle root

commitment            = Poseidon(header\_hash, vote\_hash, randomness)

```



public signals：



```text

election\_id\_hash

eligibility\_root

nullifier\_hash

commitment

rule\_hash

```



private witness：



```text

vote\_vector

randomness

credential\_secret

merkle\_path\_elements

merkle\_path\_indices

```



\---



\## 系统架构



当前项目采用 monorepo 结构。



```text

VeriVote-ABP

├── apps/

│   ├── api/          # legacy Node/Express backend

│   ├── api\_py/       # primary Python/FastAPI backend

│   └── web/          # React/Vite frontend

├── packages/

│   ├── crypto/       # legacy/shared TypeScript crypto utilities

│   ├── shared/       # shared TS types

│   └── zk/           # legacy/mock ZK utilities

├── circuits/         # Circom circuits and ZK inputs

├── scripts/

│   └── zk/           # ZK build/prove/verify scripts

├── artifacts/

│   └── zk/

│       └── private\_valid\_vote/

├── contracts/        # Solidity/Hardhat contracts

├── docs/             # protocol, API, ZK, threat model, roadmap docs

├── tests/

├── package.json

└── pnpm-workspace.yaml

```



\---



\## 目录结构



重要目录说明：



| Path                              | 说明                                    |

| --------------------------------- | ------------------------------------- |

| `apps/api\_py`                     | 当前主后端，基于 Python/FastAPI               |

| `apps/api`                        | legacy Node/Express demo backend      |

| `apps/web`                        | React/Vite 前端                         |

| `circuits`                        | Circom 电路                             |

| `scripts/zk`                      | ZK input/build/prove/verify 脚本        |

| `artifacts/zk/private\_valid\_vote` | 当前 private valid vote proof artifacts |

| `contracts`                       | Solidity/Hardhat 链上审计合约               |

| `docs/API\_V2.md`                  | Python API v2 文档                      |

| `docs/VERIVOTE\_ABP\_SPEC.md`       | ABP v2 协议说明                           |

| `docs/ZK\_PRIVATE\_VALID\_VOTE.md`   | private valid vote proof 说明           |

| `docs/THREAT\_MODEL\_V2.md`         | 当前威胁模型                                |

| `docs/TESTING.md`                 | 测试命令和环境说明                             |



\---



\## 快速开始



\### 1. 安装 Node 依赖



项目使用 pnpm workspace。



```bash

pnpm install

```



Windows PowerShell 下如果 `pnpm.ps1` 被执行策略拦截，可以使用：



```powershell

pnpm.cmd install

```



\---



\### 2. 安装 Python 后端依赖



```bash

cd apps/api\_py

python -m pip install -e ".\[dev]"

```



\---



\### 3. 启动 Python/FastAPI 主后端



在项目根目录运行：



```bash

pnpm run dev:api-py

```



或者进入 Python API 目录运行：



```bash

cd apps/api\_py

python -m uvicorn app.main:create\_app --factory --reload

```



默认访问：



```text

http://127.0.0.1:8000

```



健康检查：



```bash

curl http://127.0.0.1:8000/health

curl http://127.0.0.1:8000/api/v2/health

```



\---



\### 4. 启动前端



```bash

pnpm run dev:web

```



如果需要指定 Vite 端口：



```bash

pnpm run dev:web -- --port 18340

```



\---



\## Python/FastAPI 主后端



`apps/api\_py` 是当前主后端。



安装：



```bash

cd apps/api\_py

python -m pip install -e ".\[dev]"

```



运行：



```bash

python -m uvicorn app.main:create\_app --factory --reload

```



测试：



```bash

python -m pytest

python -m ruff check app

```



根目录快捷命令：



```bash

pnpm run test:py-api

pnpm run lint:py-api

```



Windows 推荐：



```powershell

pnpm.cmd run test:py-api

pnpm.cmd run lint:py-api

```



\---



\## ABP v2 投票流程



当前 ABP v2 的 reference/demo 投票流程：



```text

1\. 创建 election

2\. 添加 candidates

3\. demo issue credential

4\. 生成 credential\_commitment

5\. 更新 eligibility\_root

6\. derive nullifier\_hash

7\. 生成 vote\_vector 与 randomness

8\. 计算 commitment

9\. 生成 sealedVotePackage

10\. 提交 /ballots/cast

11\. bulletin-board 公开 public cast record

12\. nullifier\_hash 防重复 cast

```



当前 real-ZK 流程：



```text

1\. 使用 Poseidon input generator 生成 witness input

2\. build private\_valid\_vote circuit

3\. generate witness

4\. groth16 prove

5\. groth16 verify

6\. Python wrapper 检测真实 verifier artifacts

```



下一阶段 M7 将把真实 proof 更严格地接入 cast API。



\---



\## Private Valid Vote ZK Proof



\### 电路文件



```text

circuits/private\_valid\_vote.circom

circuits/private\_valid\_vote\_4\_8.circom

```



\### 输入生成器



```text

scripts/zk/generate\_private\_valid\_vote\_input.mjs

```



生成：



```text

circuits/inputs/private\_valid\_vote.valid.json

circuits/inputs/private\_valid\_vote.invalid\_overvote.json

circuits/inputs/private\_valid\_vote.invalid\_membership.json

artifacts/zk/private\_valid\_vote/public\_signals\_expected.json

```



\### PowerShell 脚本



```powershell

powershell -ExecutionPolicy Bypass -File scripts/zk/build\_private\_valid\_vote.ps1

powershell -ExecutionPolicy Bypass -File scripts/zk/prove\_private\_valid\_vote.ps1

powershell -ExecutionPolicy Bypass -File scripts/zk/verify\_private\_valid\_vote.ps1

```



\### 生成 artifacts



```text

artifacts/zk/private\_valid\_vote/

├── private\_valid\_vote.r1cs

├── private\_valid\_vote.sym

├── private\_valid\_vote\_js/

├── private\_valid\_vote.zkey

├── verification\_key.json

├── witness.wtns

├── proof.json

└── public.json

```



\### 验证命令



```bash

pnpm exec snarkjs groth16 verify \\

&#x20; artifacts/zk/private\_valid\_vote/verification\_key.json \\

&#x20; artifacts/zk/private\_valid\_vote/public.json \\

&#x20; artifacts/zk/private\_valid\_vote/proof.json

```



Windows：



```powershell

pnpm.cmd exec snarkjs groth16 verify `

&#x20; artifacts/zk/private\_valid\_vote/verification\_key.json `

&#x20; artifacts/zk/private\_valid\_vote/public.json `

&#x20; artifacts/zk/private\_valid\_vote/proof.json

```



成功时输出：



```text

snarkJS: OK!

```



\---



\## API 概览



\### Health



```http

GET /health

GET /api/v1/legacy/health

GET /api/v2/health

```



\### Election



```http

POST /api/v2/elections

POST /api/v2/elections/{election\_id}/candidates

```



\### Demo Credential



```http

POST /api/v2/elections/{election\_id}/credentials/demo-issue

GET  /api/v2/elections/{election\_id}/credentials/public

POST /api/v2/elections/{election\_id}/credentials/derive-nullifier

```



\### Ballot



```http

POST /api/v2/elections/{election\_id}/ballots/legacy-cast

POST /api/v2/elections/{election\_id}/ballots/cast

```



说明：



\* `legacy-cast` 是迁移期 simple endpoint；

\* `/ballots/cast` 是 ABP v2 reference/demo cast path；

\* 后续 M7 会新增或强化 real-proof cast path；

\* proofless cast path 后续应逐步废弃。



\### Bulletin Board



```http

GET /api/v2/elections/{election\_id}/bulletin-board

```



返回 public cast records，不返回：



\* full sealed vote package

\* vote vector

\* randomness

\* candidate id

\* credential secret



\### ZK Status



```http

GET /api/v2/zk/private-valid-vote/status

```



典型返回字段：



```json

{

&#x20; "configured": true,

&#x20; "zk\_profile": "poseidon-v1",

&#x20; "circuit": "private\_valid\_vote\_4\_8",

&#x20; "verifier\_artifact\_present": true,

&#x20; "snarkjs\_available": true,

&#x20; "mock\_mode": false,

&#x20; "real\_verifier\_available": true,

&#x20; "warning": "SHA reference hash and Poseidon circuit profile alignment is pending"

}

```



\---



\## 测试与验证



\### Python API



```bash

cd apps/api\_py

python -m pytest

python -m ruff check app

```



根目录：



```bash

pnpm run test:py-api

pnpm run lint:py-api

```



Windows：



```powershell

pnpm.cmd run test:py-api

pnpm.cmd run lint:py-api

```



当前最近一次已知验证结果：



```text

python -m pytest              107 passed

python -m ruff check app      passed

pnpm.cmd run test:py-api      107 passed

pnpm.cmd run lint:py-api      passed

```



\### Legacy / Workspace Tests



```bash

pnpm run test:api

pnpm run test:crypto

pnpm run test:zk

pnpm run test:contract

```



聚合命令：



```bash

pnpm test

```



如果聚合命令在本地超时，迁移期优先使用 targeted tests。



\---



\## ZK 本地运行命令



\### 依赖检查



```bash

circom --version

pnpm exec snarkjs --help

node -e "console.log(require.resolve('circomlib'))"

node -e "import('circomlibjs').then(()=>console.log('circomlibjs ok'))"

```



Windows：



```powershell

circom --version

pnpm.cmd exec snarkjs --help

node -e "console.log(require.resolve('circomlib'))"

node -e "import('circomlibjs').then(()=>console.log('circomlibjs ok'))"

```



\### 安装 ZK 依赖



```bash

pnpm add -D snarkjs circomlib circomlibjs

```



如果在 workspace root 安装：



```bash

pnpm add -Dw snarkjs circomlib circomlibjs

```



\### 运行 private valid vote pipeline



```powershell

node scripts/zk/generate\_private\_valid\_vote\_input.mjs



powershell -ExecutionPolicy Bypass -File scripts/zk/build\_private\_valid\_vote.ps1

powershell -ExecutionPolicy Bypass -File scripts/zk/prove\_private\_valid\_vote.ps1

powershell -ExecutionPolicy Bypass -File scripts/zk/verify\_private\_valid\_vote.ps1

```



\---



\## 安全边界与当前限制



当前已经明确区分 real path、mock path、reference path。



\### 已完成的安全边界



\* cast ballot 不公开 `vote\_vector`；

\* cast ballot 不公开 `randomness`；

\* cast ballot 不保存 `candidate\_id`；

\* public credentials 不公开 `credential\_secret`；

\* bulletin board 不公开 sealed package 全量内容；

\* nullifier 防重复投票；

\* mock ZK 不允许在 production / competition 中 fallback；

\* real private valid vote proof pipeline 已能 build/prove/verify。



\### 当前仍然是 demo/reference/unsafe 的部分



1\. `field\_hash\_v2` 是 SHA256-to-BN254 reference hash；

2\. Python reference commitment 与 Poseidon circuit profile 尚未完全统一；

3\. 当前 Powers of Tau / zkey 是本地 unsafe development setup；

4\. fixture values 是 deterministic demo；

5\. `/ballots/cast` 仍保留 proofless migration path；

6\. sealed vote package opening 与 proof witness 的动态绑定还需要 M7/M8 继续完善；

7\. batch tally proof 尚未实现；

8\. Solidity on-chain verifier 尚未接入 ABP proof public signals；

9\. coercion-resistance 不在当前版本安全声明范围内。



\---



\## 后续路线图



\### M7：cast API 接入真实 private valid vote proof



目标：



\* 新增或强化 real-proof cast endpoint；

\* 拒绝 mock proof；

\* 调用真实 `snarkjs groth16 verify`；

\* 将 proof public signals 与 election/cast request 绑定；

\* 保留 reference cast path 作为迁移期路径；

\* 明确 SHA reference profile 与 Poseidon real-proof profile 的边界。



\### M8：cast-or-challenge 与 receipt chain 完整化



目标：



\* pending ballot；

\* cast / challenge 双路径；

\* challenge opening 公开但不计票；

\* receipt chain 模块化；

\* receipt root 生成。



\### M9：AuditBundleV2 与 offline verifier



目标：



\* 生成完整 audit bundle；

\* 包含 manifest、roots、public cast records、challenge records、proof metadata；

\* 离线 verifier 复算 roots 和 hashes；

\* 明确不包含 credential secret / decrypted openings。



\### M10：batch tally reference checker



目标：



\* 解密 sealed packages；

\* 计算 tally；

\* 校验 cast set；

\* 生成 tally hash；

\* 为 batch tally circuit 准备 witness。



\### M11：batch\_tally\_bound.circom



目标：



\* 批量计票证明；

\* public signals 绑定 election、manifest、commitmentRoot、nullifierRoot、receiptRoot、tallyHash；

\* 为 Solidity verifier 做 public input 对齐。



\### M12：tally service with proof



目标：



\* 后端接入 batch tally proof；

\* 生成 proof artifacts；

\* 写入 audit bundle。



\### M13：Solidity BoundAudit



目标：



\* 部署链上 verifier / audit registry；

\* 校验 proof public signals 与提交字段一致；

\* 记录 audit commitment。



\### M14：Python web3.py submit-chain



目标：



\* Python 后端提交 audit bundle hash；

\* 获取 transaction hash；

\* 查询链上记录。



\### M15：adversarial election corpus



目标：



\* 构造攻击数据集；

\* 包括 duplicate nullifier、tampered commitment、bad receipt chain、bad tally、invalid proof、wrong root 等。



\### M16：RQ benchmark and ablation



目标：



\* RQ1 有效性；

\* RQ2 安全攻击检测；

\* RQ3 proof 开销；

\* RQ4 可扩展性；

\* RQ5 消融实验；

\* RQ6 链上 gas 和 audit bundle size。



\### M17：frontend ABP v2 demo



目标：



\* 展示 election；

\* demo credential；

\* cast；

\* bulletin board；

\* ZK status；

\* audit bundle；

\* attack lab；

\* proof verification state。



\### M18：production guard and final gap report



目标：



\* 禁用 mock production；

\* 输出 final gap report；

\* 明确哪些是 demo/reference；

\* 准备比赛报告和答辩材料。



\---



\## 相关文档



建议阅读顺序：



1\. `docs/VERIVOTE\_ABP\_SPEC.md`

2\. `docs/API\_V2.md`

3\. `docs/ZK\_PRIVATE\_VALID\_VOTE.md`

4\. `docs/THREAT\_MODEL\_V2.md`

5\. `docs/PY\_BACKEND\_MIGRATION.md`

6\. `docs/TESTING.md`

7\. `docs/ROADMAP\_GUOYI.md`

8\. `scripts/zk/README.md`

9\. `circuits/README.md`



\---



\## 开发环境建议



推荐环境：



\* Windows 11 + PowerShell

\* Node.js 20+

\* pnpm 10+

\* Python 3.11+

\* Circom 2.2+

\* snarkjs 0.7+

\* circomlib 2+

\* circomlibjs 0.1+

\* Rust toolchain，用于安装 Circom



\---



\## 竞赛/研究说明



VeriVote-ABP 当前是一个用于信息安全竞赛和研究展示的系统原型。它强调：



\* 可验证投票；

\* 隐私保护；

\* 公开审计；

\* ZK 合法性证明；

\* 工程可运行；

\* 文档与测试可复现；

\* demo/reference/real path 清晰区分。



项目不会声称当前版本已经达到生产级电子投票系统要求。所有 demo issuer、unsafe setup、reference hash、mock path 都会在文档中明确标记，并逐步替换为真实安全组件。



\---



\## License



当前仓库尚未声明正式开源许可证。若需要公开复用，请先补充 LICENSE 文件。



