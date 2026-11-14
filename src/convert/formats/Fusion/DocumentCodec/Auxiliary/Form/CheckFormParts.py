from convert.formats.Fusion.EntityCodec.Model.EntityRecord import EntityRecord
from convert.formats.Fusion.SegmentCodec.Features.Model.LocalRef import LocalRef
from convert.formats.Fusion.DocumentCodec.Reading.Materials.GroupFields import (
    GroupFields,
)
from convert.formats.Fusion.TSplineCodec.Model.TsplineSurface import TsplineSurface
from convert.formats.Fusion.DocumentCodec.Model.DocumentForm import DocumentForm
from convert.formats.Fusion.DocumentCodec.Auxiliary.Form.FormName import FormName
from convert.formats.Fusion.DocumentCodec.Auxiliary.Form.FormTarget import FormTarget
from convert.formats.Fusion.DocumentCodec.Auxiliary.Form.LeadGuid import LeadGuid
from convert.formats.Fusion.DocumentCodec.Auxiliary.Form.FormLayout import (
    KSerialGuid,
    KSurfaceGuid,
)


def CheckFormParts(
    Owners: dict[int, EntityRecord], Forms: tuple[DocumentForm, ...]
) -> dict[int, TsplineSurface]:
    Parts = {FormName(Value.Name): Value.Surface for Value in Forms}
    if len(Parts) != len(Forms):
        raise ValueError("Document T-spline part names are duplicated")
    Joined: dict[int, TsplineSurface] = {}
    Names: list[str] = []
    for Record in Owners.values():
        if LeadGuid(Record) != KSerialGuid:
            continue
        Fields = GroupFields(Record.Groups)
        PartName = Fields.get("partName")
        if type(PartName) is not str or PartName not in Parts:
            raise ValueError("T-spline serializer names no document T-spline part")
        Surface = FormTarget(Fields.get("rSurface"), Owners, KSurfaceGuid)
        OwnerRef = GroupFields(Surface.Groups).get("rSerializer")
        if not isinstance(OwnerRef, LocalRef) or OwnerRef.ObjectId != Record.ObjectId:
            raise ValueError("T-spline surface does not own its serializer")
        Names.append(PartName)
        Joined[Surface.ObjectId] = Parts[PartName]
    if len(set(Names)) != len(Names) or set(Names) != set(Parts):
        raise ValueError("Document T-spline parts and serializers disagree")
    return Joined
