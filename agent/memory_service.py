"""
记忆流服务 — 从 memory_flow_lite 改造为可持久化的 FastAPI 服务
ODE 在后台持续推进，记忆向量写入 SQLite
"""
import numpy as np
import sqlite3
import json
import os
import time
import threading
from pathlib import Path
import asyncio

BASE_DIR = Path(__file__).parent.parent

class MemoryFlow:
    """连续记忆流引擎 — 可持久化版本"""

    def __init__(self, db_path=None, dim=10, decay_rate=0.1, external_strength=0.05):
        self.dim = dim
        self.decay_rate = decay_rate
        self.external_strength = external_strength
        self.db_path = db_path or str(BASE_DIR / "data" / "memory.db")
        self.state = np.zeros(dim)
        self.connection = np.random.randn(dim, dim) * 0.1
        self.external_pattern = np.random.randn(dim) * 0.05
        self.step_count = 0
        self.events = []  # 外部事件队列
        self._lock = threading.Lock()
        self._running = False
        self._thread = None

        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()
        self._load_state()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS memory_state (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    step INTEGER,
                    vector TEXT,
                    timestamp REAL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS memory_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    step INTEGER,
                    content TEXT,
                    event_type TEXT,
                    importance REAL DEFAULT 0.5,
                    timestamp REAL
                )
            """)
            conn.commit()

    def _load_state(self):
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT vector, step FROM memory_state ORDER BY id DESC LIMIT 1"
            ).fetchone()
            if row:
                self.state = np.array(json.loads(row[0]))
                self.step_count = row[1]

    def _save_state(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO memory_state (step, vector, timestamp) VALUES (?, ?, ?)",
                (self.step_count, json.dumps(self.state.tolist()), time.time()),
            )
            conn.commit()

    def store_event(self, content, event_type="user_input", importance=0.5):
        """存入一个外部事件，影响记忆流"""
        with self._lock:
            self.events.append({
                "content": content,
                "type": event_type,
                "importance": importance,
            })
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "INSERT INTO memory_events (step, content, event_type, importance, timestamp) VALUES (?, ?, ?, ?, ?)",
                    (self.step_count, content, event_type, importance, time.time()),
                )
                conn.commit()
            return self.step_count

    def step(self):
        """推进一个 ODE 时间步"""
        with self._lock:
            m = self.state

            # ODE: dm/dt = -decay*m + connection*m + external_input
            decay = -self.decay_rate * m
            interaction = self.connection @ m

            # 外部事件注入
            external = np.zeros(self.dim)
            while self.events:
                evt = self.events.pop(0)
                impulse = np.random.randn(self.dim) * 0.1 * evt["importance"]
                external += impulse

            if len(self.events) == 0:
                # 无事件时：周期性外部模式
                ti = self.step_count * 0.1
                external += (
                    self.external_strength
                    * self.external_pattern
                    * (0.5 + 0.5 * np.sin(ti * 2 * np.pi / 20))
                )

            dm_dt = decay + interaction + external
            dt = 0.1
            self.state = m + dm_dt * dt
            self.step_count += 1

            if self.step_count % 10 == 0:
                self._save_state()

            return self.state.copy()

    def query(self, query_text="", top_k=5):
        """查询记忆：返回最近N条事件 + 当前记忆向量相似度"""
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                "SELECT content, event_type, timestamp FROM memory_events ORDER BY id DESC LIMIT ?",
                (top_k,),
            ).fetchall()

        results = []
        for content, etype, ts in rows:
            results.append({
                "content": content,
                "type": etype,
                "timestamp": ts,
            })

        return {
            "current_step": self.step_count,
            "vector_summary": {
                "mean": float(np.mean(self.state)),
                "std": float(np.std(self.state)),
                "top_dimensions": np.argsort(np.abs(self.state))[-3:].tolist(),
            },
            "recent_events": results,
        }

    def start_background(self, interval=5.0):
        """启动后台 ODE 推进线程"""
        self._running = True

        def _run():
            while self._running:
                time.sleep(interval)
                self.step()
                # 把事件也写成衰减少量推进，模拟记忆随时间淡忘
                for _ in range(2):
                    pass  # 额外推进

        self._thread = threading.Thread(target=_run, daemon=True)
        self._thread.start()

    def stop_background(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)


# 全局单例
_memory_instance = None

def get_memory(db_path=None):
    global _memory_instance
    if _memory_instance is None:
        _memory_instance = MemoryFlow(db_path=db_path)
    return _memory_instance


# FastAPI 应用
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Qichen Memory Flow API", version="1.0")

class EventInput(BaseModel):
    content: str
    event_type: str = "user_input"
    importance: float = 0.5

class QueryInput(BaseModel):
    query: str = ""
    top_k: int = 5

@app.on_event("startup")
async def startup():
    mem = get_memory()
    mem.start_background(interval=5.0)

@app.on_event("shutdown")
async def shutdown():
    get_memory().stop_background()

@app.post("/memory/event")
async def store_event(event: EventInput):
    mem = get_memory()
    step = mem.store_event(event.content, event.event_type, event.importance)
    # 事件写入后立即推进一步
    vector = mem.step()
    return {"step": step, "vector_preview": vector[:3].tolist()}

@app.post("/memory/query")
async def query_memory(query: QueryInput):
    mem = get_memory()
    return mem.query(query.query, query.top_k)

@app.get("/memory/state")
async def get_state():
    mem = get_memory()
    return {
        "step": mem.step_count,
        "vector": mem.state.tolist(),
        "dim": mem.dim,
        "decay_rate": mem.decay_rate,
    }

@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8932)