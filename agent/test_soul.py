"""Qichen Agent v2.0 测试 — 含 Soul 引擎"""
import sys
sys.path.insert(0, "E:/workbuddy/5.27单位到家/extracted/qichen-iteration/qichen-ai/agent")

from agent_core import QichenAgent

agent = QichenAgent()

# 先看看初始 Soul
agent.show_soul()

# 任务1：写一个简单的数据分析脚本（会检测编码模式）
print("\n\n" + "="*60)
print("测试任务 1：基本文件操作")
print("="*60)
result1 = agent.run(
    "读取 sandbox/test.txt 文件内容，统计字符数和单词数，输出统计结果"
)

print(f"\n任务1结果: {'成功' if result1['success'] else '失败'}")

# 任务2：再跑一个（看Soul是否有积累）
print("\n\n" + "="*60)
print("测试任务 2：计算任务")
print("="*60)
result2 = agent.run(
    "计算斐波那契数列前 20 个数字并打印"
)

print(f"\n任务2结果: {'成功' if result2['success'] else '失败'}")

# 最终 Soul 状态
print("\n\n最终 Soul 状态：")
agent.show_soul()