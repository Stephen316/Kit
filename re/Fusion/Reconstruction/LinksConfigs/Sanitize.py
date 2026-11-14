import io
import json
import re
import sys
import zipfile
from dataclasses import replace
from pathlib import Path

repository = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(repository / 'src'))

from convert.formats.Fusion.SegmentCodec.Manifest.EmitRootWire import EmitRootWire
from convert.formats.Fusion.SegmentCodec.Manifest.ReadRootWire import ReadRootWire

lineage = re.compile(rb'(?:dm\.lineage:|fs\.file:vf\.)([A-Za-z0-9_-]{22})')
lineage_wide = re.compile(rb'(?:d\x00m\x00\.\x00l\x00i\x00n\x00e\x00a\x00g\x00e\x00:\x00|f\x00s\x00\.\x00f\x00i\x00l\x00e\x00:\x00v\x00f\x00\.\x00)((?:[A-Za-z0-9_-]\x00){22})')
private_pairs = repository / 're/Fusion/LocalOracle/LinksConfigs/tmp/PrivatePairs.json'
user_pairs = [tuple(pair) for pair in json.loads(private_pairs.read_text())] if private_pairs.exists() else []
user_pairs.append((str(Path.home()) + '/', '/Users/user/'))


class Mapper:
    def __init__(self, known=None):
        self.keys = dict(known or {})

    def key(self, original):
        if original not in self.keys:
            self.keys[original] = f'KitLinkLineage{len(self.keys) + 1:08d}'
        return self.keys[original]

    def collect(self, payload):
        for match in lineage.finditer(payload):
            self.key(match.group(1).decode('ascii'))
        for match in lineage_wide.finditer(payload):
            self.key(match.group(1).decode('utf-16-le'))

    def apply(self, payload):
        for original, synthetic in self.keys.items():
            payload = payload.replace(original.encode('ascii'), synthetic.encode('ascii'))
            payload = payload.replace(original.encode('utf-16-le'), synthetic.encode('utf-16-le'))
        for original, synthetic in user_pairs:
            payload = payload.replace(original.encode('ascii'), synthetic.encode('ascii'))
            payload = payload.replace(original.encode('utf-16-le'), synthetic.encode('utf-16-le'))
        return payload


def synth_path(original, label):
    if not original:
        return original
    base = original.rsplit('/', 1)[-1]
    prefix = f'/synthetic/{label}/'
    filler = len(original) - len(prefix) - len(base)
    if filler < 1:
        return ('/synthetic/' + 'x' * len(original))[:len(original)]
    return prefix + 'x' * (filler - 1) + '/' + base


def sanitize_root(payload, mapper):
    value = ReadRootWire(payload)
    links = tuple(
        replace(link, SourcePath=synth_path(link.SourcePath, 'source'), CachePath=synth_path(link.CachePath, 'cache'), XrefPath=synth_path(link.XrefPath, 'xref'))
        for link in value.Links
    )
    output = EmitRootWire(replace(value, Links=links))
    if len(output) != len(payload):
        raise ValueError('root manifest length changed')
    return mapper.apply(output)


def sanitize(source, target, mapper):
    with zipfile.ZipFile(io.BytesIO(source.read_bytes())) as archive:
        infos = archive.infolist()
        payloads = {info.filename: archive.read(info.filename) for info in infos}
    for payload in payloads.values():
        mapper.collect(payload)
    output = io.BytesIO()
    with zipfile.ZipFile(output, 'w') as archive:
        for info in infos:
            payload = payloads[info.filename]
            if info.filename == 'Manifest.dat':
                payload = sanitize_root(payload, mapper)
            else:
                payload = mapper.apply(payload)
            fresh = zipfile.ZipInfo(info.filename, date_time=info.date_time)
            fresh.external_attr = info.external_attr
            fresh.compress_type = info.compress_type
            archive.writestr(fresh, payload)
    target.write_bytes(output.getvalue())


if __name__ == '__main__':
    out_dir = Path(sys.argv[1])
    out_dir.mkdir(parents=True, exist_ok=True)
    map_path = Path(sys.argv[2])
    mapper = Mapper(json.loads(map_path.read_text()) if map_path.exists() else None)
    for name in sys.argv[3:]:
        source = Path(name)
        stem = source.name.replace('.f3z.f3d', '.f3d')
        sanitize(source, out_dir / stem, mapper)
        print(stem)
    map_path.write_text(json.dumps(mapper.keys, indent=1) + '\n')
