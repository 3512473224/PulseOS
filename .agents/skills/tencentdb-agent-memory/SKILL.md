---
name: tencentdb-agent-memory
description: >-
  Connects to and manages the user's remote TencentDB Agent Memory cluster on VPS (104.129.1.216).
  Use this skill whenever retrieving persistent user preferences, checking VPS server architecture rules,
  storing new memories/lessons learned, or adhering to critical infrastructure red lines (such as port 443 isolation).
---

# TencentDB Agent Memory 集群交互技能

本技能使 Antigravity 能够与部署在用户 VPS 上的 **TencentDB Agent Memory** 持久化记忆大脑进行双向交互。

## 1. 记忆服务终端配置 (Endpoints & Credentials)

- **Memory Core Gateway**: `http://104.129.1.216:8420` (v3 RPC 接口)
- **Memory Hub Panel (可视化后台)**: `http://104.129.1.216:8125`
- **Memory Proxy (大模型记忆代理)**: `http://104.129.1.216:8096`
- **Admin User Key**: `sk-mem-Q7XHl4cYK0UnrXxmYOw5J2m9ZBOYR4Ol`
- **默认实例 ID (Service ID)**: `default`

---

## 2. 核心红线与用户档案 (Core Rules & Persona)

在执行任何服务器操作前，**必须严格遵守已沉淀在记忆库中的以下铁律**：

1. **🚫 443 端口绝对红线**：
   - 443 端口已被 **Xray (X-UI VLESS Reality)** 独占运行代理节点。
   - **严禁**将 Nginx、Web 服务或任何新容器绑定到 443 端口！
   - 所有 Web 流量必须走 80 端口配合 Cloudflare **Flexible SSL** 模式。
2. **🛡️ 网站资产完整性保护**：
   - `/var/www/html/index.html`（星空动态官网落地页）**绝对不可删除或覆盖**！
   - PulseOS 平台托管在 `/app/` 路径（对应目录 `/var/www/html/app/index.html`）。
   - PulseOS 后端为 Python 3.11 FastAPI ASGI 异步服务，位于 `/opt/pulseos`，由 systemd `pulseos.service` 管理，运行在 8000 端口。
3. **💻 用户偏好技术栈**：
   - 用户名: `ppday` (邮箱: `3512473224@qq.com`)
   - 前端偏好: Vue 3 (Composition API) + Tailwind CSS + 响应式暗黑玻璃拟态。
   - 容器化偏好: Docker 超轻量 `alpine` 镜像，保持低内存开销。

---

## 3. 记忆操作工作流 (Memory Workflows)

### 3.1 读取核心记忆 (Read Core Memory)
```powershell
$headers = @{
    "Authorization" = "Bearer sk-mem-Q7XHl4cYK0UnrXxmYOw5J2m9ZBOYR4Ol"
    "x-tdai-service-id" = "default"
}
$res = Invoke-RestMethod -Uri "http://104.129.1.216:8420/v3/core/read" -Method Post -Headers $headers -Body "{}" -ContentType "application/json; charset=utf-8"
Write-Host $res.data.content
```

### 3.2 追加并持久化新的用户偏好/事实 (Ingest Conversation & Auto Extract)
```powershell
$body = @{
    session_id = "user_memory_sync"
    messages = @(
        @{ role = "user"; content = "请记住新的规则或偏好：<具体内容>" }
        @{ role = "assistant"; content = "已记住：<确认内容>" }
    )
} | ConvertTo-Json -Depth 5

$bytes = [System.Text.Encoding]::UTF8.GetBytes($body)
$headers = @{
    "Authorization" = "Bearer sk-mem-Q7XHl4cYK0UnrXxmYOw5J2m9ZBOYR4Ol"
    "x-tdai-service-id" = "default"
}
Invoke-RestMethod -Uri "http://104.129.1.216:8420/v3/conversation/add" -Method Post -Headers $headers -Body $bytes -ContentType "application/json; charset=utf-8"
```

### 3.3 快速辅助脚本
技能目录内置了封装脚本，可在终端直接调用：
- `powershell -File ./scripts/memory_tool.ps1 -Action read_core`
- `powershell -File ./scripts/memory_tool.ps1 -Action store_core -Content "..."`
- `powershell -File ./scripts/memory_tool.ps1 -Action search -Query "..."`
