from pathlib import Path as FilePath

from pytest import mark as TestMark

from tests.Convert.Commands.BuildIncomplete import BuildIncomplete
from tests.Convert.Commands.CheckJsonBlock import CheckJsonBlock
from tests.Convert.Commands.WrapDocument import WrapDocument


# resolved sources and nested placement graphs must not qualify assembly history or overwrite output
@TestMark.parametrize("RecordKind", ("ResolvedReference", "ProvenanceOnly"))
@TestMark.parametrize("OwnerName", ("", "root", "subassembly"))
@TestMark.parametrize("IsNested", (False, True))
@TestMark.parametrize("HasOutput", (False, True))
def CheckPlacement(
    RecordKind: str,
    OwnerName: str,
    IsNested: bool,
    HasOutput: bool,
    TmpPath: FilePath,
) -> None:
    Document = BuildIncomplete(RecordKind, OwnerName)
    assert Document.assembly is not None and Document.assembly.instances
    assert not Document.feature_timeline
    if IsNested:
        Document = WrapDocument(Document)
    CheckJsonBlock(Document, "UnqualifiedAssembly", HasOutput, TmpPath)
