from multiprocessing import connection


output = connection.send_command("show running-config")

with open("config/R2.txt", "w") as file:
    file.write(output)