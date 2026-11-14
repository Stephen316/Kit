import hashlib
import json
import sys
from pathlib import Path

repository = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(repository / 'src'))

from convert.formats.Fusion.DocumentCodec.Model.DocumentSpec import DocumentSpec
from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.formats.Fusion.LinkAuthor.EmitAssembly import EmitAssembly
from convert.formats.Fusion.LinkAuthor.Model.AssemblySpec import AssemblySpec
from convert.formats.Fusion.LinkAuthor.Model.LinkTarget import LinkTarget
from convert.formats.Fusion.LinkAuthor.Model.PlacedPart import PlacedPart
from convert.formats.Fusion.LinkAuthor.Model.RigidJoint import RigidJoint
from convert.formats.Fusion.MetaIndex import SegmentKind

private = repository / 're/Fusion/LocalOracle/LinksConfigs/tmp'
author = private / 'author'
run = 'Author1'

# Placement matrices are row-major 4x4 in Fusion internal centimetres.
part_b_in_sub = (0.0, -1.0, 0.0, 2.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 0.0, 0.0, 0.0, 1.0)
part_a_in_root = (0.6, -0.8, 0.0, 5.0, 0.8, 0.6, 0.0, 2.0, 0.0, 0.0, 1.0, 1.0, 0.0, 0.0, 0.0, 1.0)
sub_in_root = (1.0, 0.0, 0.0, -3.0, 0.0, 0.0, -1.0, 4.0, 0.0, 1.0, 0.0, 0.5, 0.0, 0.0, 0.0, 1.0)


def compose(left, right):
    return tuple(sum(left[row * 4 + k] * right[k * 4 + col] for k in range(4)) for row in range(4) for col in range(4))


def urns():
    path = author / 'Urns.json'
    known = json.loads(path.read_text()) if path.exists() else {}
    probe = private / 'ProbeAsmTargets.json'
    if probe.exists():
        for row in json.loads(probe.read_text()).get('probes', []):
            if row.get('lineage_urn') and row.get('version_urn'):
                known[row['name']] = {'lineage_urn': row['lineage_urn'], 'version_urn': row['version_urn'], 'version': row.get('version')}
    path.write_text(json.dumps(known, indent=2) + '\n')
    return known


def target(name, known):
    entry = known[name]
    return LinkTarget(name, entry['lineage_urn'], entry['version_urn'], ReadDocument((author / (name + '.f3d')).read_bytes()))


def summary(name, data, spec):
    model = ReadDocument(data)
    design = [s for s in model.Segments if s.Metadata.Header.Segment is SegmentKind.KDesign][0]
    return {
        'name': name,
        'operation': 'EmitAssembly(AssemblySpec)',
        'targets': [t.DisplayName for t in spec.Targets],
        'placements': [{'target': spec.Targets[p.TargetIndex].DisplayName, 'matrix_cm': list(p.Matrix), 'grounded': p.Grounded} for p in spec.Placements],
        'joint': None if spec.Joint is None else [spec.Joint.FirstIndex, spec.Joint.SecondIndex],
        'design_next_id': design.Metadata.NextId,
        'contexts': {s.Metadata.Header.Segment.name: len(s.Metadata.Contexts) for s in model.Segments},
        'links': len(model.Document.Links),
        'output_bytes': len(data),
        'output_sha256': hashlib.sha256(data).hexdigest(),
    }


def build(stage):
    known = urns()
    if stage == 'sub':
        name = 'KitAsmSub'
        spec = AssemblySpec(DocumentSpec(name, 'subLength', 3.0, ProfileKind='parameter'), (target('KitAsmPartB', known),), (PlacedPart(0, part_b_in_sub),), SourcePath=name + '.f3d')
    elif stage == 'root':
        name = 'KitAsmRoot'
        spec = AssemblySpec(
            DocumentSpec(name, 'rootLength', 10.0, ProfileKind='parameter'),
            (target('KitAsmPartA', known), target('KitAsmSub', known)),
            (PlacedPart(0, part_a_in_root, True), PlacedPart(1, sub_in_root)),
            RigidJoint(0, 1),
            SourcePath=name + '.f3d',
        )
    else:
        raise SystemExit('stage must be sub or root')
    data = EmitAssembly(spec)
    (author / (name + '.f3d')).write_bytes(data)
    row = summary(name, data, spec)
    path = author / 'Assembly.json'
    report = json.loads(path.read_text()) if path.exists() else {'outputs': []}
    report['outputs'] = [entry for entry in report['outputs'] if entry['name'] != name] + [row]
    path.write_text(json.dumps(report, indent=2) + '\n')
    (author / 'Upload.json').write_text(json.dumps({'run': run, 'files': [{'name': name, 'sha256': row['output_sha256']}]}, indent=2) + '\n')
    (author / 'Probe.json').write_text(json.dumps({'run': run, 'names': [name]}, indent=2) + '\n')
    if stage == 'root':
        expected = {
            'KitAsmPartA:1': list(part_a_in_root),
            'KitAsmSub:1': list(sub_in_root),
            'KitAsmSub:1+KitAsmPartB:1': list(compose(sub_in_root, part_b_in_sub)),
        }
        accept = {'run': run, 'root': name, 'expected': expected, 'grounded': ['KitAsmPartA:1'], 'edit': {'name': 'KitAsmPartA', 'parameter': 'heightA', 'expression': '8 mm', 'height_cm': 0.8}}
        (author / 'Accept.json').write_text(json.dumps(accept, indent=2) + '\n')
    print(name, row['output_bytes'], row['output_sha256'])


build(sys.argv[1])
