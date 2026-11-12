from math import radians as Radians

from convert.adapters.freecad.Brep import BrepModelBrep
from convert.adapters.freecad.EditShape.Revolution.RevolveShape import IsEditRevolve
from convert.geometry.Revolve.FullPolySweep import BuildFullSweep
from convert.geometry.Revolve.PolygonSweep import BuildPolySweep
from interchange.brep.topology.BrepModel import BrepModel
from interchange.geometry.models.Transform import KAxisX, KAxisY, KAxisZ, KOriginZero

# this positive radius ring has the same analytic carriers after phase only changes
KTestMeridian = ((10.0, 0.0), (30.0, 0.0), (30.0, 20.0), (10.0, 20.0))


# meridian coordinates and angle are independent input witnesses
def MakeRevolve(
    Start: float, EndValue: float, Corner: tuple[float, float] = (30.0, 20.0)
) -> BrepModel:
    Profile = (*KTestMeridian[:2], Corner, KTestMeridian[-1])
    return BuildPolySweep(
        "test-revolve",
        Profile,
        KOriginZero,
        KAxisZ,
        KAxisX,
        Radians(Start),
        Radians(EndValue),
    )


# equal spans cannot make an incorrect absolute sweep phase or stale corner valid
def TestRevPhase() -> None:
    Expected = MakeRevolve(0.0, 80.0)
    ShapeData = BrepModelBrep(Expected)
    assert IsEditRevolve(ShapeData, Expected)
    assert not IsEditRevolve(ShapeData, MakeRevolve(30.0, 110.0))
    assert not IsEditRevolve(ShapeData, MakeRevolve(-80.0, 0.0))
    assert not IsEditRevolve(ShapeData, MakeRevolve(0.0, 81.0))
    assert not IsEditRevolve(ShapeData, MakeRevolve(0.0, 80.0, (27.0, 17.0)))


# the shell and pcurve guards reject changed topology even with identical spatial carriers
def TestRevolveTrim() -> None:
    Expected = MakeRevolve(0.0, 80.0)
    ShapeData = BrepModelBrep(Expected)
    Prefix, Pcurves = ShapeData.split(b"Curve2ds ", 1)
    Count, CurveRow, Remaining = Pcurves.split(b"\n", 2)
    KindValue, Origin, Remainder = CurveRow.split(maxsplit=2)
    Changed = b" ".join((KindValue, str(float(Origin) + 1.0).encode(), Remainder))
    WrongTrim = Prefix + b"Curve2ds " + b"\n".join((Count, Changed, Remaining))
    ShellHead, ShellData = ShapeData.split(b"\nSh\n", 1)
    ShellLine, Flags, TailValue = ShellData.split(b"\n", 2)
    assert Flags[4:5] == b"1"
    OpenShell = (
        ShellHead
        + b"\nSh\n"
        + b"\n".join((ShellLine, Flags[:4] + b"0" + Flags[5:], TailValue))
    )
    assert not IsEditRevolve(WrongTrim, Expected)
    assert not IsEditRevolve(OpenShell, Expected)
    assert not IsEditRevolve(ShapeData + b"\nSo", Expected)


# full annuli retain their geometry when the reference seam moves in phase
def TestRevSeams() -> None:
    Model = BuildFullSweep("test-revolve", KTestMeridian, KOriginZero, KAxisZ, KAxisX)
    Expected = BuildFullSweep(
        "test-revolve", KTestMeridian, KOriginZero, KAxisZ, KAxisY
    )
    ShapeData = BrepModelBrep(Model)
    assert b" CN " in ShapeData
    assert IsEditRevolve(ShapeData, Expected)
    assert not IsEditRevolve(ShapeData.replace(b" CN ", b" C1 ", 1), Expected)
