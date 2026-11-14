# Research harness for the production DWG inventory reader.
#
# Usage (from anywhere):
#   /opt/homebrew/bin/python3.14 -I re/Fusion/Reconstruction/Drawings/Dwg/InspectDwg.py <directory-with-dwg-files>
#
# Runs convert.formats.Fusion.DrawingCodec.Dwg.ReadDwgInventory on every *.dwg in the
# given directory and writes DwgInventory.json next to this script. Only file names,
# hashes and decoded structure are recorded; the input directory path is not.
# User names (SummaryInfo Author / LastSavedBy) and any absolute filesystem paths are
# replaced by "<redacted>" with booleans recording that they were present. Every
# decompressed section is additionally scanned (at all 8 bit alignments, as Latin-1 and
# UTF-16LE) for absolute-path shapes, user-profile directory names and the current login
# name; only counts are written, never the matched text.

import datetime
import getpass
import hashlib
import json
import re
import sys
import uuid
from pathlib import Path

WORKTREE = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(WORKTREE / 'src'))

from convert.formats.Fusion.DrawingCodec.Dwg.ReadDwgInventory import ReadDwgInventory  # noqa: E402

OUTPUT = Path(__file__).resolve().parent / 'DwgInventory.json'
REDACTED = '<redacted>'
JULIAN_UNIX_EPOCH = 2440588

PATH_PATTERNS = {
    'WindowsDrivePath': re.compile(r'[A-Za-z]:[\\/][\w .()$~-]{2,}[\\/]'),
    'UncPath': re.compile(r'\\\\[\w.$-]{2,}\\[\w .$-]{2,}'),
    'PosixHomePath': re.compile(r'/(?:Users|home|private|var|tmp|Volumes|mnt|opt|Library|Applications)/[\w .-]{2,}'),
    'FileUri': re.compile(r'file:/{1,3}[\w.%-]'),
}
PROFILE_PATTERN = re.compile(r'(?:[A-Za-z]:\\(?:Users|Documents and Settings)\\|/Users/|/home/)([^\\/\x00-\x1f]{1,64})[\\/]')
MODEL_DOC_PATTERN =re.compile(r'ViewRep|Assoc|Acm|Amdt|Amg|AcMe|AcIm|ViewBorder|ViewSymbol|ViewStyle|Synergy|Fusion|Idw|Gref|AmiMaster|DRAWINGVIEW|ReferenceData|PersSubent|CenterMark', re.I)


def login_pattern():
    name = getpass.getuser()
    if len(name) < 3:
        return None
    return re.compile(r'(?<![A-Za-z])' + re.escape(name) + r'(?![A-Za-z])', re.I)


LOGIN = login_pattern()


def path_kinds(text):
    return sorted(kind for kind, pattern in PATH_PATTERNS.items() if pattern.search(text))


def has_login(text):
    return bool(LOGIN and LOGIN.search(text))


def day_time(value, is_duration=False):
    row = {'DayNumber': value.DayNumber, 'MilliSeconds': value.MilliSeconds}
    if is_duration:
        row['Seconds'] = value.DayNumber * 86400 + value.MilliSeconds / 1000
    elif value.DayNumber:
        stamp = datetime.datetime(1970, 1, 1) + datetime.timedelta(days=value.DayNumber - JULIAN_UNIX_EPOCH, milliseconds=value.MilliSeconds)
        row['Iso'] = stamp.isoformat(timespec='milliseconds') + ' (zone unspecified)'
    return row


def guid_text(raw):
    return str(uuid.UUID(bytes_le=raw))


def redact_text(text, is_user_name):
    kinds = path_kinds(text)
    login = has_login(text)
    present = bool(text) and is_user_name
    if text and (present or kinds or login):
        return REDACTED, present, kinds, login
    return text, False, kinds, login


def summary_json(summary):
    if summary is None:
        return None
    fields = {}
    user_present = False
    path_kinds_found = set()
    login_found = False
    for name in ('Title', 'Subject', 'Author', 'Keywords', 'Comments', 'LastSavedBy', 'RevisionNumber', 'HyperlinkBase'):
        text, present, kinds, login = redact_text(getattr(summary, name), name in ('Author', 'LastSavedBy'))
        fields[name] = text
        user_present |= present
        path_kinds_found.update(kinds)
        login_found |= login
    props = []
    for prop in summary.CustomProps:
        key, _, key_kinds, key_login = redact_text(prop.PropName, False)
        value, _, value_kinds, value_login = redact_text(prop.PropValue, False)
        props.append({'Name': key, 'Value': value})
        path_kinds_found.update(key_kinds + value_kinds)
        login_found |= key_login or value_login
    fields.update({
        'EditingTime': day_time(summary.EditingTime, True),
        'CreatedTime': day_time(summary.CreatedTime),
        'ModifiedTime': day_time(summary.ModifiedTime),
        'CustomProps': props,
        'ReservedWords': list(summary.ReservedWords),
        'UserNamePresent': user_present,
        'AbsolutePathPresent': bool(path_kinds_found),
        'AbsolutePathKinds': sorted(path_kinds_found),
        'LoginNamePresent': login_found,
    })
    return fields


def product_attributes(text):
    return dict(re.findall(r'(\w+)\s*=\s*\\?"([^"\\]*)\\?"', text))


def appinfo_json(info):
    if info is None:
        return None
    entries = []
    any_path = False
    any_login = False
    for entry in info.AppEntries:
        text, _, kinds, login = redact_text(entry.TextValue, False)
        any_path |= bool(kinds)
        any_login |= login
        row = {'KeyHex': entry.KeyBytes.hex(), 'KeyGuid': guid_text(entry.KeyBytes), 'Text': text}
        if text.lstrip('"').startswith('<ProductInformation'):
            row['ProductAttributes'] = product_attributes(text)
        entries.append(row)
    return {'LeadWord': info.LeadWord, 'InfoName': info.InfoName, 'Entries': entries,
            'AbsolutePathPresent': any_path, 'LoginNamePresent': any_login}


def bit_shifted_views(data):
    if not data:
        return []
    number = int.from_bytes(data, 'big')
    views = []
    for shift in range(8):
        shifted = (number << shift).to_bytes(len(data) + 1, 'big')[1:] if shift else data
        views.append(shifted)
    return views


def privacy_scan(data):
    counts = {kind: 0 for kind in PATH_PATTERNS}
    counts['LoginName'] = 0
    profiles = set()
    for view in bit_shifted_views(data):
        texts = [view.decode('latin-1'), view.decode('utf-16-le', 'replace'), view[1:].decode('utf-16-le', 'replace')]
        for text in texts:
            for kind, pattern in PATH_PATTERNS.items():
                counts[kind] += len(pattern.findall(text))
            if LOGIN:
                counts['LoginName'] += len(LOGIN.findall(text))
            profiles.update(name.casefold() for name in PROFILE_PATTERN.findall(text))
    counts['DistinctUserProfiles'] = len(profiles)
    return counts


def file_dep_list(data):
    pos = 0

    def u32():
        nonlocal pos
        value = int.from_bytes(data[pos:pos + 4], 'little')
        pos += 4
        return value

    def text32():
        nonlocal pos
        size = u32()
        raw = data[pos:pos + size]
        pos += size
        return raw.decode('utf-16-le', 'replace')

    features = [text32() for _ in range(u32())]
    file_count = u32()
    return {'Features': features, 'FileCount': file_count, 'FileRowsDecoded': False,
            'ConsumedBytes': pos, 'SectionBytes': len(data)}


def section_json(section):
    info = section.SectionInfo
    return {
        'Name': info.SectionName, 'SectionId': info.SectionId, 'DataSize': info.DataSize,
        'PageCount': info.PageCount, 'MaxPageSize': info.MaxPageSize, 'ReservedWord': info.ReservedWord,
        'CompressFlag': info.CompressFlag, 'EncryptFlag': info.EncryptFlag,
        'DataSha256': hashlib.sha256(section.DataValue).hexdigest(),
        'Pages': [{'PageNumber': page.PageNumber, 'FileOffset': page.FileOffset, 'SectionNumber': page.SectionNumber,
                   'DataSize': page.DataSize, 'PageSize': page.PageSize, 'StartOffset': page.StartOffset,
                   'HeadChecksum': f'{page.HeadChecksum:#010x}', 'DataChecksum': f'{page.DataChecksum:#010x}'}
                  for page in section.DataPages],
    }


def class_json(row):
    return {
        'ClassNumber': row.ClassNumber, 'ProxyFlags': f'{row.ProxyFlags:#x}', 'AppName': row.AppName,
        'CppName': row.CppName, 'DxfName': row.DxfName, 'WasZombie': row.WasZombie,
        'ItemClassId': f'{row.ItemClassId:#x}', 'IsEntity': row.ItemClassId == 0x1F2,
        'InstanceCount': row.InstanceCount, 'DwgVersion': row.DwgVersion, 'MaintVersion': row.MaintVersion,
        'ReservedFirst': row.ReservedFirst, 'ReservedSecond': row.ReservedSecond,
        'ModelDocumentationFamily': bool(MODEL_DOC_PATTERN.search(row.CppName + ' ' + row.DxfName)),
    }


def header_json(header):
    return {
        'VersionText': header.VersionText, 'PaddingBytes': header.PaddingBytes.hex(),
        'MaintenanceVersion': header.MaintenanceVersion, 'HeaderMarker': header.HeaderMarker,
        'PreviewAddress': header.PreviewAddress, 'AppVersion': header.AppVersion,
        'AppMaintenance': header.AppMaintenance, 'CodePage': header.CodePage,
        'ReservedTriple': header.ReservedTriple.hex(), 'SecurityFlags': header.SecurityFlags,
        'ReservedAddress': header.ReservedAddress, 'SummaryAddress': header.SummaryAddress,
        'VbaAddress': header.VbaAddress, 'CryptAddress': header.CryptAddress,
        'AppInfoAddress': header.AppInfoAddress, 'AppHistoryAddress': header.AppHistoryAddress,
        'TrailingWords': list(header.TrailingWords),
    }


def crypt_json(crypt):
    row = {name: getattr(crypt, name) for name in crypt.__slots__}
    row['FixedWords'] = list(crypt.FixedWords)
    row['LayoutWords'] = list(crypt.LayoutWords)
    row['CrcValue'] = f'{crypt.CrcValue:#010x}'
    return row


def address_checks(inventory):
    first = {s.SectionInfo.SectionName: s.DataPages[0].FileOffset + 0x20 for s in inventory.Sections if s.DataPages}
    header = inventory.FileHeader
    pairs = {
        'PreviewAddress': ('AcDb:Preview', header.PreviewAddress),
        'SummaryAddress': ('AcDb:SummaryInfo', header.SummaryAddress),
        'AppInfoAddress': ('AcDb:AppInfo', header.AppInfoAddress),
        'AppHistoryAddress': ('AcDb:AppInfoHistory', header.AppHistoryAddress),
    }
    return {field: {'Section': name, 'Value': value, 'FirstPageDataOffset': first.get(name),
                    'Matches': first.get(name) == value} for field, (name, value) in pairs.items()}


def inspect(path):
    data = path.read_bytes()
    inventory = ReadDwgInventory(data)
    named = {s.SectionInfo.SectionName: s.DataValue for s in inventory.Sections}
    rows = [class_json(row) for row in inventory.ClassTable.ClassRows]
    class_text = ' '.join(r['AppName'] + ' ' + r['CppName'] + ' ' + r['DxfName'] for r in rows)
    scan = {name or '<unnamed>': privacy_scan(value) for name, value in named.items()}
    return {
        'Source': path.name,
        'Sha256': hashlib.sha256(data).hexdigest(),
        'Size': len(data),
        'FileHeader': header_json(inventory.FileHeader),
        'CryptHeader': crypt_json(inventory.CryptHeader),
        'PageMap': {'EntryCount': len(inventory.MapPages),
                    'GapCount': sum(1 for page in inventory.MapPages if page.PageNumber < 0),
                    'Entries': [{'PageNumber': page.PageNumber, 'PageSize': page.PageSize, 'FileOffset': page.FileOffset,
                                 'GapLinks': list(page.GapLinks)} for page in inventory.MapPages]},
        'SectionMapWords': list(inventory.MapWords),
        'Sections': [section_json(section) for section in inventory.Sections],
        'HeaderAddressChecks': address_checks(inventory),
        'ClassTable': {'MaxClassNumber': inventory.ClassTable.MaxClassNumber, 'LeadCodes': list(inventory.ClassTable.LeadCodes),
                       'CrcValue': f'{inventory.ClassTable.CrcValue:#06x}', 'Count': len(rows),
                       'ModelDocumentationCount': sum(1 for r in rows if r['ModelDocumentationFamily']),
                       'AbsolutePathPresent': bool(path_kinds(class_text)), 'LoginNamePresent': has_login(class_text),
                       'Rows': rows},
        'SummaryInfo': summary_json(inventory.Summary),
        'AppInfo': appinfo_json(inventory.AppInfo),
        'FileDepList': file_dep_list(named['AcDb:FileDepList']) if 'AcDb:FileDepList' in named else None,
        'HandleMap': {'HandleCount': inventory.HandleMap.HandleCount, 'LastHandle': inventory.HandleMap.LastHandle,
                      'LastHandleHex': f'{inventory.HandleMap.LastHandle:#x}', 'BlockCount': inventory.HandleMap.BlockCount},
        'SectionPrivacyScan': scan,
        'PrivacySummary': {
            'SectionsWithAbsolutePaths': sorted(name for name, counts in scan.items() if any(counts[kind] for kind in PATH_PATTERNS)),
            'SectionsWithLoginName': sorted(name for name, counts in scan.items() if counts['LoginName']),
            'MaxDistinctUserProfiles': max((counts['DistinctUserProfiles'] for counts in scan.values()), default=0),
            'Note': 'counts only; matched text deliberately not recorded',
        },
    }


def main(directory):
    samples = sorted(Path(directory).glob('*.dwg'))
    report = {
        'Reader': 'convert.formats.Fusion.DrawingCodec.Dwg.ReadDwgInventory.ReadDwgInventory',
        'Python': sys.version.split()[0],
        'Redaction': 'SummaryInfo Author/LastSavedBy and any text containing an absolute path or the local login name are replaced by <redacted>',
        'Samples': [],
        'Failures': [],
    }
    for path in samples:
        try:
            report['Samples'].append(inspect(path))
        except ValueError as error:
            report['Failures'].append({'Source': path.name, 'Sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'Error': str(error)})
    OUTPUT.write_text(json.dumps(report, indent=1, ensure_ascii=False) + '\n')
    for sample in report['Samples']:
        summary = sample['SummaryInfo'] or {}
        print(sample['Source'], sample['FileHeader']['VersionText'], 'sections', len(sample['Sections']),
              'classes', sample['ClassTable']['Count'], 'handles', sample['HandleMap']['HandleCount'],
              'summary-user', summary.get('UserNamePresent'), 'summary-paths', summary.get('AbsolutePathPresent'),
              'section-paths', sample['PrivacySummary']['SectionsWithAbsolutePaths'],
              'section-login', sample['PrivacySummary']['SectionsWithLoginName'],
              'profiles', sample['PrivacySummary']['MaxDistinctUserProfiles'])
    for failure in report['Failures']:
        print('FAILED', failure['Source'], failure['Error'])
    return 1 if report['Failures'] else 0


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit('usage: InspectDwg.py <directory-with-dwg-files>')
    raise SystemExit(main(sys.argv[1]))
