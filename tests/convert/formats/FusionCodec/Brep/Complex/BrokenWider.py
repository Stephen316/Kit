from dataclasses import replace as ReplaceValue

from convert.formats.Fusion.BrepCodec.Journal.Complex.Authoring.NurbsBody import (
    CylinderCarrier,
    NurbsBody,
    NurbsFace,
    NurbsUse,
    PlaneCarrier,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Spline.BsSurface import BsSurface
from tests.convert.formats.FusionCodec.Brep.Complex.WiderNurbs import (
    CappedTube,
    CollapsedPatch,
    DomedCylinder,
    HoledPatch,
    NurbsTorus,
    PeriodLine,
)

KWiderFaults = (
    "closure",
    "singular",
    "offset",
    "pinch",
    "analytic",
    "cap",
    "radius",
    "frame",
    "empty",
    "triple",
    "bounds",
    "sense",
    "seam",
)


def SwapFace(Model: NurbsBody, FaceIndex: int, FaceSpec: NurbsFace) -> NurbsBody:
    Faces = list(Model.Faces)
    Faces[FaceIndex] = FaceSpec
    return ReplaceValue(Model, Faces=tuple(Faces))


def SwapUse(Model: NurbsBody, FaceIndex: int, UseSpec: NurbsUse) -> NurbsBody:
    FaceSpec = Model.Faces[FaceIndex]
    return SwapFace(
        Model, FaceIndex, ReplaceValue(FaceSpec, Uses=(UseSpec, *FaceSpec.Uses[1:]))
    )


def SpliceSide(Model: NurbsBody) -> NurbsBody:
    Surface = Model.Faces[0].Surface
    if not isinstance(Surface, BsSurface):
        raise ValueError("Wider fault needs a spline side")
    Poles = list(Surface.Poles)
    Shifted = Poles[17]
    Poles[17] = (Shifted[0] + 0.1, Shifted[1], Shifted[2])
    return SwapFace(
        Model,
        0,
        ReplaceValue(Model.Faces[0], Surface=ReplaceValue(Surface, Poles=tuple(Poles))),
    )


def MoveCarrier(
    Model: NurbsBody, FaceIndex: int, Carrier: PlaneCarrier | CylinderCarrier
) -> NurbsBody:
    return SwapFace(
        Model, FaceIndex, ReplaceValue(Model.Faces[FaceIndex], Surface=Carrier)
    )


def HoleFault(Fault: str) -> NurbsBody:
    Holed = HoledPatch()
    FaceSpec = Holed.Faces[0]
    if Fault == "offset":
        HoleUses = FaceSpec.Holes[0]
        Edited = ReplaceValue(HoleUses[0], OffsetU=1.0)
        return SwapFace(
            Holed, 0, ReplaceValue(FaceSpec, Holes=((Edited, *HoleUses[1:]),))
        )
    if Fault == "empty":
        return SwapFace(Holed, 0, ReplaceValue(FaceSpec, Holes=((),)))
    Edges = list(Holed.Edges)
    Edges[4] = ReplaceValue(Edges[4], Bounds=(0.3, 1.2))
    return ReplaceValue(Holed, Edges=tuple(Edges))


def TubeFault(Fault: str) -> NurbsBody:
    Capped = CappedTube()
    if Fault == "closure":
        return SpliceSide(Capped)
    if Fault == "pinch":
        return SwapUse(Capped, 0, ReplaceValue(Capped.Faces[0].Uses[0], OffsetV=1.0))
    if Fault == "analytic":
        return SwapUse(
            Capped, 2, NurbsUse(1, False, PeriodLine((0.0, 1.0), (1.0, 1.0)))
        )
    if Fault == "cap":
        return MoveCarrier(
            Capped, 2, PlaneCarrier((0.0, 0.0, 2.5), (0.0, 0.0, 1.0), (1.0, 0.0, 0.0))
        )
    return MoveCarrier(
        Capped, 1, PlaneCarrier((0.0, 0.0, 0.0), (0.0, 0.0, -2.0), (1.0, 0.0, 0.0))
    )


def SeamFault(Fault: str) -> NurbsBody:
    Capped = CappedTube()
    FaceSpec = Capped.Faces[0]
    SeamUse = FaceSpec.Uses[1]
    Edited = (
        ReplaceValue(SeamUse, Reversed=True)
        if Fault == "sense"
        else ReplaceValue(SeamUse, OffsetU=0.0)
    )
    return SwapFace(
        Capped,
        0,
        ReplaceValue(FaceSpec, Uses=(FaceSpec.Uses[0], Edited, *FaceSpec.Uses[2:])),
    )


def BrokenWider(Fault: str) -> NurbsBody:
    if Fault in ("sense", "seam"):
        return SeamFault(Fault)
    if Fault in ("offset", "empty", "bounds"):
        return HoleFault(Fault)
    if Fault in ("closure", "pinch", "analytic", "cap", "frame"):
        return TubeFault(Fault)
    if Fault == "singular":
        Collapsed = CollapsedPatch()
        Surface = Collapsed.Faces[0].Surface
        if not isinstance(Surface, BsSurface):
            raise ValueError("Wider fault needs a spline patch")
        return SwapFace(
            Collapsed,
            0,
            ReplaceValue(
                Collapsed.Faces[0], Surface=ReplaceValue(Surface, VSingular=1)
            ),
        )
    if Fault == "radius":
        return MoveCarrier(
            DomedCylinder(),
            0,
            CylinderCarrier((0.0, 0.0, 0.0), (0.0, 0.0, 1.0), (1.2, 0.0, 0.0)),
        )
    Torus = NurbsTorus()
    FaceSpec = Torus.Faces[0]
    return SwapFace(
        Torus, 0, ReplaceValue(FaceSpec, Uses=(*FaceSpec.Uses, FaceSpec.Uses[0]))
    )
