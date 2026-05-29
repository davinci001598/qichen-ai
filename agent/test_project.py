"""测试项目模式"""
import sys
sys.path.insert(0, r"E:\workbuddy\5.27单位到家\extracted\qichen-iteration\qichen-ai\agent")

from agent_core import QichenAgent

agent = QichenAgent()
result = agent.run_project(
    "给爬虫添加日期过滤功能：在config.json中增加start_date和end_date字段，修改crawler.py读取这两个配置并在爬取时按日期过滤新闻",
    r"E:\workbuddy\5.27单位到家\extracted\qichen-iteration\projects\demo-news-crawler"
)

print("\n=== 最终结果 ===")
print(f"成功: {result['success']}")
print(f"变更文件数: {result['files_changed']}")
print(f"变更列表: {result['file_list']}")
if result.get('commands'):
    print(f"执行命令: {result['commands']}")