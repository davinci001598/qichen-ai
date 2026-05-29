"""
Qichen Agent 主循环 v2.0
整合 Memory Flow + LLM + Sandbox + Soul Engine
"""
import json
import re
import yaml
import time
from pathlib import Path
import httpx

BASE_DIR = Path(__file__).parent

from llm_client import LLMClient, load_config
from sandbox import Sandbox
from memory_service import get_memory
from soul_engine import init_soul, load_soul, save_soul, examine_task, accelerate, generate_soul_summary
from cognition_service import inject_cognition_to_context
from project_workspace import ProjectWorkspace
from zhu_hun_integration import ZhuHunEnhancer


def extract_code(text):
    """从 LLM 回复中提取代码块"""
    pattern = r"```python\s*\n(.*?)```"
    matches = re.findall(pattern, text, re.DOTALL)
    if matches:
        return matches[0].strip()
    pattern2 = r"```\s*\n(.*?)```"
    matches2 = re.findall(pattern2, text, re.DOTALL)
    if matches2:
        return matches2[0].strip()
    return None


def extract_json(text):
    """从文本中提取 JSON"""
    pattern = r"\{[\s\S]*\}"
    match = re.search(pattern, text)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            return None
    return None


def extract_project_changes(text):
    """从 LLM 回复中提取多文件变更
    返回: {"files": {"路径": "内容"}, "commands": ["命令1"]}
    """
    changes = {"files": {}, "commands": []}

    # 匹配 ```file:路径\n...```
    file_pattern = r"```file:(.+?)\n(.*?)```"
    for match in re.finditer(file_pattern, text, re.DOTALL):
        path = match.group(1).strip()
        content = match.group(2).strip()
        changes["files"][path] = content

    # 匹配 ```command:命令```
    cmd_pattern = r"```command:(.+?)```"
    for match in re.finditer(cmd_pattern, text, re.DOTALL):
        changes["commands"].append(match.group(1).strip())

    return changes


class QichenAgent:
    """启辰编程 Agent v2.0 — 带 Soul 引擎"""

    def __init__(self):
        config = load_config()
        self.llm = LLMClient(config)
        self.sandbox = Sandbox(
            work_dir=config["sandbox"]["work_dir"],
            timeout=config["sandbox"]["timeout"],
            max_output_lines=config["sandbox"]["max_output_lines"],
        )
        self.memory = get_memory(db_path=config["memory"]["db_path"])
        self.max_retries = 3
        self.history = []

        # ═══ Soul 引擎 ═══
        self.soul = load_soul()
        self.soul_path = BASE_DIR.parent / "data" / "agent_soul.json"

        # ═══ Zhu Hun 铸魂增强器 ═══
        self.zhu_hun = ZhuHunEnhancer()

    def run(self, task):
        """执行一个编程任务（含 Soul 自修改 + Zhu Hun 增强）"""
        print(f"\n{'='*60}")
        print(f"Qichen Agent 收到任务：{task}")
        print(f"  Soul 成熟度: {self.soul['maturity']:.0%} | 规则: {len(self.soul['personal_rules'])}条")
        print(f"{'='*60}")

        # ═══ Zhu Hun 任务前增强 ═══
        zh_result = self.zhu_hun.before_task(task, self.soul)
        if zh_result.get("acceleration"):
            print(f"  [Zhu Hun 加速器] 运行完成")

        # 1. 存入记忆
        self.memory.store_event(f"[任务] {task}", "task", importance=0.8)
        self.memory.step()

        # 2. 获取上下文（记忆 + Soul + Zhu Hun 团队视角）
        memory_ctx = self._get_memory_context()
        soul_ctx = generate_soul_summary(self.soul)
        cognition_ctx = inject_cognition_to_context(memory_ctx)
        zhu_hun_ctx = zh_result.get("planning_context", "")
        full_context = f"{zhu_hun_ctx}\n\n{soul_ctx}\n\n{cognition_ctx}".strip()

        # 3. 规划
        print(f"\n[1/5] 规划中... (Zhu Hun: {zh_result['category']}, 团队: {zh_result['team']})")
        plan_text = self.llm.plan(task, memory_context=full_context)
        plan = extract_json(plan_text)
        if plan:
            steps = plan.get("steps", [])
            print(f"  计划: {len(steps)} 步")
            for i, s in enumerate(steps, 1):
                print(f"    步骤{i}: {s['description'][:60]}")
        else:
            print("  规划失败，直接生成代码")

        # 4. 生成代码
        print("\n[2/5] 生成代码...")
        context = json.dumps(plan, ensure_ascii=False) if plan else ""
        code = self.llm.generate_code(task, context=context, memory_context=full_context)

        if code and "CANNOT_CODE:" in code:
            reason = code.split("CANNOT_CODE:")[-1].strip()
            print(f"\n  无法用代码完成: {reason}")
            output = {"success": False, "reason": reason, "type": "cannot_code", "code": "", "stdout": "", "stderr": reason, "retries": 0}
            self._update_soul(task, "", output)
            return output

        extracted = extract_code(code)
        if not extracted:
            print("  未提取到有效代码")
            output = {"success": False, "reason": "未生成有效代码", "type": "no_code", "code": code or "", "stdout": "", "stderr": "LLM 未生成代码块", "retries": 0}
            self._update_soul(task, code or "", output)
            return output

        print(f"  代码: {len(extracted)} 字符")

        # 5. 沙箱执行
        print("\n[3/5] 沙箱执行...")
        result = self.sandbox.execute(extracted)

        if result["success"]:
            print(f"  执行成功 ✓")
            self.memory.store_event(f"[成功] {task[:80]}", "success", importance=0.6)
        else:
            print(f"  执行失败: {result['stderr'][:100]}")

        # 6. 反思与重试
        retry = 0
        while not result["success"] and retry < self.max_retries:
            retry += 1
            print(f"\n[3.{retry}/5] 反思重试 ({retry}/{self.max_retries})...")

            reflect_text = self.llm.reflect(
                task, extracted, result.get("stdout", ""), result.get("stderr", "")
            )
            reflection = extract_json(reflect_text)

            if reflection and reflection.get("fix"):
                print(f"  修复: {reflection['fix'][:80]}")
                code = self.llm.generate_code(
                    f"{task}\n\n上次错误: {result['stderr'][:500]}\n修复方案: {reflection['fix']}",
                    memory_context=full_context,
                )
                extracted = extract_code(code)
                if extracted:
                    result = self.sandbox.execute(extracted)
                    if result["success"]:
                        print("  重试成功 ✓")
                        self.memory.store_event(f"[重试成功] {task[:80]}", "retry_success", importance=0.5)
                    else:
                        print(f"  重试失败: {result['stderr'][:100]}")

        # 7. 记忆更新
        self.memory.store_event(
            f"[结果] {'成功' if result['success'] else '失败'}: {task[:100]}",
            "result", importance=0.7,
        )
        self.memory.step()

        # 8. 组装结果
        output = {
            "task": task,
            "success": result["success"],
            "code": extracted,
            "stdout": result.get("stdout", ""),
            "stderr": result.get("stderr", ""),
            "retries": retry,
            "file": result.get("file", ""),
        }

        # 9. Soul 自修改
        print("\n[4/5] Soul 检视...")
        self._update_soul(task, extracted, output)

        # 9.5. Zhu Hun 团队评审
        review = self.zhu_hun.after_task(task, extracted, output, self.soul)
        if review["consultations"]:
            print(f"  [Zhu Hun 三方会诊] {len(review['consultations'])}次, "
                  f"采纳{len(review['approved'])}, 驳回{len(review['rejected'])}")

        # 10. 完成
        print(f"\n[5/5] 完成")
        return output

    def run_project(self, task, project_dir):
        """项目级任务 — 操作多文件工程"""
        ws = ProjectWorkspace(project_dir)
        print(f"\n{'='*60}")
        print(f"Qichen Agent 项目模式")
        print(f"  项目: {project_dir}")
        print(f"  Soul 成熟度: {self.soul['maturity']:.0%}")
        print(f"{'='*60}")

        # 1. 扫描项目
        print("\n[1/6] 扫描项目结构...")
        tree = ws.scan()
        print(tree[:500])

        # 2. 获取上下文
        memory_ctx = self._get_memory_context()
        soul_ctx = generate_soul_summary(self.soul)

        # 3. 生成多文件代码
        print("\n[2/6] 分析项目并生成变更...")
        project_context = f"项目结构:\n{tree}\n\nSoul: {soul_ctx}"
        full_context = f"{soul_ctx}\n\n{memory_ctx}".strip()

        code_text = self.llm.generate_project_code(task, project_context, memory_context=full_context)

        if code_text and "CANNOT_CODE:" in code_text:
            reason = code_text.split("CANNOT_CODE:")[-1].strip()
            print(f"  无法完成: {reason}")
            return {"success": False, "reason": reason, "type": "cannot_code"}

        changes = extract_project_changes(code_text)
        if not changes["files"] and not changes["commands"]:
            print("  未提取到有效的文件变更")
            print(f"  LLM 原始输出(前300字):\n{code_text[:300]}")
            return {"success": False, "reason": "未生成有效变更", "type": "no_changes"}

        print(f"  文件变更: {len(changes['files'])} 个 | 命令: {len(changes['commands'])} 个")
        for fpath in changes["files"]:
            print(f"    → {fpath}")

        # 4. 写入文件
        print("\n[3/6] 写入文件...")
        results = []
        for fpath, content in changes["files"].items():
            r = ws.write_file(fpath, content)
            results.append(r)
            status = r["action"]
            print(f"  {status}: {fpath} ({r.get('size', 0)} 字符)")

        # 5. 执行命令
        print("\n[4/6] 执行命令...")
        cmd_results = []
        for cmd in changes["commands"]:
            r = ws.run_command(cmd)
            cmd_results.append(r)
            icon = "✓" if r.get("success") else "✗"
            print(f"  {icon} {cmd}")
            if r.get("stdout"):
                print(f"    {r['stdout'][:200]}")

        # 6. 写回记忆
        self.memory.store_event(f"[项目任务] {task}", "project_task", importance=0.8)
        self.memory.store_event(
            f"[项目结果] {len(changes['files'])} 文件变更, {len(cmd_results)} 命令执行",
            "project_result", importance=0.7,
        )
        self.memory.step()

        # 7. Soul 更新
        print("\n[5/6] Soul 检视...")
        code_snippet = "\n".join(f"{k}: {v[:100]}" for k, v in changes["files"].items())
        result_data = {
            "success": True,
            "stdout": f"{len(changes['files'])} files, {len(cmd_results)} commands",
            "stderr": "",
        }
        self._update_soul(task, code_snippet, result_data)

        # Zhu Hun 团队评审
        review = self.zhu_hun.after_task(task, code_snippet, result_data, self.soul)
        if review["consultations"]:
            print(f"  [Zhu Hun 三方会诊] 采纳{len(review['approved'])}, 驳回{len(review['rejected'])}")

        output = {
            "task": task,
            "project": str(project_dir),
            "files_changed": len(changes["files"]),
            "file_list": list(changes["files"].keys()),
            "commands": changes["commands"],
            "cmd_results": cmd_results,
            "success": True,
        }

        print(f"\n[6/6] 完成 ✓")
        print(f"  最新结构:")
        print(ws.scan()[:400])

        return output

    def _update_soul(self, task, code, result):
        """任务完成后更新 Soul"""
        self.soul, changes, detected = examine_task(self.soul, task, code, result)
        save_soul(self.soul, self.soul_path)

        if changes:
            print(f"  ★ Soul 更新: {len(changes)} 条新规则")
            for c in changes:
                print(f"    - [{c.get('type', '')}] {c.get('rule', '')[:80]}")
        if detected:
            print(f"  ⚠ 检测到问题: {', '.join(detected)}")
        print(f"  成熟度: {self.soul['maturity']:.0%} | 规则: {len(self.soul['personal_rules'])}条 | 成功率: {self.soul['successful_tasks']}/{self.soul['total_tasks']}")

    def _get_memory_context(self):
        """获取记忆上下文摘要"""
        mem = self.memory.query(top_k=8)
        if not mem["recent_events"]:
            return ""
        lines = []
        for evt in mem["recent_events"]:
            lines.append(f"[{evt['type']}] {evt['content'][:120]}")
        return "\n".join(lines)

    def accelerate_soul(self, years=5):
        """运行 Soul 十年加速器"""
        print(f"\n[加速器] 模拟 {years} 年经验压缩...")
        events = accelerate(self.soul, years)
        save_soul(self.soul, self.soul_path)
        for e in events:
            print(f"  Year {e['cycle']}: {e['event']}")
        print(f"\n  加速后成熟度: {self.soul['maturity']:.0%} | 规则: {len(self.soul['personal_rules'])}条")

    def show_soul(self):
        """展示 Soul 状态"""
        print(f"\n{'='*50}")
        print(f"  Agent Soul — {self.soul['agent_name']}")
        print(f"{'='*50}")
        print(f"  出生: {self.soul.get('birth', '?')[:19]}")
        print(f"  成熟度: {self.soul['maturity']:.0%}")
        print(f"  总任务: {self.soul['total_tasks']} | 成功: {self.soul['successful_tasks']}")
        print(f"  编码规则 ({len(self.soul['personal_rules'])}条):")
        for i, r in enumerate(self.soul['personal_rules'], 1):
            print(f"    {i}. {r[:80]}")
        if self.soul['error_memory']:
            print(f"  错误记忆 ({len(self.soul['error_memory'])}条，最近3条):")
            for e in self.soul['error_memory'][-3:]:
                print(f"    - {e['task'][:60]} → {e['error'][:60]}")
        if self.soul['preferences'].get('preferred_libs'):
            print(f"  偏好库: {', '.join(self.soul['preferences']['preferred_libs'])}")
        print(f"  模式统计: {json.dumps(self.soul['pattern_history'], ensure_ascii=False)}")
        print(f"{'='*50}")


def interactive():
    """交互式模式"""
    agent = QichenAgent()

    print("╔══════════════════════════════════════════╗")
    print("║    启辰 AI 编程 Agent v2.0               ║")
    print("║    Memory Flow + DeepSeek + Soul Engine  ║")
    print("╚══════════════════════════════════════════╝")
    print(f"\nSoul 成熟度: {agent.soul['maturity']:.0%} | 规则: {len(agent.soul['personal_rules'])}条")
    print("命令: soul(查看Soul) | accelerate(加速器) | memory(记忆) | zhu(Zhu Hun)")
    print("      project <目录> <任务>(项目模式) | quit\n")

    while True:
        try:
            task = input("\n>>> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n再见！")
            break

        if not task:
            continue
        if task.lower() in ("quit", "exit", "q"):
            print("再见！")
            break
        if task.lower() == "soul":
            agent.show_soul()
            continue
        if task.lower().startswith("accelerate"):
            parts = task.split()
            years = int(parts[1]) if len(parts) > 1 else 5
            agent.accelerate_soul(years)
            continue
        if task.lower() == "memory":
            mem = agent.memory.query(top_k=10)
            print(f"\n记忆状态 (step {mem['current_step']}):")
            print(f"  向量均值: {mem['vector_summary']['mean']:.4f}")
            print(f"  向量标准差: {mem['vector_summary']['std']:.4f}")
            print(f"  最近事件:")
            for evt in mem["recent_events"]:
                print(f"    [{evt['type']}] {evt['content'][:80]}")
            continue
        if task.lower() == "zhu":
            print(f"\n{'='*50}")
            print(f"  Zhu Hun 铸魂增强器")
            print(f"{'='*50}")
            print(f"  累计任务: {agent.zhu_hun.task_count}")
            print(f"  加速器节奏: 每{agent.zhu_hun.acceleration_cadence}个任务")
            print(f"  近期任务:")
            for t in agent.zhu_hun.recent_tasks[-5:]:
                print(f"    - {t[:60]}")
            print(f"{'='*50}")
            continue
        if task.lower().startswith("project "):
            parts = task.split(" ", 2)
            if len(parts) < 3:
                print("用法: project <项目目录绝对路径> <任务描述>")
                continue
            project_dir = parts[1].strip('"')
            project_task = parts[2]
            result = agent.run_project(project_task, project_dir)
            if result.get("success"):
                print(f"\n✓ 项目任务完成 — {result['files_changed']} 个文件变更")
                for f in result.get("file_list", []):
                    print(f"  {f}")
            else:
                print(f"\n✗ 失败: {result.get('reason', '未知')}")
            continue

        result = agent.run(task)

        if result.get("success"):
            print(f"\n✓ 任务完成")
            if result.get("stdout"):
                print(f"输出:\n{result['stdout'][:500]}")
        else:
            print(f"\n✗ 任务失败: {result.get('reason', result.get('stderr', '未知错误')[:200])}")


if __name__ == "__main__":
    interactive()