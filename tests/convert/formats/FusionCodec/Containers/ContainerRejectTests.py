from tests.convert.formats.FusionCodec.Containers.MutateZipMut import (
    MutateZipMut,
)
from dataclasses import replace as Replace
from io import BytesIO
from pathlib import Path as FilePath
from zipfile import ZipFile

from pytest import mark as TestMarks, raises as RaiseError

from convert.formats.Fusion.ContainerCodec.EmitContainer import EmitContainer
from convert.formats.Fusion.ContainerCodec.Model.ContainerPart import ContainerPart
from convert.formats.Fusion.ContainerCodec.ReadContainer import ReadContainer
from tests.convert.formats.FusionCodec.Containers.MakeContainer import MakeContainer


@TestMarks.parametrize(
    "Mutation",
    (
        "directory",
        "unknown",
        "case_alias",
        "identity",
        "watermark",
        "offsets",
        "preview",
    ),
)
def TestRejectFile(TmpPath: FilePath, Mutation: str) -> None:
    Source = EmitContainer(MakeContainer())
    with ZipFile(BytesIO(Source)) as Archive:
        Members = {Entry.filename: Archive.read(Entry) for Entry in Archive.infolist()}
    MutateZipMut(Members, Mutation)
    Target = TmpPath / "Malformed.f3d"
    with ZipFile(Target, "w") as Archive:
        for NameValue, Payload in Members.items():
            Archive.writestr(NameValue, Payload)
    with RaiseError(ValueError):
        _ = ReadContainer(Target.read_bytes())


@TestMarks.parametrize(
    "PartName",
    (
        "../Escape",
        "Images.BlobParts/../Escape",
        "Images.BlobParts/CON.png",
        "Images.BlobParts/Independent.png",
    ),
)
def TestRejectParts(TmpPath: FilePath, PartName: str) -> None:
    Value = MakeContainer()
    Invalid = Replace(Value, Parts=(*Value.Parts, ContainerPart(PartName, b"")))
    Target = TmpPath / "Invalid.f3d"
    with RaiseError(ValueError):
        _ = Target.write_bytes(EmitContainer(Invalid))
    assert not Target.exists()
