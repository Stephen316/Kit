from __future__ import annotations

# the replay names vocabulary must stay centralized so payload policy agrees on supported native identities
KReplayNames = frozenset(
    {"ReplayAssembly", "ReplayConfig", "ReplayFixed", "ReplayResolved"}
)

# kind pattern must remain consistent across callers so captured document data cannot become production writer input
KKindPattern = r"[a-z]+(?::[A-Za-z0-9]+)?"

# standard path needs a stable location so payload policy resolves inputs independently of the caller working directory
KStandardPath = (
    ".agents/skills/standard-pr-practice/references/Standards/Portable/NoDonorBlocks.md"
)
