from dataclasses import replace as ChangeRecord
from io import BytesIO as ByteStream
from json import dumps as EncodeJson, loads as ParseJson
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import argv as Arguments, executable as PythonExe
from typing import cast as CastValue
from xml.etree.ElementTree import fromstring as ParseXml
from zipfile import ZipFile

from pytest import mark as MarkValue

from convert.adapters.base.UsabilityError import UsabilityError
from convert.api.ApiWrite import WriteDocument
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Enums.EnumFeatures import FeatureKind
from interchange.Features.FeatureStep import FeatureStep
from tests.Research.Archives.FreeCadReversedWriteTests import MakeInput

# public process cases must inspect the same writer source as the committed checkout
KRepoRoot = FilePath(__file__).resolve().parents[3]

# forward reverse implicit and symmetric controls retain independently editable extrusion histories
KCaseNames = (
    "explicit-positive",
    "explicit-reversed",
    "implicit-negative-reversed",
    "explicit-symmetric",
    "omitted-operation",
    "reference-create",
    "reference-omitted",
)


# reference dependencies and omitted operations must follow the admitted native extrusion contract
def MakeControl(CaseName: str) -> CadDocument:
    Document = MakeInput(
        CaseName
        if CaseName.startswith(("explicit", "implicit"))
        else "explicit-positive"
    )
    (Feature,) = Document.feature_timeline
    if CaseName in {"omitted-operation", "reference-omitted"}:
        Feature = ChangeRecord(Feature, operation=None)
    if not CaseName.startswith("reference"):
        return ChangeRecord(Document, feature_timeline=(Feature,))
    Reference = FeatureStep(
        "reference:profile",
        "Profile reference",
        FeatureKind.KReference,
        0,
        sketch_id=Feature.sketch_id,
        attributes={"native_type": "sketch"},
    )
    Feature = ChangeRecord(Feature, order=1, input_feature_ids=(Reference.id,))
    return ChangeRecord(Document, feature_timeline=(Reference, Feature))


# research emission preserves the archive without converting computed shape presence into measured native acceptance
def EmitResearch(Document: CadDocument) -> dict[str, object]:
    Output = ByteStream()
    Result = WriteDocument(
        Document, Output, DestFormat="freecad.fcstd", AllowCarrier=True
    )
    assert Result.bytes_written == len(Output.getvalue()) > 0
    assert not Result.application_usable and not Result.vendor_loadable
    assert Result.metadata["application_usable"] is False
    assert Result.metadata["vendor_loadable"] is False
    assert Result.metadata["recompute_required"] is True
    assert not Result.carrier_capabilities
    with ZipFile(ByteStream(Output.getvalue())) as Archive:
        RootValue = ParseXml(Archive.read("Document.xml"))
    NativeTypes = [
        NodeValue.get("type") for NodeValue in RootValue.findall("./Objects/Object")
    ]
    assert NativeTypes.count("Part::Extrusion") == 1
    assert not {
        "Part::Fuse",
        "Part::MultiFuse",
        "Part::Cut",
        "Part::Common",
    }.intersection(NativeTypes)
    return {
        "application_usable": Result.application_usable,
        "vendor_loadable": Result.vendor_loadable,
        "bytes_written": Result.bytes_written,
    }


# existing usability policy must refuse unqualified writes before committing any caller destination
def AssertRejected(Document: CadDocument, TargetData: FilePath | ByteStream) -> None:
    try:
        _ = WriteDocument(
            Document,
            TargetData,
            DestFormat="freecad.fcstd",
            AllowCarrier=False,
            Overwrite=True,
        )
    except UsabilityError as Problem:
        assert not Problem.IsAppUsable and not Problem.VendorLoadable
        assert {"application_unusable", "vendor_unloadable"} <= set(Problem.issues)
    else:
        raise AssertionError(
            "unqualified initial geometry must fail public usability policy"
        )


# both empty and existing streams and paths retain their exact prior state after refusal
def CheckTargets(Document: CadDocument, RootPath: FilePath) -> None:
    Existing = b"caller owned destination"
    for Content in (b"", Existing):
        Output = ByteStream(Content)
        AssertRejected(Document, Output)
        assert Output.getvalue() == Content and Output.tell() == 0
    AbsentPath = RootPath / "Absent.FCStd"
    AssertRejected(Document, AbsentPath)
    assert not AbsentPath.exists()
    ExistingPath = RootPath / "Existing.FCStd"
    assert ExistingPath.write_bytes(Existing) == len(Existing)
    AssertRejected(Document, ExistingPath)
    assert ExistingPath.read_bytes() == Existing
    assert set(RootPath.iterdir()) == {ExistingPath}


# every mode crosses the real neutral codec and public writer before policy observations are returned
def ObserveCase(CaseName: str, RootPath: FilePath) -> dict[str, object]:
    Document = CadDocument.from_json(MakeControl(CaseName).to_json(indent=None))
    Original = Document.to_json(indent=None)
    Report = EmitResearch(Document)
    CheckTargets(Document, RootPath)
    assert Document.to_json(indent=None) == Original
    return {**Report, "refusals": 4, "input_unchanged": True}


# independent processes distinguish public write policy from private adapter return values
@MarkValue.parametrize("CaseName", KCaseNames)
def CheckAttest(TmpPath: FilePath, CaseName: str) -> None:
    Process = RunProcess(
        [
            PythonExe,
            "-B",
            "-m",
            "tests.Research.Archives.FreeCadInitialGeometryAttestationTests",
            CaseName,
            str(TmpPath),
        ],
        cwd=KRepoRoot,
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )
    assert Process.returncode == 0, Process.stderr + Process.stdout
    Report = CastValue(dict[str, object], ParseJson(Process.stdout))
    assert Report["application_usable"] is False
    assert Report["vendor_loadable"] is False
    assert CastValue(int, Report["bytes_written"]) > 0
    assert Report["refusals"] == 4 and Report["input_unchanged"] is True


if __name__ == "__main__":
    print(EncodeJson(ObserveCase(Arguments[1], FilePath(Arguments[2])), sort_keys=True))
