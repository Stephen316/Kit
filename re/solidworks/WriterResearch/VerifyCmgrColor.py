from hashlib import sha256
import json
from pathlib import Path
from struct import calcsize
import sys

ROOT = Path(__file__).resolve().parents[3]
CAPTURE_REVISION = "466dcb172dfa3803463e07ccde963ba01671d200"
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "re/automation")]

from CmgrColorReadback import ReadColorSpan
from CmgrMass import EncodeEmptyMass, ReadEmptyMass
from CmgrOpening import ReadCmgrFeature
from CmgrTail import ReadCmgrTail, WriteCmgrTail
from ColorAppearance import EncodeColorDspbr
from SolidworksCensusInputs import capture_inputs
from convert.adapters.solidworks.container.Archive import (
    KClassRefKind,
    ArchiveError,
    ContainerMo,
    ReadTag,
)
from convert.adapters.solidworks.container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.container.ArchiveCursor import ArchiveCursor
from convert.adapters.solidworks.container.Cmgr import KObjectListClass
from convert.adapters.solidworks.container.Container import SldprtArchive
from convert.adapters.solidworks.container.Definition import ArchiveWriter

TREE_IDS = {"P01": (), "P03": (34,), "P04": (34, 46)}


# the mass block follows the part feature fields and its base configuration header
def read_mass_start(stream: bytes, visual_end: int) -> int:
    RequireArch(visual_end, 1095, "CMgr visual return before empty mass")
    cursor = ArchiveCursor(stream, visual_end, 9, {}, {})
    ReadCmgrFeature(cursor, 19000)
    RequireArch(cursor.Offset, 1206, "CMgr base configuration opening")
    RequireArch(
        (cursor.ReadText(), cursor.ReadInts("<iI"), cursor.ReadText()),
        ("", (-1, 0x80400180), ""),
        "CMgr base configuration header",
    )
    first, _, last = cursor.ReadInts("<3I")
    RequireArch((first, last), (28, 0), "CMgr empty configuration members")
    RequireArch(cursor.Offset, 1234, "CMgr empty mass start")
    return cursor.Offset


# the independent archive path must supply the exact span for byte comparison
def verify_empty_mass(stream: bytes, visual_end: int, body_count: int, asset: str) -> str:
    start = read_mass_start(stream, visual_end)
    end = ReadEmptyMass(stream, start, 19000, body_count)
    RequireArch(end, 1488, "CMgr empty mass return")
    saved = stream[start:end]
    RequireArch(
        EncodeEmptyMass(19000, body_count) == saved,
        True,
        f"CMgr empty mass reconstruction in {asset}",
    )
    return sha256(saved).hexdigest()


# the witnessed second list reference anchors the typed terminal scan from EOF
def verify_tail(stream: bytes, tree_ids: tuple[int, ...], asset: str) -> str:
    second_list = len(stream) - 70
    reference = ReadTag(stream, second_list)
    RequireArch(
        (reference.kind, reference.size), (KClassRefKind, 2), "CMgr second list"
    )
    index = reference.index
    if index is None:
        raise ArchiveError("CMgr second list has no class allocation")
    first_list = (
        second_list
        - calcsize("<HHH")
        - len(KObjectListClass)
        - calcsize("<Hi3iIi")
        - len(tree_ids) * calcsize("<iII")
    )
    cursor = ArchiveCursor(stream, first_list, index, {}, {})
    stamps = ReadCmgrTail(cursor, 19000)
    RequireArch(tuple(stamp.tree_id for stamp in stamps), tree_ids, "CMgr feature IDs")
    writer = ArchiveWriter()
    writer.SetNextIndex(index)
    WriteCmgrTail(writer, 19000, stamps)
    RequireArch(writer.next_index, cursor.NextIndex, "CMgr terminal allocations")
    RequireArch(
        writer.build() == stream[first_list:], True, f"complete CMgr tail in {asset}"
    )
    return sha256(stream[first_list:]).hexdigest()


# the emitted default color body must occupy exactly the independently framed span
def verify_color():
    rows, _ = capture_inputs(ROOT, CAPTURE_REVISION)
    captures = {}
    tails = {}
    masses = {}
    for recipe, item, data, _, measurement in rows:
        archive = SldprtArchive.from_bytes(data, item["path"])
        generation = ContainerMo(archive.streams)
        RequireArch(generation, 19000, "CMgr verification generation")
        stream = archive.require("Contents/CMgr")
        color, start, end = ReadColorSpan(stream, 19000)
        saved = stream[start:end]
        RequireArch(end - start, 300, "CMgr default DSPBR body width")
        RequireArch(
            EncodeColorDspbr(19000, color) == saved,
            True,
            f"CMgr default DSPBR reconstruction for {item['path']}",
        )
        captures[item["sha256"]] = sha256(saved).hexdigest()
        tails[item["sha256"]] = verify_tail(stream, TREE_IDS[recipe], item["path"])
        if recipe == "P01":
            masses[item["sha256"]] = verify_empty_mass(
                stream, end, measurement["body_count"], item["path"]
            )
    RequireArch(len(masses), 6, "CMgr empty mass capture count")
    return {
        "capture_revision": CAPTURE_REVISION,
        "captures": captures,
        "terminal_records": tails,
        "empty_mass_records": masses,
    }


if __name__ == "__main__":
    print(json.dumps(verify_color(), sort_keys=True))
