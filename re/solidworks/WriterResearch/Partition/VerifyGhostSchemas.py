# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from argparse import ArgumentParser
from hashlib import sha256
from json import dumps as DumpJson, loads as LoadJson
from pathlib import Path
import sys

# only the pinned repository supplies the audit and codec modules
KRepository = Path(__file__).resolve().parents[4]

# preserve the private native capture outside the module resolution path
sys.path[:0] = [
    str(KRepository / "src"),
    str(KRepository / "re/automation"),
    str(KRepository / "re/automation/TwoPad"),
    str(KRepository / "re/solidworks/WriterResearch"),
]

from PadReceipts import ReadPadBytes
from Partition.GhostSchemas import EncodeGhostSchemas
from Partition.VerifyTwoPadGhostBodies import ReadWorld
from Partition.VerifyTwoPadGhostRows import (
    KBodyRow,
    KDefinition,
    KStreamName,
    ReadDefinition,
)
from VerifyDiscovery import AuditDiscovery
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.Parasolid import DecodePartition
from convert.Geometry.Parasolid import ParaHeaderData, ParaWriteError

# the legacy receipt provides independently authored single body controls
KLegacyPath = KRepository / "re/automation/PairedCaptures/P01/solidworks-75b9308cf13e"

# the earlier archive inventory is sealed before these type comparisons
KLegacyReceipt = "3c389fe4069bece7ecf64f0294d111ce7f44131b2fc576d3f2ac4291e0fec7bf"


# the source world and the definition name bind both descriptor boundaries
def CheckArchive(Raw: bytes) -> dict[str, object]:
    Stream = SldprtArchive.from_bytes(Raw).require(KStreamName)
    (Payload,) = DecodePartition(Stream, KStreamName)
    Header = ParaHeaderData(Payload.data)
    if Header is None or Payload.kind != "partition":
        raise ParaWriteError("ghost archive lacks a partition member")
    Data = Payload.data[Header.body_offset :]
    World, _, BodySchemaOffset = ReadWorld(Data)
    Name, Definition = ReadDefinition(Data)
    RequireArch(World.definition + 1, Definition, "world owns the ghost attribute type")
    Rendered = EncodeGhostSchemas(Header.schema)
    BodyOffset = BodySchemaOffset + len(Rendered.body)
    Body = KBodyRow.unpack_from(Data, BodyOffset)
    RequireArch(
        (Body[0], Body[17]),
        (World.body + 1, World.world + 1),
        "leading body and world ownership",
    )

    DefSchemaOffset = BodyOffset + KBodyRow.size
    DefOffset = DefSchemaOffset + len(Rendered.attribute_definition)
    Slots = KDefinition.unpack_from(Data, DefOffset)
    RequireArch(
        Slots[:5],
        (2, Definition, 1, Name, 9000),
        "named definition follows its declared type",
    )
    RequireArch(
        (Data[BodySchemaOffset:BodyOffset], Data[DefSchemaOffset:DefOffset]),
        tuple(Rendered),
        "generated ghost type declarations",
    )
    return {
        "input_sha256": sha256(Raw).hexdigest(),
        "offsets": [BodySchemaOffset, DefSchemaOffset],
        "size_bytes": list(map(len, Rendered)),
        "sha256": [sha256(Value).hexdigest() for Value in Rendered],
    }


# each legacy archive must retain its complete source receipt independently
def CheckLegacy() -> dict[str, object]:
    Receipt = (KLegacyPath / "receipt.json").read_bytes()
    RequireArch(sha256(Receipt).hexdigest(), KLegacyReceipt, "legacy discovery receipt")
    Inputs = LoadJson(Receipt)["native_files"]
    RequireArch(len(Inputs), 6, "six legacy authored controls")
    Captures = {}
    for Input in Inputs:
        Raw = ReadPadBytes(KLegacyPath, Input["file"], Input["sha256"])
        RequireArch(len(Raw), Input["size_bytes"], "legacy archive length")
        Captures[Input["file"]] = CheckArchive(Raw)
    return Captures


# both save families expose the same descriptor grammar under their sealed custody
def RunVerification() -> None:
    Parser = ArgumentParser(
        description="Reproduce ghost body and definition type descriptors."
    )
    Parser.add_argument("--run-directory", type=Path, required=True)
    Parser.add_argument("--source-revision", required=True)
    Parser.add_argument("--report-sha256", required=True)
    Parser.add_argument("--authoring-sha256", required=True)
    Parser.add_argument("--reopen-sha256", required=True)
    Args = Parser.parse_args()
    Native = AuditDiscovery(
        Args.run_directory,
        KRepository,
        Args.source_revision,
        Args.report_sha256,
        Args.authoring_sha256,
        Args.reopen_sha256,
        True,
    )
    Cases = {}
    for Case in Native["cases"]:
        Variant, Digest = Case["variant"], Case["archive_sha256"]
        Raw = ReadPadBytes(Args.run_directory, f"{Variant}.SLDPRT", Digest)
        Cases[Variant] = CheckArchive(Raw)
    try:
        EncodeGhostSchemas("other schema")
    except ParaWriteError:
        pass
    else:
        raise ParaWriteError("unsupported ghost type descriptor schema was accepted")
    Report = {
        "two_pad": Cases,
        "legacy": CheckLegacy(),
        "native_observations": Native["verified_native_observations"],
        "stock_controls": Native["stock_controls"],
    }
    Payload = DumpJson(Report, sort_keys=True, separators=(",", ":"), allow_nan=False)
    sys.stdout.buffer.write((Payload + "\n").encode("utf-8"))


if __name__ == "__main__":
    RunVerification()
