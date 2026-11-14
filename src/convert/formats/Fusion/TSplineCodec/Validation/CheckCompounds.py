from convert.formats.Fusion.TSplineCodec.Model.TsplineSurface import TsplineSurface
from convert.formats.Fusion.TSplineCodec.Validation.CheckIndices import CheckIndices


def CheckCompounds(Surface: TsplineSurface) -> None:
    Mapping = Surface.Mapping
    if Mapping is None:
        return
    CheckIndices(
        tuple(Value.VertexIndex for Value in Mapping.Compounds),
        len(Surface.Topology.Vertices),
        "compound owner",
    )
    Referenced: list[int] = []
    for Layout in Mapping.Compounds:
        Lengths = Layout.SpokeLengths
        if len(Lengths) != 4 or any(
            type(Value) is not int or Value not in (0, 1) for Value in Lengths
        ):
            raise ValueError("Unsupported TSM compound spoke layout")
        Expected = sum(
            Value + Value * Lengths[(Index + 1) % 4]
            for Index, Value in enumerate(Lengths)
        )
        if len(Layout.GripIndices) != Expected or Expected == 0:
            raise ValueError("TSM compound grip count differs")
        CheckIndices(Layout.GripIndices, len(Surface.Grips), "compound grip")
        for Index in Layout.GripIndices:
            Owner = Mapping.Owners[Index]
            if Owner.VertexIndex != Layout.VertexIndex or Owner.IsPrimary:
                raise ValueError("TSM compound grip ownership differs")
        Referenced.extend(Layout.GripIndices)
    ExpectedSet = {
        Index for Index, Owner in enumerate(Mapping.Owners) if not Owner.IsPrimary
    }
    if len(set(Referenced)) != len(Referenced) or set(Referenced) != ExpectedSet:
        raise ValueError("TSM compound layouts do not cover secondary grips")
