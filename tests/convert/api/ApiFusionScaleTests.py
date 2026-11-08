# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from io import BytesIO as ByteStream
from zipfile import ZipFile

import pytest as Pytest

from convert import open_document as OpenDocument
from convert.formats.Fusion.DesignZip import KDesignPrefix, ReadDesignZip
from convert.formats.Fusion.Topology.BodyAsmMap import ReadBodyAsmRef
from interchange.document.models.DocumentModel import CadDocument
from interchange.features.BoundScaleValues import GetScaleValues
from interchange.features.FeatureBoundScale import BoundScale
from interchange.geometry.models.VectorSpace import SpaceVector
from tests.convert.api.ApiFusionAssemblyTests import KRequiresCodec, KStudyPath

# real saved controls exercise every supported parameter and center route
KScaleCases = (
    ("tools-fda3948848f4/Scale.f3d", (1.25,) * 3, (0, 0, 0), 46875, 8125, 1),
    (
        "bodymodes-df9b7113539f/scale_uniform.f3d",
        (1.75,) * 3,
        (0, 0, 0),
        128625,
        15925,
        1,
    ),
    (
        "bodymodes-df9b7113539f/scale_nonuniform.f3d",
        (1.2, 0.8, 1.6),
        (0, 0, 0),
        36864,
        6912,
        1,
    ),
    ("bodymodes-d696a14d5f0b/scale_holdout.f3d", (0.65,) * 3, (0, 0, 0), 6591, 2197, 1),
    (
        "bodyselections-62e42366c722/scale_two_bodies_point.f3d",
        (1.4,) * 3,
        (10, -10, 0),
        49392,
        8232,
        2,
    ),
    (
        "scaleshellinputs-97ef1cfd19e4/scale_construction_point.f3d",
        (1.3,) * 3,
        (20, -10, 0),
        39546,
        7098,
        1,
    ),
)


# the public reader retains editable controls and exposes only fully verified final bodies
@KRequiresCodec
@Pytest.mark.parametrize("Sample,Factors,Center,Volume,Area,Count", KScaleCases)
def TestScaleRead(
    Sample: str,
    Factors: tuple[float, float, float],
    Center: tuple[float, float, float],
    Volume: float,
    Area: float,
    Count: int,
) -> None:
    Archive = KStudyPath / Sample
    Document = OpenDocument(Archive, strict=False)
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
    for Body, SelectionId in zip(
        Document.bodies, Definition.BodySelectionIds, strict=True
    ):
        Query = Selections[SelectionId].query
        assert Body.id == f"fusion-derived-body-{Query['source_feature_id']}"
        assert Body.final_feature_id == Feature.id
        assert Body.provenance is not None and Body.provenance.native_id == str(
            Query["native_body_id"]
        )
        assert (Body.topology.volume, Body.topology.surface_area) == Pytest.approx(
            (Volume, Area)
        )
        assert (
            Body.topology.face_count,
            Body.topology.edge_count,
            Body.topology.vertex_count,
        ) == (6, 12, 8)
    if Count == 2:
        assert tuple(
            Body.topology.bounding_box.minimum.x
            for Body in Document.bodies
            if Body.topology.bounding_box is not None
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
        for Name in Original.namelist():
            Mutated.writestr(Name, Wrong if Name == BulkName else Original.read(Name))
    Stream.seek(0)
    Document = OpenDocument(Stream, strict=False)
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
    Document = OpenDocument(Archive, strict=False)
    Feature = Document.feature_timeline[-1]
    assert len(Feature.selection_ids) == 1 and Feature.definition is None
    assert Document.brep is None and not Document.bodies
    assert any(
        Value.code == "fusion.scale.body_unsupported"
        and "center source method" in Value.message
        for Value in Document.diagnostics
    )
