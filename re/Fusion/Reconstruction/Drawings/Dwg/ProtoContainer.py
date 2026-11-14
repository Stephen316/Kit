import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / 'src'))

from convert.formats.Fusion.DrawingCodec.Dwg.ReadDwgInventory import ReadInventory
from convert.formats.Fusion.DrawingCodec.Dwg.Header.MakeCryptMask import MakeCryptMask


def take_byte(data, pos):
    return data[pos]


def read_zero_run(data, pos):
    total = 0
    while data[pos] == 0:
        total += 0xFF
        pos += 1
    return total + data[pos], pos + 1


def read_extended(data, pos):
    if data[pos] != 0:
        return data[pos], pos + 1
    run, pos = read_zero_run(data, pos + 1)
    return run + 0xFF, pos


def read_literal(data, pos, op):
    if op != 0:
        return op + 3, pos
    run, pos = read_zero_run(data, pos)
    return run + 0x12, pos


def parse_stream(data):
    tokens = []
    pos = 0
    op = data[pos]
    pos += 1
    first = 0
    if op < 0x10:
        count, pos = read_literal(data, pos, op)
        first = count
        pos += count
        op = data[pos]
        pos += 1
    while op != 0x11:
        start = pos - 1
        if op >= 0x40:
            second = data[pos]
            distance = second << 2 | (op & 0x0C) >> 2
            length = (op >> 4) - 1
            trailing = op & 3
            pos += 1
            form = 'short'
        else:
            if op >= 0x21:
                length, bias, form = op - 0x1E, 0, 'mid'
            elif op == 0x20:
                extra, pos = read_extended(data, pos)
                length, bias, form = extra + 0x21, 0, 'midext'
            elif op >= 0x12:
                length, bias, form = (op & 0x0F) + 2, 0x3FFF, 'far'
            elif op == 0x10:
                extra, pos = read_extended(data, pos)
                length, bias, form = extra + 9, 0x3FFF, 'farext'
            else:
                raise ValueError('bad opcode %x at %d' % (op, pos - 1))
            b1, b2 = data[pos], data[pos + 1]
            distance = (b1 >> 2 | b2 << 6) + bias
            trailing = b1 & 3
            pos += 2
        literal = trailing
        if trailing == 0:
            op = data[pos]
            pos += 1
            if op < 0x10:
                literal, pos = read_literal(data, pos, op)
            else:
                tokens.append((length, distance, 0, form, data[start:pos - 1]))
                continue
        tokens.append((length, distance, literal, form, data[start:pos]))
        pos += literal
        op = data[pos]
        pos += 1
    return first, tokens, pos


def encode_zero_run(value):
    out = bytearray()
    while value > 0xFF:
        out.append(0)
        value -= 0xFF
    out.append(value)
    return bytes(out)


def encode_literal_count(count):
    if count <= 0x12:
        return bytes([count - 3])
    return b'\x00' + encode_zero_run(count - 0x12)


def encode_extended(value):
    if 0 < value <= 0xFF:
        return bytes([value])
    return b'\x00' + encode_zero_run(value - 0xFF)


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
    if length <= 17:
        head = bytes([0x10 | (length - 2)])
    else:
        head = b'\x10' + encode_extended(length - 9)
    return head + bytes([(far & 0x3F) << 2 | trailing, far >> 6])


def encode_tokens(first, tokens, raw_literals):
    out = bytearray()
    lit_iter = iter(raw_literals)
    if first:
        out += encode_literal_count(first) + next(lit_iter)
    for length, distance, literal, form, original in tokens:
        trailing = literal if 0 < literal <= 3 else 0
        out += encode_match(length, distance, trailing)
        if literal > 3:
            out += encode_literal_count(literal)
        if literal:
            out += next(lit_iter)
    out.append(0x11)
    return bytes(out)


def literal_bytes(data, first, tokens):
    result = []
    pos = 0
    op = data[0]
    pos = 1
    if first:
        _, pos = read_literal(data, 1, op)
        result.append(data[pos:pos + first])
        pos += first
    return result


def check_page(packed):
    first, tokens, end = parse_stream(packed)
    stats = {'tokens': len(tokens), 'end': end, 'size': len(packed)}
    rebuilt = bytearray()
    mismatch = 0
    forms = {}
    for length, distance, literal, form, original in tokens:
        trailing = literal if 0 < literal <= 3 else 0
        mine = encode_match(length, distance, trailing)
        if literal > 3:
            mine += encode_literal_count(literal)
        if mine != original:
            mismatch += 1
            forms[form] = forms.get(form, 0) + 1
    stats['mismatch'] = mismatch
    stats['forms'] = forms
    return stats


def main(path):
    content = Path(path).read_bytes()
    inv = ReadInventory(content)
    covered = bytearray(len(content))
    print(path, len(content), inv.FileHeader.VersionText)
    print('crypt', inv.CryptHeader)
    for page in inv.MapPages:
        print('page', page.PageNumber, page.PageSize, page.FileOffset)
    for section in inv.Sections:
        info = section.SectionInfo
        for page in section.DataPages:
            mask = 0x4164536B ^ page.FileOffset
            packed = content[page.FileOffset + 32: page.FileOffset + 32 + page.DataSize]
            pad = content[page.FileOffset + 32 + page.DataSize: page.FileOffset + page.PageSize]
            note = ''
            if info.CompressFlag == 2:
                stats = check_page(packed)
                note = stats
            print(info.SectionName, page.PageNumber, page.DataSize, page.PageSize, len(pad), pad[:16].hex(), note)


if __name__ == '__main__':
    main(sys.argv[1])
