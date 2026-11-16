from dataclasses import replace as ChangeRecord
from io import BytesIO as ByteStream
from json import dumps as EncodeJson, loads as ParseJson
from pathlib import Path as FilePath
from subprocess import run as RunProcess
import sys as System

from pytest import mark as MarkValue

from convert.api.ApiWrite import WriteDocument
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Enums.EnumValues import ParameterRole
from interchange.Features.FeatureExtrude import ExtrudeFeature
from interchange.Records.RecordParameter import ParameterValue

# authored readiness controls stay shared without importing research code into production modules
KRepoRoot = FilePath(__file__).resolve().parents[3]
System.path.insert(0, str(KRepoRoot / "re/automation"))

from FreeCadTwoLengthReadiness import (
    BuildCase,
    CASES as KReadinessCases,
    ObserveCase,
    ObserveNative,
    ReadinessCase,
)


# each malformed case isolates one end ownership invariant at the public write boundary
def ChangeBindings(ModeName: str) -> CadDocument:
    Document = BuildCase(KReadinessCases[0])
    Feature = Document.feature_timeline[0]
    Definition = Feature.definition
    assert isinstance(Definition, ExtrudeFeature)
    Forward, Reverse = Document.parameters
    if ModeName == "missing":
        Feature = ChangeRecord(Feature, attributes={})
    elif ModeName == "duplicate":
        Feature = ChangeRecord(
            Feature, attributes={"length_parameter_ids": (Forward.id, Forward.id)}
        )
    elif ModeName == "unknown":
        Feature = ChangeRecord(
            Feature, attributes={"length_parameter_ids": (Forward.id, "missing")}
        )
    elif ModeName == "owner":
        Forward = ChangeRecord(Forward, owner_id="missing")
    elif ModeName == "role":
        Forward = ChangeRecord(Forward, role=ParameterRole.KReference)
    elif ModeName == "stale":
        Forward = ChangeRecord(Forward, value=ChangeRecord(Forward.value, value=12.0))
    elif ModeName == "units":
        Forward = ChangeRecord(
            Forward, value=ChangeRecord(Forward.value, value=1.0, unit="in")
        )
        Feature = ChangeRecord(
            Feature,
            definition=ChangeRecord(
                Definition, length=ParameterValue(25.4, Forward.value.kind, "mm")
            ),
        )
    elif ModeName == "definition-units":
        Forward = ChangeRecord(Forward, value=ChangeRecord(Forward.value, value=25.4))
        Feature = ChangeRecord(
            Feature,
            definition=ChangeRecord(
                Definition, length=ParameterValue(1.0, Forward.value.kind, "in")
            ),
        )
    else:
        raise ValueError("unknown binding fixture mode")
    return ChangeRecord(
        Document, parameters=(Forward, Reverse), feature_timeline=(Feature,)
    )


# modified inputs cross the actual codec and writer before native expressions are inspected
def ObserveModified(ModeName: str) -> dict[str, object]:
    Document = ChangeBindings(ModeName)
    Document = CadDocument.from_json(Document.to_json(indent=None))
    Output = ByteStream()
    try:
        Result = WriteDocument(
            Document, Output, DestFormat="freecad.fcstd", AllowCarrier=False
        )
    except ValueError as Problem:
        assert not Output.getvalue()
        return {"status": "refused", "reason": str(Problem)}
    assert (
        Result.bytes_written == len(Output.getvalue())
        and not Result.carrier_capabilities
    )
    return {
        "status": "emitted",
        "native": ObserveNative(Output.getvalue(), ReadinessCase(ModeName, 25.4, 5.0)),
    }


# independent processes prevent in memory helper assertions from replacing the public conversion boundary
def RunBinding(ModeName: str) -> str:
    Process = RunProcess(
        [
            System.executable,
            "-B",
            "-m",
            "tests.Research.Archives.FreeCadTwoLengthBindingTests",
            ModeName,
        ],
        cwd=KRepoRoot,
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )
    assert Process.returncode == 0, Process.stderr + Process.stdout
    return Process.stdout


# equal lengths and roster permutations must retain both independent native driver expressions
def CheckEndOwners() -> None:
    Report = ParseJson(RunBinding("roster"))
    for NameText, Observation in Report.items():
        if NameText == "open-outline":
            assert Observation["status"] == "refused"
            continue
        assert Observation["status"] == "emitted"
        Native = Observation["native"]
        assert Native["missing_drivers"] == []
        assert Native["crossed_drivers"] == []
        assert Native["expressions"] == Native["expected_drivers"]


# equivalent physical lengths retain parameter units while native distance properties remain millimetres
@MarkValue.parametrize("ModeName", ("units", "definition-units"))
def CheckEndUnits(ModeName: str) -> None:
    Report = ParseJson(RunBinding(ModeName))
    assert Report["status"] == "emitted"
    Native = Report["native"]
    assert Native["length_fwd"] == 25.4 and Native["length_rev"] == 5.0
    assert Native["expressions"] == Native["expected_drivers"]
    CellValue = Native["spreadsheet_aliases"]["depth_forward"]
    NumberText, UnitText = CellValue.removeprefix("=").split()
    assert (float(NumberText), UnitText) == (
        (1.0, "in") if ModeName == "units" else (25.4, "mm")
    )


# invalid ownership cannot publish geometry with guessed or stale parametric dependencies
@MarkValue.parametrize(
    "ModeName", ("missing", "duplicate", "unknown", "owner", "role", "stale")
)
def CheckEndRefusal(ModeName: str) -> None:
    assert ParseJson(RunBinding(ModeName))["status"] == "refused"


if __name__ == "__main__":
    if System.argv[1] == "roster":
        print(EncodeJson({Case.Name: ObserveCase(Case) for Case in KReadinessCases}))
    else:
        print(EncodeJson(ObserveModified(System.argv[1])))
