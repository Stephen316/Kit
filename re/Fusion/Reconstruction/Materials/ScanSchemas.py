import collections
import io
import json
import sys
from pathlib import Path
from zipfile import ZipFile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[4]
SWEEP = ROOT / 're/Fusion/LocalOracle/MaterialFamilies/Sweep'


def walk(node, parent, found):
    for child in node:
        found[(parent, child.tag)].update(child.attrib)
        walk(child, child.tag, found)


def main():
    tags = collections.defaultdict(set)
    schemas = {}
    for path in sorted(SWEEP.glob('*.f3d')):
        with ZipFile(path) as outer:
            name = next(item for item in outer.namelist() if item.endswith('.protein'))
            with ZipFile(io.BytesIO(outer.read(name))) as inner:
                for member in inner.namelist():
                    if 'Schemas/' in member and member.endswith('.xml'):
                        root = ET.fromstring(inner.read(member))
                        stem = Path(member).stem
                        text = ET.tostring(root)
                        if stem in schemas and schemas[stem]['text'] != text:
                            schemas[stem]['variants'] += 1
                        schemas.setdefault(stem, {'text': text, 'variants': 0, 'first': path.stem})
                        schemas[stem]['count'] = schemas[stem].get('count', 0) + 1
                        walk(root, root.tag, tags)
    for stem, value in sorted(schemas.items()):
        print(stem, value['count'], 'variants', value['variants'], 'first', value['first'])
    for (parent, tag), attrs in sorted(tags.items()):
        print(' ', parent, '>', tag, sorted(attrs))
    if len(sys.argv) > 1:
        Path(sys.argv[1]).write_text(json.dumps({stem: value['text'].decode() for stem, value in schemas.items()}, indent=1))


if __name__ == '__main__':
    main()
