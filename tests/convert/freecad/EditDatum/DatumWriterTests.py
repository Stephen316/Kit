# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt


from xml.etree.ElementTree import Element
from interchange.features.FeatureStep import FeatureStep
from interchange.document.models.DocumentModel import CadDocument
from dataclasses import replace as Replace
from json import loads as LoadJson
from xml.etree.ElementTree import fromstring as ParseXml  # noqa: DUO107

from convert.adapters.freecad.Archive import BuildDocXmlMut
from convert.adapters.freecad.EditDatum.DatumBinding import KDatumBinding, KDatumGroup
from convert.adapters.freecad.EditDatum.DatumPlan import ReadDatumPlan
from interchange.features.FeatureBoundPlane import BoundDatum
from interchange.records.RecordParameter import Expression
from tests.interchange.document.BoundPlaneTests import PlaneDocument


# independent datums may share labels while retaining distinct source and native identities
def CheckMultiDatum() -> None:
    Offset = PlaneDocument("offset")
    Angle = PlaneDocument("angle")
    AngleStep = Angle.feature_timeline[0]
    AngleDef = AngleStep.definition
    assert isinstance(AngleDef, BoundDatum)
    Extra = Replace(
        AngleStep,
        id="second",
        order=1,
        parameter_ids=("angle_extra", "angle_scalar"),
        definition=Replace(
            AngleDef,
            SupportPlaneId="second_plane",
            ScalarParameterId="angle_scalar",
            OffsetParameterId="angle_extra",
        ),
    )
    OffsetScalar, OffsetExtra = Offset.parameters
    AngleScalar, AngleExtra = Angle.parameters
    SecondParams = tuple(
        Replace(Param, id=f"angle_{Param.id}", owner_id=Extra.id)
        for Param in (
            Replace(AngleScalar, expression=Expression("90 deg")),
            AngleExtra,
        )
    )
    Document = Replace(
        Offset,
        parameters=(
            Replace(OffsetScalar, expression=Expression("-2.5 cm")),
            OffsetExtra,
            *SecondParams,
        ),
        support_planes=(
            *Offset.support_planes,
            Replace(Angle.support_planes[0], id="second_plane"),
        ),
        feature_timeline=(*Offset.feature_timeline, Extra),
    )
    Editable: set[str] = set()
    DataValue, Entries = BuildDocXmlMut(
        Document.to_dict(), "", "", EditableFeatures=Editable
    )
    assert Editable == {"plane", "second"} and not Entries
    AssertDatumXml(DataValue, Document)


# the emitted datum group preserves both live parameter references and source identities
def AssertDatumXml(DataValue: bytes, Document: CadDocument) -> None:
    RootValue = ParseXml(DataValue)
    Objects = RootValue.findall("./Objects/Object")
    Planes = [
        Value.get("name") for Value in Objects if Value.get("type") == "App::Plane"
    ]
    assert len(Planes) == 2 and len(set(Planes)) == 2
    assert not any(Value.get("type") == "Part::Feature" for Value in Objects)
    MetadataValue = RootValue.find(
        "./ObjectData/Object[@name='KitMetadata']/Properties"
    )
    assert MetadataValue is not None
    Marker = MetadataValue.find(f"./Property[@name='{KDatumBinding}']/String")
    assert Marker is not None and Marker.get("value") == KDatumGroup
    AliasProp = MetadataValue.find("./Property[@name='ParameterAliasesJSON']/String")
    assert AliasProp is not None
    Aliases = LoadJson(AliasProp.get("value", ""))
    Cells = {
        Value.get("alias"): Value.get("content")
        for Value in RootValue.findall("./ObjectData/Object[@name='Parameters']//Cell")
        if Value.get("alias")
    }
    assert Cells[Aliases["scalar"]] == "=-2.5 cm"
    assert Cells[Aliases["angle_scalar"]] == "=90 deg"
    Timeline = RootValue.findall(
        f"./ObjectData/Object[@name='{KDatumGroup}']/Properties/"
        + "Property[@name='Group']/LinkList/Link"
    )
    assert [Value.get("value") for Value in Timeline] == Planes
    for NameValue, StepValue in zip(Planes, Document.feature_timeline, strict=True):
        AssertDatumProp(RootValue, NameValue, StepValue, Aliases)


# each live datum must retain its own native placement expression and neutral identity
def AssertDatumProp(
    RootValue: Element,
    NameValue: str | None,
    StepValue: FeatureStep,
    Aliases: dict[str, str],
) -> None:
    Properties = RootValue.find(f"./ObjectData/Object[@name='{NameValue}']/Properties")
    assert Properties is not None
    FeatureId = Properties.find("./Property[@name='KitFeatureId']/String")
    assert FeatureId is not None and FeatureId.get("value") == StepValue.id
    Definition = StepValue.definition
    assert isinstance(Definition, BoundDatum)
    PlaneId = Properties.find("./Property[@name='KitId']/String")
    assert PlaneId is not None and PlaneId.get("value") == Definition.SupportPlaneId
    Visibility = Properties.find("./Property[@name='Visibility']/Bool")
    assert Visibility is not None and Visibility.get("value") == "true"
    Placement = Properties.find("./Property[@name='Placement']/PropertyPlacement")
    assert Placement is not None
    assert float(Placement.get("Px", "")) == (
        -22.0 if Definition.Method == "offset" else 3.0
    )
    (ExprData,) = Properties.findall(
        "./Property[@name='ExpressionEngine']/ExpressionEngine/Expression"
    )
    assert ExprData.get("path") == "Placement"
    assert f"Parameters.{Aliases[Definition.ScalarParameterId]}" in ExprData.get(
        "expression", ""
    )


# unverified expressions and historical state must stay in the legacy support route
def CheckBadDatum() -> None:
    Document = PlaneDocument("offset")
    Scalar, Extra = Document.parameters
    Formula = Replace(
        Document,
        parameters=(
            Replace(Scalar, expression=Expression("-2 cm - 5 mm", language="fusion")),
            Extra,
        ),
    )
    Stale = Replace(
        Document,
        parameters=(Replace(Scalar, expression=Expression("9 mm")), Extra),
    )
    Unproven = Replace(
        Document, source=Replace(Document.source, format_id="fusion.f3d")
    )
    (StepValue,) = Document.feature_timeline
    Rolled = Replace(
        Document,
        feature_timeline=(Replace(StepValue, attributes={"fusion.rolled_back": True}),),
    )
    for Value in (Formula, Stale, Unproven, Rolled):
        assert not ReadDatumPlan(Value)
        Editable: set[str] = set()
        DataValue, _ = BuildDocXmlMut(
            Value.to_dict(), "", "", EditableFeatures=Editable
        )
        assert not Editable and KDatumBinding.encode() not in DataValue
        assert b'name="FeatureTimeline"' in DataValue
