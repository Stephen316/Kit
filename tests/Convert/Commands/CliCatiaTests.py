from json import dumps as DumpJson, loads as LoadJson
from pathlib import Path as FilePath

from pytest import mark as TestMark

from interchange.document.Models.DocumentModel import CadDocument
from tests.Convert.Commands.CliProcess import CliProcess


# retained native assembly payloads must remain decodable while conversion preserves existing files
@TestMark.parametrize("HasOutput", (False, True))
@TestMark.parametrize("IsExplicit", (False, True))
def CheckCatiaFile(HasOutput: bool, IsExplicit: bool, TmpPath: FilePath) -> None:
    Fixture = (
        FilePath(__file__).resolve().parents[3]
        / "re/catia/examples/.CATProduct/Tilton_Set.CATProduct"
    )
    Source = TmpPath / "isolated.CATProduct"
    Original = Fixture.read_bytes()
    _ = Source.write_bytes(Original)
    Target = TmpPath / "blocked.json"
    if HasOutput:
        _ = Target.write_bytes(b"existing output")
    Arguments = ("--from", "CATIA.V5", "--to", "INTERCHANGE.JSON") if IsExplicit else ()
    Result = CliProcess(
        TmpPath,
        "convert",
        str(Source),
        str(Target),
        *Arguments,
        "--overwrite",
        "--json",
    )
    assert Result.returncode == 1 and Result.stdout == ""
    assert "RetainedPayload" in LoadJson(Result.stderr)["message"]
    assert Source.read_bytes() == Original
    assert Target.exists() is HasOutput
    if HasOutput:
        assert Target.read_bytes() == b"existing output"
    Decoded = CliProcess(TmpPath, "decode", str(Source))
    assert Decoded.returncode == 0, Decoded.stderr
    Document = CadDocument.from_json(DumpJson(LoadJson(Decoded.stdout)["document"]))
    assert not Document.feature_timeline and Document.brep_payloads
    assert Document.assembly is not None and not Document.assembly.documents
    assert any(
        Diagnostic.code == "catia.product.component_sources_missing"
        for Diagnostic in Document.diagnostics
    )
