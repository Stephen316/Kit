"""Generate per-class field defaults for sheet objects from several Fusion controls.

A field becomes a class default only when every instance of the class in every control holds the
same value. References become symbolic keys when they point at a template object; a reference to
another sheet object is never a default, so Kit's builders always supply those. The output lists,
for each class, the defaults and the fields that the builders must supply.
"""

import argparse
import collections
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE.parents[4] / 'src'))

import BuildVariants  # noqa: E402
from GenerateStandard import SHARED_ENTRIES, Converter, Keys  # noqa: E402
from LoadVariant import load_variant  # noqa: E402
from PruneDwg import Graph  # noqa: E402

from convert.formats.Fusion.DrawingCodec.Dwg.ReadDwgFile import ReadDwgFile  # noqa: E402

# Fields that only look constant because every control shares one design, one sheet name, one
# scale and one title block. Kit's builders must always supply them, so they never become defaults.
ALWAYS_SUPPLIED = {
    ('LAYOUT', 'Data', 'LayoutName'),
    ('LAYOUT', 'Data', 'ViewportCount'),
    ('DRAWINGVIEW', 'Data', 'ViewScale'),
    ('DRAWINGVIEW', 'Data', 'ScaleObject'),
    ('ACDBVIEWREPORIENTATION', 'Data', 'TargetPoint'),
    ('ACDBREFERENCEDATA', 'Data', 'TextTwo'),
    ('ACDBREFERENCEDATA', 'Data', 'TextThree'),
    ('ACDBREFERENCEDATA', 'Data', 'TextFour'),
    ('CIRCLE', 'Data', 'Center'),
    ('CIRCLE', 'Data', 'Radius'),
    ('CIRCLE', 'Data', 'Extrusion'),
    ('INSERT', 'Data', 'OwnedCount'),
}


def load(spec):
    if spec.endswith('.f2d'):
        return ReadDwgFile(BuildVariants.database(Path(spec).read_bytes()))
    return load_variant(spec)


def sheet_rows(dwg):
    graph = Graph(dwg)
    keys = Keys(dwg, graph)
    sheet = {handle for handle, name in graph.names.items() if handle >= keys.paper and name not in SHARED_ENTRIES}
    converter = Converter(keys, sheet)
    sheet_keys = {keys.keys[handle] for handle in sheet}
    for obj in dwg.DwgObjects:
        if obj.ObjectHandle in sheet and obj.ClassKind and not obj.TailWidth:
            yield obj.ClassKind, converter.record(obj.ObjectHandle, obj.CommonData), converter.record(obj.ObjectHandle, obj.ClassData), sheet_keys


def mentions_sheet(value, sheet_keys):
    if isinstance(value, dict):
        if value.get('Key') in sheet_keys:
            return True
        return any(mentions_sheet(item, sheet_keys) for item in value.values())
    if isinstance(value, list):
        return any(mentions_sheet(item, sheet_keys) for item in value)
    return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--controls', nargs='+', required=True, help='variant labels or f2d paths')
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    seen = collections.defaultdict(lambda: collections.defaultdict(list))
    order = collections.defaultdict(dict)
    for spec in args.controls:
        for class_name, common, data, sheet_keys in sheet_rows(load(spec)):
            for part, record in (('Common', common), ('Data', data)):
                for name, value in record:
                    order[class_name].setdefault((part, name), len(order[class_name]))
                    text = json.dumps(value, sort_keys=True)
                    seen[class_name][(part, name)].append(None if mentions_sheet(value, sheet_keys) else text)
    defaults, needs = {}, {}
    for class_name, fields in sorted(seen.items()):
        entry = {'Common': [], 'Data': []}
        missing = []
        for (part, name), texts in sorted(fields.items(), key=lambda item: order[class_name][item[0]]):
            if None not in texts and len(set(texts)) == 1 and (class_name, part, name) not in ALWAYS_SUPPLIED:
                entry[part].append([name, json.loads(texts[0])])
            else:
                missing.append(f'{part}.{name}')
        defaults[class_name] = entry
        needs[class_name] = missing
    Path(args.out).write_text(json.dumps(defaults, separators=(',', ':')) + '\n')
    for class_name, missing in needs.items():
        print(f'{class_name}: {", ".join(missing)}')


if __name__ == '__main__':
    main()
