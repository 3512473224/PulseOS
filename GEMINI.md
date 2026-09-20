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

## 4. 4K 大文件流媒体与播放器架构守则 (HTML5 Video & Streaming Engine)
1. **🚫 严禁对大视频 Range 流拦截 Service Worker**：
   - 绝不可在 Service Worker 的 `fetch` 事件中拦截大视频文件的 Range 请求，这会破坏 Chromium 原生 C++ 硬件解码管道，并在暂停/恢复时导致流中断挂起。视频流必须走原生浏览器直连通道。
2. **🚫 严禁播放时并发拉取大块片头缓存**：
   - 播放器启动时严禁发起后台并发的大块 Range fetch（如并发拉取 16MB 片头），这会耗尽网盘（如夸克/AList）的单连接并发配额，导致视频首帧卡死或无限加载。
3. **🚫 严禁在视频加载期间注入盲目重试 Seek**：
   - 禁止使用 `setTimeout` 盲目触发二次 `seek`，4K 原画流向网盘握手耗时较长，过早重试会中断上一条 HTTP 连接并导致播放器无声挂死。
4. **实时速率显示必须永久保留，不可被提示文案覆盖**：
   - 速率指示器（`↓ X.X MB/s · ↑ X KB/s`）必须永久独立存在，任何状态提示、解码看门狗警示语只能放在缓冲胶囊或独立徽章中，严禁覆盖下载速率数值。
5. **本地与生产一致性强制校验**：
   - 每次前端核心改动后，必须校验本地与 VPS 生产服务器的文件哈希一致性，杜绝本地修改未部署导致用户在生产端验证失败。
6. **🚫 核心播放引擎永久冻结保护 (Cinema Core Engine Frozen)**：
   - 影视视听舱核心播放管线（`artCinemaInstance` 初始化、`updateCinemaTelemetryTick` 速率引擎、`getCinemaHistory`/`saveCinemaHistory` 断点记忆、`playCinemaEpisode` 事件生命周期、`extractPath` 规范化匹配）已达到生产级高稳状态。**严禁以任何理由擅自修改、重构或触碰此处的播放核心代码，除非用户明确要求！**


