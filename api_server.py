"""
Qichen Agent API 服务
FastAPI 包装，部署到 Render / Railway
"""
import sys
import os
from pathlib import Path

# 强制 UTF-8 编码
os.environ["PYTHONIOENCODING"] = "utf-8"
os.environ["LANG"] = "C.UTF-8"
os.environ["LC_ALL"] = "C.UTF-8"

BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR / "agent"))
sys.path.insert(0, str(BASE_DIR / "zhu_hun"))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn

from agent_core import QichenAgent


class UTF8JSONResponse(JSONResponse):
    media_type = "application/json; charset=utf-8"


app = FastAPI(
    title="Qichen AI Agent API",
    default_response_class=UTF8JSONResponse,
)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# 全局单例 Agent
agent = QichenAgent()


class TaskRequest(BaseModel):
    task: str


class TaskResponse(BaseModel):
    success: bool
    task: str
    stdout: str = ""
    stderr: str = ""
    retries: int = 0
    maturity: float = 0.0
    rules: int = 0


@app.get("/")
def root():
    return {
        "name": "Qichen AI Agent",
        "version": "2.0",
        "status": "running",
        "maturity": f"{agent.soul['maturity']:.0%}",
        "rules": len(agent.soul["personal_rules"]),
    }


@app.get("/soul")
def get_soul():
    return {
        "maturity": agent.soul["maturity"],
        "rules": agent.soul["personal_rules"],
        "history": agent.soul.get("personal_rule_history", [])[-10:],
        "total_tasks": agent.soul.get("total_tasks", 0),
        "success_rate": agent.soul.get("success_rate", 0),
    }


@app.post("/run", response_model=TaskResponse)
def run_task(req: TaskRequest):
    try:
        result = agent.run(req.task)
        return TaskResponse(
            success=result["success"],
            task=req.task,
            stdout=result.get("stdout", ""),
            stderr=result.get("stderr", ""),
            retries=result.get("retries", 0),
            maturity=agent.soul["maturity"],
            rules=len(agent.soul["personal_rules"]),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)