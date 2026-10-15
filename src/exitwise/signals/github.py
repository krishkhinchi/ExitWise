"""GitHub repository health signal with rate limit tolerance."""

import datetime
import os
import re
from dataclasses import dataclass
import httpx

from exitwise.models import Evidence


@dataclass
class GitHubHealth:
    """Repository maintenance status from GitHub."""

    is_archived: bool = False
    last_push_date: str | None = None
    open_issues_count: int | None = None
    stars_count: int | None = None
    repo_url: str | None = None
    evidence_id: str = ""


def extract_github_repo(project_urls: dict[str, str]) -> tuple[str, str] | None:
    """Extract (owner, repo) from project URLs."""
    gh_pattern = re.compile(r"github\.com/([a-zA-Z0-9_\-\.]+)/([a-zA-Z0-9_\-\.]+)")
    for url in project_urls.values():
        if isinstance(url, str):
            match = gh_pattern.search(url)
            if match:
                owner, repo = match.group(1), match.group(2).rstrip("/")
                if repo.endswith(".git"):
                    repo = repo[:-4]
                return owner, repo
    return None


def fetch_github_health(
    package_name: str,
    project_urls: dict[str, str],
    evidence_counter: int = 1,
    offline_mode: bool = False,
) -> tuple[GitHubHealth, Evidence]:
    """Query GitHub API for repository archived status and activity."""
    ev_id = f"EV-GH-{evidence_counter:04d}"
    gh_info = extract_github_repo(project_urls)

    if offline_mode or not gh_info:
        ev = Evidence(
            id=ev_id,
            source="github_api",
            kind="repo_health",
            observed_value={"package": package_name, "status": "no_github_url_or_offline"},
            timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        )
        return GitHubHealth(evidence_id=ev_id), ev

    owner, repo = gh_info
    repo_url = f"https://github.com/{owner}/{repo}"
    token = os.getenv("GITHUB_TOKEN")
    headers = {"Accept": "application/vnd.github.v3+json", "User-Agent": "Exitwise/0.1.0"}
    if token:
        headers["Authorization"] = f"token {token}"

    health = GitHubHealth(repo_url=repo_url, evidence_id=ev_id)
    try:
        resp = httpx.get(f"https://api.github.com/repos/{owner}/{repo}", headers=headers, timeout=6.0)
        if resp.status_code == 200:
            data = resp.json()
            health.is_archived = data.get("archived", False)
            health.last_push_date = (data.get("pushed_at") or "")[:10]
            health.open_issues_count = data.get("open_issues_count")
            health.stars_count = data.get("stargazers_count")
    except Exception:
        # Degrade gracefully on rate limits or network issues
        pass

    ev = Evidence(
        id=ev_id,
        source="github_api",
        kind="repo_health",
        observed_value={
            "package": package_name,
            "repo_url": repo_url,
            "is_archived": health.is_archived,
            "last_push": health.last_push_date,
            "open_issues": health.open_issues_count,
        },
        timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    )
    return health, ev
