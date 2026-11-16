from datetime import datetime, timezone
from hashlib import sha256
from struct import unpack_from

from HeaderLogs import ReadHeaderLogs
from HeaderSelf import ReadHeaderSelf
from PartFraming import BuildVersionedArchive, CheckVersionStreams, VersionStorage
from convert.adapters.solidworks.Container.Archive import ContainerMo
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.Container import (
    CentralMarks,
    SldprtArchive,
    TemplateFields,
)


def archive_time(word: int) -> int:
    return int(
        datetime(
            1980 + (word >> 25),
            (word >> 21) & 0xF,
            (word >> 16) & 0x1F,
            (word >> 11) & 0x1F,
            (word >> 5) & 0x3F,
            (word & 0x1F) * 2,
            tzinfo=timezone.utc,
        ).timestamp()
    )


# Only generated framing records enter this independent container readback.
def verify_version_framing(archive: SldprtArchive, generation: int) -> str:
    root = VersionStorage(generation)
    RequireArch(
        {name for name in archive.streams if name.startswith(root + "/")},
        {f"{root}/History", f"{root}/Biography"},
        "observed native version storage paths",
    )
    header, _ = ReadHeaderLogs(archive.require("Header2"), generation)
    time = ReadHeaderSelf(header, generation).ModifiedTime
    generated = BuildVersionedArchive(generation, time, {})
    readback = SldprtArchive.from_bytes(generated)
    RequireArch(
        (readback.format_version, ContainerMo(readback.streams), len(readback.streams)),
        (4, generation, 2),
        "research framing metadata and version selection",
    )
    CheckVersionStreams(generation, readback.streams)
    _, local_times = TemplateFields(generated, readback)
    markers = CentralMarks(
        generated,
        readback.records,
        {
            (
                record.name,
                record.crc32,
                record.compressed_size,
                record.uncompressed_size,
            )
            for record in readback.records
        },
    )
    central_times = {unpack_from("<I", generated, mark + 6)[0] for mark in markers}
    RequireArch(
        set(local_times.values()), central_times, "shared local and central ZIP clock"
    )
    RequireArch(
        {archive_time(word) for word in central_times},
        {time - time % 2},
        "generated ZIP date and two-second clock",
    )
    return sha256(generated).hexdigest()
