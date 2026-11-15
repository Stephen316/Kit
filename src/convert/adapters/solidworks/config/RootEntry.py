from functools import partial as Partial

from convert.adapters.solidworks.config.RootLayout import KConfigGen, KRootClass
from convert.adapters.solidworks.container.Archive import (
    KClassRefKind,
    KDefinitionKind,
    KNullKind,
    ArchiveError,
    Frame,
    LayoutTable,
    Segment,
    Segmentation,
    TagAction,
)
from convert.adapters.solidworks.container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.container.ArchiveTags import (
    BindMapTagMut,
    ResolveMapType,
)


# the enclosing parser needs the binding map as soon as the requested body begins
class EntryStop(Segmentation):

    # normal segmentation progress preserves the map until the caller can resume it
    def __init__(
        self,
        NameValue: str,
        Offset: int,
        Counter: int,
        Classes: dict[int, str],
        Objects: dict[int, str],
    ) -> None:
        super().__init__(NameValue, "lead", Offset, "typed configuration entry")
        self.Counter = Counter
        self.Classes = Classes
        self.Objects = Objects


# the native part root creates its shared extension before ordinary allocation starts
def SeedPartMut(
    TagValue: TagAction, Classes: dict[int, str], Objects: dict[int, str]
) -> None:
    RequireArch(
        (TagValue.kind, TagValue.class_name, TagValue.schema),
        (KDefinitionKind, KRootClass, 1),
        "native part root",
    )
    Classes[1] = KRootClass
    Objects.update({2: KRootClass, 3: "moExtObject_c"})


# native configuration references can only target earlier allocations of the correct kind
def ResolveSeedMut(
    StopClass: str,
    TagValue: TagAction,
    Counter: int,
    BaseValue: int,
    Layouts: LayoutTable,
    Frames: list[Frame],
    Classes: dict[int, str],
    Objects: dict[int, str],
    ParentName: str,
    ParentSlot: str,
    Offset: int,
) -> tuple[int, int, str, int]:
    if Offset == 0:
        SeedPartMut(TagValue, Classes, Objects)
        return 1, 2, KRootClass, BaseValue
    NameValue = ResolveMapType(TagValue, Classes, Objects)
    ObjectIndex, NextIndex = BindMapTagMut(
        TagValue, Counter, Classes, Objects, NameValue
    )
    if NameValue is None:
        return 0, 0, KNullKind, NextIndex
    if TagValue.kind in (KDefinitionKind, KClassRefKind):
        if NameValue == StopClass:
            raise EntryStop(StopClass, Offset, NextIndex, Classes, Objects)
        ClassIndex = Counter if TagValue.kind == KDefinitionKind else TagValue.index
        return ClassIndex, ObjectIndex, NameValue, NextIndex
    return 0, ObjectIndex, NameValue, NextIndex


# early entry is available only through the common checked archive segment walker
def FindEntry(BlobValue: bytes, Layouts: LayoutTable, StopClass: str) -> EntryStop:
    try:
        _ = Segment(
            BlobValue,
            4,
            Layouts,
            HeaderSize=0,
            MoVersion=KConfigGen,
            ResolveValue=Partial(ResolveSeedMut, StopClass),
        )
    except EntryStop as Entry:
        return Entry
    raise ArchiveError(f"No allocation reached for {StopClass}")
