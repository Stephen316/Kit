from dataclasses import replace as ReplaceValue
from math import pi as CirclePi

from pytest import approx as Approx, raises as Raises

from convert.adapters.freecad.Brep import BrepModelBrep, FreeCADBrepWriteError
from convert.geometry.Parasolid import EncodeBrepModel, ParaWriteError
from convert.geometry.Revolve.SphereSweep import BuildSphere
from interchange.brep.surfaces.BrepSurfaces import SphereSurface
from interchange.geometry.models.VectorSpace import SpaceVector
from interchange.serialization.Deserialize import FromData
from interchange.serialization.EncodeData import ToData


# the sphere retains its tilted frame without changing world aligned bounds
def TestSphereSolid() -> None:
    Center = SpaceVector(10.0, -20.0, 30.0)
    AxisValue = SpaceVector(0.0, 0.6, 0.8)
    Radial = SpaceVector(1.0, 0.0, 0.0)
    Model, Volume, AreaValue, Bounds = BuildSphere(
        "part", Center, AxisValue, Radial, 2.0
    )
    assert Model.validate(frozenset(("part",))) == ()
    assert FromData(ToData(Model)) == Model
    assert Model.surfaces == (
        SphereSurface(Model.faces[0].surface_id, Center, AxisValue, Radial, 2.0),
    )
    assert not (Model.loops or Model.edges or Model.vertices)
    assert Model.shells[0].closed and Model.regions[0].solid
    assert Model.shells[0].face_use_ids == (Model.face_uses[0].id,)
    assert Model.face_uses[0].face_id == Model.faces[0].id
    assert Model.bodies[0].design_body_id == "part"
    assert Volume == Approx(32.0 * CirclePi / 3.0)
    assert AreaValue == Approx(16.0 * CirclePi)
    assert Bounds.minimum == SpaceVector(8.0, -22.0, 28.0)
    assert Bounds.maximum == SpaceVector(12.0, -18.0, 32.0)


# a missing trim loop is valid only for a finite carrier in a closed owned shell
def TestSphereGuard() -> None:
    Center = SpaceVector(0.0, 0.0, 0.0)
    AxisValue = SpaceVector(0.0, 0.0, 1.0)
    Radial = SpaceVector(1.0, 0.0, 0.0)
    Model = BuildSphere("part", Center, AxisValue, Radial, 2.0)[0]
    OpenValue = ReplaceValue(
        Model, shells=(ReplaceValue(Model.shells[0], closed=False),)
    )
    assert any(
        "has no loops" in Error for Error in OpenValue.validate(frozenset(("part",)))
    )
    Unowned = ReplaceValue(Model, regions=())
    assert any(
        "has no loops" in Error for Error in Unowned.validate(frozenset(("part",)))
    )
    with Raises(ValueError, match="orthonormal sphere"):
        _ = BuildSphere("part", Center, AxisValue, AxisValue, 2.0)
    with Raises(ValueError, match="orthonormal sphere"):
        _ = BuildSphere("part", Center, AxisValue, Radial, 0.0)


# unproven native sphere topology must fail before target bytes are emitted
def TestSphereWrite() -> None:
    Model = BuildSphere(
        "part",
        SpaceVector(0.0, 0.0, 0.0),
        SpaceVector(0.0, 0.0, 1.0),
        SpaceVector(1.0, 0.0, 0.0),
        2.0,
    )[0]
    with Raises(FreeCADBrepWriteError, match="lacks a proven native topology"):
        _ = BrepModelBrep(Model)
    with Raises(ParaWriteError, match="first loop"):
        _ = EncodeBrepModel(Model)
