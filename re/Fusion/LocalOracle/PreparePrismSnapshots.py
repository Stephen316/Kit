from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import sys
from zipfile import ZipFile

root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(root / 'src'))

from convert.formats.Fusion.ContainerCodec.Model.ContainerPart import ContainerPart
from convert.formats.Fusion.DocumentCodec.Auxiliary.PrismSnapshot.Models.PrismSnapshot import PrismSnapshot
from convert.formats.Fusion.DocumentCodec.Auxiliary.Snapshots.ReadSnapPart import ReadSnapPart
from convert.formats.Fusion.DocumentCodec.Auxiliary.Snapshots.EmitSnapPart import EmitSnapPart


def digest(value):
    return hashlib.sha256(value).hexdigest()


def prepare():
    output = root / 're/Fusion/LocalOracle/PrismSnapshot'
    output.mkdir(parents=True, exist_ok=True)
    reports = []
    cases = (
        ('OrdinaryRectangle', 're/Fusion/Study/thinextrudes-c1632bcb5efe/ordinary_rectangle_control.f3d', 'd1', 37.0),
        ('SavedCuboid', 're/Fusion/LocalOracle/RectangleAuthoring/vendor_ProductionCuboid37mm.f3d', 'authoredLength', 43.0),
    )
    for label, relative, parameter, edited_height in cases:
        source = root / relative
        target = output / f'{label}Snapshot.f3d'
        with ZipFile(source) as archive:
            names = [name for name in archive.namelist() if name.endswith('.smb')]
            if len(names) != 1:
                raise ValueError('Expected exactly one complete snapshot member')
            original = archive.read(names[0])
            value = ReadSnapPart(ContainerPart(names[0].removeprefix('FusionAssetName[Active]/'), original))
            if not isinstance(value.Snapshot, PrismSnapshot):
                raise ValueError('Expected a typed cuboid snapshot')
            regenerated = EmitSnapPart(value).Payload
            with ZipFile(target, 'w') as result:
                for entry in archive.infolist():
                    result.writestr(entry, regenerated if entry.filename == names[0] else archive.read(entry))
        standalone = output / f'{label}Snapshot.smb'
        standalone.write_bytes(regenerated)
        model = value.Snapshot.Model
        reports.append({
            'name': label,
            'source': relative,
            'source_sha256': digest(source.read_bytes()),
            'output': str(target.relative_to(root)),
            'output_sha256': digest(target.read_bytes()),
            'snapshot_member': names[0],
            'source_snapshot_sha256': digest(original),
            'snapshot': str(standalone.relative_to(root)),
            'snapshot_sha256': digest(regenerated),
            'snapshot_bytes': len(regenerated),
            'geometry_mm': asdict(model),
            'expected_volume_cm3': model.Width * model.Depth * model.Height / 1000,
            'expected_topology': {'faces': 6, 'edges': 12, 'vertices': 8},
            'height_parameter': parameter,
            'edited_height_mm': edited_height,
            'expected_edited_volume_cm3': model.Width * model.Depth * edited_height / 1000,
            'typed_snapshot': asdict(value.Snapshot),
            'scope': 'Only the complete snapshot is typed-decoded and independently serialized; every other member remains this same source archive, including its history, Design, materials and graphics',
            'construction': 'All 168 snapshot records regenerated from typed topology, carrier frames, generic tags, sketch links and headers; no source bytes retained by the model',
            'native_acceptance': 'not performed by this preparation script',
        })
    report = {'cases': reports, 'local_execution': 'Authorized artifact generation for parent-coordinated native acceptance; no local tests or native calls'}
    (output / 'Preparation.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps([{key: value for key, value in item.items() if key != 'typed_snapshot'} for item in reports], indent=2))


if __name__ == '__main__':
    prepare()
