from pathlib import Path as FilePath

from pytest import mark as TestMark

from convert import open_document as OpenDocument
from convert.adapters.json.Adapter import JsonAdapter
from tests.convert.api.Fusion.AdapterCases import AdapterCase
from tests.convert.qualification.AssemblyCase import AssemblyCase
from tests.convert.qualification.RejectPublic import RejectPublic
from tests.convert.solidworks.core.NestedDocument import NestedDocument
from tests.interchange.fixtures.AssemblyFixture import BuildAssembly


# nested assemblies must retain unresolved placement and constraint refusals after interchange
@TestMark.parametrize("ModeValue", ("both", "status", "instance"))
@TestMark.parametrize("RelabelSource", (False, True))
@TestMark.parametrize("IsNested", (False, True))
def TestAsmGate(
    TmpPath: FilePath, ModeValue: str, RelabelSource: bool, IsNested: bool
) -> None:
    Document = AssemblyCase(ModeValue, RelabelSource)
    if IsNested:
        Document = NestedDocument(AdapterCase("rectangle"), Document)
    RejectPublic(Document, TmpPath)


# complete typed assembly controls keep the shared refusal boundary narrowly scoped
def TestTypedAsm(TmpPath: FilePath) -> None:
    Document = BuildAssembly()
    TargetPath = TmpPath / "Typed.json"
    _ = JsonAdapter().write(Document, TargetPath)
    assert OpenDocument(TargetPath).assembly == Document.assembly


# ordinary fusion records must remain eligible for interchange export without native blockers
def TestTypedFusion(TmpPath: FilePath) -> None:
    Document = AdapterCase("rectangle")
    TargetPath = TmpPath / "Typed.json"
    _ = JsonAdapter().write(Document, TargetPath)
    assert OpenDocument(TargetPath).feature_timeline == Document.feature_timeline
