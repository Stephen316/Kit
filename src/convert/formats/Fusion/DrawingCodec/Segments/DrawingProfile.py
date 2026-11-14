from convert.formats.Fusion.DocumentCodec.Records.DocumentCatalog import (
    DocumentCatalog,
)
from convert.formats.Fusion.DrawingCodec.Segments.ReadDrawSchemas import (
    ReadDrawSchemas,
)
from convert.formats.Fusion.EntityCodec.Schema.BindProfile import BindProfile
from convert.formats.Fusion.EntityCodec.Schema.EntityProfile import EntityProfile
from convert.formats.Fusion.EntityCodec.Schema.ExternalTarget import ExternalTarget
from convert.formats.Fusion.EntityCodec.Vocabulary.CloseCatalog import CloseCatalog
from convert.formats.Fusion.EntityCodec.Vocabulary.NativeRoot import KNativeRoot
from convert.formats.Fusion.EntityCodec.Vocabulary.PickSchema import PickSchema
from convert.formats.Fusion.EntityCodec.Vocabulary.SelectClasses import SelectClasses
from convert.formats.Fusion.SegmentCodec.Metadata.MetaSegment import MetaSegment

KPinnedClasses = (("4C835764-5BAB-4421-B5D2-06015BEF6EB2", 5),)


def DrawingProfile(Metadata: tuple[MetaSegment, ...], SegmentId: int) -> EntityProfile:
    Selected = tuple(
        Segment for Segment in Metadata if Segment.Header.SegmentId == SegmentId
    )
    if len(Selected) != 1:
        raise ValueError("Missing or duplicate Fusion drawing segment identity")
    Targets = tuple(
        ExternalTarget(Segment.Header.SegmentId, ObjectId, ClassValue.ClassGuid)
        for Segment in Metadata
        if Segment.Header.SegmentId != SegmentId
        for ClassValue in Segment.Classes
        for ObjectId in ClassValue.OwnerIds
    )
    Catalog = DocumentCatalog(ReadDrawSchemas())
    Pinned = KPinnedClasses + tuple(
        (ClassValue.ClassGuid, ClassValue.SchemaVersion)
        for Segment in Metadata
        if Segment.Header.SegmentId != SegmentId
        for ClassValue in Segment.Classes
    )
    Chosen = {
        **{
            ClassGuid.upper(): PickSchema(ClassGuid, Version, Catalog)
            for ClassGuid, Version in Pinned
        },
        **SelectClasses(Selected[0].Classes, Catalog),
    }
    Profile = EntityProfile(
        KNativeRoot,
        CloseCatalog(Chosen, Catalog, Targets),
        Targets,
        Catalog.NamedTypes,
    )
    _ = BindProfile(Profile, Selected[0].Classes)
    return Profile
