# Persistent User Profile & Infrastructure Rules (Antigravity Memory)

## 1. User Identity & Multi-Scenario Emails
- **Username**: ppday
- **国内常用邮箱 (Domestic / China)**: `3512473224@qq.com`
- **国外闲用/日常邮箱 (Overseas Personal / Casual)**: `ppday666@gmail.com`
- **工作专用邮箱 (Work / Professional)**: `clevercccp@gmail.com`
- **GitHub**: https://github.com/3512473224/PulseOS
- **云端存储资产 (Cloud Storage Assets)**:
  - **夸克网盘 (Quark Drive)**: **SVIP 会员** (无上限极速下载、官方原画直连与大文件快速流传输)
  - **谷歌云盘 (Google Drive)**: **5TB 超大空间** (美西 VPS 同区高速骨干直连、典藏级原盘媒体库)

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

## 5. 纯网页端视听舱架构与用户最高偏好守则 (Web-Only Cinema Directive)
1. **🚫 坚决只用纯网页端，绝不推脱给第三方播放器 (Web-Only First Principle)**：
   - 用户坚决只在 PulseOS 网页端视听舱观看，坚决不用也不要建议使用 PotPlayer、VLC 等外部播放器。所有的音视频解码、次世代音频兼容、多音轨切换、字幕挂载、色彩调优必须 100% 在网页前端与自主后端中闭环实现。
2. **HDR 色调映射永久自适应 (Tone Mapping)**：
   - 网页端播放 HDR10 / BT.2020 视频时，必须默认提供色调映射（Cinema / Vibrant / Film 模式），彻底杜绝普通 SDR 显示器上的画面发灰发白，保证胶片级浓郁对比度与深邃黑位。
3. **次世代音频实时中继 (DTS/TrueHD to Web AAC)**：
   - 针对 Chromium 浏览器不支持的 DTS-HD MA / TrueHD 7.1 音轨，必须无缝提供后端无损视频直通 + 音频实时 AAC 重混流 (`/api/cinema/remux-stream`)，并标明国语配音与多音轨切换，确保网页端直接出声并保证音画严格同步。
4. **超大原盘安全跳转与末尾索引看门狗**：
   - 超大文件（>10GB）禁止开局直接同步调用 `currentTime` 暴力 Seek，防止网盘连接被掐断；
   - MP4 尾部 `moov` 索引加载超时（>5s 处于 `00:00 / 00:00`）必须由看门狗自动接入 FastStart 中继。
