# ============================================================
# MODULE: netmiko_module.py
# Covers: Netmiko (#28/#32/#33/#36/#37),
#         Functions (#11), Exception Handling (#13),
#         Strings (#1), Lists (#8), Dictionary (#7),
#         For-loops (#2), Conditional (#12),
#         Variables (#5), Numbers (#3), Operators (#4),
#         Advanced Functions (#14), List Comprehension (#16),
#         Regex (#19), While Loop (#6)
# ============================================================

import re                                                    # Regex (#19)
import time
from typing import List, Dict, Optional
from netmiko import ConnectHandler                           # Netmiko (#28)
from netmiko.exceptions import NetmikoTimeoutException, NetmikoAuthenticationException


def netmiko_connect(device: dict):
    """
    Create a Netmiko connection from a device dict.
    Covers: Netmiko (#28), Exception Handling (#13)
    """
    connection_params = {                                    # Dictionary (#7)
        "device_type": device["platform"],
        "host":        device["host"],
        "port":        device["ssh_port"],
        "username":    device["username"],
        "password":    device["password"],
        "secret":      device["enable_password"],
        "timeout":     15,
        "session_log": None,
    }
    try:
        conn = ConnectHandler(**connection_params)           # Netmiko (#28)
        conn.enable()
        return conn
    except NetmikoAuthenticationException as e:              # Exception Handling (#13)
        raise PermissionError(f"Auth failed for {device['name']}: {e}")
    except NetmikoTimeoutException as e:
        raise TimeoutError(f"Timeout for {device['name']}: {e}")
    except Exception as e:
        raise ConnectionError(f"Netmiko connect error: {e}")


# ── 1. Send Show Commands (#36)
def netmiko_send_commands(device: dict, commands: List[str]) -> Dict[str, str]:
    """
    Send multiple show commands to a device.
    Covers: Netmiko Send Commands (#36), Dictionary (#7), For-loops (#2)
    """
    results: Dict[str, str] = {}                             # Dictionary (#7)
    try:
        conn = netmiko_connect(device)
        for cmd in commands:                                 # For-loops (#2)
            output = conn.send_command(cmd)                  # Netmiko (#36)
            results[cmd] = output
            print(f"      » {cmd} — {len(output)} chars returned")
        conn.disconnect()
    except Exception as e:                                   # Exception Handling (#13)
        results["error"] = str(e)
    return results


# ── 2. Send Multi-line Commands (#37)
def netmiko_send_multiline(device: dict, config_commands: List[str]) -> str:
    """
    Push a config block (multi-line) via Netmiko.
    Covers: Netmiko Multiline (#37), Lists (#8)
    """
    try:
        conn = netmiko_connect(device)
        output = conn.send_config_set(config_commands)       # Netmiko (#37)
        conn.save_config()
        conn.disconnect()
        print(f"    [NM] ✓ Config pushed to {device['name']}")
        return output
    except Exception as e:                                   # Exception Handling (#13)
        return f"ERROR: {e}"


# ── 3. Interface Status (#32)
def netmiko_interface_status(device: dict) -> List[Dict[str, str]]:
    """
    Get interface status and parse with Regex.
    Covers: Netmiko Interface Status (#32), Regex (#19),
            List Comprehension (#16), Dictionary (#7)
    """
    try:
        conn = netmiko_connect(device)
        raw = conn.send_command("show interfaces")           # Netmiko (#36)
        conn.disconnect()
    except Exception as e:                                   # Exception Handling (#13)
        return [{"error": str(e)}]

    # Regex to extract interface name + status
    pattern = re.compile(                                    # Regex (#19)
        r"^(\S+) is (up|down|administratively down),\s+line protocol is (up|down)",
        re.MULTILINE
    )
    matches = pattern.findall(raw)

    # List comprehension to build structured list
    interfaces = [                                           # List Comprehension (#16)
        {"interface": m[0], "status": m[1], "protocol": m[2]}
        for m in matches
    ]

    print(f"    [NM] Found {len(interfaces)} interfaces on {device['name']}")
    return interfaces


# ── 4. Configure Loopback (#32)
def netmiko_configure_loopback(device: dict) -> str:
    """
    Configure a loopback interface.
    Covers: Netmiko Loopback Config (#32), Strings (#1), Variables (#5)
    """
    loopback_num = 0                                         # Numbers (#3)
    ip           = device["loopback_ip"]                     # Variables (#5)
    mask         = device["loopback_mask"]

    commands: List[str] = [                                  # Lists (#8)
        f"interface Loopback{loopback_num}",
        f"ip address {ip} {mask}",
        "no shutdown",
        f"description LOOPBACK_{device['name']}",
    ]

    print(f"    [NM] Configuring Loopback on {device['name']}: {ip}")
    return netmiko_send_multiline(device, commands)


# ── 5. BGP Configuration (#32)
def netmiko_configure_bgp(device: dict) -> str:
    """
    Configure BGP on the device.
    Covers: Netmiko BGP Config (#32), Variables (#5), Strings (#1)
    """
    my_as       = device["bgp_as"]                           # Variables (#5)
    neighbor_ip = device["bgp_neighbor"]
    neighbor_as = device["bgp_neighbor_as"]
    router_id   = device["loopback_ip"]

    commands: List[str] = [                                  # Lists (#8)
        f"router bgp {my_as}",
        f"bgp router-id {router_id}",
        f"neighbor {neighbor_ip} remote-as {neighbor_as}",
        "address-family ipv4",
        f"network {device['ip_address']} mask {device['subnet_mask']}",
        f"network {device['loopback_ip']} mask 255.255.255.255",
        "exit-address-family",
    ]

    print(f"    [NM] Configuring BGP AS{my_as} on {device['name']}")
    return netmiko_send_multiline(device, commands)


# ── 6. Apply ACL (#32)
def netmiko_apply_acl(device: dict, acl_config: dict) -> str:
    """
    Create and apply an extended ACL.
    Covers: Netmiko ACL (#32), Dictionary (#7), For-loops (#2)
    """
    acl_name = acl_config["name"]                            # Dictionary (#7)
    commands = [f"ip access-list extended {acl_name}"]       # Lists (#8)

    for rule in acl_config["rules"]:                         # For-loops (#2)
        seq  = rule["sequence"]                              # Numbers (#3)
        act  = rule["action"]
        proto= rule["protocol"]
        src  = rule["source"]
        dst  = rule["destination"]

        # Build ACL line conditionally
        if "dest_port" in rule:                              # Conditional (#12)
            line = f"{seq} {act} {proto} {src} {dst} eq {rule['dest_port']}"
        else:
            line = f"{seq} {act} {proto} {src} {dst}"

        commands.append(line)

    # Apply ACL inbound on the interface
    commands += [
        f"interface {device['interface']}",
        f"ip access-group {acl_name} in",
    ]

    print(f"    [NM] Applying ACL '{acl_name}' on {device['name']}")
    return netmiko_send_multiline(device, commands)


# ── 7. DHCP Pool Configuration (#30)
def netmiko_configure_dhcp(device: dict, dhcp_cfg: dict) -> str:
    """
    Configure a DHCP pool.
    Covers: DHCP Pool (#30), Netmiko Multiline (#37),
            Dictionary (#7), Strings (#1)
    """
    pool    = dhcp_cfg["pool_name"]                          # Variables (#5)
    network = dhcp_cfg["network"]
    mask    = dhcp_cfg["mask"]
    gw      = dhcp_cfg["default_router"]
    dns     = dhcp_cfg["dns_server"]
    lease   = dhcp_cfg["lease_days"]                         # Numbers (#3)

    commands: List[str] = [                                  # Lists (#8)
        f"ip dhcp pool {pool}",
        f"network {network} {mask}",
        f"default-router {gw}",
        f"dns-server {dns}",
        f"lease {lease}",
        "exit",
        f"ip dhcp excluded-address {gw}",
    ]

    print(f"    [NM] Configuring DHCP pool '{pool}' on {device['name']}")
    return netmiko_send_multiline(device, commands)


# ── 8. Loop over multiple devices (#32)
def netmiko_loop_devices(devices: List[dict],
                         command_fn,
                         **kwargs) -> Dict[str, str]:
    """
    Loop over multiple devices and apply a command function.
    Covers: Looping Devices (#32), For-loops (#2),
            Functions (#11), Dictionary (#7)
    """
    results: Dict[str, str] = {}                             # Dictionary (#7)

    for device in devices:                                   # For-loops (#2)
        name = device["name"]
        print(f"\n  [LOOP] Processing {name}...")
        try:
            output = command_fn(device, **kwargs)            # Functions (#11)
            results[name] = output
        except Exception as e:                               # Exception Handling (#13)
            results[name] = f"ERROR: {e}"
            print(f"  [LOOP] ✗ {name}: {e}")

    return results


# ── 9. BGP Verification / Show commands output
def netmiko_show_bgp_summary(device: dict) -> str:
    """Get BGP summary from a device."""
    commands = ["show bgp summary", "show ip bgp"]           # Lists (#8)
    results  = netmiko_send_commands(device, commands)
    combined = "\n".join(                                    # Strings (#1)
        f"\n=== {k} ===\n{v}" for k, v in results.items()
    )
    return combined
