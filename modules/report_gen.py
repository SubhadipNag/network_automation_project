# ============================================================
# MODULE: report_gen.py
# Covers: Report Generation (#32), Functions (#11),
#         Strings (#1), Lists (#8), Dictionary (#7),
#         For-loops (#2), Numbers (#3), Operators (#4),
#         Variables (#5), Conditional (#12)
# ============================================================

import os
from datetime import datetime
from typing import List, Dict, Any


REPORT_DIR = os.path.join(os.path.dirname(__file__), "..", "reports")


def generate_report(
    devices:            List[dict],
    interface_results:  Dict[str, Any],
    bgp_results:        Dict[str, Any],
    inventory:          List[dict],
    topology_summary:   str,
    configs:            Dict[str, str],
) -> str:
    """
    Generate a full automation run report.
    Covers: Report Generation (#32), Strings (#1),
            For-loops (#2), Conditional (#12), Numbers (#3)
    """
    now         = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Strings (#1)
    total_devs  = len(devices)                                   # Numbers (#3)
    report_lines: List[str] = []                                 # Lists (#8)

    # ── Header
    report_lines += [
        "=" * 70,
        "  NETWORK AUTOMATION REPORT",
        f"  Generated : {now}",
        f"  Devices   : {total_devs}",
        "=" * 70,
    ]

    # ── Device Summary
    report_lines.append("\n[1] DEVICE INVENTORY\n" + "-" * 50)
    for dev in inventory:                                        # For-loops (#2)
        name   = dev.get("name", "?")                           # Variables (#5)
        ip     = dev.get("ip_address", "?")
        status = dev.get("status", "unknown")
        report_lines.append(                                     # Strings (#1)
            f"  {name:5s} | IP: {ip:16s} | Status: {status}"
        )

    # ── Interface Status
    report_lines.append("\n[2] INTERFACE STATUS\n" + "-" * 50)
    for dev_name, ifaces in interface_results.items():           # For-loops (#2)
        report_lines.append(f"\n  {dev_name}:")
        if isinstance(ifaces, list):                             # Conditional (#12)
            for iface in ifaces:                                 # For-loops (#2)
                if "error" in iface:
                    report_lines.append(f"    ERROR: {iface['error']}")
                else:
                    intf  = iface.get("interface", "?")
                    state = iface.get("status", "?")
                    proto = iface.get("protocol", "?")
                    up_icon = "✓" if state == "up" else "✗"     # Conditional (#12)
                    report_lines.append(                         # Strings (#1)
                        f"    {up_icon} {intf:30s} {state:10s} (proto={proto})"
                    )
        else:
            report_lines.append(f"    {ifaces}")

    # ── BGP Summary
    report_lines.append("\n[3] BGP SUMMARY\n" + "-" * 50)
    for dev_name, bgp_out in bgp_results.items():                # For-loops (#2)
        report_lines.append(f"\n  {dev_name}:")
        if bgp_out:
            # Truncate to first 20 lines
            lines = str(bgp_out).split("\n")[:20]                # Lists (#8), Numbers (#3)
            for line in lines:                                   # For-loops (#2)
                report_lines.append(f"    {line}")
        else:
            report_lines.append("    No BGP data available.")

    # ── GNS3 Topology
    report_lines.append("\n[4] GNS3 TOPOLOGY\n" + "-" * 50)
    if topology_summary:                                         # Conditional (#12)
        report_lines.append(topology_summary)
    else:
        report_lines.append("  GNS3 API not reachable.")

    # ── Generated Configs
    report_lines.append("\n[5] CONFIG GENERATION SUMMARY\n" + "-" * 50)
    for name, cfg in configs.items():                            # For-loops (#2)
        line_count = len(cfg.split("\n"))                        # Numbers (#3)
        report_lines.append(
            f"  {name}: {line_count} lines generated"
        )

    # ── Footer
    total_lines = len(report_lines)                              # Numbers (#3)
    report_lines += [
        "\n" + "=" * 70,
        f"  END OF REPORT — {total_lines} lines",
        "=" * 70,
    ]

    return "\n".join(report_lines)                               # Strings (#1)


def save_report(report_text: str) -> str:
    """Save report to file and return path."""
    os.makedirs(REPORT_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path      = os.path.join(REPORT_DIR, f"report_{timestamp}.txt")

    with open(path, "w") as f:
        f.write(report_text)

    print(f"  [RPT] Report saved: {path}")
    return path


def print_report(report_text: str) -> None:
    """Print report with a visible header banner."""
    banner = "\n" + "█" * 70 + "\n"
    print(banner)
    print(report_text)
    print(banner)
