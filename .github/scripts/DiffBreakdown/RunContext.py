from __future__ import annotations

import os as OsLib
import re as Regex

from RequireSha import RequireSha

KRepoPattern = r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+"


def ReadContext() -> dict[str, object]:
    EnvValues = OsLib.environ
    Repository = EnvValues["GITHUB_REPOSITORY"]
    if Regex.fullmatch(KRepoPattern, Repository) is None:
        raise ValueError("Invalid repository identity")
    return {
        "Repository": Repository,
        "EventName": EnvValues["GITHUB_EVENT_NAME"],
        "TrustedSha": RequireSha(EnvValues["GITHUB_SHA"]),
        "Pull": int(EnvValues["PULL_NUMBER"]),
        "Base": RequireSha(EnvValues["BASE_SHA"]),
        "Head": RequireSha(EnvValues["HEAD_SHA"]),
        "RunId": int(EnvValues["GITHUB_RUN_ID"]),
        "RunNumber": int(EnvValues["GITHUB_RUN_NUMBER"]),
        "Attempt": int(EnvValues["GITHUB_RUN_ATTEMPT"]),
    }


def BuildIdentity(
    Context: dict[str, object], Trusted: str, Previous: dict[str, object] | None
) -> dict[str, object]:
    return {
        "Version": 1,
        "Repository": Context["Repository"],
        "Pull": Context["Pull"],
        "Base": Context["Base"],
        "Head": Context["Head"],
        "Implementation": RequireSha(Trusted),
        "RunId": Context["RunId"],
        "RunNumber": Context["RunNumber"],
        "EventId": f"{Context['RunId']}:{Context['Attempt']}",
        "Sequence": Previous["Sequence"] + 1 if Previous else 1,
    }
