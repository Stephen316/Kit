from dataclasses import dataclass as MakeDataClass
from pathlib import Path as FilePath


# the rotary case boundary needs grouped coverage so repository automation cannot silently change its observable contract
@MakeDataClass(frozen=True, slots=True)
class RotaryCase:
    RoleName: str
    RadiusMm: float
    HeightMm: float
    TaperDegrees: float
    BodyId: str | None
    OutputDigest: str


# the rotary cases cases must remain explicit so native document reconstruction exercises the intended compatibility boundary
KRotaryCases = (
    RotaryCase(
        "circle",
        14.0,
        0.0,
        0.0,
        None,
        "1b2a7c2d57ca750030c75514ccb977c0cf8bb9dcfea7c0018de08716ef161610",
    ),
    RotaryCase(
        "extrusion",
        12.0,
        21.0,
        0.0,
        "fusion:0:1125",
        "29b666aa7afc20267e273bbd4d29f98143d3c2157af3ca2e353785724f2e4176",
    ),
    RotaryCase(
        "frustum",
        12.0,
        21.0,
        -3.0,
        "fusion:0:1125",
        "fa018c7ec54ae00ebbb0da84312eafb5915a3ce3ed90e57149cf78c8caa39e81",
    ),
)


# shared rotary source setup keeps fixtures consistent so native document reconstruction failures identify the intended compatibility boundary
def RotarySource(CaseValue: RotaryCase) -> FilePath:
    RootPath = FilePath(__file__).resolve().parents[5]
    return (
        RootPath
        / f"re/Fusion/LocalOracle/PublicAdapter/vendor_{CaseValue.RoleName}Edited.f3d"
    )
