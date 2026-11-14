from pathlib import Path as FilePath

from pytest import mark as MarkTests
from pytest import raises as RaisesError

from convert.formats.Fusion.DocumentCodec.EmitDocument import EmitDocument
from convert.formats.Fusion.DocumentCodec.Model.DocumentSpec import DocumentSpec


@MarkTests.parametrize(
    "Degrees", (float("nan"), float("inf"), -90.0, 90.0, -45.0, 1e-20, True)
)
def TestBadTaper(TmpPath: FilePath, Degrees: float) -> None:
    Target = TmpPath / "Rejected.f3d"
    with RaisesError(ValueError):
        _ = Target.write_bytes(
            EmitDocument(
                DocumentSpec(
                    "Invalid taper",
                    "frustumHeight",
                    17.0,
                    ProfileKind="frustum",
                    RadiusMm=10.0,
                    TaperDegrees=Degrees,
                )
            )
        )
    assert not Target.exists()


def TestTaperKind(TmpPath: FilePath) -> None:
    Target = TmpPath / "WrongProfile.f3d"
    with RaisesError(ValueError, match="requires the frustum"):
        _ = Target.write_bytes(
            EmitDocument(
                DocumentSpec(
                    "Wrong profile",
                    "frustumHeight",
                    17.0,
                    TaperDegrees=7.0,
                )
            )
        )
    assert not Target.exists()
