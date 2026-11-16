from hashlib import sha256
from typing import cast as CastValue

from CmgrColorReadback import ReadColorSpan
from CmgrOpening import ReadCmgrOpening
from CmgrVisualPrefix import CmgrVisualFields, WriteCmgrVisualPrefix
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.ArchiveCursor import FieldCursor
from convert.adapters.solidworks.Container.Definition import ArchiveWriter


# Fixed scalar and CString groups are validated by the exact reconstruction.
def read_visual_fields(cursor: FieldCursor) -> CmgrVisualFields:
    surface_color, wire_color, hidden_line_color = cursor.ReadInts("<3I")
    cursor.ReadText()
    material_name = cursor.ReadText()
    cursor.ReadValue("<6di5i")
    cursor.ReadText()
    cursor.ReadInts("<2i")
    (appearance_id,) = cursor.ReadInts("<Q")
    cursor.ReadText()
    mapping_mode, material_color = cursor.ReadInts("<BI")
    cursor.ReadValue("<10fi5fi2f")
    locator = cursor.ReadText()
    cursor.ReadValue("<I2f")
    cursor.ReadText()
    bump_strength, displacement, _ = CastValue(
        tuple[float, float, float], cursor.ReadValue("<3f")
    )
    (flags,) = cursor.ReadInts("<i")
    cursor.ReadValue("<fi13f")
    cursor.ReadText()
    cursor.ReadValue("<f")
    cursor.ReadText()
    cursor.ReadInts("<2i")
    cursor.ReadText()
    cursor.ReadInts("<2i")
    cursor.ReadText()
    _, uses_default_appearance, _, _, _, _ = cursor.ReadInts("<6i")
    return CmgrVisualFields(
        surface_color,
        wire_color,
        hidden_line_color,
        material_name,
        appearance_id,
        material_color,
        locator,
        mapping_mode,
        bump_strength,
        displacement,
        bool(flags & 0x100),
        bool(uses_default_appearance),
    )


def verify_visual_prefix(stream: bytes, generation: int, asset: str) -> str:
    cursor = ReadCmgrOpening(stream, generation)
    start = cursor.Offset
    fields = read_visual_fields(cursor)
    _, dspbr_start, _ = ReadColorSpan(stream, generation)
    RequireArch(
        (start, cursor.Offset, dspbr_start),
        (278, 795, 795),
        f"CMgr material and RealView boundaries in {asset}",
    )
    writer = ArchiveWriter()
    writer.SetNextIndex(cursor.NextIndex)
    writer.classes.update((name, index) for index, name in cursor.Classes.items())
    WriteCmgrVisualPrefix(writer, generation, fields)
    RequireArch(
        (writer.next_index, writer.classes),
        (cursor.NextIndex, {name: index for index, name in cursor.Classes.items()}),
        "CMgr visual prefix allocations",
    )
    saved = stream[start:dspbr_start]
    RequireArch(
        writer.build() == saved,
        True,
        f"CMgr material and RealView reconstruction in {asset}",
    )
    return sha256(saved).hexdigest()
