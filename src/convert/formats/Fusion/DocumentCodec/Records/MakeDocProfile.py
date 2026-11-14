from convert.formats.Fusion.DocumentCodec.Records.MakeDesignProf import MakeDesignProf
from convert.formats.Fusion.DocumentCodec.Records.PickVersions import PickVersions
from convert.formats.Fusion.EntityCodec.Schema.ClassSchema import ClassSchema
from convert.formats.Fusion.EntityCodec.Schema.EntityProfile import EntityProfile
from convert.formats.Fusion.EntityCodec.Schema.ExternalTarget import ExternalTarget
from convert.formats.Fusion.MetaIndex import SegmentKind
from convert.formats.Fusion.SegmentCodec.Metadata.MetaSegment import MetaSegment


def MakeDocProfile(
    Schemas: tuple[ClassSchema, ...], Metadata: tuple[MetaSegment, ...], SegmentId: int
) -> EntityProfile:
    Targets = tuple(
        ExternalTarget(Segment.Header.SegmentId, ObjectId, ClassValue.ClassGuid)
        for Segment in Metadata
        if Segment.Header.SegmentId != SegmentId
        for ClassValue in Segment.Classes
        for ObjectId in ClassValue.OwnerIds
    )
    Selected = tuple(
        Segment for Segment in Metadata if Segment.Header.SegmentId == SegmentId
    )
    if len(Selected) != 1:
        raise ValueError("Missing or duplicate Fusion document segment identity")
    if Selected[0].Header.Segment == SegmentKind.KDesign:
        return MakeDesignProf(Schemas, Selected[0].Classes, Targets)
    return EntityProfile(
        "98542EB9-A4F2-4137-A808-DBB5B3CD6159",
        PickVersions(Schemas, Selected[0].Classes),
        Targets,
    )
