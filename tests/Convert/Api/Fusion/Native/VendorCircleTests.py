# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from hashlib import sha256 as HashBytes
from pathlib import Path as FilePath

from pytest import mark as MarkTests, raises as RaisesError

from convert.adapters.Fusion.Native.Graph.BuildGraph import BuildGraph
from convert.api.ApiOpen import OpenDocument
from convert.Formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from interchange.Enums.EnumGeometry import GeometryKind
from interchange.geometry.Models.GeometryCurves import CircleGeometry
from tests.Convert.Api.Fusion.Native.ChangeNative import ChangeField

# the oracle binds each independently reopened circle to its complete native archive
KCircleCases = (
    (
        "vendor_NativeCircleControl.f3d",
        "949acf09b31e2cc9a4cb92a68e19de616e7501b32d80a23c93925c8d1f182d08",
    ),
    (
        "vendor_NativeCircleReemitted.f3d",
        "d28603eed2249dc9fa17f8eba8e0d1046b1f8b7416133040f5e470f85bf879d0",
    ),
)


# verify the source identity before attributing the recorded native measurements
def ReadCircle(CaseValue: tuple[str, str]) -> bytes:
    FileName, ExpectedDigest = CaseValue
    SourcePath = (
        FilePath(__file__).resolve().parents[5]
        / "re/Fusion/LocalOracle/RotationalDocuments"
        / FileName
    )
    Payload = SourcePath.read_bytes()
    assert HashBytes(Payload).hexdigest() == ExpectedDigest
    return Payload


# strict projection must preserve the single native circle recovered after reopening
@MarkTests.parametrize("CaseValue", KCircleCases)
def TestSavedCircle(CaseValue: tuple[str, str]) -> None:
    Document = OpenDocument(ReadCircle(CaseValue), SourceFormat="fusion.f3d")
    assert len(Document.sketches) == len(Document.feature_timeline) == 1
    assert not Document.bodies and not Document.diagnostics
    SketchValue = Document.sketches[0]
    Circles = tuple(
        Value for Value in SketchValue.entities if Value.kind == GeometryKind.KCircle
    )
    assert len(Circles) == 1
    Circle = Circles[0]
    Geometry = Circle.geometry
    assert isinstance(Geometry, CircleGeometry)
    assert (Geometry.center.x, Geometry.center.y, Geometry.radius) == (0.0, 0.0, 16.0)
    assert SketchValue.closed_profile_entity_ids == ((Circle.id,),)


# a nondefault mesh container cannot qualify through the empty scaffold route
def TestEmptyMesh() -> None:
    Model = ReadDocument(ReadCircle(KCircleCases[0]))
    Scaffold = BuildGraph(Model).OneClass("ParaMeshBodies")
    Changed = ChangeField(Model, Scaffold.ObjectId, "isVisible", False)
    with RaisesError(
        ValueError, match=r"Unsupported native Fusion ParaMeshBodies\.isVisible"
    ):
        _ = OpenDocument(EmitParsed(Changed), SourceFormat="fusion.f3d")
