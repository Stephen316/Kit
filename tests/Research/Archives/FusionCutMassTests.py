import pytest as Pytest

from interchange.enums.EnumDocument import Capability
from tests.Research.Archives.ArchiveEvidenceTests import OpenCutArchive


# the saved measurements include independent rotated and through all controls
@Pytest.mark.parametrize(
    ("Variant", "Volume", "Center"),
    (
        ("baseline-a", 7680.0, (20.0, 10.0, 4.875)),
        ("baseline-b", 7680.0, (20.0, 10.0, 4.875)),
        ("edit-width_mm-44", 8480.0, (22.0, 10.0, 4.886792453)),
        ("edit-height_mm-24", 9280.0, (20.0, 12.0, 4.896551724)),
        ("edit-depth_mm-12", 9280.0, (20.0, 10.0, 5.862068966)),
        ("edit-cut_width_mm-12", 7616.0, (20.0, 10.0, 4.848739496)),
        ("edit-cut_height_mm-10", 7600.0, (20.0, 10.0, 4.842105263)),
        ("edit-cut_depth_mm-5", 7600.0, (20.0, 10.0, 4.868421053)),
        ("units-inch", 7680.0, (20.0, 10.0, 4.875)),
        ("plane-yz", 7680.0, (4.875, 20.0, 10.0)),
        ("termination-through-all", 7200.0, (20.0, 10.0, 5.0)),
    ),
)
def CheckCutMass(
    Variant: str, Volume: float, Center: tuple[float, float, float]
) -> None:
    Document = OpenCutArchive(Variant)
    (BodyValue,) = Document.bodies
    assert BodyValue.attributes["fusion.geometry_source"] == "saved_cut_result_topology"
    assert BodyValue.topology.volume == Pytest.approx(Volume, abs=1e-6, rel=0.0)
    assert BodyValue.attributes["fusion.body_centroid_mm"] == Pytest.approx(
        Center, abs=1e-7, rel=0.0
    )
    assert "fusion.saved_cut_mass_unresolved" not in BodyValue.attributes
    assert Document.brep is None
    assert Capability.KBrep not in Document.capabilities
    assert "fusion.native_state" not in Document.metadata
