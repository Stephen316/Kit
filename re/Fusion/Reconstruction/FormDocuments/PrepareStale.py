import dataclasses
import hashlib
import json
import struct
import sys
import zipfile
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[3]
sys.path.insert(0, str(ROOT / 'src'))
from convert.formats.Fusion.TSplineCodec.EmitTspline import EmitTspline
from convert.formats.Fusion.TSplineCodec.ReadTspline import ReadTspline

OUTPUT = ROOT / 're/Fusion/LocalOracle/FormDocuments/Stale'
SOURCES = {
    'Plane': ROOT / 're/Fusion/LocalOracle/TSplineCodec/vendor_PlaneControl.f3d',
    'Box': ROOT / 're/Fusion/LocalOracle/TSplineCodec/vendor_BoxControl.f3d',
}


def moved(text):
    model = ReadTspline(text)
    grips = list(model.Grips)
    first = grips[0]
    grips[0] = dataclasses.replace(first, CoordZ=first.CoordZ + 0.25)
    return EmitTspline(dataclasses.replace(model, Grips=tuple(grips)))


def replace_embedded(data, old, new):
    for tag, width in ((7, '<B'), (8, '<H'), (9, '<I')):
        if len(old) >= 1 << (8 * struct.calcsize(width)):
            continue
        marker = bytes([tag]) + struct.pack(width, len(old)) + old
        if data.count(marker) == 1:
            size = struct.calcsize(width)
            if len(new) >= 1 << (8 * size):
                raise ValueError('Replacement does not fit the original string token')
            return data.replace(marker, bytes([tag]) + struct.pack(width, len(new)) + new)
    raise ValueError('Embedded TSM token not found exactly once')


def rewrite(source, target, member_tsm, brep_tsm, drop_breps):
    with zipfile.ZipFile(source) as archive:
        infos = archive.infolist()
        tsm_name = next(info.filename for info in infos if info.filename.endswith('.tsm'))
        original = archive.read(tsm_name)
        with zipfile.ZipFile(target, 'w') as output:
            for info in infos:
                data = archive.read(info.filename)
                if info.filename == tsm_name and member_tsm is not None:
                    data = member_tsm
                if info.filename.endswith(('.smb', '.smbh')):
                    if drop_breps:
                        continue
                    if brep_tsm is not None:
                        data = replace_embedded(data, original, brep_tsm)
                clone = zipfile.ZipInfo(info.filename, info.date_time)
                clone.compress_type = info.compress_type
                clone.external_attr = info.external_attr
                clone.create_system = info.create_system
                output.writestr(clone, data)


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    rows = []
    for kind, source in SOURCES.items():
        with zipfile.ZipFile(source) as archive:
            original = archive.read(next(name for name in archive.namelist() if name.endswith('.tsm')))
        changed = moved(original)
        variants = {
            'MemberMoved': (changed, None, False),
            'BrepMoved': (None, changed, False),
            'BothMoved': (changed, changed, False),
            'NoBrep': (None, None, True),
        }
        for label, (member, brep, drop) in variants.items():
            target = OUTPUT / (kind + label + '.f3d')
            rewrite(source, target, member, brep, drop)
            rows.append({'kind': kind, 'variant': label, 'source': str(source.relative_to(ROOT)), 'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(), 'file': str(target.relative_to(ROOT)), 'sha256': hashlib.sha256(target.read_bytes()).hexdigest(), 'member_tsm_changed': member is not None, 'brep_tsm_changed': brep is not None, 'breps_removed': drop})
    report = {'scope': 'Research variants for stale or omitted Form BRep caches; raw member rewrite, not a production writer', 'grip_change': 'Grip 0 Z coordinate +0.25 cm', 'cases': rows}
    (OUTPUT / 'Preparation.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
