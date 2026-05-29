"""
Zhu Hun 集成层 — 将铸魂系统嵌入 Agent 主循环

桥接点：
  1. 任务前：角色工坊 + 经验注入 → 多视角规划上下文
  2. 任务后：团队评审 + 三方会诊 → Soul 深度更新
  3. 周期性：加速器驱动 → 成熟度演进
  4. 产出后：主动建言 → "你该知道但没问到的"
"""
import os
import sys
import json
from pathlib import Path

# 确保 zhu_hun 目录在 path 中
BASE_DIR = Path(__file__).parent
ZHU_HUN_DIR = BASE_DIR.parent / "zhu_hun"
sys.path.insert(0, str(ZHU_HUN_DIR))

from zhu_hun import (
    role_workshop, inject_experiences, init_soul,
    accelerate_decade, team_discuss,
    tripartite_consultation, generate_proactive_suggestions,
    PERSONAL_PATTERNS, TEAM_PATTERNS, EXPERIENCE_LIBRARY,
)


# ═══════════════════════════════════════════
# 1. 任务前：多视角规划
# ═══════════════════════════════════════════

def enhance_planning(task, agent_soul=None):
    """
    用 Zhu Hun 增强任务规划上下文
    返回多视角建议文本，注入到 LLM 规划 prompt
    """
    # 角色工坊
    category, roles = role_workshop(task)
    roles = inject_experiences(roles, task)

    # 生成每个角色的视角建议
    lines = []
    lines.append(f"[Zhu Hun 团队分析] 问题类型: {category}")
    lines.append(f"  团队 ({len(roles)}人):")
    for r in roles:
        exps = r.get("experiences", [])
        exp_sources = ", ".join(e["source"][:10] for e in exps) if exps else "无"
        lines.append(f"    {r['name']} ({r['expertise']})")
        lines.append(f"      盲区: {r['blind_spot'][:40]}")
        if exps:
            lines.append(f"      经验: {exp_sources}")

    # 生成团队建议
    lines.append(f"\n[Zhu Hun 视角建议]")
    for r in roles:
        advice = _generate_role_advice(r, task)
        lines.append(f"  {r['name']}: {advice}")

    # 注入大厂经验警告
    all_triggers = []
    for r in roles:
        for exp in r.get("experiences", []):
            all_triggers.extend(exp["trigger_on"])

    if all_triggers:
        relevant_exps = set()
        for r in roles:
            for exp in r.get("experiences", []):
                if any(t in task for t in exp["trigger_on"]):
                    relevant_exps.add(exp["lesson"])

        if relevant_exps:
            lines.append(f"\n[大厂伤痕警告]")
            for lesson in list(relevant_exps)[:3]:
                lines.append(f"  ⚠ {lesson[:120]}")

    return {
        "category": category,
        "roles": [r["name"] for r in roles],
        "context": "\n".join(lines),
    }


def _generate_role_advice(role, task):
    """根据角色生成一句话建议"""
    expertise = role["expertise"]
    experiences = role.get("experiences", [])

    # 经验驱动建议
    if experiences:
        exp = experiences[0]
        return f"依据 {exp['source']} 经验，建议: {exp['lesson'][:80]}"

    # 专业驱动建议
    advice_map = {
        "用户": "先确认目标用户是谁，他们真的需要这个吗",
        "竞争": "先看竞品为什么没做成，是能力问题还是时机问题",
        "增长": "先跑通留存再谈增长",
        "技术": "先用最小成本验证可行性",
        "模型": "选最小的模型先跑通端到端",
        "数据": "数据质量比模型选择重要十倍",
        "系统": "先做最小可用版本，别过度设计",
        "产品": "先看用户实际行为，别假设用户会按你的设计走",
        "伦理": "考虑这个方案对弱势用户是否公平",
        "组织": "先明确谁对什么结果负责",
    }
    for keyword, advice in advice_map.items():
        if keyword in expertise:
            return advice
    return f"从{expertise}角度，建议聚焦核心问题，避免过度发散"


# ═══════════════════════════════════════════
# 2. 任务后：团队评审 + 三方会诊
# ═══════════════════════════════════════════

def review_with_team(task, code, result, agent_soul, existing_rules):
    """
    任务完成后，Zhu Hun 团队评审
    返回: 是否需要修改规则, 三方会诊结果
    """
    # 用 Zhu Hun 的团队讨论框架评审
    category, _ = role_workshop(task)

    # 检查是否有冲突需要三方会诊
    new_rules_from_soul = _extract_new_rules(agent_soul)

    consultations = []
    approved_rules = []
    rejected_rules = []

    for rule in new_rules_from_soul[-3:]:  # 最近3条新规则
        verdict, reason, voices = tripartite_consultation(
            rule, existing_rules, []
        )
        consultations.append({
            "rule": rule,
            "verdict": verdict,
            "reason": reason,
            "voices": [v["vote"] for v in voices],
        })
        if verdict == "采纳":
            approved_rules.append(rule)
        elif verdict == "驳回":
            rejected_rules.append(rule)

    # 生成团队评审意见
    review = {
        "category": category,
        "consultations": consultations,
        "approved": approved_rules,
        "rejected": rejected_rules,
        "summary": _generate_review_summary(task, result, approved_rules, rejected_rules),
    }

    return review


def _extract_new_rules(agent_soul):
    """从 Agent Soul 中提取最近新增的规则"""
    return agent_soul.get("personal_rules", [])[-5:]


def _generate_review_summary(task, result, approved, rejected):
    lines = [f"[Zhu Hun 团队评审]"]
    if result.get("success"):
        lines.append("  结论: 执行成功，以下建议: ")
    else:
        lines.append("  结论: 执行失败，以下建议: ")

    if approved:
        lines.append(f"  会诊通过: {len(approved)}条规则")
    if rejected:
        lines.append(f"  会诊驳回: {len(rejected)}条规则")

    return "\n".join(lines)


# ═══════════════════════════════════════════
# 3. 周期加速器
# ═══════════════════════════════════════════

def periodic_acceleration(agent_soul, task_count):
    """
    每完成 N 个任务，运行一次加速器
    返回加速事件列表
    """
    # 将 agent_soul 转换为 Zhu Hun 格式
    zhu_soul = _agent_soul_to_zhu(agent_soul)

    # 从任务历史中提取一个"问题"用于加速器
    question = f"经过 {task_count} 个编程任务的积累，Agent 的编程能力如何进化"

    souls = [zhu_soul]
    events = accelerate_decade(souls, [], question, num_cycles=min(3, task_count))

    # 将加速结果写回 agent_soul
    agent_soul["maturity"] = zhu_soul["maturity"]
    agent_soul["personal_rules"] = zhu_soul["personal_rules"]

    return events


def _agent_soul_to_zhu(agent_soul):
    """将 agent_soul 转换为 zhu_hun 格式"""
    return {
        "name": agent_soul.get("agent_name", "Qichen Agent"),
        "expertise": "Python编程与系统架构",
        "blind_spot": agent_soul.get("blind_spot", "过度工程化"),
        "experiences": agent_soul.get("experiences", []),
        "personal_rules": agent_soul.get("personal_rules", []),
        "personal_rule_history": agent_soul.get("personal_rule_history", []),
        "pattern_history": agent_soul.get("pattern_history", {}),
        "iteration": agent_soul.get("total_tasks", 0),
        "maturity": agent_soul.get("maturity", 0.0),
    }


# ═══════════════════════════════════════════
# 4. 主动建言
# ═══════════════════════════════════════════

def generate_insights(agent_soul, recent_tasks, result_count):
    """生成主动建言"""
    zhu_soul = _agent_soul_to_zhu(agent_soul)
    souls = [zhu_soul]
    team_rules = agent_soul.get("personal_rules", [])

    # 用最后一个任务作为问题
    question = recent_tasks[-1] if recent_tasks else "编程任务"
    history = [{"discussion": {}, "team_rules": team_rules}]

    suggestions = generate_proactive_suggestions(souls, team_rules, question, history)

    return {
        "suggestions": suggestions,
        "maturity": agent_soul["maturity"],
        "rule_count": len(agent_soul["personal_rules"]),
    }


# ═══════════════════════════════════════════
# 集成入口：Agent 主循环调用
# ═══════════════════════════════════════════

class ZhuHunEnhancer:
    """Zhu Hun 增强器 — Agent 主循环的每次迭代调用"""

    def __init__(self):
        self.task_count = 0
        self.recent_tasks = []
        self.acceleration_cadence = 5  # 每5个任务跑一次加速器

    def before_task(self, task, agent_soul):
        """任务前：增强规划上下文"""
        self.task_count += 1
        self.recent_tasks.append(task)
        self.recent_tasks = self.recent_tasks[-10:]  # 保留最近10个

        enhanced = enhance_planning(task, agent_soul)

        # 每 N 个任务跑一次加速器
        acceleration_events = None
        if self.task_count % self.acceleration_cadence == 0:
            acceleration_events = periodic_acceleration(agent_soul, self.task_count)

        return {
            "planning_context": enhanced["context"],
            "category": enhanced["category"],
            "team": enhanced["roles"],
            "acceleration": acceleration_events,
        }

    def after_task(self, task, code, result, agent_soul):
        """任务后：团队评审"""
        existing_rules = agent_soul.get("personal_rules", [])
        review = review_with_team(task, code, result, agent_soul, existing_rules)
        return review

    def periodic_insights(self, agent_soul):
        """定期生成主动建言"""
        if self.task_count % 10 == 0:  # 每10个任务
            return generate_insights(agent_soul, self.recent_tasks, self.task_count)
        return None


# ═══════════════════════════════════════════
# 测试
# ═══════════════════════════════════════════

if __name__ == "__main__":
    enhancer = ZhuHunEnhancer()

    # 模拟 agent soul
    fake_soul = {
        "agent_name": "Qichen Agent v2.0",
        "maturity": 0.1,
        "total_tasks": 4,
        "successful_tasks": 4,
        "personal_rules": [
            "对文件读写、网络请求、外部命令必须加 try/except",
            "执行成功时必须 print 关键结果",
        ],
        "personal_rule_history": [],
        "pattern_history": {"硬编码路径": 2, "缺失错误处理": 1},
        "experiences": [],
    }

    # 测试任务前增强
    task = "给爬虫项目添加多线程支持，同时爬取5个新闻源，结果合并去重"
    result = enhancer.before_task(task, fake_soul)

    print("=" * 60)
    print("Zhu Hun 集成层测试")
    print("=" * 60)

    print(f"\n[任务前] 问题类型: {result['category']}")
    print(f"  团队: {result['team']}")
    print(f"\n  规划上下文:\n{result['planning_context'][:500]}...")

    # 测试任务后评审
    fake_result = {"success": True}
    review = enhancer.after_task(task, "print('hello')", fake_result, fake_soul)
    print(f"\n[任务后评审]")
    print(f"  会诊次数: {len(review['consultations'])}")

    # 测试主动建言
    insights = enhancer.periodic_insights(fake_soul)
    if insights:
        print(f"\n[主动建言] {len(insights['suggestions'])}条建议")
        for s in insights["suggestions"]:
            print(f"  [{s['type']}] {s['suggestion'][:80]}...")