import base64
import hashlib
import json
import lzma
import re
import sys
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'src'))

from compression import zstd  # noqa: E402

from convert.formats.Fusion.DrawingCodec.EmitDrawing import EmitDrawing  # noqa: E402
from convert.formats.Fusion.DrawingCodec.ReadDrawing import ReadDrawing  # noqa: E402

TARGET = ROOT / 'tests/convert/formats/FusionCodec/Drawings/DrawingSources.xz'
REPORT = Path(__file__).resolve().parent / 'Fixtures.json'
CACHE_PREFIX = re.compile(r'^.*/W\.login/F/')
GUID = re.compile(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}')
URN_TOKEN = re.compile(r'(urn:adsk\.wipprod:(?:fs\.file:vf\.|dm\.lineage:))([A-Za-z0-9_-]{22})')
PRIVATE = ('/Users/', 'Library/Application Support', 'AppData')


class Normalizer:
    def __init__(self):
        self.tokens = {}
        self.guids = {}

    def token(self, value):
        if value not in self.tokens:
            self.tokens[value] = ('KitFixtureLineage' + str(len(self.tokens))).ljust(22, 'x')
        return self.tokens[value]

    def text(self, value):
        value = URN_TOKEN.sub(lambda match: match.group(1) + self.token(match.group(2)), value)
        if '/W.login/F/' in value:
            value = CACHE_PREFIX.sub('C:/KitFixture/W.login/F/', value)
            value = GUID.sub(lambda match: self.guids.setdefault(match.group(0), '00000000-0000-4000-8000-%012d' % len(self.guids)), value)
        return value

    def root(self, root):
        links = tuple(replace(link, SourcePath=self.text(link.SourcePath), TargetPath=self.text(link.TargetPath), LocalPath=self.text(link.LocalPath), Properties=tuple((key, self.text(value)) for key, value in link.Properties)) for link in root.References)
        label = None if root.SaveLabel is None else self.text(root.SaveLabel)
        return replace(root, References=links, SaveLabel=label)


class Replay:
    def __init__(self):
        self.frames = {}

    def inflate(self, packed, size):
        value = zstd.decompress(packed)
        if len(value) != size:
            raise ValueError('zstd size mismatch')
        self.frames[value] = packed
        return value

    def compress(self, value):
        if value in self.frames:
            return self.frames[value]
        codec = zstd.ZstdCompressor(options={zstd.CompressionParameter.compression_level: 3, zstd.CompressionParameter.checksum_flag: 1, zstd.CompressionParameter.content_size_flag: 0})
        return codec.compress(value) + codec.flush()


def main(pairs):
    normalizer = Normalizer()
    sources, report = {}, {'schema': 'KitFusionDrawingFixtures/1', 'fixtures': {}}
    for pair in pairs:
        label, path = pair.split('=', 1)
        data = Path(path).read_bytes()
        if path.endswith('.f3d'):
            sources[label] = base64.b64encode(data).decode('ascii')
            report['fixtures'][label] = {'design_sha256': hashlib.sha256(data).hexdigest(), 'design_bytes': len(data)}
            continue
        replay = Replay()
        drawing = ReadDrawing(data, replay.inflate)
        if EmitDrawing(drawing, replay.compress) != data:
            raise ValueError('Control is not byte exact: ' + label)
        layout = tuple(slot for slot in drawing.Layout if not slot.Name.endswith('.dwg'))
        normal = replace(drawing, Root=normalizer.root(drawing.Root), Database=None, Layout=layout)
        output = EmitDrawing(normal, replay.compress)
        text = output.decode('latin-1') + output.decode('utf-16-le', 'ignore')
        if any(token in text for token in PRIVATE) or any(token in text for token in normalizer.tokens):
            raise ValueError('Private token survived normalization: ' + label)
        sources[label] = base64.b64encode(output).decode('ascii')
        report['fixtures'][label] = {'control_sha256': hashlib.sha256(data).hexdigest(), 'control_bytes': len(data), 'fixture_sha256': hashlib.sha256(output).hexdigest(), 'fixture_bytes': len(output), 'database_bytes': len(drawing.Database.Content) if drawing.Database else 0}
    TARGET.write_bytes(lzma.compress(json.dumps(sources, sort_keys=True).encode(), preset=9))
    report['archive_sha256'] = hashlib.sha256(TARGET.read_bytes()).hexdigest()
    REPORT.write_text(json.dumps(report, indent=1) + '\n')
    print(json.dumps(report, indent=1))


if __name__ == '__main__':
    main(sys.argv[1:])
