"""
DeepSeek API 客户端 — 支持 deepseek-chat / deepseek-coder
"""
import httpx
import json
import yaml
from pathlib import Path

BASE_DIR = Path(__file__).parent

def load_config():
    with open(BASE_DIR / "config.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)


class LLMClient:
    def __init__(self, config=None):
        if config is None:
            config = load_config()
        llm_cfg = config["llm"]
        self.api_key = llm_cfg["api_key"]
        self.model = llm_cfg["model"]
        self.base_url = llm_cfg.get("base_url", "https://api.deepseek.com/v1")
        self.max_tokens = llm_cfg.get("max_tokens", 4096)
        self.temperature = llm_cfg.get("temperature", 0.3)

    def chat(self, messages, system_prompt=None):
        """发送聊天请求"""
        full_messages = []
        if system_prompt:
            full_messages.append({"role": "system", "content": system_prompt})

        if isinstance(messages, str):
            full_messages.append({"role": "user", "content": messages})
        else:
            full_messages.extend(messages)

        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        body = {
            "model": self.model,
            "messages": full_messages,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
        }

        with httpx.Client(timeout=120) as client:
            resp = client.post(url, headers=headers, json=body)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]

    def generate_code(self, task, context="", memory_context=""):
        """生成代码"""
        system = """你是一个Python编程助手。根据用户需求生成可直接运行的Python代码。

规则：
1. 只输出代码，放在 ```python ``` 代码块中
2. 代码必须完整、可独立运行
3. 不要使用未安装的第三方库（只用标准库或 numpy/matplotlib）
4. 如果任务涉及文件操作，使用绝对路径
5. 输出结果用 print() 打印
6. 错误处理用 try/except，出错时打印错误信息

如果任务无法用代码完成，输出：CANNOT_CODE: <原因>"""

        prompt = f"任务：{task}\n\n"

        if context:
            prompt += f"上下文信息：\n{context}\n\n"

        if memory_context:
            prompt += f"历史记忆：\n{memory_context}\n\n"

        prompt += "请生成代码："

        return self.chat(prompt, system_prompt=system)

    def plan(self, task, memory_context=""):
        """规划任务步骤"""
        system = """你是一个任务规划助手。将用户需求拆解为可执行的步骤。

输出格式（JSON）：
{
    "steps": [
        {"action": "code", "description": "具体操作描述"},
        {"action": "code", "description": "下一步操作"}
    ],
    "tools_needed": ["python", "file"],
    "expected_output": "预期产出描述"
}

注意：
- 每个步骤要具体、可执行
- 优先用代码完成，实在不行再标记为 manual
"""

        prompt = f"任务：{task}\n"

        if memory_context:
            prompt += f"\n历史记忆：\n{memory_context}\n"

        return self.chat(prompt, system_prompt=system)

    def generate_project_code(self, task, project_context, memory_context=""):
        """项目级代码生成 — 理解整个项目后操作多文件"""
        system = """你是一个项目级编程助手。你可以操作整个项目的多个文件。

输出格式：用 ```file:<相对路径>``` 标记每个文件的操作，例如：

```file:fix_bug.py
# 新建文件的完整代码
```

```file:utils.py
# 修改已有文件的完整新内容
```

```file:README.md
# 更新文档
```

规则：
1. 每个要操作的文件，单独一个 ```file:<路径>``` 代码块
2. 路径是相对于项目根目录的文件名，不要包含项目根目录名称本身
3. 新建文件写完整代码，修改文件写完整新内容（不是 diff）
4. 如果只需执行命令，用 ```command:<命令>``` 标记（命令在项目根目录执行）
5. 只用标准库或项目已有依赖
6. 错误处理用 try/except

如果任务无法用代码完成，输出：CANNOT_CODE: <原因>"""

        prompt = f"任务：{task}\n\n"
        prompt += f"项目结构：\n{project_context}\n\n"

        if memory_context:
            prompt += f"历史记忆：\n{memory_context}\n\n"

        prompt += "请生成代码（用 file: 标记每个文件）："

        return self.chat(prompt, system_prompt=system)

    def reflect(self, task, code, output, error=None):
        """反思代码执行结果，改进代码"""
        system = """你是一个代码审查助手。分析代码执行结果，判断是否成功，如果不成功则给出改进方案。

输出格式（JSON）：
{
    "success": true/false,
    "analysis": "一句话分析",
    "fix": "如果需要修复，描述修复方案；如果成功，留空"
}"""

        prompt = f"""原始任务：{task}

执行的代码：
{code}

执行输出：
{output[:2000] if output else '(无输出)'}
"""

        if error:
            prompt += f"\n错误信息：\n{error}"

        return self.chat(prompt, system_prompt=system)


if __name__ == "__main__":
    client = LLMClient()
    result = client.chat("你好，请用一句话介绍自己")
    print(result)