"""Same-length scrubber for account residue inside Fusion-saved archives.

Fusion copies uninitialized heap bytes into protein asset members, and those
bytes can hold account identifiers, home paths and cloud document ids. Every
rule here is generic: it keys on JSON field names, path shapes and URN
prefixes, never on a particular account. Replacements keep byte lengths so
length prefixes and offsets inside members stay valid. Unchanged members are
copied byte for byte; changed members are recompressed with their original
method, and every header field other than CRC, sizes and offsets is kept.

Usage: python3.14 ScrubSaved.py [--dry-run] [--ledger PATH] ARCHIVE...
All archives in one run share one placeholder map, so a cloud id that appears
in several archives receives the same placeholder in each of them. The ledger,
ScrubLedger.json beside this script unless --ledger names another, lists every
placeholder already written. Values that lie inside a listed placeholder are
left unchanged, so a second run over a scrubbed archive changes no byte.
"""

import argparse
import hashlib
import hmac
import io
import json
import re
import secrets
import struct
import sys
import zipfile
import zlib
from compression import zstd
from pathlib import Path

ACCOUNT_KEYS = (
    "hubId",
    "hubIdHashed",
    "spaceCollectionId",
    "hubEdition",
    "user_id",
    "userId",
    "ownerId",
    "oxygenId",
    "fileId",
    "teamProjectID",
    "lineageHash",
    "user_hub_urn",
    "user_hub_id",
    "session_id",
)
NAME_KEYS = (
    "ownerName",
    "userName",
    "user_name",
    "displayUserName",
    "createUserName",
    "lastModifiedUserName",
    "lastUpdateUserName",
    "creatorName",
    "authorName",
    "fullName",
    "firstName",
    "lastName",
)
RULES = ("account", "partial", "bare", "name", "home", "urn", "echo")
ORDER = ("urn", "account", "partial", "bare", "name", "home", "echo")
MIN_KEY_TAIL = 4
MIN_PARTIAL_KEY = 2
MIN_LEARNED = 6
MIN_FRAGMENT = 7
MIN_HEX_FRAGMENT = 10
MAX_DEPTH = 4
LOCAL = struct.Struct("<4sHHHHHLLLHH")
CENTRAL = struct.Struct("<4sHHHHHHLLLHHHHHLL")
END = struct.Struct("<4sHHHHLLH")
LOCAL_SIG = b"PK\x03\x04"
CENTRAL_SIG = b"PK\x01\x02"
END_SIG = b"PK\x05\x06"
DESCRIPTOR_SIG = b"PK\x07\x08"
STORE = struct.Struct("<4L")
BLOCK = struct.Struct("<LHH")
STORE_HEADER = (136, 0xFFFFFFFF, 0xFFFFFFFF, 0)
BLOCK_SIZE = 136
BLOCK_CAPACITY = 128
DEFLATE_LEVELS = {0: 6, 2: 9, 4: 2, 6: 1}
HOME_PLACEHOLDER = b"user"
REASON = (
    "Fusion copies uninitialized heap bytes with account identifiers, home paths and cloud ids into saved archives, so these fixtures were rewritten with same-length placeholders before publication. "
    "Protein AssetData property stores are a 16-byte header followed by 136-byte blocks, and each block's 8-byte header records how many of its 128 capacity bytes are used; "
    "the truncated-key rule reads only the unused capacity after those bytes, and the bare-value rule accepts a value only when its quote, colon and quote begin exactly where that unused capacity begins. "
    "In AssetData members that are not block stores, the truncated-key rule reads the whole member and the bare-value rule is off. "
    "The placeholders list holds every placeholder already written, and values inside those placeholders are left unchanged, so a second run makes no replacement."
)


def suffixes(keys, minimum):
    return {key[start:] for key in keys for start in range(len(key) - minimum + 1)}


def prefixes(keys, minimum):
    return {key[:end] for key in keys for end in range(minimum, len(key) + 1)}


def key_tails(keys):
    tails = {key[start:] for key in keys if key.lower().endswith("id") for start in range(1, len(key) - MIN_KEY_TAIL + 1)}
    return b"|".join(re.escape(tail.encode()) for tail in sorted(tails, key=lambda tail: (-len(tail), tail)))


def alternation(keys):
    return b"|".join(re.escape(key.encode()) for key in sorted(keys, key=lambda key: (-len(key), key)))


def wide(pattern):
    return b"".join(re.escape(bytes([byte])) + b"\x00" for byte in pattern)


ACCOUNT = re.compile(rb"(?:" + alternation(ACCOUNT_KEYS) + rb')"\s*:\s*("?)([A-Za-z0-9_.+/=-]+)')
ACCOUNT_TAIL = re.compile(rb"(?:" + key_tails(ACCOUNT_KEYS) + rb')"\s*:\s*("?)([A-Za-z0-9_.+/=-]*[0-9][A-Za-z0-9_.+/=-]*)')
PARTIAL = re.compile(
    rb'(?<![A-Za-z0-9_"])(?:(?:'
    + alternation(suffixes(ACCOUNT_KEYS, MIN_PARTIAL_KEY))
    + rb')"\s*:\s*"([A-Za-z0-9_.+/=-]+)|(?:'
    + alternation(suffixes(NAME_KEYS, MIN_PARTIAL_KEY))
    + rb')"\s*:\s*"([^"\x00-\x1f]{1,80}))'
)
BARE = re.compile(rb'"\s*:\s*"([A-Za-z0-9]{6,40})(?:"|\Z)')
DIGIT = re.compile(rb"[0-9]")
ID_SHAPE = re.compile(rb"(?=[A-Za-z0-9_=-]*[0-9])(?=[A-Za-z0-9_=-]*[A-Za-z])[A-Za-z0-9_=-]{6,}")
ASSET_DATA = re.compile(rb"(?:^|/)AssetData/[^/]+\.bin$")
NAMED = re.compile(rb"(?:" + alternation(NAME_KEYS) + rb')"\s*:\s*"([^"\x00-\x1f]{1,80})')
NEXT_KEY = rb'"\s*,\s*"(?:(?:' + alternation(ACCOUNT_KEYS) + rb')"|(?:' + alternation(prefixes(ACCOUNT_KEYS, MIN_PARTIAL_KEY)) + rb')\Z)'
ACCOUNT_LEAD = re.compile(rb"(?<![\x20-\x7e])((?=[A-Za-z0-9_=-]*[0-9])[A-Za-z0-9_=-]{3,80})" + NEXT_KEY)
QUOTED_LEAD = re.compile(rb'(?<![\x20-\x7e])"((?=[A-Za-z0-9_=-]*[0-9])[A-Za-z0-9_=-]{3,80})' + NEXT_KEY)
HEX_LEAD = re.compile(rb"(?<![0-9a-f])([0-9a-f]{%d,80})" % MIN_HEX_FRAGMENT + NEXT_KEY)
HEX_RUN = re.compile(rb"[0-9a-f]{%d,}" % MIN_HEX_FRAGMENT)
OWNER = b'","ownerId"'
LINK = (b"?show=", b"?version=")
NAME_BYTES = re.compile(rb'[^"\x00-\x1f]')
LINK_BYTES = re.compile(rb"[A-Za-z0-9_=-]")
LITERALS = (b"true", b"false", b"null")
HOME = re.compile(rb"[\\/]{1,2}Users[\\/]{1,2}([A-Za-z0-9._-]+)")
HOME_WIDE = re.compile(rb"(?:[\\/]\x00){1,2}" + wide(b"Users") + rb"(?:[\\/]\x00){1,2}((?:[A-Za-z0-9._-]\x00)+)")
URN_PREFIX = rb"(?:dm\.(?:lineage|folder|version):|fs\.(?:file|folder):[a-z]{2}\.|wip\.dm\.[a-z]+:|prod\.project:|lineage:|versionedFile:)"
URN = re.compile(URN_PREFIX + rb"([A-Za-z0-9_-]{6,})")
URN_WIDE = re.compile(
    rb"(?:"
    + b"|".join(
        wide(prefix)
        for prefix in (b"dm.lineage:", b"dm.folder:", b"dm.version:", b"fs.file:vf.", b"fs.folder:co.", b"prod.project:", b"lineage:", b"versionedFile:")
    )
    + rb")((?:[A-Za-z0-9_-]\x00){6,})"
)
HUB = re.compile(rb"(?<![A-Za-z0-9])a\.((?:YnVzaW5lc3M|cGVyc29uYWw|cHJvamVjd)[A-Za-z0-9_=-]*)")
PROJECT = re.compile(rb"(?<![A-Za-z0-9])b\.([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})")
SYNTHETIC = re.compile(rb"(?:Kit|Synthetic)[A-Za-z]*[0-9]*")
SHARED = (b"Shared", HOME_PLACEHOLDER)


def keep(value):
    return SYNTHETIC.fullmatch(value) is not None or value in LITERALS


def backward(blob, marker, allowed, limit, minimum):
    found = []
    start = blob.find(marker)
    while start >= 0:
        cursor = start
        while cursor > 0 and start - cursor < limit and allowed.fullmatch(blob[cursor - 1 : cursor]):
            cursor -= 1
        if start - cursor >= minimum:
            found.append((cursor, start))
        start = blob.find(marker, start + 1)
    return found


class Masker:
    def __init__(self, key, placeholders=()):
        self.key = key
        self.learned = set()
        self.cache = {}
        self.echo = None
        self.anchors = {}
        self.written = set()
        self.listed = b"\x00" + b"\x00".join(sorted(placeholders)) + b"\x00"

    def known(self, value):
        return bool(value) and value in self.listed

    def learn(self, value, minimum=MIN_LEARNED):
        if len(value) >= minimum and not keep(value):
            self.learned.add(value)

    def seal(self):
        values = sorted(self.learned, key=lambda value: (-len(value), value))
        kept = []
        for value in values:
            if not any(value != other and (other.startswith(value) or other.endswith(value)) for other in kept):
                kept.append(value)
        self.learned = kept
        anchors = {}
        for value in kept:
            mask = self.fresh(value)
            for form, cover, step in ((value, mask, 1), (value.decode("latin-1").encode("utf-16-le"), mask.decode("latin-1").encode("utf-16-le"), 2)):
                size = MIN_FRAGMENT * step
                if len(form) <= size or value.isdigit():
                    anchors.setdefault(form, []).append((0, form, cover, step, value))
                    continue
                for offset in range(0, len(form) - size + 1, step):
                    anchors.setdefault(form[offset : offset + size], []).append((offset, form, cover, step, value))
        self.anchors = anchors
        if anchors:
            self.echo = re.compile(b"|".join(re.escape(anchor) for anchor in sorted(anchors, key=lambda anchor: (-len(anchor), anchor))))

    def fresh(self, value):
        if value in self.cache:
            return self.cache[value]
        counter = 0
        while True:
            digest = b""
            block = 0
            while len(digest) < len(value):
                digest += hmac.new(self.key, value + bytes([counter, block]), hashlib.sha256).digest()
                block += 1
            mask = render(value, digest)
            if mask != value or not any(chr(byte).isalnum() for byte in value):
                self.cache[value] = mask
                return mask
            counter += 1

    def canon(self, value):
        if len(value) >= 3:
            for other in self.learned:
                if other.startswith(value):
                    return self.fresh(other)[: len(value)]
                if other.endswith(value):
                    return self.fresh(other)[len(other) - len(value) :]
        return self.fresh(value)


def render(value, digest):
    shape, allowed = alphabet(value)
    hexdigits = bytes(sorted(byte for byte in allowed if chr(byte).isalnum()))
    output = bytearray()
    for index, byte in enumerate(value):
        pick = digest[index]
        if shape == "hex" and chr(byte).isalnum():
            output.append(hexdigits[pick % 16])
        elif 48 <= byte <= 57:
            output.append(48 + pick % 10)
        elif 65 <= byte <= 90:
            output.append(65 + pick % 26)
        elif 97 <= byte <= 122 or byte >= 128:
            output.append(97 + pick % 26)
        else:
            output.append(byte)
    return bytes(output)


def home_mask(name):
    return (HOME_PLACEHOLDER + b"_" * len(name))[: len(name)]


def residue(payload, parent, name):
    if not parent.endswith(b".protein") or not ASSET_DATA.search(name):
        return [], False
    whole = [(0, len(payload))]
    if len(payload) < STORE.size or STORE.unpack_from(payload) != STORE_HEADER or (len(payload) - STORE.size) % BLOCK_SIZE:
        return whole, False
    regions = []
    for base in range(STORE.size, len(payload), BLOCK_SIZE):
        _, used, flags = BLOCK.unpack_from(payload, base)
        if used > BLOCK_CAPACITY or flags not in (0, 1):
            return whole, False
        if used < BLOCK_CAPACITY:
            regions.append((base + BLOCK.size + used, base + BLOCK_SIZE))
    return regions, True


def keyed(blob, regions, delimited):
    found = []
    seen = set()
    for pattern in (ACCOUNT, ACCOUNT_TAIL):
        for match in pattern.finditer(blob):
            value = match.group(2)
            if keep(value) or match.start(2) in seen:
                continue
            seen.add(match.start(2))
            if match.group(1) or DIGIT.search(value):
                found.append(("account", match.start(2), match.end(2), 1, True))
    for low, high in regions:
        chunk = blob[low:high]
        for match in PARTIAL.finditer(chunk):
            group = 1 if match.group(1) is not None else 2
            start, end = low + match.start(group), low + match.end(group)
            value = match.group(group)
            if start in seen or keep(value):
                continue
            seen.add(start)
            found.append(("partial", start, end, 1, group == 1 and ID_SHAPE.fullmatch(value) is not None))
        bare = BARE.match(chunk) if delimited else None
        if bare and low + bare.start(1) not in seen and not keep(bare.group(1)):
            seen.add(low + bare.start(1))
            found.append(("bare", low + bare.start(1), low + bare.end(1), 1, ID_SHAPE.fullmatch(bare.group(1)) is not None))
    for pattern in (ACCOUNT_LEAD, QUOTED_LEAD, HEX_LEAD):
        for match in pattern.finditer(blob):
            value = match.group(1)
            if keep(value) or match.start(1) in seen:
                continue
            seen.add(match.start(1))
            teach = HEX_RUN.fullmatch(value) is not None or (pattern is QUOTED_LEAD and ID_SHAPE.fullmatch(value) is not None)
            found.append(("account", match.start(1), match.end(1), 1, teach))
    found += [("name", match.start(1), match.end(1), 1, True) for match in NAMED.finditer(blob)]
    found += [("name", start, end, 1, True) for start, end in backward(blob, OWNER, NAME_BYTES, 80, 1)]
    urns = [(match.start(1), match.end(1), 1) for pattern in (URN, HUB, PROJECT) for match in pattern.finditer(blob)]
    urns += [(match.start(1), match.end(1), 2) for match in URN_WIDE.finditer(blob)]
    urns += [(start, end, 1) for marker in LINK for start, end in backward(blob, marker, LINK_BYTES, 256, 6)]
    for start, end, step in urns:
        if not keep(blob[start:end][::step]):
            found.append(("urn", start, end, step, True))
    return found


def widened(mask, step):
    return mask.decode("latin-1").encode("utf-16-le") if step == 2 else mask


def find_spans(blob, masker, learn, regions=(), delimited=False):
    spans = {rule: [] for rule in RULES}
    for rule, start, end, step, teach in keyed(blob, regions, delimited):
        raw = blob[start:end]
        value = raw[::step]
        if masker.known(value):
            spans[rule].append((start, end, raw, None))
            continue
        if learn:
            if teach:
                masker.learn(value)
            continue
        mask = masker.canon(value)
        spans[rule].append((start, end, widened(mask, step), mask))
    if learn:
        return spans
    for pattern, step in ((HOME, 1), (HOME_WIDE, 2)):
        for match in pattern.finditer(blob):
            name = match.group(1)[::step]
            if name in SHARED or name == home_mask(name):
                continue
            spans["home"].append((match.start(1), match.end(1), widened(home_mask(name), step), None))
    spans["echo"] = echo_spans(blob, masker, regions)
    return spans


def alphabet(value):
    alnum = bytes(byte for byte in value if chr(byte).isalnum())
    extra = bytes(sorted({byte for byte in value if not chr(byte).isalnum()}))
    if alnum and re.fullmatch(rb"[0-9a-f]+", alnum):
        return "hex", set(b"0123456789abcdef" + extra)
    if alnum and re.fullmatch(rb"[0-9A-F]+", alnum):
        return "hex", set(b"0123456789ABCDEF" + extra)
    if alnum.isdigit():
        return "digits", set(b"0123456789" + extra)
    return "text", set(b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789" + extra)


def accept(blob, start, end, head, tail, shape):
    if head and tail:
        return True
    if shape == "digits":
        return False
    if shape == "hex" and end - start < MIN_HEX_FRAGMENT:
        if head and start > 0 and blob[start - 1 : start] in (b'"', b" "):
            return True
        return tail and blob[end : end + 1] == b'"'
    return True


def widen(blob, start, end, allowed, step, floor, ceiling):
    while start - step >= floor and blob[start - step] in allowed and (step == 1 or blob[start - 1] == 0):
        start -= step
    while end + step <= ceiling and blob[end] in allowed and (step == 1 or blob[end + 1] == 0):
        end += step
    return start, end


def echo_spans(blob, masker, regions):
    found = set()
    if masker.echo is None:
        return []
    for match in masker.echo.finditer(blob):
        floor, ceiling = next(((low, high) for low, high in regions if low <= match.start() and match.end() <= high), (None, None))
        if floor is None:
            continue
        for offset, form, cover, step, value in masker.anchors[match.group(0)]:
            start, end = match.start(), match.end()
            low, high = offset, offset + (end - start)
            while low >= step and start - step >= floor and blob[start - step : start] == form[low - step : low]:
                start, low = start - step, low - step
            while high + step <= len(form) and end + step <= ceiling and blob[end : end + step] == form[high : high + step]:
                end, high = end + step, high + step
            shape, allowed = alphabet(value)
            if masker.known(blob[start:end][::step]) or not accept(blob, start, end, low == 0, high == len(form), shape):
                continue
            wide_start, wide_end = widen(blob, start, end, allowed, step, floor, ceiling)
            if (wide_start, wide_end) != (start, end):
                text = blob[wide_start:wide_end][::step]
                if masker.known(text):
                    continue
                fresh = masker.fresh(text)
                found.add((wide_start, wide_end, widened(fresh, step), fresh))
            else:
                found.add((start, end, cover[low:high], cover[low:high][::step]))
    return sorted(found)


def apply_spans(blob, spans, counts, masker):
    taken = []
    output = bytearray(blob)
    for rule in ORDER:
        for start, end, mask, narrow in sorted(spans[rule], key=lambda span: span[:2]):
            if any(start < other_end and other_start < end for other_start, other_end in taken):
                continue
            if len(mask) != end - start:
                raise ValueError("placeholder length differs from the replaced span")
            taken.append((start, end))
            if blob[start:end] == mask:
                continue
            output[start:end] = mask
            counts[rule] += 1
            if narrow is not None:
                masker.written.add(narrow)
    return bytes(output)


class Entry:
    def __init__(self, blob, offset):
        fields = CENTRAL.unpack_from(blob, offset)
        if fields[0] != CENTRAL_SIG:
            raise ValueError("bad central directory signature")
        self.central = offset
        self.flags, self.method = fields[3], fields[4]
        self.crc, self.csize, self.usize = fields[7], fields[8], fields[9]
        self.length = CENTRAL.size + fields[10] + fields[11] + fields[12]
        self.name = blob[offset + CENTRAL.size : offset + CENTRAL.size + fields[10]]
        self.local = fields[16]
        if 0xFFFFFFFF in (self.csize, self.usize, self.local):
            raise ValueError("ZIP64 members are not supported")
        if self.flags & 1:
            raise ValueError("encrypted members are not supported")
        local = LOCAL.unpack_from(blob, self.local)
        if local[0] != LOCAL_SIG:
            raise ValueError("bad local header signature")
        self.data = self.local + LOCAL.size + local[9] + local[10]
        self.tail = self.data + self.csize
        self.descriptor = 0
        if self.flags & 8:
            self.descriptor = 16 if blob[self.tail : self.tail + 4] == DESCRIPTOR_SIG else 12
        self.end = self.tail + self.descriptor


def read_member(blob, entry):
    data = blob[entry.data : entry.tail]
    if entry.method == zipfile.ZIP_STORED:
        payload = data
    elif entry.method == zipfile.ZIP_DEFLATED:
        payload = zlib.decompress(data, -15)
    elif entry.method == zipfile.ZIP_ZSTANDARD:
        payload = zstd.decompress(data)
    else:
        raise ValueError(f"unsupported compression method {entry.method}")
    if zlib.crc32(payload) != entry.crc or len(payload) != entry.usize:
        raise ValueError("member CRC or size mismatch")
    return payload


def write_member(payload, entry):
    if entry.method == zipfile.ZIP_STORED:
        return payload
    if entry.method == zipfile.ZIP_DEFLATED:
        packer = zlib.compressobj(DEFLATE_LEVELS[entry.flags & 6], zlib.DEFLATED, -15)
        return packer.compress(payload) + packer.flush()
    return zstd.compress(payload)


def parse_archive(blob):
    end = blob.rfind(END_SIG, max(0, len(blob) - 65557))
    if end < 0:
        raise ValueError("missing end of central directory")
    fields = END.unpack_from(blob, end)
    if end + END.size + fields[7] != len(blob):
        raise ValueError("unexpected bytes after the archive comment")
    if end >= 20 and blob[end - 20 : end - 16] == b"PK\x06\x07":
        raise ValueError("ZIP64 archives are not supported")
    entries = []
    cursor = fields[6]
    for _ in range(fields[4]):
        entry = Entry(blob, cursor)
        entries.append(entry)
        cursor += entry.length
    if cursor != end:
        raise ValueError("central directory does not end at the end record")
    return entries, fields[6], end


def walk_archive(blob, masker, counts, learn, depth, parent=b""):
    entries, directory, end = parse_archive(blob)
    output = bytearray()
    moved = {}
    position = 0
    changed = False
    for entry in sorted(entries, key=lambda item: item.local):
        if entry.local < position:
            raise ValueError("overlapping archive members")
        output += blob[position : entry.local]
        moved[entry.central] = len(output)
        position = entry.end
        payload = read_member(blob, entry)
        fresh = walk_payload(payload, masker, counts, learn, depth, parent, entry.name)
        if learn or fresh == payload:
            output += blob[entry.local : entry.end]
            continue
        changed = True
        packed = write_member(fresh, entry)
        crc = zlib.crc32(fresh)
        header = bytearray(blob[entry.local : entry.data])
        if not entry.flags & 8 or struct.unpack_from("<L", header, 14)[0]:
            struct.pack_into("<LLL", header, 14, crc, len(packed), len(fresh))
        descriptor = bytearray(blob[entry.tail : entry.end])
        if entry.descriptor:
            struct.pack_into("<LLL", descriptor, entry.descriptor - 12, crc, len(packed), len(fresh))
        output += header + packed + descriptor
        entry.crc, entry.csize, entry.usize = crc, len(packed), len(fresh)
    if learn or not changed:
        return blob
    output += blob[position:directory]
    start = len(output)
    for entry in entries:
        record = bytearray(blob[entry.central : entry.central + entry.length])
        struct.pack_into("<LLL", record, 16, entry.crc, entry.csize, entry.usize)
        struct.pack_into("<L", record, 42, moved[entry.central])
        output += record
    record = bytearray(blob[end:])
    struct.pack_into("<L", record, 16, start)
    output += record
    check_archive(blob, bytes(output))
    return bytes(output)


def walk_payload(payload, masker, counts, learn, depth, parent, name):
    if payload[:4] == LOCAL_SIG and depth < MAX_DEPTH:
        return walk_archive(payload, masker, counts, learn, depth + 1, name)
    regions, delimited = residue(payload, parent, name)
    spans = find_spans(payload, masker, learn, regions, delimited)
    if learn:
        return payload
    return apply_spans(payload, spans, counts, masker)


def check_archive(before, after):
    fields = ("filename", "compress_type", "date_time", "external_attr", "internal_attr", "extra", "comment", "create_system", "create_version", "extract_version", "flag_bits")
    with zipfile.ZipFile(io.BytesIO(before)) as old, zipfile.ZipFile(io.BytesIO(after)) as new:
        if old.comment != new.comment:
            raise ValueError("archive comment changed")
        old_infos, new_infos = old.infolist(), new.infolist()
        if len(old_infos) != len(new_infos):
            raise ValueError("member count changed")
        for old_info, new_info in zip(old_infos, new_infos, strict=True):
            for field in fields:
                if getattr(old_info, field) != getattr(new_info, field):
                    raise ValueError(f"member {field} changed")
        if new.testzip() is not None:
            raise ValueError("rewritten archive fails its CRC check")


def digest(blob):
    return hashlib.sha256(blob).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("paths", nargs="+", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--ledger", type=Path, default=Path(__file__).resolve().with_name("ScrubLedger.json"))
    options = parser.parse_args()
    ledger = json.loads(options.ledger.read_text()) if options.ledger.exists() else {"reason": REASON, "files": []}
    listed = {value.encode("latin-1") for value in ledger.get("placeholders", [])}
    masker = Masker(secrets.token_bytes(32), listed)
    blobs = {}
    failed = 0
    for path in options.paths:
        blob = path.read_bytes()
        try:
            walk_archive(blob, masker, {rule: 0 for rule in RULES}, True, 0)
        except (ValueError, KeyError, struct.error, zipfile.BadZipFile, zlib.error, zstd.ZstdError) as error:
            print(f"{path} skipped: {error}")
            failed += 1
            continue
        blobs[path] = blob
    masker.seal()
    rows = []
    for path, blob in blobs.items():
        counts = {rule: 0 for rule in RULES}
        fresh = walk_archive(blob, masker, counts, False, 0)
        summary = " ".join(f"{rule}={counts[rule]}" for rule in RULES)
        print(f"{path} {digest(blob)} {digest(fresh)} {summary}")
        if fresh == blob:
            continue
        rows.append({"path": path.as_posix(), "fusionSavedSha256": digest(blob), "committedSha256": digest(fresh), "counts": counts})
        if not options.dry_run:
            path.write_bytes(fresh)
    if rows and not options.dry_run:
        known = {row["path"]: row for row in ledger["files"]}
        for row in rows:
            prior = known.get(row["path"])
            if prior and prior["committedSha256"] == row["fusionSavedSha256"]:
                row["fusionSavedSha256"] = prior["fusionSavedSha256"]
                row["counts"] = {rule: prior["counts"].get(rule, 0) + row["counts"][rule] for rule in RULES}
            known[row["path"]] = row
        ledger["reason"] = REASON
        ledger["files"] = [known[name] for name in sorted(known)]
        ledger["placeholders"] = sorted(value.decode("latin-1") for value in listed | masker.written)
        options.ledger.write_text(json.dumps(ledger, indent=2) + "\n")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
