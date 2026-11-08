# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from dataclasses import replace as Replace
from json import loads as LoadJson

import pytest as Pytest

from convert import open_document as OpenDocument
from convert.formats.Fusion.Assembly.ComponentRead import KComponentGuid
from convert.formats.Fusion.Assembly.OccurrenceRead import KOccurrenceGuid
from convert.formats.Fusion.DesignZip import ReadDesignZip
from convert.formats.Fusion.FormulaDeps.FormulaLink import LinkFormulaDeps
from convert.formats.Fusion.FormulaDeps.ParamRegistry import KParamRegistry
from convert.formats.Fusion.NativeHistory import KHistoryGuid
from convert.formats.Fusion.ZipHistory import ReadBulkHistory
from interchange.document.models.DocumentModel import CadDocument
from interchange.features.FeatureDistExt import DistanceExtrude
from tests.convert.api.ApiFusionAssemblyTests import KRequiresCodec, KStudyPath

# captured getters independently identify source names and saved parameter values
KFormulaStudy = KStudyPath / "parameterexpressions-3ddbef2b20bd"


# saved native getters prove stable names even when one input is repeated in the formula
@KRequiresCodec
@Pytest.mark.parametrize(
    "CaptureName",
    (
        "product_sum.f3d",
        "parenthesized.f3d",
        "unary_reference.f3d",
        "repeated_reference.f3d",
        "function_outside_subset.f3d",
    ),
)
def CheckSavedGraph(CaptureName: str) -> None:
    Oracle = LoadJson((KFormulaStudy / "ground_truth.json").read_text(encoding="utf-8"))
    Capture = next(Entry for Entry in Oracle["samples"] if Entry["file"] == CaptureName)
    Document = OpenDocument(KFormulaStudy / CaptureName, strict=False)
    Parameters = {Param.name: Param for Param in Document.parameters}
    Expected = next(
        Entry for Entry in Capture["parameters"] if Entry["name"] == "probeResult"
    )
    Result = Parameters["probeResult"]
    assert Result.value.value == Pytest.approx(Expected["value"])
    assert Result.expression is not None
    assert Result.expression.source == Expected["expression"]
    ExpectedNames = (
        ()
        if CaptureName == "function_outside_subset.f3d"
        else Expected["dependency_names"]
    )
    assert set(Result.expression.parameter_ids) == {
        Parameters[NameValue].id for NameValue in ExpectedNames
    }
    assert len(Result.expression.parameter_ids) == len(ExpectedNames)
    assert CadDocument.from_json(Document.to_json()) == Document


# equal saved numbers cannot substitute for the exact native named dependency
@KRequiresCodec
@Pytest.mark.parametrize(
    ("CaptureName", "LinkedName"),
    (("02_alpha_reference", "alpha"), ("03_bravo_reference", "bravo")),
)
def CheckNamedId(CaptureName: str, LinkedName: str) -> None:
    Folder = KStudyPath / "parameteridentity-8fc83529b236"
    Document = OpenDocument(Folder / f"{CaptureName}.f3d", strict=False)
    Parameters = {Param.name: Param for Param in Document.parameters}
    assert Parameters["alpha"].value == Parameters["bravo"].value
    Expression = Parameters["result"].expression
    assert Expression is not None
    assert Expression.parameter_ids == (Parameters[LinkedName].id,)


# a live extrusion distance keeps the native ownership and linked user parameter
@KRequiresCodec
def CheckDepthGraph() -> None:
    Folder = KStudyPath / "holdouts-f8c508a73323"
    Document = OpenDocument(Folder / "expression_depth.f3d", strict=False)
    Feature = Document.feature_timeline[-1]
    assert isinstance(Feature.definition, DistanceExtrude)
    Parameters = {Param.id: Param for Param in Document.parameters}
    Depth = Parameters[Feature.definition.AlongParameterId]
    assert Depth.owner_id == Feature.id
    assert Depth.value.value == Pytest.approx(1.925)
    assert Depth.expression is not None
    assert Depth.expression.source == "probeDepth * 2 + 1 mm"
    assert Depth.expression.parameter_ids == ("fusion-parameter-202",)
    assert Parameters[Depth.expression.parameter_ids[0]].name == "probeDepth"


# cached values and a validated input chain are required before exposing any expression edge
@KRequiresCodec
@Pytest.mark.parametrize(
    ("Sources", "Linked"),
    (
        ({"probeWidth": "probeAllowance + 6.1 mm"}, ("probeWidth", "probeResult")),
        ({"probeWidth": "probeWidth"}, ()),
        ({"probeWidth": "probeAllowance + 6.2 mm"}, ()),
        ({"probeWidth": "probeAllowance + 6.1"}, ()),
        ({"probeWidth": "probeallowance + 6.1 mm"}, ()),
        (
            {
                "probeWidth": "probeAllowance + 6.1 mm",
                "probeAllowance": "probeWidth - 6.1 mm",
            },
            (),
        ),
    ),
)
def CheckGuards(Sources: dict[str, str], Linked: tuple[str, ...]) -> None:
    BulkData, Spans = ReadDesignZip((KFormulaStudy / "product_sum.f3d").read_bytes())
    Parts, Parameters, _ = ReadBulkHistory(BulkData, Spans)
    Updated = tuple(
        (
            Replace(
                Param, expression=Replace(Param.expression, source=Sources[Param.name])
            )
            if Param.name in Sources and Param.expression is not None
            else Param
        )
        for Param in Parameters
    )
    Results = LinkFormulaDeps(BulkData, Spans, Parts[0], Updated)
    assert (
        tuple(
            Param.name
            for Param in Results
            if Param.expression and Param.expression.parameter_ids
        )
        == Linked
    )
    for Original, Result in zip(Updated, Results, strict=True):
        assert Original.expression is not None and Result.expression is not None
        assert Original.expression.source == Result.expression.source
        assert Original.value == Result.value


# contradictory native names cannot be hidden by a successful arithmetic evaluation
@KRequiresCodec
def CheckNameGuard() -> None:
    BulkData, Spans = ReadDesignZip((KFormulaStudy / "product_sum.f3d").read_bytes())
    Parts, Parameters, _ = ReadBulkHistory(BulkData, Spans)
    Registry = next(
        SpanValue
        for SpanValue in Spans
        if SpanValue.IsPrimary and SpanValue.ClassGuid == KParamRegistry
    )
    NameStart = BulkData.index(
        "probeScale".encode("utf-16le"), Registry.PayloadOffset, Registry.EndOffset
    )
    Duplicate = "probeWidth".encode("utf-16le")
    Invalid = BulkData[:NameStart] + Duplicate + BulkData[NameStart + len(Duplicate) :]
    assert LinkFormulaDeps(Invalid, Spans, Parts[0], Parameters) == Parameters


# selecting one history cannot make another component or history disappear from name scope
@KRequiresCodec
@Pytest.mark.parametrize("ClassGuid", (KComponentGuid, KHistoryGuid, KOccurrenceGuid))
def CheckScopeGuard(ClassGuid: str) -> None:
    BulkData, Spans = ReadDesignZip((KFormulaStudy / "product_sum.f3d").read_bytes())
    Parts, Parameters, _ = ReadBulkHistory(BulkData, Spans)
    Existing = next(
        SpanValue
        for SpanValue in Spans
        if SpanValue.IsPrimary and SpanValue.ClassGuid == ClassGuid
    )
    OtherScope = Replace(
        Existing, ObjectId=max(SpanValue.ObjectId for SpanValue in Spans) + 1
    )
    assert (
        LinkFormulaDeps(BulkData, Spans + (OtherScope,), Parts[0], Parameters)
        == Parameters
    )
