import paramiko
import time
import requests

def main():
    print("Connecting to VPS 104.129.1.216:22222...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect('104.129.1.216', port=22222, username='root', password='zxcvbnm2016', timeout=15)
    print("Connected.")

    # 1. Upload workspace.html to /var/www/html/workspace.html
    local_html = r'c:\Users\lan\.gemini\antigravity\scratch\vesper-geek-workspace\workspace.html'
    target_html = '/var/www/html/workspace.html'
    local_vtt = r'c:\Users\lan\.gemini\antigravity\scratch\vesper-geek-workspace\Ep01_CyberPulse_HD.vtt'
    target_vtt = '/opt/alist/data/videos/Ep01_CyberPulse_HD.vtt'

    print(f"Uploading {local_html} to {target_html}...")
    sftp = ssh.open_sftp()
    sftp.put(local_html, target_html)
    print(f"Uploading {local_vtt} to {target_vtt}...")
    sftp.put(local_vtt, target_vtt)
    sftp.close()
    print("Uploads completed.")

    # 2. Set permissions
    stdin, stdout, stderr = ssh.exec_command("chown www-data:www-data /var/www/html/workspace.html && chmod 644 /var/www/html/workspace.html && ls -lh /var/www/html/workspace.html")
    print("VPS File Details:\n", stdout.read().decode('utf-8'))

    # 3. Reload Nginx
    print("Reloading Nginx...")
    stdin, stdout, stderr = ssh.exec_command("docker exec ppday-nginx nginx -s reload")
    print("Nginx reload:\n", stdout.read().decode('utf-8'), stderr.read().decode('utf-8'))

    # 4. Check AList container stats
    stdin, stdout, stderr = ssh.exec_command("docker stats ppday-alist --no-stream")
    print("AList container stats:\n", stdout.read().decode('utf-8'))

    ssh.close()

    # 5. Verify production URL
    print("Testing https://ppday.site/workspace ...")
    r = requests.get('https://ppday.site/workspace', timeout=15)
    print("Status:", r.status_code)
    print("Content length:", len(r.text))
    print("Contains view-cinema:", 'id="view-cinema"' in r.text)
    print("Contains artplayer:", 'artplayer.js' in r.text)
    print("Contains AList stream:", 'Demo-Cinema' in r.text)

if __name__ == '__main__':
    main()
