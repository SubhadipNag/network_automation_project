import json

report = {
    "device": "R2",
    "status": "Success"
    "interfaces": "up"
}

with open("R2.json", "w") as file:
    json.dump(report, file, indent=4)