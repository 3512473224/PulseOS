import hashlib
import paramiko

def get_md5(filepath):
    h = hashlib.md5()
    with open(filepath, 'rb') as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

local_md5 = get_md5('workspace.html')
print('Local workspace.html MD5:', local_md5)

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('104.129.1.216', port=22222, username='root', password='zxcvbnm2016', timeout=15)

sftp = ssh.open_sftp()
print('Uploading workspace.html to /var/www/html/workspace.html...')
sftp.put('workspace.html', '/var/www/html/workspace.html')
sftp.close()

stdin, stdout, stderr = ssh.exec_command('md5sum /var/www/html/workspace.html')
remote_out = stdout.read().decode().strip()
print('Remote MD5 output:', remote_out)
remote_md5 = remote_out.split()[0] if remote_out else ''

ssh.close()

if local_md5 == remote_md5:
    print('[SUCCESS] MD5 VERIFICATION PASSED: Local and Production VPS are 100% IDENTICAL!')
else:
    print('[ERROR] MD5 MISMATCH: Local', local_md5, 'vs Remote', remote_md5)
    raise SystemExit(1)
