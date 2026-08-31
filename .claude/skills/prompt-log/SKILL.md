---
name: prompt-log
description: >-
  本仓库正式任务 prompt 的台账流程。当用户发出一条编号的正式任务 prompt
  （如"第 4 个 prompt"、"prompt04"、"下一个 prompt："），或要求查看、维护、
  核对 PROMPT.md 台账 / README 镜像表，或提到 prompt 记录 harness 的
  begin / finish / sync 命令时使用。不适用于日常小修改或闲聊式请求。
---

# prompt-log：正式 prompt 台账流程

正式 prompt 必须走 harness（scripts/prompt_log.py），不手工编辑 PROMPT.md
的元数据表。README 中的镜像节（prompt-log:begin/end 标记之间）同样禁止手工编辑。

## 1. 判定是否为"正式 prompt"

三个信号，满足任意两条即视为正式（拿不准就问用户，不要擅自 begin）：

1. 用户明确给了编号（"第 N 个 prompt" / "promptNN"）
2. 任务会产生代码或文档产出
3. 任务有明确验收标准

## 2. begin（执行任务之前）

1. 检查 `git status` 是否干净；不干净先请用户处置（脚本也会拒绝并列出脏文件）
2. 把用户 prompt **逐字**写入仓库外的临时文件（如 `/tmp/promptNN.txt`），
   空白结构原样保留，一个字不改
3. 运行：
   ```bash
   uv run python scripts/prompt_log.py begin --file /tmp/promptNN.txt
   ```
4. 核对输出的编号、日期、commit sha

## 3. 执行任务

- 按 prompt 原文与 AGENTS.md 执行
- **禁止**修改 PROMPT.md 中已登记的任何原文

## 4. finish 前的验证门槛（AGENTS.md 第 9 条）

状态只能二选一，判定标准：

- `已完成` = 产出齐备，且验证命令**真实运行过**（测试/校验输出已保存）
- `未完成` = 其余一切情况（含部分完成；如实注明缺什么）

**严禁**：编造验证输出；把未验证的实现记为已完成；登记不存在的文件路径
（脚本会拒绝）；用空文件蒙混。

## 5. finish

```bash
uv run python scripts/prompt_log.py finish N --status 已完成|未完成 \
  --outputs 产出1,产出2 \
  --evidence "实际运行的验证命令 + 关键输出"
```

- `--outputs` 是仓库相对路径，必须真实存在；纯调研任务可省略
- `--evidence` 会进入 commit message，必须来自真实运行
- 脚本自动做两段提交：commit A 收任务全部产出，commit B 回填 sha

## 6. 失败恢复

| 报错 | 处置 |
| --- | --- |
| 工作树不干净 | 先提交/处置列出的文件，再重试 begin |
| 缺少镜像标记 | `uv run python scripts/prompt_log.py sync --init` |
| 镜像漂移 | `uv run python scripts/prompt_log.py sync` 重建 |
| promptNN 已终结 | 确需更正：手工编辑 PROMPT.md 该行，以普通 commit 说明理由 |
| begin 后任务中断 | 该行保持"进行中"，下次继续或 finish 未完成 |
