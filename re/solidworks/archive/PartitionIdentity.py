"""Audit native partition ownership in the eleven original P04 saves."""

from argparse import ArgumentParser
import json
from pathlib import Path
import sys

if __name__ == "__main__":
    root = Path(__file__).resolve().parents[3]
    sys.path[:0] = [str(root / "src"), str(root / "re" / "automation")]

from PairedCaptureIntake import require, sha256
from ScopePartitionIds import ReadNativeIds
from SketchEvidence import (
    KApplicationBuild,
    KCaptureRev,
    KReceiptDigest,
    ReadPinned,
    ReadReceipts,
)
from SolidWorksScopePartition import PARTITION, RESOLVED, TOPOLOGY, region_model

from convert.adapters.solidworks.config.CutConfig import ReadCutConfig
from convert.adapters.solidworks.config.RootLayout import KConfigGen
from convert.adapters.solidworks.container.Archive import ArchiveError, ContainerMo
from convert.adapters.solidworks.container.Container import SldprtArchive
from convert.adapters.solidworks.container.Parasolid import DecodeBrep, DecodePartition
from convert.adapters.solidworks.resolved.cut.CutLinks import ReadCutLinks
from convert.adapters.solidworks.resolved.cut.CutProof import ReadCutProof


# the independently decoded cut provides the authored atom and target body
def ReadP04Identity(root, asset):
    name = asset["file"]
    data = ReadPinned(root, name)
    archive_sha = sha256(data)
    require(
        (len(data), archive_sha) == (asset["size_bytes"], asset["sha256"]),
        f"{name} capture differs from its receipt",
    )
    archive = SldprtArchive.from_bytes(data, name)
    require(ContainerMo(archive.streams) == KConfigGen, "unsupported P04 generation")
    resolved = archive.require(RESOLVED)
    configuration = ReadCutConfig(archive.require("Contents/Config-0"), KConfigGen)
    proof = ReadCutProof(ReadCutLinks(resolved, configuration), configuration)
    operation = proof.Operation
    partition = ReadP04Partition(archive)
    require(
        partition["native_identity"]["recent_atom_id"] == operation["atom_id"],
        f"{name} active partition atom differs from the typed Cut atom",
    )
    return {
        "file": name,
        "archive_sha256": archive_sha,
        "resolved_sha256": sha256(resolved),
        "cut_feature_id": operation["native_feature_id"],
        "boss_feature_id": proof.Links.BossValue["native_feature_id"],
        "atom_id": operation["atom_id"],
        "target_body_id": operation["solid_body"]["body_id"],
        "termination": operation["end_specification"]["conditions"][0],
        **partition,
    }


# the complete decoded solid provides an independent check of native face membership
def ReadP04Partition(archive):
    raw = archive.require(PARTITION)
    parts = [
        part for part in DecodePartition(raw, PARTITION) if part.kind == "partition"
    ]
    require(len(parts) == 1, "expected a single active P04 partition")
    (part,) = parts
    model = DecodeBrep(part.data)
    require(
        model is not None
        and not model.validate()
        and len(model.regions) == len(model.bodies) == 1
        and not model.wires,
        "expected one decoded P04 carrier and region",
    )
    (region,) = model.regions
    (carrier,) = model.bodies
    require(
        region.solid and carrier.region_ids == (region.id,),
        "P04 carrier does not resolve its single solid region",
    )
    subset = region_model(model, region, carrier)
    require(
        all(
            len(getattr(model, field)) == len(getattr(subset, field))
            for field in TOPOLOGY
        ),
        "P04 region does not account for all decoded topology",
    )
    identities = ReadNativeIds(
        part.data, {region.id: {face.id for face in subset.faces}}
    )
    return {
        "partition_stream_sha256": sha256(raw),
        "partition_sha256": part.sha256,
        "schema": part.schema,
        "carrier_id": carrier.id,
        "decoded_region_id": region.id,
        "face_count": len(subset.faces),
        "native_identity": identities[region.id],
    }


# one immutable receipt limits the audit to the measured discovery corpus
def MainEntry():
    parser = ArgumentParser(description=__doc__)
    parser.parse_args()
    root = Path(__file__).resolve().parents[3]
    try:
        receipt, _ = ReadReceipts(root)
        captures = [ReadP04Identity(root, asset) for asset in receipt["native_files"]]
    except (ArchiveError, OSError, ValueError) as error:
        parser.exit(1, f"P04 partition identity refused: {error}\n")
    report = {
        "scope": "p04_active_partition_native_identity",
        "application_build": KApplicationBuild,
        "capture_revision": KCaptureRev,
        "capture_receipt_sha256": KReceiptDigest,
        "captures": captures,
    }
    text = json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n"
    sys.stdout.buffer.write(text.encode())


if __name__ == "__main__":
    MainEntry()
