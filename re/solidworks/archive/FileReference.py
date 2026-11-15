"""Read the guarded modern local file reference without disclosing its path."""

from convert.adapters.solidworks.container.Archive import (
    KClassRefKind,
    KDefinitionKind,
    ReadString,
)
from SketchRoot import Require


# every string uses the archive encoding before the following scalar can be read
def read_text(cursor):
    value, width = ReadString(cursor.blob, cursor.position)
    cursor.position += width
    return value


# the nested filename handles also materialize entries in the shared map
def read_file_reference(cursor):
    offset = cursor.position
    index = cursor.pointer(KDefinitionKind, "moExtObject_c")
    cursor.pointer(KDefinitionKind, "moCStringHandle_c")
    read_text(cursor)
    cursor.pointer(KClassRefKind, "moCStringHandle_c")
    Require(bool(read_text(cursor)), True, "saved local document name present")
    object_kind, shared_flags, shared_time = cursor.read("<HBI")
    Require((object_kind, shared_flags), (2, 0), "saved part file identity")
    Require([read_text(cursor) for _ in range(3)], [""] * 3, "empty alternate names")
    Require(cursor.read("<B"), (0,), "guarded shared file state")
    file_flags, _ = cursor.read("<BI")
    Require(file_flags in (0, 8), True, "guarded external reference state")
    Require(cursor.read("<3i"), (0, 0, 0), "guarded local file scalars")
    Require(read_text(cursor), "Default", "saved local configuration name")
    Require(cursor.read("<2iIi"), (0, 0, 0, 0), "guarded file reference trailer")
    return {
        "offset": offset,
        "object_index": index,
        "end": cursor.position,
        "shared_time_word": shared_time,
    }
