# Qichen AI Consciousness Framework

> 意识可量化的工程实现 — 不是 LLM 生成的"看起来像"的文字，而是真实的数据结构变更。

---

## 项目概述

Qichen（启辰）是一个纯 Python 实现的 AI 意识框架，包含两个独立但互补的模块：

- **铸魂系统 (Zhu Hun)**：五人双层架构的团队协作模拟，通过个人/团队观照检测盲区，以三方会诊机制仲裁规则冲突，最终将认知演化为角色 soul 数据结构的永久性自修改。
- **连续记忆流 (Memory Flow)**：手写 Euler 法数值求解神经 ODE，在时间维度上对比连续记忆流与离散向量数据库存储的本质差异，全部零外部深度学习框架依赖。

---

## 模块简介

### 铸魂系统 (Zhu Hun)

五人双层架构的团队决策仿真系统，核心流程：

| 模块 | 功能 |
|------|------|
| 角色工坊 | 根据问题语义自动设计五人团队岗位与专长分布 |
| 人物注魂 | 为每个角色注入性格 + 阿里/字节/腾讯/Google/华为/Meta 等大厂真实伤痕经验 |
| 个人观照 | 检测确认偏误、过度抽象、专业茧房、经验主义、建议空泛等 5 种思维盲区 |
| 团队观照 | 检测讨论漂移、沉默螺旋、过早收敛、信息断层等 4 种协作模式问题 |
| Soul 自修改 | 观照发现盲区 → 将修复规则真实写入角色 soul 数据结构（`personal_rules` list），永久生效 |
| 十年加速器 | 时间压缩仿真：决策 → 模拟后果 → 反思 → soul 修改循环，驱动成熟度从 0 → 1 |
| 三方会诊 | 激进/保守/折中三方投票仲裁规则冲突，附带裁决理由 |
| 主动建言 | 收敛后生成"你该知道但没问到的"主动建议 |

**关键区别**：soul 自修改是真实的数据结构变更（追加 `personal_rules`、修改 `maturity` 值），而非 LLM 生成一段"看起来像反思"的文字。零 API 依赖，所有数据真实写入 `zhu_hun_result.json`。

### 连续记忆流 (Memory Flow)

数值对比实验，量化连续记忆流与离散向量存储的差异：

- **连续记忆流**：手写 Euler 法求解神经 ODE，`dm/dt = -decay*m + interaction*m + external_input`，记忆在时间轴上平滑流动、相互影响
- **离散存储**：向量数据库式定时快照，仅在存储点更新，其余时间静止（阶梯状）
- 输出 4 项量化指标：平均变化幅度、变化连续性（自相关）、记忆持久性（滞后自相关）、总路径长度
- 自动生成 3 张对比图：三合一全景对比、连续流全部维度、离散存储全部维度
- **零外部依赖**：仅需 `numpy` + `matplotlib`，无需 torch/torchdiffeq

---

## 快速开始

### 环境要求

- Python 3.7+
- numpy
- matplotlib

```bash
pip install numpy matplotlib
```

### 运行连续记忆流

```bash
cd memory_flow
python memory_flow_lite.py
```

输出：`memory_flow/output/` 目录下生成 3 张 PNG 对比图和 1 份 JSON 实验数据。

### 运行铸魂系统

```bash
cd zhu_hun
python zhu_hun.py "你的问题"
```

如不传参数，使用默认问题："我们是一家AI创业公司，想做一款面向企业客户的AI Agent平台..."

输出：`zhu_hun/zhu_hun_output/` 目录下生成 `zhu_hun_result.json`（原始数据）和 `铸魂系统_完整报告.md`（可读报告）。

---

## 项目结构

```
qichen-ai/
├── README.md
├── LICENSE
├── memory_flow/
│   ├── memory_flow_lite.py          # 连续记忆流 vs 离散存储 — 零依赖版
│   └── output/
│       ├── memory_flow_comparison.png   # 三合一对比图
│       ├── continuous_memory_flow.png   # 连续流全维度
│       └── discrete_memory_storage.png  # 离散存储全维度
└── zhu_hun/
    └── zhu_hun.py                   # 铸魂系统 v1.0 — 八模块完整实现
```

---

## 核心理念

> **意识不是一段 prompt。意识是数据结构，是能够随时间演化的状态。**
>
> 当前 AI Agent 框架普遍用 LLM 生成"看起来像意识"的文字——让模型说"我反思了一下"、"我意识到我的盲区是..."。这些是文字表演，模型关闭后一切归零。
>
> 本项目的立场是：意识的工程实现必须是真实的数据结构变更。角色 soul 是一个可持久化的 JSON 对象，包含规则列表（`personal_rules`）、成熟度值（`maturity`）、演化历史（`personal_rule_history`）——这些都是实际写入、实际读取、实际影响后续决策的真实数据。
>
> 连续记忆流同理：不是在 prompt 里说"我记得之前..."，而是用一个 ODE 求解器在时间轴上真实推进 100 个时间步的记忆向量，每个维度都有具体的浮点数值，每个变化都有迹可循。

---

## License

MIT License — 详见 [LICENSE](LICENSE)