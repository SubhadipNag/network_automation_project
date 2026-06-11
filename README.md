# 🌐 GNS3 Network Automation Mini Project
## Full Python Network Automation Suite — R2 & R3 with Cloud1

---

## 📁 Project Structure

```
network_automation_project/
├── README.md
├── requirements.txt
├── main.py                  ← Entry point (runs all modules)
├── config/
│   ├── devices.yaml         ← Device inventory (YAML)
│   └── acl_template.j2      ← Jinja2 ACL template
├── inventory/
│   └── devices.json         ← JSON inventory store
├── logs/
│   └── automation.log       ← Auto-generated logs
├── reports/
│   └── report.txt           ← Auto-generated report
├── templates/
│   └── dhcp_template.txt    ← DHCP config template
└── modules/
    ├── __init__.py
    ├── device_model.py      ← Pydantic models
    ├── inventory_manager.py ← JSON inventory store
    ├── telnet_module.py     ← Telnet automation
    ├── ssh_paramiko.py      ← Paramiko SSH
    ├── netmiko_module.py    ← Netmiko automation
    ├── napalm_module.py     ← NAPALM getter
    ├── api_module.py        ← GNS3 REST API (POST/JSON)
    ├── sniff_module.py      ← Packet sniffing
    ├── log_parser.py        ← Log parsing + Regex
    ├── config_gen.py        ← Config generator
    └── report_gen.py        ← Report generation
```

---

## 🖥️ GNS3 Lab Setup

### Devices
| Device | Telnet Port         | Role     |
|--------|---------------------|----------|
| R1     | 192.168.80.129:5003 | Router 1 |
| R2     | 192.168.80.129:5002 | Router 2 |
| Cloud1 | —                   | NAT/Link |

### Interfaces Used
- R1: `FastEthernet0/0` → 10.0.0.1/30
- R2: `FastEthernet0/0` → 10.0.0.2/30

---

## 🔧 Pre-requisites & Installation

### Step 1: Install Python packages
```bash
pip install netmiko napalm paramiko pydantic pyyaml scapy requests pydantic
```

### Step 2: Configure R2 and R3 via Telnet first
Use `main.py` — it auto-configures via Telnet on first run.

### Step 3: Run the project
```bash
python main.py
```
