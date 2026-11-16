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
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Features.FeatureExtrude import ExtrudeEnd, ExtrudeFeature
from interchange.geometry.Models.VectorSpace import SpaceVector

# process fixtures must invoke the same checkout that owns the native interpretation contract
KRepoRoot = FilePath(__file__).resolve().parents[3]

# independent flag variations distinguish equal end lengths from symmetric total thickness and reversal
KEndCases = (
    ("equal-separate", 7.0, 7.0, False, False),
    ("symmetric-total", 16.0, 0.0, True, False),
    ("equal-symmetric", 7.0, 7.0, True, False),
    ("equal-reversed", 7.0, 7.0, True, True),
    ("unequal-separate", 11.0, 5.0, False, False),
    ("unequal-reversed", 11.0, 5.0, False, True),
    ("inactive-reverse", 16.0, 5.0, True, True),
    ("absent-flags", 7.0, 7.0, None, None),
)


# authored xml properties exercise native reading without either embedded kit manifest representation
def MakeNative(
    Forward: float, Reverse: float, Symmetric: bool | None, Reversed: bool | None
) -> bytes:
    Fields = [
        ("Label", "App::PropertyString", "String", {"value": "Independent ends"}),
        (
            "Dir",
            "App::PropertyVector",
            "PropertyVector",
            {"valueX": "0", "valueY": "0", "valueZ": "2"},
        ),
        ("LengthFwd", "App::PropertyDistance", "Float", {"value": str(Forward)}),
        ("LengthRev", "App::PropertyDistance", "Float", {"value": str(Reverse)}),
    ]
    for FieldName, FlagValue in (("Symmetric", Symmetric), ("Reversed", Reversed)):
        if FlagValue is not None:
            Fields.append(
                (
                    FieldName,
                    "App::PropertyBool",
                    "Bool",
                    {"value": str(FlagValue).lower()},
                )
            )
    RootValue = XmlTree.Element(
        "Document", {"SchemaVersion": "4", "ProgramVersion": "1.0", "FileVersion": "1"}
    )
    Objects = XmlTree.SubElement(RootValue, "Objects", {"Count": "1"})
    _ = XmlTree.SubElement(
        Objects, "Object", {"type": "Part::Extrusion", "name": "Extrusion", "id": "1"}
    )
    ObjectData = XmlTree.SubElement(RootValue, "ObjectData", {"Count": "1"})
    OwnerNode = XmlTree.SubElement(ObjectData, "Object", {"name": "Extrusion"})
    Properties = XmlTree.SubElement(
        OwnerNode, "Properties", {"Count": str(len(Fields))}
    )
    for FieldName, TypeName, TagName, Values in Fields:
        Property = XmlTree.SubElement(
            Properties, "Property", {"name": FieldName, "type": TypeName}
        )
        _ = XmlTree.SubElement(Property, TagName, Values)
    assert not any(
        ChildNode.get("name", "").startswith("KitManifest")
        for ChildNode in RootValue.iter()
    )
    Output = ByteStream()
    with ZipFile(Output, "w") as Archive:
        Archive.writestr("Document.xml", XmlTree.tostring(RootValue, encoding="utf-8"))
    return Output.getvalue()


# the child crosses the actual public native archive decoder and portable codec without writer admission
def ReadNative(SourcePath: FilePath) -> dict[str, object]:
    Original = SourcePath.read_bytes()
    Document = OpenDocument(SourcePath, SourceFormat="freecad.fcstd", StrictMode=True)
    assert SourcePath.read_bytes() == Original
    return {
        "scope": "native_reader_observation",
        "semantic_qualification": "unverified",
        "native_acceptance": "not_established",
        "input_sha256": DigestBytes(Original).hexdigest(),
        "document": ParseJson(Document.to_json(indent=None)),
    }


# saved flags and inactive properties must survive the real standalone public read process unchanged
@MarkValue.parametrize("CaseName,Forward,Reverse,Symmetric,Reversed", KEndCases)
def CheckNativeEnds(
    TmpPath: FilePath,
    CaseName: str,
    Forward: float,
    Reverse: float,
    Symmetric: bool | None,
    Reversed: bool | None,
) -> None:
    Payload = MakeNative(Forward, Reverse, Symmetric, Reversed)
    SourcePath = TmpPath / f"{CaseName}.FCStd"
    assert SourcePath.write_bytes(Payload) == len(Payload)
    Process = RunProcess(
        [
            PythonExe,
            "-B",
            "-m",
            "tests.Research.Archives.FreeCadNativeEndTests",
            str(SourcePath),
        ],
        cwd=KRepoRoot,
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )
    assert Process.returncode == 0, Process.stderr + Process.stdout
    assert SourcePath.read_bytes() == Payload
    Report = CastValue(dict[str, object], ParseJson(Process.stdout))
    assert Report["scope"] == "native_reader_observation"
    assert Report["semantic_qualification"] == "unverified"
    assert Report["native_acceptance"] == "not_established"
    assert Report["input_sha256"] == DigestBytes(Payload).hexdigest()
    Document = CadDocument.from_json(EncodeJson(Report["document"]))
    assert Document.source.sha256 == Report["input_sha256"]
    (Feature,) = Document.feature_timeline
    Definition = Feature.definition
    assert isinstance(Definition, ExtrudeFeature)
    assert Definition.length is not None and Definition.length.value == Forward
    assert (
        Definition.second_length is not None
        and Definition.second_length.value == Reverse
    )
    assert Definition.length.unit == Definition.second_length.unit == "mm"
    assert Definition.end_condition == ExtrudeEnd.KBlind
    assert Definition.symmetric is bool(Symmetric) and Definition.reversed is bool(
        Reversed
    )
    assert Definition.direction == SpaceVector(0.0, 0.0, 2.0)
    VerifyRawFlags(Feature.attributes, Symmetric, Reversed)


# raw property preservation keeps inactive native settings available without fabricating active semantics
def VerifyRawFlags(
    Attributes: object, Symmetric: bool | None, Reversed: bool | None
) -> None:
    FeatureAttrs = CastValue(dict[str, object], Attributes)
    NativeValue = CastValue(dict[str, object], FeatureAttrs["freecad"])
    Properties = CastValue(dict[str, object], NativeValue["properties"])
    for FieldName, FlagValue in (("Symmetric", Symmetric), ("Reversed", Reversed)):
        if FlagValue is None:
            assert FieldName not in Properties
            continue
        assert Properties[FieldName] == {
            "tag": "Property",
            "attributes": {"name": FieldName, "type": "App::PropertyBool"},
            "children": [
                {"tag": "Bool", "attributes": {"value": str(FlagValue).lower()}}
            ],
        }


if __name__ == "__main__":
    print(EncodeJson(ReadNative(FilePath(Arguments[1])), sort_keys=True))
