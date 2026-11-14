import hashlib
import io
import json
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'src'))

from convert.formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument

TARGET = ROOT / 're/Fusion/LocalOracle/ReaderCoverage'

CASES = [
    ('DraftV6', 're/Fusion/LocalOracle/JournalStates/vendor_DraftControlEdited.f3d', 'DcDraftFeature v6 with m_fixedPlaneDraftAngleMode and DRMatrix v16 under a parametric timeline'),
    ('TransientHolder', 're/Fusion/LocalOracle/Brep/vendor_binary_temporary.f3d', 'TransientEntityHolder v0 and newest-version closure of classes absent from metadata'),
    ('DecodedSphere', 're/Fusion/LocalOracle/RoundBodies/vendor_DecodedSphere.f3d', 'TransientEntityHolder v0 in a decoded round body document'),
    ('RoundFillets', 're/Fusion/LocalOracle/RoundBodies/vendor_RoundFilletsControl.f3d', 'DRMatrix v16 nonidentity matrix3d rows'),
    ('StripCuboid', 're/Fusion/LocalOracle/PublicAdapter/vendor_cuboidEdited.f3d', 'OgsSimpleMesh triangle-strip primitive 5 in mesh streams'),
    ('StripRectangle', 're/Fusion/LocalOracle/DimensionAuthoring/vendor_DimensionedRectangleEdited.f3d', 'triangle-strip primitive 5 for dimension arrowheads'),
    ('CylinderIds', 're/Fusion/LocalOracle/RotationalDocuments/vendor_NativeCylinderControl.f3d', 'typed cylinder history with assigned face and vertex entity ids'),
    ('FrustumIds', 're/Fusion/LocalOracle/RotationalDocuments/vendor_NativeFrustumControl.f3d', 'typed frustum history with assigned face and vertex entity ids'),
    ('JournalFallback', 're/Fusion/Study/extents-f0f33a9a605f/offset_negative.f3d', 'typed body view disagrees, exact journal model kept'),
    ('SnapshotFallback', 're/Fusion/Study/namedbodies-3c7c11fc2924/namedbodies.f3d', 'typed snapshot view disagrees, exact geometry state kept'),
    ('PrismFallback', 're/Fusion/Study/thinextrudes-f758eff14202/open_line_side1.f3d', 'prism record inventory outside the typed view, exact journal model kept'),
    ('AssemblyIds', 're/Fusion/Study/assembly-acc48a9dc05d/assembly.f3d', 'multi-component document with assigned BRep entity ids'),
    ('DeflatedFolders', 're/Fusion/LocalOracle/JournalStates/DraftTypedHistory.f3d', 'container with deflated empty directory entries'),
    ('WireShell', 're/Fusion/Study/splitfacemodes-4fc4adf2a868/along_vector.f3d', 'journal shell holding a wire and no face, and wire-owned coedges'),
    ('NestedTag', 're/Fusion/Study/moretools-88a2cd6cad0b/MoveRotate.f3d', 'journal generic tags owning a nested tag with an empty identifier'),
    ('ThreadFace', 're/Fusion/Study/threadmodes-d51d2ae60564/modeled_full.f3d', 'journal thread face feature attributes with two payloads'),
    ('EdgeRing', 're/Fusion/Study/thinextrudes-c1632bcb5efe/closed_two_sides_mixed.f3d', 'four-use alternating nonmanifold edge rings in saved geometry and journal'),
    ('FillRing', 're/Fusion/Study/boundaryfills-a0953038318b/plane_first.f3d', 'boundary fill journal with four-use mixed-sense edge rings and 64-bit sculpt name attributes'),
    ('FillCells', 're/Fusion/Study/boundaryfills-a0953038318b/component_middle.f3d', 'boundary fill journal with three-use edge rings and 64-bit sculpt name attributes'),
    ('ApexEdge', 're/Fusion/Study/holes-926347c1eaa8/simple.f3d', 'journal cone apex edges without a curve'),
    ('TorusSign', 're/Fusion/Study/specialfillets-d50f7a4f04e0/rule_all_both.f3d', 'journal torus carriers with a negative minor radius'),
    ('FreeRoots', 're/Fusion/Study/extents-f0f33a9a605f/from_plane.f3d', 'journal root count including free faces and free edges'),
    ('WorkingDelta', 're/Fusion/Study/pathpatterns-de9857f6a1bc/arc_along.f3d', 'journal saved with an open working delta state'),
    ('BoardSize', 're/Fusion/Study/patterns-35e49809a812/symmetric_one.f3d', 'journal bulletin board with more than 1000 changes'),
    ('SceneMesh', 're/Fusion/Study/timeline-5867579925b5/grouped.f3d', 'Fusion_mesh enhanced edge and face display items in graphics scenes'),
    ('RolledScene', 're/Fusion/Study/timeline-5867579925b5/rolled_back.f3d', 'Fusion_mesh scenes in a rolled-back timeline'),
]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def differing(before, after):
    left = zipfile.ZipFile(io.BytesIO(before))
    right = zipfile.ZipFile(io.BytesIO(after))
    names = sorted(set(left.namelist()) | set(right.namelist()))
    result = []
    for name in names:
        if name.endswith('/'):
            continue
        if name not in left.namelist() or name not in right.namelist() or left.read(name) != right.read(name):
            result.append(name)
    return result


def views(model):
    return {
        'bodies': sorted(type(body.History).__name__ for body in model.Bodies),
        'snapshots': sorted(type(snap.Snapshot).__name__ for snap in model.Snapshots),
    }


if __name__ == '__main__':
    TARGET.mkdir(parents=True, exist_ok=True)
    rows = []
    for label, source, covers in CASES:
        data = (ROOT / source).read_bytes()
        model = ReadDocument(data)
        emitted = EmitParsed(model)
        again = ReadDocument(emitted)
        if again != model:
            raise SystemExit('model inequality for ' + source)
        output = TARGET / (label + 'Reemitted.f3d')
        output.write_bytes(emitted)
        rows.append({
            'label': label,
            'covers': covers,
            'source': source,
            'source_sha256': digest(data),
            'output': str(output.relative_to(ROOT)),
            'output_sha256': digest(emitted),
            'model_equal': True,
            'byte_identical': data == emitted,
            'differing_members': differing(data, emitted),
            'views': views(model),
        })
    (TARGET / 'Preparation.json').write_text(json.dumps({'python': sys.version.split()[0], 'codec': 'ReadDocument then EmitParsed', 'cases': rows}, indent=2) + '\n')
    for row in rows:
        print(row['label'], row['byte_identical'], len(row['differing_members']), row['views'])
