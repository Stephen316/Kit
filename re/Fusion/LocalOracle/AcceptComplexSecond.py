"""Second native acceptance pass for complex ASM geometry.

Reads ComplexGeometry/SecondPass/Preparation.json and, using local files only:

* authored: imports each wider NURBS body through TemporaryBRepManager, persists it in a
  direct design, checks counts, face types, mass properties against independent
  integrals, surface evaluation, hole membership, vertices and seam pcurves, then
  saves to a local .f3d, reopens it and checks again;
* subtypes: imports each corpus body holding a never-opened subtype and its one-field
  mutant, checks that the Fusion API reports the predicted change, persists both,
  saves and reopens them, and exports attribute cases back to SMB for decoding.

Selection.json (next to Preparation.json) names the run and the labels it covers, so a
crash loses one short run only. Each case records its current stage in the run report
before every native call, so a native exit leaves the exact step in the checkpoint.
Cases marked native=False in Preparation.json are never sent to Fusion.

Every document opened here is closed again and documents_after is recorded.
"""

import hashlib
import json
import math
import shutil
import tempfile
import traceback
from pathlib import Path

import adsk.core
import adsk.fusion

root = Path(__file__).resolve().parents[3]
folder = Path(__file__).resolve().parent / 'ComplexGeometry' / 'SecondPass'
exported = folder / 'Exported'
app = adsk.core.Application.get()
vendor = Path(tempfile.mkdtemp(prefix='kit-complex-second-'))
document = None
selection = json.loads((folder / 'Selection.json').read_text())
report = dict(schema='FusionComplexSecondAcceptance/2', run=selection['run'], selection=selection, fusion_version=app.version, documents_before=app.documents.count, authored=[], subtypes=[], failures=[], status='running')
NURBS = 'adsk::core::NurbsSurface'


def private(text):
    return text.replace(str(root), '<repo>').replace(str(Path.home()), '~')


def checkpoint():
    target = folder / 'Runs' / (selection['run'] + '.json')
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, indent=1) + '\n')


def stage(result, name):
    result['stage'] = name
    checkpoint()


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def distance(first, second):
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(first, second)))


def close_document():
    global document
    if document is not None and document.isValid:
        document.close(False)
    document = None


def surface_data(geometry):
    surface = adsk.core.NurbsSurface.cast(geometry)
    if surface is None:
        return None
    ok, degree_u, degree_v, count_u, count_v, points, knots_u, knots_v, weights, props_u, props_v = surface.getData()
    return dict(ok=ok, degreeU=degree_u, degreeV=degree_v, countU=count_u, countV=count_v, controlPointsCm=[point.asArray() for point in points], knotsU=list(knots_u), knotsV=list(knots_v), weights=list(weights), propertiesU=props_u, propertiesV=props_v)


def curve3_data(geometry):
    curve = adsk.core.NurbsCurve3D.cast(geometry)
    if curve is None:
        return None
    ok, points, degree, knots, rational, weights, periodic = curve.getData()
    return dict(ok=ok, degree=degree, knots=list(knots), rational=rational, weights=list(weights), periodic=periodic, controlPointsCm=[point.asArray() for point in points])


def curve2_data(geometry):
    curve = adsk.core.NurbsCurve2D.cast(geometry)
    if curve is None:
        return None
    ok, points, degree, knots, rational, weights, periodic = curve.getData()
    return dict(ok=ok, degree=degree, knots=list(knots), rational=rational, weights=list(weights), periodic=periodic, controlPoints=[list(point.asArray())[:2] for point in points])


def extents(evaluator):
    try:
        ok, lower, upper = evaluator.getParameterExtents()
        return [lower, upper] if ok else None
    except Exception:
        return None


def physical(body):
    try:
        props = body.getPhysicalProperties(adsk.fusion.CalculationAccuracy.VeryHighCalculationAccuracy)
    except Exception:
        props = None
    if props is None:
        return dict(accuracy='body', areaCm2=body.area, volumeCm3=body.volume if body.isSolid else None, centerCm=None)
    return dict(accuracy='VeryHigh', areaCm2=props.area, volumeCm3=props.volume if body.isSolid else None, centerCm=props.centerOfMass.asArray() if body.isSolid else None)


def summary(body):
    bounds = body.boundingBox
    return dict(valid=body.isValid, solid=body.isSolid, faces=body.faces.count, edges=body.edges.count, vertices=body.vertices.count, areaCm2=body.area, volumeCm3=body.volume if body.isSolid else None, boundsCm=[bounds.minPoint.asArray(), bounds.maxPoint.asArray()], surfaceTypes=sorted(face.geometry.objectType for face in body.faces), curveTypes=sorted(edge.geometry.objectType for edge in body.edges))


def readback(body):
    edges = list(body.edges)
    vertices = list(body.vertices)
    faces = []
    for face in body.faces:
        loops = []
        for loop in face.loops:
            coedges = []
            for coedge in loop.coEdges:
                geometry = coedge.geometry
                coedges.append(dict(edge=edges.index(coedge.edge), opposed=coedge.isOpposedToEdge, range=extents(coedge.evaluator) if geometry else None, nurbs=curve2_data(geometry) if geometry else None))
            loops.append(dict(outer=loop.isOuter, coedges=coedges))
        faces.append(dict(type=face.geometry.objectType, valid=face.isValid, areaCm2=face.area, reversed=face.isParamReversed, nurbs=surface_data(face.geometry), loops=loops))
    edge_rows = [dict(type=edge.geometry.objectType, tolerant=edge.isTolerant, tolerance=edge.tolerance, lengthCm=edge.length, start=vertices.index(edge.startVertex), end=vertices.index(edge.endVertex), range=extents(edge.evaluator), nurbs=curve3_data(edge.geometry)) for edge in edges]
    vertex_rows = [dict(pointCm=vertex.geometry.asArray(), tolerant=vertex.isTolerant, tolerance=vertex.tolerance, edges=sorted(edges.index(edge) for edge in vertex.edges)) for vertex in vertices]
    return dict(summary=summary(body), faces=faces, edges=edge_rows, vertices=vertex_rows)


def import_temporary(path):
    bodies = adsk.fusion.TemporaryBRepManager.get().createFromFile(str(path))
    if bodies is None or bodies.count < 1:
        raise RuntimeError('SMB import produced no bodies')
    return [bodies.item(index) for index in range(bodies.count)]


def persist(bodies):
    global document
    document = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    design = adsk.fusion.Design.cast(document.products.itemByProductType('DesignProductType'))
    design.designType = adsk.fusion.DesignTypes.DirectDesignType
    for body in bodies:
        if design.rootComponent.bRepBodies.add(body) is None:
            raise RuntimeError('Temporary body could not be persisted')
    return design


def open_archive(path):
    global document
    document = app.importManager.importToNewDocument(app.importManager.createFusionArchiveImportOptions(str(path)))
    if document is None:
        raise RuntimeError('Native archive import failed')
    return adsk.fusion.Design.cast(document.products.itemByProductType('DesignProductType'))


def save_reopen(design, label):
    path = vendor / (label + '.f3d')
    if not design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(path))):
        raise RuntimeError('Native archive export failed')
    sha = digest(path)
    close_document()
    return open_archive(path), sha


def same(first, second, trail, tolerance=1e-9):
    if isinstance(first, float) and isinstance(second, (float, int)) and not isinstance(second, bool):
        if not math.isclose(first, second, rel_tol=tolerance, abs_tol=tolerance):
            raise RuntimeError(f'{trail}: {first} != {second}')
    elif isinstance(first, dict) and isinstance(second, dict):
        if first.keys() != second.keys():
            raise RuntimeError('Different fields at ' + trail)
        for key in first:
            same(first[key], second[key], trail + '.' + str(key), tolerance)
    elif isinstance(first, (list, tuple)) and isinstance(second, (list, tuple)):
        if len(first) != len(second):
            raise RuntimeError('Different counts at ' + trail)
        for index, (left, right) in enumerate(zip(first, second)):
            same(left, right, trail + '.' + str(index), tolerance)
    elif first != second:
        raise RuntimeError(f'{trail}: {first!r} != {second!r}')


def poles_equal(found, wanted, tolerance, any_direction=False):
    if found is None or len(found) != len(wanted):
        return False
    if max(distance(a, b) for a, b in zip(found, wanted)) <= tolerance:
        return True
    return any_direction and max(distance(a, b) for a, b in zip(found[::-1], wanted)) <= tolerance


def coedge_sites(rows, wanted):
    found = []
    for body_index, row in enumerate(rows):
        for face_index, face in enumerate(row['faces']):
            for loop_index, loop in enumerate(face['loops']):
                for coedge_index, coedge in enumerate(loop['coedges']):
                    if coedge['nurbs'] and poles_equal(coedge['nurbs']['controlPoints'], wanted, 1e-12):
                        found.append([body_index, face_index, loop_index, coedge_index])
    return found


def coedge_at(rows, site):
    body_index, face_index, loop_index, coedge_index = site
    return rows[body_index]['faces'][face_index]['loops'][loop_index]['coedges'][coedge_index]


def count_matches(rows, kind, wanted, any_direction=False):
    total = 0
    for row in rows:
        if kind == 'face_poles':
            for face in row['faces']:
                total += bool(face['nurbs'] and poles_equal(face['nurbs']['controlPointsCm'], wanted, 1e-12))
        elif kind == 'edge_poles':
            for edge in row['edges']:
                total += bool(edge['nurbs'] and poles_equal(edge['nurbs']['controlPointsCm'], wanted, 1e-9, True))
        elif kind == 'coedge_poles':
            for face in row['faces']:
                for loop in face['loops']:
                    for coedge in loop['coedges']:
                        total += bool(coedge['nurbs'] and poles_equal(coedge['nurbs']['controlPoints'], wanted, 1e-12, any_direction))
        elif kind == 'edge_tolerance':
            total += sum(1 for edge in row['edges'] if edge['tolerant'] and edge['tolerance'] == wanted)
    return total


def find_vertex(rows, point):
    for row in rows:
        for vertex in row['vertices']:
            if distance(vertex['pointCm'], point) <= 1e-9:
                return row, vertex
    raise RuntimeError('Predicted vertex not found')


def face_with_poles(bodies, wanted):
    for body in bodies:
        for face in body.faces:
            data = surface_data(face.geometry)
            if data and poles_equal(data['controlPointsCm'], wanted, 1e-12):
                return face, data
    return None, None


def evaluate(face, samples):
    points = []
    for uv in samples:
        parameter = adsk.core.Point2D.create(*uv)
        ok_surface, on_surface = face.geometry.evaluator.getPointAtParameter(parameter)
        ok_face, on_face = face.evaluator.getPointAtParameter(parameter)
        points.append(dict(uv=uv, surfaceCm=on_surface.asArray() if ok_surface else None, faceCm=on_face.asArray() if ok_face else None))
    return points


def judge(prediction, original, mutant, original_bodies, mutant_bodies):
    kind = prediction['kind']
    sites = prediction.get('sites', 1)
    verdict = dict(kind=kind, hard=prediction.get('hard', kind not in ('observe_evaluator', 'observe_coedge_range', 'export_attribute')))
    if kind == 'coedge_pairs':
        verdict['pairs'] = [judge(dict(kind='coedge_poles', before=pair['before'], after=pair['after'], sites=pair['sites']), original, mutant, original_bodies, mutant_bodies) for pair in prediction['pairs']]
        for entry, pair in zip(verdict['pairs'], prediction['pairs']):
            entry.update(pcurve=pair['pcurve'], form=pair['form'], offsetU=pair['offsetU'])
            if not entry['reflected']:
                sites = coedge_sites(original, pair['before'])
                entry['diagnosis'] = dict(originalSites=sites, original=[coedge_at(original, site) for site in sites], mutant=[coedge_at(mutant, site) for site in sites], predicted=pair['after'])
        verdict['reflected'] = bool(verdict['pairs']) and all(entry['reflected'] for entry in verdict['pairs'])
    elif kind in ('face_poles', 'edge_poles', 'coedge_poles', 'edge_tolerance'):
        any_direction = prediction.get('anyDirection', False)
        counts = dict(originalBefore=count_matches(original, kind, prediction['before'], any_direction), originalAfter=count_matches(original, kind, prediction['after'], any_direction), mutantBefore=count_matches(mutant, kind, prediction['before'], any_direction), mutantAfter=count_matches(mutant, kind, prediction['after'], any_direction))
        verdict['counts'] = counts
        verdict['sites'] = sites
        verdict['reflected'] = counts['originalBefore'] >= sites and counts['mutantAfter'] == counts['originalAfter'] + sites and counts['mutantBefore'] == counts['originalBefore'] - sites
    elif kind == 'vertex_tolerance':
        _, before = find_vertex(original, prediction['pointCm'])
        _, after = find_vertex(mutant, prediction['pointCm'])
        verdict.update(original=before['tolerance'], mutant=after['tolerance'], expectedOriginal=prediction['before'], expectedMutant=prediction['after'])
        verdict['reflected'] = before['tolerance'] == prediction['before'] and after['tolerance'] == prediction['after']
    elif kind == 'vertex_edges':
        row_before, before = find_vertex(original, prediction['pointCm'])
        row_after, after = find_vertex(mutant, prediction['pointCm'])
        verdict.update(originalEdges=len(before['edges']), mutantEdges=len(after['edges']), originalLengthsCm=sorted(row_before['edges'][index]['lengthCm'] for index in before['edges']), mutantLengthsCm=sorted(row_after['edges'][index]['lengthCm'] for index in after['edges']))
        verdict['reflected'] = len(after['edges']) == len(before['edges']) - 1
    elif kind == 'observe_evaluator':
        first, first_data = face_with_poles(original_bodies, prediction['before'])
        second, second_data = face_with_poles(mutant_bodies, prediction['before'])
        verdict['getDataUnchanged'] = second is not None
        if first is not None and second is not None:
            left, right = evaluate(first, prediction['samples']), evaluate(second, prediction['samples'])
            verdict['original'], verdict['mutant'] = left, right
            verdict['maxSurfaceShiftCm'] = max(distance(a['surfaceCm'], b['surfaceCm']) for a, b in zip(left, right))
            verdict['maxFaceShiftCm'] = max(distance(a['faceCm'], b['faceCm']) for a, b in zip(left, right))
            verdict['reflected'] = verdict['maxSurfaceShiftCm'] > 1e-9
        else:
            verdict['reflected'] = None
    elif kind == 'observe_coedge_range':
        def ranges(rows):
            found = []
            for row in rows:
                for face in row['faces']:
                    for loop in face['loops']:
                        for coedge in loop['coedges']:
                            if coedge['nurbs'] and prediction['pcurve'] and poles_equal(coedge['nurbs']['controlPoints'], prediction['pcurve'], 1e-12, True):
                                found.append(dict(range=coedge['range'], knots=coedge['nurbs']['knots'], edge=row['edges'][coedge['edge']]['range']))
            return found
        verdict['original'], verdict['mutant'] = ranges(original), ranges(mutant)
        verdict['reflected'] = verdict['original'] != verdict['mutant'] if verdict['original'] else None
    elif kind == 'export_attribute':
        verdict['reflected'] = None
    return verdict


def export_bodies(bodies, name):
    exported.mkdir(parents=True, exist_ok=True)
    target = vendor / (name + '.smb')
    if not adsk.fusion.TemporaryBRepManager.get().exportToFile(list(bodies), str(target)):
        raise RuntimeError('TemporaryBRepManager export failed')
    final = exported / (name + '.smb')
    shutil.copyfile(target, final)
    return dict(path=str(final.relative_to(root)), sha256=digest(final), bytes=final.stat().st_size)


def roundtrip(bodies, label, check):
    design = persist(bodies)
    persisted = [readback(body) for body in design.rootComponent.bRepBodies]
    design, sha = save_reopen(design, label)
    reopened = [readback(body) for body in design.rootComponent.bRepBodies]
    same([row['summary'] for row in persisted], [row['summary'] for row in reopened], 'reopened')
    outcome = dict(saved_sha256=sha, persisted=[row['summary'] for row in persisted], reopenedEqual=True)
    if check is not None:
        outcome['persistedVerdict'] = check(persisted)
        outcome['reopenedVerdict'] = check(reopened)
    close_document()
    return outcome


originals = {}


def accept_subtypes(prepared):
    by_label = {item['label']: item for item in prepared['subtypes']}
    for label in selection['subtypes']:
        item = by_label[label]
        if not item['native']:
            raise RuntimeError(item['label'] + ' is not a native case')
        result = dict(label=item['label'], covers=item['covers'], source=item['source'], member=item['member'], original_sha256=item['originalSha256'], mutant_sha256=item['mutantSha256'], editedType=item['editedType'], detail=item['detail'])
        report['subtypes'].append(result)
        try:
            for key, sha in (('original', item['originalSha256']), ('mutant', item['mutantSha256'])):
                if digest(root / item[key]) != sha:
                    raise RuntimeError(key + ' digest changed')
            stage(result, 'import original')
            original_bodies = import_temporary(root / item['original'])
            stage(result, 'import mutant')
            mutant_bodies = import_temporary(root / item['mutant'])
            stage(result, 'read back original')
            original = [readback(body) for body in original_bodies]
            stage(result, 'read back mutant')
            mutant = [readback(body) for body in mutant_bodies]
            result['original'] = [row['summary'] for row in original]
            result['mutant'] = [row['summary'] for row in mutant]
            stage(result, 'judge')
            result['verdict'] = judge(item['prediction'], original, mutant, original_bodies, mutant_bodies)
            if item['prediction']['kind'] == 'export_attribute':
                stage(result, 'export')
                result['exported'] = dict(original=export_bodies(original_bodies, item['label'] + 'Original'), mutant=export_bodies(mutant_bodies, item['label'] + 'Mutant'))
            if item['originalSha256'] not in originals:
                stage(result, 'persist, save and reopen original')
                originals[item['originalSha256']] = roundtrip(original_bodies, item['label'] + 'Original', None)
            result['originalRoundtrip'] = originals[item['originalSha256']]
            kind = item['prediction']['kind']
            check = None
            if kind in ('face_poles', 'edge_poles', 'coedge_poles', 'edge_tolerance'):
                check = lambda rows, item=item, kind=kind: dict(after=count_matches(rows, kind, item['prediction']['after'], item['prediction'].get('anyDirection', False)), before=count_matches(rows, kind, item['prediction']['before'], item['prediction'].get('anyDirection', False)))
            elif kind == 'vertex_tolerance':
                check = lambda rows, item=item: find_vertex(rows, item['prediction']['pointCm'])[1]['tolerance']
            elif kind == 'vertex_edges':
                check = lambda rows, item=item: len(find_vertex(rows, item['prediction']['pointCm'])[1]['edges'])
            elif kind == 'coedge_pairs':
                check = lambda rows, item=item: [dict(pcurve=pair['pcurve'], after=count_matches(rows, 'coedge_poles', pair['after']), before=count_matches(rows, 'coedge_poles', pair['before'])) for pair in item['prediction']['pairs']]
            stage(result, 'persist, save and reopen mutant')
            result['mutantRoundtrip'] = roundtrip(mutant_bodies, item['label'] + 'Mutant', check)
            valid = all(row['valid'] for row in result['original'] + result['mutant'])
            result['allValid'] = valid
            hard = result['verdict']['hard']
            if hard and not result['verdict']['reflected']:
                report['failures'].append(item['label'] + ': prediction not reflected')
            result['status'] = 'reflected' if result['verdict']['reflected'] else ('observed' if not hard else 'not reflected')
            result['stage'] = 'done'
        except Exception:
            result['status'] = 'error'
            result['traceback'] = private(traceback.format_exc())
            report['failures'].append(item['label'] + ': error')
            close_document()
        checkpoint()


def match_surface(face, expected):
    data = surface_data(face.geometry)
    best = None
    for candidate in expected:
        if (candidate['countU'], candidate['countV']) != (data['countU'], data['countV']):
            continue
        drift = max(distance(a, b) for a, b in zip(candidate['controlPointsCm'], data['controlPointsCm']))
        if best is None or drift < best[0]:
            best = (drift, candidate)
    entry = dict(fusion=dict(degreeU=data['degreeU'], degreeV=data['degreeV'], countU=data['countU'], countV=data['countV'], knotsU=data['knotsU'], knotsV=data['knotsV'], propertiesU=data['propertiesU'], propertiesV=data['propertiesV'], weights=len(data['weights'])))
    if best is None and len(expected) == 1:
        entry['fusion']['controlPointsCm'] = data['controlPointsCm']
        entry['fusion']['weightValues'] = data['weights']
        best = (None, expected[0])
    if best is None:
        entry['matched'] = False
        return entry
    drift, candidate = best
    entry.update(matched=drift is not None and drift <= 1e-9, label=candidate['label'], poleDriftCm=drift)
    if len(candidate['knotsU']) == len(data['knotsU']) and len(candidate['knotsV']) == len(data['knotsV']):
        entry['knotDrift'] = max(abs(a - b) for a, b in zip(candidate['knotsU'] + candidate['knotsV'], data['knotsU'] + data['knotsV']))
    if candidate['weights'] and len(candidate['weights']) == len(data['weights']):
        entry['weightDrift'] = max(abs(a - b) for a, b in zip(candidate['weights'], data['weights']))
    samples = []
    for sample in candidate['samples']:
        parameter = adsk.core.Point2D.create(*sample['uv'])
        ok_surface, on_surface = face.geometry.evaluator.getPointAtParameter(parameter)
        ok_face, on_face = face.evaluator.getPointAtParameter(parameter)
        inside = face.evaluator.isParameterOnFace(parameter)
        samples.append(dict(uv=sample['uv'], surfaceDriftCm=distance(on_surface.asArray(), sample['pointCm']) if ok_surface else None, faceDriftCm=distance(on_face.asArray(), sample['pointCm']) if ok_face else None, onFace=inside, expectedOnFace=sample.get('onFace', True)))
    entry['samples'] = samples
    drifts = [value for item in samples for value in (item['surfaceDriftCm'], item['faceDriftCm']) if value is not None]
    entry['worstSampleDriftCm'] = max(drifts) if drifts else None
    entry['membershipAsExpected'] = all(item['onFace'] == item['expectedOnFace'] for item in samples)
    return entry


def match_coedges(body, expected):
    found = []
    for face in body.faces:
        for loop in face.loops:
            for coedge in loop.coEdges:
                data = curve2_data(coedge.geometry) if coedge.geometry else None
                if data:
                    found.append(data['controlPoints'])
    matched = [any(poles_equal(points, item['controlPoints'], 1e-9) for points in found) for item in expected]
    return dict(expected=len(expected), matched=sum(matched), unmatched=[item for item, ok in zip(expected, matched) if not ok], fusion=found)


def check_authored(body, expected):
    info = readback(body)
    props = physical(body)
    checks = dict(summary=info['summary'], physical=props)
    problems = []
    shape = (info['summary']['solid'], info['summary']['faces'], info['summary']['edges'], info['summary']['vertices'])
    if shape != (expected['solid'], expected['faces'], expected['edges'], expected['vertices']):
        problems.append('topology counts ' + str(shape))
    if info['summary']['surfaceTypes'] != expected['faceTypes']:
        problems.append('face types ' + str(info['summary']['surfaceTypes']))
    if not info['summary']['valid'] or not all(face['valid'] for face in info['faces']):
        problems.append('invalid body or face')
    checks['areaRelativeError'] = abs(props['areaCm2'] - expected['areaCm2']) / expected['areaCm2']
    if checks['areaRelativeError'] > 1e-5:
        problems.append('area')
    if expected['solid']:
        checks['volumeRelativeError'] = abs(props['volumeCm3'] - expected['volumeCm3']) / expected['volumeCm3']
        checks['centerDriftCm'] = distance(props['centerCm'], expected['centerCm']) if props['centerCm'] else None
        if checks['volumeRelativeError'] > 1e-5 or checks['centerDriftCm'] is None or checks['centerDriftCm'] > 1e-5:
            problems.append('volume or centroid')
    surfaces = [match_surface(face, expected['surfaces']) for face in body.faces if face.geometry.objectType == NURBS]
    checks['surfaces'] = surfaces
    for entry in surfaces:
        if 'samples' not in entry:
            problems.append('NURBS face without an expected surface')
            continue
        if entry['worstSampleDriftCm'] is None or entry['worstSampleDriftCm'] > 1e-7:
            problems.append('surface evaluation')
        if not entry['membershipAsExpected']:
            problems.append('face membership')
    checks['coedges'] = match_coedges(body, expected['coedges'])
    vertex_drift = max(min(distance(vertex['pointCm'], point) for point in expected['verticesCm']) for vertex in info['vertices'])
    checks['vertexDriftCm'] = vertex_drift
    if vertex_drift > 1e-9:
        problems.append('vertices')
    checks['problems'] = problems
    return checks


def accept_authored(prepared):
    for item in prepared['authored']:
        if item['label'] not in selection['authored']:
            continue
        result = dict(label=item['label'], scope=item['scope'], source_sha256=item['targetSha256'], history_sha256=item['historySha256'])
        report['authored'].append(result)
        try:
            path = root / item['target']
            if digest(path) != item['targetSha256']:
                raise RuntimeError('Authored geometry digest changed')
            stage(result, 'import')
            bodies = import_temporary(path)
            if len(bodies) != 1:
                raise RuntimeError('Authored SMB must hold exactly one body')
            result['temporary'] = summary(bodies[0])
            stage(result, 'persist and check')
            design = persist(bodies)
            result['persisted'] = check_authored(design.rootComponent.bRepBodies.item(0), item['expected'])
            stage(result, 'save and reopen')
            design, result['saved_sha256'] = save_reopen(design, item['label'])
            stage(result, 'check reopened')
            result['reopened'] = check_authored(design.rootComponent.bRepBodies.item(0), item['expected'])
            same(result['persisted']['summary'], result['reopened']['summary'], 'reopened')
            close_document()
            problems = result['persisted']['problems'] + result['reopened']['problems']
            result['status'] = 'accepted' if not problems else 'failed'
            result['stage'] = 'done'
            if problems:
                report['failures'].append(item['label'] + ': ' + ', '.join(sorted(set(problems))))
        except Exception:
            result['status'] = 'error'
            result['traceback'] = private(traceback.format_exc())
            report['failures'].append(item['label'] + ': error')
            close_document()
        checkpoint()


try:
    prepared = json.loads((folder / 'Preparation.json').read_text())
    accept_authored(prepared)
    accept_subtypes(prepared)
    covered = [entry['label'] for entry in report['authored'] + report['subtypes']]
    if sorted(covered) != sorted(selection['authored'] + selection['subtypes']):
        report['failures'].append('selection not fully covered: ' + str(covered))
    report['status'] = 'accepted' if not report['failures'] else 'failed'
except Exception:
    report['status'] = 'failed'
    report['traceback'] = private(traceback.format_exc())
finally:
    close_document()
    shutil.rmtree(vendor, ignore_errors=True)
    report['documents_after'] = app.documents.count
    checkpoint()
