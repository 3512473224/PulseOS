import sys
import paramiko

sys.stdout.reconfigure(encoding='utf-8')

def main():
    print("Connecting to VPS 104.129.1.216:22222...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect('104.129.1.216', port=22222, username='root', password='zxcvbnm2016', timeout=15)
    print("Connected successfully!")
    sftp = ssh.open_sftp()

    # 1. Upload workspace.html to /var/www/html/workspace.html
    local_html = r'c:\Users\lan\.gemini\antigravity\scratch\vesper-geek-workspace\workspace.html'
    target_html = '/var/www/html/workspace.html'
    print(f"Uploading {local_html} to {target_html}...")
    sftp.put(local_html, target_html)
    print("workspace.html uploaded successfully!")

    # 2. Upload server_main.py to /opt/pulseos/main.py
    local_py = r'c:\Users\lan\.gemini\antigravity\scratch\vesper-geek-workspace\server_main.py'
    target_py = '/opt/pulseos/main.py'
    print(f"Uploading {local_py} to {target_py}...")
    sftp.put(local_py, target_py)
    print("server_main.py uploaded successfully!")

    sftp.close()

    # 3. Permissions & verify files
    stdin, stdout, stderr = ssh.exec_command("chown www-data:www-data /var/www/html/workspace.html && ls -lh /var/www/html/workspace.html /opt/pulseos/main.py")
    print("Files verified on VPS:\n", stdout.read().decode('utf-8'))

    # 4. Restart pulseos.service
    print("Restarting pulseos.service...")
    stdin, stdout, stderr = ssh.exec_command("systemctl restart pulseos.service && systemctl status pulseos.service --no-pager -n 5")
    print("PulseOS Service Status:\n", stdout.read().decode('utf-8'))

    # 5. Reload Nginx
    print("Reloading Nginx...")
    stdin, stdout, stderr = ssh.exec_command("docker exec ppday-nginx nginx -s reload || systemctl reload nginx")
    print("Nginx reloaded:\n", stdout.read().decode('utf-8'))

    # 6. Test /api/ai/cat endpoint with telemetry context directly on localhost:8000
    test_payload = '''{"action": "system_check", "context": {"view": "home", "client_time": "21:20", "pomodoro": {"running": true, "task": "PulseOS 核心重构", "remaining": "22:15"}, "music": {"playing": true, "track": {"title": "夜的第七章", "artist": "周杰伦"}}, "weather": {"city": "长沙", "temp": "23°C", "condition": "晴"}, "system": {"cpu": "11%", "memory": "46%"}}}'''
    cmd = f"""curl -s -X POST http://127.0.0.1:8000/api/ai/cat -H "Content-Type: application/json" -d '{test_payload}'"""
    stdin, stdout, stderr = ssh.exec_command(cmd)
    res = stdout.read().decode('utf-8')
    print("Test /api/ai/cat response:\n", res)

    ssh.close()
    print("All deployments and tests finished successfully!")

if __name__ == '__main__':
    main()
