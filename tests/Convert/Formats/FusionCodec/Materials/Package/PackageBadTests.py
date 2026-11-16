from pathlib import Path as FilePath

from pytest import mark as MarkTests, raises as ExpectError

from convert.Formats.Fusion.MaterialCodec.Package.ReadPackage import ReadPackage
from tests.Convert.Formats.FusionCodec.Materials.Package.ChangePackage import (
    ChangePackage,
)
from tests.Convert.Formats.FusionCodec.Materials.Package.NativePackage import (
    NativePackage,
)


# the reject pack contract needs boundary coverage so stored document relationships remain consistent
@MarkTests.parametrize(
    "ModeName", ("extra", "version", "schema", "doctype", "resource")
)
def TestRejectPack(TmpPath: FilePath, ModeName: str) -> None:
    Target = TmpPath / "Malformed.protein"
    _ = Target.write_bytes(ChangePackage(NativePackage(), ModeName))
    with ExpectError(ValueError):
        _ = ReadPackage(Target.read_bytes())
