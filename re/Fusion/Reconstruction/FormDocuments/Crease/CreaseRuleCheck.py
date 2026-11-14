"""Research: test the crease rule in ClassifyEdges against Fusion's own bodies.

Part one reads every Fusion-saved Form archive (the crease probe saves under
LocalOracle/FormDocuments/Crease/tmp and every other Fusion-saved Form archive
found under re/Fusion) and decodes the converted body Fusion stored. Edges
that share one curve are pieces of one crease. For each such curve the rule
predicts the pieces and labels from the geometry alone (CurvePieces over the
whole curve range); the row records whether the prediction equals Fusion's
pieces and labels.

Part two repeats the old CreaseCheck comparison for archives whose cage the general
rules convert: the Kit body built from the cage alone by CageBody (ShapeBody, then
ClassifyEdges and CheckFolds), against the converted topology Fusion stored.

Writes CreaseRuleCheck.json.
"""

import hashlib
import json
import sys
from collections import Counter
from functools import partial
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[4]
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(BASE.parent / 'Cages'))
from convert.formats.Fusion.BrepCodec.Journal.Spline.Stencil import ClassifyEdges as Rule
from convert.formats.Fusion.BrepCodec.Journal.Spline.Stencil.CageBody import CageBody, ShapeBody
from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from ReadConverted import ReadConverted

TARGET = BASE / 'CreaseRuleCheck.json'
KIT_WRITTEN = ('FormDocuments/StencilAccept/Cases/', 'FormDocuments/Acceptance/Reemitted', 'FormDocuments/Sourceless/Variants/', 'FormDocuments/Cache/BoxSurf', 'FormDocuments/Cache/PlaneSurf')
KIT_FOLDERS = ('FormDocuments/CageDocuments/', 'FormDocuments/Sourceless/')


def kit_written(relative):
    if any(folder in relative for folder in KIT_FOLDERS) and not any(folder in relative for folder in ('/Saved/', '/Loaded/')):
        return True
    if '/Saved/Kit' in relative or '/Loaded/Kit' in relative:
        return True
    return any(part in relative for part in KIT_WRITTEN)


def native_pieces(body, members):
    return [[round(value, 9) for value in Rule.EdgeRange(body.Edges[index])] + [body.Edges[index].Convexity] for index in members]


def predict(body, sides, members):
    curve = body.Edges[members[0]].Curve
    lower = Rule.EdgeRange(body.Edges[members[0]])[0]
    upper = Rule.EdgeRange(body.Edges[members[-1]])[1]
    measure = partial(Rule.TurnAngle, curve, sides[members[0]])
    pieces = Rule.SpanPieces(measure, Rule.EdgeSpans(curve, sides[members[0]], lower, upper), curve.Knots, Curve=curve)
    return [[round(begin, 9), round(finish, 9), label] for begin, finish, label in pieces]


def topology(body):
    uses = Counter(use.EdgeIndex for face in body.Faces for use in face.Uses)
    rows = []
    for index, edge in enumerate(body.Edges):
        bounds = None if edge.Bounds is None else tuple(round(value, 9) for value in edge.Bounds)
        rows.append((uses[index], edge.Convexity, bounds))
    return {'faces': len(body.Faces), 'edges': sorted(rows, key=repr)}


def part_one(relative, body):
    sides = Rule.EdgeSides(body)
    groups = Rule.CurveGroups(body, sides)
    rows = []
    for members in groups:
        native = native_pieces(body, members)
        try:
            predicted = predict(body, sides, members)
        except ValueError as error:
            predicted = 'error: ' + str(error)
        status = 'equal' if native == predicted else 'refused' if isinstance(predicted, str) else 'different'
        if status != 'equal' or any(piece[2] != 'tangent' for piece in native) or len(members) > 1:
            rows.append({'edges': members, 'native': native, 'predicted': predicted, 'status': status})
    statuses = Counter(row['status'] for row in rows)
    return {'file': relative, 'groups': len(groups), 'equal': len(groups) - statuses['refused'] - statuses['different'], 'refused': statuses['refused'], 'different': statuses['different'], 'crease_groups': rows}


def part_two(relative, model, native):
    surface = model.Forms[0].Surface
    try:
        shaped = ShapeBody(surface)
    except ValueError:
        return None
    try:
        built = CageBody(surface)
        verdict = 'accepted'
    except ValueError as error:
        built = shaped
        verdict = 'refused: ' + str(error)
    same = topology(built) == topology(native)
    return {'file': relative, 'status': ('accept' if verdict == 'accepted' else 'refuse') + ('_equal' if same else '_different'), 'shape_topology_equal': topology(shaped) == topology(native), 'native_topology': None if same else topology(native), 'kit_topology': None if same else topology(built)}


def main():
    report = {'scope': 'Crease rule of ClassifyEdges against converted bodies saved by Fusion 2706.1.17: a piece is tangent iff its dihedral stays within 1 degree; pieces break at interior curve knots where the faces meet flat, unless both sides are tangent, and at an exact sign change of the dihedral away from a knot when both sides pass 1 degree; the rule refuses (status refused) a flat knot where the dihedral changes sign between a tangent and an unknown side; a lone sign change away from a knot with both sides unknown and the root not turned is cut by the run rule of CreaseSplitNotes.md (at the root, or at a cage knot of the tangent run around it), and is refused when the run, the slope unit or the lean is undecided', 'turn_rate_rad_per_unit': Rule.KTurnRate, 'end_halves': list(Rule.KEndHalves), 'python': sys.version.split()[0], 'tangent_limit_deg': 1.0, 'flat_turn_rad': Rule.KFlatTurn, 'peak_steps': Rule.KPeakSteps, 'samples_per_span': Rule.KCreaseSamples, 'part_one_totals': Counter(), 'part_two_totals': Counter(), 'part_one': [], 'part_two': []}
    seen = set()
    paths = sorted({path for pattern in ('re/Fusion/LocalOracle/FormDocuments/**/*.f3d', 're/Fusion/LocalOracle/TSplineCodec/**/*.f3d', 're/Fusion/LocalOracle/TSpline/**/*.f3d') for path in ROOT.glob(pattern) if path.is_file()})
    for path in paths:
        relative = str(path.relative_to(ROOT))
        if kit_written(relative) or '/External/' in relative:
            continue
        data = path.read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        if digest in seen:
            continue
        seen.add(digest)
        try:
            model = ReadDocument(data)
            if len(model.Forms) != 1:
                continue
            body = ReadConverted(model)
        except Exception as error:
            if 'Form' in relative or 'TSpline' in relative:
                report['part_one_totals']['unreadable'] += 1
            continue
        first = part_one(relative, body)
        first['sha256'] = digest
        report['part_one_totals']['groups'] += first['groups']
        report['part_one_totals']['groups_equal'] += first['equal']
        report['part_one_totals']['groups_refused'] += first['refused']
        report['part_one_totals']['groups_different'] += first['different']
        report['part_one_totals']['archives'] += 1
        if first['crease_groups']:
            report['part_one'].append(first)
        try:
            second = part_two(relative, model, body)
        except Exception as error:
            second = {'file': relative, 'status': 'shape_error', 'error': type(error).__name__ + ': ' + str(error)[:120]}
        if second is not None:
            second['sha256'] = digest
            report['part_two_totals'][second['status']] += 1
            report['part_two'].append(second)
    report['part_one_totals'] = dict(sorted(report['part_one_totals'].items()))
    report['part_two_totals'] = dict(sorted(report['part_two_totals'].items()))
    TARGET.write_text(json.dumps(report, indent=1) + '\n')
    print('part one', json.dumps(report['part_one_totals']))
    print('part two', json.dumps(report['part_two_totals']))
    for row in report['part_one']:
        for group in row['crease_groups']:
            if group['status'] != 'equal':
                print(group['status'].upper(), row['file'].replace('re/Fusion/LocalOracle/', ''), group['native'], group['predicted'])
    for row in report['part_two']:
        if row['status'] != 'accept_equal':
            print(row['status'], row['file'].replace('re/Fusion/LocalOracle/', ''), row.get('error', ''))


if __name__ == '__main__':
    main()
