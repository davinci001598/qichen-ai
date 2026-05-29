"""
代码沙箱 — 隔离执行用户代码
"""
import subprocess
import os
import tempfile
import time
from pathlib import Path


class Sandbox:
    def __init__(self, work_dir=None, timeout=30, max_output_lines=200):
        if work_dir is None:
            work_dir = Path(__file__).parent.parent / "sandbox"
        else:
            work_dir = Path(work_dir)
            if not work_dir.is_absolute():
                work_dir = (Path(__file__).parent.parent / work_dir).resolve()
        self.work_dir = Path(work_dir)
        self.work_dir.mkdir(parents=True, exist_ok=True)
        self.timeout = timeout
        self.max_output_lines = max_output_lines

    def execute(self, code, filename=None):
        """在沙箱中执行 Python 代码"""
        if filename is None:
            filename = f"run_{int(time.time() * 1000)}.py"

        filepath = self.work_dir / filename

        # 写入代码
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(code)

        try:
            result = subprocess.run(
                ["python", str(filepath)],
                capture_output=True,
                text=True,
                timeout=self.timeout,
                cwd=str(self.work_dir),
                encoding="utf-8",
                errors="replace",
            )

            stdout = result.stdout
            stderr = result.stderr

            # 截断过长输出
            stdout_lines = stdout.split("\n")
            if len(stdout_lines) > self.max_output_lines:
                stdout = (
                    "\n".join(stdout_lines[: self.max_output_lines])
                    + f"\n... (截断，共 {len(stdout_lines)} 行)"
                )

            return {
                "success": result.returncode == 0,
                "stdout": stdout,
                "stderr": stderr,
                "returncode": result.returncode,
                "file": str(filepath),
            }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "stdout": "",
                "stderr": f"执行超时（>{self.timeout}秒）",
                "returncode": -1,
                "file": str(filepath),
            }
        except Exception as e:
            return {
                "success": False,
                "stdout": "",
                "stderr": str(e),
                "returncode": -1,
                "file": str(filepath),
            }