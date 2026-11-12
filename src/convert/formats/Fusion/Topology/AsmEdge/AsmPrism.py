from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.Topology.AsmEdge.AsmFields import (
    IsAsmFlag,
    ReadAsmInt,
    ReadAsmPtr,
    RequireAsm,
)
from convert.formats.Fusion.Topology.AsmEdge.AsmIdentity import CheckAsmIdent
from convert.formats.Fusion.Topology.AsmEdge.AsmNames import KNameTerms, ReadFaceName
from convert.formats.Fusion.Topology.AsmEdge.AsmRim import AsmUse, ReadAsmRim
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import AsmTable


# the initial planar body is indexed by exact face names and owned coedges
@MakeDataClass(frozen=True, slots=True)
class AsmPrism:
    Names: dict[KNameTerms, int]
    Rings: dict[int, tuple[AsmUse, ...]]


# a typed body handle must agree with the complete declared mapped root set
def ReadAsmBody(Table: AsmTable, BodyHandle: int, BodyHandles: frozenset[int]) -> int:
    Roots = Table.Records[1 : Table.RootCount]
    BodyIds = tuple(
        Index for Index, Value in enumerate(Roots, 1) if Value.Name == "body"
    )
    if (
        any(Value.Name not in ("body", "edge", "face") for Value in Roots)
        or len(BodyIds) != len(BodyHandles)
        or any(Value.Name == "body" for Value in Table.Records[Table.RootCount :])
    ):
        raise ValueError("Fusion ASM declared body table disagrees with native mapping")
    Mapped = {
        ReadAsmInt(RequireAsm(Table, Identity, "body", 6), 1): Identity
        for Identity in BodyIds
    }
    if Mapped.keys() != BodyHandles or BodyHandle not in Mapped:
        raise ValueError("Fusion ASM stored body handles disagree with native mapping")
    return Mapped[BodyHandle]


# one reciprocal lump and shell delimit a source body in its original component frame
def ReadAsmShell(
    Table: AsmTable, BodyId: int, *, AllowIdentity: bool = False
) -> tuple[int, int]:
    BodyValue = RequireAsm(Table, BodyId, "body", 6)
    LumpId = ReadAsmPtr(BodyValue, 3)
    LumpValue = RequireAsm(Table, LumpId, "lump", 6)
    ShellId = ReadAsmPtr(LumpValue, 4)
    Shell = RequireAsm(Table, ShellId, "shell", 8)
    if (
        any(ReadAsmPtr(BodyValue, Index) != -1 for Index in (2, 4))
        or (not AllowIdentity and ReadAsmPtr(BodyValue, 5) != -1)
        or ReadAsmPtr(LumpValue, 3) != -1
        or ReadAsmPtr(LumpValue, 5) != BodyId
        or any(ReadAsmPtr(Shell, Index) != -1 for Index in (3, 4, 6))
        or ReadAsmPtr(Shell, 7) != LumpId
    ):
        raise ValueError(
            "Fusion ASM source body is transformed or not one closed shell"
        )
    TransformId = ReadAsmPtr(BodyValue, 5)
    if TransformId != -1:
        CheckAsmIdent(Table, TransformId)
    return ShellId, ReadAsmPtr(Shell, 5)


# only live face owners in the selected prism can contribute generic names
def ReadAsmPrism(
    Table: AsmTable, BodyId: int, Sides: int, *, AllowIdentity: bool = False
) -> AsmPrism:
    ShellId, Current = ReadAsmShell(Table, BodyId, AllowIdentity=AllowIdentity)
    Names: dict[KNameTerms, int] = {}
    Rings: dict[int, tuple[AsmUse, ...]] = {}
    for _ in range(Sides + 2):
        FaceValue = RequireAsm(Table, Current, "face", 10)
        if (
            Current in Rings
            or ReadAsmPtr(FaceValue, 5) != ShellId
            or ReadAsmPtr(FaceValue, 6) != -1
            or IsAsmFlag(FaceValue, 9)
        ):
            raise ValueError("Fusion ASM prism face is not owned by its shell")
        _ = RequireAsm(Table, ReadAsmPtr(FaceValue, 7), "plane-surface")
        NameValue = ReadFaceName(Table, Current, FaceValue)
        if NameValue in Names:
            raise ValueError("Fusion ASM prism face names are ambiguous")
        Names[NameValue] = Current
        Rings[Current] = ReadAsmRim(
            Table, Current, ReadAsmPtr(FaceValue, 4), max(Sides, 4)
        )
        Current = ReadAsmPtr(FaceValue, 3)
    if Current != -1:
        raise ValueError("Fusion ASM prism has extra or cyclic source faces")
    return AsmPrism(Names, Rings)
