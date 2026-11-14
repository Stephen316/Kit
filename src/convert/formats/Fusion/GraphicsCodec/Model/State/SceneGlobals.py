from dataclasses import dataclass as MakeDataClass


@MakeDataClass(frozen=True, slots=True)
class SceneGlobals:
    Versions: tuple[tuple[str, int], ...]
    Environment: str
