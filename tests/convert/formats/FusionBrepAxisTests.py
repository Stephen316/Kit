from io import BytesIO
from math import radians as Radians
from zipfile import ZipFile

import pytest as Pytest

from tests.convert.FusionRead import OpenResearch as OpenDocument
from convert.formats.Fusion.DesignZip import KDesignPrefix, ReadDesignZip
from interchange.document.models.DocumentModel import CadDocument
from interchange.features.FeatureAngleRev import AngularRevolve
from tests.convert.api.ApiFusionAssemblyTests import KRequiresCodec, KStudyPath

# the native controls select the bottom rim of the prior extrusion along different axes
KEdgeAxisCases = (
    (
        "revolveaxes-a83b542c4a07/brep_edge.f3d",
        (0.0, 30.0, 0.0),
        (0.0, 1.0, 0.0),
        750.0,
        "prism-edge-2",
    ),
    (
        "revolveaxes-14700158dba9/brep_edge_offset_x.f3d",
        (48.0, 0.0, 0.0),
        (1.0, 0.0, 0.0),
        1110.0,
        "prism-edge-3",
    ),
)


# typed body and edge selection must retain the native source and both neutral solids
@KRequiresCodec
@Pytest.mark.parametrize(
    ("Capture", "Origin", "Direction", "SeedVolume", "EdgeName"), KEdgeAxisCases
)
def TestBrepAxisRev(
    Capture: str,
    Origin: tuple[float, ...],
    Direction: tuple[float, ...],
    SeedVolume: float,
    EdgeName: str,
) -> None:
    DocValue = OpenDocument(KStudyPath / Capture, StrictMode=False)
    _, Creator, _, Sweep = DocValue.feature_timeline
    Definition = Sweep.definition
    assert isinstance(Definition, AngularRevolve)
    BaseValue = Definition.AxisOrigin
    AxisValue = Definition.AxisDirection
    assert (BaseValue.x, BaseValue.y, BaseValue.z) == Pytest.approx(Origin)
    assert (AxisValue.x, AxisValue.y, AxisValue.z) == Pytest.approx(Direction)
    assert Creator.id in Sweep.input_feature_ids
    assert DocValue.parameter(Definition.AlongParameterId).value.value == Pytest.approx(
        Radians(73)
    )
    SeedValue, Result = DocValue.bodies
    assert (
        SeedValue.final_feature_id == Creator.id and Result.final_feature_id == Sweep.id
    )
    assert SeedValue.provenance is not None and Result.provenance is not None
    assert (
        SeedValue.provenance.native_id == "275" and Result.provenance.native_id == "378"
    )
    assert [Value.topology.volume for Value in (SeedValue, Result)] == Pytest.approx(
        (SeedVolume, 2446.25347959525)
    )
    (Selection,) = DocValue.selections
    assert Selection.id == Definition.AxisSelectionId == "fusion-selection-347-axis"
    assert (
        Selection.path[0].entity_kind == "body"
        and Selection.path[0].entity_id == SeedValue.id
    )
    assert Selection.path[1].entity_kind == "edge"
    assert Selection.path[1].entity_id == f"{SeedValue.id}-{EdgeName}"
    assert DocValue.brep is not None
    assert any(Value.id == Selection.path[1].entity_id for Value in DocValue.brep.edges)
    assert Selection.provenance is not None
    assert any(
        SpanValue.record_kind == "asm_history"
        for SpanValue in Selection.provenance.spans
    )
    assert not DocValue.brep.validate(frozenset({SeedValue.id, Result.id}))
    assert CadDocument.FromJson(DocValue.ToJson()) == DocValue


# a valid saved line cannot rescue a recipe naming the wrong native face
@KRequiresCodec
def TestBrepName() -> None:
    Source = KStudyPath / KEdgeAxisCases[0][0]
    BulkData, Spans = ReadDesignZip(Source.read_bytes())
    Recipe = next(Value for Value in Spans if Value.IsPrimary and Value.ObjectId == 353)
    Position = Recipe.PayloadOffset + 4 + 22
    Changed = bytearray(BulkData)
    assert Changed[Position] == ord("3")
    Changed[Position] = ord("1")
    Buffer = BytesIO()
    with ZipFile(Source) as Archive, ZipFile(Buffer, "w") as CopyValue:
        for NameValue in Archive.namelist():
            CopyValue.writestr(
                NameValue,
                (
                    Changed
                    if NameValue == KDesignPrefix + "BulkStream.dat"
                    else Archive.read(NameValue)
                ),
            )
    DocValue = OpenDocument(Buffer.getvalue(), StrictMode=False)
    assert DocValue.feature_timeline[-1].definition is None
    assert DocValue.brep is None
    assert any(
        Value.code == "fusion.revolve.angular_extent_unsupported"
        for Value in DocValue.diagnostics
    )
