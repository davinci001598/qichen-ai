"""测试 Zhu Hun 集成"""
import sys
sys.path.insert(0, r"E:\workbuddy\5.27单位到家\extracted\qichen-iteration\qichen-ai\agent")
sys.path.insert(0, r"E:\workbuddy\5.27单位到家\extracted\qichen-iteration\qichen-ai\zhu_hun")

from agent_core import QichenAgent

agent = QichenAgent()
print("Agent 初始化成功")
print(f"Soul 成熟度: {agent.soul['maturity']:.0%}")
print(f"Soul 规则: {len(agent.soul['personal_rules'])}条")
print(f"Zhu Hun 累计: {agent.zhu_hun.task_count}")

# 测试单任务
task = "写一个Python脚本，读取当前目录下所有txt文件，合并成一个merged.txt"
print(f"\n执行任务: {task}")
result = agent.run(task)

print(f"\n=== 最终 ===")
print(f"成功: {result['success']}")
print(f"Soul 成熟度: {agent.soul['maturity']:.0%}")
print(f"Zhu Hun 累计: {agent.zhu_hun.task_count}")

# 测试 zhu 状态
print(f"\nZhu Hun 状态:")
print(f"  累计任务: {agent.zhu_hun.task_count}")
print(f"  加速器节奏: {agent.zhu_hun.acceleration_cadence}")
print(f"  近期任务: {agent.zhu_hun.recent_tasks}")