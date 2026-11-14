import hashlib
import struct


class Reader:
    def __init__(self, data):
        self.data = data
        self.offset = 0

    def take(self, count):
        if count < 0 or self.offset + count > len(self.data):
            raise ValueError("Property payload exceeds its chain")
        value = self.data[self.offset:self.offset + count]
        self.offset += count
        return value

    def number(self, kind):
        return struct.unpack("<" + kind, self.take(struct.calcsize("<" + kind)))[0]

    def text(self):
        return self.take(self.number("I")).decode("utf-8")

    def strings(self):
        count = self.number("I")
        if count > len(self.data) // 4:
            raise ValueError("Property string list exceeds payload")
        return [self.text() for _ in range(count)]


def table(data):
    reader = Reader(data)
    rows = []
    while reader.offset < len(data):
        start = reader.offset
        rows.append({"offset": start, "instance_id": reader.text(), "role": reader.text(), "definition_root": reader.number("I"), "instance_root": reader.number("I"), "schema": reader.text(), "end_offset": reader.offset})
    return {"records": rows, "unresolved_bytes": len(data) - reader.offset}


def definition(data):
    reader = Reader(data)
    row = {"BaseSchema": reader.text(), "Hidden": reader.number("B"), "UIName": reader.text(), "VersionGUID": reader.text(), "category": reader.strings(), "description": reader.text(), "keyword": reader.strings(), "thumbnail": reader.strings()}
    row["consumed_bytes"] = reader.offset
    row["unresolved_bytes"] = len(data) - reader.offset
    row["remaining_hex"] = data[reader.offset:].hex()
    return row


def instance_prefix(data):
    reader = Reader(data)
    row = {name: reader.text() for name in ("schema", "instance_id", "definition_id")}
    row["consumed_bytes"] = reader.offset
    row["unresolved_bytes"] = len(data) - reader.offset
    return row


def block_stream(data, definitions):
    reader = Reader(data)
    header = {"block_size": reader.number("I"), "header_word_a": reader.number("I"), "header_word_b": reader.number("I"), "header_word_c": reader.number("I")}
    block_size = header["block_size"]
    if block_size < 8 or (len(data) - 16) % block_size:
        raise ValueError("Property block size does not divide stream")
    blocks = []
    payloads = []
    for index in range((len(data) - 16) // block_size):
        start = reader.offset
        next_index, used, flags = reader.number("I"), reader.number("H"), reader.number("H")
        if used > block_size - 8:
            raise ValueError("Property block length exceeds capacity")
        payload = reader.take(block_size - 8)
        blocks.append({"index": index, "offset": start, "next_index": next_index, "used_length": used, "flags": flags, "unused_storage_bytes": block_size - 8 - used})
        payloads.append(payload[:used])
    records = []
    visited = set()
    for block in blocks:
        if not block["flags"] & 1:
            continue
        indices, parts, index = [], [], block["index"]
        while index != 0xffffffff:
            if index >= len(blocks) or index in visited:
                raise ValueError("Property chain is invalid, shared or cyclic")
            visited.add(index)
            indices.append(index)
            parts.append(payloads[index])
            index = blocks[index]["next_index"]
        payload = b"".join(parts)
        row = {"root": block["index"], "blocks": indices, "logical_size": len(payload), "logical_sha256": hashlib.sha256(payload).hexdigest()}
        row["decoded"] = definition(payload) if definitions else instance_prefix(payload)
        records.append(row)
    return {"header": header, "blocks": blocks, "records": records, "unvisited_blocks": sorted(set(range(len(blocks))) - visited), "unused_storage_bytes": sum(block["unused_storage_bytes"] for block in blocks)}
