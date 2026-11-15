from os import environ as KEnvironment
from pathlib import Path as FilePath
from subprocess import run as RunProcess


# research compatibility must fail clearly when the pinned checkout was not provisioned
def ResearchRoot() -> FilePath:
    RootValue = KEnvironment.get("KIT_RESEARCH_CHECKOUT")
    if RootValue is None:
        raise ValueError("KIT_RESEARCH_CHECKOUT must identify the candidate checkout")
    CliPath = FilePath(__file__).resolve().parents[2]
    RootPath = CliPath / "ResearchCheckout"
    if (
        not FilePath(RootValue).is_absolute()
        or FilePath(RootValue) != RootPath
        or RootPath.resolve() != RootPath
    ):
        raise ValueError(
            "KIT_RESEARCH_CHECKOUT must identify this repository ResearchCheckout"
        )
    if not (RootPath / ".git").exists() or not (RootPath / "src/convert").is_dir():
        raise ValueError(
            "KIT_RESEARCH_CHECKOUT must contain the candidate repository and SDK"
        )
    Revision = KEnvironment.get("GITHUB_SHA")
    if Revision != ReadHead(CliPath) or Revision != ReadHead(RootPath):
        raise ValueError(
            "CLI and research checkouts must both match the GitHub candidate"
        )
    return RootPath


# matching the two local commits against the workflow provenance prevents stale compatibility evidence
def ReadHead(RootPath: FilePath) -> str:
    Result = RunProcess(
        ("git", "-C", str(RootPath), "rev-parse", "--show-prefix", "--verify", "HEAD"),
        capture_output=True,
        text=True,
        check=True,
        timeout=30,
    )
    Prefix, Revision = Result.stdout.splitlines()
    if Prefix:
        raise ValueError("CLI compatibility requires a separate research Git root")
    return Revision
