from dataclasses import replace as ChangeRecord
from hashlib import sha256 as DigestBytes
from io import BytesIO as ByteStream
from json import dumps as EncodeJson, loads as ParseJson
from math import isclose as IsClose
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import argv as Arguments, executable as PythonExe
from typing import cast as CastValue
from xml.etree import ElementTree as XmlTree
from zipfile import ZipFile

from pytest import mark as MarkValue

from convert.api.ApiOpen import OpenDocument
from convert.api.ApiWrite import WriteDocument
from interchange.brep.Curves.BrepCurves import CircleCurve
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Enums.EnumFeatures import BooleanOp
from interchange.Enums.EnumUnits import UnitSystem
from interchange.Features.FeatureExtrude import ExtrudeFeature
from interchange.geometry.Models.GeometryCurves import CircleGeometry, LineGeometry
from interchange.geometry.Models.Sketch import SketchEntity
from interchange.geometry.Models.Transform import Transform
from interchange.geometry.Models.VectorPlane import PlaneVector
from interchange.geometry.Models.VectorSpace import SpaceVector
from tests.Research.Archives.FreeCadReversedWriteTests import StripManifest
from tests.Research.Archives.FreeCadTwoLengthBindingTests import (
    KBuildCase,
    KReadinessCases,
)

# fresh geometric inputs vary topology independently from the saved end controls
KProfiles: dict[str, tuple[tuple[float, float], ...]] = {
    "triangle": ((0.0, 0.0), (2.0, 9.0), (13.0, 0.0)),
    "rectangle": ((-3.0, 1.0), (14.0, 1.0), (14.0, 8.0), (-3.0, 8.0)),
    "pentagon": ((0.0, 0.0), (11.0, 0.0), (15.0, 4.0), (8.0, 12.0), (-2.0, 7.0)),
    "circle": (),
}

# independently stated physical stations distinguish flag semantics from equal distances
KEndModes = {
    "forward": (False, False, 1, -5.0, 11.0),
    "reverse": (False, True, 1, -11.0, 5.0),
    "anti": (False, False, -1, -11.0, 5.0),
    "double": (False, True, -1, -5.0, 11.0),
    "symmetric": (True, True, 1, -8.0, 8.0),
}

# both rigid frames have independently known coordinate formulas
KFrames = {
    "xy": Transform(),
    "right": Transform(
        SpaceVector(3.0, -2.0, 5.0),
        SpaceVector(0.0, 0.0, -1.0),
        SpaceVector(0.0, 1.0, 0.0),
        SpaceVector(1.0, 0.0, 0.0),
    ),
}

# child execution uses the checkout owning the real public writer
KRepoRoot = FilePath(__file__).resolve().parents[3]


# a loop with reversed source edges still defines one independently authored face
def MakeProfile(ProfileName: str) -> tuple[SketchEntity, ...]:
    if ProfileName == "circle":
        return (
            SketchEntity(
                "circle", "circle", CircleGeometry(PlaneVector(2.0, -1.0), 4.25)
            ),
        )
    Points = KProfiles[ProfileName]
    return tuple(
        SketchEntity(
            f"edge:{Index}",
            "line",
            (
                LineGeometry(PlaneVector(*Finish), PlaneVector(*Start))
                if Index % 2
                else LineGeometry(PlaneVector(*Start), PlaneVector(*Finish))
            ),
        )
        for Index, (Start, Finish) in enumerate(
            zip(Points, (*Points[1:], Points[0]), strict=True)
        )
    )


# authored inputs retain actual spreadsheet end ownership and contain no brep or native payload
def MakeInitial(CaseName: str) -> CadDocument:
    ProfileName, FrameName, ModeName = CaseName.split(":")
    Symmetric, Reversed, DirectionSign, _, _ = KEndModes[ModeName]
    Document = KBuildCase(KReadinessCases[4 if Symmetric else 0])
    Feature = Document.feature_timeline[0]
    Definition = Feature.definition
    assert isinstance(Definition, ExtrudeFeature)
    if ProfileName == "rectangle" and not Symmetric:
        Forward, Reverse = Document.parameters
        Forward = ChangeRecord(
            Forward, value=ChangeRecord(Forward.value, value=1.1, unit="cm")
        )
        Document = ChangeRecord(Document, parameters=(Forward, Reverse))
        Definition = ChangeRecord(Definition, length=Forward.value)
    FrameValue = KFrames[FrameName]
    Normal = FrameValue.z_axis
    Direction = (
        SpaceVector(
            *(DirectionSign * 2 * Value for Value in (Normal.x, Normal.y, Normal.z))
        )
        if ModeName != "forward"
        else None
    )
    Entities = MakeProfile(ProfileName)
    Sketch = ChangeRecord(
        Document.sketches[0],
        entities=Entities,
        constraints=(),
        closed_profile_entity_ids=(tuple(Entity.id for Entity in Entities),),
    )
    return ChangeRecord(
        Document,
        sketches=(Sketch,),
        support_planes=(
            ChangeRecord(Document.support_planes[0], transform=FrameValue),
        ),
        feature_timeline=(
            ChangeRecord(
                Feature,
                definition=ChangeRecord(
                    Definition, direction=Direction, reversed=Reversed
                ),
            ),
        ),
    )


# archive checks follow native shape ownership rather than metadata or portable manifest copies
def ReadShapeOwner(Payload: bytes) -> tuple[bytes, str]:
    with ZipFile(ByteStream(Payload)) as Archive:
        RootValue = XmlTree.fromstring(Archive.read("Document.xml"))
        Names = {
            Value.attrib["name"]
            for Value in RootValue.findall("./Objects/Object")
            if Value.get("type") == "Part::Extrusion"
        }
        (Owner,) = (
            Value
            for Value in RootValue.findall("./ObjectData/Object")
            if Value.get("name") in Names
        )
        (Shape,) = Owner.findall("./Properties/Property[@name='Shape']/Part")
        EntryName = Shape.attrib["file"]
        assert EntryName and EntryName in Archive.namelist()
        assert not any(
            Value.get("type") == "Part::Feature"
            for Value in RootValue.findall("./Objects/Object")
        )
        assert Owner.findall(
            "./Properties/Property[@name='ExpressionEngine']/ExpressionEngine/Expression"
        )
        (Cached,) = RootValue.findall(
            "./ObjectData/Object/Properties/Property[@name='CachedShapeEntry']/String"
        )
        assert Cached.attrib["value"] == EntryName
        return Archive.read(EntryName), EntryName


# native point expectations use independent world coordinate formulas for each authored frame
def ExpectedPoints(CaseName: str) -> set[tuple[float, float, float]]:
    ProfileName, FrameName, ModeName = CaseName.split(":")
    Lower, Upper = KEndModes[ModeName][3:]
    return {
        (
            (Station + 3.0, Second - 2.0, 5.0 - First)
            if FrameName == "right"
            else (First, Second, Station)
        )
        for First, Second in KProfiles[ProfileName]
        for Station in (Lower, Upper)
    }


# separately decoded native topology must describe the requested solid before any application recompute
def ReadCachedBody(CaseName: str, Document: CadDocument) -> dict[str, object]:
    Model = Document.brep
    assert Model is not None and len(Model.bodies) == len(Model.regions) == 1
    assert Model.regions[0].solid and all(Shell.closed for Shell in Model.shells)
    ProfileName, FrameName, ModeName = CaseName.split(":")
    if ProfileName == "circle":
        Circles = tuple(
            Curve for Curve in Model.curves if isinstance(Curve, CircleCurve)
        )
        assert len(Circles) == 2 and all(
            IsClose(Curve.radius, 4.25, rel_tol=0, abs_tol=1e-9) for Curve in Circles
        )
        Lower, Upper = KEndModes[ModeName][3:]
        Centers = {
            (Curve.center.x, Curve.center.y, Curve.center.z) for Curve in Circles
        }
        assert Centers == (
            {(3.0 + Station, -3.0, 3.0) for Station in (Lower, Upper)}
            if FrameName == "right"
            else {(2.0, -1.0, Station) for Station in (Lower, Upper)}
        )
    else:
        Actual = {
            (Vertex.point.x, Vertex.point.y, Vertex.point.z)
            for Vertex in Model.vertices
        }
        assert Actual == ExpectedPoints(CaseName)
        assert len(Model.faces) == len(KProfiles[ProfileName]) + 2
    return {
        "faces": len(Model.faces),
        "vertices": len(Model.vertices),
        "solid_count": len(Model.regions),
    }


# research output keeps explicit unqualified flags across public write and native read boundaries
def ObserveInitial(CaseName: str) -> dict[str, object]:
    if CaseName == "later":
        return ObserveLater()
    if CaseName in ("units", "oblique", "extra"):
        return ObserveUncached(CaseName)
    Document = CadDocument.from_json(MakeInitial(CaseName).to_json(indent=None))
    Before = Document.to_json(indent=None)
    Output = ByteStream()
    Result = WriteDocument(
        Document, Output, DestFormat="freecad.fcstd", AllowCarrier=True
    )
    assert not Result.application_usable and not Result.vendor_loadable
    assert (
        Result.metadata["application_usable"] is False
        and Result.metadata["vendor_loadable"] is False
    )
    Payload = Output.getvalue()
    ShapeData, EntryName = ReadShapeOwner(Payload)
    assert ShapeData and Result.bytes_written == len(Payload)
    NativeOnly = StripManifest(Payload)
    Readback = OpenDocument(NativeOnly, SourceFormat="freecad.fcstd", StrictMode=True)
    assert Readback.source.sha256 == DigestBytes(NativeOnly).hexdigest()
    assert Document.to_json(indent=None) == Before
    return {
        "geometry": ReadCachedBody(CaseName, Readback),
        "entry": EntryName,
        "native_acceptance": "not_established",
    }


# a later boolean owns its result and must never advertise the preceding extrusion cache
def ObserveLater() -> dict[str, object]:
    Document = MakeInitial("triangle:xy:forward")
    First = Document.feature_timeline[0]
    Later = ChangeRecord(
        First,
        id="later",
        name="LaterJoin",
        order=1,
        input_feature_ids=(First.id,),
        parameter_ids=(),
        attributes={},
        operation=BooleanOp.KJoin,
    )
    Document = ChangeRecord(
        Document,
        feature_timeline=(First, Later),
        bodies=(ChangeRecord(Document.bodies[0], final_feature_id=Later.id),),
    )
    Output = ByteStream()
    Result = WriteDocument(
        Document, Output, DestFormat="freecad.fcstd", AllowCarrier=True
    )
    assert Result.bytes_written == len(Output.getvalue())
    with ZipFile(ByteStream(Output.getvalue())) as Archive:
        RootValue = XmlTree.fromstring(Archive.read("Document.xml"))
        (Cached,) = RootValue.findall(
            "./ObjectData/Object/Properties/Property[@name='CachedShapeEntry']/String"
        )
        assert Cached.attrib["value"] == ""
        assert any(EntryName.endswith(".Shape.brp") for EntryName in Archive.namelist())
    return {
        "later_result_cache": "not_supplied",
        "native_acceptance": "not_established",
    }


# each unsupported cache request remains a valid request for explicit unqualified native research output
def MakeUncached(CaseName: str) -> CadDocument:
    Document = MakeInitial("triangle:xy:forward")
    if CaseName == "units":
        return ChangeRecord(Document, units=UnitSystem.KMeter)
    if CaseName == "extra":
        Sketch = Document.sketches[0]
        Extra = SketchEntity(
            "extra", "circle", CircleGeometry(PlaneVector(50.0, 50.0), 2.0)
        )
        return ChangeRecord(
            Document,
            sketches=(ChangeRecord(Sketch, entities=(*Sketch.entities, Extra)),),
        )
    Feature = Document.feature_timeline[0]
    Definition = Feature.definition
    assert isinstance(Definition, ExtrudeFeature)
    return ChangeRecord(
        Document,
        feature_timeline=(
            ChangeRecord(
                Feature,
                definition=ChangeRecord(
                    Definition, direction=SpaceVector(1e-5, 0.0, 1.0)
                ),
            ),
        ),
    )


# unsupported cache families preserve explicit unqualified output without a wrongly constructed shape
def ObserveUncached(CaseName: str) -> dict[str, object]:
    Document = MakeUncached(CaseName)
    Output = ByteStream()
    Result = WriteDocument(
        Document, Output, DestFormat="freecad.fcstd", AllowCarrier=True
    )
    assert not Result.application_usable and not Result.vendor_loadable
    with ZipFile(ByteStream(Output.getvalue())) as Archive:
        RootValue = XmlTree.fromstring(Archive.read("Document.xml"))
        assert not any(
            EntryName.endswith(".Shape.brp") for EntryName in Archive.namelist()
        )
        (Cached,) = RootValue.findall(
            "./ObjectData/Object/Properties/Property[@name='CachedShapeEntry']/String"
        )
        assert Cached.attrib["value"] == ""
    return {"initial_cache": "not_supplied", "native_acceptance": "not_established"}


# independent processes confirm unsupported geometry units directions and selections cannot acquire cache evidence
@MarkValue.parametrize("CaseName", ("units", "oblique", "extra"))
def CheckUnitCache(CaseName: str) -> None:
    Result = RunProcess(
        [
            PythonExe,
            "-B",
            "-m",
            "tests.Research.Archives.FreeCadInitialShapeTests",
            CaseName,
        ],
        cwd=KRepoRoot,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    assert Result.returncode == 0, Result.stderr
    assert ParseJson(Result.stdout)["initial_cache"] == "not_supplied"


# a real later feature write checks stale result ownership across native object construction
def CheckLaterCache() -> None:
    Result = RunProcess(
        [
            PythonExe,
            "-B",
            "-m",
            "tests.Research.Archives.FreeCadInitialShapeTests",
            "later",
        ],
        cwd=KRepoRoot,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    assert Result.returncode == 0, Result.stderr
    assert ParseJson(Result.stdout)["later_result_cache"] == "not_supplied"


# each process invokes actual public components with independently authored inputs
@MarkValue.parametrize("ProfileName", tuple(KProfiles))
@MarkValue.parametrize("FrameName", tuple(KFrames))
@MarkValue.parametrize("ModeName", tuple(KEndModes))
def CheckInitial(ProfileName: str, FrameName: str, ModeName: str) -> None:
    Result = RunProcess(
        [
            PythonExe,
            "-B",
            "-m",
            "tests.Research.Archives.FreeCadInitialShapeTests",
            f"{ProfileName}:{FrameName}:{ModeName}",
        ],
        cwd=KRepoRoot,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    assert Result.returncode == 0, Result.stderr
    Report = CastValue(dict[str, object], ParseJson(Result.stdout))
    assert Report["native_acceptance"] == "not_established"
    assert CastValue(dict[str, object], Report["geometry"])["solid_count"] == 1


if __name__ == "__main__":
    print(EncodeJson(ObserveInitial(Arguments[1]), sort_keys=True))
