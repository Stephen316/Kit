from dataclasses import replace as ChangeRecord
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
from interchange.Features.FeatureExtrude import ExtrudeFeature
from interchange.geometry.Models.Transform import Transform
from interchange.geometry.Models.VectorSpace import SpaceVector
from tests.Research.Archives.FreeCadTwoLengthBindingTests import (
    KBuildCase,
    KObserveNative,
    KReadinessCases,
)

# process fixtures invoke the same checkout that owns the public writer and native read contracts
KRepoRoot = FilePath(__file__).resolve().parents[3]

# independent mode controls expose ignored explicit reversal and double reversed implicit profile normals
KReverseCases = {
    "explicit-positive": (True, 1, False, False),
    "explicit-reversed": (True, 1, True, False),
    "explicit-negative": (True, -1, False, False),
    "explicit-negative-reversed": (True, -1, True, False),
    "implicit-positive": (False, 1, False, False),
    "implicit-reversed": (False, 1, True, False),
    "implicit-negative": (False, -1, False, False),
    "implicit-negative-reversed": (False, -1, True, False),
    "explicit-symmetric": (True, 1, True, True),
    "implicit-symmetric": (False, -1, True, True),
}

# these are the two documented neutral manifest representations and no other native metadata is removed
KManifestProps = frozenset(
    {"KitManifestData", "KitManifestEncoding", "KitManifestSHA256"}
)


# typed authored controls retain their original geometry and depth bindings while varying only direction semantics
def MakeInput(CaseName: str) -> CadDocument:
    Explicit, SignValue, Reversed, Symmetric = KReverseCases[CaseName]
    Document = KBuildCase(KReadinessCases[4 if Symmetric else 0])
    Feature = Document.feature_timeline[0]
    Definition = Feature.definition
    assert isinstance(Definition, ExtrudeFeature)
    Definition = ChangeRecord(
        Definition,
        reversed=Reversed,
        direction=SpaceVector(0.0, 0.0, 2.0 * SignValue) if Explicit else None,
    )
    Frame = Transform(
        y_axis=SpaceVector(0.0, float(SignValue), 0.0),
        z_axis=SpaceVector(0.0, 0.0, float(SignValue)),
    )
    return ChangeRecord(
        Document,
        support_planes=(ChangeRecord(Document.support_planes[0], transform=Frame),),
        feature_timeline=(
            ChangeRecord(
                Feature,
                definition=Definition,
                attributes={**Feature.attributes, "direction_multiplier": -1.0},
            ),
        ),
    )


# native readback must consume the actual properties rather than either stored portable manifest copy
def StripManifest(Payload: bytes) -> bytes:
    with ZipFile(ByteStream(Payload)) as Archive:
        Entries = {Entry.filename: Archive.read(Entry) for Entry in Archive.infolist()}
    assert "interchange/document.json" in Entries
    del Entries["interchange/document.json"]
    RootValue = XmlTree.fromstring(Entries["Document.xml"])
    Removed: set[str] = set()
    for Properties in RootValue.findall(".//Properties"):
        for Property in tuple(Properties.findall("./Property")):
            if Property.get("name") in KManifestProps:
                Removed.add(Property.attrib["name"])
                Properties.remove(Property)
        Properties.set("Count", str(len(Properties.findall("./Property"))))
    assert Removed == KManifestProps
    Entries["Document.xml"] = XmlTree.tostring(RootValue, encoding="utf-8")
    Output = ByteStream()
    with ZipFile(Output, "w") as Archive:
        for EntryName, Content in Entries.items():
            Archive.writestr(EntryName, Content)
    return Output.getvalue()


# native object properties keep the unmodified base vector separate from the saved reversal control
def ReadDirection(Payload: bytes) -> tuple[list[float], bool]:
    with ZipFile(ByteStream(Payload)) as Archive:
        RootValue = XmlTree.fromstring(Archive.read("Document.xml"))
    Names = {
        NodeValue.attrib["name"]
        for NodeValue in RootValue.findall("./Objects/Object")
        if NodeValue.get("type") == "Part::Extrusion"
    }
    (Owner,) = (
        NodeValue
        for NodeValue in RootValue.findall("./ObjectData/Object")
        if NodeValue.get("name") in Names
    )
    Properties = {
        NodeValue.attrib["name"]: NodeValue
        for NodeValue in Owner.findall("./Properties/Property")
    }
    Direction = Properties["Dir"][0]
    return (
        [
            float(Direction.attrib[FieldName])
            for FieldName in ("valueX", "valueY", "valueZ")
        ],
        Properties["Reversed"][0].attrib["value"] == "true",
    )


# fresh public writes cross the codec admission native emission and independent native read boundaries
def ObserveWrite(CaseName: str) -> dict[str, object]:
    Document = CadDocument.from_json(MakeInput(CaseName).to_json(indent=None))
    Original = Document.to_json(indent=None)
    Output = ByteStream()
    Result = WriteDocument(
        Document, Output, DestFormat="freecad.fcstd", AllowCarrier=False
    )
    Payload = Output.getvalue()
    assert Result.bytes_written == len(Payload) and not Result.carrier_capabilities
    assert Document.to_json(indent=None) == Original
    NativeOnly = StripManifest(Payload)
    Readback = OpenDocument(NativeOnly, SourceFormat="freecad.fcstd", StrictMode=True)
    assert Readback.source.sha256 == DigestBytes(NativeOnly).hexdigest()
    (Feature,) = (
        Value
        for Value in Readback.feature_timeline
        if isinstance(Value.definition, ExtrudeFeature)
    )
    Definition = Feature.definition
    assert isinstance(Definition, ExtrudeFeature) and Definition.direction is not None
    Direction, Reversed = ReadDirection(Payload)
    return {
        "scope": "native_writer_property_observation",
        "native_acceptance": "not_established",
        "input_sha256": DigestBytes(Original.encode()).hexdigest(),
        "direction": Direction,
        "reversed": Reversed,
        "native": KObserveNative(
            Payload, KReadinessCases[4 if KReverseCases[CaseName][3] else 0]
        ),
        "read_direction": [
            Definition.direction.x,
            Definition.direction.y,
            Definition.direction.z,
        ],
        "read_reversed": Definition.reversed,
        "read_symmetric": Definition.symmetric,
    }


# real process execution prevents fixture or serialization assertions from substituting for public writes
@MarkValue.parametrize("CaseName", tuple(KReverseCases))
def CheckReversal(CaseName: str) -> None:
    Process = RunProcess(
        [
            PythonExe,
            "-B",
            "-m",
            "tests.Research.Archives.FreeCadReversedWriteTests",
            CaseName,
        ],
        cwd=KRepoRoot,
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )
    assert Process.returncode == 0, Process.stderr + Process.stdout
    Report = CastValue(dict[str, object], ParseJson(Process.stdout))
    _, SignValue, Reversed, Symmetric = KReverseCases[CaseName]
    assert Report["scope"] == "native_writer_property_observation"
    assert Report["native_acceptance"] == "not_established"
    assert (
        Report["direction"] == Report["read_direction"] == [0.0, 0.0, float(SignValue)]
    )
    assert Report["reversed"] is Reversed and Report["read_reversed"] is Reversed
    assert Report["read_symmetric"] is Symmetric
    Native = CastValue(dict[str, object], Report["native"])
    assert Native["symmetric"] is Symmetric
    assert Native["length_fwd"] == (16.0 if Symmetric else 11.0)
    assert Native["length_rev"] == (0.0 if Symmetric else 5.0)
    assert Native["expressions"] == Native["expected_drivers"]
    assert Native["missing_drivers"] == Native["crossed_drivers"] == []


if __name__ == "__main__":
    print(EncodeJson(ObserveWrite(Arguments[1]), sort_keys=True))
