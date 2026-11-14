from pathlib import Path as FilePath
from zipfile import ZipFile

from convert.formats.Fusion.BrepCodec.Frustum.Models.FrustumHistory import (
    FrustumHistory,
)
from convert.formats.Fusion.BrepCodec.Frustum.ReadFrustumHist import ReadFrustumHist


def FrustumArchive(Target: FilePath, Payload: bytes) -> FrustumHistory:
    with ZipFile(Target, "w") as Archive:
        Archive.writestr("Solved.smbh", Payload)
    with ZipFile(Target) as Archive:
        return ReadFrustumHist(Archive.read("Solved.smbh"))
