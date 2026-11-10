# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from dataclasses import replace as Replace
from pathlib import Path as FilePath
from xml.etree.ElementTree import fromstring as ParseXml
from zipfile import ZipFile

import pytest as Pytest

from convert import write_document as WriteDocument
from tests.convert.FusionRead import OpenResearch as OpenDocument
from convert.adapters.base.TransferContract import CarrierReason, TransferMode
from interchange.core.Common import FreezeMapping
from interchange.enums.EnumDocument import Capability

# saved fusion api controls have independently measured driving state and geometry
KSketchStudy = FilePath(__file__).parents[3] / "re" / "Fusion" / "Study"


# a native solver needs incidence between point records and the curves they control
def TestSketchRules(TmpPath: FilePath) -> None:
    Source = KSketchStudy / "sketches-0ccea2ac0f9c" / "radius.f3d"
    Document = OpenDocument(Source, StrictMode=False)
    (Sketch,) = Document.sketches
    assert tuple(Value.kind for Value in Sketch.constraints) == (
        "horizontal",
        "vertical",
        "coincident",
        "radius",
    )
    Radius = Sketch.constraints[-1]
    assert Radius.parameter_id in Sketch.parameter_ids
    Target = TmpPath / "sketch.FCStd"
    _ = WriteDocument(Document, Target)
    with ZipFile(Target) as Archive:
        RootValue = ParseXml(Archive.read("Document.xml"))
    Rules = RootValue.findall(
        ".//Property[@name='Constraints']/ConstraintList/Constrain"
    )
    Sources = [
        Value for Value in Rules if not Value.attrib["Name"].startswith("incidence_")
    ]
    assert [Value.attrib["Type"] for Value in Sources] == ["2", "3", "1", "11"]
    assert float(Sources[-1].attrib["Value"]) == Pytest.approx(12.5)
    assert len(Rules) == len(Sources) + 5
    NativeCoincident = Sources[-2]
    assert NativeCoincident.attrib["First"] != NativeCoincident.attrib["Second"]
    assert (
        NativeCoincident.attrib["FirstPos"]
        == NativeCoincident.attrib["SecondPos"]
        == "1"
    )
    assert OpenDocument(Target) == Document


# a reference dimension measures the native sketch without imposing its captured value
def TestRefRadius(TmpPath: FilePath) -> None:
    Source = KSketchStudy / "dimcontrols-2a0d0bdbc8a6" / "radius_reference.f3d"
    Document = OpenDocument(Source, StrictMode=False)
    (Sketch,) = Document.sketches
    (Radius,) = Sketch.constraints
    assert Radius.kind == "radius" and not Radius.driving
    Target = TmpPath / "reference.FCStd"
    _ = WriteDocument(Document, Target)
    with ZipFile(Target) as Archive:
        RootValue = ParseXml(Archive.read("Document.xml"))
    Datum = RootValue.find(".//ConstraintList/Constrain[@Type='11']")
    assert Datum is not None and Datum.attrib["IsDriving"] == "0"
    assert float(Datum.attrib["Value"]) == Pytest.approx(14.0)
    assert not any(
        "Constraints" in Value.attrib["path"]
        for Value in RootValue.findall(".//ExpressionEngine/Expression")
    )


# reversing the point order changes the solver sign without changing the source magnitude
def TestSignedRule(TmpPath: FilePath) -> None:
    Source = KSketchStudy / "dimensions-f83a2edd2f72" / "dimensions.f3d"
    Document = OpenDocument(Source, StrictMode=False)
    Sketch = next(
        Value for Value in Document.sketches if Value.name == "DimensionHorizontal"
    )
    (RuleValue,) = Sketch.constraints
    ReversedRule = Replace(
        RuleValue,
        references=RuleValue.references[::-1],
        attributes=FreezeMapping(
            {**RuleValue.attributes, "fusion.signed_distance_multiplier": -1}
        ),
    )
    Edited = Replace(Sketch, constraints=(ReversedRule,))
    Document = Replace(
        Document,
        sketches=tuple(
            Edited if Value.id == Edited.id else Value for Value in Document.sketches
        ),
    )
    Target = TmpPath / "negative.FCStd"
    Result = WriteDocument(Document, Target)
    SketchTransfer = next(
        Value
        for Value in Result.transfers
        if Value.capability is Capability.EDITABLE_SKETCHES
    )
    assert SketchTransfer.mode is TransferMode.MIXED
    assert SketchTransfer.carrier_reason is CarrierReason.SOURCE_OPAQUE
    with ZipFile(Target) as Archive:
        RootValue = ParseXml(Archive.read("Document.xml"))
    Datum = RootValue.find(".//ConstraintList/Constrain[@Type='7']")
    assert Datum is not None and float(Datum.attrib["Value"]) == -35.0
    PathValue = f".Constraints.{Datum.attrib['Name']}"
    Engine = RootValue.find(f".//ExpressionEngine/Expression[@path='{PathValue}']")
    assert Engine is not None
    assert Engine.attrib["expression"] == "-(Parameters.fusion_parameter_277)"
