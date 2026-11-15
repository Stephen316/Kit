"""Read modern inline environment folders and the ordinary saved light set."""

from functools import partial as Partial

from SketchRoot import Require
from SupportPlane import read_feature_base
from convert.adapters.solidworks.container.Archive import (
    KClassRefKind,
    KDefinitionKind,
    KNullKind,
    KObjectRefKind,
)


# the common feature reader advances this same archive cursor and reports each null
class ConfigFeature:
    def __init__(self, Cursor, ReadNull):
        self.cursor = Cursor
        self.blob = Cursor.BlobValue
        self.read = Cursor.ReadValue
        self.vector = Cursor.ReadPoint
        self.null = ReadNull

    @property
    def position(self):
        return self.cursor.Offset

    @position.setter
    def position(self, Offset):
        self.cursor.Offset = Offset


# the concept fields are shared by both named light nodes and unnamed managers
def ReadSceneConcept(Cursor, ReadNull, ExpectedFlags):
    State, Flags, _, Tail = Cursor.ReadValue("<iIii")
    Require((State, Flags, Tail), (0, ExpectedFlags, 0), "ordinary scene concept")
    Require(Cursor.ReadText(), "", "empty scene concept label")
    Require(Cursor.ReadCount(), 0, "empty lightweight scene child list")
    ReadNull()


# an ordinary light or manager finishes the concept with an empty child list
def ReadSceneFeature(Cursor, ReadNull, Flags):
    ReadSceneConcept(Cursor, ReadNull, Flags)
    Require(Cursor.ReadValue("<Hi"), (0, 0), "empty scene feature list and trailer")
    read_feature_base(ConfigFeature(Cursor, ReadNull))


# the saved light has a modern model feature base followed by four display settings
def ReadLight(Cursor, ReadPointer, ReadNull, Kind, Name):
    ReadPointer(Kind, Name)
    ReadPointer(KClassRefKind, "moNodeName_c")
    Cursor.ReadText()
    ReadSceneFeature(Cursor, ReadNull, 0xC0000000)
    Cursor.ReadValue("<i")  # moModelFeature_c
    Cursor.ReadValue("<3dI4i")
    Cursor.ReadText()
    Cursor.ReadValue("<3idid")
    Require(Cursor.ReadValue("<I"), (0,), "empty light user properties")
    if Name == "moDirectionLight_c":
        Cursor.ReadPoint(4)


# the folder owns the actual archive child list, followed by its inherited fields
def ReadEnvironment(Cursor, ReadPointer):
    ReadNull = Partial(ReadPointer, KNullKind)
    ReadPointer(KDefinitionKind, "moEnvFolder_c")
    ReadPointer(KClassRefKind, "moNodeName_c")
    Cursor.ReadText()
    ReadSceneConcept(Cursor, ReadNull, 0x40000000)
    Require(Cursor.ReadValue("<H"), (4,), "ordinary environment light count")
    ReadLight(Cursor, ReadPointer, ReadNull, KDefinitionKind, "moAmbientLight_c")
    for Kind in (KDefinitionKind, KClassRefKind, KClassRefKind):
        ReadLight(Cursor, ReadPointer, ReadNull, Kind, "moDirectionLight_c")
    Require(Cursor.ReadValue("<i"), (0,), "environment child list trailer")
    read_feature_base(ConfigFeature(Cursor, ReadNull))
    Cursor.ReadValue("<2i")  # moFolder_c


# the inline block settings must refer to their own allocated manager
def ReadSketchBlock(Cursor, ReadPointer):
    ReadNull = Partial(ReadPointer, KNullKind)
    Manager = ReadPointer(KDefinitionKind, "moSketchBlockMgr_c")
    ReadNull()  # moNodeName_c
    ReadSceneFeature(Cursor, ReadNull, 0x40000000)
    Cursor.ReadValue("<16s")  # archive GUID
    Cursor.ReadValue("<i")
    Require(
        ReadPointer(KObjectRefKind, "moSketchBlockMgr_c"),
        Manager,
        "block settings reference their own manager",
    )
    Require(Cursor.ReadCount(), 0, "empty sketch block table")
    Require(Cursor.ReadCount(), 0, "empty sketch block name table")


# the exploded view manager owns two nullable objects and an inline index
def ReadExplManager(Cursor, ReadPointer):
    ReadNull = Partial(ReadPointer, KNullKind)
    ReadPointer(KDefinitionKind, "moPrtExplViewManager_c")
    ReadNull()  # moNodeName_c
    ReadSceneFeature(Cursor, ReadNull, 0x40000000)
    ReadNull()  # suObArray
    ReadNull()  # selected view
    Cursor.ReadValue("<d2i")
    Require(Cursor.ReadValue("<H"), (0,), "empty exploded view word-to-object map")
