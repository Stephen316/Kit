from typing import TypedDict

from convert.adapters.solidworks.container.Archive import KClassRefKind
from convert.adapters.solidworks.container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.container.ArchiveCursor import ArchiveCursor
from convert.adapters.solidworks.resolved.BossChooser import (
    CheckChoiceOwn,
    ChooserCentre,
    ReadChoiceTail,
)
from convert.adapters.solidworks.resolved.BossEntry import BossHead, OpNode
from convert.adapters.solidworks.resolved.cut.CutResultFace import (
    CutResultAlias,
    CutResultFace,
    ReadResultAlias,
    ReadResultFace,
)

# the ordinary subtract operation owns both saved chooser groups
KCutClass = "moICE_c"


# the two result assemblies retain actual face identities and the chooser centre
class CutChoices(TypedDict):
    primary_object: int
    repeated_object: int
    faces: list[CutResultFace]
    face_aliases: list[CutResultAlias]
    centre: ChooserCentre
    repeated_centre_object: int
    end: int


# cut result choosers keep ownership references and guard their two face arrays
def ReadCutChoices(
    Cursor: ArchiveCursor, BossValue: BossHead, CutValue: OpNode
) -> CutChoices:
    RequireArch(Cursor.ReadInts("<i2H"), (1, 1, 1), "one first cut chooser item")
    _, _, First = Cursor.TakePointer(
        ("moPerBodyChooserData_c",), KClassRefKind, CompactOnly=True
    )
    RequireArch(Cursor.ReadInts("<H"), (2,), "two cut chooser faces")
    Faces = [ReadResultFace(Cursor, BossValue, CutValue, 768) for _ in range(2)]
    Clocks = {
        Entity["time_word"]
        for FaceValue in Faces
        for Entity in FaceValue["entities"]
        if Entity["feature_id"] == CutValue["native_feature_id"]
    }
    RequireArch(len(Clocks), 1, "same authored cut result timestamp")
    Bounds = ReadChoiceTail(Cursor, KClassRefKind, ())
    CheckChoiceOwn(Cursor, CutValue, KCutClass)
    RequireArch(Cursor.ReadInts("<3H"), (1, 1, 0), "witnessed empty second cut chooser")
    CheckChoiceOwn(Cursor, CutValue, KCutClass)
    RequireArch(Cursor.ReadInts("<i2H"), (1, 1, 1), "one repeated cut chooser item")
    _, _, Repeat = Cursor.TakePointer(
        ("moPerBodyChooserData_c",), KClassRefKind, CompactOnly=True
    )
    RequireArch(Cursor.ReadInts("<H"), (2,), "two repeated cut chooser faces")
    Aliases = [ReadResultAlias(Cursor, FaceValue) for FaceValue in Faces]
    Current = ReadChoiceTail(Cursor, KClassRefKind, ())
    RequireArch(
        Current["centre_and_scale"],
        Bounds["centre_and_scale"],
        "same cut chooser centre",
    )
    CheckChoiceOwn(Cursor, CutValue, KCutClass)
    return {
        "primary_object": First,
        "repeated_object": Repeat,
        "faces": Faces,
        "face_aliases": Aliases,
        "centre": Bounds,
        "repeated_centre_object": Current["centre_object"],
        "end": Cursor.Offset,
    }
