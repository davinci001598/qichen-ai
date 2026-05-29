"""
Soul 引擎 — 从 Zhu Hun 提取，适配编程 Agent
Agent 的任务偏好、编码规则、经验教训都沉淀在 Soul 数据结构中
每次任务完成后触发 Soul 自修改
"""
import json
import os
import copy
import random
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).parent.parent

# ═══════════════════════════════════════════
# 基础模式检测库（编程 Agent 版）
# ═══════════════════════════════════════════

TASK_PATTERNS = {
    "硬编码路径": {
        "keywords": [],
        "desc": "代码中使用了硬编码的绝对路径，换环境就跑不了",
        "check": lambda code, output: detect_hardcoded_paths(code),
        "fix": "使用 os.path.join() 或 pathlib.Path() 构造路径，避免写死 C:/Users/xxx 这类路径",
        "severity": "medium",
    },
    "缺失错误处理": {
        "keywords": [],
        "desc": "文件操作/网络请求没有 try/except，一崩全崩",
        "check": lambda code, output: detect_missing_error_handling(code),
        "fix": "对文件读写、网络请求、外部命令执行必须加 try/except，并给出清晰的错误信息",
        "severity": "high",
    },
    "过度工程化": {
        "keywords": ["class ", "def __init__", "abstract", "factory", "singleton"],
        "desc": "一个简单脚本写成了 OOP 八股文",
        "check": lambda code, output: detect_overengineering(code),
        "fix": "单文件脚本优先用函数式，超过 3 个类才开始考虑架构",
        "severity": "low",
    },
    "重复代码": {
        "keywords": [],
        "desc": "同一段逻辑出现 3 次以上，该抽函数了",
        "check": lambda code, output: detect_duplication(code),
        "fix": "提取公共逻辑为函数，参数化差异部分",
        "severity": "low",
    },
    "未关闭资源": {
        "keywords": ["open(", "sqlite3.connect(", "requests.get("],
        "desc": "文件/连接打开后没有 with 语句或 close()",
        "check": lambda code, output: detect_unclosed_resources(code),
        "fix": "文件、数据库连接、网络请求统一用 with 语句管理生命周期",
        "severity": "medium",
    },
    "缺少注释": {
        "keywords": [],
        "desc": "超过 30 行没有任何注释的代码块",
        "check": lambda code, output: detect_missing_comments(code),
        "fix": "关键逻辑块前加一行注释说明意图，不要解释代码本身在做什么",
        "severity": "low",
    },
    "输出不友好": {
        "keywords": [],
        "desc": "执行成功但没有任何结果输出，用户不知道发生了什么",
        "check": lambda code, output: detect_silent_success(code, output),
        "fix": "执行成功时必须 print 关键结果；失败时必须 print 清晰的错误描述",
        "severity": "medium",
    },
}

# ═══════════════════════════════════════════
# 检测函数
# ═══════════════════════════════════════════

def detect_hardcoded_paths(code):
    """检测硬编码路径"""
    import re
    patterns = [
        r'C:[/\\]Users[/\\]',
        r'D:[/\\]',
        r'E:[/\\]',
        r'/home/\w+/',
    ]
    count = sum(1 for p in patterns if re.search(p, code))
    return count > 2

def detect_missing_error_handling(code):
    """检测缺失错误处理"""
    has_open = "open(" in code
    has_requests = "requests" in code or "urllib" in code
    has_subprocess = "subprocess" in code or "os.system" in code
    has_try = "try:" in code
    return (has_open or has_requests or has_subprocess) and not has_try

def detect_overengineering(code):
    """检测过度工程化"""
    class_count = code.count("class ")
    lines = len(code.split("\n"))
    return class_count >= 3 and lines < 100

def detect_duplication(code):
    """检测重复代码"""
    lines = [l.strip() for l in code.split("\n") if l.strip() and not l.strip().startswith("#")]
    # 简单检测：超过 3 行完全相同的非空行
    seen = {}
    for line in lines:
        seen[line] = seen.get(line, 0) + 1
    duplicated = [line for line, count in seen.items() if count >= 3 and len(line) > 20]
    return len(duplicated) > 0

def detect_unclosed_resources(code):
    """检测未关闭资源"""
    has_open_no_with = False
    for line in code.split("\n"):
        stripped = line.strip()
        if "open(" in stripped and "with" not in stripped:
            has_open_no_with = True
            break
    return has_open_no_with

def detect_missing_comments(code):
    """检测缺少注释"""
    lines = code.split("\n")
    non_comment = [l for l in lines if l.strip() and not l.strip().startswith("#")]
    comments = [l for l in lines if l.strip().startswith("#")]
    return len(non_comment) > 50 and len(comments) < 2

def detect_silent_success(code, output):
    """检测无声成功"""
    has_print = "print(" in code
    output_empty = not output or len(output.strip()) == 0
    return not has_print or output_empty


# ═══════════════════════════════════════════
# Soul 数据结构
# ═══════════════════════════════════════════

def init_soul():
    """初始化 Agent Soul"""
    return {
        "agent_name": "Qichen Coder",
        "version": "1.0",
        "birth": datetime.now().isoformat(),
        "maturity": 0.0,
        "total_tasks": 0,
        "successful_tasks": 0,
        "personal_rules": [],       # 从经验中学到的编码规则
        "personal_rule_history": [], # 规则变更记录
        "preferences": {            # 用户偏好
            "preferred_libs": [],   # 偏好的库
            "code_style": "",       # 简洁/详细/函数式/OOP
            "common_patterns": [],  # 常见任务模式
        },
        "error_memory": [],         # 犯过的错误及修复
        "pattern_history": {},      # 各类模式出现频次
    }


def load_soul(soul_path=None):
    """加载持久化的 Soul"""
    if soul_path is None:
        soul_path = BASE_DIR / "data" / "agent_soul.json"
    
    if os.path.exists(soul_path):
        with open(soul_path, encoding="utf-8") as f:
            return json.load(f)
    return init_soul()


def save_soul(soul, soul_path=None):
    """持久化 Soul"""
    if soul_path is None:
        soul_path = BASE_DIR / "data" / "agent_soul.json"
        os.makedirs(os.path.dirname(soul_path), exist_ok=True)
    
    with open(soul_path, "w", encoding="utf-8") as f:
        json.dump(soul, f, ensure_ascii=False, indent=2)


# ═══════════════════════════════════════════
# Soul 自修改引擎
# ═══════════════════════════════════════════

def examine_task(soul, task, code, result):
    """
    检视本次任务执行，决定是否需要修改 Soul。
    返回：修改后的 soul + 修改记录列表
    """
    changes = []
    
    # 1. 统计任务
    soul["total_tasks"] += 1
    if result.get("success"):
        soul["successful_tasks"] += 1
    
    # 2. 检测编码模式问题
    code_text = code or ""
    output_text = result.get("stdout", "") + result.get("stderr", "")
    
    detected = []
    for pattern_name, pattern_info in TASK_PATTERNS.items():
        if pattern_info["check"](code_text, output_text):
            detected.append(pattern_name)
            soul["pattern_history"][pattern_name] = soul["pattern_history"].get(pattern_name, 0) + 1
    
    # 3. 对高频问题生成规则
    for pattern_name, count in soul["pattern_history"].items():
        if count >= 2 and pattern_name in TASK_PATTERNS:
            fix_rule = TASK_PATTERNS[pattern_name]["fix"]
            severity = TASK_PATTERNS[pattern_name]["severity"]
            # 检查是否已有此规则
            if not any(fix_rule in r for r in soul["personal_rules"]):
                soul["personal_rules"].append(fix_rule)
                change = {
                    "time": datetime.now().isoformat(),
                    "type": "pattern_learned",
                    "pattern": pattern_name,
                    "rule": fix_rule,
                    "severity": severity,
                    "occurrences": count,
                }
                soul["personal_rule_history"].append(change)
                changes.append(change)
    
    # 4. 任务成功 → 学习成功经验
    if result.get("success"):
        # 提取任务中的关键词，学习偏好
        task_lower = task.lower()
        if any(kw in task_lower for kw in ["爬虫", "抓取", "requests", "http"]):
            if "requests" not in str(soul["preferences"]["preferred_libs"]):
                soul["preferences"]["preferred_libs"].append("requests")
        
        if any(kw in task_lower for kw in ["数据", "表格", "csv", "excel", "统计"]):
            if "pandas" not in str(soul["preferences"]["preferred_libs"]):
                soul["preferences"]["preferred_libs"].append("pandas")
        
        if any(kw in task_lower for kw in ["图", "可视化", "chart", "plot"]):
            if "matplotlib" not in str(soul["preferences"]["preferred_libs"]):
                soul["preferences"]["preferred_libs"].append("matplotlib")
    
    # 5. 任务失败 → 记录错误
    if not result.get("success"):
        error_entry = {
            "time": datetime.now().isoformat(),
            "task": task[:120],
            "error": result.get("stderr", "")[:200],
            "retries": result.get("retries", 0),
        }
        soul["error_memory"].append(error_entry)
        # 只保留最近 20 条错误记忆
        if len(soul["error_memory"]) > 20:
            soul["error_memory"] = soul["error_memory"][-20:]
        
        # 如果反复失败，生成禁止规则
        if result.get("retries", 0) >= 3:
            fail_rule = f"任务连续失败 3 次以上：{task[:80]}。下次遇到类似需求，先确认环境依赖和路径。"
            if fail_rule not in soul["personal_rules"]:
                soul["personal_rules"].append(fail_rule)
                change = {
                    "time": datetime.now().isoformat(),
                    "type": "failure_learned",
                    "rule": fail_rule,
                    "severity": "high",
                }
                soul["personal_rule_history"].append(change)
                changes.append(change)
    
    # 6. 成熟度增长
    success_rate = soul["successful_tasks"] / max(soul["total_tasks"], 1)
    base_growth = 0.02 if result.get("success") else 0.005
    bonus = 0.01 if len(detected) == 0 else 0  # 无问题代码额外加分
    soul["maturity"] = min(1.0, soul["maturity"] + base_growth + bonus)
    
    return soul, changes, detected


def generate_soul_summary(soul):
    """生成 Soul 状态摘要，注入到代码生成的 system prompt 中"""
    rules = soul["personal_rules"]
    prefs = soul["preferences"]
    errors = soul["error_memory"]
    
    summary = ""
    
    if rules:
        summary += "## 你从经验中学到的编码规则（务必遵守）\n"
        for i, rule in enumerate(rules[-8:], 1):  # 最近 8 条
            summary += f"{i}. {rule}\n"
        summary += "\n"
    
    if prefs.get("preferred_libs"):
        summary += f"## 用户偏好库：{', '.join(prefs['preferred_libs'])}\n\n"
    
    if errors and len(errors) > 0:
        recent_errors = errors[-3:]
        summary += "## 最近犯过的错误（不要再犯）\n"
        for e in recent_errors:
            summary += f"- {e['task'][:60]} → {e['error'][:80]}\n"
        summary += "\n"
    
    summary += f"## 当前成熟度：{soul['maturity']:.0%} | 完成任务：{soul['successful_tasks']}/{soul['total_tasks']}"
    
    return summary


# ═══════════════════════════════════════════
# 十年加速器（压缩版）
# ═══════════════════════════════════════════

def accelerate(soul, num_cycles=5):
    """
    时间压缩：通过模拟任务执行加速 Soul 成长。
    每个 cycle 模拟一个"经验年"。
    """
    simulated_events = []
    
    for cycle in range(1, num_cycles + 1):
        # 随机选择一个问题模式来"体验"
        pattern = random.choice(list(TASK_PATTERNS.keys()))
        fix = TASK_PATTERNS[pattern]["fix"]
        
        # 模拟：经历这个问题 → 学习 → 内化规则
        soul["pattern_history"][pattern] = soul["pattern_history"].get(pattern, 0) + 1
        
        count = soul["pattern_history"][pattern]
        if count >= 2 and fix not in soul["personal_rules"]:
            soul["personal_rules"].append(fix)
            event = {
                "cycle": cycle,
                "event": f"经历了 {pattern} 问题 {count} 次后，学会了：{fix[:60]}",
                "maturity_gain": 0.05,
            }
            simulated_events.append(event)
            soul["personal_rule_history"].append({
                "time": f"accelerated_cycle_{cycle}",
                "type": "simulated_learning",
                "pattern": pattern,
                "rule": fix,
            })
        
        soul["maturity"] = min(1.0, soul["maturity"] + 0.03)
        soul["total_tasks"] += 1
        soul["successful_tasks"] += 1
    
    return simulated_events


if __name__ == "__main__":
    soul = init_soul()
    print("初始 Soul:", json.dumps(soul, ensure_ascii=False, indent=2)[:500])
    
    # 模拟加速
    events = accelerate(soul, 10)
    print(f"\n加速完成：{len(events)} 个学习事件")
    print(f"成熟度：{soul['maturity']:.0%}")
    print(f"规则数：{len(soul['personal_rules'])}")
    
    summary = generate_soul_summary(soul)
    print(f"\nSoul 摘要:\n{summary}")
    
    save_soul(soul)
    print("\nSoul 已保存到 data/agent_soul.json")