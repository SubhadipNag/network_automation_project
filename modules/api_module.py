# ============================================================
# MODULE: api_module.py
# Covers: POST APIs (#22), JSON API (#23), Exception Handling (#13),
#         Functions (#11), Variables (#5), Strings (#1),
#         Dictionary (#7), Lists (#8), Conditional (#12)
# ============================================================

import requests                                              # POST APIs (#22)
import json                                                  # JSON API (#23)
from typing import Dict, Any, List, Optional


class GNS3API:
    """
    GNS3 REST API client.
    Covers: PyClasses (#25), POST APIs (#22), JSON API (#23)
    """

    def __init__(self, host: str, port: int,
                 username: str = "admin", password: str = "admin"):
        self.base_url = f"http://{host}:{port}/v2"           # Strings (#1), Variables (#5)
        self.auth     = (username, password)                 # Tuples (#9)
        self.session  = requests.Session()                   # POST APIs (#22)
        self.session.auth = self.auth

    # ─── GET request helper
    def _get(self, endpoint: str) -> Dict[str, Any]:
        """
        Generic GET request.
        Covers: Functions (#11), Exception Handling (#13)
        """
        url = f"{self.base_url}{endpoint}"                   # Strings (#1)
        try:
            resp = self.session.get(url, timeout=10)
            resp.raise_for_status()
            return resp.json()                               # JSON API (#23)
        except requests.HTTPError as e:                      # Exception Handling (#13)
            return {"error": f"HTTP {resp.status_code}: {e}"}
        except requests.ConnectionError:
            return {"error": f"Cannot connect to GNS3 at {url}"}
        except Exception as e:
            return {"error": str(e)}

    # ─── POST request helper (#22)
    def _post(self, endpoint: str, data: dict) -> Dict[str, Any]:
        """
        Generic POST request.
        Covers: POST APIs (#22), JSON API (#23), Exception Handling (#13)
        """
        url = f"{self.base_url}{endpoint}"
        try:
            resp = self.session.post(                        # POST APIs (#22)
                url,
                json=data,                                   # JSON API (#23)
                timeout=10,
            )
            resp.raise_for_status()
            return resp.json()
        except requests.HTTPError as e:
            return {"error": f"POST HTTP {resp.status_code}: {e}"}
        except Exception as e:
            return {"error": str(e)}

    # ─── GET all projects
    def get_projects(self) -> List[Dict[str, Any]]:
        """Return list of GNS3 projects."""
        result = self._get("/projects")
        if isinstance(result, list):                         # Conditional (#12)
            return result
        return []

    # ─── GET project nodes
    def get_nodes(self, project_id: str) -> List[Dict[str, Any]]:
        """Return all nodes in a project."""
        result = self._get(f"/projects/{project_id}/nodes")
        if isinstance(result, list):
            return result
        return []

    # ─── GET server version
    def get_version(self) -> str:
        """Return GNS3 server version string."""
        result = self._get("/version")
        return result.get("version", "unknown")              # Dictionary (#7)

    # ─── POST: Start all nodes in project
    def start_all_nodes(self, project_id: str) -> Dict[str, Any]:
        """
        Send POST to start all nodes in a project.
        Covers: POST APIs (#22)
        """
        return self._post(f"/projects/{project_id}/nodes/start", {})

    # ─── POST: Stop all nodes in project
    def stop_all_nodes(self, project_id: str) -> Dict[str, Any]:
        """Send POST to stop all nodes."""
        return self._post(f"/projects/{project_id}/nodes/stop", {})

    # ─── GET: Summarize topology
    def topology_summary(self) -> str:
        """
        Return topology summary as formatted text.
        Covers: Strings (#1), For-loops (#2), JSON (#23)
        """
        lines = ["", "  GNS3 TOPOLOGY SUMMARY", "  " + "=" * 40]

        version  = self.get_version()
        lines.append(f"  Server version : {version}")

        projects = self.get_projects()
        lines.append(f"  Total projects : {len(projects)}")

        for project in projects:                             # For-loops (#2)
            pid   = project.get("project_id", "?")
            pname = project.get("name", "unnamed")
            lines.append(f"\n  Project: {pname} (id={pid})")

            nodes = self.get_nodes(pid)
            for node in nodes:                               # For-loops (#2)
                nname  = node.get("name", "?")
                ntype  = node.get("node_type", "?")
                status = node.get("status", "?")
                lines.append(f"    └─ {nname:10s} [{ntype}] status={status}")

        return "\n".join(lines)


def fetch_gns3_topology(host: str, port: int) -> str:
    """
    Functional wrapper: fetch and print topology.
    Covers: Functions (#11), POST APIs (#22), JSON (#23)
    """
    api = GNS3API(host, port)
    print("    [API] Querying GNS3 REST API...")
    summary = api.topology_summary()
    print("    [API] ✓ Topology fetched")
    return summary
