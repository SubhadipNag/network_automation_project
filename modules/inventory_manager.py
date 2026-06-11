# ============================================================
# MODULE: inventory_manager.py
# Covers: JSON API (#23), Dictionary (#7), Lists (#8),
#         Functions (#11), Exception Handling (#13),
#         File I/O, Variables (#5), For-loops (#2)
# ============================================================

import json
import os
from typing import List, Dict, Any
from datetime import datetime


INVENTORY_FILE = os.path.join(
    os.path.dirname(__file__), "..", "inventory", "devices.json"
)


def load_inventory() -> List[Dict[str, Any]]:
    """
    Load device inventory from JSON file.
    Returns an empty list if file doesn't exist.
    Covers: JSON (#23), Exception Handling (#13), Functions (#11)
    """
    try:                                                     # Exception Handling (#13)
        with open(INVENTORY_FILE, "r") as f:
            data = json.load(f)                              # JSON API (#23)
        print(f"  [INV] Loaded {len(data)} devices from inventory.")
        return data                                          # Lists (#8)
    except FileNotFoundError:
        print("  [INV] No inventory file found — starting fresh.")
        return []
    except json.JSONDecodeError as e:
        print(f"  [INV] JSON parse error: {e}")
        return []


def save_inventory(devices: List[Dict[str, Any]]) -> None:
    """
    Save device inventory to JSON file.
    Covers: JSON (#23), Exception Handling (#13), Functions (#11)
    """
    os.makedirs(os.path.dirname(INVENTORY_FILE), exist_ok=True)

    # Add a timestamp to each device entry
    for device in devices:                                   # For-loops (#2)
        device["last_updated"] = datetime.now().isoformat() # Strings (#1)

    try:
        with open(INVENTORY_FILE, "w") as f:
            json.dump(devices, f, indent=4)                  # JSON API (#23)
        print(f"  [INV] Saved {len(devices)} devices to {INVENTORY_FILE}")
    except IOError as e:                                     # Exception Handling (#13)
        print(f"  [INV] ERROR saving inventory: {e}")


def build_inventory_from_yaml(yaml_devices: list) -> List[Dict[str, Any]]:
    """
    Convert YAML-loaded device list into JSON-storable inventory.
    Covers: Dictionary (#7), Lists (#8), For-loops (#2)
    """
    inventory = []                                           # Lists (#8)

    for dev in yaml_devices:                                 # For-loops (#2)
        # Build a dictionary per device
        entry: Dict[str, Any] = {                            # Dictionary (#7)
            "name":         dev["name"],
            "host":         dev["host"],
            "telnet_port":  dev["telnet_port"],
            "ssh_port":     dev["ssh_port"],
            "username":     dev["username"],
            "password":     dev["password"],
            "platform":     dev["platform"],
            "ip_address":   dev["ip_address"],
            "loopback_ip":  dev["loopback_ip"],
            "bgp_as":       dev["bgp_as"],
            "status":       "unknown",                       # will be updated later
        }
        inventory.append(entry)

    return inventory


def update_device_status(name: str, status: str) -> None:
    """
    Update status field of a single device in inventory.
    Covers: Functions (#11), Conditional (#12), Dictionary (#7)
    """
    inventory = load_inventory()

    for device in inventory:                                 # For-loops (#2)
        if device["name"] == name:                           # Conditional (#12)
            device["status"] = status
            device["last_seen"] = datetime.now().isoformat()
            break

    save_inventory(inventory)
    print(f"  [INV] Updated {name} status → {status}")


def get_device_names() -> List[str]:
    """
    Return a list of all device names in inventory.
    Covers: List Comprehension (#16), Functions (#11)
    """
    inventory = load_inventory()
    return [d["name"] for d in inventory]                   # List Comprehension (#16)


def get_unique_platforms() -> set:
    """
    Return a set of unique platform types in inventory.
    Covers: Sets (#10), Functions (#11)
    """
    inventory = load_inventory()
    platforms = {d["platform"] for d in inventory}           # Sets (#10)
    return platforms


def print_inventory_table() -> None:
    """Pretty-print inventory as a table."""
    inventory = load_inventory()
    if not inventory:
        print("  [INV] Inventory is empty.")
        return

    print("\n  ┌─────────────────────────────────────────────────────┐")
    print("  │               DEVICE INVENTORY                      │")
    print("  ├──────┬──────────────────┬──────────┬───────────────┤")
    print("  │ Name │ IP Address       │ Platform │ Status        │")
    print("  ├──────┼──────────────────┼──────────┼───────────────┤")

    for dev in inventory:                                    # For-loops (#2)
        name     = dev.get("name", "N/A").ljust(4)
        ip       = dev.get("ip_address", "N/A").ljust(16)
        platform = dev.get("platform", "N/A").ljust(8)
        status   = dev.get("status", "unknown").ljust(13)
        print(f"  │ {name} │ {ip} │ {platform} │ {status} │")

    print("  └──────┴──────────────────┴──────────┴───────────────┘\n")
