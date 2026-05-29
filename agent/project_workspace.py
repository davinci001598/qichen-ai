"""
项目工作区 — 让 Agent 操作多文件项目
支持：扫描目录、读取文件、写入/修改文件、执行命令
"""
import os
import subprocess
import time
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent


class ProjectWorkspace:
    """项目级工作区，Agent 在此操作多文件工程"""

    def __init__(self, project_dir):
        self.project_dir = Path(project_dir).resolve()
        self.project_dir.mkdir(parents=True, exist_ok=True)

    def scan(self, max_depth=3, ignore_patterns=None):
        """扫描项目结构"""
        if ignore_patterns is None:
            ignore_patterns = [".git", "__pycache__", ".venv", "node_modules",
                               ".idea", ".vscode", "*.pyc", ".DS_Store"]

        def should_ignore(name):
            for pat in ignore_patterns:
                if pat.startswith("*"):
                    if name.endswith(pat[1:]):
                        return True
                elif name == pat:
                    return True
            return False

        tree = []
        tree.append(f"# 项目根目录: {self.project_dir}")
        tree.append("")

        for root, dirs, files in os.walk(self.project_dir):
            # 计算深度
            rel = os.path.relpath(root, self.project_dir)
            depth = 0 if rel == "." else rel.count(os.sep) + 1
            if depth > max_depth:
                dirs.clear()
                continue

            # 过滤
            dirs[:] = [d for d in dirs if not should_ignore(d)]
            filtered_files = [f for f in files if not should_ignore(f)]

            indent = "  " * depth
            if depth == 0:
                tree.append("./")
            else:
                tree.append(f"{indent}{os.path.basename(root)}/")

            for f in sorted(filtered_files):
                filepath = os.path.join(root, f)
                size = os.path.getsize(filepath)
                tree.append(f"{indent}  {f} ({self._format_size(size)})")

        return "\n".join(tree)

    def read_file(self, relative_path):
        """读取项目中的文件"""
        filepath = (self.project_dir / relative_path).resolve()
        # 安全检查：确保在项目目录内
        if not str(filepath).startswith(str(self.project_dir)):
            return {"error": f"路径越界: {relative_path}"}

        if not filepath.exists():
            return {"error": f"文件不存在: {relative_path}"}

        try:
            with open(filepath, encoding="utf-8") as f:
                content = f.read()
            return {
                "path": str(filepath),
                "size": len(content),
                "lines": content.count("\n") + 1,
                "content": content,
            }
        except UnicodeDecodeError:
            return {"error": f"无法以 UTF-8 读取（可能是二进制文件）: {relative_path}"}

    def write_file(self, relative_path, content, overwrite=True):
        """写入/创建文件"""
        filepath = (self.project_dir / relative_path).resolve()
        if not str(filepath).startswith(str(self.project_dir)):
            return {"error": f"路径越界: {relative_path}"}

        if filepath.exists() and not overwrite:
            return {"error": f"文件已存在且不允许覆盖: {relative_path}"}

        os.makedirs(filepath.parent, exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        return {
            "action": "created" if not filepath.exists() else "overwritten",
            "path": str(filepath),
            "size": len(content),
        }

    def edit_file(self, relative_path, changes):
        """
        编辑文件（查找替换）
        changes: [{"old": "...", "new": "..."}, ...]
        """
        filepath = (self.project_dir / relative_path).resolve()
        if not str(filepath).startswith(str(self.project_dir)):
            return {"error": f"路径越界: {relative_path}"}

        if not filepath.exists():
            return {"error": f"文件不存在: {relative_path}"}

        with open(filepath, encoding="utf-8") as f:
            content = f.read()

        applied = 0
        for change in changes:
            old = change["old"]
            new = change["new"]
            if old in content:
                content = content.replace(old, new, 1)
                applied += 1

        if applied > 0:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)

        return {
            "path": str(filepath),
            "changes_requested": len(changes),
            "changes_applied": applied,
        }

    def run_command(self, command, timeout=60, cwd=None):
        """在项目环境中执行命令"""
        if cwd:
            cwd_path = (self.project_dir / cwd).resolve()
        else:
            cwd_path = self.project_dir

        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=str(cwd_path),
                encoding="utf-8",
                errors="replace",
            )
            return {
                "command": command,
                "cwd": str(cwd_path),
                "success": result.returncode == 0,
                "returncode": result.returncode,
                "stdout": result.stdout[-3000:],  # 截断
                "stderr": result.stderr[-1000:],
            }
        except subprocess.TimeoutExpired:
            return {"command": command, "error": f"超时（>{timeout}秒）", "success": False}
        except Exception as e:
            return {"command": command, "error": str(e), "success": False}

    def list_recent_changes(self, n=10):
        """列出最近修改的文件"""
        files = []
        for root, dirs, filenames in os.walk(self.project_dir):
            for f in filenames:
                fp = os.path.join(root, f)
                try:
                    mtime = os.path.getmtime(fp)
                    files.append((fp, mtime))
                except:
                    pass

        files.sort(key=lambda x: x[1], reverse=True)
        recent = []
        for fp, mtime in files[:n]:
            rel = os.path.relpath(fp, self.project_dir)
            recent.append({
                "path": rel,
                "modified": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(mtime)),
            })
        return recent

    @staticmethod
    def _format_size(size):
        if size < 1024:
            return f"{size}B"
        elif size < 1024 * 1024:
            return f"{size/1024:.1f}KB"
        else:
            return f"{size/1024/1024:.1f}MB"


def create_sample_project(workspace):
    """创建示例项目，用于测试 Agent 的多文件操作能力"""
    # 创建一个简单的 Web 爬虫项目
    workspace.write_file("README.md", """# 示例项目：简单新闻爬虫

爬取新闻标题并保存为 CSV。

## 结构
- `crawler.py` — 核心爬虫
- `utils.py` — 工具函数
- `config.json` — 配置文件
- `data/` — 输出目录
""")

    workspace.write_file("config.json", """{
  "target_url": "https://news.ycombinator.com",
  "output_file": "data/news.csv",
  "max_items": 20,
  "timeout": 10
}""")

    workspace.write_file("utils.py", """\"\"\"工具函数\"\"\"
import csv
import os
from datetime import datetime


def ensure_dir(path):
    \"\"\"确保目录存在\"\"\"
    os.makedirs(os.path.dirname(path), exist_ok=True)


def save_to_csv(data, filepath):
    \"\"\"保存数据到 CSV\"\"\"
    ensure_dir(filepath)
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
    return filepath


def log(msg):
    \"\"\"带时间戳的日志\"\"\"
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")""")

    workspace.write_file("crawler.py", """\"\"\"核心爬虫 — 模拟版本（无需网络）\"\"\"
import json
from datetime import datetime
from utils import save_to_csv, log


def load_config():
    \"\"\"加载配置\"\"\"
    with open("config.json", encoding="utf-8") as f:
        return json.load(f)


def crawl():
    \"\"\"爬取新闻（模拟数据，替换为真实请求即可）\"\"\"
    config = load_config()
    log(f"开始爬取: {config['target_url']}")

    # 模拟数据（实际使用时换成 requests + BeautifulSoup）
    news = [
        {"title": f"新闻标题 #{i}", "time": datetime.now().isoformat()}
        for i in range(1, config["max_items"] + 1)
    ]

    save_to_csv(news, config["output_file"])
    log(f"完成！共 {len(news)} 条，保存到 {config['output_file']}")
    return news


if __name__ == "__main__":
    crawl()""")

    workspace.write_file("tests/test_crawler.py", """\"\"\"爬虫测试\"\"\"
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crawler import crawl, load_config


def test_config():
    config = load_config()
    assert "target_url" in config
    assert "output_file" in config
    assert config["max_items"] > 0
    print("✓ 配置加载正常")


def test_crawl():
    result = crawl()
    assert len(result) > 0
    assert all("title" in item for item in result)
    print(f"✓ 爬取正常，共 {len(result)} 条")


if __name__ == "__main__":
    test_config()
    test_crawl()
    print("\\n全部测试通过 ✓")""")


if __name__ == "__main__":
    # 创建示例项目
    sample_dir = BASE_DIR.parent / "projects" / "demo-news-crawler"
    ws = ProjectWorkspace(sample_dir)
    create_sample_project(ws)
    print("示例项目创建完成:")
    print(ws.scan())
    print("\n最近变更:")
    for c in ws.list_recent_changes():
        print(f"  {c['path']} — {c['modified']}")