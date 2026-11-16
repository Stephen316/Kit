from collections.abc import Iterator
from io import BytesIO as ByteStream
from zipfile import ZipFile

from tests.Convert.Formats.FusionCodec.Documents.Form.FormArchives import (
    KFormArchives,
)
from tests.Convert.Formats.FusionCodec.Documents.Form.ReadFormFile import (
    ReadFormFile,
)


# shared spline members setup keeps fixtures consistent so native document reconstruction failures identify the intended compatibility boundary
def SplineMembers() -> Iterator[tuple[str, bytes, bytes]]:
    for CaseValue in KFormArchives:
        with ZipFile(ByteStream(ReadFormFile(*CaseValue))) as Archive:
            Names = Archive.namelist()
            Program = Archive.read(
                next(EntryName for EntryName in Names if EntryName.endswith(".tsm"))
            )
            for NameValue in Names:
                if NameValue.endswith((".smb", ".smbh")):
                    yield NameValue, Archive.read(NameValue), Program
