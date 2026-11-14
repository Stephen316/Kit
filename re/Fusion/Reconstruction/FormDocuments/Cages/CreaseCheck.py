"""Research: does the crease edge classifier ever accept a wrong topology.

For every Fusion-saved archive whose cage layout has a body shape, builds the
Kit body from the cage alone, runs ClassifyEdges on it and compares the edge
topology (edge count, coedge count, convexity and split bounds) with the
converted body that Fusion stored. A false accept is a checked body whose
topology differs from Fusion's. A false refusal is a refused body whose
topology matches. The probe folders under Stencil/tmp are ignored by git, so
each row records the SHA-256 of the archive it read.
"""

import hashlib
import json
import math
import sys
from collections import Counter
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[4]
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(ROOT / 're/Fusion/Reconstruction/FormDocuments/Tables'))
sys.path.insert(0, str(BASE))
from convert.formats.Fusion.BrepCodec.Journal.Spline.Stencil import ClassifyEdges as Rule
from convert.formats.Fusion.BrepCodec.Journal.Spline.Stencil.CageBody import ShapeBody
from convert.formats.Fusion.BrepCodec.Journal.Spline.Stencil.ConvertCage import ConvertCage
from ReadShapes import ReadShapes
from StencilKey import StencilKey
from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from ReadConverted import ReadConverted

TARGET = BASE / 'CreaseCheck.json'
KIT_WRITTEN = ('FormDocuments/StencilAccept/Cases/', 'FormDocuments/Acceptance/Reemitted', 'FormDocuments/Sourceless/Variants/')
KIT_FOLDERS = ('FormDocuments/CageDocuments/', 'FormDocuments/Sourceless/')


def kit_written(relative):
    if any(folder in relative for folder in KIT_FOLDERS) and not any(folder in relative for folder in ('/Saved/', '/Loaded/')):
        return True
    return any(part in relative for part in KIT_WRITTEN)


def topology(body):
    uses = Counter(use.EdgeIndex for face in body.Faces for use in face.Uses)
    rows = []
    for index, edge in enumerate(body.Edges):
        bounds = None if edge.Bounds is None else tuple(round(value, 9) for value in edge.Bounds)
        rows.append((uses[index], edge.Convexity, bounds))
    return {'faces': len(body.Faces), 'edges': sorted(rows, key=repr)}


def angles(body):
    rows = []
    for index, sides in sorted(Rule.EdgeSides(body).items()):
        if len(sides) != 2:
            continue
        edge = body.Edges[index]
        signed = Rule.EdgeSines(edge, sides)
        degrees = [math.degrees(math.asin(min(1.0, abs(value)))) for value in signed]
        rows.append({'edge': index, 'shape_convexity': edge.Convexity, 'bounds': edge.Bounds, 'max_deg': max(degrees), 'min_deg': min(degrees), 'signs': sorted({value > 0.0 for value in signed})})
    return [row for row in rows if row['shape_convexity'] != 'tangent' or row['max_deg'] > 1e-6]


def study(relative, data):
    model = ReadDocument(data)
    if len(model.Forms) != 1:
        return None
    surface = model.Forms[0].Surface
    shape = ReadShapes().get(StencilKey(surface))
    if shape is None:
        return None
    shaped = ShapeBody(surface)
    try:
        native = ReadConverted(model)
    except Exception as error:
        return {'file': relative, 'shape': shape.Label, 'status': 'no native body', 'error': type(error).__name__}
    try:
        built = Rule.ClassifyEdges(shaped)
        verdict = 'accepted'
    except ValueError as error:
        built = shaped
        verdict = 'refused: ' + str(error)
    same = topology(built) == topology(native)
    outcome = ('accept' if verdict == 'accepted' else 'refuse') + ('_equal' if same else '_different')
    changed = sum(left.Convexity != right.Convexity for left, right in zip(shaped.Edges, built.Edges))
    return {'file': relative, 'shape': shape.Label, 'status': outcome, 'verdict': verdict, 'reclassified_edges': changed, 'shape_topology_equal': topology(shaped) == topology(native), 'native_topology': topology(native) if not same else None, 'kit_topology': topology(built) if not same else None, 'crease_angles': angles(shaped)}


def main():
    report = {'scope': 'Crease edge classification of Kit cage bodies against the converted topology of every Fusion-saved archive of a body-shape layout, including the ignored probe folders', 'python': sys.version.split()[0], 'tangent_limit_deg': 0.65, 'crease_minimum_deg': 1.15, 'flat_sine': Rule.KFlatSine, 'samples_per_span': Rule.KCreaseSamples, 'totals': Counter(), 'archives': []}
    seen = set()
    for path in sorted(ROOT.glob('re/Fusion/**/*.f3d')):
        relative = str(path.relative_to(ROOT))
        if kit_written(relative):
            continue
        data = path.read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        if digest in seen:
            continue
        seen.add(digest)
        try:
            row = study(relative, data)
        except Exception as error:
            row = {'file': relative, 'status': 'unreadable', 'error': type(error).__name__ + ': ' + str(error)[:120]}
            if 'Form' not in relative and 'TSpline' not in relative:
                continue
        if row is None:
            continue
        row['sha256'] = digest
        report['totals'][row['status']] += 1
        report['archives'].append(row)
    report['totals'] = dict(sorted(report['totals'].items()))
    TARGET.write_text(json.dumps(report, indent=1) + '\n')
    print(json.dumps(report['totals']))
    for row in report['archives']:
        if row['status'] != 'accept_equal' or row.get('reclassified_edges'):
            print(row['status'], row['file'].replace('re/Fusion/LocalOracle/', ''), row.get('verdict', row.get('error')), [(a['edge'], a['shape_convexity'], round(a['max_deg'], 4), round(a['min_deg'], 6), a['signs']) for a in row.get('crease_angles', [])])


if __name__ == '__main__':
    main()
