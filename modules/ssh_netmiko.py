from netmiko import ConnectHandler

device = {
    "device_type": "cisco_ios_telnet",
    "host": "192.168.80.129",
    "port": 5003,
    "username": "cisco",
    "password": "cisco"
}

connection = ConnectHandler(**device)

output = connection.send_command("show ip interface brief")

print(output)

connection.disconnect()