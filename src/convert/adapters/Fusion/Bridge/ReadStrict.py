from collections.abc import Callable
from hashlib import sha256 as HashBytes
from pathlib import Path
from typing import cast as CastValue

from convert.adapters.base.ContractTypes import KSourceType
from convert.adapters.base.ReadOptions import ReadOptions
from convert.adapters.Fusion.Projection.ProjectNative import ProjectNative
from convert.adapters.Fusion.StreamRead import ReadSourceMut
from convert.formats.Fusion.ArchiveRead.ArchiveBounds import KArchiveLimit
from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from interchange.document.models.DocumentModel import CadDocument
from interchange.records.RecordSource import CadSource


def ReadStrict(SourceData: KSourceType, Settings: ReadOptions) -> CadDocument:
    if (
        Settings.configuration is not None
        or not Settings.include_brep
        or set(Settings.values) - {"fusion.inflate_zstd"}
    ):
        raise ValueError(
            "Strict Fusion reading requires the complete qualified document; use strict=False for the partial legacy reader"
        )
    Inflate = Settings.values.get("fusion.inflate_zstd")
    if Inflate is not None and not callable(Inflate):
        raise ValueError("Fusion inflation option must be callable")
    Loaded = ReadSourceMut(SourceData)
    PathValue = "" if isinstance(Loaded, bytes) else str(Loaded)
    if isinstance(Loaded, bytes):
        Payload = Loaded
    else:
        with Path(Loaded).open("rb") as Stream:
            Payload = Stream.read(KArchiveLimit + 1)
    if len(Payload) > KArchiveLimit:
        raise ValueError("Fusion ZIP exceeds input size limit")
    ModelValue = ReadDocument(
        Payload, CastValue(Callable[[bytes, int], bytes] | None, Inflate)
    )
    Source = CadSource("fusion.f3d", PathValue, HashBytes(Payload).hexdigest())
    return ProjectNative(ModelValue, Source)
