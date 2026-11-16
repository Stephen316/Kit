from hashlib import sha256
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
CAPTURE_REVISION = "466dcb172dfa3803463e07ccde963ba01671d200"
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "re/automation")]

from HeaderLogs import ReadHeaderLogs
from ResolvedCabinet import ReadCabinetRec, WriteCabinetRec
from ResolvedFolders import ReadSysFolders, WriteSysFolders
from SolidworksCensusInputs import capture_inputs
from convert.adapters.solidworks.Config.OrdinaryMap import ReadOrdinaryMap
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.ArchiveCursor import ArchiveCursor
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.Definition import ArchiveWriter
from convert.adapters.solidworks.Resolved.ResolvedHead import OpenResolved
from convert.adapters.solidworks.Resolved.SystemPrefix import ReadSysPrefix


# Both control families inherit their namespace from the actual configuration.
def verify_resolved_folders() -> dict[str, object]:
    rows, _ = capture_inputs(ROOT, CAPTURE_REVISION)
    captures = {}
    cabinets = {}
    for recipe, asset, source, _, measurement in rows:
        if recipe not in ("P01", "P03"):
            continue
        archive = SldprtArchive.from_bytes(source, asset["path"])
        config, model = ReadOrdinaryMap(archive.require("Contents/Config-0"), 19000)
        atom_count = model["atom_count"]
        RequireArch(atom_count, int(recipe == "P03"), "resolved folders configuration")
        stream = archive.require("Contents/Config-0-ResolvedFeatures")
        cursor = OpenResolved(stream, config, 18 + atom_count)
        comparison = ArchiveCursor(
            stream,
            cursor.Offset,
            cursor.NextIndex,
            cursor.Classes.copy(),
            cursor.Objects.copy(),
        )
        system = ReadSysPrefix(comparison)
        prior = system.FirstFolders
        start = cursor.Offset
        writer = ArchiveWriter()
        writer.SetNextIndex(cursor.NextIndex)
        writer.classes.update((name, index) for index, name in cursor.Classes.items())
        folders = ReadSysFolders(cursor, 19000)
        RequireArch(
            (
                (cursor.Offset, cursor.NextIndex),
                tuple((row.Name, row.TreeId) for row in folders),
            ),
            (
                (prior[-1].EndOffset, prior[-1].NextIndex),
                tuple((row.NameValue, row.FeatureId) for row in prior),
            ),
            "resolved system folder boundary and identities",
        )
        _, header = ReadHeaderLogs(
            archive.require("Contents/Config-0-ModelHeader"), 19000
        )
        logged = {(log.Name, log.TreeId) for log in header.Revisions}
        measured = {feature["name"] for feature in measurement["feature_tree"]}
        RequireArch(
            all(
                folder.Name in measured and (folder.Name, folder.TreeId) in logged
                for folder in folders
            ),
            True,
            "resolved folders native tree and revision evidence",
        )
        WriteSysFolders(writer, 19000, folders)
        saved = stream[start : cursor.Offset]
        RequireArch(
            writer.build() == saved, True, f"resolved folders in {asset['path']}"
        )
        RequireArch(
            (
                writer.next_index,
                {index: name for name, index in writer.classes.items()},
            ),
            (cursor.NextIndex, cursor.Classes),
            "resolved folders live archive allocator",
        )
        captures[asset["sha256"]] = sha256(saved).hexdigest()
        cabinet_start = cursor.Offset
        cabinet = ReadCabinetRec(cursor, 19000)
        expected = (system.Details.Cabinet, system.Details.Notes, system.Details.EndTag)
        entries = (cabinet.Cabinet, cabinet.Notes, cabinet.EndTag)
        RequireArch(
            tuple((row.Name, row.TreeId) for row in entries),
            tuple((row.NameValue, row.FeatureId) for row in expected),
            "resolved cabinet tree identities",
        )
        RequireArch(
            all(
                row.Name in measured and (row.Name, row.TreeId) in logged
                for row in entries
            ),
            True,
            "resolved cabinet native tree and revision evidence",
        )
        RequireArch(
            (cursor.Offset, cursor.NextIndex),
            (system.Details.Cabinet.EndOffset, system.Details.Cabinet.NextIndex),
            "resolved cabinet native boundary",
        )
        WriteCabinetRec(writer, 19000, cabinet)
        RequireArch(
            writer.build() == stream[start : cursor.Offset],
            True,
            "resolved folder and cabinet bytes",
        )
        RequireArch(
            (
                writer.next_index,
                {index: name for name, index in writer.classes.items()},
            ),
            (cursor.NextIndex, cursor.Classes),
            "resolved cabinet live archive allocator",
        )
        cabinets[asset["sha256"]] = sha256(
            stream[cabinet_start : cursor.Offset]
        ).hexdigest()
    return {
        "capture_revision": CAPTURE_REVISION,
        "captures": captures,
        "cabinet_records": cabinets,
    }


if __name__ == "__main__":
    print(json.dumps(verify_resolved_folders(), sort_keys=True))
