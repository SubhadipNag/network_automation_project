#!/usr/bin/env python3
# ============================================================
# main.py — GNS3 Network Automation Suite
# Orchestrates all modules covering all 38 learning topics.
#
# GNS3 Lab:
#   R2 → 192.168.80.129:5003  (Telnet)
#   R3 → 192.168.80.129:5002  (Telnet)
#   Cloud1 → NAT bridge
#
# Run:  python main.py
# ============================================================

# ── Standard library
import os
import sys
import json
import yaml                                                  # YAML (#29)
import time
import threading                                             # Multithreading (#18)
from typing import List, Dict, Any

# ── Project modules (#26 - PyModule Package)
from modules.device_model      import DeviceModel, GNS3ServerModel
from modules.inventory_manager import (
    build_inventory_from_yaml, save_inventory,
    load_inventory, update_device_status,
    get_device_names, get_unique_platforms,
    print_inventory_table,
)
from modules.telnet_module     import (
    telnet_configure_basic, telnet_run_commands,
    telnet_configure_ssh,
)
from modules.ssh_paramiko      import paramiko_run_show_commands
from modules.netmiko_module    import (
    netmiko_interface_status, netmiko_configure_loopback,
    netmiko_configure_bgp, netmiko_apply_acl,
    netmiko_configure_dhcp, netmiko_loop_devices,
    netmiko_send_commands, netmiko_show_bgp_summary,
)
from modules.napalm_module     import napalm_get_all_devices, format_napalm_facts
from modules.api_module        import fetch_gns3_topology
from modules.sniff_module      import (
    start_packet_sniff, wait_for_sniff,
    run_multithreaded_commands,
)
from modules.log_parser        import (
    write_log, parse_log_file, get_log_summary,
    extract_ip_addresses, parse_cisco_log_string,
)
from modules.config_gen        import (
    generate_all_configs, save_config_to_file,
)
from modules.report_gen        import (
    generate_report, save_report, print_report,
)

# ─────────────────────────────────────────────────────────────
# STEP 0: LOAD YAML CONFIG (#29 - Python YAML)
# ─────────────────────────────────────────────────────────────

def load_yaml_config(path: str) -> dict:
    """Load YAML config file. Covers: YAML (#29), Functions (#11)"""
    with open(path, "r") as f:
        data = yaml.safe_load(f)                             # YAML (#29)
    print(f"[YAML] Loaded config: {path}")
    return data


# ─────────────────────────────────────────────────────────────
# STEP 1: VALIDATE DEVICES WITH PYDANTIC (#38)
# ─────────────────────────────────────────────────────────────

def validate_devices(yaml_devices: list) -> List[DeviceModel]:
    """
    Validate all devices with Pydantic models.
    Covers: Pydantic (#38), Lists (#8), For-loops (#2),
            Exception Handling (#13)
    """
    validated: List[DeviceModel] = []
    for raw in yaml_devices:                                 # For-loops (#2)
        try:
            model = DeviceModel(**raw)                       # Pydantic (#38)
            validated.append(model)
            print(f"  [PYD] ✓ {model.summary()}")
        except Exception as e:                               # Exception Handling (#13)
            print(f"  [PYD] ✗ Validation failed: {e}")
            sys.exit(1)
    return validated


# ─────────────────────────────────────────────────────────────
# STEP 2: TELNET INITIAL CONFIGURATION
# ─────────────────────────────────────────────────────────────

def phase_telnet_setup(devices: List[DeviceModel]) -> None:
    """
    Phase 1: Configure routers via Telnet.
    Covers: Telnet (#20/#21), For-loops (#2), Exception Handling (#13)
    """
    print("\n" + "─" * 60)
    print("  PHASE 1 — TELNET INITIAL CONFIG")
    print("─" * 60)

    for device in devices:                                   # For-loops (#2)
        print(f"\n  [{device.name}] Configuring via Telnet...")
        write_log(f"Starting Telnet config for {device.name}")

        host, port = device.to_telnet_tuple()                # Tuples (#9)

        try:
            # Basic interface + hostname config
            telnet_configure_basic(
                host        = host,
                port        = port,
                username    = device.username,
                password    = device.password,
                enable_pass = device.enable_password,
                device_name = device.name,
                interface   = device.interface,
                ip_address  = device.ip_address,
                subnet_mask = device.subnet_mask,
            )

            # Enable SSH on the device
            telnet_configure_ssh(host, port,
                                 device.username,
                                 device.password,
                                 device.enable_password)

            update_device_status(device.name, "telnet_configured")
            write_log(f"Telnet config complete for {device.name}", "INFO")

        except Exception as e:                               # Exception Handling (#13)
            write_log(f"Telnet error on {device.name}: {e}", "ERROR")
            print(f"  ✗ Telnet error on {device.name}: {e}")


# ─────────────────────────────────────────────────────────────
# STEP 3: PARAMIKO SSH SHOW COMMANDS
# ─────────────────────────────────────────────────────────────

def phase_paramiko(devices: List[DeviceModel]) -> None:
    """
    Phase 2: Run show commands via Paramiko SSH.
    Covers: SSH Paramiko (#24), For-loops (#2), Strings (#1)
    """
    print("\n" + "─" * 60)
    print("  PHASE 2 — PARAMIKO SSH SHOW COMMANDS")
    print("─" * 60)

    show_cmds: List[str] = [                                 # Lists (#8)
        "show version",
        "show ip interface brief",
        "show running-config | section router bgp",
    ]

    for device in devices:                                   # For-loops (#2)
        dev_dict = device.model_dump()                       # Pydantic (#38)
        dev_dict["ssh_port"] = device.ssh_port
        print(f"\n  [{device.name}] Paramiko SSH...")
        try:
            out = paramiko_run_show_commands(dev_dict, show_cmds)
            write_log(f"Paramiko output ({device.name}):\n{out[:200]}", "INFO")
            print(f"  ✓ Got {len(out)} chars from {device.name}")
        except Exception as e:                               # Exception Handling (#13)
            print(f"  ✗ Paramiko error on {device.name}: {e}")
            write_log(f"Paramiko error {device.name}: {e}", "ERROR")


# ─────────────────────────────────────────────────────────────
# STEP 4: NETMIKO — FULL CONFIG PUSH
# ─────────────────────────────────────────────────────────────

def phase_netmiko(devices: List[DeviceModel],
                  acl_cfg: dict,
                  dhcp_cfg: dict) -> tuple:
    """
    Phase 3: Full Netmiko automation.
    Covers: Netmiko (#28/#32/#37), Multithreading (#18),
            Tuples (#9), For-loops (#2)
    """
    print("\n" + "─" * 60)
    print("  PHASE 3 — NETMIKO FULL CONFIG PUSH")
    print("─" * 60)

    dev_dicts = [d.model_dump() for d in devices]           # List Comprehension (#16)

    # ── 3a. Configure loopbacks (multi-threaded) (#18)
    print("\n  [3a] Loopback config (multi-threaded)...")
    loopback_results = run_multithreaded_commands(           # Multithreading (#18)
        dev_dicts, netmiko_configure_loopback
    )

    # ── 3b. Configure BGP
    print("\n  [3b] BGP configuration...")
    bgp_results: Dict[str, str] = {}
    for d in dev_dicts:                                      # For-loops (#2)
        try:
            bgp_results[d["name"]] = netmiko_configure_bgp(d)
        except Exception as e:
            bgp_results[d["name"]] = f"ERROR: {e}"

    # ── 3c. Apply ACL
    print("\n  [3c] Applying ACL...")
    acl_results = netmiko_loop_devices(                      # Looping Devices (#32)
        dev_dicts, netmiko_apply_acl, acl_config=acl_cfg
    )

    # ── 3d. DHCP on R2 only
    print("\n  [3d] DHCP pool on R2...")
    r2_dict = next((d for d in dev_dicts if d["name"] == "R2"), None)
    if r2_dict:                                              # Conditional (#12)
        try:
            netmiko_configure_dhcp(r2_dict, dhcp_cfg)
        except Exception as e:
            print(f"  ✗ DHCP error: {e}")

    # ── 3e. Interface status
    print("\n  [3e] Interface status check...")
    iface_results: Dict[str, Any] = {}
    for d in dev_dicts:                                      # For-loops (#2)
        iface_results[d["name"]] = netmiko_interface_status(d)

    # ── 3f. BGP show summary
    print("\n  [3f] BGP verification...")
    bgp_show: Dict[str, str] = {}
    for d in dev_dicts:                                      # For-loops (#2)
        try:
            bgp_show[d["name"]] = netmiko_show_bgp_summary(d)
        except Exception as e:
            bgp_show[d["name"]] = f"ERROR: {e}"

    return iface_results, bgp_show                          # Tuples (#9)


# ─────────────────────────────────────────────────────────────
# STEP 5: NAPALM DATA COLLECTION (#27)
# ─────────────────────────────────────────────────────────────

def phase_napalm(devices: List[DeviceModel]) -> None:
    """NAPALM facts collection."""
    print("\n" + "─" * 60)
    print("  PHASE 4 — NAPALM DEVICE COLLECTION")
    print("─" * 60)

    dev_dicts = [d.model_dump() for d in devices]
    all_facts = napalm_get_all_devices(dev_dicts)
    formatted = format_napalm_facts(all_facts)
    print(formatted)
    write_log("NAPALM collection complete", "INFO")


# ─────────────────────────────────────────────────────────────
# STEP 6: GNS3 API (#22/#23)
# ─────────────────────────────────────────────────────────────

def phase_gns3_api(gns3_server: dict) -> str:
    """Call GNS3 REST API to get topology info."""
    print("\n" + "─" * 60)
    print("  PHASE 5 — GNS3 REST API (POST/JSON)")
    print("─" * 60)

    host = gns3_server["host"]
    port = gns3_server["port"]

    topology = fetch_gns3_topology(host, port)
    print(topology)
    return topology


# ─────────────────────────────────────────────────────────────
# STEP 7: CONFIG GENERATION (#34)
# ─────────────────────────────────────────────────────────────

def phase_config_gen(devices: List[DeviceModel],
                     acl_cfg: dict, dhcp_cfg: dict) -> Dict[str, str]:
    """Generate and save all device configs."""
    print("\n" + "─" * 60)
    print("  PHASE 6 — GENERATE CONFIGURATION FILES")
    print("─" * 60)

    dev_dicts = [d.model_dump() for d in devices]
    configs   = generate_all_configs(dev_dicts, acl_cfg, dhcp_cfg)

    for name, cfg_text in configs.items():                   # For-loops (#2)
        report_dir = os.path.join(
            os.path.dirname(__file__), "reports"
        )
        save_config_to_file(name, cfg_text, report_dir)

    return configs


# ─────────────────────────────────────────────────────────────
# STEP 8: LOG PARSING (#31/#19)
# ─────────────────────────────────────────────────────────────

def phase_log_parsing() -> None:
    """Parse log file and show summary."""
    print("\n" + "─" * 60)
    print("  PHASE 7 — LOG PARSING & REGEX")
    print("─" * 60)

    events  = parse_log_file()
    summary = get_log_summary(events)                        # Dictionary (#7)

    print(f"  Total log events : {len(events)}")
    print("  Event summary:")
    for etype, count in summary.items():                     # For-loops (#2)
        print(f"    {etype:30s}: {count}")

    # Also demo IP extraction from a sample show output
    sample = (
        "Neighbor 10.0.0.2 is up. BGP state = Established. "
        "Router-ID 3.3.3.3. Interface 10.0.0.1 is active."
    )
    ips = extract_ip_addresses(sample)
    print(f"\n  IPs extracted from sample: {ips}")


# ─────────────────────────────────────────────────────────────
# STEP 9: MULTITHREADED PACKET SNIFF (#18/#28)
# ─────────────────────────────────────────────────────────────

def phase_packet_sniff() -> None:
    """Start and wait for packet sniff thread."""
    print("\n" + "─" * 60)
    print("  PHASE 8 — MULTITHREADED PACKET SNIFF")
    print("─" * 60)

    t       = start_packet_sniff(interface="eth0", count=15, timeout=8)
    packets = wait_for_sniff(t)

    # Show summary
    protos: Dict[str, int] = {}                              # Dictionary (#7)
    for pkt in packets:                                      # For-loops (#2)
        ptype = pkt.get("type", "unknown")
        protos[ptype] = protos.get(ptype, 0) + 1            # Numbers (#3)

    print("  Protocol breakdown:")
    for proto, count in protos.items():                      # For-loops (#2)
        print(f"    {proto:10s}: {count} packets")


# ─────────────────────────────────────────────────────────────
# STEP 10: REPORT GENERATION (#32)
# ─────────────────────────────────────────────────────────────

def phase_report(devices: List[DeviceModel],
                 iface_results: Dict[str, Any],
                 bgp_results:   Dict[str, str],
                 topology:      str,
                 configs:       Dict[str, str]) -> None:
    """Generate and save final report."""
    print("\n" + "─" * 60)
    print("  PHASE 9 — REPORT GENERATION")
    print("─" * 60)

    inventory = load_inventory()
    report    = generate_report(
        devices           = [d.model_dump() for d in devices],
        interface_results = iface_results,
        bgp_results       = bgp_results,
        inventory         = inventory,
        topology_summary  = topology,
        configs           = configs,
    )

    path = save_report(report)
    print_report(report)
    print(f"  [DONE] Report at: {path}")


# ─────────────────────────────────────────────────────────────
# ── MAIN
# ─────────────────────────────────────────────────────────────

def main() -> None:
    """
    Main orchestrator function.
    Covers: Functions (#11), Variables (#5), Conditional (#12),
            All 38 topics via the phases above.
    """
    banner = """
╔══════════════════════════════════════════════════════════╗
║     GNS3 PYTHON NETWORK AUTOMATION SUITE                 ║
║     R2 (192.168.80.129:5003)  ↔  R3 (192.168.80.129:5002) ║
╚══════════════════════════════════════════════════════════╝
    """
    print(banner)

    # ── 0. Load YAML config
    cfg_path   = os.path.join(os.path.dirname(__file__),
                              "config", "devices.yaml")
    yaml_cfg   = load_yaml_config(cfg_path)                  # YAML (#29)

    gns3_srv   = yaml_cfg["gns3_server"]                     # Dictionary (#7)
    raw_devs   = yaml_cfg["devices"]
    acl_cfg    = yaml_cfg["acl"]
    dhcp_cfg   = yaml_cfg["dhcp"]

    # ── 1. Pydantic validation
    print("\n[STEP 1] Validating device models...")
    validated_devices = validate_devices(raw_devs)           # Pydantic (#38)

    # ── 2. Build and save inventory
    print("\n[STEP 2] Building JSON inventory...")
    inventory = build_inventory_from_yaml(raw_devs)
    save_inventory(inventory)
    print_inventory_table()

    # Print unique platforms (Sets)
    platforms = get_unique_platforms()                        # Sets (#10)
    print(f"  Unique platforms in inventory: {platforms}")

    # ── 3. Telnet setup
    print("\n[STEP 3] Telnet initial configuration...")
    phase_telnet_setup(validated_devices)

    # ── 4. Paramiko SSH
    print("\n[STEP 4] Paramiko show commands...")
    phase_paramiko(validated_devices)

    # ── 5. Netmiko full config
    print("\n[STEP 5] Netmiko configuration push...")
    iface_results, bgp_results = phase_netmiko(
        validated_devices, acl_cfg, dhcp_cfg
    )

    # ── 6. NAPALM
    print("\n[STEP 6] NAPALM facts collection...")
    phase_napalm(validated_devices)

    # ── 7. GNS3 API
    print("\n[STEP 7] GNS3 REST API query...")
    topology = phase_gns3_api(gns3_srv)

    # ── 8. Config generation
    print("\n[STEP 8] Generating config files...")
    configs = phase_config_gen(validated_devices, acl_cfg, dhcp_cfg)

    # ── 9. Log parsing
    print("\n[STEP 9] Log parsing...")
    phase_log_parsing()

    # ── 10. Packet sniff (runs briefly)
    print("\n[STEP 10] Packet sniffing...")
    phase_packet_sniff()

    # ── 11. Report
    print("\n[STEP 11] Generating final report...")
    phase_report(validated_devices, iface_results, bgp_results,
                 topology, configs)

    print("\n\n✅  ALL PHASES COMPLETE.\n")


if __name__ == "__main__":
    main()
