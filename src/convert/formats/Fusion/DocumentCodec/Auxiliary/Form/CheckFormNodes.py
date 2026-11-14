from convert.formats.Fusion.EntityCodec.Model.EntityRecord import EntityRecord
from convert.formats.Fusion.EntityCodec.Model.ValueSeries import ValueSeries
from convert.formats.Fusion.SegmentCodec.Features.Model.LocalRef import LocalRef
from convert.formats.Fusion.DocumentCodec.Reading.Materials.GroupFields import (
    GroupFields,
)
from convert.formats.Fusion.TSplineCodec.Model.TsplineSurface import TsplineSurface
from convert.formats.Fusion.DocumentCodec.Auxiliary.Form.FormTarget import FormTarget
from convert.formats.Fusion.DocumentCodec.Auxiliary.Form.MetaValue import MetaValue
from convert.formats.Fusion.DocumentCodec.Auxiliary.Form.FormLayout import (
    KBodiesMeta,
    KBodyGuid,
    KNodeMeta,
    KSurfaceGuid,
)


def CheckFormNodes(
    Record: EntityRecord,
    Owners: dict[int, EntityRecord],
    Joined: dict[int, TsplineSurface],
) -> None:
    SurfaceRef = GroupFields(Record.Groups).get("rSurface")
    Surface = FormTarget(SurfaceRef, Owners, KSurfaceGuid)
    OwnerRef = GroupFields(Surface.Groups).get("rVSurface")
    if Surface.ObjectId not in Joined or not isinstance(OwnerRef, LocalRef):
        raise ValueError("T-spline surface node has no serialized surface")
    if OwnerRef.ObjectId != Record.ObjectId:
        raise ValueError("T-spline surface does not name its surface node")
    Bodies = MetaValue(Record, KBodiesMeta)
    if not isinstance(Bodies, ValueSeries) or not Bodies.Items:
        raise ValueError("T-spline surface node names no converted body")
    for ItemValue in Bodies.Items:
        BodyValue = FormTarget(ItemValue, Owners, KBodyGuid)
        BackRef = MetaValue(BodyValue, KNodeMeta)
        if not isinstance(BackRef, LocalRef) or BackRef.ObjectId != Record.ObjectId:
            raise ValueError("Converted Form body names another surface node")
