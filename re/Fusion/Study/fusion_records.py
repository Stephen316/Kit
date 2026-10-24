"""Observed object-header fragments, without claiming a complete binary grammar."""

from dataclasses import dataclass
import struct


@dataclass
class Record:
    start: int
    body: int
    end: int
    type_code: str
    object_id: int
    payload_start: int = None
    class_guid: str = None
    class_namespace: str = None
    is_primary: bool = None


def record_fragments(data):
    records = []
    for position in range(max(0, len(data) - 19)):
        length = struct.unpack_from("<I", data, position)[0]
        if not 1 <= length <= 4:
            continue
        code = data[position + 4:position + 4 + length]
        body = position + 16 + length
        if body > len(data) or not code.isdigit():
            continue
        identity = struct.unpack_from("<Q", data, position + 4 + length)[0]
        if identity >= 2**32 or data[body - 4:body] != b"\0" * 4:
            continue
        records.append(Record(position, body, len(data), code.decode(), identity))
    for current, following in zip(records, records[1:]):
        current.end = following.start
    return records
