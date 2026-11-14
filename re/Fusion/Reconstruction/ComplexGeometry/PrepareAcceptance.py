"""Prepare native acceptance inputs for complex ASM geometry.

Run with /opt/homebrew/bin/python3.14 -I (ZIP method 93 needs Python 3.14).
"""
import argparse
import dataclasses
import hashlib
import json
import sys
import zipfile
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(HERE))

from convert.formats.Fusion.BrepCodec.Journal.Complex.Authoring.CreateNurbsBody import CreateNurbsBody  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.Complex.Authoring.ExactSubtypes import ExactSurface, SplineCurve, SplineSurface  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.Complex.Authoring.SplineEval import PointOnSurface  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.Spline.SplineNode import SplineNode  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.EmitJournal import EmitJournal  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.EmitStateSmb import EmitStateSmb  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.ReadJournal import ReadJournal  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.Snapshot.EmitGeometry import EmitGeometry  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.Snapshot.ReadGeometry import ReadGeometry  # noqa: E402
from convert.formats.Fusion.BrepCodec.Models.HistoryState import HistoryState  # noqa: E402
from convert.formats.Fusion.GeometryCodec.GeometryStamp import GeometryStamp  # noqa: E402

from AuthoredModels import authored_models  # noqa: E402
import NurbsMath  # noqa: E402

OUT = ROOT / 're/Fusion/LocalOracle/ComplexGeometry'
HISTORY = HistoryState(7, 2, 7, 1, 2, 7)
STAMP = GeometryStamp('Kit independent NURBS author', 'ASM 232.5.0.65535 OSX', 'Thu Nov 12 00:00:00 2026')
STUDY = 're/Fusion/Study/'
GEOMETRY = (
    ('SplinePatches', 'splinepatches-ac5e846e59c0/splinepatches.f3d', 'exact_spl_sur, exp_par_cur'),
    ('LoftDirection', 'lofts-838ea6e83e97/both_direction.f3d', 'loft_spl_sur'),
    ('SweepRail', 'sweepoperations-62378e7c0294/rail_flip_false.f3d', 'sweep_sur'),
    ('SolidSweep', 'solidsweeps-7d2677669e3d/solid_aligned.f3d', 'sweep_sur, exact_spl_sur'),
    ('ChordFillet', 'edgemodes-87edbf67527b/fillet_chord.f3d', 'srf_srf_v_bl_spl_sur'),
    ('CurvatureFillet', 'edgemodes-52695761f185/fillet_curvature.f3d', 'g2_blend_spl_sur'),
    ('RuleFillet', 'specialfillets-d50f7a4f04e0/rule_asymmetric.f3d', 'VBL_SURF'),
    ('VariableFillet', 'variablefillets-a5080b076434/one_quarter.f3d', 'srf_srf_v_bl_spl_sur'),
)
HISTORIES = (
    ('LoftDirection', 'd1', 1.25),
    ('SweepRail', 'd2', 0.8),
    ('SolidSweep', 'd5', 0.8),
    ('ChordFillet', 'd4', 1.25),
    ('CurvatureFillet', 'd4', 1.25),
    ('RuleFillet', 'd7', 1.5),
)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def research_surface(value):
    return NurbsMath.Surface(value.UDegree, value.VDegree, value.UKnots, value.UMultiplicity, value.VKnots, value.VMultiplicity, list(value.Poles), list(value.Weights))


def describe_surface(value, label):
    surface = research_surface(value)
    poles, weights = NurbsMath.fusion_order(surface)
    ulow, uhigh, vlow, vhigh = surface.domain
    grid = [(ulow + (uhigh - ulow) * a, vlow + (vhigh - vlow) * b) for a in (0.13, 0.5, 0.87) for b in (0.21, 0.5, 0.79)]
    samples = []
    for u, v in grid:
        expected = surface.point(u, v)
        production = PointOnSurface(value, u, v)
        drift = max(abs(first - second) for first, second in zip(expected, production))
        if drift > 1e-12:
            raise RuntimeError(f'Production and research evaluators disagree by {drift}')
        samples.append(dict(uv=[u, v], pointCm=expected))
    return dict(label=label, degreeU=value.UDegree, degreeV=value.VDegree, countU=surface.ucount, countV=surface.vcount, knotsU=surface.uvec, knotsV=surface.vvec, rational=value.Rational, controlPointsCm=[list(point) for point in poles], weights=list(weights) if value.Rational else [], samples=samples)


def describe_curve(value):
    vector = NurbsMath.full_knots(value.Knots, value.Multiplicity, value.Degree)
    return dict(degree=value.Degree, knots=vector, rational=value.Rational, controlPointsCm=[list(point) for point in value.Poles], weights=list(value.Weights))


def expected_body(model):
    surfaces = [face.Surface for face in model.Faces]
    research = [research_surface(value) for value in surfaces]
    totals = [NurbsMath.integrate(surface) for surface in research]
    closed = all(count == 2 for count in __import__('collections').Counter(use.EdgeIndex for face in model.Faces for use in face.Uses).values())
    boxes = [NurbsMath.sample_bounds(surface) for surface in research]
    bounds = [[min(box[0][axis] for box in boxes) for axis in range(3)], [max(box[1][axis] for box in boxes) for axis in range(3)]]
    hull = [[min(point[axis] for value in surfaces for point in value.Poles) for axis in range(3)], [max(point[axis] for value in surfaces for point in value.Poles) for axis in range(3)]]
    volume = sum(total['volume'] for total in totals)
    result = dict(solid=closed, faces=len(model.Faces), edges=len(model.Edges), vertices=len(model.PointsCm), areaCm2=sum(total['area'] for total in totals), sampledBoundsCm=bounds, controlHullCm=hull)
    if closed:
        result['volumeCm3'] = volume
        result['centerCm'] = [sum(total['moment'][axis] for total in totals) / volume for axis in range(3)]
    result['surfaces'] = [describe_surface(value, f'face{index}') for index, value in enumerate(surfaces)]
    result['curves'] = [describe_curve(edge.Curve) for edge in model.Edges]
    result['verticesCm'] = [list(point) for point in model.PointsCm]
    return result


def prepare_authored(report):
    for label, model, scope in authored_models():
        journal = CreateNurbsBody(model, HISTORY, STAMP)
        history = EmitJournal(journal)
        if ReadJournal(history) != journal:
            raise RuntimeError('Authored journal does not reread to the same typed model')
        payload = EmitStateSmb(journal)
        state = ReadGeometry(payload)
        if state.Entities != journal.Entities or EmitGeometry(state) != payload:
            raise RuntimeError('Authored state does not reread to the same typed model')
        target = OUT / (label + '.smb')
        target.write_bytes(payload)
        (OUT / (label + '.smbh')).write_bytes(history)
        report['authored'].append(dict(label=label, scope=scope, target=str(target.relative_to(ROOT)), targetSha256=digest(payload), history=str((OUT / (label + '.smbh')).relative_to(ROOT)), historySha256=digest(history), records=len(journal.Entities), expected=expected_body(model)))
        print(label, digest(payload), flush=True)


def read_member(path, suffix):
    with zipfile.ZipFile(path) as archive:
        names = [name for name in archive.namelist() if name.endswith(suffix)]
        if len(names) != 1:
            raise RuntimeError(f'Expected one {suffix} member in {path}')
        return names[0], archive.read(names[0])


def prepare_geometry(report):
    for label, relative, families in GEOMETRY:
        source = ROOT / STUDY / relative
        member, original = read_member(source, '.smb')
        model = ReadGeometry(original)
        payload = EmitGeometry(model)
        if payload != original:
            raise RuntimeError(label + ' snapshot is not byte exact')
        target = OUT / ('Decoded' + label + '.smb')
        target.write_bytes(payload)
        report['geometry'].append(dict(label=label, families=families, source=str(source.relative_to(ROOT)), sourceSha256=digest(source.read_bytes()), member=member, memberSha256=digest(original), target=str(target.relative_to(ROOT)), targetSha256=digest(payload), byteExact=True, records=len(model.Entities)))
        print('Decoded' + label, digest(payload), flush=True)


def prepare_edited(report):
    source = ROOT / STUDY / GEOMETRY[0][1]
    member, original = read_member(source, '.smb')
    model = ReadGeometry(original)
    index = next(index for index, value in enumerate(model.Entities) if isinstance(value, SplineNode) and not SplineSurface(value.Surface).Rational)
    surface = SplineSurface(model.Entities[index].Surface)
    poles = list(surface.Poles)
    poles[4] = (poles[4][0], poles[4][1], 2.0)
    edited = dataclasses.replace(surface, Poles=tuple(poles))
    entities = list(model.Entities)
    entities[index] = dataclasses.replace(entities[index], Surface=ExactSurface(edited))
    payload = EmitGeometry(dataclasses.replace(model, Entities=tuple(entities)))
    if ReadGeometry(payload).Entities != tuple(entities):
        raise RuntimeError('Edited snapshot does not reread to the edited typed model')
    truth = json.loads((source.parent / 'ground_truth.json').read_text())
    target = OUT / 'EditedPatch.smb'
    target.write_bytes(payload)
    others = [SplineSurface(value.Surface) for position, value in enumerate(model.Entities) if isinstance(value, SplineNode) and position != index]
    expected = [describe_surface(edited, 'edited')] + [describe_surface(value, 'unchanged') for value in others]
    case = next(item for item in truth['cases'] if item['name'] == 'PolynomialPatch')
    grid = case['input_surface']['evaluation_uv']
    research = research_surface(edited)
    expected[0]['samples'] += [dict(uv=uv, pointCm=research.point(*uv)) for uv in grid]
    original_research = research_surface(surface)
    drift = max(abs(a - b) for uv, point in zip(grid, case['input_surface']['evaluation_points_cm']) for a, b in zip(original_research.point(*uv), point))
    report['edited'].append(dict(label='EditedPatch', source=str(source.relative_to(ROOT)), sourceSha256=digest(source.read_bytes()), member=member, memberSha256=digest(original), target=str(target.relative_to(ROOT)), targetSha256=digest(payload), edit='Typed exact_spl_sur pole 4 (u=1, v=1) z 1.2 -> 2.0 cm on the polynomial patch; boundary poles and edges unchanged', groundTruthDriftCm=drift, expected=dict(surfaces=expected, faces=2, edges=8, vertices=8)))
    print('EditedPatch', digest(payload), 'ground-truth drift', drift, flush=True)


def prepare_histories(report):
    sources = {label: relative for label, relative, _ in GEOMETRY}
    for label, parameter, factor in HISTORIES:
        source = ROOT / STUDY / sources[label]
        target = OUT / (label + 'History.f3d')
        members = []
        with zipfile.ZipFile(source) as archive, zipfile.ZipFile(target, 'w') as output:
            for entry in archive.infolist():
                data = archive.read(entry)
                if entry.filename.endswith('.smbh'):
                    model = ReadJournal(data)
                    emitted = EmitJournal(model)
                    members.append(dict(member=entry.filename, kind='history', sha256=digest(data), emittedSha256=digest(emitted), records=len(model.Entities), activeRecords=model.ActiveCount, states=len(model.States), byteExact=emitted == data))
                elif entry.filename.endswith('.smb'):
                    emitted = EmitGeometry(ReadGeometry(data))
                    members.append(dict(member=entry.filename, kind='snapshot', sha256=digest(data), emittedSha256=digest(emitted), byteExact=emitted == data))
                else:
                    emitted = data
                output.writestr(entry.filename, emitted)
        if not all(item['byteExact'] for item in members):
            raise RuntimeError(label + ' history archive members are not byte exact')
        report['histories'].append(dict(label=label, source=str(source.relative_to(ROOT)), sourceSha256=digest(source.read_bytes()), target=str(target.relative_to(ROOT)), targetSha256=digest(target.read_bytes()), members=members, parameter=parameter, factor=factor, boundary='Every SMB and SMBH member replaced by typed ReadJournal/EmitJournal or ReadGeometry/EmitGeometry output; other members copied'))
        print(label + 'History', digest(target.read_bytes()), flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    report = dict(schema='FusionComplexGeometryPreparation/1', status='preparing', authored=[], geometry=[], edited=[], histories=[])
    prepare_authored(report)
    prepare_geometry(report)
    prepare_edited(report)
    prepare_histories(report)
    report['status'] = 'prepared'
    (OUT / 'Preparation.json').write_text(json.dumps(report, indent=1) + '\n')


if __name__ == '__main__':
    main()
