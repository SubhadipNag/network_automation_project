import paramiko

ssh = paramiko.SSHClient()

ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

ssh.connect(
    "192.168.80.129",
    port=5003,
    username="cisco",
    password="cisco"

)

stdin, stdout, stderr = ssh.exec_command("show ip interface brief")

print(stdout.read().decode())