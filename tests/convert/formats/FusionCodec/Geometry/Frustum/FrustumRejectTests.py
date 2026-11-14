from pathlib import Path as FilePath

from pytest import mark as TestMarks, raises as RaiseError

from convert.formats.Fusion.GeometryCodec.Frustum.EmitFrustumSmb import EmitFrustumSmb
from convert.formats.Fusion.GeometryCodec.Frustum.EmitFrustumSmt import EmitFrustumSmt
from convert.formats.Fusion.GeometryCodec.Frustum.FrustumBody import FrustumBody
from convert.formats.Fusion.GeometryCodec.GeometryStamp import GeometryStamp


@TestMarks.parametrize(
    "Lengths,BasePoint",
    (
        ((0.0, 2.0, 3.0), (0.0, 0.0, 0.0)),
        ((2.0, 0.0, 3.0), (0.0, 0.0, 0.0)),
        ((2.0, -1.0, 3.0), (0.0, 0.0, 0.0)),
        ((2.0, 1.0, 0.0), (0.0, 0.0, 0.0)),
        ((2.0, float("nan"), 3.0), (0.0, 0.0, 0.0)),
        ((2.0, 1.0, float("inf")), (0.0, 0.0, 0.0)),
        ((2.0, 1.0, 3.0), (float("inf"), 0.0, 0.0)),
        ((2.0, 1.0, 3.0), (1e30, 0.0, 0.0)),
        ((2.0, 1.0, 3.0), (0.0, 0.0, 1e30)),
        ((5e-324, 1.0, 3.0), (0.0, 0.0, 0.0)),
        ((1.0, 1e308, 5e-323), (0.0, 0.0, 0.0)),
    ),
)
def TestFrustumDeny(
    TmpPath: FilePath,
    Lengths: tuple[float, float, float],
    BasePoint: tuple[float, float, float],
) -> None:
    Stamp = GeometryStamp("Kit", "Frustum rejection", "2026-11-12T00:00:00Z")
    for Emitter, Suffix in ((EmitFrustumSmb, "smb"), (EmitFrustumSmt, "smt")):
        Target = TmpPath / f"RejectedFrustum.{Suffix}"
        with RaiseError(ValueError):
            Payload = Emitter(FrustumBody(*Lengths, BasePoint), Stamp)
            _ = Target.write_bytes(Payload)
        assert not Target.exists()
