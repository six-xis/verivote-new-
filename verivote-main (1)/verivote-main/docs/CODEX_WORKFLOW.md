# Codex Workflow for VeriVote-ABP

本文件是后续 Codex 开发 VeriVote 的硬规则。从本阶段开始，后端主实现位于 `apps/api_py`。原 Node/Express 后端 `apps/api` 保留为 legacy demo，不再作为新功能主开发对象。

## 1. 后端主线

- 主后端：`apps/api_py`，技术栈为 FastAPI、Pydantic、pytest、httpx、ruff。
- Legacy 后端：`apps/api`，只用于兼容旧 demo 和历史测试。
- 新的 ABP 协议、API 拆分、审计绑定证明、攻击语料库和 Python 测试优先落在 `apps/api_py`。
- 不允许删除 `apps/api`，不允许破坏 legacy demo。

## 2. 每次任务范围

- 每次只做一个小任务。
- 不做无关重构。
- 不重写前端、circuits、contracts，除非任务明确要求。
- 不删除旧接口；需要替换时先标记 deprecated 并保持兼容。

## 3. 测试规则

- 每次 Codex 任务必须新增或更新 pytest 测试，除非任务纯文档且已说明原因。
- Python 后端验收以 `python -m pytest`、`python -m ruff check app` 为准。
- 如果后续配置 mypy，再以 `python -m mypy app` 作为类型检查入口。
- 不允许伪造测试通过；没有运行就必须说明没有运行。

## 4. 密码学与隐私红线

- 不允许把 mock verifier 当成 production verifier。
- 不允许把 mock proof 当成真实 ZK proof。
- 不允许把 `voteVector` 放入 publicSignals。
- 不允许把明文 `candidateId` 放入 publicSignals。
- 不允许 ABP cast ballot 明文保存 `candidateId`、`voteVector`、`randomness`。
- `legacy-cast` 只是迁移期测试基线，不是最终隐私投票接口。

## 5. 输出要求

每次最终输出必须说明：

1. 新增/修改文件。
2. 运行过的测试命令和真实结果。
3. 未完成项。
4. 哪些能力仍是 legacy/simple/demo。
5. 下一步建议。

