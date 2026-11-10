# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from io import BytesIO
from math import pi as HalfTurn
from pathlib import Path as FilePath
import xml.etree.ElementTree as XmlTree
from zipfile import ZipFile

import pytest as Pytest

from convert import write_document as WriteDocument
from tests.convert.FusionRead import OpenResearch as OpenDocument
from convert.adapters.freecad.Adapter import FreeCadAdapterA
from convert.adapters.freecad.ArchiveEditPlan import KEditableBinding, KProfileBinding
from convert.adapters.freecad.Brep import BrepModelBrep
from convert.adapters.freecad.EditableExt import FindEditFrame
from convert.adapters.freecad.EditExtProfile import GetEditCircle
from convert.geometry.Extrude.Circular.CircularExtrude import BuildCircular
from interchange.document.models.DocumentModel import CadDocument
from interchange.geometry.models.GeometryCurves import CircleGeometry

# the native source fixture supplies the original carrier independently of the edit
KSourcePath = (
    FilePath(__file__).parents[3]
    / "re/Fusion/Study/extents-f0f33a9a605f/distance_positive.f3d"
)

# the formula holdout includes a second sketch that must remain independent
KFormulaPath = (
    FilePath(__file__).parents[3]
    / "re/Fusion/Study/holdouts-f8c508a73323/expression_depth.f3d"
)


# rebuilds let readback tests exercise the archive boundary without requiring a cad executable
def MakeEditShape(
    DocValue: CadDocument,
    DistanceMm: float,
    EditedProfile: CircleGeometry | None = None,
) -> bytes:
    Feature = DocValue.feature_timeline[-1]
    ProfileFrame = FindEditFrame(DocValue, Feature.sketch_id)
    assert ProfileFrame is not None
    Sketch, Plane = ProfileFrame
    Profile = (
        EditedProfile if EditedProfile is not None else GetEditCircle(Feature, Sketch)
    )
    assert Profile is not None
    Lower, Upper = sorted((0.0, DistanceMm))
    Model, _, _, _ = BuildCircular(
        DocValue.bodies[0].id,
        Plane.transform,
        Profile,
        Lower,
        Upper,
        Profile.radius,
        Profile.radius,
    )
    return BrepModelBrep(Model)


# separate sheet and shape replacements reproduce coherent and stale saves against one manifest
def ChangeEditFile(
    Output: FilePath,
    DistanceMm: float,
    ShapeData: bytes | None,
    ChangeMode: str,
    DriverAlias: str = "fusion_parameter_242",
    DriverText: str | None = None,
) -> bytes:
    with ZipFile(Output) as Archive:
        Entries = {
            NameValue: Archive.read(NameValue) for NameValue in Archive.namelist()
        }
    RootValue = XmlTree.fromstring(Entries["Document.xml"])
    Feature = RootValue.find("./Objects/Object[@type='Part::Extrusion']")
    assert Feature is not None
    FeaturePath = f"./ObjectData/Object[@name='{Feature.attrib['name']}']/Properties"
    CellValue = RootValue.find(f".//Cell[@alias='{DriverAlias}']")
    Depth = RootValue.find(f"{FeaturePath}/Property[@name='LengthFwd']/Float")
    Shape = RootValue.find(f"{FeaturePath}/Property[@name='Shape']/Part")
    assert CellValue is not None and Depth is not None and Shape is not None
    CellValue.set(
        "content", DriverText if DriverText is not None else f"={DistanceMm:g} mm"
    )
    Depth.set("value", str(DistanceMm))
    if ShapeData is not None:
        Entries[Shape.attrib["file"]] = ShapeData
    if ChangeMode == "wrong-formula":
        ResultCell = RootValue.find(".//Cell[@alias='fusion_parameter_276']")
        assert ResultCell is not None
        ResultCell.set("content", "=fusion_parameter_202 + 13.5 mm")
    ChangeBindMut(RootValue, ChangeMode, FeaturePath)
    if ChangeMode in {"carrier-shape", "sketch-shape"}:
        SetCarrierMut(RootValue, ChangeMode, Shape.attrib["file"])
    Entries["Document.xml"] = XmlTree.tostring(RootValue, encoding="utf-8")
    Buffer = BytesIO()
    with ZipFile(Buffer, "w") as Archive:
        for NameValue, DataValue in Entries.items():
            Archive.writestr(NameValue, DataValue)
    return Buffer.getvalue()


# legacy archive mutations retain the exact original binding and incidence cases
def ChangeBindMut(
    RootValue: XmlTree.Element, ChangeMode: str, FeaturePath: str
) -> None:
    if ChangeMode in {"unmarked", "legacy-identity", "legacy-bound"}:
        Metadata = RootValue.find("./ObjectData/Object[@name='KitMetadata']/Properties")
        assert Metadata is not None
        Binding = Metadata.find(f"Property[@name='{KEditableBinding}']")
        assert Binding is not None
        if ChangeMode != "legacy-bound":
            Metadata.remove(Binding)
        ProfileBinding = Metadata.find(f"Property[@name='{KProfileBinding}']")
        if ProfileBinding is not None:
            Metadata.remove(ProfileBinding)
            for Rules in RootValue.findall(".//ConstraintList"):
                for RuleValue in tuple(Rules):
                    if RuleValue.get("Name", "").startswith("incidence_"):
                        Rules.remove(RuleValue)
                Rules.set("count", str(len(Rules)))
        Metadata.set("Count", str(len(Metadata)))
    if ChangeMode in {"identity", "legacy-identity"}:
        Identity = RootValue.find(f"{FeaturePath}/Property[@name='KitId']/String")
        assert Identity is not None
        Identity.set("value", "removed-binding")


# carrier shapes simulate a saved cache attached to the wrong native object
def SetCarrierMut(RootValue: XmlTree.Element, ChangeMode: str, ShapeFile: str) -> None:
    TypeName = (
        "Part::Feature" if ChangeMode == "carrier-shape" else "Sketcher::SketchObject"
    )
    Other = RootValue.find(f"./Objects/Object[@type='{TypeName}']")
    assert Other is not None
    OtherProps = RootValue.find(
        f"./ObjectData/Object[@name='{Other.attrib['name']}']/Properties"
    )
    assert OtherProps is not None
    OtherShape = OtherProps.find("Property[@name='Shape']")
    if OtherShape is None:
        OtherShape = XmlTree.SubElement(
            OtherProps,
            "Property",
            {"name": "Shape", "type": "Part::PropertyPartShape"},
        )
        OtherProps.set("Count", str(len(OtherProps)))
    OtherPart = OtherShape.find("Part")
    if OtherPart is None:
        OtherPart = XmlTree.SubElement(OtherShape, "Part")
    OtherPart.set("file", ShapeFile)


# signed edits must update measures and preserve identities before applying public read filters
@Pytest.mark.parametrize(
    ("DistanceMm", "ChangeMode"),
    ((25.0, "bound"), (-25.0, "unmarked"), (0.021, "bound"), (22.0, "legacy-bound")),
)
def TestDepthEdit(TmpPath: FilePath, DistanceMm: float, ChangeMode: str) -> None:
    Document = OpenDocument(KSourcePath, StrictMode=False)
    Output = TmpPath / "editable.FCStd"
    _ = WriteDocument(Document, Output)
    assert OpenDocument(Output) == Document
    DataValue = ChangeEditFile(
        Output, DistanceMm, MakeEditShape(Document, DistanceMm), ChangeMode
    )
    Readback = OpenDocument(DataValue)
    Parameter = next(
        Value for Value in Readback.parameters if Value.id == "fusion-parameter-242"
    )
    ExpectedValue = (
        (DistanceMm, "mm") if DistanceMm == 0.021 else (DistanceMm / 10.0, "cm")
    )
    assert (Parameter.value.value, Parameter.value.unit) == ExpectedValue
    assert (
        Parameter.expression is not None and Parameter.expression.language == "freecad"
    )
    assert Readback.feature_timeline == Document.feature_timeline
    assert Readback.brep_payloads == Document.brep_payloads
    assert Readback.bodies[0].id == Document.bodies[0].id
    assert Readback.bodies[0].topology.volume == Pytest.approx(
        100.0 * abs(DistanceMm) * HalfTurn
    )
    assert Readback.bodies[0].topology.surface_area == Pytest.approx(
        (200.0 + 20.0 * abs(DistanceMm)) * HalfTurn
    )
    Bounds = Readback.bodies[0].topology.bounding_box
    assert Bounds is not None
    assert (Bounds.minimum.z, Bounds.maximum.z) == tuple(sorted((0.0, DistanceMm)))
    Filtered = OpenDocument(DataValue, IncludeBrep=False)
    assert Filtered.brep is None and Filtered.parameters == Readback.parameters
    Reexport = TmpPath / "reexport.FCStd"
    _ = WriteDocument(Readback, Reexport)
    assert OpenDocument(Reexport) == Readback


# a marked missing feature and a stale attached solid must fail explicitly
@Pytest.mark.parametrize(
    ("ChangeMode", "Reason"),
    (
        ("bound", "shape disagrees"),
        ("identity", "feature is missing"),
        ("legacy-identity", "feature is missing"),
    ),
)
def TestStaleEdit(TmpPath: FilePath, ChangeMode: str, Reason: str) -> None:
    Document = OpenDocument(KSourcePath, StrictMode=False)
    Output = TmpPath / "editable.FCStd"
    _ = WriteDocument(Document, Output)
    Stale = ChangeEditFile(Output, 25.0, None, ChangeMode)
    with Pytest.raises(FreeCadAdapterA, match=Reason):
        _ = OpenDocument(Stale)


# a valid edited solid must not hide a second solid on another native object
@Pytest.mark.parametrize(
    ("ChangeMode", "Reason"),
    (
        ("carrier-shape", "additional nonempty shape"),
        ("sketch-shape", "sketch cache disagrees"),
    ),
)
def TestExtraShape(TmpPath: FilePath, ChangeMode: str, Reason: str) -> None:
    Document = OpenDocument(KSourcePath, StrictMode=False)
    Output = TmpPath / "editable.FCStd"
    _ = WriteDocument(Document, Output)
    Edited = ChangeEditFile(Output, 25.0, MakeEditShape(Document, 25.0), ChangeMode)
    with Pytest.raises(FreeCadAdapterA, match=Reason):
        _ = OpenDocument(Edited)


# dependent geometry must follow the native driver without flattening its formula
def TestFormulaEdit(TmpPath: FilePath) -> None:
    Document = OpenDocument(KFormulaPath, StrictMode=False)
    Output = TmpPath / "editable.FCStd"
    _ = WriteDocument(Document, Output)
    assert OpenDocument(Output) == Document
    Edited = ChangeEditFile(
        Output,
        26.0,
        MakeEditShape(Document, 26.0),
        "bound",
        "fusion_parameter_202",
        "=12.5 mm",
    )
    Readback = OpenDocument(Edited)
    Driver = Readback.parameter("fusion-parameter-202")
    Result = Readback.parameter("fusion-parameter-276")
    assert Driver.value.value == 1.25 and Driver.value.unit == "cm"
    assert Result.value.value == 2.6 and Result.value.unit == "cm"
    assert Result.expression == Document.parameter(Result.id).expression
    assert Readback.sketches == Document.sketches
    assert Readback.feature_timeline == Document.feature_timeline
    assert Readback.brep_payloads == Document.brep_payloads
    assert Readback.bodies[0].topology.volume == Pytest.approx(3744 * HalfTurn)
    Reexport = TmpPath / "reexport.FCStd"
    _ = WriteDocument(Readback, Reexport)
    with ZipFile(Reexport) as Archive:
        assert b'type="Part::Extrusion"' in Archive.read("Document.xml")
    assert OpenDocument(Reexport) == Readback


# stale lengths and different formulas with the same result must both fail readback
@Pytest.mark.parametrize("ChangeMode", ("bound", "wrong-formula"))
def TestBadFormula(TmpPath: FilePath, ChangeMode: str) -> None:
    Document = OpenDocument(KFormulaPath, StrictMode=False)
    Output = TmpPath / "editable.FCStd"
    _ = WriteDocument(Document, Output)
    DistanceMm = 19.25 if ChangeMode == "bound" else 26.0
    ShapeData = None if ChangeMode == "bound" else MakeEditShape(Document, DistanceMm)
    Edited = ChangeEditFile(
        Output, DistanceMm, ShapeData, ChangeMode, "fusion_parameter_202", "=12.5 mm"
    )
    with Pytest.raises(FreeCadAdapterA, match="formula|depth|quantity"):
        _ = OpenDocument(Edited)


# equivalent spreadsheet units must not change provenance after a native no op save
def TestNoOpDepth(TmpPath: FilePath) -> None:
    Source = KSourcePath.parents[1] / "output-7230965e9265" / "depth07_a.f3d"
    Document = OpenDocument(Source, StrictMode=False)
    Output = TmpPath / "editable.FCStd"
    _ = WriteDocument(Document, Output)
    NativeSave = ChangeEditFile(
        Output, 7.0, MakeEditShape(Document, 7.0), "bound", DriverText="=0.7 cm"
    )
    assert OpenDocument(NativeSave) == Document
