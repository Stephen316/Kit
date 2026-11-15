from json import loads as LoadJson
from pathlib import Path as FilePath

from pytest import mark as TestMark

from tests.convert.Commands.BuildInactive import BuildInactive
from tests.convert.Commands.CheckJsonBlock import CheckJsonBlock
from tests.convert.Commands.CliProcess import CliProcess
from tests.convert.Commands.WrapDocument import WrapDocument


# suppressed final features and dependencies must not qualify retained body geometry
@TestMark.parametrize(
    "RecordKind",
    (
        "Final",
        "ConfigState",
        "ConfigRecord",
        "Dependency",
        "ConfigDependency",
        "ConfigRecordDependency",
        "Transitive",
    ),
)
@TestMark.parametrize("IsNested", (False, True))
@TestMark.parametrize("HasOutput", (False, True))
def CheckInactive(
    RecordKind: str, IsNested: bool, HasOutput: bool, TmpPath: FilePath
) -> None:
    Document = BuildInactive(RecordKind)
    assert Document.bodies and Document.brep is not None
    assert Document.feature_timeline[-1].definition is not None
    if IsNested:
        Document = WrapDocument(Document)
    CheckJsonBlock(Document, "IncompleteFeature", HasOutput, TmpPath)


# active references need qualified sketch geometry while supported execution ordering remains stable
@TestMark.parametrize("RecordKind", ("InactiveReference", "Unordered"))
@TestMark.parametrize("IsNested", (False, True))
def CheckActive(RecordKind: str, IsNested: bool, TmpPath: FilePath) -> None:
    Document = BuildInactive(RecordKind)
    Document.AssertValid()
    if RecordKind == "InactiveReference":
        assert not Document.bodies and Document.brep is None
        assert any(Feature.suppressed for Feature in Document.feature_timeline)
        if IsNested:
            Document = WrapDocument(Document)
        CheckJsonBlock(Document, "UnqualifiedGeometry", False, TmpPath)
        return
    else:
        assert Document.feature_timeline[0].order > Document.feature_timeline[-1].order
    if IsNested:
        Document = WrapDocument(Document)
        CheckJsonBlock(Document, "UnqualifiedAssembly", False, TmpPath)
        return
    Source = TmpPath / "source.json"
    Original = Document.to_json()
    _ = Source.write_text(Original, encoding="utf-8")
    Target = TmpPath / "active.json"
    Result = CliProcess(TmpPath, "convert", str(Source), str(Target), "--json")
    assert Result.returncode == 0, Result.stderr
    assert LoadJson(Target.read_text(encoding="utf-8")) == LoadJson(Original)
    assert Source.read_text(encoding="utf-8") == Original
