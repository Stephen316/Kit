import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(BASE))

from ExampleRecords import documents, segments
from convert.formats.Fusion.EntityCodec.Vocabulary.ReadCatalog import ReadCatalog

VOCABULARY = ROOT / 'src/convert/formats/Fusion/DocumentCodec/Vocabulary'
TARGET = VOCABULARY / 'HistoricClasses.json'
SOURCES = (
    VOCABULARY / 'DesignClasses.json',
    VOCABULARY / 'FormClasses.json',
    VOCABULARY / 'SavedClasses.json',
    ROOT / 'src/convert/formats/Fusion/ContainerCodec/Assembly/ActClasses.json',
    ROOT / 'src/convert/formats/Fusion/ContainerCodec/Browser/BrowserClasses.json',
)


def unique_layouts():
    rows = json.loads((BASE / 'VersionLayouts.json').read_text())
    for row in rows:
        if len(row['layouts']) == 1:
            yield row['class'], row['version'], row['layouts'][0]


def vocabulary():
    found = {}
    for source in SOURCES:
        for entry in json.loads(source.read_text()):
            found[(entry['ClassGuid'].upper(), entry['SchemaVersion'])] = entry
    return found


def native(guid, version):
    for entry in json.loads(__import__('lzma').decompress((ROOT / 'src/convert/formats/Fusion/EntityCodec/Vocabulary/NativeClasses.xz').read_bytes()))['Classes']:
        if entry['ClassGuid'].upper() == guid and entry['SchemaVersion'] == version:
            return entry
    return None


def metadata_rows():
    rows = {}
    for name, data in documents():
        for segment, meta, spans, bulk in segments(data):
            for row in meta.Classes:
                rows.setdefault((row.ClassGuid.upper(), row.SchemaVersion), set()).add((row.BaseGuid.upper(), row.ClassSpace))
    return rows


def main():
    gaps = {gap['class']: gap['class_guid'].upper() for gap in json.loads((BASE.parent / 'ReaderCoverage' / 'ExampleGaps.json').read_text())['gaps']}
    known = vocabulary()
    rows = metadata_rows()
    output = []
    for name, version, layout in unique_layouts():
        guid = gaps[name]
        source = known.get((guid, layout['from'])) or native(guid, layout['from'])
        if source is None:
            raise SystemExit(f'no source schema for {name} {layout["from"]}')
        bases = rows[(guid, version)]
        if len(bases) != 1:
            raise SystemExit(f'ambiguous metadata base for {name} {version}')
        base, space = next(iter(bases))
        rebased = base != source['BaseGuid'].upper()
        members = [member for member in source['Members'] if member['FieldName'] not in layout['removed']]
        named = known.get((guid, layout['from']))
        output.append({
            'ClassGuid': source['ClassGuid'],
            'BaseGuid': base if rebased else source['BaseGuid'],
            'SchemaVersion': version,
            'Members': members,
            'IsValue': source['IsValue'],
            'NameValue': named['NameValue'] if named else name.split('::')[-1],
            'ClassSpace': space if rebased or not named else named['ClassSpace'],
        })
    TARGET.write_text(json.dumps(output, indent=2) + '\n')
    print(json.dumps([(entry['NameValue'], entry['SchemaVersion'], len(entry['Members'])) for entry in output]))


if __name__ == '__main__':
    main()
