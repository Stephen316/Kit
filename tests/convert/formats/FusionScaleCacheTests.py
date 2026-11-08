# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from dataclasses import replace as Replace

import pytest as Pytest

from convert.api import open_document as OpenDocument
from convert.formats.Fusion.BodyBlob import ReadBodyBlob
from convert.formats.Fusion.DesignZip import ReadDesignZip
from convert.formats.Fusion.Topology.AsmEdge.AsmFields import ReadAsmPtr
from convert.formats.Fusion.Topology.AsmEdge.AsmPrism import ReadAsmPrism
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import (
    AsmTable,
    KAsmToken,
    ReadAsmTable,
)
from convert.formats.Fusion.Topology.AsmEdge.PrismCache import ReadPrismCache
from convert.formats.Fusion.Topology.AsmEdge.PrismProfile import ReadProfileTags
from convert.formats.Fusion.Topology.BodyAsmMap import BodyAsmRef, ReadBodyAsmRef
from convert.geometry.Extrude.Polygon.PolygonExtrude import BuildPrism
from interchange.brep.topology.BrepModel import BrepModel
from interchange.features.DistanceValues import GetDistValues
from interchange.features.FeatureDistExt import DistanceExtrude
from interchange.geometry.models.GeometryCurves import LineGeometry
from interchange.geometry.models.Transform import KTransformIdentity
from interchange.geometry.models.VectorPlane import PlaneVector
from tests.convert.api.ApiFusionAssemblyTests import KRequiresCodec, KStudyPath

# captured controls cover positive expansion contraction and each distinct axis factor
KOriginCases = (
    ("tools-fda3948848f4/Scale.f3d", (1.25, 1.25, 1.25), (0.0, 0.0, 0.0), (1,)),
    (
        "bodymodes-df9b7113539f/scale_uniform.f3d",
        (1.75, 1.75, 1.75),
        (0.0, 0.0, 0.0),
        (0,),
    ),
    (
        "bodymodes-df9b7113539f/scale_nonuniform.f3d",
        (1.2, 0.8, 1.6),
        (0.0, 0.0, 0.0),
        (0,),
    ),
    (
        "bodymodes-d696a14d5f0b/scale_holdout.f3d",
        (0.65, 0.65, 0.65),
        (0.0, 0.0, 0.0),
        (0,),
    ),
)

# displaced centres verify that the complete saved result includes affine translation
KOffsetCases = (
    (
        "bodyselections-62e42366c722/scale_two_bodies_point.f3d",
        (1.4, 1.4, 1.4),
        (10.0, -10.0, 0.0),
        (0, 1),
    ),
    (
        "scaleshellinputs-97ef1cfd19e4/scale_vertex.f3d",
        (1.3, 1.3, 1.3),
        (40.0, 40.0, 0.0),
        (2,),
    ),
    (
        "scaleshellinputs-97ef1cfd19e4/scale_construction_point.f3d",
        (1.3, 1.3, 1.3),
        (20.0, -10.0, 0.0),
        (0,),
    ),
)

# native history references are compared against separately constructed test solids
KCachePrism = tuple[AsmTable, BodyAsmRef, BrepModel, tuple[int, ...]]


# saved api controls independently move each sketch coordinate in the component frame
def ScaleTestPoint(
    PointValue: PlaneVector, Factors: tuple[float, ...], Center: tuple[float, ...]
) -> PlaneVector:
    return PlaneVector(
        Center[0] + Factors[0] * (PointValue.x - Center[0]),
        Center[1] + Factors[1] * (PointValue.y - Center[1]),
    )


# source sketch and distance build a test witness without consuming any cached coordinates
def OpenScalePrisms(
    SampleName: str, Factors: tuple[float, ...], Center: tuple[float, ...]
) -> tuple[KCachePrism, ...]:
    Source = KStudyPath / SampleName
    SourceData = Source.read_bytes()
    DocValue = OpenDocument(Source, strict=False)
    BulkData, Spans = ReadDesignZip(SourceData)
    Owners = {Value.ObjectId: Value for Value in Spans if Value.IsPrimary}
    Features = {Value.id: Value for Value in DocValue.feature_timeline}
    Sketches = {Value.id: Value for Value in DocValue.sketches}
    Params = {Value.id: Value for Value in DocValue.parameters}
    Prisms = []
    for PickValue in DocValue.selections:
        if PickValue.query.get("kind") != "historical_body":
            continue
        StepValue = Features[PickValue.query["source_feature_id"]]
        SketchValue = Sketches[StepValue.sketch_id]
        Entities = {Value.id: Value for Value in SketchValue.entities}
        Profile = tuple(
            Entities[Identity]
            for Identity in StepValue.attributes["fusion.profile_entity_ids"]
        )
        Definition = StepValue.definition
        assert isinstance(Definition, DistanceExtrude)
        Values = GetDistValues(StepValue, Definition, Params)
        Lines = tuple(
            LineGeometry(
                ScaleTestPoint(Value.geometry.start, Factors, Center),
                ScaleTestPoint(Value.geometry.end, Factors, Center),
            )
            for Value in Profile
            if isinstance(Value.geometry, LineGeometry)
        )
        assert len(Lines) == 4 and Center[2] == 0.0
        RefValue = ReadBodyAsmRef(
            BulkData,
            Owners,
            PickValue.query["native_body_id"],
            PickValue.query["native_component_id"],
        )
        Table = ReadAsmTable(ReadBodyBlob(SourceData, RefValue.FileName, None))
        Model = BuildPrism(
            "expected-prism",
            KTransformIdentity,
            Lines,
            0.0,
            Factors[2] * Values.UpperMm,
        )[0]
        Prisms.append((Table, RefValue, Model, ReadProfileTags(Profile)))
    return tuple(Prisms)


# named topology and all carriers must match independently constructed scaled geometry
@KRequiresCodec
@Pytest.mark.parametrize(
    "SampleName,Factors,Center,Handles", (*KOriginCases, *KOffsetCases)
)
def TestScaleCache(
    SampleName: str,
    Factors: tuple[float, ...],
    Center: tuple[float, ...],
    Handles: tuple[int, ...],
) -> None:
    Prisms = OpenScalePrisms(SampleName, Factors, Center)
    assert tuple(RefValue.Handle for _, RefValue, _, _ in Prisms) == Handles
    for Ordinal, (Table, RefValue, Model, CurveTags) in enumerate(Prisms, 1):
        assert (
            ReadPrismCache(Table, RefValue.Handle, RefValue.Handles, Model, CurveTags)
            == Ordinal
        )
        with Pytest.raises(ValueError, match="transformed"):
            ReadAsmPrism(Table, Ordinal, len(CurveTags))

    if len(Prisms) == 2:
        (Table, RefValue, Model, CurveTags), (_, OtherRef, _, _) = Prisms
        with Pytest.raises(ValueError, match="tags do not bind"):
            ReadPrismCache(Table, OtherRef.Handle, RefValue.Handles, Model, CurveTags)


# semantic token mutations exercise actual cache checks without altering a saved fixture
def ChangeAsmToken(
    Table: AsmTable, Identity: int, Position: int, Token: KAsmToken
) -> AsmTable:
    Record = Table.Records[Identity]
    Updated = Replace(
        Record,
        Tokens=(*Record.Tokens[:Position], Token, *Record.Tokens[Position + 1 :]),
    )
    return Replace(
        Table,
        Records=(*Table.Records[:Identity], Updated, *Table.Records[Identity + 1 :]),
    )


# a matching handle alone cannot make a different transform line or plane authoritative
@KRequiresCodec
def TestBadScale() -> None:
    SampleName, Factors, Center, _ = KOriginCases[2]
    ((Table, RefValue, Model, CurveTags),) = OpenScalePrisms(
        SampleName, Factors, Center
    )
    TransformId = ReadAsmPtr(Table.Records[1], 5)
    CurveId = next(
        Index
        for Index, Value in enumerate(Table.Records)
        if Value.Name == "straight-curve"
    )
    PlaneId = next(
        Index
        for Index, Value in enumerate(Table.Records)
        if Value.Name == "plane-surface"
    )
    PointId = next(
        Index for Index, Value in enumerate(Table.Records) if Value.Name == "point"
    )
    Mutations = (
        (TransformId, 5, (20, (0.0, 0.0, 1.0)), "placement is not identity"),
        (PointId, 3, (19, (0.0, 0.0, 0.0)), "vertices disagree"),
        (CurveId, 4, (20, (-2.0, 0.0, 0.0)), "line disagrees"),
        (PlaneId, 3, (19, (0.0, 0.0, 0.0)), "plane disagrees"),
    )
    for Identity, Position, Token, Message in Mutations:
        Changed = ChangeAsmToken(Table, Identity, Position, Token)
        with Pytest.raises(ValueError, match=Message):
            ReadPrismCache(Changed, RefValue.Handle, RefValue.Handles, Model, CurveTags)
    with Pytest.raises(ValueError, match="stored body handles"):
        ReadPrismCache(Table, 2, frozenset({2}), Model, CurveTags)
