"""Turn a generated drawing standard into the typed ISO standard that Kit's DWG author reads.

The generated standard is the template part of a pruned Fusion control. This step removes what a
source-free author must not carry or must build itself:

* block preview images, which are byte payloads Fusion does not need (G2FreshClean);
* the FBXASSET material asset records, which are zipped byte payloads (G2FreshClean);
* the annotation scale list entries, because the author adds one scale per used view scale;
* the AcFusionPimIds records, which name the source design's cloud lineage and cache file;
* the HasDsData flags of the two layouts, because the author writes no AcDsPrototype_1b section.
  A layout that claims data-store data in a file without that section makes Fusion report
  "Drawing file is not valid." (D6Minimal and the M-series authored drawings).

Absolute paths are cut to their file name. Fusion writes the absolute path of the drawing template
into the NOD save history and into the CMODELDOCTEMPLATE variable, and those paths name accounts.

It then checks that every symbolic link names a template object or one of the sheet objects that the
sheet builders always place, and that no private string from the controls survived. The sheet
defaults JSON gets the same flag change, is checked for the same private strings and is written next to the standard.
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[5] / 'src'))

from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgRecord import DwgField, DwgRecord  # noqa: E402
from convert.formats.Fusion.DrawingCodec.Dwg.Records.GroupItems import EncodeGroups  # noqa: E402

MATERIAL_ASSETS = 'FBXASSET'
SCALE_LIST = 'NOD/ACAD_SCALELIST'
PIM_IDS = 'NOD/AcFusionPimIds/'
SHEET_KEYS = {'BLOCK_HEADER:*Paper_Space'}
LOCAL_TOKENS = tuple(token for token in os.environ.get('KIT_PRIVATE_TOKENS', '').split(',') if token)
PRIVATE = re.compile('|'.join([r'KitDrw', r'urn:adsk', r'[/\\]Users[/\\]', r'webdeploy', r'[\w.+-]+@[\w-]+\.[\w.]+'] + [re.escape(token) for token in LOCAL_TOKENS]), re.IGNORECASE)
TEMPLATE_PATH = re.compile(r'^(?:[A-Za-z]:\\|/).*[\\/]([^\\/]+)$')


def redacted(value):
    if isinstance(value, str):
        return TEMPLATE_PATH.sub(r'\1', value)
    if isinstance(value, list):
        return [redacted(item) for item in value]
    if isinstance(value, dict):
        return {name: redacted(item) for name, item in value.items()}
    return value


def group_size(code, text):
    return len(EncodeGroups(DwgRecord((DwgField(code, text),))))


def resized(data, before):
    """Correct an xrecord's DataSize after its template paths were shortened."""
    values = fields(data)
    old_items = fields(before)['Items']['Fields']
    new_items = values['Items']['Fields']
    delta = sum(group_size(code, new) - group_size(code, old) for (code, old), (_, new) in zip(old_items, new_items) if old != new)
    if not delta:
        return data
    return [[name, value + delta if name == 'DataSize' else value] for name, value in data]


def is_dropped(key):
    return key.endswith('/' + MATERIAL_ASSETS) or key.startswith(SCALE_LIST + '/') or key.startswith(PIM_IDS)


def without_entries(data, values):
    keys = [item.get('Key') if isinstance(item, dict) else None for item in values['Items']]
    keep = [index for index, key in enumerate(keys) if not (key and is_dropped(key))]
    if len(keep) == len(keys):
        return data
    return [[name, len(keep) if name == 'ItemCount' else [value[index] for index in keep] if name in ('Entries', 'Items') else value] for name, value in data]


def fields(entries):
    return {name: value for name, value in entries}


def without_data_store(common):
    return [[name, 0 if name == 'HasDsData' else value] for name, value in common]


def strip_rows(rows):
    kept = []
    for key, cls, common, data, eed in rows:
        if is_dropped(key):
            continue
        common = without_data_store(common)
        before, data = data, redacted(data)
        if cls == 'XRECORD' and data != before:
            data = resized(data, before)
        values = fields(data)
        if cls == 'BLOCK_HEADER' and values.get('PreviewSize'):
            data = [[name, 0 if name == 'PreviewSize' else {'Hex': ''} if name == 'Preview' else value] for name, value in data]
        if cls == 'DICTIONARY' and isinstance(values.get('Items'), list) and key != SCALE_LIST:
            data = without_entries(data, values)
        if key == SCALE_LIST:
            data = [[name, {'Slot': SCALE_LIST + '.Items', 'Form': 1} if name == 'ItemCount' else {'Slot': SCALE_LIST + '.' + name, 'Form': 0} if name in ('Entries', 'Items') else value] for name, value in data]
        kept.append([key, cls, common, data, eed])
    return kept


def links(value):
    if isinstance(value, dict):
        if 'Key' in value:
            yield value['Key']
        for item in value.values():
            yield from links(item)
    elif isinstance(value, list):
        for item in value:
            yield from links(item)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--standard', required=True)
    parser.add_argument('--defaults', required=True)
    parser.add_argument('--out-dir', required=True)
    args = parser.parse_args()
    standard = json.loads(Path(args.standard).read_text())
    standard['Rows'] = strip_rows(standard['Rows'])
    standard['Slots'] = [slot for slot in standard['Slots'] if not slot[0].startswith(SCALE_LIST + '.')]
    standard['Slots'] += [[SCALE_LIST + '.Entries', []], [SCALE_LIST + '.Items', []]]
    keys = {row[0] for row in standard['Rows']} | SHEET_KEYS
    dangling = sorted({key for key in links(standard) if key not in keys})
    if dangling:
        raise SystemExit(f'standard links to unplaced objects: {dangling}')
    text = json.dumps(standard, separators=(',', ':'), ensure_ascii=False) + '\n'
    shapes = json.loads(Path(args.defaults).read_text())
    for shape in shapes.values():
        shape['Common'] = without_data_store(shape['Common'])
    defaults = json.dumps(shapes, separators=(',', ':'), ensure_ascii=False) + '\n'
    for name, body in (('standard', text), ('defaults', defaults)):
        found = PRIVATE.findall(body)
        if found:
            raise SystemExit(f'{name} still holds private strings: {sorted(set(found))}')
    out = Path(args.out_dir)
    (out / 'IsoStandard.json').write_text(text, encoding='utf-8')
    (out / 'SheetDefaults.json').write_text(defaults, encoding='utf-8')
    print(json.dumps({'rows': len(standard['Rows']), 'slots': len(standard['Slots']), 'bytes': len(text.encode())}))


if __name__ == '__main__':
    main()
