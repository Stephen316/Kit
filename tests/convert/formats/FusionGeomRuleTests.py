# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt


from dataclasses import replace as Replace
from json import loads as LoadJson
from struct import pack as PackBytes

import pytest as Pytest

from tests.convert.FusionRead import OpenResearch as OpenDocument
from convert.formats.Fusion.DesignZip import ReadDesignZip
from convert.formats.Fusion.MetaCursor import MetaCursor
from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.Sketches.GeomRuleProjection import BuildGeomRules
from convert.formats.Fusion.Sketches.RulePrefix import ReadRulePrefix
from interchange.document.models.DocumentModel import CadDocument
from tests.convert.api.ApiFusionAssemblyTests import KRequiresCodec, KStudyPath

# the geometric fixtures retain actual api constraint getters alongside native ids
KBasicSketch = KStudyPath / "sketches-0ccea2ac0f9c"

# the advanced export isolates each higher arity relation in its own sketch
KAdvancedSketch = KStudyPath / "advanced-627f7fe095f4"


# native sketch projection may be verified before the public document integration
def ReadCase(
    Folder: str, NameValue: str
) -> tuple[CadDocument, bytes, tuple[RecordSpan, ...]]:
    FileValue = KStudyPath / Folder / f"{NameValue}.f3d"
    BulkData, Spans = ReadDesignZip(FileValue.read_bytes())
    return OpenDocument(FileValue, StrictMode=False), BulkData, Spans


# exact native reference bytes let mutations target only the disputed slot
def MakeReference(Identity: int) -> bytes:
    return b"\1" + PackBytes("<Q", Identity) + bytes(2)


# independent api labels corroborate line and point relation variants from basic sketches
@KRequiresCodec
@Pytest.mark.parametrize(
    "NameValue", ("baseline", "horizontal", "vertical", "coincident", "radius")
)
def CheckBasicRules(NameValue: str) -> None:
    DocValue, BulkData, Spans = ReadCase(KBasicSketch.name, NameValue)
    Oracle = LoadJson((KBasicSketch / "ground_truth.json").read_text(encoding="utf-8"))
    Expected = next(
        ItemValue["constraint_types"]
        for ItemValue in Oracle["samples"]
        if ItemValue["file"] == f"{NameValue}.f3d"
    )
    SketchValue = DocValue.sketches[0]
    BySketch, Diagnostics = BuildGeomRules(BulkData, Spans, DocValue.sketches)
    Relations = BySketch[SketchValue.id]
    assert not Diagnostics
    assert [RuleValue.kind for RuleValue in Relations] == [
        NameValue.split("::")[-1].removesuffix("Constraint").lower()
        for NameValue in Expected
    ]
    if NameValue in ("coincident", "radius"):
        Coincident = Relations[-1]
        assert Coincident.attributes["fusion.constraint_argument_ids"] == (230, 236)
        assert [
            (RefValue.entity_id, RefValue.point) for RefValue in Coincident.references
        ] == [
            ("fusion-sketch-entity-230", "start"),
            ("fusion-sketch-entity-236", "start"),
        ]
        assert (
            Coincident.provenance is not None
            and Coincident.provenance.native_id == "282"
        )
        assert len(Coincident.provenance.spans) == 2
    Updated = Replace(DocValue, sketches=(Replace(SketchValue, constraints=Relations),))
    assert Updated.validate() == ()
    assert CadDocument.from_json(Updated.to_json()) == Updated


# advanced role order keeps midpoint and point symmetry distinct from whole curve relations
@KRequiresCodec
def CheckMoreRules() -> None:
    DocValue, BulkData, Spans = ReadCase(KAdvancedSketch.name, "advanced")
    BySketch, Diagnostics = BuildGeomRules(BulkData, Spans, DocValue.sketches)
    Oracle = LoadJson(
        (KAdvancedSketch / "ground_truth.json").read_text(encoding="utf-8")
    )
    Captured = {
        ItemValue["name"]: ItemValue["constraints"] for ItemValue in Oracle["sketches"]
    }
    Expected = {
        "Parallel": ("parallel", ("", ""), "ParallelConstraint"),
        "Perpendicular": ("perpendicular", ("", ""), "PerpendicularConstraint"),
        "Equal": ("equal", ("", ""), "EqualConstraint"),
        "Collinear": ("collinear", ("", ""), "CollinearConstraint"),
        "Concentric": ("concentric", ("", ""), "ConcentricConstraint"),
        "Tangent": ("tangent", ("", ""), "TangentConstraint"),
        "MidPoint": ("midpoint", ("start", ""), "MidPointConstraint"),
        "HorizontalPoints": (
            "horizontal",
            ("start", "start"),
            "HorizontalPointsConstraint",
        ),
        "VerticalPoints": ("vertical", ("start", "start"), "VerticalPointsConstraint"),
        "Symmetry": ("symmetric", ("start", "start", ""), "SymmetryConstraint"),
    }
    for SketchValue in DocValue.sketches:
        Relations = BySketch[SketchValue.id]
        if SketchValue.name not in Expected:
            assert not Relations
            continue
        KindValue, Points, ApiName = Expected[SketchValue.name]
        assert Captured[SketchValue.name] == [ApiName]
        (Relation,) = Relations
        assert Relation.kind == KindValue
        assert tuple(RefValue.point for RefValue in Relation.references) == Points
        if KindValue == "midpoint":
            assert Relation.attributes["fusion.constraint_dependency_ids"] == (697, 701)
            assert Relation.attributes["fusion.constraint_argument_ids"] == (701, 697)
    assert len(Diagnostics) == 4
    assert all(
        Issue.code == "fusion.sketch.constraint.unsupported" for Issue in Diagnostics
    )


# malformed native claims cannot replace the authenticated argument roles or ownership
@KRequiresCodec
@Pytest.mark.parametrize("GuardName", ("owner", "roles", "missing", "tail"))
def CheckRuleGuards(GuardName: str) -> None:
    DocValue, BulkData, Spans = ReadCase(KBasicSketch.name, "coincident")
    Relation = next(
        SpanValue
        for SpanValue in Spans
        if SpanValue.IsPrimary and SpanValue.ObjectId == 282
    )
    RootSpan = next(
        SpanValue
        for SpanValue in Spans
        if SpanValue.IsPrimary and SpanValue.ObjectId == 202
    )
    Start = Relation.PayloadOffset + 4
    Cursor = MetaCursor(BulkData[Start : Relation.EndOffset])
    _ = ReadRulePrefix(Cursor)
    if GuardName == "owner":
        Offset, Content = Start + Cursor.Offset, MakeReference(203)
    elif GuardName == "roles":
        Offset = Start + Cursor.Offset + 23
        Content = MakeReference(236) + MakeReference(230)
    elif GuardName == "missing":
        Offset = BulkData.index(
            MakeReference(282), RootSpan.PayloadOffset + 4, RootSpan.EndOffset
        )
        Content = MakeReference(100000)
    else:
        Offset, Content = Relation.EndOffset - 1, b"\1"
    Invalid = BulkData[:Offset] + Content + BulkData[Offset + len(Content) :]
    BySketch, Diagnostics = BuildGeomRules(Invalid, Spans, DocValue.sketches)
    assert tuple(RuleValue.kind for RuleValue in BySketch[DocValue.sketches[0].id]) == (
        "horizontal",
        "vertical",
    )
    assert (
        len(Diagnostics) == 1
        and Diagnostics[0].code == "fusion.sketch.constraint.unsupported"
    )


# a point selected against a whole curve has a distinct native solver role
@KRequiresCodec
def CheckPointCurve() -> None:
    DocValue, BulkData, Spans = ReadCase(KBasicSketch.name, "coincident")
    Relation = next(
        SpanValue
        for SpanValue in Spans
        if SpanValue.IsPrimary and SpanValue.ObjectId == 282
    )
    Start = Relation.PayloadOffset + 4
    BodyValue = bytearray(BulkData[Start : Relation.EndOffset])
    Cursor = MetaCursor(bytes(BodyValue))
    _ = ReadRulePrefix(Cursor)
    BodyValue[5:16] = MakeReference(240)
    BodyValue[20:31] = MakeReference(230)
    ArgStart = Cursor.Offset + 23
    BodyValue[ArgStart : ArgStart + 22] = MakeReference(230) + MakeReference(240)
    Changed = BulkData[:Start] + bytes(BodyValue) + BulkData[Relation.EndOffset :]
    BySketch, Diagnostics = BuildGeomRules(Changed, Spans, DocValue.sketches)
    RuleValue = BySketch[DocValue.sketches[0].id][-1]
    assert not Diagnostics
    assert RuleValue.kind == "point_on_object"
    assert [
        (RefValue.entity_id, RefValue.point) for RefValue in RuleValue.references
    ] == [
        ("fusion-sketch-entity-230", "start"),
        ("fusion-sketch-entity-240", ""),
    ]
