import pytest as Pytest

from convert.adapters.freecad.Brep import BrepModelBrep
from convert.formats.Fusion.Revolves.JoinRevModels import JoinRevModels
from convert.geometry.Extrude.Polygon.PolygonExtrude import BuildPrism
from convert.geometry.Opencascade import decode_ascii_brep as DecodeBrep
from interchange.brep.topology.BrepModel import BrepModel
from interchange.geometry.models.GeometryCurves import LineGeometry
from interchange.geometry.models.Transform import KTransformIdentity
from interchange.geometry.models.VectorPlane import PlaneVector
from interchange.geometry.models.VectorSpace import SpaceVector


# simple separated prisms exercise one solid root and a root above multiple bodies
def MakeTestPrism(Identity: str, Shift: float = 0.0) -> BrepModel:
    Points = (
        PlaneVector(Shift, 0.0),
        PlaneVector(Shift + 10.0, 0.0),
        PlaneVector(Shift + 10.0, 6.0),
        PlaneVector(Shift, 6.0),
    )
    Profile = tuple(
        LineGeometry(Start, Finish)
        for Start, Finish in zip(Points, Points[1:] + Points[:1], strict=True)
    )
    return BuildPrism(Identity, KTransformIdentity, Profile, 0.0, 5.0)[0]


# only the location datum and root reference should differ from local shape bytes
@Pytest.mark.parametrize("Compound", (False, True))
def TestBrepRootLoc(Compound: bool) -> None:
    Model = MakeTestPrism("first")
    if Compound:
        Model = JoinRevModels((Model, MakeTestPrism("second", 20.0)))
    Translation = SpaceVector(-4.0, 4.0, 2.25)
    Default = BrepModelBrep(Model).splitlines()
    Placed = BrepModelBrep(Model, RootTranslation=Translation).splitlines()
    assert Placed[3:8] == [b"Locations 1", b"1", b"1 0 0 -4", b"0 1 0 4", b"0 0 1 2.25"]
    assert Placed[:3] == Default[:3] and Placed[8:-1] == Default[4:-1]
    assert Placed[-1].split() == [Default[-1].split()[0], b"1"]
    Restored = DecodeBrep(b"\n".join(Placed) + b"\n", id_prefix="placed")
    assert Restored is not None and Restored.validate() == ()
    assert len(Restored.regions) == len(Model.regions)
    assert len(Restored.faces) == len(Model.faces) and len(Restored.edges) == len(
        Model.edges
    )
    assert {Value.point for Value in Restored.vertices} == {
        SpaceVector(
            Value.point.x + Translation.x,
            Value.point.y + Translation.y,
            Value.point.z + Translation.z,
        )
        for Value in Model.vertices
    }


# exact zero shares the legacy representation and invalid locations are rejected
def TestBrepLocZero() -> None:
    Model = MakeTestPrism("origin")
    Original = BrepModelBrep(Model)
    assert BrepModelBrep(Model, RootTranslation=SpaceVector(0.0, -0.0, 0.0)) == Original
    for Value in (float("inf"), float("nan")):
        with Pytest.raises(ValueError, match="finite coordinates"):
            _ = BrepModelBrep(Model, RootTranslation=SpaceVector(Value, 0.0, 0.0))
