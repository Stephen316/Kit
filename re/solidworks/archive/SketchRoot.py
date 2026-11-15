"""Build the typed map up to the first configuration sketch."""

from functools import partial as Partial
import json as Json
from pathlib import Path
from struct import unpack_from as Unpack

from convert.adapters.solidworks.container.Archive import (
    KClassRefKind,
    KDefinitionKind,
    KNullKind,
    KObjectRefKind,
    LayoutTable,
    ReadString,
    ReadTag,
    ResolveTagMut,
    Segment,
    Segmentation,
)

# configuration research starts from the part root witnessed on native map initialization
KRootClass = "moPart_c"

# the captured loader context limits the layouts to one model generation
KGeneration = 19000


# archive probes need to return the exact map before reading the next body
class EntryStop(Segmentation):
    # the normal layout walker reports intermediate progress on this deliberate boundary
    def __init__(SelfData, NameValue, Offset, Counter, Classes, Objects):
        super().__init__(NameValue, "lead", Offset, "research entry boundary")
        SelfData.Counter = Counter
        SelfData.Classes = Classes
        SelfData.Objects = Objects


# the research map requires exact ownership even below the ordinary archive base
def ResolveNative(
    StopClass,
    TagValue,
    Counter,
    BaseValue,
    Layouts,
    Frames,
    Classes,
    Objects,
    ParentName,
    ParentSlot,
    Offset,
):
    if Offset == 0:
        Require(
            (TagValue.kind, TagValue.class_name, TagValue.schema),
            (KDefinitionKind, KRootClass, 1),
            "native part root",
        )
        Classes[1] = KRootClass
        Objects.update({2: KRootClass, 3: "moExtObject_c"})
        return 1, 2, KRootClass, BaseValue
    if (
        (TagValue.kind == KClassRefKind and TagValue.index not in Classes)
        or (TagValue.kind == KObjectRefKind and TagValue.index not in Objects)
        or (TagValue.kind == KDefinitionKind and TagValue.schema != 1)
    ):
        raise Segmentation(
            ParentName, ParentSlot, Offset, "unsupported research archive tag"
        )
    Result = ResolveTagMut(
        TagValue,
        Counter,
        BaseValue,
        Layouts,
        Frames,
        Classes,
        Objects,
        ParentName,
        ParentSlot,
        Offset,
    )
    if Result[2] == StopClass and TagValue.kind in (KDefinitionKind, KClassRefKind):
        raise EntryStop(StopClass, Offset, Result[3], Classes, Objects)
    return Result


# the reader must reject unsupported branches at the first contradictory field
def Require(Value, Expected, FieldName):
    if Value != Expected:
        raise ValueError(f"{FieldName}: got {Value!r}, expected {Expected!r}")


# each phase needs its own map because later inline fields derive earlier layout runs
def FindEntry(BlobValue, Classes, StopClass):
    try:
        Segment(
            BlobValue,
            4,
            LayoutTable.FromMapping({"classes": Classes}),
            HeaderSize=0,
            MoVersion=KGeneration,
            ResolveValue=Partial(ResolveNative, StopClass),
        )
    except EntryStop as Entry:
        return Entry
    raise ValueError(f"No allocation reached for {StopClass}")


# the part stores modern inline fields between its transform and material objects
def FindMaterial(BlobValue, Cursor):
    Require(Unpack("<B", BlobValue, Cursor)[0], 1, "bounding box presence")
    Cursor += 81
    Fields = Unpack("<6I2dI", BlobValue, Cursor)
    Require(
        (Fields[1], Fields[5], Fields[-1]),
        (0, 0, 2),
        "root optional lists and record selector",
    )
    Cursor += 44
    Require(
        Unpack("<H2I", BlobValue, Cursor),
        (0, 0xAAAAAAAA, 0xBBBBBBBB),
        "empty inline alias map",
    )
    Cursor += 10
    Require(Unpack("<I", BlobValue, Cursor)[0], 0, "absent dynamic array")
    _, Shrink, Defeature, _ = Unpack("<4I", BlobValue, Cursor + 4)
    Require((Shrink, Defeature), (0, 0), "absent shrink wrap and defeature")
    Count, _, Notes = Unpack("<H2I", BlobValue, Cursor + 20)
    Require((Count, Notes), (0, 0), "empty inline objects and notes")
    Cursor += 78
    Imported, _, _, _, Count = Unpack("<5I", BlobValue, Cursor)
    Require(Imported, 0, "absent import metadata")
    Cursor += 20 + Count * 8
    Require(ReadTag(BlobValue, Cursor).kind, KNullKind, "absent publish cache")
    Require(
        ReadTag(BlobValue, Cursor + 2).class_name, "gcXhatch_c", "typed hatch boundary"
    )
    return Cursor


# the atom list uses inline scalar modes that the generic layout cannot infer
def AtomEnd(BlobValue, Cursor):
    Require(ReadTag(BlobValue, Cursor).kind, KNullKind, "absent atom name")
    _, Width = ReadString(BlobValue, Cursor + 18)
    Cursor += 18 + Width
    Require(Unpack("<i", BlobValue, Cursor)[0], 0, "absent atom child list")
    Require(
        ReadTag(BlobValue, Cursor + 4).kind, KNullKind, "absent atom visual properties"
    )
    Cursor += 6
    Require(
        Unpack("<Hi", BlobValue, Cursor), (0, 0), "empty atom node list and trailer"
    )
    Cursor += 6
    Require(Unpack("<i", BlobValue, Cursor + 20)[0], 0, "supported atom body mode")
    return Cursor + 52


# the ghost body manager contains bounded inline arrays before the relation pointer
def EndGhosts(BlobValue, Cursor):
    _, PackedCount = Unpack("<2I", BlobValue, Cursor)
    Cursor += 8
    Count = PackedCount & 0x0FFFFFFF
    Require(Count <= (len(BlobValue) - Cursor) // 28, True, "bounded ghost bodies")
    for _ in range(Count):
        Length = Unpack("<i", BlobValue, Cursor + 16)[0]
        Require(
            0 <= Length <= (len(BlobValue) - Cursor - 28) // 4,
            True,
            "bounded ghost body ids",
        )
        Cursor += 20 + 4 * Length
        Require(
            Unpack("<2i", BlobValue, Cursor), (0, 0), "absent ghost geometry and points"
        )
        Cursor += 8
    return Cursor


# split lengths independently check the body boundary and permit one shared object map
def FindRelations(BlobValue, ModelEntry):
    Cursor = ModelEntry.offset + ReadTag(BlobValue, ModelEntry.offset).size
    Require(ReadTag(BlobValue, Cursor).kind, KNullKind, "absent model scene")
    Cursor += 6
    Require(Unpack("<2i", BlobValue, Cursor), (0, 0), "empty body visualization groups")
    Count = Unpack("<I", BlobValue, Cursor + 24)[0]
    Split = Cursor + 28 + Count * 8
    RootBody = ReadTag(BlobValue, 0).size
    Require(
        Split, RootBody + 4 + Unpack("<I", BlobValue, RootBody)[0], "first split end"
    )
    Require(
        Split + 4 + Unpack("<I", BlobValue, Split)[0],
        len(BlobValue),
        "second split end",
    )
    Require(Unpack("<Hi", BlobValue, Split + 4), (0, 0), "empty root feature list")
    Require(Unpack("<i", BlobValue, Split + 14)[0], 2, "guarded atom count")
    FirstAtom = Split + 18
    FirstTag = ReadTag(BlobValue, FirstAtom)
    Require(
        (FirstTag.kind, FirstTag.class_name),
        (KDefinitionKind, "moAtom_c"),
        "typed first atom",
    )
    NextAtom = AtomEnd(BlobValue, FirstAtom + FirstTag.size)
    NextTag = ReadTag(BlobValue, NextAtom)
    Require(NextTag.kind, KClassRefKind, "typed second atom")
    AtomStop = AtomEnd(BlobValue, NextAtom + NextTag.size)
    Relation = EndGhosts(BlobValue, AtomStop + 4)
    Require(
        ReadTag(BlobValue, Relation).class_name, "moRelMgr_c", "typed relation manager"
    )
    return FirstAtom - Cursor, Relation - AtomStop


# the shared archive engine owns the root pointer traversal and all map allocations
def ReadSketchStart(BlobValue):
    LayoutPath = Path(__file__).with_suffix(".json")
    Stages = Json.loads(LayoutPath.read_text(encoding="utf-8"))
    Classes = Stages["prefix"]
    Root = Classes[KRootClass]
    Transform = FindEntry(BlobValue, Classes, "moTransRefPlaneData_c")
    TransformEnd = Transform.offset + ReadTag(BlobValue, Transform.offset).size + 24
    MaterialPos = FindMaterial(BlobValue, TransformEnd)
    Classes.update(Stages["material"])
    Root["child_slots"] += [
        "moMBD3DPDFPublishCacheData_c",
        "gcXhatch_c",
        "moMaterial_c",
        "uoModelData_c",
    ]
    Root["runs"].update({"5": MaterialPos - TransformEnd, "6": 0, "7": 0, "8": 0})
    Model = FindEntry(BlobValue, Classes, "uoModelData_c")
    AtomRun, RelationRun = FindRelations(BlobValue, Model)
    Classes.update(Stages["relations"])
    Root["child_slots"] += ["moAtom_c", "moAtom_c", "moRelMgr_c"]
    Root["runs"].update({"9": AtomRun, "10": 0, "11": RelationRun})
    return FindEntry(BlobValue, Classes, "sgSketch")
