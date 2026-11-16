from convert.adapters.solidworks.Container.Archive import (
    KClassRefKind,
    ArchiveError,
    ReadTag,
)
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.ArchiveCursor import ArchiveCursor
from convert.adapters.solidworks.Resolved.Cut.CutResultFace import (
    KCutSelectors,
    CutResultId,
)
from convert.adapters.solidworks.Resolved.FaceIdentity import (
    KCapClass,
    KEdgeClass,
    KSurfaceId,
    ReadSurfaceId,
)


# prior body and cut surfaces use the same reference base but keep distinct selectors
def ReadScopeSurface(Cursor: ArchiveCursor) -> KSurfaceId | CutResultId:
    TagValue = ReadTag(Cursor.BlobValue, Cursor.Offset)
    RequireArch(TagValue.kind, KClassRefKind, "reached scope surface class reference")
    ClassName = Cursor.Classes.get(TagValue.index)
    if ClassName is None:
        raise ArchiveError("unreached scope surface class")
    Selectors = KCutSelectors.get(ClassName)
    RequireArch(
        ClassName in (KCapClass, KEdgeClass) or Selectors is not None,
        True,
        "witnessed scope surface class",
    )
    Surface = ReadSurfaceId(Cursor, ClassName, IsCap=ClassName == KCapClass)
    if Selectors is None:
        return Surface
    First, Second = Cursor.ReadInts("<2i")
    RequireArch((First, Second), Selectors, "witnessed scope surface selectors")
    return {**Surface, "end": Cursor.Offset, "extra_fields": (First, Second)}
