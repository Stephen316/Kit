from os import environ as KEnvironment
from pathlib import Path as FilePath


# research compatibility must fail clearly when the pinned checkout was not provisioned
def ResearchRoot() -> FilePath:
    RootValue = KEnvironment.get("KIT_RESEARCH_CHECKOUT")
    if RootValue is None:
        raise ValueError("KIT_RESEARCH_CHECKOUT must identify the pinned PR94 checkout")
    RootPath = FilePath(__file__).resolve().parents[2] / "ResearchCheckout"
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
            "KIT_RESEARCH_CHECKOUT must contain the pinned repository and SDK"
        )
    return RootPath
