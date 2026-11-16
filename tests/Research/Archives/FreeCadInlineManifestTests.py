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

from convert.adapters.freecad.Adapter import FreeCadAdapterA
from convert.adapters.freecad.Archive import ExtractManifest
from convert.api.ApiOpen import OpenDocument
from convert.api.ApiWrite import WriteDocument
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Enums.EnumFeatures import FeatureKind
from interchange.Enums.EnumDocument import Capability
from interchange.Features.FeatureStep import FeatureStep
from interchange.geometry.Models.VectorSpace import SpaceVector
from interchange.mesh.SurfaceMesh import SurfaceMesh
from interchange.Payloads.PayloadRecord import BrepPayload
from interchange.Payloads.PayloadRoles import PayloadRole
from tests.Research.Archives.FreeCadInitialShapeTests import MakeInitial
from tests.Research.Archives.FreeCadTwoLengthBindingTests import (
    KBuildCase,
    KReadinessCases,
)

# source graphs vary their actual native end semantics and retain original parameter identities
KInlineCases = {
    "two-length": ("rectangle:right:reverse", False, False),
    "symmetric": ("triangle:right:symmetric", False, False),
    "omitted": ("circle:xy:forward", True, False),
    "reference": ("pentagon:xy:anti", True, True),
    "constrained": ("", False, False),
}

# retained geometry and native binding contracts stay outside this bounded reconciliation guard
KRetainedCases = (
    "usable-mesh",
    "native-binding",
    "empty-mesh",
    "auxiliary-note",
    "verification-note",
)

# structurally valid field changes leave the original neutral copies untouched
KFieldEdits = {
    "forward": ("LengthFwd", "value", "14.25"),
    "reverse": ("LengthRev", "value", "9.5"),
    "symmetric": ("Symmetric", "value", "true"),
    "reversal": ("Reversed", "value", "false"),
    "direction": ("Dir", "valueY", "0.25"),
    "direction-mode": ("DirMode", "value", "1"),
    "solid": ("Solid", "value", "false"),
    "termination": ("EndCondition", "value", "through_all"),
    "nonfinite": ("LengthFwd", "value", "nan"),
}

# the exact current checkout supplies both real public process boundaries
KRepoRoot = FilePath(__file__).resolve().parents[3]


# default operations and sketch references do not erase the inline native feature owner
def MakeInline(CaseName: str) -> CadDocument:
    if CaseName in KRetainedCases:
        return MakeRetained(CaseName)
    if CaseName == "constrained":
        return KBuildCase(KReadinessCases[0])
    SeedName, Omitted, Reference = KInlineCases[CaseName]
    Document = MakeInitial(SeedName)
    Feature = Document.feature_timeline[0]
    if Omitted:
        Feature = ChangeRecord(Feature, operation=None)
    if not Reference:
        return ChangeRecord(Document, feature_timeline=(Feature,))
    SketchStep = FeatureStep(
        "inline:reference",
        "Profile",
        FeatureKind.KReference,
        0,
        sketch_id=Feature.sketch_id,
        attributes={"native_type": "sketch"},
    )
    Feature = ChangeRecord(Feature, order=1, input_feature_ids=(SketchStep.id,))
    return ChangeRecord(Document, feature_timeline=(SketchStep, Feature))


# actual typed retained routes remain independently readable without qualifying their native behavior
def MakeRetained(CaseName: str) -> CadDocument:
    Document = MakeInline("two-length")
    if CaseName.endswith("mesh"):
        MeshValue = SurfaceMesh("retained:mesh", "Retained mesh", (), ())
        if CaseName == "usable-mesh":
            MeshValue = ChangeRecord(
                MeshValue,
                vertices=(
                    SpaceVector(0, 0, 0),
                    SpaceVector(3, 0, 0),
                    SpaceVector(0, 2, 0),
                ),
                triangles=((0, 1, 2),),
            )
        return ChangeRecord(Document, meshes=(MeshValue,))
    IsBinding = CaseName == "native-binding"
    Content = (
        DigestBytes(b"independently authored binding control").digest()
        if IsBinding
        else b"independent note"
    )
    Payload = BrepPayload(
        "freecad:native-document-binding" if IsBinding else "independent-note",
        "freecad.fcstd.sha256" if IsBinding else "research.note",
        "native_document_binding" if IsBinding else "text",
        "sha256" if IsBinding else "utf8",
        DigestBytes(Content).hexdigest(),
        Content,
        role=(
            PayloadRole.KAuxiliary
            if CaseName == "auxiliary-note"
            else PayloadRole.KVerification
        ),
        file_extension=".sha256" if IsBinding else ".txt",
    )
    return ChangeRecord(Document, brep_payloads=(Payload,))


# native object lookup uses declared types before selecting any property values
def ReadNativeObj(RootValue: XmlTree.Element, TypeName: str) -> XmlTree.Element:
    Names = {
        Value.attrib["name"]
        for Value in RootValue.findall("./Objects/Object")
        if Value.get("type") == TypeName
    }
    (Owner,) = (
        Value
        for Value in RootValue.findall("./ObjectData/Object")
        if Value.get("name") in Names
    )
    return Owner


# test mutations address one actual native property child rather than editing portable data
def ReadNativeVal(Owner: XmlTree.Element, FieldName: str) -> XmlTree.Element:
    (Property,) = Owner.findall(f"./Properties/Property[@name='{FieldName}']")
    return Property[0]


# the saved native end expression identifies the live spreadsheet alias independently of metadata
def ChangeCellMut(RootValue: XmlTree.Element, SourceText: str) -> None:
    Owner = ReadNativeObj(RootValue, "Part::Extrusion")
    Engine = ReadNativeVal(Owner, "ExpressionEngine")
    (Expression,) = Engine.findall("./Expression[@path='LengthFwd']")
    Alias = Expression.attrib["expression"].split(".", 1)[1]
    Sheet = ReadNativeObj(RootValue, "Spreadsheet::Sheet")
    (CellValue,) = ReadNativeVal(Sheet, "cells").findall(f"./Cell[@alias='{Alias}']")
    CellValue.set("content", SourceText)


# native owner and base changes remain valid xml while contradicting the embedded source graph
def ChangeOwnerMut(RootValue: XmlTree.Element, ModeName: str) -> None:
    Owner = ReadNativeObj(RootValue, "Part::Extrusion")
    if ModeName == "base":
        ReadNativeVal(Owner, "Base").set("value", "Parameters")
    elif ModeName == "missing-owner":
        ReadNativeVal(Owner, "KitId").set("value", "foreign-owner")
    elif ModeName == "duplicate-owner":
        Sketch = ReadNativeObj(RootValue, "Sketcher::SketchObject")
        ReadNativeVal(Sketch, "KitId").set(
            "value", ReadNativeVal(Owner, "KitId").attrib["value"]
        )
    elif ModeName == "end-roster":
        Engine = ReadNativeVal(Owner, "ExpressionEngine")
        (Expression,) = Engine.findall("./Expression[@path='LengthRev']")
        Expression.set("path", "LengthFwd")
    elif ModeName == "placement":
        Sketch = ReadNativeObj(RootValue, "Sketcher::SketchObject")
        ReadNativeVal(Sketch, "Placement").set("Px", "21.0")
    elif ModeName == "cell":
        ChangeCellMut(RootValue, "=19 mm")
    elif ModeName == "literal":
        ChangeCellMut(RootValue, "=11 mm")


# extra native taper controls cannot silently enter the untapered source family
def ChangeTaperMut(RootValue: XmlTree.Element) -> None:
    Owner = ReadNativeObj(RootValue, "Part::Extrusion")
    (Properties,) = Owner.findall("Properties")
    Property = XmlTree.SubElement(
        Properties, "Property", {"name": "TaperAngle", "type": "App::PropertyAngle"}
    )
    _ = XmlTree.SubElement(Property, "Float", {"value": "2.0"})
    Properties.set("Count", str(len(Properties.findall("Property"))))


# duplicate local links and unknown records cannot be hidden behind unchanged alias cells
def ChangeLinksMut(RootValue: XmlTree.Element, ModeName: str) -> None:
    Cells = ReadNativeVal(ReadNativeObj(RootValue, "Spreadsheet::Sheet"), "cells")
    if ModeName == "duplicate-links":
        _ = XmlTree.SubElement(Cells, "XLinks", {"count": "0"})
    elif ModeName == "unknown-cell-child":
        _ = XmlTree.SubElement(Cells, "UnknownRecord", {"value": "unresolved"})
    else:
        Cells.set("xlink", "0")


# profile edits keep the source snapshots intact while changing actual solver inputs
def ChangeSketchMut(RootValue: XmlTree.Element, ModeName: str) -> None:
    Sketch = ReadNativeObj(RootValue, "Sketcher::SketchObject")
    if ModeName == "constraint":
        Constraints = ReadNativeVal(Sketch, "Constraints")
        Constraints[0].set("IsDriving", "0")
        return
    Geometry = ReadNativeVal(Sketch, "Geometry")[0]
    if ModeName == "construction":
        (Construction,) = Geometry.findall("Construction")
        Construction.set("value", "1")
        (Extension,) = Geometry.findall("./GeoExtensions/GeoExtension")
        Extension.set("geometryModeFlags", "0" * 30 + "10")
        return
    (Segment,) = Geometry.findall("LineSegment")
    Segment.set("StartX", "3.125")


# a new real shape owner cannot disappear behind the unchanged original body tip
def AddForeignMut(RootValue: XmlTree.Element) -> None:
    (Objects,) = RootValue.findall("Objects")
    (ObjectData,) = RootValue.findall("ObjectData")
    NextId = max(int(Value.attrib["id"]) for Value in Objects.findall("Object")) + 1
    _ = XmlTree.SubElement(
        Objects,
        "Object",
        {"type": "Part::Feature", "name": "ForeignSolid", "id": str(NextId)},
    )
    Objects.set("Count", str(len(Objects.findall("Object"))))
    Owner = XmlTree.SubElement(ObjectData, "Object", {"name": "ForeignSolid"})
    Properties = XmlTree.SubElement(Owner, "Properties", {"Count": "1"})
    Property = XmlTree.SubElement(
        Properties, "Property", {"name": "Shape", "type": "Part::PropertyPartShape"}
    )
    Source = ReadNativeVal(ReadNativeObj(RootValue, "Part::Extrusion"), "Shape")
    Property.append(XmlTree.fromstring(XmlTree.tostring(Source)))
    ObjectData.set("Count", str(len(ObjectData.findall("Object"))))


# only native document fields change while archived sidecars and both portable snapshots remain available
def RewriteNative(Payload: bytes, ModeName: str) -> bytes:
    with ZipFile(ByteStream(Payload)) as Archive:
        Entries = {Value.filename: Archive.read(Value) for Value in Archive.infolist()}
    RootValue = XmlTree.fromstring(Entries["Document.xml"])
    if ModeName in KFieldEdits:
        FieldName, AttrName, NewValue = KFieldEdits[ModeName]
        ReadNativeVal(ReadNativeObj(RootValue, "Part::Extrusion"), FieldName).set(
            AttrName, NewValue
        )
    elif ModeName == "taper":
        ChangeTaperMut(RootValue)
    elif ModeName in ("geometry", "constraint", "construction"):
        ChangeSketchMut(RootValue, ModeName)
    elif ModeName == "foreign-solid":
        AddForeignMut(RootValue)
    elif ModeName in ("duplicate-links", "unknown-cell-child", "local-links"):
        ChangeLinksMut(RootValue, ModeName)
    elif ModeName == "copies":
        Manifest = ParseJson(Entries["interchange/document.json"])
        Manifest["schema_version"] = "2.0"
        Entries["interchange/document.json"] = EncodeJson(Manifest).encode()
    elif ModeName == "hash":
        (Digest,) = RootValue.findall(
            "./ObjectData/Object/Properties/Property[@name='KitManifestSHA256']/String"
        )
        Digest.set("value", "0" * 64)
    else:
        ChangeOwnerMut(RootValue, ModeName)
    Entries["Document.xml"] = XmlTree.tostring(
        RootValue, encoding="utf-8", xml_declaration=True
    )
    Output = ByteStream()
    with ZipFile(Output, "w") as Archive:
        for EntryName, Content in Entries.items():
            Archive.writestr(EntryName, Content)
    return Output.getvalue()


# public research writes create the actual native control graph used by the read boundary
def WriteInline(Document: CadDocument, *, RequireUnqualified: bool = True) -> bytes:
    Output = ByteStream()
    Result = WriteDocument(
        Document, Output, DestFormat="freecad.fcstd", AllowCarrier=True
    )
    assert Result.bytes_written == len(Output.getvalue())
    assert Result.metadata["application_usable"] is Result.application_usable
    assert Result.metadata["vendor_loadable"] is Result.vendor_loadable
    if RequireUnqualified:
        assert not Result.application_usable and not Result.vendor_loadable
    if Document.brep_payloads:
        assert Capability.KNativePayloads in Result.carrier_capabilities
    if any(MeshValue.triangles for MeshValue in Document.meshes):
        assert Capability.KTessellation in Result.native_capabilities
    return Output.getvalue()


# unchanged native controls preserve every original source identity and metadata field
def ObservePlain(CaseName: str) -> dict[str, object]:
    Document = CadDocument.from_json(MakeInline(CaseName).to_json(indent=None))
    Before = Document.to_json(indent=None)
    Payload = WriteInline(
        Document, RequireUnqualified=CaseName not in ("usable-mesh", "native-binding")
    )
    for StrictValue in (True, False):
        Readback = OpenDocument(
            Payload, SourceFormat="freecad.fcstd", StrictMode=StrictValue
        )
        assert Readback.to_json(indent=None) == Before
    if CaseName == "two-length":
        Alternate = RewriteNative(Payload, "literal")
        assert (
            OpenDocument(Alternate, SourceFormat="freecad.fcstd").to_json(indent=None)
            == Before
        )
    assert Document.to_json(indent=None) == Before
    return {"input_sha256": DigestBytes(Payload).hexdigest(), "source_preserved": True}


# detected unsupported changes cannot become a stale successful read even under filtering or permissive mode
def ObserveChange(ModeName: str) -> dict[str, object]:
    SourceCase = (
        ModeName.removesuffix("-forward")
        if ModeName.endswith("-forward")
        else "two-length"
    )
    if ModeName == "constraint":
        SourceCase = "constrained"
    Payload = WriteInline(MakeInline(SourceCase))
    Changed = RewriteNative(
        Payload, "forward" if ModeName.endswith("-forward") else ModeName
    )
    OriginalDigest = DigestBytes(Payload).hexdigest()
    ChangedDigest = DigestBytes(Changed).hexdigest()
    if ModeName not in ("copies", "hash"):
        assert ExtractManifest(Changed) == ExtractManifest(Payload)
    Expected = {"copies": "copies do not match", "hash": "hash mismatch"}.get(
        ModeName, "inline native controls require unsupported edit reconciliation"
    )
    for StrictValue in (True, False):
        try:
            _ = OpenDocument(
                Changed,
                SourceFormat="freecad.fcstd",
                StrictMode=StrictValue,
                IncludeBrep=False,
                IncludeTess=False,
            )
        except FreeCadAdapterA as Problem:
            assert Expected in str(Problem)
        else:
            raise AssertionError("changed native controls returned the stale snapshot")
    assert DigestBytes(Payload).hexdigest() == OriginalDigest
    assert DigestBytes(Changed).hexdigest() == ChangedDigest
    return {"refusals": 2, "original_unchanged": True, "changed_sha256": ChangedDigest}


# each child exercises the real public reader without a native runtime or a private reconciliation call
@MarkValue.parametrize("CaseName", (*KInlineCases, *KRetainedCases))
def CheckUnchanged(CaseName: str) -> None:
    Process = RunProcess(
        [
            PythonExe,
            "-B",
            "-m",
            "tests.Research.Archives.FreeCadInlineManifestTests",
            "plain",
            CaseName,
        ],
        cwd=KRepoRoot,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    assert Process.returncode == 0, Process.stderr
    assert ParseJson(Process.stdout)["source_preserved"] is True


# independent native field and manifest mutations retain strict public refusal assertions
@MarkValue.parametrize(
    "ModeName",
    (
        *KFieldEdits,
        "base",
        "missing-owner",
        "duplicate-owner",
        "end-roster",
        "placement",
        "cell",
        "taper",
        "geometry",
        "constraint",
        "construction",
        "foreign-solid",
        "duplicate-links",
        "unknown-cell-child",
        "local-links",
        "empty-mesh-forward",
        "auxiliary-note-forward",
        "verification-note-forward",
        "copies",
        "hash",
    ),
)
def CheckRefused(ModeName: str) -> None:
    Process = RunProcess(
        [
            PythonExe,
            "-B",
            "-m",
            "tests.Research.Archives.FreeCadInlineManifestTests",
            "changed",
            ModeName,
        ],
        cwd=KRepoRoot,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    assert Process.returncode == 0, Process.stderr
    Report = CastValue(dict[str, object], ParseJson(Process.stdout))
    assert Report["refusals"] == 2 and Report["original_unchanged"] is True


if __name__ == "__main__":
    print(
        EncodeJson(
            (
                ObservePlain(Arguments[2])
                if Arguments[1] == "plain"
                else ObserveChange(Arguments[2])
            ),
            sort_keys=True,
        )
    )
