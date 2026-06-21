#!/usr/bin/env python3
"""
Converts OWASP Dependency-Track findings into SonarQube Generic Issue JSON format.

Usage:
    python dtrack-to-sonarqube.py

Requires env vars: DTRACK_URL, DTRACK_API_KEY
Optional env vars: PROJECT_NAME (default: wallet-tracker-api),
                    PROJECT_VERSION (default: 0.1.0)
"""

import json
import os
import sys
import time
import urllib.error
import urllib.request
from urllib.parse import quote

SEVERITY_MAP = {
    "CRITICAL": "BLOCKER",
    "HIGH": "CRITICAL",
    "MEDIUM": "MAJOR",
    "LOW": "MINOR",
    "INFO": "INFO",
    "UNKNOWN": "INFO",
    "NONE": "INFO",
}


def _api(base_url, api_key, path, method="GET", retries=3):
    url = f"{base_url.rstrip('/')}{path}"
    headers = {"X-Api-Key": api_key, "Accept": "application/json"}

    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=headers, method=method)
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            if attempt == retries - 1:
                print(f"  HTTP {e.code} on {path}", file=sys.stderr)
                return None
            time.sleep(2 ** attempt)
        except urllib.error.URLError as e:
            if attempt == retries - 1:
                print(f"  Connection error on {path}: {e.reason}", file=sys.stderr)
                return None
            time.sleep(2 ** attempt)
    return None


def get_project_uuid(base_url, api_key, name, version):
    data = _api(base_url, api_key, f"/api/v1/project/lookup?name={quote(name)}&version={quote(version)}")
    return (data or {}).get("uuid")


def get_findings(base_url, api_key, project_uuid, max_retries=12, delay=10):
    for attempt in range(max_retries):
        data = _api(base_url, api_key, f"/api/v1/finding/project/{project_uuid}")
        if data is not None and len(data) > 0:
            return data
        if data is not None and attempt >= 6:
            return data
        print(f"  Waiting for DT to finish processing... ({attempt + 1}/{max_retries})", file=sys.stderr)
        time.sleep(delay)
    return _api(base_url, api_key, f"/api/v1/finding/project/{project_uuid}") or []


def convert(manifest_path, findings):
    rules = {}
    issues = []
    dedup = set()

    for f in findings:
        vuln = f.get("vulnerability") or {}
        comp = f.get("component") or {}

        vuln_id = vuln.get("vulnId") or "UNKNOWN"
        severity = vuln.get("severity") or "UNKNOWN"
        desc = (vuln.get("description") or "")[:400]
        c_name = comp.get("name") or "unknown"
        c_ver = comp.get("version") or "unknown"

        key = (vuln_id, c_name, c_ver)
        if key in dedup:
            continue
        dedup.add(key)

        if vuln_id not in rules:
            rules[vuln_id] = {
                "id": vuln_id,
                "name": vuln_id,
                "description": desc,
                "cleanCodeAttribute": "CONVENTIONAL",
                "impact": {
                    "softwareQuality": "SECURITY",
                    "severity": severity.capitalize(),
                },
            }

        issues.append({
            "ruleId": vuln_id,
            "effortMinutes": 0,
            "primaryLocation": {
                "message": f"{c_name}@{c_ver} - {vuln_id}: {desc}",
                "filePath": manifest_path,
            },
            "type": "VULNERABILITY",
            "severity": SEVERITY_MAP.get(severity.upper(), "INFO"),
        })

    return {"rules": list(rules.values()), "issues": issues}


def main():
    base = os.environ.get("DTRACK_URL")
    key = os.environ.get("DTRACK_API_KEY")
    proj = os.environ.get("PROJECT_NAME") or "wallet-tracker-api"
    vers = os.environ.get("PROJECT_VERSION") or "0.1.0"
    manifest = os.environ.get("MANIFEST_PATH") or "app/pyproject.toml"
    out = os.environ.get("OUTPUT_PATH") or "dependency-check-report/dtrack-findings.json"

    if not base or not key:
        print("ERROR: DTRACK_URL and DTRACK_API_KEY must be set", file=sys.stderr)
        sys.exit(0)

    print(f"Looking up project {proj}@{vers} ...", file=sys.stderr)
    puid = get_project_uuid(base, key, proj, vers)
    if not puid:
        print(f"WARNING: Project {proj}@{vers} not found in Dependency-Track", file=sys.stderr)
        sys.exit(0)

    print(f"Project UUID: {puid}", file=sys.stderr)
    findings = get_findings(base, key, puid)
    print(f"Findings returned: {len(findings)}", file=sys.stderr)

    sq_data = convert(manifest, findings)

    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    with open(out, "w") as f:
        json.dump(sq_data, f, indent=2)

    print(f"Converted {len(sq_data['issues'])} issues → {out}", file=sys.stderr)


if __name__ == "__main__":
    main()
