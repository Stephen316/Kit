"""Native acceptance of archives whose members the boundary pass made readable.

Inputs come from re/Fusion/Reconstruction/ComplexGeometry/PrepareBounds.py.
Each case opens the native control and the typed re-emitted archive, measures
every stage, rolls the timeline back marker by marker, rebuilds, edits the
driving parameter when the case names one, saves to a local archive and
reopens it. Helix cases also measure the NURBS thread faces and edges so the
parameter edit shows up in measured values. Parameters are observed by name,
expression and unit only, because Parameter.value raises on the emboss text
parameter of two_texts.f3d. Run only through RunLocked.mjs.
"""

import hashlib
import json
import math
from pathlib import Path
import shutil
import tempfile
import traceback

import adsk.core
import adsk.fusion

root = Path(__file__).resolve().parents[3]
folder = Path(__file__).resolve().parent / 'ComplexGeometry' / 'Bounds'
app = adsk.core.Application.get()
original = app.activeDocument
document = None
vendor = Path(tempfile.mkdtemp(prefix='kit-bounds-'))
report = dict(schema='FusionComplexBoundsAcceptance/1', fusion_version=app.version, documents_before=app.documents.count, scope='Archives with FDM thread attributes, helix subtypes, wire records, no-merge attributes, degenerate edges and records above the old 4096-token and board limits, re-emitted by the typed codec', cases=[])
NURBS = 'adsk::core::NurbsSurface'
CURVE = 'adsk::core::NurbsCurve3D'


def kind(entity):
    return 'None' if entity.geometry is None else entity.geometry.objectType


def checkpoint():
    (folder / 'NativeAcceptance.json').write_text(json.dumps(report, indent=1) + '\n')


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def compare(first, second, trail='state', tolerance=1e-8):
    if isinstance(first, float) and isinstance(second, (float, int)) and not isinstance(second, bool):
        if not math.isclose(first, second, rel_tol=tolerance, abs_tol=tolerance):
            raise RuntimeError(f'{trail}: {first} != {second}')
    elif isinstance(first, dict) and isinstance(second, dict):
        if first.keys() != second.keys():
            raise RuntimeError('Different fields at ' + trail)
        for key in first:
            compare(first[key], second[key], trail + '.' + str(key), tolerance)
    elif isinstance(first, (list, tuple)) and isinstance(second, (list, tuple)):
        if len(first) != len(second):
            raise RuntimeError('Different counts at ' + trail)
        for index, (left, right) in enumerate(zip(first, second)):
            compare(left, right, trail + '.' + str(index), tolerance)
    elif first != second:
        raise RuntimeError(f'{trail}: {first!r} != {second!r}')


def float_drift(first, second, trail='stages'):
    if isinstance(first, float) and isinstance(second, (float, int)) and not isinstance(second, bool):
        scale = max(abs(first), abs(second))
        return 0.0 if scale == 0 else abs(first - second) / scale
    if isinstance(first, dict) and isinstance(second, dict):
        if first.keys() != second.keys():
            raise RuntimeError('Different fields at ' + trail)
        return max((float_drift(first[key], second[key], trail + '.' + str(key)) for key in first), default=0.0)
    if isinstance(first, (list, tuple)) and isinstance(second, (list, tuple)):
        if len(first) != len(second):
            raise RuntimeError('Different counts at ' + trail)
        return max((float_drift(left, right, trail + '.' + str(index)) for index, (left, right) in enumerate(zip(first, second))), default=0.0)
    if first != second:
        raise RuntimeError(f'{trail}: {first!r} != {second!r}')
    return 0.0


def thread_info(body):
    faces = [face for face in body.faces if kind(face) == NURBS]
    edges = [edge for edge in body.edges if kind(edge) == CURVE]
    if not faces:
        return None
    low = [min(face.boundingBox.minPoint.asArray()[axis] for face in faces) for axis in range(3)]
    high = [max(face.boundingBox.maxPoint.asArray()[axis] for face in faces) for axis in range(3)]
    return dict(nurbsFaces=len(faces), nurbsFaceAreaCm2=sum(face.area for face in faces), nurbsEdges=len(edges), nurbsEdgeLengthCm=sum(edge.length for edge in edges), boxCm=[low, high])


def body_info(body):
    bounds = body.boundingBox
    info = dict(name=body.name, valid=body.isValid, solid=body.isSolid, faces=body.faces.count, edges=body.edges.count, vertices=body.vertices.count, areaCm2=body.area, volumeCm3=body.volume if body.isSolid else None, boundsCm=[bounds.minPoint.asArray(), bounds.maxPoint.asArray()], surfaceTypes=sorted(kind(face) for face in body.faces), curveTypes=sorted(kind(edge) for edge in body.edges))
    info['thread'] = thread_info(body)
    return info


def all_bodies(design):
    return [body for component in design.allComponents for body in component.bRepBodies]


def observe(design):
    return dict(marker=design.timeline.markerPosition, parameters=[dict(name=value.name, expression=value.expression, unit=value.unit) for value in design.allParameters], timeline=[dict(name=value.name, health=value.healthState, message=value.errorOrWarningMessage) for value in design.timeline], bodies=[body_info(body) for body in all_bodies(design)])


def validate(stage, label):
    if not all(body['valid'] for body in stage['bodies']):
        raise RuntimeError(label + ' has an invalid body')
    if any(value['health'] == adsk.fusion.FeatureHealthStates.ErrorFeatureHealthState for value in stage['timeline']):
        raise RuntimeError(label + ' has a failed feature')


def open_archive(path):
    global document
    document = app.importManager.importToNewDocument(app.importManager.createFusionArchiveImportOptions(str(path)))
    if document is None:
        raise RuntimeError('Native archive import failed')
    return adsk.fusion.Design.cast(document.products.itemByProductType('DesignProductType'))


def close_document():
    global document
    if document is not None and document.isValid:
        document.close(False)
    document = None


def save_reopen(design, label):
    path = vendor / ('vendor_' + label + '.f3d')
    if not design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(path))):
        raise RuntimeError('Native archive export failed')
    sha = digest(path)
    close_document()
    return open_archive(path), sha


def thread_change(before, after, expected):
    rows = []
    for first, second in zip(before['bodies'], after['bodies']):
        if first['thread'] is None or second['thread'] is None:
            continue
        old, new = first['thread'], second['thread']
        extents = [[old['boxCm'][1][axis] - old['boxCm'][0][axis] for axis in range(3)], [new['boxCm'][1][axis] - new['boxCm'][0][axis] for axis in range(3)]]
        deltas = [extents[1][axis] - extents[0][axis] for axis in range(3)]
        axis = max(range(3), key=lambda index: abs(deltas[index]))
        rows.append(dict(body=first['name'], axis=axis, extentBeforeCm=extents[0][axis], extentAfterCm=extents[1][axis], extentChangeCm=deltas[axis], expectedChangeCm=expected, nurbsFaceAreaBeforeCm2=old['nurbsFaceAreaCm2'], nurbsFaceAreaAfterCm2=new['nurbsFaceAreaCm2'], nurbsEdgeLengthBeforeCm=old['nurbsEdgeLengthCm'], nurbsEdgeLengthAfterCm=new['nurbsEdgeLengthCm'], volumeBeforeCm3=first['volumeCm3'], volumeAfterCm3=second['volumeCm3']))
    if not rows:
        raise RuntimeError('No body with NURBS thread faces in both stages')
    for row in rows:
        row['reflected'] = abs(row['extentChangeCm'] - expected) <= 0.02 and row['nurbsFaceAreaAfterCm2'] != row['nurbsFaceAreaBeforeCm2'] and row['nurbsEdgeLengthAfterCm'] != row['nurbsEdgeLengthBeforeCm']
    return rows


def run_variant(case, variant, relative, sha):
    path = root / relative
    if digest(path) != sha:
        raise RuntimeError('Acceptance input changed: ' + relative)
    entry = dict(variant=variant, source=relative, source_sha256=sha, stages={})
    design = open_archive(path)
    entry['stages']['opened'] = observe(design)
    validate(entry['stages']['opened'], variant + ' opened')
    for marker in reversed(range(design.timeline.count)):
        design.timeline.markerPosition = marker
        entry['stages']['rollback_' + str(marker)] = observe(design)
    if not design.timeline.moveToEnd() or not design.computeAll():
        raise RuntimeError('History restore or rebuild failed')
    entry['stages']['rebuilt'] = observe(design)
    validate(entry['stages']['rebuilt'], variant + ' rebuilt')
    last = 'rebuilt'
    if case.get('parameter'):
        parameter = design.allParameters.itemByName(case['parameter'])
        if parameter is None:
            raise RuntimeError('Driving parameter is absent')
        prior = parameter.value
        parameter.value = prior * case['factor']
        if not design.computeAll():
            raise RuntimeError('Driving parameter edit failed to rebuild')
        entry['stages']['edited'] = observe(design)
        validate(entry['stages']['edited'], variant + ' edited')
        entry['edit'] = dict(name=case['parameter'], prior=prior, edited=parameter.value, expression=parameter.expression)
        entry['thread_change'] = thread_change(entry['stages']['rebuilt'], entry['stages']['edited'], case['expectedThreadExtentChangeCm'])
        last = 'edited'
    design, entry['saved_sha256'] = save_reopen(design, case['label'] + variant)
    if not design.computeAll():
        raise RuntimeError('Reopened archive failed to rebuild')
    entry['stages']['reopened'] = observe(design)
    validate(entry['stages']['reopened'], variant + ' reopened')
    shape = lambda bodies: [(body['faces'], body['edges'], body['vertices'], body['surfaceTypes']) for body in bodies]
    if shape(entry['stages'][last]['bodies']) != shape(entry['stages']['reopened']['bodies']):
        raise RuntimeError('Reopened archive changed its topology')
    entry['reopen_relative_drift'] = float_drift(entry['stages'][last]['bodies'], entry['stages']['reopened']['bodies'])
    close_document()
    entry['status'] = 'accepted'
    return entry


def accept(case):
    result = dict(label=case['label'], scope=case['scope'], source=case['source'], source_sha256=case['sourceSha256'], target=case['target'], target_sha256=case['targetSha256'], member_sha256=[dict(member=item['member'], sha256=item['sha256'], emittedSha256=item['emittedSha256'], byteExact=item['byteExact']) for item in case['members']], variants=[])
    report['cases'].append(result)
    for variant, relative, sha in (('Control', case['source'], case['sourceSha256']), ('Reemitted', case['target'], case['targetSha256'])):
        result['variants'].append(run_variant(case, variant, relative, sha))
        checkpoint()
    control, reemitted = result['variants'][0]['stages'], result['variants'][1]['stages']
    try:
        compare(control, reemitted, 'variants')
        result['comparison'] = 'every stage equal within 1e-8'
    except RuntimeError as error:
        result['strict_difference'] = str(error)
        result['variants'].append(run_variant(case, 'ControlRepeat', case['source'], case['sourceSha256']))
        repeat = result['variants'][2]['stages']
        result['control_self_drift'] = float_drift(control, repeat)
        result['reemitted_drift'] = float_drift(control, reemitted)
        if result['reemitted_drift'] > max(2 * result['control_self_drift'], 1e-8):
            raise RuntimeError('Re-emitted archive differs from control beyond native self-variation')
        result['comparison'] = 'structure, strings and integers equal; floats within twice the control-versus-control drift'
    if case.get('parameter'):
        result['helix_reflected'] = all(row['reflected'] for variant in result['variants'] for row in variant['thread_change'])
    result['status'] = 'accepted'
    checkpoint()


try:
    prepared = json.loads((folder / 'Preparation.json').read_text())
    report['preparation_sha256'] = digest(folder / 'Preparation.json')
    for case in prepared['cases']:
        accept(case)
    report['status'] = 'accepted'
except Exception:
    report['status'] = 'failed'
    report['traceback'] = traceback.format_exc()
    raise
finally:
    close_document()
    if original is not None and original.isValid:
        original.activate()
    shutil.rmtree(vendor, ignore_errors=True)
    report['documents_after'] = app.documents.count
    checkpoint()
