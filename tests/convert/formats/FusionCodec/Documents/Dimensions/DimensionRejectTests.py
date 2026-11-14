from pathlib import Path as FilePath

from pytest import mark as MarkTests
from pytest import raises as RaisesError

from convert.formats.Fusion.DocumentCodec.EmitDocument import EmitDocument
from convert.formats.Fusion.DocumentCodec.Model.DocumentSpec import DocumentSpec


@MarkTests.parametrize(
    "WidthName,DepthName",
    (
        ("", "boxDepth"),
        ("d2", "boxDepth"),
        ("d6", "boxDepth"),
        ("same", "same"),
        ("boxHeight", "boxDepth"),
        ("bad-name", "boxDepth"),
    ),
)
def TestDimNames(TmpPath: FilePath, WidthName: str, DepthName: str) -> None:
    Target = TmpPath / "Rejected.f3d"
    with RaisesError(ValueError, match="parameter name"):
        _ = Target.write_bytes(
            EmitDocument(
                DocumentSpec(
                    "Invalid dimension names",
                    "boxHeight",
                    31.0,
                    ProfileKind="cuboid",
                    ConstrainRectangle=True,
                    WidthParamName=WidthName,
                    DepthParamName=DepthName,
                )
            )
        )
    assert not Target.exists()


def TestDimProfile(TmpPath: FilePath) -> None:
    Target = TmpPath / "WrongProfile.f3d"
    with RaisesError(ValueError, match="rectangle or cuboid"):
        _ = Target.write_bytes(
            EmitDocument(
                DocumentSpec(
                    "Invalid profile",
                    "boxHeight",
                    31.0,
                    ConstrainRectangle=True,
                )
            )
        )
    assert not Target.exists()


@MarkTests.parametrize("Selection", (1, None, "yes"))
def TestDimBoolean(TmpPath: FilePath, Selection: bool) -> None:
    Target = TmpPath / "WrongBoolean.f3d"
    with RaisesError(ValueError, match="must be Boolean"):
        _ = Target.write_bytes(
            EmitDocument(
                DocumentSpec(
                    "Invalid selector",
                    "boxHeight",
                    31.0,
                    ProfileKind="rectangle",
                    ConstrainRectangle=Selection,
                )
            )
        )
    assert not Target.exists()
