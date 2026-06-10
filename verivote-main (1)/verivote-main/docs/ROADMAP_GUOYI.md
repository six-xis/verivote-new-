# VeriVote-ABP 国一冲刺路线图

本路线图以 Python/FastAPI 后端 `apps/api_py` 为主线。`apps/api` 只保留为 legacy Node demo。

## Phase 0 Python backend baseline

建立 FastAPI 目录、内存仓库、pytest、ruff、health/basic-flow/attack-detection 测试。

## Phase 1 ABP models

在 `models/abp.py` 和 `schemas/abp.py` 中补全 `ElectionManifestV2`、`CastBallotRecordV2`、`ChallengeBallotRecordV2`。

## Phase 2 commitmentV2

实现 `commitmentV2`、`sealedVotePackageHash`、canonical hash helpers 和单元测试。

## Phase 3 cast ballot v2

新增 `/api/v2/elections/{id}/ballots/cast`，禁止明文保存 `candidateId`、`voteVector`、`randomness`。

## Phase 4 eligibility + nullifier

实现 `eligibilityRoot`、`credentialCommitment`、`nullifierHash` 和重复投票检测。

## Phase 5 private valid vote proof

实现 private valid vote proof adapter，publicSignals 不包含 voteVector。

## Phase 6 cast-or-challenge

实现 pending ballot、cast、challenge opening，challenge 不计入 tally。

## Phase 7 audit bundle

实现 canonical audit bundle 和 `auditBundleHash`。

## Phase 8 batch tally bound proof

实现绑定 `electionIdHash`、`manifestHash`、roots、`tallyHash`、`auditBundleHash` 的 batch proof。

## Phase 9 on-chain bound audit

合约检查 public signals 与 audit fields 一致后再调用 verifier。

## Phase 10 adversarial corpus

覆盖 proof reuse、root replacement、tally replacement、audit bundle tampering、duplicate nullifier、plaintext persistence。

## Phase 11 RQ benchmark

形成 RQ1-RQ4 性能与安全评估。

## Phase 12 frontend integration

前端切换到 Python API，保留 legacy Node demo fallback。

## Phase 13 report/demo

整理说明书、PPT、录屏、答辩脚本和限制说明。

