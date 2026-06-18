import yaml
import json
from netmiko import ConnectHandler
from threading import Thread

def configure_device(device):

    try:

        connection = ConnectHandler(
            device_type="cisco_ios_telnet",
            host=device["host"],
            port=device["telnet_port"],
            username=device["username"],
            password=device["password"]
        )

        print(f"Connected to {device['name']}")

        # Push Configuration File
        if device["name"] == "R2":
            connection.send_config_from_file("configs/R2.txt")
            output = connection.send_command(
                "show ip interface brief"
            )

            print(output)

            running = connection.send_command(
                "show running-config"
            )

            report = {
                "device": device["name"],
                "host": device["host"],
                "status": "Success"
            }

            with open(
                f"{device['name']}.json",
                "w"
            ) as file:
                json.dump(
                    report,
                    file,
                    indent=4
                )

        connection.disconnect()
    except Exception as e:
        print(
            f"Failed on {device['name']}"
        )

        print(e)

with open(
    "devices.yaml", "r") as file:
    data = yaml.safe_load(file)
    print(data)

threads = []

for device in data["routers"]:

    t = Thread(
        target=configure_device,
        args=(device,)

    )

    t.start()

    threads.append(t)

for t in threads:

    t.join()

print("Automation Complete")