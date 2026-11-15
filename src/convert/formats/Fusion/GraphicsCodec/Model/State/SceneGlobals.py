from dataclasses import dataclass as MakeDataClass


# scene globals needs an explicit state contract so display geometry retains its entity and scene relationships
@MakeDataClass(frozen=True, slots=True)
class SceneGlobals:
    Versions: tuple[tuple[str, int], ...]
    Environment: str
