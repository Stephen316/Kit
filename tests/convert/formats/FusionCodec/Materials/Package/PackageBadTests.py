from pathlib import Path as FilePath

from pytest import mark as MarkTests, raises as ExpectError

from convert.formats.Fusion.MaterialCodec.Package.ReadPackage import ReadPackage
from tests.convert.formats.FusionCodec.Materials.Package.ChangePackage import (
    ChangePackage,
)
from tests.convert.formats.FusionCodec.Materials.Package.NativePackage import (
    NativePackage,
)


@MarkTests.parametrize(
    "ModeName", ("extra", "version", "schema", "doctype", "resource")
)
def TestRejectPack(TmpPath: FilePath, ModeName: str) -> None:
    Target = TmpPath / "Malformed.protein"
    _ = Target.write_bytes(ChangePackage(NativePackage(), ModeName))
    with ExpectError(ValueError):
        _ = ReadPackage(Target.read_bytes())
