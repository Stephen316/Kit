"""Read the ordinary model presentation suffix through the Config-0 return."""

from functools import partial as Partial

from ConfigAnnoData import ReadFinishData, ReadNoteData, ReadWeldData
from ConfigAnnot import ReadAnnotDefs
from ConfigDetail import (
    KStyleTails,
    ReadDetailStart,
    ReadLengthCode,
    ReadStyleHead,
    ReadStyleTail,
)
from ConfigDetailEnd import ReadDetailEnd
from ConfigLabel import ReadLabelDefs
from ConfigModelLists import ReadModelLists
from ConfigRegions import ReadModelRegions, ReadPartReturn
from ConfigScene import ReadEnvironment, ReadExplManager, ReadSketchBlock
from ConfigTable import ReadTableDefs
from ConfigTol import ReadTolData
from SketchRoot import Require
from convert.adapters.solidworks.container.Archive import (
    KClassRefKind,
    KDefinitionKind,
    KNullKind,
    ReadTag,
)


# capture the order and counter that native ReadObject observes before each token
def ReadPointer(Cursor, Events, KindValue, NameValue=None, SchemaValue=1):
    Offset, Counter = Cursor.Offset, Cursor.NextIndex
    TagValue, _, Index = Cursor.TakePointer((NameValue,), KindValue, SchemaValue)
    Events.append((Offset, Counter, TagValue.kind, NameValue, Index))
    return Index


# the presence byte selects the nine-double matrix before the translation and scale
def ReadViewXform(Cursor):
    (MatrixFlag,) = Cursor.ReadValue("<B")
    Require(MatrixFlag in (0, 1), True, "view transform matrix flag")
    if MatrixFlag:
        Cursor.ReadPoint(9)
    Cursor.ReadPoint(4)
    Require(Cursor.ReadValue("<B"), (0,), "view transform extension mode")


# the three optional view collections have no entries on the witnessed path
def ReadConfigView(Cursor):
    Name = Cursor.ReadText()
    for _ in range(2):
        ReadViewXform(Cursor)
    Cursor.ReadValue("<Hi")
    Cursor.ReadPoint(1)
    Require(Cursor.ReadCount(), 0, "empty view pointer array")
    Cursor.ReadValue("<2i")
    Require(Cursor.ReadCount(), 0, "empty first view list")
    Cursor.ReadValue("<i")
    Cursor.ReadPoint(1)
    Require(Cursor.ReadCount(), 0, "empty second view list")
    Cursor.ReadValue("<2i")
    return Name


# the style selects an absent or inline dual unit from the actual archive tag
def ReadLengthLink(Cursor, Events):
    if ReadTag(Cursor.BlobValue, Cursor.Offset).kind == KNullKind:
        ReadPointer(Cursor, Events, KNullKind)
        return
    ReadPointer(Cursor, Events, KClassRefKind, "moLengthUserUnits_c")
    ReadLengthCode(Cursor)
    ReadPointer(Cursor, Events, KNullKind)


# the annotation subtype reads its inline view base before its nullable references
def ReadAnnotationView(Cursor, Events, NameValues):
    Require(ReadConfigView(Cursor) in NameValues, True, "witnessed annotation view name")
    Cursor.ReadValue("<i")
    ReadPointer(Cursor, Events, KNullKind)  # moCompRef_c
    ReadPointer(Cursor, Events, KNullKind)  # first moRefWrapper_c
    Cursor.ReadValue("<id")
    ReadPointer(Cursor, Events, KNullKind)  # second moRefWrapper_c
    Cursor.ReadValue("<2i")
    ReadPointer(Cursor, Events, KNullKind)  # moFeatComment_c
    Cursor.ReadValue("<4i")


# the same model serializer stores the presentation records after either relation path
def ReadModelPresentation(Cursor):
    Events = []
    ReadDetailStart(Cursor)
    for Format in KStyleTails:
        ReadStyleHead(Cursor)
        ReadLengthCode(Cursor)
        ReadLengthLink(Cursor, Events)
        ReadStyleTail(Cursor, Format)
    ReadAnnotDefs(Cursor)
    ReadTableDefs(Cursor)
    ReadLabelDefs(Cursor)
    ReadFinishData(Cursor)
    ReadNoteData(Cursor)
    ReadWeldData(Cursor)
    ReadTolData(Cursor, Partial(ReadPointer, Cursor, Events, KNullKind))
    ReadDetailEnd(Cursor)
    Require(Cursor.ReadValue("<H"), (0,), "empty shared parameter array")
    ReadEnvironment(Cursor, Partial(ReadPointer, Cursor, Events))
    ReadPointer(Cursor, Events, KNullKind)
    ListKind = KClassRefKind if "suObList" in Cursor.Classes.values() else KDefinitionKind
    ReadPointer(Cursor, Events, ListKind, "suObList")
    Require(Cursor.ReadValue("<H"), (0,), "empty leading view list")
    ReadPointer(Cursor, Events, KDefinitionKind, "moView_c")
    ReadConfigView(Cursor)
    for _ in range(9):
        ReadPointer(Cursor, Events, KClassRefKind, "moView_c")
        ReadConfigView(Cursor)
    Cursor.ReadValue("<B2i")
    ReadPointer(Cursor, Events, KDefinitionKind, "moFeatColorTab_c", 0)
    Require(Cursor.ReadCount(), 0, "empty feature color table")
    ReadPointer(Cursor, Events, KNullKind)
    Cursor.ReadValue("<i")
    Require(Cursor.ReadCount(), 0, "absent inline model node list")
    Cursor.ReadValue("<i")
    ReadSketchBlock(Cursor, Partial(ReadPointer, Cursor, Events))
    ReadPointer(Cursor, Events, KClassRefKind, "suObList")
    (AnnotationCount,) = Cursor.ReadValue("<H")
    Require(AnnotationCount in (1, 2), True, "witnessed annotation view count")
    ReadPointer(Cursor, Events, KDefinitionKind, "moAnnotationView_c")
    ReadAnnotationView(Cursor, Events, ("*Front", "*Right"))
    if AnnotationCount == 2:
        ReadPointer(Cursor, Events, KClassRefKind, "moAnnotationView_c")
        ReadAnnotationView(Cursor, Events, ("*Top",))
    ReadModelLists(Cursor, Partial(ReadPointer, Cursor, Events))
    Regions = ReadModelRegions(Cursor)
    ReadExplManager(Cursor, Partial(ReadPointer, Cursor, Events))
    ReadPartReturn(Cursor)
    Require(Cursor.Offset, len(Cursor.BlobValue), "complete witnessed Config-0 extent")
    return Events, Regions
