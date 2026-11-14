from hashlib import sha256 as HashBytes
from math import pi as KPiValue, radians as Radians, tan as Tangent
from pathlib import Path as FilePath

from pytest import approx as NearValue, mark as MarkTests

from convert import open_document as OpenDocument, write_document as WriteDocument
from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from interchange import CadDocument
from interchange.geometry.models.GeometryCurves import CircleGeometry
from interchange.features.FeatureDistExt import DistanceExtrude
from tests.convert.api.Fusion.Rotational.RotaryCase import (
    KRotaryCases,
    RotaryCase,
    RotarySource,
)


@MarkTests.parametrize("CaseValue", KRotaryCases)
def TestRotaryRound(TmpPath: FilePath, CaseValue: RotaryCase) -> None:
    Source = RotarySource(CaseValue)
    Document = OpenDocument(Source)
    Circle = Document.sketches[0].entities[-1].geometry
    assert isinstance(Circle, CircleGeometry)
    assert Circle.radius == CaseValue.RadiusMm
    assert Document.sketches[0].id == "fusion:0:1089"
    assert Document.parameters[0].name == "publicHeight"
    assert Document.parameters[0].value.value == 21.0
    assert not Document.brep_payloads and not Document.diagnostics
    if CaseValue.BodyId is None:
        assert not Document.bodies and not Document.materials
        assert len(Document.feature_timeline) == 1
    else:
        VerifyRotary(Document, CaseValue)
    Neutral = CadDocument.from_json(Document.to_json())
    assert Neutral == Document
    Target = TmpPath / "Rotary.f3d"
    Result = WriteDocument(
        Neutral, Target, destination_format="f3d", allow_carrier=False
    )
    assert Result.application_usable and Result.vendor_loadable
    assert HashBytes(Target.read_bytes()).hexdigest() == CaseValue.OutputDigest
    assert ReadDocument(Target.read_bytes()) == ReadDocument(Source.read_bytes())
    Reopened = OpenDocument(Target)
    assert Reopened.parameters == Document.parameters
    assert Reopened.sketches == Document.sketches
    assert Reopened.brep == Document.brep
    assert Reopened.materials == Document.materials


def VerifyRotary(Document: CadDocument, CaseValue: RotaryCase) -> None:
    assert Document.bodies[0].id == CaseValue.BodyId
    UpperRadius = CaseValue.RadiusMm + CaseValue.HeightMm * Tangent(
        Radians(CaseValue.TaperDegrees)
    )
    Volume = (
        KPiValue
        * CaseValue.HeightMm
        * (CaseValue.RadiusMm**2 + CaseValue.RadiusMm * UpperRadius + UpperRadius**2)
        / 3
    )
    assert Document.bodies[0].topology.volume == NearValue(Volume)
    assert Document.materials[0].Density == 2870.0
    assert len(Document.feature_timeline) == 2
    Definition = Document.feature_timeline[-1].definition
    assert isinstance(Definition, DistanceExtrude)
    Parameters = {Value.id: Value for Value in Document.parameters}
    assert Parameters[Definition.AlongParameterId].value.value == CaseValue.HeightMm
    assert Definition.TaperParameterId is not None
    assert Parameters[Definition.TaperParameterId].value.value == NearValue(
        Radians(CaseValue.TaperDegrees)
    )
