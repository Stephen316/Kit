import json
import lzma
import sys
from pathlib import Path

repository = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(repository / 'src'))

from convert.formats.Fusion.MetaIndex import SegmentKind
from convert.formats.Fusion.SegmentCodec.Metadata.ReadMetaWire import ReadMetaWire

names = {}
for item in json.loads((repository / 're/Fusion/Reconstruction/BinaryClasses.json').read_text()).get('classes', []):
    names[item['identifier'].upper()] = item['class']
vocab = {}
for source in ('src/convert/formats/Fusion/DocumentCodec/Vocabulary/DesignClasses.json', 'src/convert/formats/Fusion/ContainerCodec/Assembly/ActClasses.json', 'src/convert/formats/Fusion/ContainerCodec/Browser/BrowserClasses.json'):
    for item in json.loads((repository / source).read_text()):
        vocab[item['ClassGuid'].upper()] = item.get('NameValue')
native = {item['ClassGuid'].upper() for item in json.loads(lzma.decompress((repository / 'src/convert/formats/Fusion/EntityCodec/Vocabulary/NativeClasses.xz').read_bytes()))['Classes']}

kinds = {'FusionDesignSegmentType1': SegmentKind.KDesign, 'FusionACTSegmentType1': SegmentKind.KAct, 'FusionBrowserSegmentType1': SegmentKind.KBrowser}


def classes(folder):
    out = {}
    for sub, kind in kinds.items():
        meta = (Path(folder) / 'FusionAssetName[Active]' / sub / 'MetaStream.dat')
        if not meta.exists():
            continue
        segment = ReadMetaWire(meta.read_bytes(), Segment=kind)
        for row in segment.Classes:
            out[(sub[6:10], row.ClassGuid.upper())] = (len(row.OwnerIds), row.SchemaVersion, row.ClassSpace)
    return out


base = classes(sys.argv[1])
for other in sys.argv[2:]:
    found = classes(other)
    print('==', Path(other).name)
    for key in sorted(set(found) - set(base)):
        print('  +', key[0], key[1], found[key], names.get(key[1]), 'vocab' if key[1] in vocab else '-', 'native' if key[1] in native else '-')
    for key in sorted(set(base) & set(found)):
        if base[key] != found[key]:
            print('  ~', key[0], key[1], base[key], '->', found[key], names.get(key[1]))
