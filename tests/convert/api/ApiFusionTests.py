# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from io import BytesIO as ByteStream
from pathlib import Path as FilePath
from zipfile import ZipFile

import pytest as Pytest

from convert import open_document as OpenDocument
from convert import write_document as WriteDocument
from convert.adapters import AdapterNotFoundError
from convert.adapters import AdapterRegistry
from convert.formats.Fusion.DesignZip import KDesignPrefix
from interchange.document.models.DocumentModel import CadDocument
from tests.convert.formats.FusionHistoryTests import HistoryArchive
from tests.convert.formats.JsonTests import NonSeekable


# explicit aliases and signature detection should expose the same partial native document
def CheckFusionRead(TmpPath: FilePath) -> None:
    Archive = HistoryArchive()
    SourcePath = TmpPath / "sample.f3d"
    SourcePath.write_bytes(Archive)
    Document = OpenDocument(
        Archive, source_format="f3d", configuration="104", strict=False
    )
    Detected = OpenDocument(SourcePath, configuration="104", strict=False)
    assert Document.source.format_id == Detected.source.format_id == "fusion.f3d"
    assert Document.source.sha256 == Detected.source.sha256
    assert Document.feature_timeline == Detected.feature_timeline
    assert Document.feature_timeline[0].name == "Test sweep"
    assert Document.metadata["fusion.history_id"] == 104
    assert any(Item.code == "fusion.history.partial" for Item in Document.diagnostics)
    assert Document.brep_payloads[0].data == Archive
    assert CadDocument.from_json(Document.to_json()) == Document
    with Pytest.raises(ValueError, match="strict=False"):
        OpenDocument(SourcePath, configuration="104")
    with Pytest.raises(ValueError, match="Fusion history"):
        OpenDocument(
            Archive, source_format="fusion.f3d", configuration="999", strict=False
        )


# recognition should inspect archive metadata without opening compressed design members
def RejectMember(*Values: object, **Keywords: object) -> None:
    raise AssertionError("Fusion probe must not open ZIP member contents")


# a seekable source can be shared with other probes and resume at the same byte
def CheckFusionProbe(MonkeyPatch: Pytest.MonkeyPatch) -> None:
    Registry = AdapterRegistry()
    Registry.introspect()
    Reader = Registry.reader("f3d")
    Prefix = b"prefix:"
    Source = ByteStream(Prefix + HistoryArchive())
    Source.seek(len(Prefix))
    MissingMember = ByteStream(Prefix)
    with ZipFile(MissingMember, "a") as Archive:
        Archive.writestr(KDesignPrefix + "BulkStream.dat", b"not design data")
    MissingMember.seek(len(Prefix))
    MonkeyPatch.setattr(ZipFile, "open", RejectMember)
    Probe = Reader.probe(Source)
    assert Probe.format_id == "fusion.f3d"
    assert Probe.confidence > 0.0
    assert Source.tell() == len(Prefix)
    assert Reader.probe(MissingMember).confidence == 0.0
    assert MissingMember.tell() == len(Prefix)


# registry replay keeps one shot inputs and seekable suffixes readable after detection
def CheckFusionStream() -> None:
    Archive = HistoryArchive()
    Prefix = b"prefix:"
    Source = ByteStream(Prefix + Archive)
    Source.seek(len(Prefix))
    Document = OpenDocument(Source, configuration="104", strict=False)
    assert Source.tell() == len(Prefix) + len(Archive)
    assert Document == OpenDocument(
        NonSeekable(Archive), configuration="104", strict=False
    )


# a reader only format cannot claim output or create a target file
def CheckFusionWriter(TmpPath: FilePath) -> None:
    Document = OpenDocument(HistoryArchive(), source_format="f3d", strict=False)
    TargetPath = TmpPath / "blocked.f3d"
    for FormatId in ("fusion.f3d", "f3d"):
        with Pytest.raises(AdapterNotFoundError, match="no writer registered"):
            WriteDocument(Document, TargetPath, destination_format=FormatId)
    with Pytest.raises(AdapterNotFoundError, match="no writer supports"):
        WriteDocument(Document, TargetPath)
    assert tuple(TmpPath.iterdir()) == ()
