from convert.adapters.freecad.EditShape.CylinderRims import IsNearPoint
from convert.adapters.freecad.EditShape.Prism.PrismRaw import KLocationChain, PrismRaw
from convert.geometry.Opencascade import (
    DecodeFailure,
    LocationPoint,
    Reference,
    VertexData,
)
from interchange.geometry.models.VectorSpace import SpaceVector

# native edge selection needs the exact directed endpoints at its saved subelement number
KPrismLink = tuple[int, SpaceVector, SpaceVector]


# first seen located edge identities reproduce freecad subelement numbering
def PrismEdgeRefs(
    RawValue: PrismRaw,
) -> list[tuple[Reference, KLocationChain, bool]]:
    (Shell,) = RawValue.Records[RawValue.RootRef.RecordA].Children
    ShellPlace = RawValue.Place(Shell, RawValue.Place(RawValue.RootRef))
    SeenValues: set[tuple[int, KLocationChain]] = set()
    Edges: list[tuple[Reference, KLocationChain, bool]] = []
    for FaceValue in RawValue.Records[Shell.RecordA].Children:
        (WireValue,) = RawValue.Records[FaceValue.RecordA].Children
        WirePlace = RawValue.Place(WireValue, RawValue.Place(FaceValue, ShellPlace))
        Prefix = (
            (Shell.Orientation == "-")
            ^ (FaceValue.Orientation == "-")
            ^ (WireValue.Orientation == "-")
        )
        for EdgeValue in RawValue.Records[WireValue.RecordA].Children:
            Place = RawValue.Place(EdgeValue, WirePlace)
            KeyValue = EdgeValue.RecordA, Place
            if KeyValue not in SeenValues:
                SeenValues.add(KeyValue)
                Edges.append(
                    (EdgeValue, Place, Prefix ^ (EdgeValue.Orientation == "-"))
                )
    return Edges


# a changed native record order cannot silently redirect a correct looking solid
def CheckPrismLink(RawValue: PrismRaw, LinkValue: KPrismLink) -> None:
    SlotValue, Start, Finish = LinkValue
    References = PrismEdgeRefs(RawValue)
    if not 0 < SlotValue <= len(References):
        raise DecodeFailure("saved prism edge slot is missing")
    EdgeValue, Place, Reverse = References[SlotValue - 1]
    Vertices = RawValue.Records[EdgeValue.RecordA].Children
    Points: dict[str, SpaceVector] = {}
    for RefValue in Vertices:
        DataValue = RawValue.Records[RefValue.RecordA].GeometryA
        if not isinstance(DataValue, VertexData):
            raise DecodeFailure("saved prism edge has no bounded vertex")
        Points[RefValue.Orientation] = LocationPoint(
            RawValue.Matrix(RawValue.Place(RefValue, Place)), DataValue.Point
        )
    if set(Points) != {"+", "-"}:
        raise DecodeFailure("saved prism edge has no directed endpoints")
    HeadValue, TailValue = ("-", "+") if Reverse else ("+", "-")
    if not IsNearPoint(Points[HeadValue], Start) or not IsNearPoint(
        Points[TailValue], Finish
    ):
        raise DecodeFailure("saved prism selected edge slot disagrees with its axis")
