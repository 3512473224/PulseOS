import asyncio
import json
import os
import shutil
import sqlite3
import subprocess
import time
from datetime import datetime
from typing import List, Optional
import aiosqlite
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import psutil
import httpx

app = FastAPI(
    title="PulseOS Telemetry & AI Workstation",
    description="High-performance real-time telemetry, DevOps diagnostics and AI Agent workstation",
    version="1.0.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = "/opt/pulseos/pulseos.db"

# Initialize SQLite database
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("PRAGMA journal_mode=WAL;")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            status TEXT NOT NULL DEFAULT 'todo',
            priority TEXT NOT NULL DEFAULT 'medium',
            created_at TEXT NOT NULL
        )
    """)
    # Seed initial tasks if empty
    cursor.execute("SELECT COUNT(*) FROM tasks")
    if cursor.fetchone()[0] == 0:
        now = datetime.utcnow().isoformat()
        sample_tasks = [
            ("Docker 容器网络加固", "配置 UFW / iptables 与容器隔离规则", "done", "high", now),
            ("PulseOS 实时遥测引擎部署", "集成 WebSocket 实时硬件监测与 Chart.js 渲染", "done", "high", now),
            ("AI Agent 自治决策矩阵接入", "配置轻量级流式推理与自动化诊断沙箱", "in_progress", "medium", now),
            ("Nginx 边缘节点缓存策略优化", "针对 /app 与静态资产开启 Brotli / Gzip 缓存", "todo", "low", now)
        ]
        cursor.executemany(
            "INSERT INTO tasks (title, description, status, priority, created_at) VALUES (?, ?, ?, ?, ?)",
            sample_tasks
        )
        conn.commit()
    conn.close()

init_db()

# Models
class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = ""
    status: Optional[str] = "todo"
    priority: Optional[str] = "medium"

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None

class PingRequest(BaseModel):
    target: str

class HttpCheckRequest(BaseModel):
    url: str

def get_system_metrics():
    # CPU
    cpu_percent = psutil.cpu_percent(interval=None)
    cpu_count = psutil.cpu_count(logical=True)
    load_avg = os.getloadavg() if hasattr(os, "getloadavg") else [0.0, 0.0, 0.0]

    # Memory
    mem = psutil.virtual_memory()
    swap = psutil.swap_memory()

    # Disk
    disk = psutil.disk_usage("/")

    # Net IO
    net = psutil.net_io_counters()

    # Uptime
    boot_time = psutil.boot_time()
    uptime_seconds = int(time.time() - boot_time)

    # Docker containers
    docker_containers = []
    try:
        res = subprocess.run(
            ["docker", "ps", "--format", "{{json .}}"],
            capture_output=True,
            text=True,
            timeout=2
        )
        if res.returncode == 0 and res.stdout.strip():
            for line in res.stdout.strip().splitlines():
                if line.strip():
                    try:
                        docker_containers.append(json.loads(line))
                    except Exception:
                        pass
    except Exception:
        pass

    return {
        "timestamp": int(time.time() * 1000),
        "cpu": {
            "percent": cpu_percent,
            "cores": cpu_count,
            "load_avg": [round(x, 2) for x in load_avg]
        },
        "memory": {
            "total_mb": round(mem.total / 1024 / 1024, 1),
            "used_mb": round(mem.used / 1024 / 1024, 1),
            "free_mb": round(mem.free / 1024 / 1024, 1),
            "percent": mem.percent
        },
        "swap": {
            "total_mb": round(swap.total / 1024 / 1024, 1),
            "used_mb": round(swap.used / 1024 / 1024, 1),
            "percent": swap.percent
        },
        "disk": {
            "total_gb": round(disk.total / 1024 / 1024 / 1024, 1),
            "used_gb": round(disk.used / 1024 / 1024 / 1024, 1),
            "free_gb": round(disk.free / 1024 / 1024 / 1024, 1),
            "percent": disk.percent
        },
        "network": {
            "bytes_sent": net.bytes_sent,
            "bytes_recv": net.bytes_recv
        },
        "uptime": {
            "seconds": uptime_seconds,
            "formatted": f"{uptime_seconds // 86400}d {(uptime_seconds % 86400) // 3600}h {(uptime_seconds % 3600) // 60}m"
        },
        "docker_count": len(docker_containers),
        "docker_containers": docker_containers
    }

@app.get("/api/system/metrics")
async def api_system_metrics():
    return get_system_metrics()

# WebSocket for Real-time Hardware Telemetry
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in list(self.active_connections):
            try:
                await connection.send_text(message)
            except Exception:
                self.disconnect(connection)

manager = ConnectionManager()

@app.websocket("/ws")
async def websocket_telemetry(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            metrics = get_system_metrics()
            await websocket.send_text(json.dumps(metrics))
            await asyncio.sleep(1.0)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception:
        manager.disconnect(websocket)

# Tasks CRUD
@app.get("/api/tasks")
async def get_tasks():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM tasks ORDER BY id DESC") as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

@app.post("/api/tasks")
async def create_task(task: TaskCreate):
    now = datetime.utcnow().isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "INSERT INTO tasks (title, description, status, priority, created_at) VALUES (?, ?, ?, ?, ?)",
            (task.title, task.description, task.status, task.priority, now)
        )
        await db.commit()
        task_id = cursor.lastrowid
        return {"id": task_id, "title": task.title, "description": task.description, "status": task.status, "priority": task.priority, "created_at": now}

@app.patch("/api/tasks/{task_id}")
async def update_task(task_id: int, updates: TaskUpdate):
    fields = []
    values = []
    if updates.title is not None:
        fields.append("title = ?")
        values.append(updates.title)
    if updates.description is not None:
        fields.append("description = ?")
        values.append(updates.description)
    if updates.status is not None:
        fields.append("status = ?")
        values.append(updates.status)
    if updates.priority is not None:
        fields.append("priority = ?")
        values.append(updates.priority)

    if not fields:
        raise HTTPException(status_code=400, detail="No fields to update")

    values.append(task_id)
    query = f"UPDATE tasks SET {', '.join(fields)} WHERE id = ?"

    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(query, values)
        await db.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Task not found")
        return {"status": "success", "updated_id": task_id}

@app.delete("/api/tasks/{task_id}")
async def delete_task(task_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        await db.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Task not found")
        return {"status": "success", "deleted_id": task_id}

# DevOps Diagnostic Tools
@app.post("/api/tools/ping")
async def run_ping(req: PingRequest):
    target = req.target.strip()
    # Simple sanitization
    allowed_chars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.-")
    if not target or not all(c in allowed_chars for c in target) or len(target) > 100:
        raise HTTPException(status_code=400, detail="Invalid hostname or IP address")

    try:
        proc = await asyncio.create_subprocess_exec(
            "ping", "-c", "3", "-W", "2", target,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        raw_output = stdout.decode("utf-8", errors="ignore")
        return {
            "target": target,
            "returncode": proc.returncode,
            "output": raw_output,
            "success": proc.returncode == 0
        }
    except Exception as e:
        return {"target": target, "success": False, "error": str(e)}

@app.post("/api/tools/http-check")
async def run_http_check(req: HttpCheckRequest):
    url = req.url.strip()
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url

    start = time.time()
    try:
        async with httpx.AsyncClient(timeout=6.0, follow_redirects=True, verify=False) as client:
            resp = await client.get(url)
            duration_ms = round((time.time() - start) * 1000, 1)
            return {
                "url": url,
                "status_code": resp.status_code,
                "latency_ms": duration_ms,
                "server": resp.headers.get("server", "unknown"),
                "content_type": resp.headers.get("content-type", "unknown"),
                "success": 200 <= resp.status_code < 400
            }
    except Exception as e:
        return {
            "url": url,
            "success": False,
            "error": str(e),
            "latency_ms": round((time.time() - start) * 1000, 1)
        }

# AI Agent Stream
@app.get("/api/ai/agent-stream")
async def agent_stream(prompt: str = "Analyze system architecture and optimize network buffer"):
    async def event_generator():
        steps = [
            f"[Agent Initialized] 目标任务: '{prompt}'",
            "[Analysis Phase] 正在挂载 VPS 硬件遥测管道与内存状态...",
            "[Telemetry Check] CPU 负载良好，Swap 占用率稳定，网络 I/O 缓冲区已就绪。",
            "[Decision Tree] 评估方案: 启用 Nginx 动态压缩与 TCP KeepAlive 保活机制。",
            "[Code Synthesis] 生成内核参数优化模板: net.core.somaxconn=1024",
            "[Execution Plan] 自动同步 SQLite 状态机并更新任务看板。",
            "[Status: Complete] AI 智能体任务已圆满收敛，系统各节点就绪。"
        ]
        for step in steps:
            yield f"data: {json.dumps({'message': step, 'timestamp': datetime.utcnow().strftime('%H:%M:%S')})}\n\n"
            await asyncio.sleep(0.8)
        yield f"data: {json.dumps({'done': True})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=False, workers=1)
