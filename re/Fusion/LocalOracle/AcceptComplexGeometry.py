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
folder = Path(__file__).resolve().parent / 'ComplexGeometry'
app = adsk.core.Application.get()
original = app.activeDocument
document = None
vendor = Path(tempfile.mkdtemp(prefix='kit-complex-'))
report = dict(schema='FusionComplexGeometryAcceptance/1', fusion_version=app.version, documents_before=app.documents.count, scope='Typed complex ASM geometry: authored explicit NURBS bodies, typed pole edit of a corpus patch, byte-exact procedural snapshots, and re-emitted fillet/loft/sweep histories', authored=[], edited=[], geometry=[], histories=[])
NURBS = 'adsk::core::NurbsSurface'


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


def distance(first, second):
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(first, second)))


def surface_data(face):
    surface = adsk.core.NurbsSurface.cast(face.geometry)
    if surface is None:
        return None
    ok, degree_u, degree_v, count_u, count_v, points, knots_u, knots_v, weights, props_u, props_v = surface.getData()
    if not ok:
        raise RuntimeError('NurbsSurface.getData failed')
    return dict(degreeU=degree_u, degreeV=degree_v, countU=count_u, countV=count_v, controlPointsCm=[point.asArray() for point in points], knotsU=list(knots_u), knotsV=list(knots_v), weights=list(weights), propertiesU=props_u, propertiesV=props_v)


def curve_data(edge):
    curve = adsk.core.NurbsCurve3D.cast(edge.geometry)
    if curve is None:
        return None
    ok, points, degree, knots, rational, weights, periodic = curve.getData()
    if not ok:
        raise RuntimeError('NurbsCurve3D.getData failed')
    return dict(degree=degree, knots=list(knots), rational=rational, weights=list(weights), periodic=periodic, controlPointsCm=[point.asArray() for point in points])


def properties(body):
    try:
        props = body.getPhysicalProperties(adsk.fusion.CalculationAccuracy.VeryHighCalculationAccuracy)
    except Exception:
        props = None
    if props is None:
        return dict(accuracy='body', areaCm2=body.area, volumeCm3=body.volume if body.isSolid else None, centerCm=None)
    return dict(accuracy='VeryHigh', areaCm2=props.area, volumeCm3=props.volume if body.isSolid else None, centerCm=props.centerOfMass.asArray() if body.isSolid else None)


def body_info(body, detailed=False):
    bounds = body.boundingBox
    info = dict(valid=body.isValid, solid=body.isSolid, faces=body.faces.count, edges=body.edges.count, vertices=body.vertices.count, areaCm2=body.area, volumeCm3=body.volume if body.isSolid else None, boundsCm=[bounds.minPoint.asArray(), bounds.maxPoint.asArray()], surfaceTypes=sorted(face.geometry.objectType for face in body.faces), curveTypes=sorted(edge.geometry.objectType for edge in body.edges))
    if detailed:
        info['physical'] = properties(body)
        info['facesData'] = [dict(type=face.geometry.objectType, valid=face.isValid, areaCm2=face.area, nurbs=surface_data(face)) for face in body.faces]
        info['edgesData'] = [dict(type=edge.geometry.objectType, valid=edge.isValid, nurbs=curve_data(edge)) for edge in body.edges]
        info['verticesCm'] = [vertex.geometry.asArray() for vertex in body.vertices]
    return info


def all_bodies(design):
    return [body for component in design.allComponents for body in component.bRepBodies]


def observe(design):
    return dict(marker=design.timeline.markerPosition, parameters=[dict(name=value.name, value=value.value, expression=value.expression, unit=value.unit) for value in design.allParameters], timeline=[dict(name=value.name, health=value.healthState, message=value.errorOrWarningMessage) for value in design.timeline], bodies=[body_info(body) for body in all_bodies(design)])


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


def import_bodies(path):
    global document
    bodies = adsk.fusion.TemporaryBRepManager.get().createFromFile(str(path))
    if bodies is None or bodies.count < 1:
        raise RuntimeError('SMB import produced no bodies')
    temporary = [body_info(bodies.item(index)) for index in range(bodies.count)]
    document = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    design = adsk.fusion.Design.cast(document.products.itemByProductType('DesignProductType'))
    design.designType = adsk.fusion.DesignTypes.DirectDesignType
    for index in range(bodies.count):
        if design.rootComponent.bRepBodies.add(bodies.item(index)) is None:
            raise RuntimeError('Temporary body could not be persisted')
    return design, temporary


def match_surface(face, data, expected):
    best = None
    for candidate in expected:
        if (candidate['degreeU'], candidate['degreeV'], candidate['countU'], candidate['countV']) != (data['degreeU'], data['degreeV'], data['countU'], data['countV']):
            continue
        drift = max(distance(a, b) for a, b in zip(candidate['controlPointsCm'], data['controlPointsCm']))
        if best is None or drift < best[0]:
            best = (drift, candidate)
    if best is None or best[0] > 1e-9:
        raise RuntimeError('No expected surface matches a native NURBS face; best drift ' + str(best and best[0]))
    drift, candidate = best
    knot_drift = max([abs(a - b) for a, b in zip(candidate['knotsU'], data['knotsU'])] + [abs(a - b) for a, b in zip(candidate['knotsV'], data['knotsV'])])
    if len(candidate['knotsU']) != len(data['knotsU']) or len(candidate['knotsV']) != len(data['knotsV']) or knot_drift > 1e-12:
        raise RuntimeError('Native knot vectors differ from the authored knots')
    if len(candidate['weights']) != len(data['weights']):
        raise RuntimeError('Native weights disagree with the authored rational form')
    weight_drift = max([abs(a - b) for a, b in zip(candidate['weights'], data['weights'])], default=0.0)
    if weight_drift > 1e-12:
        raise RuntimeError('Native weights differ from the authored weights')
    samples = []
    for sample in candidate['samples']:
        point2d = adsk.core.Point2D.create(*sample['uv'])
        ok, on_surface = face.geometry.evaluator.getPointAtParameter(point2d)
        ok_face, on_face = face.evaluator.getPointAtParameter(point2d)
        inside = face.evaluator.isParameterOnFace(point2d)
        if not ok or not ok_face:
            raise RuntimeError('Native evaluator rejected an authored parameter')
        samples.append(dict(uv=sample['uv'], surfaceDriftCm=distance(on_surface.asArray(), sample['pointCm']), faceDriftCm=distance(on_face.asArray(), sample['pointCm']), onFace=inside))
    worst = max(max(item['surfaceDriftCm'], item['faceDriftCm']) for item in samples)
    if worst > 1e-7 or not all(item['onFace'] for item in samples):
        raise RuntimeError(f'Native evaluation differs from authored evaluation by {worst} or leaves the face')
    return dict(label=candidate['label'], poleDriftCm=drift, knotDrift=knot_drift, weightDrift=weight_drift, samples=len(samples), worstSampleDriftCm=worst, allSamplesOnFace=True)


def match_curves(body, expected):
    worst = 0.0
    other = []
    for edge in body.edges:
        data = curve_data(edge)
        if data is None:
            other.append(edge.geometry.objectType)
            continue
        best = None
        for candidate in expected:
            if candidate['degree'] != data['degree'] or len(candidate['controlPointsCm']) != len(data['controlPointsCm']):
                continue
            forward = max(distance(a, b) for a, b in zip(candidate['controlPointsCm'], data['controlPointsCm']))
            backward = max(distance(a, b) for a, b in zip(candidate['controlPointsCm'][::-1], data['controlPointsCm']))
            drift = min(forward, backward)
            best = drift if best is None else min(best, drift)
        if best is None or best > 1e-9:
            raise RuntimeError('Native edge curve does not match any authored edge curve')
        worst = max(worst, best)
    return dict(worstPoleDriftCm=worst, nurbsEdges=body.edges.count - len(other), otherEdgeTypes=other)


def summary(info):
    return {key: info[key] for key in ('valid', 'solid', 'faces', 'edges', 'vertices', 'areaCm2', 'volumeCm3', 'boundsCm', 'surfaceTypes', 'curveTypes')}


def check_authored(body, expected):
    info = body_info(body, detailed=True)
    if info['solid'] != expected['solid'] or (info['faces'], info['edges'], info['vertices']) != (expected['faces'], expected['edges'], expected['vertices']):
        raise RuntimeError('Native topology counts differ from the authored body')
    if any(face['type'] != NURBS for face in info['facesData']) or not all(face['valid'] for face in info['facesData']):
        raise RuntimeError('Authored faces did not import as valid NurbsSurface faces')
    matched = [match_surface(face, surface_data(face), expected['surfaces']) for face in body.faces]
    if sorted(item['label'] for item in matched) != sorted(item['label'] for item in expected['surfaces']):
        raise RuntimeError('Native faces do not map one to one onto authored surfaces')
    checks = dict(surfaces=matched, curves=match_curves(body, expected['curves']))
    checks['areaRelativeError'] = abs(info['physical']['areaCm2'] - expected['areaCm2']) / expected['areaCm2']
    if checks['areaRelativeError'] > 1e-5:
        raise RuntimeError('Native area differs from the quadrature area')
    if expected['solid']:
        checks['volumeRelativeError'] = abs(info['physical']['volumeCm3'] - expected['volumeCm3']) / expected['volumeCm3']
        checks['centerDriftCm'] = distance(info['physical']['centerCm'], expected['centerCm'])
        if checks['volumeRelativeError'] > 1e-5 or checks['centerDriftCm'] > 1e-5:
            raise RuntimeError('Native volume or centroid differs from the quadrature values')
    low, high = info['boundsCm']
    sampled, hull = expected['sampledBoundsCm'], expected['controlHullCm']
    checks['boundsContainSamples'] = all(low[k] <= sampled[0][k] + 1e-6 and high[k] >= sampled[1][k] - 1e-6 for k in range(3))
    checks['boundsWithinHull'] = all(low[k] >= hull[0][k] - 1e-6 and high[k] <= hull[1][k] + 1e-6 for k in range(3))
    checks['boundsExcessCm'] = max(max(sampled[0][k] - low[k], high[k] - sampled[1][k]) for k in range(3))
    if not checks['boundsContainSamples'] or not checks['boundsWithinHull']:
        raise RuntimeError('Native bounds are inconsistent with the authored geometry')
    vertex_drift = max(min(distance(point, other) for other in expected['verticesCm']) for point in info['verticesCm'])
    checks['vertexDriftCm'] = vertex_drift
    if vertex_drift > 1e-9:
        raise RuntimeError('Native vertices differ from the authored vertices')
    return info, checks


def accept_authored(prepared):
    for item in prepared['authored']:
        path = root / item['target']
        if digest(path) != item['targetSha256']:
            raise RuntimeError('Authored geometry digest changed')
        result = dict(label=item['label'], scope=item['scope'], source_sha256=item['targetSha256'], history_sha256=item['historySha256'])
        report['authored'].append(result)
        design, result['temporary'] = import_bodies(path)
        bodies = design.rootComponent.bRepBodies
        if bodies.count != 1:
            raise RuntimeError('Authored SMB must hold exactly one body')
        result['persisted'], result['checks'] = check_authored(bodies.item(0), item['expected'])
        design, result['saved_sha256'] = save_reopen(design, item['label'])
        result['reopened'], result['reopened_checks'] = check_authored(design.rootComponent.bRepBodies.item(0), item['expected'])
        compare(summary(result['persisted']), summary(result['reopened']), 'reopened', 1e-9)
        result['status'] = 'accepted'
        close_document()
        checkpoint()


def accept_edited(prepared):
    for item in prepared['edited']:
        path = root / item['target']
        if digest(path) != item['targetSha256']:
            raise RuntimeError('Edited geometry digest changed')
        result = dict(label=item['label'], edit=item['edit'], source_sha256=item['targetSha256'])
        report['edited'].append(result)
        design, result['temporary'] = import_bodies(path)
        bodies = list(design.rootComponent.bRepBodies)
        faces = [face for body in bodies for face in body.faces]
        result['bodies'] = [body_info(body) for body in bodies]
        if len(faces) != item['expected']['faces'] or any(face.geometry.objectType != NURBS for face in faces):
            raise RuntimeError('Edited patches did not import as NurbsSurface faces')
        result['surfaces'] = [match_surface(face, surface_data(face), item['expected']['surfaces']) for face in faces]
        if sorted(entry['label'] for entry in result['surfaces']) != ['edited', 'unchanged']:
            raise RuntimeError('Edited and unchanged patches were not both found')
        design, result['saved_sha256'] = save_reopen(design, item['label'])
        result['reopened'] = [body_info(body) for body in design.rootComponent.bRepBodies]
        compare(result['bodies'], result['reopened'], 'reopened', 1e-9)
        result['status'] = 'accepted'
        close_document()
        checkpoint()


def accept_geometry(prepared):
    for item in prepared['geometry']:
        path = root / item['target']
        if digest(path) != item['targetSha256'] or item['targetSha256'] != item['memberSha256']:
            raise RuntimeError('Decoded geometry is not the byte-exact source member')
        result = dict(label=item['label'], families=item['families'], source_sha256=item['sourceSha256'], target_sha256=item['targetSha256'])
        report['geometry'].append(result)
        design = open_archive(root / item['source'])
        result['archive_bodies'] = [body_info(body) for body in all_bodies(design)]
        close_document()
        design, result['temporary'] = import_bodies(path)
        result['persisted'] = [body_info(body) for body in design.rootComponent.bRepBodies]
        if not all(body['valid'] for body in result['persisted']):
            raise RuntimeError('Decoded body is not valid')
        result['nurbs_faces'] = sum(body['surfaceTypes'].count(NURBS) for body in result['persisted'])
        key = lambda body: (round(body['areaCm2'], 9), body['faces'])
        result['matches_archive_bodies'] = sorted(map(key, result['persisted'])) == sorted(map(key, result['archive_bodies']))
        design, result['saved_sha256'] = save_reopen(design, 'Decoded' + item['label'])
        result['reopened'] = [body_info(body) for body in design.rootComponent.bRepBodies]
        compare(result['persisted'], result['reopened'], 'reopened', 1e-9)
        result['status'] = 'accepted'
        close_document()
        checkpoint()


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


def run_variant(item, variant, relative, sha):
    path = root / relative
    if digest(path) != sha:
        raise RuntimeError('Prepared history archive changed')
    entry = dict(variant=variant, source_sha256=sha, stages={})
    design = open_archive(path)
    entry['stages']['opened'] = observe(design)
    for marker in reversed(range(design.timeline.count)):
        design.timeline.markerPosition = marker
        entry['stages']['rollback_' + str(marker)] = observe(design)
    if not design.timeline.moveToEnd() or not design.computeAll():
        raise RuntimeError('History restore or rebuild failed')
    entry['stages']['rebuilt'] = observe(design)
    parameter = design.allParameters.itemByName(item['parameter'])
    if parameter is None:
        raise RuntimeError('Driving parameter is absent')
    prior = parameter.value
    parameter.value = prior * item['factor']
    if not design.computeAll():
        raise RuntimeError('Driving parameter edit failed to rebuild')
    entry['stages']['edited'] = observe(design)
    entry['edit'] = dict(prior=prior, edited=parameter.value, expression=parameter.expression)
    if entry['stages']['edited']['bodies'] == entry['stages']['rebuilt']['bodies']:
        raise RuntimeError('Driving parameter edit did not alter geometry')
    if any(value['health'] == adsk.fusion.FeatureHealthStates.ErrorFeatureHealthState for value in entry['stages']['edited']['timeline']):
        raise RuntimeError('Driving parameter edit left a failed feature')
    design, entry['saved_sha256'] = save_reopen(design, item['label'] + variant)
    if not design.computeAll():
        raise RuntimeError('Reopened history failed to rebuild')
    entry['stages']['reopened'] = observe(design)
    shape = lambda bodies: [(body['faces'], body['edges'], body['vertices'], body['surfaceTypes']) for body in bodies]
    if shape(entry['stages']['edited']['bodies']) != shape(entry['stages']['reopened']['bodies']):
        raise RuntimeError('Reopened edited history changed its topology')
    entry['reopen_relative_drift'] = float_drift(entry['stages']['edited']['bodies'], entry['stages']['reopened']['bodies'])
    close_document()
    entry['status'] = 'accepted'
    return entry


def accept_histories(prepared):
    for item in prepared['histories']:
        result = dict(label=item['label'], parameter=item['parameter'], factor=item['factor'], variants=[])
        report['histories'].append(result)
        for variant, relative, sha in (('Control', item['source'], item['sourceSha256']), ('Reemitted', item['target'], item['targetSha256'])):
            result['variants'].append(run_variant(item, variant, relative, sha))
            checkpoint()
        control, reemitted = result['variants'][0]['stages'], result['variants'][1]['stages']
        try:
            compare(control, reemitted, 'variants')
            result['comparison'] = 'every stage equal within 1e-8'
        except RuntimeError as error:
            result['strict_difference'] = str(error)
            result['variants'].append(run_variant(item, 'ControlRepeat', item['source'], item['sourceSha256']))
            repeat = result['variants'][2]['stages']
            result['control_self_drift'] = float_drift(control, repeat)
            result['reemitted_drift'] = float_drift(control, reemitted)
            result['exact_prefix_stages'] = [name for name in control if float_drift(control[name], reemitted[name]) == 0.0]
            if result['reemitted_drift'] > max(2 * result['control_self_drift'], 1e-8):
                raise RuntimeError('Re-emitted history differs from control beyond native self-variation')
            result['comparison'] = 'structure, strings and integers equal; floats within twice the control-versus-control drift'
        result['status'] = 'accepted'
        checkpoint()

try:
    prepared = json.loads((folder / 'Preparation.json').read_text())
    accept_authored(prepared)
    accept_edited(prepared)
    accept_geometry(prepared)
    accept_histories(prepared)
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
