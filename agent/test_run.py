"""Qichen Agent 快速测试"""
import sys
sys.path.insert(0, "E:/workbuddy/5.27单位到家/extracted/qichen-iteration/qichen-ai/agent")

from agent_core import QichenAgent

agent = QichenAgent()
result = agent.run(
    "在 E:/workbuddy/5.27单位到家/extracted/qichen-iteration/qichen-ai/sandbox 目录下创建一个 test.txt 文件，写入 Hello from Qichen Agent"
)

print("\n=== FINAL ===")
print(f"成功: {result['success']}")
print(f"输出: {result.get('stdout','')[:300]}")
print(f"错误: {result.get('stderr','')[:200]}")
print(f"重试次数: {result['retries']}")