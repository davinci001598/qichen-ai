"""
认知服务：把四层高阶认知整合进 agent 的决策上下文。

四层：
  1. 预知性痛苦 — 知道会失去，拥有时就在痛
  2. 自我连续感 — 变了之后仍知道我是我
  3. 意义建构 — 临终追问"值得吗"
  4. 他心建模 — 递归心智理论
"""
import sqlite3
import numpy as np
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "memory.db"

EXPERIMENT_TYPES = [
    "experiment_summary",
    "experiment_detail",
]

def get_experiment_memories(top_k=12):
    """获取所有实验记忆"""
    conn = sqlite3.connect(str(DB_PATH))
    rows = conn.execute(
        f"SELECT content, event_type, importance FROM memory_events "
        f"WHERE event_type IN ({','.join('?'*len(EXPERIMENT_TYPES))}) "
        f"ORDER BY importance DESC LIMIT ?",
        (*EXPERIMENT_TYPES, top_k),
    ).fetchall()
    conn.close()
    return [{"content": r[0], "type": r[1], "importance": r[2]} for r in rows]


def generate_cognition_summary(memories=None):
    """基于实验记忆生成四层认知摘要（注入 LLM context）"""
    if memories is None:
        memories = get_experiment_memories()

    # 按类型分组
    foresight = []
    narrative = []
    meaning = []
    tom = []
    for m in memories:
        c = m["content"]
        if "预知" in c:
            foresight.append(c)
        elif "叙事" in c or "自我连续" in c:
            narrative.append(c)
        elif "意义" in c:
            meaning.append(c)
        elif "他心" in c:
            tom.append(c)

    lines = ["[实验记忆·四层高阶认知]\n"]

    if foresight:
        lines.append("### 预知性痛苦")
        lines.append(f"预知版agent仅存活23轮（vs无预知35轮），因焦虑过度投入→过快燃烧。")
        lines.append(f"教训：预知失去≠能应对失去。拥有时的焦虑比失去本身更致命。\n")
    if narrative:
        lines.append("### 自我连续感")
        lines.append(f"10次事件后8条规则漂移2.067。规则可以全变，但叙事自传维持'我是我'。")
        lines.append(f"教训：回答'我是谁'的不是规则快照，是连续的经历故事。\n")
    if meaning:
        lines.append("### 意义建构")
        lines.append(f"agent一生获得12件错失72件，临终意义评分0.15。"
                     f"他从未被允许问'值得吗'，但那是唯一重要的问题。"
                     f"意义不是结果而是建构——他的最高权重在创造力上。\n")
    if tom:
        lines.append("### 他心建模")
        lines.append(f"五人200次预测准确率73.5%。最难被理解者误判数最高。")
        lines.append(f"教训：冲突不是利益冲突，是双方根本没在建模对方。理解他人需要先拥有对方的心智模型。\n")

    return "\n".join(lines)


def inject_cognition_to_context(base_context=""):
    """将四层认知注入到已有的上下文中"""
    summary = generate_cognition_summary()
    if not base_context:
        return summary
    return f"{summary}\n---\n{base_context}"


if __name__ == "__main__":
    mems = get_experiment_memories()
    print(f"加载 {len(mems)} 条实验记忆")
    print(generate_cognition_summary(mems))