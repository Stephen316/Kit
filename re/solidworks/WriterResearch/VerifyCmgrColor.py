from hashlib import sha256
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
CAPTURE_REVISION = "466dcb172dfa3803463e07ccde963ba01671d200"
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "re/automation")]

from CmgrBaseHeader import ReadCmgrHeader
from CmgrColorReadback import ReadColorSpan
from CmgrExternal import ReadCmgrExt, WriteCmgrExt
from CmgrMass import EncodeEmptyMass, ReadEmptyMass
from CmgrOpening import ReadCmgrFeature
from CmgrTail import ReadCmgrTail, WriteCmgrTail
from ColorAppearance import EncodeColorDspbr
from SolidworksCensusInputs import capture_inputs
from VerifyCmgrBaseState import verify_base_state
from VerifyCmgrBoss import verify_boss_mass
from VerifyCmgrComposition import verify_cmgr_composition
from VerifyCmgrIndex import verify_cmgr_index
from VerifyCmgrOpen import verify_opening
from VerifyCmgrPart import verify_part_end
from VerifyCmgrVisual import verify_visual_prefix
from VerifyPartFraming import verify_version_framing
from convert.adapters.solidworks.Container.Archive import ContainerMo
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.ArchiveCursor import ArchiveCursor
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.Definition import ArchiveWriter

TREE_IDS = {"P01": (), "P03": (34,), "P04": (34, 46)}


# the mass block follows the part feature fields and its base configuration header
def read_mass_start(
    stream: bytes, visual_end: int
) -> tuple[ArchiveCursor, tuple[int, ...]]:
    RequireArch(visual_end, 1095, "CMgr visual return before mass")
    cursor = ArchiveCursor(stream, visual_end, 9, {}, {})
    ReadCmgrFeature(cursor, 19000)
    RequireArch(cursor.Offset, 1206, "CMgr base configuration opening")
    fields = ReadCmgrHeader(cursor, 19000)
    RequireArch(cursor.Offset, 1234, "CMgr mass start")
    return cursor, (fields.model_highest_id, fields.session_stamp, fields.mass_stamp)


# the independent archive path must supply the exact span for byte comparison
def verify_empty_mass(
    stream: bytes, visual_end: int, body_count: int, asset: str
) -> str:
    cursor, (first, _, last) = read_mass_start(stream, visual_end)
    RequireArch((first, last), (28, 0), "CMgr empty configuration members")
    start = cursor.Offset
    end = ReadEmptyMass(stream, start, 19000, body_count)
    RequireArch(end, 1488, "CMgr empty mass return")
    saved = stream[start:end]
    RequireArch(
        EncodeEmptyMass(19000, body_count) == saved,
        True,
        f"CMgr empty mass reconstruction in {asset}",
    )
    return sha256(saved).hexdigest()


# The part aliases leave the reader at the external object with its live archive map.
def verify_tail(
    cursor: ArchiveCursor, tree_ids: tuple[int, ...], asset: str
) -> tuple[str, str]:
    stream, start = cursor.BlobValue, cursor.Offset
    writer = ArchiveWriter()
    writer.SetNextIndex(cursor.NextIndex)
    writer.classes.update((name, index) for index, name in cursor.Classes.items())
    state = ReadCmgrExt(cursor, 19000)
    first_list = cursor.Offset
    external = stream[start:first_list]
    WriteCmgrExt(writer, 19000, state)
    RequireArch(
        writer.build() == external,
        True,
        f"CMgr external file reconstruction in {asset}",
    )
    RequireArch(
        (writer.next_index, writer.classes),
        (cursor.NextIndex, {name: index for index, name in cursor.Classes.items()}),
        "CMgr external file allocations",
    )
    stamps = ReadCmgrTail(cursor, 19000)
    RequireArch(tuple(stamp.tree_id for stamp in stamps), tree_ids, "CMgr feature IDs")
    WriteCmgrTail(writer, 19000, stamps)
    RequireArch(
        (writer.next_index, writer.classes),
        (cursor.NextIndex, {name: index for index, name in cursor.Classes.items()}),
        "CMgr terminal allocations",
    )
    terminal = stream[first_list:]
    RequireArch(
        writer.build()[len(external) :] == terminal,
        True,
        f"complete CMgr tail in {asset}",
    )
    return sha256(external).hexdigest(), sha256(terminal).hexdigest()


# the emitted default color body must occupy exactly the independently framed span
def verify_color():
    rows, _ = capture_inputs(ROOT, CAPTURE_REVISION)
    captures = {}
    visuals = {}
    compositions = {}
    configuration_indexes = {}
    version_framing = {}
    externals = {}
    tails = {}
    masses = {}
    boss_masses = {}
    base_headers = {}
    collection_fronts = {}
    collection_tails = {}
    part_reports = {
        "linked_atom_records": {},
        "base_return_records": {},
        "part_return_records": {},
        "manager_alias_records": {},
    }
    for recipe, item, data, _, measurement in rows:
        archive = SldprtArchive.from_bytes(data, item["path"])
        generation = ContainerMo(archive.streams)
        RequireArch(generation, 19000, "CMgr verification generation")
        stream = archive.require("Contents/CMgr")
        if recipe in ("P01", "P03"):
            verify_opening(stream, generation, item["path"])
            visuals[item["sha256"]] = verify_visual_prefix(
                stream, generation, item["path"]
            )
            compositions[item["sha256"]] = verify_cmgr_composition(
                archive, generation, measurement
            )
            configuration_indexes[item["sha256"]] = verify_cmgr_index(
                archive, generation
            )
            version_framing[item["sha256"]] = verify_version_framing(
                archive, generation
            )
        color, start, cursor = ReadColorSpan(stream, generation)
        end = cursor.Offset
        saved = stream[start:end]
        RequireArch(end - start, 300, "CMgr default DSPBR body width")
        RequireArch(
            EncodeColorDspbr(19000, color) == saved,
            True,
            f"CMgr default DSPBR reconstruction for {item['path']}",
        )
        captures[item["sha256"]] = sha256(saved).hexdigest()
        if recipe in ("P01", "P03"):
            header, front, trailing = verify_base_state(
                cursor, generation, measurement["body_count"], TREE_IDS[recipe]
            )
            base_headers[item["sha256"]] = header
            collection_fronts[item["sha256"]] = front
            collection_tails[item["sha256"]] = trailing
        part_evidence = verify_part_end(cursor, recipe, TREE_IDS[recipe], item["path"])
        for record, digest in part_evidence.items():
            part_reports[record][item["sha256"]] = digest
        externals[item["sha256"]], tails[item["sha256"]] = verify_tail(
            cursor, TREE_IDS[recipe], item["path"]
        )
        if recipe == "P01":
            masses[item["sha256"]] = verify_empty_mass(
                stream, end, measurement["body_count"], item["path"]
            )
        if recipe == "P03":
            mass_cursor, _ = read_mass_start(stream, end)
            boss_masses[item["sha256"]] = verify_boss_mass(
                mass_cursor, archive, generation, measurement, item["path"]
            )
    RequireArch(len(masses), 6, "CMgr empty mass capture count")
    RequireArch(len(visuals), 14, "CMgr visual prefix capture count")
    RequireArch(len(compositions), 14, "CMgr composed stream capture count")
    RequireArch(len(configuration_indexes), 14, "CMgr active index capture count")
    RequireArch(len(version_framing), 14, "modern framing input capture count")
    return {
        "capture_revision": CAPTURE_REVISION,
        "captures": captures,
        "visual_prefix_records": visuals,
        "composed_cmgr_records": compositions,
        "configuration_index_records": configuration_indexes,
        "version_framing_records": version_framing,
        "external_file_records": externals,
        "terminal_records": tails,
        "empty_mass_records": masses,
        "boss_mass_wrappers": boss_masses,
        "base_header_records": base_headers,
        "collection_front_records": collection_fronts,
        "collection_tail_records": collection_tails,
        **part_reports,
    }


if __name__ == "__main__":
    print(json.dumps(verify_color(), sort_keys=True))
