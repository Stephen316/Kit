import hashlib
import struct
import sys
from binascii import crc32
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from convert.formats.Fusion.DrawingCodec.Dwg.ReadDwgInventory import ReadInventory
from convert.formats.Fusion.DrawingCodec.Dwg.Header.MakeCryptMask import MakeCryptMask
from convert.formats.Fusion.DrawingCodec.Dwg.Integrity.PageChecksum import PageChecksum
from convert.formats.Fusion.DrawingCodec.Dwg.Inflate.InflatePage import InflatePage
from ProtoContainer import parse_stream, encode_literal_count, encode_extended

MASK = MakeCryptMask(0x10000)
MAGIC = bytes.fromhex('f8466a0496730ed9162f6768d4f74a4ad0576876')
DATA_PAGE = 0x4163043B
PAGE_MAP = 0x41630E3B
SECTION_MAP = 0x4163003B


def encode_match(length, distance, trailing):
    if 3 <= length <= 14 and distance <= 0x3FF:
        return bytes([((length + 1) << 4) | ((distance & 3) << 2) | trailing, distance >> 2])
    if distance <= 0x3FFF:
        if length <= 33:
            head = bytes([length + 0x1E])
        else:
            head = b'\x20' + encode_extended(length - 0x21)
        return head + bytes([(distance & 0x3F) << 2 | trailing, distance >> 6])
    far = distance - 0x3FFF
    if length <= 9:
        head = bytes([0x10 | (length - 2)])
    else:
        head = b'\x10' + encode_extended(length - 9)
    return head + bytes([(far & 0x3F) << 2 | trailing, far >> 6])


def plan_of(packed):
    first, tokens, end = parse_stream(packed)
    return first, tuple((length, distance, literal) for length, distance, literal, _, _ in tokens)


def compress(data, plan):
    first, tokens = plan
    out = bytearray()
    pos = 0
    if first:
        out += encode_literal_count(first) + data[:first]
        pos = first
    for length, distance, literal in tokens:
        trailing = literal if 0 < literal <= 3 else 0
        out += encode_match(length, distance, trailing)
        pos += length
        if literal > 3:
            out += encode_literal_count(literal)
        out += data[pos:pos + literal]
        pos += literal
    if pos != len(data):
        raise ValueError('plan covers %d of %d bytes' % (pos, len(data)))
    out += b'\x11\x00\x00'
    return bytes(out)


def read_layout(content):
    inv = ReadInventory(content)
    pages = []
    by_number = {}
    for section in inv.Sections:
        for page, ref in zip(section.DataPages, section.SectionInfo.PageRefs):
            by_number[page.PageNumber] = (section, page, ref)
    for map_page in inv.MapPages:
        offset = map_page.FileOffset
        word = struct.unpack_from('<I', content, offset)[0]
        if map_page.PageNumber in by_number:
            section, page, ref = by_number[map_page.PageNumber]
            info = section.SectionInfo
            packed = content[offset + 32: offset + 32 + page.DataSize]
            start = ref.StartOffset
            needed = min(info.MaxPageSize, info.DataSize - start)
            if info.CompressFlag == 2:
                raw = InflatePage(packed, info.MaxPageSize)
                plan = plan_of(packed)
            else:
                raw = packed
                plan = None
            pages.append({'kind': 'data', 'number': map_page.PageNumber, 'size': map_page.PageSize,
                          'section': info.SectionName, 'section_id': info.SectionId, 'start': start,
                          'raw': raw, 'plan': plan, 'needed': needed})
        else:
            head = struct.unpack_from('<5I', content, offset)
            packed = content[offset + 20: offset + 20 + head[2]]
            raw = InflatePage(packed, head[1])
            used = 20 + head[2]
            if head[0] == PAGE_MAP:
                slack = content[offset + used: inv.CryptHeader.SecondAddress]
            else:
                slack = content[offset + used: offset + map_page.PageSize]
            pages.append({'kind': 'system', 'type': head[0], 'number': map_page.PageNumber,
                          'size': map_page.PageSize, 'raw': raw, 'plan': plan_of(packed), 'slack': slack})
    return inv, pages


def slack_standard(length, last):
    block = struct.pack('<5I', 0, 0, 0, 2, 0)
    return block, MASK[:max(0, length - 20)]


def emit(content, inv, pages):
    out = bytearray(content[:0x80])
    crypt = content[0x80:0x80 + 0x6C]
    out += crypt
    out += MAGIC
    for page in pages:
        offset = len(out)
        if page['kind'] == 'data':
            raw = page['raw']
            if page['plan'] is not None:
                packed = compress(raw, page['plan'])
            else:
                packed = raw
            data_check = PageChecksum(0, packed)
            words = [DATA_PAGE, page['section_id'], len(packed), page['size'], page['start'] & 0xFFFFFFFF, page['start'] >> 32, 0, data_check]
            head = struct.pack('<8I', *words)
            words[6] = PageChecksum(data_check, head)
            mask = 0x4164536B ^ offset
            out += struct.pack('<8I', *[w ^ mask for w in words])
            out += packed
            out += MASK[:page['size'] - 32 - len(packed)]
        else:
            packed = compress(page['raw'], page['plan'])
            head = struct.pack('<5I', page['type'], len(page['raw']), len(packed), 2, 0)
            check = PageChecksum(PageChecksum(0, head), packed)
            out += struct.pack('<5I', page['type'], len(page['raw']), len(packed), 2, check)
            out += packed
            out += page['slack']
    out += crypt
    return bytes(out)


def main(paths):
    for path in paths:
        content = Path(path).read_bytes()
        inv, pages = read_layout(content)
        again = emit(content, inv, pages)
        same = again == content
        first = next((i for i in range(min(len(again), len(content))) if again[i] != content[i]), None)
        print(Path(path).name, len(content), len(again), 'exact' if same else 'DIFF at %s' % first)
        modern = all(p['slack'][:20] == struct.pack('<5I', p['type'], 0, 0, 2, 0) and p['slack'][20:] == MASK[:len(p['slack']) - 20]
                     for p in pages if p['kind'] == 'system')
        print('  standard slack', modern, [(p['type'], len(p['slack'])) for p in pages if p['kind'] == 'system'])


if __name__ == '__main__':
    main(sys.argv[1:])
