import hashlib
import paramiko

def get_md5(filepath):
    h = hashlib.md5()
    with open(filepath, 'rb') as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

local_ws_md5 = get_md5('workspace.html')
local_py_md5 = get_md5('backend/main.py')
print('Local workspace.html MD5:', local_ws_md5)
print('Local backend/main.py MD5:', local_py_md5)

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('104.129.1.216', port=22222, username='root', password='zxcvbnm2016', timeout=15)

sftp = ssh.open_sftp()
print('Uploading workspace.html to /var/www/html/workspace.html...')
sftp.put('workspace.html', '/var/www/html/workspace.html')

print('Uploading backend/main.py to /opt/pulseos/main.py...')
sftp.put('backend/main.py', '/opt/pulseos/main.py')
sftp.close()

# Verify MD5
stdin, stdout, stderr = ssh.exec_command('md5sum /var/www/html/workspace.html /opt/pulseos/main.py')
remote_out = stdout.read().decode().strip()
print('Remote MD5 output:\n' + remote_out)

lines = remote_out.splitlines()
remote_ws_md5 = lines[0].split()[0] if len(lines) > 0 else ''
remote_py_md5 = lines[1].split()[0] if len(lines) > 1 else ''

# Restart pulseos service
print('Restarting pulseos.service...')
stdin, stdout, stderr = ssh.exec_command('systemctl restart pulseos.service && systemctl is-active pulseos.service')
svc_status = stdout.read().decode().strip()
print('Service status:', svc_status)

ssh.close()

if local_ws_md5 == remote_ws_md5 and local_py_md5 == remote_py_md5:
    print('[SUCCESS] MD5 VERIFICATION PASSED: All local and remote files match 100%!')
else:
    print('[ERROR] MD5 mismatch detected!')
    raise SystemExit(1)
