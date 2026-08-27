# PulseOS (脉动云控系统) ⚡

<p align="center">
  <img src="https://img.shields.io/badge/FastAPI-0.141+-009688.svg?style=flat-square&logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/Vue-3.x-4FC08D.svg?style=flat-square&logo=vuedotjs&logoColor=white" alt="Vue 3">
  <img src="https://img.shields.io/badge/TailwindCSS-3.x-38B2AC.svg?style=flat-square&logo=tailwind-css&logoColor=white" alt="Tailwind">
  <img src="https://img.shields.io/badge/Docker-Alpine-2496ED.svg?style=flat-square&logo=docker&logoColor=white" alt="Docker">
  <img src="https://img.shields.io/badge/RAM_Usage-~46MB-success.svg?style=flat-square" alt="RAM Usage">
  <img src="https://img.shields.io/badge/License-MIT-blue.svg?style=flat-square" alt="License">
</p>

**PulseOS** 是一个专为低配云服务器（Low-spec VPS / Edge Nodes）深度优化的**超轻量、高性能全栈实时云控平台与 AI 协同工作空间**。

---

## 🌟 核心特性

- 📡 **原生 WebSocket 实时硬件遥测**：以 1Hz 频率无缝推送 CPU / 物理内存 / 磁盘 I/O / 持续运行时间及 Docker 容器拓扑。
- 📊 **动态流动性能图谱**：基于 Chart.js 实时渲染近 30 秒高精动态负载波形。
- 🛠️ **DevOps 智能网络诊断套件**：内置非阻塞 ICMP Ping 丢包探测与 HTTP/SSL 状态探测探针。
- 📋 **云端敏捷看板 (Kanban)**：内置 SQLite 3 (WAL 预写式日志模式)，支持任务 CRUD 与无锁高并发持久化。
- 🤖 **AI Agent 自主决策矩阵**：基于 SSE (Server-Sent Events) 协议实时展示智能体分析链路。
- 🎵 **Web Audio 合成器交互音效**：纯原生 Web Audio API 代码合成科幻交互提示音（支持一键静音）。
- ⚡ **极致轻量（~46MB RAM）**：后端 FastAPI 仅占 ~40MB，Docker Nginx 仅占 ~6MB，对服务器原宿主程序零干扰。

---

## 📁 目录结构

```text
.
├── backend/                  # FastAPI 异步后端
│   ├── main.py               # 核心业务接口、WebSocket 服务与 SQLite 引擎
│   └── requirements.txt      # Python 依赖清单
├── frontend/                 # 前端资源
│   ├── app/                  # PulseOS 现代化单页应用 (Vue 3 + Tailwind + Chart.js)
│   │   └── index.html
│   └── landing/              # 星空特效暗黑质感官网落地页
│       └── index.html
├── nginx/                    # 网关与反向代理
│   └── default.conf          # Nginx 路由、Gzip 压缩与 WebSocket 转发配置
├── deploy/                   # 自动化部署配置
│   ├── docker-compose.yml    # Docker Compose 一键启动模版
│   └── pulseos.service       # Systemd 守护进程与资源隔离配置
├── .gitignore
└── README.md
```

---

## 🚀 快速启动

### 1. 后端服务启动 (FastAPI)

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

### 2. Docker 容器化运行 Nginx 网关

```bash
docker run -d \
  --name pulseos-nginx \
  --restart always \
  -p 80:80 \
  -v $(pwd)/frontend:/usr/share/nginx/html:ro \
  -v $(pwd)/nginx:/etc/nginx/conf.d:ro \
  nginx:alpine
```

---

## 📖 交互式 API 接口文档

服务启动后，直接在浏览器访问即可查看并在线调试所有接口：
- **Swagger UI 交互文档**：`http://your-server/api/docs`
- **OpenAPI 规范文件**：`http://your-server/api/openapi.json`

---

## 📄 开源协议
本项目采用 [MIT License](LICENSE) 协议开源。
