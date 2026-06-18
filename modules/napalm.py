from napalm import get_network_driver

driver = get_network_driver("ios")

device = driver(
    hostname="192.168.80.129",
    username="cisco",
    password="cisco",
    optional_args={"port": 5003}
)

device.open()

facts = device.get_facts()
print(facts)
device.close()