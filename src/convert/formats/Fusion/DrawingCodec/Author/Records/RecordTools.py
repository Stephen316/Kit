from convert.formats.Fusion.EntityCodec.Model.EntityFrame import EntityFrame
from convert.formats.Fusion.EntityCodec.Model.EntityGroup import EntityGroup
from convert.formats.Fusion.EntityCodec.Model.EntityRecord import EntityRecord
from convert.formats.Fusion.EntityCodec.Model.NamedMetadata import NamedMetadata
from convert.formats.Fusion.EntityCodec.Model.NamedValue import NamedValue
from convert.formats.Fusion.EntityCodec.Model.SubjectValue import SubjectValue
from convert.formats.Fusion.EntityCodec.Model.ValueSeries import ValueSeries
from convert.formats.Fusion.EntityCodec.Model.ValueTypes import KEntityValue
from convert.formats.Fusion.SegmentCodec.Features.Model.LocalRef import LocalRef

KClientGuid = "A7AEA631-985B-4DD1-8CE2-DE2C-14B54081"

KChildGuid = "834C9DEF-4C39-4587-A08D-A5BD1267B7B4"

KParentGuid = "CB844AB6-240D-4fc9-9C9F-3679DC896D6F"

KObjectGuid = "63D6AD42-466A-40B7-9CCD-EB21BC500EF6"


def ChildTail(
    Parent: LocalRef | None, Children: tuple[LocalRef, ...] = ()
) -> tuple[EntityGroup[KEntityValue], ...]:
    return (
        EntityGroup(KClientGuid, (NamedValue("rClientObject", None),)),
        EntityGroup(KChildGuid, (NamedValue("children", ValueSeries(Children)),)),
        EntityGroup(KParentGuid, (NamedValue("rParent", Parent),)),
    )


def ObjectTail(Parent: LocalRef | None) -> tuple[EntityGroup[KEntityValue], ...]:
    return (
        EntityGroup(KObjectGuid, (NamedValue("rClientObject", None),)),
        EntityGroup(KParentGuid, (NamedValue("rParent", Parent),)),
    )


def MakeRecord(
    ObjectId: int,
    Groups: tuple[EntityGroup[KEntityValue], ...],
    RootId: str = "",
    IsPrimary: bool = True,
    Subjects: tuple[SubjectValue, ...] | None = None,
    Metadata: tuple[NamedMetadata, ...] | None = None,
) -> EntityRecord:
    return EntityRecord(
        ObjectId, 0, IsPrimary, EntityFrame(RootId, Subjects, Metadata), Groups
    )
