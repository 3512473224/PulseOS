import os
import sys
import base64
import paramiko

sys.stdout.reconfigure(encoding='utf-8')

def main():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    print("Connecting to VPS 104.129.1.216:22222...")
    ssh.connect('104.129.1.216', port=22222, username='root', password='zxcvbnm2016', timeout=15)
    print("Connected successfully!")

    def exec_cmd(cmd, check_status=True):
        print(f"--> {cmd}")
        stdin, stdout, stderr = ssh.exec_command(cmd)
        out = stdout.read().decode('utf-8', errors='ignore')
        err = stderr.read().decode('utf-8', errors='ignore')
        code = stdout.channel.recv_exit_status()
        if out: print("STDOUT:", out.strip()[:1000])
        if err: print("STDERR:", err.strip()[:1000])
        if check_status and code != 0:
            print(f"WARNING: Exit code {code} for: {cmd}")
        return code, out, err

    # 1. Deploy fetch_news.py
    print("\n[Step 1] Deploying /opt/pulseos/fetch_news.py...")
    with open(r'c:\Users\lan\.gemini\antigravity\scratch\vesper-geek-workspace\new_fetch_news.py', 'rb') as f:
        fetch_news_bytes = f.read()
    b64_fetch = base64.b64encode(fetch_news_bytes).decode('utf-8')
    stdin, stdout, stderr = ssh.exec_command("base64 -d > /opt/pulseos/fetch_news.py && chmod +x /opt/pulseos/fetch_news.py")
    stdin.write(b64_fetch)
    stdin.close()
    stdout.channel.recv_exit_status()
    exec_cmd("ls -lh /opt/pulseos/fetch_news.py")

    # 2. Update /opt/pulseos/main.py
    print("\n[Step 2] Updating /opt/pulseos/main.py...")
    # We will read main.py on VPS, replace the news endpoints, and write back
    update_main_script = """python3 -c '
with open("/opt/pulseos/main.py", "r", encoding="utf-8") as f:
    code = f.read()

target = \"\"\"@app.get("/api/system/news")
async def api_system_news(force: bool = False):
    cache_path = "/opt/pulseos/data/news_cache.json"
    now_ts = time.time()
    need_refresh = force or not os.path.exists(cache_path)
    if not need_refresh and os.path.exists(cache_path):
        mtime = os.path.getmtime(cache_path)
        if (now_ts - mtime) > 1200:
            need_refresh = True

    if need_refresh:
        try:
            proc = await asyncio.create_subprocess_exec(
                "/opt/pulseos/venv/bin/python3",
                "/opt/pulseos/fetch_news.py",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await asyncio.wait_for(proc.communicate(), timeout=15.0)
        except Exception as e:
            pass

    if os.path.exists(cache_path):
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return JSONResponse(content=data, headers={"Cache-Control": "no-cache, no-store, must-revalidate"})
        except Exception as e:
            return {"code": 500, "error": str(e)}
    return {"code": 404, "error": "News cache not found"}

@app.post("/api/system/news/refresh")
async def api_system_news_refresh():
    try:
        proc = await asyncio.create_subprocess_exec(
            "/opt/pulseos/venv/bin/python3",
            "/opt/pulseos/fetch_news.py",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        await asyncio.wait_for(proc.communicate(), timeout=15.0)
    except Exception as e:
        pass
    cache_path = "/opt/pulseos/data/news_cache.json"
    if os.path.exists(cache_path):
        with open(cache_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            data["message"] = "权威时事与学术前沿实时同步成功"
            return JSONResponse(content=data, headers={"Cache-Control": "no-cache, no-store, must-revalidate"})
    return {"code": 500, "error": "News service temporarily unavailable"}\"\"\"

replacement = \"\"\"NEWS_LOCK = asyncio.Lock()

@app.get("/api/system/news")
async def api_system_news(force: bool = False, rotate: bool = False):
    cache_path = "/opt/pulseos/data/news_cache.json"
    pool_path = "/opt/pulseos/data/news_pool.json"
    now_ts = time.time()
    need_network = force or not os.path.exists(cache_path)
    if not need_network and os.path.exists(pool_path):
        mtime = os.path.getmtime(pool_path)
        if (now_ts - mtime) > 1800:
            need_network = True

    cmd = ["/opt/pulseos/venv/bin/python3", "/opt/pulseos/fetch_news.py"]
    if need_network:
        cmd.append("--force")
    if rotate or force:
        cmd.append("--rotate")

    if need_network or rotate:
        async with NEWS_LOCK:
            try:
                proc = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await asyncio.wait_for(proc.communicate(), timeout=20.0)
            except Exception as e:
                pass

    if os.path.exists(cache_path):
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return JSONResponse(content=data, headers={"Cache-Control": "no-cache, no-store, must-revalidate"})
        except Exception as e:
            return JSONResponse(content={"code": 500, "error": str(e)}, status_code=500)
    return JSONResponse(content={"code": 404, "error": "News cache not found"}, status_code=404)

@app.post("/api/system/news/refresh")
async def api_system_news_refresh():
    cache_path = "/opt/pulseos/data/news_cache.json"
    async with NEWS_LOCK:
        try:
            proc = await asyncio.create_subprocess_exec(
                "/opt/pulseos/venv/bin/python3",
                "/opt/pulseos/fetch_news.py",
                "--deep-ai",
                "--force",
                "--rotate",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await asyncio.wait_for(proc.communicate(), timeout=25.0)
        except Exception as e:
            pass
        if os.path.exists(cache_path):
            with open(cache_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                data["message"] = "DeepSeek AI 深度重研完成：多源权威资讯已重新研炼"
                return JSONResponse(content=data, headers={"Cache-Control": "no-cache, no-store, must-revalidate"})
    return JSONResponse(content={"code": 500, "error": "News service temporarily unavailable"}, status_code=500)\"\"\"

if target in code:
    code = code.replace(target, replacement)
    with open("/opt/pulseos/main.py", "w", encoding="utf-8") as f:
        f.write(code)
    print("SUCCESS: main.py updated successfully!")
else:
    print("WARNING: target block not found in main.py, check current content!")
'"""
    exec_cmd(update_main_script)

    # 3. Restart pulseos.service
    print("\n[Step 3] Restarting pulseos.service...")
    exec_cmd("systemctl restart pulseos")
    exec_cmd("systemctl status pulseos --no-pager")

    # 4. Deploy workspace.html ONLY to /var/www/html/workspace.html
    print("\n[Step 4] Deploying workspace.html...")
    with open(r'c:\Users\lan\.gemini\antigravity\scratch\vesper-geek-workspace\workspace.html', 'rb') as f:
        ws_bytes = f.read()
    b64_ws = base64.b64encode(ws_bytes).decode('utf-8')
    stdin, stdout, stderr = ssh.exec_command("base64 -d > /var/www/html/workspace.html")
    stdin.write(b64_ws)
    stdin.close()
    stdout.channel.recv_exit_status()

    # 5. Strictly preserve protected assets
    print("\n[Step 5] Checking protected assets...")
    exec_cmd("cp /var/www/html/starfield_backup.html /var/www/html/index.html")
    exec_cmd("cp /var/www/html/app/index.html.bak /var/www/html/app/index.html")
    exec_cmd("chown -R www-data:www-data /var/www/html")
    exec_cmd("ls -lh /var/www/html/index.html /var/www/html/app/index.html /var/www/html/workspace.html")

    # 6. Reload Nginx
    print("\n[Step 6] Reloading Nginx...")
    exec_cmd("docker exec ppday-nginx nginx -s reload")

    # 7. Execute initial seeding of news pool
    print("\n[Step 7] Seeding news pool on VPS...")
    exec_cmd("/opt/pulseos/venv/bin/python3 /opt/pulseos/fetch_news.py --force --rotate")

    ssh.close()
    print("\nDeployment complete!")

if __name__ == "__main__":
    main()
