from dataclasses import replace as Replace
from pathlib import Path as FilePath

from pytest import approx as Approx, mark as TestMarks

from convert.formats.Fusion.BrepCodec.Frustum.EmitFrustumHist import EmitFrustumHist
from convert.formats.Fusion.BrepCodec.Frustum.Writing.FreshFrustum import FreshFrustum
from convert.formats.Fusion.GeometryCodec.Frustum.FrustumBody import FrustumBody
from tests.convert.formats.FusionCodec.Brep.Frustum.FrustumArchive import FrustumArchive
from tests.convert.formats.FusionCodec.Brep.SampleInputs import MakeSample


@TestMarks.parametrize("TopRadius", (8.0, 12.5, 17.0))
def TestFreshHist(TmpPath: FilePath, TopRadius: float) -> None:
    Sample = MakeSample()
    Model = FrustumBody(12.5, TopRadius, 21.75, (3.0, -4.0, 5.0))
    Payload = EmitFrustumHist(
        Model, Sample.Identity, Sample.TagSet, Sample.History, Sample.Stamp
    )
    Parsed = FrustumArchive(TmpPath / "Independent.zip", Payload)
    assert (
        Parsed.Model.BottomRadius,
        Parsed.Model.TopRadius,
        Parsed.Model.Height,
    ) == Approx((12.5, TopRadius, 21.75))
    assert Parsed.Model.BasePoint == Approx(Model.BasePoint)
    assert Parsed.Identity == Sample.Identity
    assert Parsed.TagSet == Sample.TagSet
    assert Parsed.History == Sample.History
    assert Parsed.Stamp == Sample.Stamp
    assert Parsed.Frame.Upper.Normal == (0.0, 0.0, 1.0)
    assert Parsed.Frame.Upper.SideReverse
    assert not Parsed.Frame.Upper.CapReverse
    assert Parsed.Frame.Upper.VertexIndex == 0
    assert (
        Parsed.Header.FileVersion,
        Parsed.Header.RootCount,
        Parsed.Header.Flags,
        Parsed.Header.Scale,
    ) == (23200, 2, 3, 50.0)
    assert (
        EmitFrustumHist(
            Parsed.Model,
            Parsed.Identity,
            Parsed.TagSet,
            Parsed.History,
            Parsed.Stamp,
            Parsed.Frame,
        )
        == Payload
    )


def TestScaleFrame(TmpPath: FilePath) -> None:
    Sample = MakeSample()
    Model = FrustumBody(12.5, 17.0, 21.75, (3.0, -4.0, 5.0))
    Frame = FreshFrustum(Model)
    Frame = Replace(Frame, Surface=Replace(Frame.Surface, ScaleCm=3.125))
    Payload = EmitFrustumHist(
        Model, Sample.Identity, Sample.TagSet, Sample.History, Sample.Stamp, Frame
    )
    Parsed = FrustumArchive(TmpPath / "ParameterScale.zip", Payload)
    assert Parsed.Frame == Frame
    assert Parsed.Frame.Surface.ScaleCm != Parsed.Model.BottomRadius / 10
    assert (
        EmitFrustumHist(
            Parsed.Model,
            Parsed.Identity,
            Parsed.TagSet,
            Parsed.History,
            Parsed.Stamp,
            Parsed.Frame,
        )
        == Payload
    )
