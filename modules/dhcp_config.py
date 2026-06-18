from multiprocessing import connection


dhcp_commands = [
    "ip dhcp pool USERS",
    "network 10.10.10.0 255.255.255.0"
    "default-router 10.10.10.1",
    "dns-server 8.8.8.8"
]

connection.send_config_set(dhcp_commands)