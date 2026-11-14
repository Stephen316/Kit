from convert.formats.Fusion.ContainerCodec.Model.SegmentStreams import SegmentStreams
from convert.formats.Fusion.DocumentCodec.Model.AuthorState import AuthorState
from convert.formats.Fusion.DocumentCodec.Model.DesignResult import DesignResult
from convert.formats.Fusion.DocumentCodec.Records.DesignProfile import DesignProfile
from convert.formats.Fusion.DocumentCodec.Records.DraftRecords import DraftRecords
from convert.formats.Fusion.EntityCodec.EncodeEntities import EncodeEntities
from convert.formats.Fusion.MetaIndex import SegmentKind
from convert.formats.Fusion.SegmentCodec.Bulk.EmitBulkStream import EmitBulkStream
from convert.formats.Fusion.SegmentCodec.Metadata.MetaHeader import MetaHeader
from convert.formats.Fusion.SegmentCodec.Metadata.MetaRows import (
    MetaClass,
    MetaOffset,
    MetaProperty,
)
from convert.formats.Fusion.SegmentCodec.Metadata.MetaSegment import MetaSegment
from convert.formats.Fusion.SegmentCodec.Metadata.WriteMetaWire import WriteMetaWire


def EmitDesign(Author: AuthorState) -> DesignResult:
    Schemas = tuple(
        sorted(Author.Schemas, key=lambda Schema: Schema.Value.ClassGuid.upper())
    )
    TypeCodes = {
        Schema.Value.ClassGuid.upper(): 256 + Index
        for Index, Schema in enumerate(Schemas)
    }
    Records = DraftRecords(Author, TypeCodes)
    Classes = tuple(
        MetaClass(
            Schema.Value.ClassGuid,
            Schema.Value.BaseGuid,
            Schema.Value.SchemaVersion,
            Schema.ClassSpace,
            tuple(
                Record.ObjectId
                for Record in Records
                if Record.IsPrimary
                and Record.TypeCode == TypeCodes[Schema.Value.ClassGuid.upper()]
            ),
        )
        for Schema in Schemas
    )
    Profile = DesignProfile(Author)
    BulkData, Offsets = EmitBulkStream(EncodeEntities(Records, Classes, Profile))
    Software = (2706 << 50) | (1 << 38) | 17
    Header = MetaHeader(
        SegmentKind.KDesign,
        Author.Policy.DesignSegmentId,
        "00000000-0000-0000-0000-000000000000",
        1234,
        8,
        (Software & 0xFFFFFFFF, Software >> 32),
        SegmentKind.KDesign.value,
        "Fusion",
        (1, 0),
    )
    Roots = tuple(
        Author.Roles[Entity.RoleName] for Entity in Author.Entities if Entity.RootName
    )
    Primary = tuple(
        MetaOffset(ObjectId, Offset)
        for Offset, ObjectId, IsPrimary in Offsets
        if IsPrimary
    )
    Continued = tuple(
        MetaOffset(ObjectId, Offset)
        for Offset, ObjectId, IsPrimary in Offsets
        if not IsPrimary
    )
    Properties = tuple(
        MetaProperty(NameValue, Version)
        for NameValue, Version in (("Application", 9), ("Server", 7), ("VolField", 7))
    )
    Metadata = WriteMetaWire(
        MetaSegment(
            Header, Classes, Roots, Primary, Continued, Author.NextId, 0, Properties
        )
    )
    Streams = SegmentStreams(Author.Policy.DesignSegmentId, Metadata, BulkData)
    HasBody = Author.SpecValue.ProfileKind in (
        "extrusion",
        "cuboid",
        "frustum",
        "part",
        "form",
    )
    return DesignResult(
        Streams,
        Records,
        Profile,
        Author.Roles.copy(),
        Author.ComponentId,
        Author.InstanceId,
        Author.RevisionId,
        Author.AssetId,
        Author.NextId,
        Author.BrepPart if HasBody else None,
        Author.BodyId if HasBody else None,
        Author.Materials,
    )
