from pathlib import Path as FilePath

import pytest as Pytest

from convert.api.ApiOpen import OpenDocument
from interchange.features.FeatureDistExt import DistanceExtrude
from interchange.geometry.models.VectorSpace import SpaceVector


# the archive controls separate signed depth from the stored frame direction
@Pytest.mark.parametrize(
    ("Variant", "Depth", "Formula", "Normal", "Bounds"),
    (
        ("baseline-a", 1.0, "10 mm", (0, 0, 1), (0, 10)),
        ("baseline-b", 1.0, "10 mm", (0, 0, 1), (0, 10)),
        ("edit-width_mm-41", 1.0, "10 mm", (0, 0, 1), (0, 10)),
        ("edit-height_mm-23", 1.0, "10 mm", (0, 0, 1), (0, 10)),
        ("edit-depth_mm-12", 1.2, "12 mm", (0, 0, 1), (0, 12)),
        ("units-inch", 1.0, "10 mm", (0, 0, 1), (0, 10)),
        ("plane-yz", 1.0, "10 mm", (1, 0, 0), (0, 10)),
        ("direction-negative", -1.0, "-( 10 mm )", (0, 0, 1), (-10, 0)),
    ),
)
def CheckBossSource(
    Variant: str,
    Depth: float,
    Formula: str,
    Normal: tuple[int, int, int],
    Bounds: tuple[int, int],
) -> None:
    RootDir = FilePath(__file__).resolve().parents[3]
    Archive = (
        RootDir
        / "re/automation/PairedCaptures/P03/fusion-8d53584027ff"
        / f"P03-fusion-{Variant}.f3d"
    )
    Document = OpenDocument(Archive, StrictMode=False)
    Feature = Document.feature_timeline[-1]
    Definition = Feature.definition
    assert isinstance(Definition, DistanceExtrude)
    assert Definition.SideMode == "one_sided" and Definition.StartOffsetId is None
    assert Definition.Direction == SpaceVector(
        float(Normal[0]), float(Normal[1]), float(Normal[2])
    )
    Attrs = Feature.attributes
    assert Attrs["fusion.extrude.start_kind"] == "profile_plane"
    assert (
        Attrs["fusion.extrude.start_frame_id"] == Document.sketches[0].support_plane_id
    )
    assert Attrs["fusion.extrude.end_kind"] == "distance"
    assert Attrs["fusion.extrude.native_direction"] == Normal
    assert Attrs["fusion.extrude.along_binding_object_id"] == 286
    assert Attrs["fusion.extrude.cache_object_id"] == 291
    assert Attrs["fusion.profile_loop_object_id"] == 284
    Parameter = next(
        Value
        for Value in Document.parameters
        if Value.id == Definition.AlongParameterId
    )
    assert Parameter.owner_id == Feature.id and Parameter.value.unit == "cm"
    assert Parameter.value.value == Pytest.approx(Depth)
    assert Parameter.expression is not None and Parameter.expression.source == Formula
    assert Parameter.provenance is not None and Parameter.provenance.native_id == "285"
    assert Feature.provenance is not None
    assert all(
        Value in Feature.provenance.spans for Value in Parameter.provenance.spans
    )
    assert any(
        Value.record_kind == "0897AF07-EF1B-42E5-BDD9-1C746A085CBC"
        for Value in Feature.provenance.spans
    )
    BoxValue = Document.bodies[0].topology.bounding_box
    assert BoxValue is not None
    Extrema = (
        (BoxValue.minimum.x, BoxValue.maximum.x)
        if Normal[0]
        else (BoxValue.minimum.z, BoxValue.maximum.z)
    )
    assert Extrema == Pytest.approx(Bounds)
