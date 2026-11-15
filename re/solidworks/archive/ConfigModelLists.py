"""Read the modern model's saved display tables and nullable managers."""

from SketchRoot import Require
from convert.adapters.solidworks.container.Archive import (
    KClassRefKind,
    KDefinitionKind,
    KNullKind,
)


# absent child records have an archive count, even when the array is inline
def ReadDisplayLists(Cursor, ReadPointer):
    Cursor.ReadValue("<2i")
    for _ in range(Cursor.ReadCount()):
        Cursor.ReadValue("<i")  # first saved display key
    ReadPointer(KNullKind)  # moFlatPatternColorTab_c
    Cursor.ReadValue("<I")
    for _ in range(Cursor.ReadCount()):
        Cursor.ReadValue("<i")  # second saved display key
    for _ in range(8):
        Require(Cursor.ReadValue("<H"), (0,), "empty inline model array")
    ReadPointer(KNullKind)  # moLayerMgr_c
    Require(Cursor.ReadValue("<H"), (0,), "empty inline model object list")


# populated maps, solver state and print settings select bodies outside this layout
def ReadMarkerTail(Cursor):
    Cursor.ReadValue("<i")  # moPMarkRecord_c
    Cursor.ReadValue("<i")
    Require(Cursor.ReadCount(), 0, "empty model atom map")
    Require(Cursor.ReadValue("<i"), (0,), "absent model solver data")
    Require(Cursor.ReadCount(), 0, "empty model dimension map")
    Cursor.ReadValue("<i")
    Require(Cursor.ReadCount(), 0, "empty first dimension increment array")
    Cursor.ReadValue("<i")
    Require(Cursor.ReadCount(), 0, "empty second dimension increment array")
    Cursor.ReadValue("<2i")
    Require(Cursor.ReadValue("<i"), (0,), "absent 3D print settings")


# the list body and following two model names precede the typed thread manager
def ReadModelLists(Cursor, ReadPointer):
    ReadDisplayLists(Cursor, ReadPointer)
    ReadPointer(KDefinitionKind, "moPMarkRecord_c")
    ReadMarkerTail(Cursor)
    ReadPointer(KClassRefKind, "suObList")
    Require(Cursor.ReadValue("<H"), (0,), "empty saved model list")
    Cursor.ReadValue("<i")
    Cursor.ReadText()
    Cursor.ReadText()
    ReadPointer(KDefinitionKind, "moCThreadRefMgr_c")
    Require(Cursor.ReadCount(), 0, "empty cosmetic thread reference list")
    Cursor.ReadValue("<i")
    ReadPointer(KNullKind)  # moBendNoteFormat_c
