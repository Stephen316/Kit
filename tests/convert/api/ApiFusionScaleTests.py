# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from tests.convert.api.ScaleCases import KScaleCases
from io import BytesIO as ByteStream
from zipfile import ZipFile

import pytest as Pytest

from tests.convert.FusionRead import OpenResearch as OpenDocument
from convert.formats.Fusion.DesignZip import KDesignPrefix, ReadDesignZip
from convert.formats.Fusion.Topology.BodyAsmMap import ReadBodyAsmRef
from interchange.document.models.DocumentModel import CadDocument
from interchange.features.BoundScaleValues import GetScaleValues
from interchange.features.FeatureBoundScale import BoundScale
from interchange.geometry.models.VectorSpace import SpaceVector
from tests.convert.api.ApiFusionAssemblyTests import KRequiresCodec, KStudyPath


# the public reader retains editable controls and exposes only fully verified final bodies
@KRequiresCodec
@Pytest.mark.parametrize("Sample,Factors,Center,Volume,AreaValue,Count", KScaleCases)
def TestScaleRead(
    Sample: str,
    Factors: tuple[float, float, float],
    Center: tuple[float, float, float],
    Volume: float,
    AreaValue: float,
    Count: int,
) -> None:
    Archive = KStudyPath / Sample
    Document = OpenDocument(Archive, StrictMode=False)
    Feature = Document.feature_timeline[-1]
    Definition = Feature.definition
    assert isinstance(Definition, BoundScale)
    assert Definition.FactorParameterIds == Feature.parameter_ids
    assert Definition.BodySelectionIds == Feature.selection_ids[:-1]
    assert Definition.CenterSelectionId == Feature.selection_ids[-1]
    Selections = {Value.id: Value for Value in Document.selections}
    assert GetScaleValues(
        Feature,
        Definition,
        {Value.id: Value for Value in Document.parameters},
        Selections,
    ) == (
        SpaceVector(*Factors),
        SpaceVector(*Center),
    )
    assert len(Document.bodies) == Count and Document.brep is not None
    for BodyValue, SelectionId in zip(
        Document.bodies, Definition.BodySelectionIds, strict=True
    ):
        Query = Selections[SelectionId].query
        assert BodyValue.id == f"fusion-derived-body-{Query['source_feature_id']}"
        assert BodyValue.final_feature_id == Feature.id
        assert (
            BodyValue.provenance is not None
            and BodyValue.provenance.native_id == str(Query["native_body_id"])
        )
        assert (
            BodyValue.topology.volume,
            BodyValue.topology.surface_area,
        ) == Pytest.approx((Volume, AreaValue))
        assert (
            BodyValue.topology.face_count,
            BodyValue.topology.edge_count,
            BodyValue.topology.vertex_count,
        ) == (6, 12, 8)
    if Count == 2:
        assert tuple(
            BodyValue.topology.bounding_box.minimum.x
            for BodyValue in Document.bodies
            if BodyValue.topology.bounding_box is not None
        ) == (10.0, 94.0)
    assert CadDocument.from_json(Document.to_json()) == Document


# equal volume and area cannot hide swapped native cache ownership
@KRequiresCodec
def TestScaleSwap() -> None:
    Archive = KStudyPath / KScaleCases[4][0]
    BulkData, Spans = ReadDesignZip(Archive.read_bytes())
    Owners = {Value.ObjectId: Value for Value in Spans if Value.IsPrimary}
    Mapping = ReadBodyAsmRef(BulkData, Owners, 275, 3)
    assert Mapping.Handles == frozenset((0, 1))
    Offset = Owners[Mapping.RecordId].PayloadOffset + 10
    Wrong = (
        BulkData[:Offset]
        + BulkData[Offset + 16 : Offset + 24]
        + BulkData[Offset + 8 : Offset + 16]
        + BulkData[Offset : Offset + 8]
        + BulkData[Offset + 24 :]
    )
    Stream = ByteStream()
    with ZipFile(Archive) as Original, ZipFile(Stream, "w") as Mutated:
        BulkName = KDesignPrefix + "BulkStream.dat"
        for NameValue in Original.namelist():
            Mutated.writestr(
                NameValue, Wrong if NameValue == BulkName else Original.read(NameValue)
            )
    _ = Stream.seek(0)
    Document = OpenDocument(Stream, StrictMode=False)
    assert Document.brep is None and not Document.bodies
    assert Document.feature_timeline[-1].definition is None
    assert len(Document.feature_timeline[-1].selection_ids) == 2
    assert any(
        Value.code == "fusion.scale.body_unsupported" for Value in Document.diagnostics
    )


# a stored vertex coordinate cannot stand in for its persistent source identity
@KRequiresCodec
def TestScaleVertex() -> None:
    Archive = KStudyPath / "scaleshellinputs-97ef1cfd19e4/scale_vertex.f3d"
    Document = OpenDocument(Archive, StrictMode=False)
    Feature = Document.feature_timeline[-1]
    assert len(Feature.selection_ids) == 1 and Feature.definition is None
    assert Document.brep is None and not Document.bodies
    assert any(
        Value.code == "fusion.scale.body_unsupported"
        and "center source method" in Value.message
        for Value in Document.diagnostics
    )
