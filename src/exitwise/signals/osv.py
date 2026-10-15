"""Live OSV.dev vulnerability query client."""

import datetime
from dataclasses import dataclass, field
from typing import Any
import httpx

from exitwise.models import Evidence


@dataclass
class VulnerabilityRecord:
    """A known vulnerability surfaced from OSV.dev."""

    vuln_id: str
    summary: str
    details: str
    severity: str  # HIGH, MEDIUM, LOW, CRITICAL
    aliases: list[str] = field(default_factory=list)


def query_osv_vulnerabilities(
    package_name: str,
    version: str | None,
    evidence_counter: int = 1,
    offline_mode: bool = False,
) -> tuple[list[VulnerabilityRecord], Evidence]:
    """Query OSV.dev API for vulnerabilities affecting this package and pinned version."""
    vulns: list[VulnerabilityRecord] = []
    ev_id = f"EV-OSV-{evidence_counter:04d}"

    if offline_mode or not version:
        ev = Evidence(
            id=ev_id,
            source="osv_api",
            kind="vulnerabilities",
            observed_value={"package": package_name, "version": version, "vulnerabilities": []},
            timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        )
        return vulns, ev

    try:
        payload = {
            "version": version,
            "package": {"name": package_name, "ecosystem": "PyPI"},
        }
        resp = httpx.post(
            "https://api.osv.dev/v1/query",
            json=payload,
            timeout=8.0,
        )
        if resp.status_code == 200:
            data = resp.json()
            for item in data.get("vulns", []):
                v_id = item.get("id", "UNKNOWN")
                summary = item.get("summary") or item.get("details", "")[:120]
                aliases = item.get("aliases", [])
                # Determine severity
                severity = "MEDIUM"
                for sev in item.get("severity", []):
                    if sev.get("type") == "CVSS_V3":
                        score = sev.get("score", "")
                        if "CVSS:3" in score:
                            severity = "HIGH"
                vulns.append(
                    VulnerabilityRecord(
                        vuln_id=v_id,
                        summary=summary,
                        details=item.get("details", "")[:300],
                        severity=severity,
                        aliases=aliases,
                    )
                )
    except Exception:
        # Graceful degradation on network timeout or OSV error
        pass

    ev = Evidence(
        id=ev_id,
        source="osv_api",
        kind="vulnerabilities",
        observed_value={
            "package": package_name,
            "version": version,
            "count": len(vulns),
            "vuln_ids": [v.vuln_id for v in vulns],
        },
        timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    )
    return vulns, ev
