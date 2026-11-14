import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from ProtoBits import Reader, Writer
from ProtoObjects import read_ms, read_umc, handle_map
from convert.formats.Fusion.DrawingCodec.Dwg.Integrity.CrcSixteen import CrcSixteen


class Obj:
    __slots__ = ('number', 'handle', 'body', 'body_bits', 'strings', 'handles', 'string_flag')

    def __init__(self, number, handle, body, body_bits, strings, handles, string_flag):
        self.number = number
        self.handle = handle
        self.body = body
        self.body_bits = body_bits
        self.strings = strings
        self.handles = handles
        self.string_flag = string_flag


def decode_object(data, offset):
    size, pos = read_ms(data, offset)
    hsize, pos = read_umc(data, pos)
    body = data[pos:pos + size]
    total = size * 8
    data_bits = total - hsize
    r = Reader(body, 0, data_bits)
    number = r.OT()
    own = r.H()
    head_end = r.pos
    flag = Reader(body, data_bits - 1, data_bits).B()
    strings = ()
    if flag:
        cut = data_bits - 1 - 16
        str_size = Reader(body, cut, data_bits - 1).RS()
        if str_size & 0x8000:
            raise ValueError('long string stream')
        start = cut - str_size
        sr = Reader(body, start, cut)
        items = []
        while sr.pos < cut:
            items.append(sr.TU())
        strings = tuple(items)
        body_end = start
    else:
        body_end = data_bits - 1
    br = Reader(body, head_end, body_end)
    body_value = br.bits(body_end - head_end)
    hr = Reader(body, data_bits, total)
    handles = []
    while total - hr.pos >= 8:
        handles.append(hr.H())
    end = pos + size + 2
    return Obj(number, own[2], body_value, body_end - head_end, strings, tuple(handles), flag), end


def encode_object(obj):
    w = Writer()
    w.OT(obj.number)
    w.H((0, (obj.handle.bit_length() + 7) // 8, obj.handle))
    w.bits(obj.body, obj.body_bits)
    if obj.string_flag:
        sw = Writer()
        for text in obj.strings:
            sw.TU(text)
        w.bits(sw.value, sw.count)
        w.RS(sw.count)
        w.B(1)
    else:
        w.B(0)
    data_bits = w.count
    for ref in obj.handles:
        w.H(ref)
    pad = -w.count & 7
    w.bits((1 << pad) - 1, pad)
    body = w.tobytes()
    hsize = w.count - data_bits
    head = encode_ms(len(body)) + encode_umc(hsize)
    crc = CrcSixteen(0xC0C1, head + body)
    return head + body + struct.pack('<H', crc)


def encode_ms(value):
    out = bytearray()
    while True:
        word = value & 0x7FFF
        value >>= 15
        if value:
            out += struct.pack('<H', word | 0x8000)
        else:
            out += struct.pack('<H', word)
            return bytes(out)


def encode_umc(value):
    out = bytearray()
    while True:
        byte = value & 0x7F
        value >>= 7
        if value:
            out.append(byte | 0x80)
        else:
            out.append(byte)
            return bytes(out)


def encode_smc(value):
    negative = value < 0
    value = abs(value)
    out = bytearray()
    while value >= 0x40:
        out.append(value & 0x7F | 0x80)
        value >>= 7
    out.append(value | (0x40 if negative else 0))
    return bytes(out)


def decode_objects(section):
    if struct.unpack_from('<I', section, 0)[0] != 0x0DCA:
        raise ValueError('objects marker')
    objects = []
    offset = 4
    while offset < len(section):
        obj, offset = decode_object(section, offset)
        objects.append(obj)
    return objects


def encode_objects(objects):
    out = bytearray(struct.pack('<I', 0x0DCA))
    offsets = {}
    for obj in objects:
        offsets[obj.handle] = len(out)
        out += encode_object(obj)
    return bytes(out), offsets


def encode_handle_map(offsets, limit=2032):
    out = bytearray()
    block = bytearray()
    last_handle = 0
    last_offset = 0
    for handle in sorted(offsets):
        block += encode_umc(handle - last_handle) + encode_smc(offsets[handle] - last_offset)
        last_handle = handle
        last_offset = offsets[handle]
        if len(block) + 2 >= limit:
            out += flush(block)
            block = bytearray()
            last_handle = 0
            last_offset = 0
    if block:
        out += flush(block)
    out += flush(bytearray())
    return bytes(out)


def flush(block):
    size = len(block) + 2
    head = struct.pack('>H', size) + bytes(block)
    return head + struct.pack('>H', CrcSixteen(0xC0C1, head))
