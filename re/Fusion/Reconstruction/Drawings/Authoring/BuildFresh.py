"""Re-author a pruned control drawing through Kit's draft pipeline with fresh handles.

G1FreshHandles places every template row from the generated standard and every sheet row from the
same control through DraftBook, FinishBook and AuthorShell. Handles are reassigned from 0x10, the
header gets fresh GUIDs and times, and the file shell is Kit's: Kit product information, an empty
summary, and a header section without trailing bits. The only fixed handles are the control objects,
the named object dictionary and the sheet layout, because the drawing segment names the layout by
handle. Untyped sheet objects keep their undecoded bits and get remapped handle references.

G2FreshClean also drops block preview images and the material asset records, which are byte payloads
that a typed standard should not carry.
"""

import argparse
import datetime
import hashlib
import json
import sys
import uuid
from dataclasses import replace
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE.parents[4] / 'src'))
sys.path.insert(0, str(HERE))

import BuildVariants  # noqa: E402
from LoadVariant import VARIANTS, variant_drawing  # noqa: E402

from convert.formats.Fusion.DrawingCodec.Dwg.Author.AuthorShell import AuthorShell, ReplaceVars  # noqa: E402
from convert.formats.Fusion.DrawingCodec.Dwg.Author.DraftBook import DraftBook  # noqa: E402
from convert.formats.Fusion.DrawingCodec.Dwg.Author.DraftRow import DraftRow  # noqa: E402
from convert.formats.Fusion.DrawingCodec.Dwg.Author.DraftValue import DraftRecord  # noqa: E402
from convert.formats.Fusion.DrawingCodec.Dwg.Author.FinishBook import AssignHandles, FinishEed, FinishRow  # noqa: E402
from convert.formats.Fusion.DrawingCodec.Dwg.Author.ResolveDraft import ResolveDraft, ResolveRecord  # noqa: E402
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Standard.ReadDraftJson import ReadDraftJson, ReadDraftRecord  # noqa: E402
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Standard.ReadStandard import ReadDraftRow, ReadEedBlock, ReadStandard  # noqa: E402
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgClassTable import DwgClassTable  # noqa: E402
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgDayTime import DwgDayTime  # noqa: E402
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgObject import DwgObject  # noqa: E402
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgRecord import DwgRecord  # noqa: E402
from convert.formats.Fusion.DrawingCodec.Dwg.ReadDwgFile import ReadDwgFile  # noqa: E402
from convert.formats.Fusion.DrawingCodec.Dwg.EmitDwgFile import EmitDwgFile  # noqa: E402

MATERIAL_ASSETS = 'FBXASSET'


def julian(moment):
    day = moment.toordinal() + 1721425
    msec = ((moment.hour * 60 + moment.minute) * 60 + moment.second) * 1000
    return DwgDayTime(day, msec)


def clean_row(row):
    """Drop block previews and the material asset entries from template rows."""
    fields = dict(row.ClassData.DraftFields)
    if row.ClassName == 'BLOCK_HEADER' and fields.get('PreviewSize'):
        fields['PreviewSize'] = 0
        fields['Preview'] = b''
    if row.ClassName == 'DICTIONARY' and isinstance(fields['Entries'], tuple) and any(dict(entry.DraftFields).get('EntryName') == MATERIAL_ASSETS for entry in fields['Entries']):
        keep = [index for index, entry in enumerate(fields['Entries']) if dict(entry.DraftFields).get('EntryName') != MATERIAL_ASSETS]
        fields['Entries'] = tuple(fields['Entries'][index] for index in keep)
        fields['Items'] = tuple(fields['Items'][index] for index in keep)
        fields['ItemCount'] = len(keep)
    return replace(row, ClassData=DraftRecord(tuple((name, fields[name]) for name, _ in row.ClassData.DraftFields)))


def raw_object(entry, handles, slots, type_number):
    key, _type, common, eed, width, value, refs, texts, has_texts = entry
    common_data = ResolveRecord(ReadDraftRecord(common), handles, slots)
    kind = 'Entity' if common_data.RecordFields[0].FieldName == 'HasGraphics' else 'Object'
    return DwgObject(
        type_number, handles[key], tuple(FinishEed(ReadEedBlock(block), handles, slots) for block in eed),
        kind, common_data, '', DwgRecord(()),
        width, value, tuple(texts), has_texts, tuple(ResolveDraft(ReadDraftJson(ref), handles, slots) for ref in refs),
    )


def build(standard_path, sheet_path, layout_handle, clean):
    standard = ReadStandard(Path(standard_path))
    sheet = json.loads(Path(sheet_path).read_text())
    rows = list(standard.DraftRows)
    if clean:
        rows = [clean_row(row) for row in rows if not row.KeyText.endswith('/' + MATERIAL_ASSETS)]
    sheet_rows = [ReadDraftRow(entry) for entry in sheet['Rows']]
    layout_key = next(row.KeyText for row in sheet_rows if row.ClassName == 'LAYOUT')
    fixed = dict(standard.FixedHandles)
    fixed[layout_key] = layout_handle
    book = DraftBook(fixed, rows + sheet_rows, {name: list(items) for name, items in standard.SlotItems})
    for slot, item in sheet['Appends']:
        book.SlotItems[slot].append(ReadDraftJson(item))
    placeholders = [DraftRow(entry[0], 'RAW', DraftRecord(()), DraftRecord(()), ()) for entry in sheet['Raw']]
    handles = AssignHandles(DraftBook(fixed, book.DraftRows + placeholders, book.SlotItems))
    table = DwgClassTable(0, (0, 0, 1), standard.ClassRows, 0)
    objects = [FinishRow(row, handles, book.SlotItems, table, 'AC1032') for row in book.DraftRows]
    objects += [raw_object(entry, handles, book.SlotItems, entry[1]) for entry in sheet['Raw']]
    objects.sort(key=lambda item: item.ObjectHandle)
    moment = julian(datetime.datetime(2026, 11, 12, 12, 0, 0))
    header = ResolveRecord(standard.HeaderVars, handles, book.SlotItems)
    header = ReplaceVars(header, {
        'FingerprintGuid': '{' + str(uuid.uuid4()).upper() + '}',
        'VersionGuid': '{' + str(uuid.uuid4()).upper() + '}',
        'TdCreateDay': moment.DayNumber, 'TdCreateMsec': moment.MilliSeconds,
        'TdUpdateDay': moment.DayNumber, 'TdUpdateMsec': moment.MilliSeconds,
    })
    data = AuthorShell(tuple(objects), header, standard.ClassRows, moment)
    again = ReadDwgFile(data)
    if EmitDwgFile(again) != data or len(again.DwgObjects) != len(objects):
        raise ValueError('authored drawing does not read back')
    return data, handles, len(objects)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--control', required=True, help='variant label whose drawing members and design are reused')
    parser.add_argument('--standard', required=True)
    parser.add_argument('--sheet', required=True)
    parser.add_argument('--source', required=True, help='design f3d bytes of the referenced design')
    args = parser.parse_args()
    drawing = variant_drawing(args.control)
    control = ReadDwgFile(BuildVariants.database(drawing))
    layout = next(obj.ObjectHandle for obj in control.DwgObjects if obj.ClassKind == 'LAYOUT' and obj.ObjectHandle > 0x100)
    source = Path(args.source).read_bytes()
    plan = []
    for label, clean in (('G1FreshHandles', False), ('G2FreshClean', True)):
        data, handles, count = build(args.standard, args.sheet, layout, clean)
        bundle = BuildVariants.opaque_bundle(BuildVariants.without_database(drawing, data), source, label)
        path = VARIANTS / f'{label}.f3z'
        path.write_bytes(bundle)
        plan.append({'label': label, 'file': path.name, 'bytes': len(bundle), 'sha256': hashlib.sha256(bundle).hexdigest(),
                     'dwg_bytes': len(data), 'dwg_sha256': hashlib.sha256(data).hexdigest(), 'objects': count, 'max_handle': max(handles.values())})
    (VARIANTS / 'PlanFresh.json').write_text(json.dumps({'variants': plan}, indent=1) + '\n')
    print(json.dumps(plan, indent=1))


if __name__ == '__main__':
    main()
