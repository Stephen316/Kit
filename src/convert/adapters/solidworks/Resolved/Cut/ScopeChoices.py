from convert.adapters.solidworks.Container.Archive import KClassRefKind
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.ArchiveCursor import ArchiveCursor
from convert.adapters.solidworks.Resolved.BossChooser import CheckChoiceOwn
from convert.adapters.solidworks.Resolved.BossEntry import OpNode
from convert.adapters.solidworks.Resolved.Cut.CutChooser import KCutClass
from convert.adapters.solidworks.Resolved.Cut.ScopeSurfaces import ReadSurface
from convert.adapters.solidworks.Resolved.Cut.ScopeTypes import (
    ScopeChoice,
    ScopeChoiceFace,
    ScopeOwner,
)
from convert.adapters.solidworks.Resolved.FaceIdentity import (
    ReadFaceHead,
    ReadFaceReturn,
)


# chooser face references survive even when a saved cut excludes their earlier body
def ReadScopeFace(Cursor: ArchiveCursor) -> ScopeChoiceFace:
    FaceInfo, Count = ReadFaceHead(Cursor, KClassRefKind, 768)
    Surfaces = [ReadSurface(Cursor) for _ in range(Count + 1)]
    ReadFaceReturn(Cursor)
    return {**FaceInfo, "surfaces": Surfaces, "end": Cursor.Offset}


# the earlier chooser centre binds this record independently of its raw activation fields
def ReadScopeCentre(
    Cursor: ArchiveCursor, Owner: ScopeOwner
) -> tuple[int, tuple[float, ...], tuple[int, ...]]:
    RequireArch(
        Cursor.ReadInts("<2H"), (0, 1), "empty secondary chooser and one scope centre"
    )
    _, _, CentreObject = Cursor.TakePointer(
        ("moBBoxCenterData_c",), KClassRefKind, CompactOnly=True
    )
    RequireArch(Cursor.ReadInts("<i"), (1,), "witnessed scope bounding centre type")
    Centre = Cursor.ReadPoint(4)
    RequireArch(
        Centre, Owner.CentreAndScale, "scope chooser agrees with earlier boss centre"
    )
    State = Cursor.ReadInts("<2iH")
    RequireArch(
        State in ((0, 0, 0), (0, 1, 0)), True, "witnessed scope chooser centre state"
    )
    RequireArch(Cursor.ReadInts("<i"), (0,), "guarded scope chooser return")
    return CentreObject, Centre, State


# both choices retain raw face state along with their resolved earlier body identity
def ReadScopeChoice(Cursor: ArchiveCursor, Owner: ScopeOwner) -> ScopeChoice:
    Offset = Cursor.Offset
    _, _, ObjectIndex = Cursor.TakePointer(
        ("moPerBodyChooserData_c",), KClassRefKind, CompactOnly=True
    )
    RequireArch(Cursor.ReadInts("<H"), (2,), "two saved scope chooser faces")
    Faces = ReadScopeFace(Cursor), ReadScopeFace(Cursor)
    CentreObject, Centre, State = ReadScopeCentre(Cursor, Owner)
    return {
        "offset": Offset,
        "end": Cursor.Offset,
        "object_index": ObjectIndex,
        "earlier_body_id": Owner.BodyId,
        "faces": Faces,
        "centre_object": CentreObject,
        "centre_and_scale": Centre,
        "raw_centre_state": State,
    }


# both witnesses must close with references to the same reached cut before later fields
def ReadChooserPair(
    Cursor: ArchiveCursor, Owners: tuple[ScopeOwner, ScopeOwner], CutValue: OpNode
) -> tuple[ScopeChoice, ScopeChoice]:
    RequireArch(Cursor.ReadInts("<2H"), (1, 2), "two primary scope chooser entries")
    First = ReadScopeChoice(Cursor, Owners[0])
    Second = ReadScopeChoice(Cursor, Owners[1])
    CheckChoiceOwn(Cursor, CutValue, KCutClass)
    RequireArch(Cursor.ReadInts("<3H"), (1, 1, 0), "empty secondary scope chooser")
    CheckChoiceOwn(Cursor, CutValue, KCutClass)
    RequireArch(Cursor.ReadInts("<iH"), (0, 0), "empty repeated scope chooser")
    return First, Second
