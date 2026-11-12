from __future__ import annotations


# example cad inputs preserve external identities
def IsBroadSkip(RepoPath: str) -> bool:
    return RepoPath.startswith(("examples/", "re/"))
