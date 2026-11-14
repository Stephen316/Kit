import hashlib
import json
import runpy
import sys
import zipfile
from pathlib import Path

root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(root / 'src'))
sys.dont_write_bytecode = True
from convert.formats.Fusion.BrepCodec.ReadHistory import ReadHistory
from convert.formats.Fusion.BrepCodec.EmitHistory import EmitHistory

oracle = root / 're/Fusion/LocalOracle'
source = oracle / 'Features/extrude_07mm.f3d'
target = oracle / 'Authored/NativeHistoryReemitted.f3d'
reader = runpy.run_path(str(root / 're/Fusion/Reconstruction/ReflectedFeatures.py'))['archive_member']
with zipfile.ZipFile(source) as archive:
    names = [entry.filename for entry in archive.infolist()]
    histories = [name for name in names if name.endswith('.smbh')]
    if len(histories) != 1:
        raise ValueError('Expected one controlled history part')
    history_bytes = reader(source, histories[0])
    value = ReadHistory(history_bytes)
    emitted = EmitHistory(value.Model, value.Identity, value.TagSet, value.History, value.Stamp, value.Vertices)
    with zipfile.ZipFile(target, 'w', compression=zipfile.ZIP_STORED) as output:
        for name in names:
            output.writestr(name, emitted if name == histories[0] else reader(source, name))
report = {'scope': 'Production semantic read/re-emit of complete native BRep history; source document retains its own other members', 'sourceSha256': hashlib.sha256(source.read_bytes()).hexdigest(), 'outputSha256': hashlib.sha256(target.read_bytes()).hexdigest(), 'historySourceSha256': hashlib.sha256(history_bytes).hexdigest(), 'historyOutputSha256': hashlib.sha256(emitted).hexdigest(), 'dimensionsMillimeters': {'radius': value.Model.Radius, 'height': value.Model.Height}, 'vertexIndices': {'top': value.Vertices.TopIndex, 'bottom': value.Vertices.BottomIndex}, 'nativeAcceptance': 'pending'}
target.with_suffix('.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report))
