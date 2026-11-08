# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from dataclasses import replace as Replace
from pathlib import Path as FilePath
from zipfile import ZipFile

import pytest as Pytest

from convert import ApplicationUsabilityError
from convert import open_document as OpenDocument
from convert import write_document as WriteDocument
from interchange.document.models.DocumentModel import CadDocument
from interchange.enums.EnumDocument import Capability
from interchange.enums.EnumFeatures import BooleanOp, FeatureKind
from interchange.features.DistanceValues import GetDistValues
from interchange.features.FeatureDistExt import DistanceExtrude
from tests.convert.api.ApiFusionAssemblyTests import KRequiresCodec, KStudyPath


# oracle bounds distinguish signed distance offset and symmetric conventions
@KRequiresCodec
@Pytest.mark.parametrize(
    ("Folder", "ArchiveName", "SideMode", "Bounds"),
    (
        ("extents-f0f33a9a605f", "distance_negative", "one_sided", (-17, 0)),
        ("extents-f0f33a9a605f", "offset_positive", "one_sided", (7, 24)),
        ("extents-f0f33a9a605f", "offset_negative", "one_sided", (-9, 8)),
        ("models-b8a640dbddc6", "symmetric_full", "symmetric_full", (-12, 12)),
        ("models-b8a640dbddc6", "symmetric_half", "symmetric_half", (-24, 24)),
        ("models-b8a640dbddc6", "two_sided", "two_sided", (-23, 11)),
    ),
)
def CheckExtents(
    Folder: str, ArchiveName: str, SideMode: str, Bounds: tuple[float, float]
) -> None:
    Document = OpenDocument(KStudyPath / Folder / f"{ArchiveName}.f3d", strict=False)
    StepValue = Document.feature_timeline[-1]
    Definition = StepValue.definition
    assert isinstance(Definition, DistanceExtrude)
    assert StepValue.operation == BooleanOp.KCreate and Definition.SideMode == SideMode
    assert (Definition.Direction.x, Definition.Direction.y, Definition.Direction.z) == (
        0,
        0,
        1,
    )
    Parameters = {Param.id: Param for Param in Document.parameters}
    Values = GetDistValues(StepValue, Definition, Parameters)
    assert (Values.LowerMm, Values.UpperMm) == Pytest.approx(Bounds)
    if SideMode.startswith("symmetric_"):
        assert Definition.TaperParameterId == Definition.SecondTaperId
    assert CadDocument.from_json(Document.to_json()) == Document


# editing the bound parameter changes the evaluated extent without rebuilding its definition
@KRequiresCodec
def CheckExtEdit() -> None:
    Folder = KStudyPath / "extents-f0f33a9a605f"
    Document = OpenDocument(Folder / "taper.f3d", strict=False)
    StepValue = Document.feature_timeline[-1]
    Definition = StepValue.definition
    assert isinstance(Definition, DistanceExtrude)
    Parameters = {Param.id: Param for Param in Document.parameters}
    Along = Parameters[Definition.AlongParameterId]
    Parameters[Along.id] = Replace(Along, value=Replace(Along.value, value=3.4))
    Updated = Replace(Document, parameters=tuple(Parameters.values()))
    Values = GetDistValues(StepValue, Definition, Parameters)
    assert Values.UpperMm == Pytest.approx(34)
    assert Values.TaperRadians == Pytest.approx(0.12217304763960307)
    assert Updated.validate() == ()


# owned formulas stay attached to the distance instead of being copied into its definition
@KRequiresCodec
def CheckExtFormula() -> None:
    Document = OpenDocument(
        KStudyPath / "holdouts-f8c508a73323" / "expression_depth.f3d", strict=False
    )
    StepValue = Document.feature_timeline[-1]
    Definition = StepValue.definition
    assert isinstance(Definition, DistanceExtrude)
    Parameters = {Param.id: Param for Param in Document.parameters}
    Along = Parameters[Definition.AlongParameterId]
    assert (
        Along.expression is not None
        and Along.expression.source == "probeDepth * 2 + 1 mm"
    )
    assert GetDistValues(StepValue, Definition, Parameters).UpperMm == Pytest.approx(
        19.25
    )


# closed thin profiles must not acquire ordinary solid extrusion semantics
@KRequiresCodec
def CheckThinGuard() -> None:
    Folder = KStudyPath / "thinextrudes-c1632bcb5efe"
    Document = OpenDocument(Folder / "closed_center.f3d", strict=False)
    StepValue = Document.feature_timeline[-1]
    assert StepValue.kind == FeatureKind.KExtrusion
    assert not isinstance(StepValue.definition, DistanceExtrude)
    assert any(
        Item.code == "fusion.extrude.unsupported" for Item in Document.diagnostics
    )


# an unimplemented target writer must keep linked definitions out of executable geometry
@KRequiresCodec
@Pytest.mark.parametrize(
    ("Capture", "Reason"),
    (
        ("distance_positive", b"linked_distance_definition_unsupported"),
        ("to_plane", b"linked_plane_definition_unsupported"),
    ),
)
def CheckExtWrite(TmpPath: FilePath, Capture: str, Reason: bytes) -> None:
    Folder = KStudyPath / "extents-f0f33a9a605f"
    Document = OpenDocument(Folder / f"{Capture}.f3d", strict=False)
    Target = TmpPath / "extrude.FCStd"
    with Pytest.raises(ApplicationUsabilityError):
        WriteDocument(Document, Target, allow_carrier=False)
    assert not Target.exists()
    Result = WriteDocument(Document, Target)
    assert not Result.IsNearLossless
    assert Capability.KParamHistory in Result.CarrierCaps
    with ZipFile(Target) as Archive:
        ModelXml = Archive.read("Document.xml")
    assert b'type="Part::Extrusion"' not in ModelXml
    assert Reason in ModelXml
