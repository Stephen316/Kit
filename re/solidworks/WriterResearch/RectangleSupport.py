from struct import pack as PackFields

from LocalComponent import CheckLocalComponent, WriteLocalComponent
from PartArchive import PartArchiveWriter
from PrincipalPlaneView import KPrincipalFrames
from ResolvedOrigin import KPlaneRef
from ResolvedPrincipal import KUnitPose
from convert.adapters.solidworks.Container.Archive import EncodeNull
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch

# The optional body chain enters through an object definition in this profile.
KChainClass = "moSketchChain_c"
KChainFields = (6, -1, 0, 0, 5, 5)
KProfileAxes = {2: 3, 4: 1}


# The body-bearing profile owns a chain over its generated sketch edge IDs.
def WriteProfileChain(
    Writer: PartArchiveWriter, Perimeter: tuple[int, ...] | None
) -> None:
    if Perimeter is not None:
        RequireArch(
            len(Perimeter) == len(set(Perimeter)) == 4
            and all(type(Edge) is int and 0 < Edge <= 0xFFFFFFFF for Edge in Perimeter),
            True,
            "four distinct local chain edges",
        )
        RequireArch(KChainClass in Writer.classes, False, "first profile chain")
    Count = int(Perimeter is not None)
    Writer.raw(PackFields("<Ii", Count, Count))
    if Perimeter is None:
        return
    Writer.BeginObject(KChainClass, 1)
    Writer.raw(PackFields("<H4IHI6i", 4, *Perimeter, 1, 0, *KChainFields))
    Writer.string("")
    Writer.raw(PackFields("<H2I", 0, 0xFFFFFFFF, 0))
    Writer.raw(EncodeNull())
    Writer.raw(EncodeNull())
    Writer.raw(PackFields("<3i", 0, 0, 0))


# The inherited plane reference binds the real part alias to a generated principal datum.
def WriteProfileSupport(
    Writer: PartArchiveWriter,
    Generation: int,
    PartObject: int,
    DatumId: int,
    DatumTime: int,
) -> None:
    CheckLocalComponent(Writer, Generation, PartObject)
    RequireArch(DatumId in KProfileAxes, True, "ordinary rectangle support datum")
    RequireArch(
        type(DatumTime) is int and 0 <= DatumTime <= 0xFFFFFFFF,
        True,
        "local datum reference timestamp",
    )
    RequireArch(KPlaneRef in Writer.classes, True, "inherited principal support class")
    Frame = KPrincipalFrames[DatumId - 2]
    Writer.raw(PackFields("<iBiH2IH", 3, 1, 0, 0, 0, 100000, 0))
    Writer.raw(EncodeNull())
    Writer.BeginObject(KPlaneRef, 1)
    WriteLocalComponent(Writer, Generation, PartObject)
    Writer.raw(PackFields("<iI", DatumId, DatumTime))
    Writer.raw(EncodeNull())
    Writer.raw(PackFields("<iB", KProfileAxes[DatumId], int(Frame.Basis is not None)))
    if Frame.Basis is not None:
        Writer.raw(PackFields("<9d", *Frame.Basis))
    Writer.raw(PackFields("<4dB", *KUnitPose, 0))
