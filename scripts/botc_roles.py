"""Load official Blood on the Clocktower role data from botc-release roles.json."""

from __future__ import annotations

import json
import os
import subprocess
import urllib.request
from typing import Any

DEFAULT_ROLES_URL = (
    "https://raw.githubusercontent.com/ThePandemoniumInstitute/botc-release/"
    "main/resources/data/roles.json"
)

USER_AGENT = "trmnl-botc-cotd-plugin/1.0"
HTTP_TIMEOUT = 30.0

TEAM_TO_TYPE: dict[str, str] = {
    "townsfolk": "Townsfolk",
    "outsider": "Outsider",
    "minion": "Minion",
    "demon": "Demon",
    "traveller": "Traveller",
    "fabled": "Fabled",
    "loric": "Loric",
}


def role_type(role: dict[str, Any]) -> str:
    team = role.get("team") or ""
    return TEAM_TO_TYPE.get(team, team.title() if team else "Unknown")


def _curl_env() -> dict[str, str]:
    env = os.environ.copy()
    for key in (
        "HTTP_PROXY",
        "HTTPS_PROXY",
        "ALL_PROXY",
        "http_proxy",
        "https_proxy",
        "all_proxy",
    ):
        env.pop(key, None)
    env["NO_PROXY"] = "*"
    env["no_proxy"] = "*"
    return env


def fetch_roles(url: str | None = None) -> list[dict[str, Any]]:
    """Fetch roles.json from botc-release main (latest)."""
    target = url or os.environ.get("BOTC_ROLES_URL") or DEFAULT_ROLES_URL
    try:
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        req = urllib.request.Request(target, headers={"User-Agent": USER_AGENT})
        with opener.open(req, timeout=HTTP_TIMEOUT) as resp:
            data = json.load(resp)
    except Exception:
        result = subprocess.run(
            [
                "curl",
                "-sS",
                "-A",
                USER_AGENT,
                "--max-time",
                str(int(HTTP_TIMEOUT)),
                target,
            ],
            capture_output=True,
            text=True,
            check=True,
            env=_curl_env(),
        )
        data = json.loads(result.stdout)
    if not isinstance(data, list):
        raise ValueError(f"Expected roles.json array, got {type(data).__name__}")
    return data
