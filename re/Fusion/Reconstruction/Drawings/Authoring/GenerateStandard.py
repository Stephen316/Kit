"""Generate the typed ISO drawing standard that Kit authors new Fusion drawings from.

The input is a Fusion-authored control drawing that Fusion has accepted after pruning.
Every object created before the sheet's paper-space block belongs to the drawing template:
tables, styles, dictionaries, the title block and the border blocks. Those objects become typed
rows with symbolic keys instead of handles. Lists in template objects that also point at sheet
objects become named slots, which the authoring code fills.

The sheet objects (layout, paper space, views, dimension, inserts) go to a separate research
file that only the fresh-handle experiment uses. Kit's semantic builders author them instead.
"""

import argparse
import collections
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE.parents[4] / 'src'))
sys.path.insert(0, str(HERE.parent / 'Dwg'))

from PruneDwg import Graph, field, owner_of, target  # noqa: E402

from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgHandleRef import DwgHandleRef  # noqa: E402
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgRecord import DwgRecord  # noqa: E402

TABLE_ENTRIES = {'LAYER', 'STYLE', 'LTYPE', 'APPID', 'DIMSTYLE', 'VPORT', 'BLOCK_HEADER', 'VIEW', 'UCS'}
DICTIONARIES = {'DICTIONARY', 'ACDBDICTIONARYWDFLT'}
SHARED_ENTRIES = {'APPID', 'LTYPE', 'LAYER', 'STYLE', 'DIMSTYLE'}
RELATIVE = {6, 8, 0xA, 0xC}
CONTAINERS = {
    'DICTIONARY': ('ItemCount', 1, ('Entries', 'Items')),
    'ACDBDICTIONARYWDFLT': ('ItemCount', 1, ('Entries', 'Items')),
    'BLOCK_HEADER': ('OwnedCount', 1, ('Owned',)),
    'LAYOUT': ('ViewportCount', 1, ('Viewports',)),
    'SORTENTSTABLE': ('EntryCount', 1, ('Entries',)),
}
INSERT_LISTS = ('InsertCounts', 2, ('Inserts',))
FRESH_HEADER = {
    'HandSeed': {'Code': 0, 'Handle': 0},
    'FingerprintGuid': '{00000000-0000-0000-0000-000000000000}',
    'VersionGuid': '{00000000-0000-0000-0000-000000000000}',
}
TIME_HEADER = tuple(f'{name}{part}' for name in ('TdCreate', 'TdUpdate', 'TdInDwg', 'TdUsrTimer') for part in ('Day', 'Msec')) + ('TimeZone',)


class Keys:
    """Symbolic keys that name each object by its place in the database rather than its handle."""

    def __init__(self, dwg, graph):
        self.dwg = dwg
        self.graph = graph
        self.keys = {}
        self.counts = collections.Counter()
        self.entry_of = {}
        self.xdic_of = {}
        self.block_of = {}
        header = {item.FieldName: item.FieldValue for item in dwg.HeaderVars.RecordFields}
        self.nod = header['NamedObjectsHandle'].RefValue
        self.model = header['ModelSpaceHandle'].RefValue
        self.paper = header['PaperSpaceHandle'].RefValue
        for handle, name in graph.names.items():
            obj = graph.objects[handle]
            if name in DICTIONARIES:
                for entry, ref in zip(field(obj.ClassData, 'Entries', ()), field(obj.ClassData, 'Items', ())):
                    self.entry_of.setdefault(target(handle, ref), (handle, field(entry, 'EntryName')))
            xdic = field(obj.CommonData, 'Xdic')
            if xdic is not None and xdic.RefValue:
                self.xdic_of[target(handle, xdic)] = handle
            if name == 'BLOCK_HEADER':
                for part in ('BlockEntity', 'EndBlock'):
                    ref = field(obj.ClassData, part)
                    if ref is not None and ref.RefValue:
                        self.block_of[target(handle, ref)] = (handle, 'BLOCK' if part == 'BlockEntity' else 'ENDBLK')
        for handle in sorted(graph.objects):
            self.key(handle)

    def unique(self, text):
        self.counts[text] += 1
        return text if self.counts[text] == 1 else f'{text}#{self.counts[text]}'

    def ordinal(self, prefix, name):
        self.counts[(prefix, name)] += 1
        return f'{prefix}/{name}#{self.counts[(prefix, name)]}'

    def key(self, handle):
        if handle in self.keys:
            return self.keys[handle]
        self.keys[handle] = None
        self.keys[handle] = self.make(handle)
        return self.keys[handle]

    def make(self, handle):
        name = self.graph.names[handle]
        obj = self.graph.objects[handle]
        if handle == self.nod:
            return 'NOD'
        if name.endswith('_CONTROL'):
            return 'Control:' + name[:-8]
        if name in TABLE_ENTRIES:
            return self.unique(f'{name}:{field(obj.ClassData, "EntryName")}')
        if handle in self.block_of:
            header, part = self.block_of[handle]
            return f'{self.key(header)}/{part}'
        if handle in self.entry_of:
            owner, entry = self.entry_of[handle]
            return self.unique(f'{self.key(owner)}/{entry}')
        if handle in self.xdic_of:
            return f'{self.key(self.xdic_of[handle])}/Xdic'
        owner = owner_of(obj)
        if owner is None:
            mode = field(obj.CommonData, 'EntityMode')
            owner = self.paper if mode == 1 else self.model
        if owner == 0 or owner not in self.graph.objects:
            return self.ordinal('Free', name)
        return self.ordinal(self.key(owner), name)


class Converter:
    def __init__(self, keys, sheet):
        self.keys = keys
        self.sheet = sheet
        self.dangling = collections.Counter()
        self.sheet_refs = collections.Counter()

    def ref(self, own, value, where):
        code = value.RefCode
        handle = target(own, value) if code in RELATIVE else value.RefValue
        if code in RELATIVE:
            code = 4
        if handle == 0:
            return {'Code': code, 'Handle': 0}
        key = self.keys.keys.get(handle)
        if key is None:
            self.dangling[where] += 1
            return {'Code': code, 'Handle': 0}
        if own not in self.sheet and handle in self.sheet:
            self.sheet_refs[(self.keys.keys.get(own, 'Header'), where, key)] += 1
        return {'Code': code, 'Key': key}

    def value(self, own, value, where):
        if isinstance(value, DwgHandleRef):
            return self.ref(own, value, where)
        if isinstance(value, DwgRecord):
            return {'Fields': [[item.FieldName, self.value(own, item.FieldValue, item.FieldName)] for item in value.RecordFields]}
        if isinstance(value, tuple):
            return [self.value(own, element, where) for element in value]
        if isinstance(value, bytes):
            return {'Hex': value.hex()}
        if isinstance(value, bool):
            return int(value)
        return value

    def record(self, own, record):
        return self.value(own, record, '')['Fields']


def slotted(converter, key, name, fields, sheet_keys, slots, appends):
    """Turn container lists that mix template and sheet items into slots that keep the template items."""
    rules = [CONTAINERS[name]] if name in CONTAINERS else []
    if name.endswith('_CONTROL'):
        rules = [('EntryCount', 1, ('Entries',))]
    if name == 'BLOCK_HEADER':
        rules.append(INSERT_LISTS)
    values = dict(fields)
    for count_name, form, lists in rules:
        if count_name not in values:
            continue
        driver = lists[-1]
        items = values[driver]
        mixed = [isinstance(item, dict) and item.get('Key') in sheet_keys for item in items]
        if not any(mixed):
            continue
        for list_name in lists:
            slot = f'{key}.{list_name}'
            series = values[list_name]
            slots[slot] = [item for item, is_sheet in zip(series, mixed) if not is_sheet]
            appends.extend([slot, item] for item, is_sheet in zip(series, mixed) if is_sheet)
            values[list_name] = {'Slot': slot, 'Form': 0}
        values[count_name] = {'Slot': f'{key}.{driver}', 'Form': form}
    return [[field_name, values[field_name]] for field_name, _ in fields]


def slotted_reactors(key, common, sheet_keys, slots, appends):
    values = dict(common)
    items = values.get('Reactors', [])
    mixed = [isinstance(item, dict) and item.get('Key') in sheet_keys for item in items]
    if not any(mixed):
        return common
    slot = f'{key}.Reactors'
    slots[slot] = [item for item, is_sheet in zip(items, mixed) if not is_sheet]
    appends.extend([slot, item] for item, is_sheet in zip(items, mixed) if is_sheet)
    values['Reactors'] = {'Slot': slot, 'Form': 0}
    values['ReactorCount'] = {'Slot': slot, 'Form': 1}
    return [[name, values[name]] for name, _ in common]


def strings_in(value, found):
    if isinstance(value, str):
        found.add(value)
    elif isinstance(value, dict):
        for item in value.values():
            strings_in(item, found)
    elif isinstance(value, list):
        for item in value:
            strings_in(item, found)


def zeroed(value):
    if isinstance(value, dict) and 'Fields' in value:
        return {'Fields': [[name, zeroed(item)] for name, item in value['Fields']]}
    if isinstance(value, list):
        return [zeroed(item) for item in value]
    return 0 if isinstance(value, int) else 0.0 if isinstance(value, float) else value


def header_draft(converter, dwg):
    rows = []
    for item in dwg.HeaderVars.RecordFields:
        value = converter.value(0, item.FieldValue, item.FieldName)
        if item.FieldName in FRESH_HEADER:
            value = FRESH_HEADER[item.FieldName]
        if item.FieldName in TIME_HEADER:
            value = zeroed(value)
        rows.append([item.FieldName, value])
    return rows


def class_rows(dwg):
    return [
        {
            'ClassNumber': row.ClassNumber, 'ProxyFlags': row.ProxyFlags, 'AppName': row.AppName,
            'CppName': row.CppName, 'DxfName': row.DxfName, 'WasZombie': row.WasZombie,
            'ItemClassId': row.ItemClassId, 'DwgVersion': row.DwgVersion, 'MaintVersion': row.MaintVersion,
        }
        for row in dwg.ClassTable.ClassRows
    ]


def generate(dwg, drop):
    graph = Graph(dwg)
    keys = Keys(dwg, graph)
    dropped = {handle for handle, name in graph.names.items() if name in drop}
    sheet = {handle for handle, name in graph.names.items() if handle >= keys.paper and name not in SHARED_ENTRIES}
    sheet_keys = {keys.keys[handle] for handle in sheet}
    converter = Converter(keys, sheet)
    fixed = [[keys.keys[handle], handle] for handle in sorted(graph.objects) if handle < 0x10]
    standard_rows, sheet_rows, raw_rows, slots, appends = [], [], [], {}, []
    untyped = collections.Counter()
    for obj in dwg.DwgObjects:
        handle = obj.ObjectHandle
        if handle in dropped:
            continue
        name = graph.names[handle]
        key = keys.keys[handle]
        if not obj.ClassKind or obj.TailWidth or obj.HandleRefs:
            untyped[name] += 1
            if handle in sheet:
                raw_rows.append([
                    key, obj.TypeNumber, converter.record(handle, obj.CommonData),
                    [[converter.ref(handle, block.AppRef, 'Eed'), converter.record(handle, block.EedItems)] for block in obj.EedBlocks],
                    obj.TailWidth, obj.TailValue, [converter.value(handle, ref, 'Tail') for ref in obj.HandleRefs],
                    list(obj.TextItems), obj.HasTexts,
                ])
            continue
        eed = [[converter.ref(handle, block.AppRef, 'Eed'), converter.record(handle, block.EedItems)] for block in obj.EedBlocks]
        if any(block.RawData for block in obj.EedBlocks):
            raise ValueError(f'{key} has undecoded extended data')
        common = converter.record(handle, obj.CommonData)
        data = converter.record(handle, obj.ClassData)
        if handle not in sheet:
            common = slotted_reactors(key, common, sheet_keys, slots, appends)
        if handle in sheet:
            sheet_rows.append([key, obj.ClassKind, common, data, eed])
        else:
            data = slotted(converter, key, name, data, sheet_keys, slots, appends)
            standard_rows.append([key, obj.ClassKind, common, data, eed])
    standard = {
        'Classes': class_rows(dwg),
        'HeaderVars': header_draft(converter, dwg),
        'Fixed': fixed,
        'Slots': [[name, items] for name, items in slots.items()],
        'Rows': standard_rows,
    }
    sheet_part = {'Rows': sheet_rows, 'Raw': raw_rows, 'Appends': appends}
    report = {
        'objects': len(dwg.DwgObjects),
        'dropped': len(dropped),
        'standard_rows': len(standard_rows),
        'sheet_rows': len(sheet_rows),
        'untyped': dict(untyped),
        'dangling': dict(converter.dangling),
        'slots': {name: len(items) for name, items in slots.items()},
        'template_refs_to_sheet': sorted({f'{own} {where} -> {key}' for own, where, key in converter.sheet_refs}),
    }
    return standard, sheet_part, report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--variant', required=True, help='variant label under the research variants folder')
    parser.add_argument('--drop', nargs='*', default=[], help='object classes to leave out')
    parser.add_argument('--standard-out', required=True)
    parser.add_argument('--sheet-out', required=True)
    parser.add_argument('--strings', action='store_true', help='print every string in the template rows for review')
    args = parser.parse_args()
    sys.path.insert(0, str(HERE))
    from LoadVariant import load_variant
    dwg = load_variant(args.variant)
    standard, sheet_part, report = generate(dwg, set(args.drop))
    Path(args.standard_out).write_text(json.dumps(standard, separators=(',', ':')) + '\n')
    Path(args.sheet_out).write_text(json.dumps(sheet_part, separators=(',', ':')) + '\n')
    print(json.dumps(report, indent=1))
    if args.strings:
        found = set()
        strings_in(standard, found)
        for text in sorted(found):
            print(repr(text))


if __name__ == '__main__':
    main()
