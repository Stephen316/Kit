from hashlib import sha256

from CmgrColorReadback import ReadColorSpan
from CmgrInherited import ReadCmgrFeature, WriteCmgrFeature
from CmgrOpening import ReadOpenFields, WriteCmgrOpening
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.Definition import ArchiveWriter


# both stamped feature owners must close at their native boundaries
def verify_opening(stream: bytes, generation: int, asset: str) -> tuple[str, str]:
    cursor, fields, slots = ReadOpenFields(stream, generation)
    RequireArch(
        (cursor.Offset, cursor.NextIndex), (278, 9), "CMgr visual body boundary"
    )
    opening = ArchiveWriter()
    result = WriteCmgrOpening(opening, generation, fields)
    RequireArch(
        (
            result,
            opening.next_index,
            {index: name for name, index in opening.classes.items()},
        ),
        (slots, cursor.NextIndex, cursor.Classes),
        "CMgr opening slots match the typed saved allocation",
    )
    start = stream[: cursor.Offset]
    RequireArch(
        opening.build() == start, True, f"CMgr opening reconstruction in {asset}"
    )

    _, _, cursor = ReadColorSpan(stream, generation)
    feature_start, count = cursor.Offset, cursor.NextIndex
    RequireArch((feature_start, count), (1095, 9), "CMgr inherited part start")
    stamp = ReadCmgrFeature(cursor, generation)
    RequireArch(
        (cursor.Offset, cursor.NextIndex), (1206, count), "CMgr inherited part end"
    )
    inherited = ArchiveWriter()
    inherited.SetNextIndex(count)
    WriteCmgrFeature(inherited, generation, stamp)
    saved = stream[feature_start : cursor.Offset]
    RequireArch(inherited.next_index, count, "CMgr inherited part allocation count")
    RequireArch(
        inherited.build() == saved,
        True,
        f"CMgr inherited part reconstruction in {asset}",
    )
    return sha256(start).hexdigest(), sha256(saved).hexdigest()
