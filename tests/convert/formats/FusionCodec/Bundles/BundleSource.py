from pathlib import Path


def BundleSource() -> Path:
    for Parent in Path(__file__).resolve().parents:
        Candidate = Parent / "re/Fusion/examples/.f3z/example1.f3z"
        if Candidate.is_file():
            return Candidate
    raise FileNotFoundError("Fusion bundle integration fixture is unavailable")
