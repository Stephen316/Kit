from collections.abc import Mapping, Sequence
from hashlib import sha256 as DigestBytes
from io import BytesIO as ByteStream
from json import dumps as EncodeJson, loads as ParseJson
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import argv as Arguments, executable as PythonExe
from typing import cast as CastValue
from xml.etree import ElementTree as XmlTree
from zipfile import ZipFile

from pytest import mark as MarkValue

from convert.api.ApiOpen import OpenDocument
from convert.api.ApiWrite import WriteDocument
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Enums.EnumValues import ValueKind
from tests.Research.Archives.FreeCadNativeEndTests import MakeNative

# independent child reads and exact replay must use the same committed implementation
KRepoRoot = FilePath(__file__).resolve().parents[4]

# each source mutation crosses the actual native archive reader rather than calling alias helpers
KCases = (
    "literal",
    "leading-reference",
    "edited",
    "equal-reordered",
    "unknown-alias",
    "label-ref",
    "arithmetic",
    "formula",
    "unknown-unit",
    "big-exponent",
    "underflow",
    "stale",
    "duplicate-alias",
    "duplicate-address",
    "wrong-count",
    "cell-limit",
    "external-links",
    "duplicate-links",
    "unknown-child",
    "placeholder",
    "nonfinite-scalar",
    "invalid-scalar",
    "missing-scalar",
)


# source cells choose their own units aliases and addresses independently from native property owners
def MakeCells(CaseName: str) -> list[dict[str, str]]:
    Forward = {
        "edited": "=1.4 cm",
        "equal-reordered": "=7 mm",
        "stale": "=12 mm",
        "formula": "=forward + 1 mm",
        "unknown-unit": "=11 parsec",
        "big-exponent": "=1e999999 mm",
        "underflow": "=1e-999 mm",
    }.get(CaseName, "=1.1 cm")
    Cells = [
        {"address": "B1", "alias": "forward", "content": Forward},
        {
            "address": "B2",
            "alias": "reverse",
            "content": "=7 mm" if CaseName == "equal-reordered" else "5 mm",
        },
        {"address": "B3", "alias": "factor", "content": "=2.5"},
    ]
    if CaseName == "placeholder":
        Cells.append({"address": "B4", "alias": "zero", "content": "0"})
    if CaseName in {"nonfinite-scalar", "invalid-scalar", "missing-scalar"}:
        Cells[2]["content"] = "0"
    if CaseName == "duplicate-alias":
        Cells[1]["alias"] = "forward"
    if CaseName == "duplicate-address":
        Cells[1]["address"] = "B1"
    if CaseName == "cell-limit":
        Cells.extend(
            {"address": f"C{Index}", "content": "0"} for Index in range(1, 4095)
        )
    return list(reversed(Cells)) if CaseName == "equal-reordered" else Cells


# a sheet label and bogus kit alias metadata must never override actual object qualified ownership
def AddSheetMut(RootValue: XmlTree.Element, CaseName: str) -> None:
    Objects = RootValue.find("./Objects")
    ObjectData = RootValue.find("./ObjectData")
    assert Objects is not None and ObjectData is not None
    _ = XmlTree.SubElement(
        Objects,
        "Object",
        {"type": "Spreadsheet::Sheet", "name": "Dimensions", "id": "2"},
    )
    Sheet = XmlTree.SubElement(ObjectData, "Object", {"name": "Dimensions"})
    Props = XmlTree.SubElement(Sheet, "Properties", {"Count": "2"})
    Label = XmlTree.SubElement(
        Props, "Property", {"name": "Label", "type": "App::PropertyString"}
    )
    _ = XmlTree.SubElement(Label, "String", {"value": "DisplaySheet"})
    Property = XmlTree.SubElement(
        Props, "Property", {"name": "cells", "type": "Spreadsheet::PropertySheet"}
    )
    CellRows = MakeCells(CaseName)
    Cells = XmlTree.SubElement(
        Property,
        "Cells",
        {"Count": str(len(CellRows) + (CaseName == "wrong-count")), "xlink": "1"},
    )
    Links = XmlTree.SubElement(
        Cells, "XLinks", {"count": "1" if CaseName == "external-links" else "0"}
    )
    if CaseName == "external-links":
        _ = XmlTree.SubElement(Links, "XLink", {"file": "Other.FCStd", "name": "Other"})
    if CaseName == "duplicate-links":
        _ = XmlTree.SubElement(Cells, "XLinks", {"count": "0"})
    if CaseName == "unknown-child":
        _ = XmlTree.SubElement(Cells, "UnresolvedNativeRecord", {"value": "preserved"})
    for Attributes in CellRows:
        _ = XmlTree.SubElement(Cells, "Cell", Attributes)
    Objects.set("Count", str(len(Objects)))
    ObjectData.set("Count", str(len(ObjectData)))


# independent saved property values let alias edits be corroborated or explicitly diagnosed as stale
def AddExprMut(RootValue: XmlTree.Element, CaseName: str) -> None:
    Props = RootValue.find("./ObjectData/Object[@name='Extrusion']/Properties")
    assert Props is not None
    Factor = XmlTree.SubElement(
        Props, "Property", {"name": "Factor", "type": "App::PropertyFloat"}
    )
    _ = XmlTree.SubElement(Factor, "Float", {"value": "2.5"})
    Decoy = XmlTree.SubElement(
        Props,
        "Property",
        {"name": "ParameterAliasesJSON", "type": "App::PropertyString"},
    )
    _ = XmlTree.SubElement(Decoy, "String", {"value": '{"forward":"reverse"}'})
    Property = XmlTree.SubElement(
        Props,
        "Property",
        {"name": "ExpressionEngine", "type": "App::PropertyExpressionEngine"},
    )
    Engine = XmlTree.SubElement(Property, "ExpressionEngine", {"count": "3"})
    Source = {
        "unknown-alias": "Dimensions.absent",
        "label-ref": "DisplaySheet.forward",
        "arithmetic": "Dimensions.forward + 1 mm",
        "leading-reference": "= Dimensions.forward",
    }.get(CaseName, "Dimensions.forward")
    for FieldName, Expression in (
        ("LengthFwd", Source),
        ("LengthRev", "Dimensions.reverse"),
        ("Factor", "Dimensions.factor"),
    ):
        _ = XmlTree.SubElement(
            Engine, "Expression", {"path": FieldName, "expression": Expression}
        )
    Props.set("Count", str(len(Props)))


# every fixture is independently authored native xml with neither neutral manifest representation
def MakeFixture(CaseName: str) -> bytes:
    Forward = (
        14.0 if CaseName == "edited" else 7.0 if CaseName == "equal-reordered" else 11.0
    )
    Reverse = 7.0 if CaseName == "equal-reordered" else 5.0
    with ZipFile(ByteStream(MakeNative(Forward, Reverse, False, False))) as Archive:
        RootValue = XmlTree.fromstring(Archive.read("Document.xml"))
    AddSheetMut(RootValue, CaseName)
    AddExprMut(RootValue, CaseName)
    AddEvidenceMut(RootValue, CaseName)
    assert not any(
        NodeValue.get("name", "").startswith("KitManifest")
        for NodeValue in RootValue.iter()
    )
    Output = ByteStream()
    with ZipFile(Output, "w") as Archive:
        Archive.writestr("Document.xml", XmlTree.tostring(RootValue, encoding="utf-8"))
    return Output.getvalue()


# unconsumed paths and permissively normalized scalars retain their actual independent persisted evidence
def AddEvidenceMut(RootValue: XmlTree.Element, CaseName: str) -> None:
    Props = RootValue.find("./ObjectData/Object[@name='Extrusion']/Properties")
    assert Props is not None
    Scalar = Props.find("./Property[@name='Factor']/Float")
    assert Scalar is not None
    if CaseName == "nonfinite-scalar":
        Scalar.set("value", "nan")
    if CaseName == "invalid-scalar":
        Scalar.set("value", "invalid")
    if CaseName == "missing-scalar":
        del Scalar.attrib["value"]
    if CaseName == "placeholder":
        Placement = XmlTree.SubElement(
            Props, "Property", {"name": "Placement", "type": "App::PropertyPlacement"}
        )
        _ = XmlTree.SubElement(
            Placement,
            "PropertyPlacement",
            {
                "Px": "17",
                "Py": "0",
                "Pz": "0",
                "Q0": "0",
                "Q1": "0",
                "Q2": "0",
                "Q3": "1",
            },
        )
        Engine = Props.find("./Property[@name='ExpressionEngine']/ExpressionEngine")
        assert Engine is not None
        _ = XmlTree.SubElement(
            Engine,
            "Expression",
            {"path": "Placement.Base.x", "expression": "Dimensions.zero"},
        )
        Engine.set("count", str(len(Engine)))
    Props.set("Count", str(len(Props)))


# native alias reconstruction must participate in both semantic replay digest compositions
def ObserveAlias(SourcePath: FilePath) -> dict[str, object]:
    Before = SourcePath.read_bytes()
    Document = OpenDocument(SourcePath, SourceFormat="freecad.fcstd", StrictMode=True)
    assert Document.source.sha256 == DigestBytes(Before).hexdigest()
    Output = ByteStream()
    Result = WriteDocument(
        Document, Output, DestFormat="freecad.fcstd", AllowCarrier=True
    )
    assert Result.metadata["mode"] == "exact_native_roundtrip"
    assert Output.getvalue() == Before == SourcePath.read_bytes()
    return {
        "source_sha256": Document.source.sha256,
        "replay_identical": True,
        "document": ParseJson(Document.to_json(indent=None)),
        "native_acceptance": "not_established",
    }


# independently owned end properties retain units current values and exact raw expression text
def AssertOwners(Document: CadDocument, CaseName: str) -> None:
    Params = {
        Value.attributes.get("freecad_path"): Value
        for Value in Document.parameters
        if Value.owner_id == "freecad:feature:Extrusion"
    }
    Forward, Reverse, Factor = (
        Params[FieldName] for FieldName in ("LengthFwd", "LengthRev", "Factor")
    )
    assert Forward.id != Reverse.id and Forward.value.unit == Reverse.value.unit == "mm"
    assert {Forward.id, Reverse.id} <= set(Document.feature_timeline[0].parameter_ids)
    assert Forward.value.value == (
        14.0 if CaseName == "edited" else 7.0 if CaseName == "equal-reordered" else 11.0
    )
    assert Reverse.value.value == (7.0 if CaseName == "equal-reordered" else 5.0)
    assert Factor.value.value == (
        0.0
        if CaseName in {"nonfinite-scalar", "invalid-scalar", "missing-scalar"}
        else 2.5
    )
    assert Factor.value.kind == ValueKind.KNumber
    for Param in (Forward, Reverse, Factor):
        assert Param.expression is not None and Param.expression.language == "freecad"
    Expected = {
        "unknown-alias": "Dimensions.absent",
        "label-ref": "DisplaySheet.forward",
        "arithmetic": "Dimensions.forward + 1 mm",
        "leading-reference": "= Dimensions.forward",
    }.get(CaseName, "Dimensions.forward")
    assert Forward.expression is not None and Forward.expression.source == Expected
    assert (
        Reverse.expression is not None
        and Reverse.expression.source == "Dimensions.reverse"
    )
    assert (
        Factor.expression is not None
        and Factor.expression.source == "Dimensions.factor"
    )


# unsupported observations remain inspectable without guessed ids or changed native scalar values
def AssertBindings(Document: CadDocument, CaseName: str) -> None:
    Params = {
        Value.attributes.get("freecad_path"): Value
        for Value in Document.parameters
        if Value.owner_id == "freecad:feature:Extrusion"
    }
    InvalidSheet = CaseName in {
        "duplicate-alias",
        "duplicate-address",
        "wrong-count",
        "cell-limit",
        "external-links",
        "duplicate-links",
        "unknown-child",
    }
    for FieldName, Address in (
        ("LengthFwd", "B1"),
        ("LengthRev", "B2"),
        ("Factor", "B3"),
    ):
        Expression = Params[FieldName].expression
        assert Expression is not None
        Expected = not InvalidSheet and (
            FieldName != "LengthFwd"
            or CaseName
            in {
                "literal",
                "leading-reference",
                "edited",
                "equal-reordered",
                "placeholder",
                "nonfinite-scalar",
                "invalid-scalar",
                "missing-scalar",
            }
        )
        if FieldName == "Factor" and CaseName in {
            "nonfinite-scalar",
            "invalid-scalar",
            "missing-scalar",
        }:
            Expected = False
        assert Expression.parameter_ids == (
            (f"freecad:parameter:Dimensions:cell:{Address}",) if Expected else ()
        )
    Cells = {
        Value.attributes.get("freecad_cell"): Value
        for Value in Document.parameters
        if Value.attributes.get("freecad_sheet") == "Dimensions"
    }
    if InvalidSheet:
        assert not Cells
    elif CaseName == "stale":
        assert Cells["B1"].value.value == 12.0 and Cells["B1"].value.unit == "mm"
    elif CaseName in {"literal", "leading-reference", "edited"}:
        assert (
            Cells["B1"].value.unit == "cm"
            and Cells["B1"].value.kind == ValueKind.KLength
        )
    if not InvalidSheet:
        assert (
            Cells["B3"].value.unit == "" and Cells["B3"].value.kind == ValueKind.KNumber
        )
    Findings = [
        Value
        for Value in Document.diagnostics
        if Value.code == "freecad.sheet_alias.unresolved"
    ]
    assert bool(Findings) is (
        CaseName not in {"literal", "leading-reference", "edited", "equal-reordered"}
    )
    if CaseName == "stale":
        assert Findings[0].attributes["counts"] == {"quantity_mismatch": 1}
    if CaseName in {
        "placeholder",
        "nonfinite-scalar",
        "invalid-scalar",
        "missing-scalar",
    }:
        assert Findings[0].attributes["counts"] == {"unverified_native_value": 1}


# raw metadata must preserve every source cell even when typed recovery is unsupported
def AssertRawSheet(Document: CadDocument, CaseName: str) -> None:
    Native = CastValue(Mapping[str, object], Document.metadata["freecad"])
    Objects = CastValue(Sequence[Mapping[str, object]], Native["objects"])
    (Sheet,) = (Value for Value in Objects if Value.get("name") == "Dimensions")
    Props = CastValue(Mapping[str, object], Sheet["properties"])
    Property = CastValue(Mapping[str, object], Props["cells"])
    Groups = CastValue(Sequence[Mapping[str, object]], Property["children"])
    (Cells,) = (Value for Value in Groups if Value.get("tag") == "Cells")
    Nodes = CastValue(Sequence[Mapping[str, object]], Cells["children"])
    Actual = [
        dict(CastValue(Mapping[str, str], Value["attributes"]))
        for Value in Nodes
        if Value.get("tag") == "Cell"
    ]
    assert Actual == MakeCells(CaseName)
    Links = [Value for Value in Nodes if Value.get("tag") == "XLinks"]
    if CaseName == "duplicate-links":
        assert len(Links) == 2
    if CaseName == "external-links":
        assert CastValue(Mapping[str, str], Links[0]["attributes"])["count"] == "1"
        assert Links[0]["children"]
    if CaseName == "unknown-child":
        assert any(Value.get("tag") == "UnresolvedNativeRecord" for Value in Nodes)


# normalized zeros cannot replace the actual native property or synthetic expression observations
def AssertEvidence(Document: CadDocument, CaseName: str) -> None:
    if CaseName == "placeholder":
        (Param,) = (
            Value
            for Value in Document.parameters
            if Value.attributes.get("freecad_path") == "Placement.Base.x"
        )
        assert Param.value.value == 0.0 and "freecad_property" not in Param.attributes
        assert (
            Param.expression is not None
            and Param.expression.source == "Dimensions.zero"
        )
        assert Param.expression.parameter_ids == ()
        Native = CastValue(Mapping[str, object], Document.metadata["freecad"])
        Objects = CastValue(Sequence[Mapping[str, object]], Native["objects"])
        (Owner,) = (Value for Value in Objects if Value.get("name") == "Extrusion")
        Props = CastValue(Mapping[str, object], Owner["properties"])
        Placement = CastValue(Mapping[str, object], Props["Placement"])
        Children = CastValue(Sequence[Mapping[str, object]], Placement["children"])
        assert CastValue(Mapping[str, str], Children[0]["attributes"])["Px"] == "17"
    if CaseName in {"nonfinite-scalar", "invalid-scalar", "missing-scalar"}:
        (Param,) = (
            Value
            for Value in Document.parameters
            if Value.attributes.get("freecad_path") == "Factor"
        )
        Property = CastValue(Mapping[str, object], Param.attributes["freecad_property"])
        Children = CastValue(Sequence[Mapping[str, object]], Property["children"])
        Actual = CastValue(Mapping[str, str], Children[0]["attributes"])
        assert (
            Actual.get("value")
            == {
                "nonfinite-scalar": "nan",
                "invalid-scalar": "invalid",
                "missing-scalar": None,
            }[CaseName]
        )
        assert Param.value.value == 0.0 and Param.expression is not None
        assert Param.expression.parameter_ids == ()


# actual native read and unchanged replay are isolated from fixture construction and assertions
@MarkValue.parametrize("CaseName", KCases)
def CheckAliases(TmpPath: FilePath, CaseName: str) -> None:
    Payload = MakeFixture(CaseName)
    SourcePath = TmpPath / "NativeAliases.FCStd"
    assert SourcePath.write_bytes(Payload) == len(Payload)
    Process = RunProcess(
        [
            PythonExe,
            "-B",
            "-m",
            "tests.Research.Archives.FreeCadAliases.NativeAliasTests",
            str(SourcePath),
        ],
        cwd=KRepoRoot,
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )
    assert Process.returncode == 0, Process.stderr + Process.stdout
    Report = CastValue(dict[str, object], ParseJson(Process.stdout))
    assert Report["source_sha256"] == DigestBytes(Payload).hexdigest()
    assert (
        Report["replay_identical"] is True
        and Report["native_acceptance"] == "not_established"
    )
    Document = CadDocument.from_json(EncodeJson(Report["document"]))
    assert SourcePath.read_bytes() == Payload
    AssertOwners(Document, CaseName)
    AssertBindings(Document, CaseName)
    AssertRawSheet(Document, CaseName)
    AssertEvidence(Document, CaseName)


if __name__ == "__main__":
    print(EncodeJson(ObserveAlias(FilePath(Arguments[1])), sort_keys=True))
