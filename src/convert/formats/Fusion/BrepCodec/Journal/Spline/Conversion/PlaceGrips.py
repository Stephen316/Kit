from convert.formats.Fusion.BrepCodec.Journal.Spline.Conversion.PlaceVertices import (
    KSpokeSteps,
)
from convert.formats.Fusion.TSplineCodec.Model.CompoundGrip import CompoundGrip
from convert.formats.Fusion.TSplineCodec.Model.GripMapping import GripMapping


def PoleIndex(Value: int, Limit: int) -> int:
    return 0 if Value == 0 else Limit + 2 if Value == Limit else Value + 1


def SpokePoles(
    Compound: CompoundGrip, Center: tuple[int, int]
) -> tuple[tuple[int, int], ...]:
    Lengths = Compound.SpokeLengths
    if len(Lengths) != 4 or any(Length not in (0, 1) for Length in Lengths):
        raise ValueError("Fusion grid conversion needs unit compound spokes")
    Targets: list[tuple[int, int]] = []
    for Spoke, Length in enumerate(Lengths):
        StepU, StepV = KSpokeSteps[Spoke]
        TurnU, TurnV = KSpokeSteps[(Spoke + 1) % 4]
        if Length:
            Targets.append((Center[0] + StepU, Center[1] + StepV))
        if Length and Lengths[(Spoke + 1) % 4]:
            Targets.append((Center[0] + StepU + TurnU, Center[1] + StepV + TurnV))
    if len(Targets) != len(Compound.GripIndices):
        raise ValueError("Fusion grid conversion found unused compound grips")
    return tuple(Targets)


def PlaceGrips(
    Mapping: GripMapping, Places: tuple[tuple[int, int], ...], GripCount: int
) -> tuple[int, int, tuple[int, ...]]:
    LimitU = max(Place[0] for Place in Places)
    LimitV = max(Place[1] for Place in Places)
    if min(min(Place) for Place in Places) != 0 or min(LimitU, LimitV) < 1:
        raise ValueError("Fusion grid conversion needs a rectangular open cage")
    if len(set(Places)) != len(Places) or len(Places) != (LimitU + 1) * (LimitV + 1):
        raise ValueError("Fusion grid conversion needs a complete vertex grid")
    Centers = [
        (PoleIndex(Place[0], LimitU), PoleIndex(Place[1], LimitV)) for Place in Places
    ]
    Assigned = [
        (Centers[Owner.VertexIndex], GripIndex)
        for GripIndex, Owner in enumerate(Mapping.Owners)
        if Owner.IsPrimary
    ]
    for Compound in Mapping.Compounds:
        Targets = SpokePoles(Compound, Centers[Compound.VertexIndex])
        Assigned.extend(zip(Targets, Compound.GripIndices))
    Poles = dict(Assigned)
    Width, Height = LimitU + 3, LimitV + 3
    Order = tuple(
        Poles.get((ColumnIndex, RowIndex), -1)
        for RowIndex in range(Height)
        for ColumnIndex in range(Width)
    )
    if len(Poles) != len(Assigned) or len(Assigned) != Width * Height:
        raise ValueError("Fusion grid conversion needs one grip per pole")
    if -1 in Order or sorted(Order) != list(range(GripCount)):
        raise ValueError("Fusion grid conversion needs one pole per grip")
    return Width, Height, Order
