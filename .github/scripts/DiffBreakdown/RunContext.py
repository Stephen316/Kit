from __future__ import annotations

import os as OsLib
import string as StringLib

from RequireSha import RequireSha

# the repo characters vocabulary must stay centralized so diff reporting agrees on supported native identities
KRepoCharacters = frozenset(StringLib.ascii_letters + StringLib.digits + "_.-")


# the context operation needs a distinct decoding boundary so published evidence stays bound to the reviewed revision
def ReadContext() -> dict[str, object]:
    EnvValues = OsLib.environ
    Repository = EnvValues["GITHUB_REPOSITORY"]
    OwnerName, Separator, RepoName = Repository.partition("/")
    if not (
        Separator
        and OwnerName
        and RepoName
        and set(OwnerName + RepoName) <= KRepoCharacters
    ):
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


# the identity operation needs a consistent construction rule so published evidence stays bound to the reviewed revision
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
