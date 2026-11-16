from dataclasses import dataclass as MakeDataClass
from pathlib import Path as FilePath


# the vendor case boundary needs grouped coverage so repository automation cannot silently change its observable contract
@MakeDataClass(frozen=True, slots=True)
class VendorCase:
    Source: str
    OutputDigest: str
    BodyId: str
    Parameters: tuple[str, ...]
    Volume: float
    Density: float


# the vendor cases cases must remain explicit so native document reconstruction exercises the intended compatibility boundary
KVendorCases = (
    VendorCase(
        "re/Fusion/Study/thinextrudes-c1632bcb5efe/ordinary_rectangle_control.f3d",
        "0203674063f58504d037a51236a1aff9cc3283ed1b8b107cc8307e1e73f10e92",
        "fusion:0:311",
        ("d1", "d2"),
        30000.0,
        7850.0,
    ),
    VendorCase(
        "re/Fusion/LocalOracle/RectangleAuthoring/vendor_ProductionCuboid37mm.f3d",
        "49f92bbe4f33fc7c1413ca8a8d433ff3ba948c1822c6513363934425f626ec31",
        "fusion:0:1140",
        ("authoredLength", "d2", "d3"),
        14467.0,
        1000.0,
    ),
)


# shared vendor source setup keeps fixtures consistent so native document reconstruction failures identify the intended compatibility boundary
def VendorSource(CaseValue: VendorCase) -> FilePath:
    return FilePath(__file__).resolve().parents[5] / CaseValue.Source
