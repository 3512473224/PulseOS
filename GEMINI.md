# Persistent User Profile & Infrastructure Rules (Antigravity Memory)

## 1. User Identity & Multi-Scenario Emails
- **Username**: ppday
- **国内常用邮箱 (Domestic / China)**: `3512473224@qq.com`
- **国外闲用/日常邮箱 (Overseas Personal / Casual)**: `ppday666@gmail.com`
- **工作专用邮箱 (Work / Professional)**: `clevercccp@gmail.com`
- **GitHub**: https://github.com/3512473224/PulseOS

## 2. Preferred Tech Stack
- **后端架构 (Backend)**: **Java, Spring Boot** (用户最高优先级核心偏好)
- **前端架构 (Frontend)**: Vue 3 (Composition API), Tailwind CSS
- **容器与部署 (DevOps)**: Docker Alpine, 低内存架构把控

## 3. VPS Infrastructure & Hard Rules
- **VPS Server**: `104.129.1.216` (SSH Port: `22222`, User: `root`, OS: Debian 12, RAM: ~2GB)
- **🚫 ABSOLUTE PROHIBITION - PORT 443**: Port 443 is dedicated to Xray (X-UI VLESS Reality). **NEVER bind, alter, or touch port 443!**
- **Web & SSL**: All web services run through Nginx on port 80, paired with Cloudflare **Flexible SSL** for `ppday.site` / `www.ppday.site`.
- **Protected Assets**:
  - `/var/www/html/index.html` (Original Starfield Landing Page) is **strictly protected and MUST NOT be deleted**.
  - `/var/www/html/app/index.html` (`/app/`) hosts the PulseOS Cloud Telemetry Platform.
  - `/opt/pulseos` hosts the FastAPI backend service (`pulseos.service`, port 8000).
- **TencentDB Agent Memory**:
  - Running in Docker at `/opt/agent-memory/deploy/global-images`.
  - Panel: `http://104.129.1.216:8125`
  - Core Gateway: `http://104.129.1.216:8420` (Admin Key: `sk-mem-Q7XHl4cYK0UnrXxmYOw5J2m9ZBOYR4Ol`)
  - Proxy: `http://104.129.1.216:8096`
  - Upstream LLM: DeepSeek (`sk-59667070f6b84ce28e7ec133fbb58feb`)
