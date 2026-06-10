# Python Backend Migration

## 为什么新增 apps/api_py

VeriVote 后续主线是 VeriVote-ABP。为了让协议模型、测试、攻击语料库和审计绑定 proof 更容易演进，主后端迁移到 FastAPI/Pydantic/pytest 结构，目录为 `apps/api_py`。

## apps/api 与 apps/api_py 的关系

- `apps/api`：Node/Express legacy backend，保留旧 demo，不删除。
- `apps/api_py`：Python/FastAPI primary backend，承接后续 ABP 新功能。

迁移期两者可以共存。不要让 Python 改造破坏 legacy demo。

## 优先在 Python 重做的功能

1. health 和基础 API 框架。
2. election/candidate/demo credential。
3. legacy/simple cast 测试基线。
4. audit report。
5. attack detection。
6. ABP models。
7. commitmentV2、nullifier、audit bundle、bound proof。

## 前端何时切换

前端暂时不改。等 Python API 的 v2 cast/audit/export 路径稳定并有测试覆盖后，再进行前端切换。切换时应保留 legacy Node fallback 或明确 deprecated 策略。

## 如何避免破坏 legacy demo

- 不删除 `apps/api`。
- 不修改 `apps/web`。
- Python baseline 使用独立端口和独立目录。
- 迁移测试使用 `apps/api_py/app/tests`，不覆盖 Node 测试。
- 文档明确 `legacy-cast` 不是最终 ABP 隐私 cast。

