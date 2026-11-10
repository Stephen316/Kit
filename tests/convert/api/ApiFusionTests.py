# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from io import BytesIO as ByteStream
from pathlib import Path as FilePath
from zipfile import ZipFile

import pytest as Pytest

from tests.convert.FusionRead import OpenResearch as OpenDocument
from convert import write_document as WriteDocument
from convert.adapters import AdapterNotFoundError
from convert.adapters.Fusion.Adapter import FusionReader
from convert.formats.Fusion.DesignZip import KDesignPrefix
from interchange.document.models.DocumentModel import CadDocument
from tests.convert.formats.FusionHistoryTests import HistoryArchive
from tests.convert.formats.JsonTests import NonSeekable


# explicit aliases and signature detection should expose the same partial native document
def CheckFusionRead(TmpPath: FilePath) -> None:
    Archive = HistoryArchive()
    SourcePath = TmpPath / "sample.f3d"
    _ = SourcePath.write_bytes(Archive)
    Document = OpenDocument(
        Archive, SourceFormat="f3d", Configuration="104", StrictMode=False
    )
    Detected = OpenDocument(SourcePath, Configuration="104", StrictMode=False)
    assert Document.source.format_id == Detected.source.format_id == "fusion.f3d"
    assert Document.source.sha256 == Detected.source.sha256
    assert Document.feature_timeline == Detected.feature_timeline
    assert Document.feature_timeline[0].name == "Test sweep"
    assert Document.metadata["fusion.history_id"] == 104
    assert any(
        ItemValue.code == "fusion.history.partial" for ItemValue in Document.diagnostics
    )
    assert Document.brep_payloads[0].data == Archive
    assert CadDocument.from_json(Document.to_json()) == Document
    with Pytest.raises(ValueError, match="strict=False"):
        _ = OpenDocument(SourcePath, Configuration="104")
    with Pytest.raises(ValueError, match="Fusion history"):
        _ = OpenDocument(
            Archive, SourceFormat="fusion.f3d", Configuration="999", StrictMode=False
        )


# recognition should inspect archive metadata without opening compressed design members
def RejectMember(*Values: object, **Keywords: object) -> None:
    raise AssertionError("Fusion probe must not open ZIP member contents")


# a seekable source can be shared with other probes and resume at the same byte
def CheckFusProbe(MonkeyPatch: Pytest.MonkeyPatch) -> None:
    Reader = FusionReader()
    Prefix = b"prefix:"
    Source = ByteStream(Prefix + HistoryArchive())
    _ = Source.seek(len(Prefix))
    MissingMember = ByteStream(Prefix)
    with ZipFile(MissingMember, "a") as Archive:
        Archive.writestr(KDesignPrefix + "BulkStream.dat", b"not design data")
    _ = MissingMember.seek(len(Prefix))
    MonkeyPatch.setattr(ZipFile, "open", RejectMember)
    Probe = Reader.probe(Source)
    assert Probe.format_id == "fusion.f3d"
    assert Probe.confidence > 0.0
    assert Source.tell() == len(Prefix)
    assert Reader.probe(MissingMember).confidence == 0.0
    assert MissingMember.tell() == len(Prefix)


# registry replay keeps one shot inputs and seekable suffixes readable after detection
def CheckFusStream() -> None:
    Archive = HistoryArchive()
    Prefix = b"prefix:"
    Source = ByteStream(Prefix + Archive)
    _ = Source.seek(len(Prefix))
    Document = OpenDocument(Source, Configuration="104", StrictMode=False)
    assert Source.tell() == len(Prefix) + len(Archive)
    assert Document == OpenDocument(
        NonSeekable(Archive), Configuration="104", StrictMode=False
    )


# a reader only format cannot claim output or create a target file
def CheckFusWriter(TmpPath: FilePath) -> None:
    Document = OpenDocument(HistoryArchive(), SourceFormat="f3d", StrictMode=False)
    TargetPath = TmpPath / "blocked.f3d"
    for FormatId in ("fusion.f3d", "f3d"):
        with Pytest.raises(AdapterNotFoundError, match="no writer registered"):
            _ = WriteDocument(Document, TargetPath, destination_format=FormatId)
    with Pytest.raises(AdapterNotFoundError, match="no writer supports"):
        _ = WriteDocument(Document, TargetPath)
    assert tuple(TmpPath.iterdir()) == ()
