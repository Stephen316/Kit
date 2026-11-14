import struct
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from convert.formats.Fusion.DrawingCodec.Dwg.ReadDwgInventory import ReadInventory
from convert.formats.Fusion.DrawingCodec.Dwg.Integrity.CrcSixteen import CrcSixteen
from ProtoBits import Reader, Writer

FIXED = {
    0x01: 'TEXT', 0x02: 'ATTRIB', 0x03: 'ATTDEF', 0x04: 'BLOCK', 0x05: 'ENDBLK', 0x06: 'SEQEND',
    0x07: 'INSERT', 0x08: 'MINSERT', 0x0A: 'VERTEX_2D', 0x0B: 'VERTEX_3D', 0x0C: 'VERTEX_MESH',
    0x0D: 'VERTEX_PFACE', 0x0E: 'VERTEX_PFACE_FACE', 0x0F: 'POLYLINE_2D', 0x10: 'POLYLINE_3D',
    0x11: 'ARC', 0x12: 'CIRCLE', 0x13: 'LINE', 0x14: 'DIMENSION_ORDINATE', 0x15: 'DIMENSION_LINEAR',
    0x16: 'DIMENSION_ALIGNED', 0x17: 'DIMENSION_ANG3PT', 0x18: 'DIMENSION_ANG2LN',
    0x19: 'DIMENSION_RADIUS', 0x1A: 'DIMENSION_DIAMETER', 0x1B: 'POINT', 0x1C: '3DFACE',
    0x1D: 'POLYLINE_PFACE', 0x1E: 'POLYLINE_MESH', 0x1F: 'SOLID', 0x20: 'TRACE', 0x21: 'SHAPE',
    0x22: 'VIEWPORT', 0x23: 'ELLIPSE', 0x24: 'SPLINE', 0x25: 'REGION', 0x26: '3DSOLID', 0x27: 'BODY',
    0x28: 'RAY', 0x29: 'XLINE', 0x2A: 'DICTIONARY', 0x2B: 'OLEFRAME', 0x2C: 'MTEXT', 0x2D: 'LEADER',
    0x2E: 'TOLERANCE', 0x2F: 'MLINE', 0x30: 'BLOCK_CONTROL', 0x31: 'BLOCK_HEADER',
    0x32: 'LAYER_CONTROL', 0x33: 'LAYER', 0x34: 'STYLE_CONTROL', 0x35: 'STYLE', 0x38: 'LTYPE_CONTROL',
    0x39: 'LTYPE', 0x3C: 'VIEW_CONTROL', 0x3D: 'VIEW', 0x3E: 'UCS_CONTROL', 0x3F: 'UCS',
    0x40: 'VPORT_CONTROL', 0x41: 'VPORT', 0x42: 'APPID_CONTROL', 0x43: 'APPID',
    0x44: 'DIMSTYLE_CONTROL', 0x45: 'DIMSTYLE', 0x46: 'VX_CONTROL', 0x47: 'VX_TABLE_RECORD',
    0x48: 'GROUP', 0x49: 'MLINESTYLE', 0x4A: 'OLE2FRAME', 0x4C: 'LONG_TRANSACTION',
    0x4D: 'LWPOLYLINE', 0x4E: 'HATCH', 0x4F: 'XRECORD', 0x50: 'ACDBPLACEHOLDER',
    0x51: 'VBA_PROJECT', 0x52: 'LAYOUT',
}
ENTITY_FIXED = set(range(0x01, 0x2A)) | {0x2C, 0x2D, 0x2E, 0x2F, 0x4D, 0x4E, 0x2B, 0x4A}
ENTITY_FIXED -= {0x2A}


def handle_map(data):
    pairs = []
    offset = 0
    while True:
        size = struct.unpack_from('>H', data, offset)[0]
        body = data[offset:offset + size]
        pos = 2
        handle = 0
        location = 0
        while pos < size:
            r = Reader(body, pos * 8)
            step = r.UMC()
            delta = r.MC()
            pos = r.pos // 8
            handle += step
            location += delta
            pairs.append((handle, location))
        offset += size + 2
        if size == 2:
            break
    return pairs


def read_ms(data, offset):
    value = 0
    shift = 0
    while True:
        word = struct.unpack_from('<H', data, offset)[0]
        offset += 2
        value |= (word & 0x7FFF) << shift
        shift += 15
        if not word & 0x8000:
            return value, offset


def read_umc(data, offset):
    value = 0
    shift = 0
    while True:
        byte = data[offset]
        offset += 1
        value |= (byte & 0x7F) << shift
        shift += 7
        if not byte & 0x80:
            return value, offset


class Model:
    def __init__(self, path):
        self.content = Path(path).read_bytes()
        self.inv = ReadInventory(self.content)
        self.named = {s.SectionInfo.SectionName: s.DataValue for s in self.inv.Sections}
        self.objects_data = self.named['AcDb:AcDbObjects']
        self.pairs = handle_map(self.named['AcDb:Handles'])
        self.classes = {row.ClassNumber: row for row in self.inv.ClassTable.ClassRows}

    def type_name(self, number):
        if number in FIXED:
            return FIXED[number]
        if number >= 500 and number in self.classes:
            return self.classes[number].DxfName
        return 'UNKNOWN_%d' % number

    def is_entity(self, number):
        if number in self.classes:
            return self.classes[number].ItemClassId == 0x1F2
        return number in ENTITY_FIXED

    def split(self, handle, offset):
        data = self.objects_data
        size, pos = read_ms(data, offset)
        hsize, pos = read_umc(data, pos)
        body_start = pos
        body = data[pos:pos + size]
        crc = struct.unpack_from('<H', data, pos + size)[0]
        crc_ok = CrcSixteen(0xC0C1, data[offset:pos + size]) == crc
        total_bits = size * 8
        data_bits = total_bits - hsize
        r = Reader(body, 0, data_bits)
        number = r.OT()
        own = r.H()
        flag_pos = data_bits - 1
        strings = None
        str_start = data_bits
        if data_bits > 0:
            flag = Reader(body, flag_pos, data_bits).B()
            if flag:
                sr = Reader(body, flag_pos - 16, flag_pos)
                str_size = sr.RS()
                cut = flag_pos - 16
                if str_size & 0x8000:
                    hr = Reader(body, flag_pos - 32, flag_pos - 16)
                    high = hr.RS()
                    str_size = (str_size & 0x7FFF) | (high << 15)
                    cut = flag_pos - 32
                str_start = cut - str_size
                strings = (str_start, cut)
            else:
                str_start = flag_pos
        hr = Reader(body, data_bits, total_bits)
        handles = []
        while total_bits - hr.pos >= 8:
            handles.append(hr.H())
        pad = hr.bits(total_bits - hr.pos)
        return {
            'handle': handle, 'offset': offset, 'size': size, 'hsize': hsize, 'number': number,
            'name': self.type_name(number), 'own': own, 'crc_ok': crc_ok, 'body': body,
            'data_bits': data_bits, 'strings': strings, 'str_start': str_start,
            'handles': handles, 'pad': pad, 'header_bits': r.pos,
        }


def main(path):
    model = Model(path)
    print(path, 'objects', len(model.pairs), 'first word', model.objects_data[:4].hex())
    counts = Counter()
    sizes = Counter()
    bad = []
    gaps = []
    ordered = sorted(model.pairs, key=lambda p: p[1])
    prev_end = 4
    for handle, offset in ordered:
        if offset != prev_end:
            gaps.append((handle, prev_end, offset))
        obj = model.split(handle, offset)
        counts[obj['name']] += 1
        sizes[obj['name']] += obj['size']
        if not obj['crc_ok'] or obj['own'][2] != handle or obj['pad'] != 0:
            bad.append((handle, obj['name'], obj['crc_ok'], obj['own'], obj['pad']))
        size_len = len(struct.pack('<H', 0))
        _, after_ms = read_ms(model.objects_data, offset)
        _, after_mc = read_umc(model.objects_data, after_ms)
        prev_end = after_mc + obj['size'] + 2
    print('end', prev_end, 'section', len(model.objects_data), 'gaps', gaps[:10], len(gaps))
    print('bad', bad[:10], len(bad))
    for name, count in counts.most_common():
        print('  %-45s %5d %8d' % (name, count, sizes[name]))


if __name__ == '__main__':
    main(sys.argv[1])
