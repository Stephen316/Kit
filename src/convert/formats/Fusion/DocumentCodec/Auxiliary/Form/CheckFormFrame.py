from convert.formats.Fusion.EntityCodec.Model.EntityRecord import EntityRecord
from convert.formats.Fusion.DocumentCodec.Reading.Materials.GroupFields import (
    GroupFields,
)
from convert.formats.Fusion.TSplineCodec.Model.TsplineSurface import TsplineSurface
from convert.formats.Fusion.EntityCodec.Model.ValueSeries import ValueSeries
from convert.formats.Fusion.DocumentCodec.Auxiliary.Form.FormTarget import FormTarget
from convert.formats.Fusion.DocumentCodec.Auxiliary.Form.FrameIndex import FrameIndex
from convert.formats.Fusion.DocumentCodec.Auxiliary.Form.FormLayout import KSurfaceGuid


def CheckFormFrame(
    Record: EntityRecord,
    Owners: dict[int, EntityRecord],
    Joined: dict[int, TsplineSurface],
) -> None:
    Fields = GroupFields(Record.Groups)
    Surface = FormTarget(Fields.get("rSurface"), Owners, KSurfaceGuid)
    Program = Joined.get(Surface.ObjectId)
    if Program is None:
        raise ValueError("Control frame surface has no serialized T-spline part")
    Expected = {
        "facets": len(Program.Topology.Faces),
        "edges": len(Program.Topology.Edges),
        "vertices": len(Program.Topology.Vertices),
        "grips": len(Program.Grips),
    }
    for FieldName, Count in Expected.items():
        Items = Fields.get(FieldName)
        if not isinstance(Items, ValueSeries):
            raise ValueError("Control frame entity list is missing")
        Indices = sorted(
            FrameIndex(ItemValue, Owners, Record.ObjectId) for ItemValue in Items.Items
        )
        if Indices != list(range(Count)):
            raise ValueError("Control frame entities disagree with the T-spline part")
