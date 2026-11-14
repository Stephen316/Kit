"""Research: record the crease rule's prediction for a probe round before Fusion runs it.

For every TSM of the round, builds the Kit shape body when the layout has
one, and records the pieces and labels that ClassifyEdges.CurvePieces
predicts on each curve shared by two faces, plus whether CageBody accepts
the cage. Writes <Round>Prediction.json next to this script.
"""

import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[4]
sys.path.insert(0, str(ROOT / 'src'))
from convert.formats.Fusion.BrepCodec.Journal.Spline.Stencil import ClassifyEdges as Rule
from convert.formats.Fusion.BrepCodec.Journal.Spline.Stencil.CageBody import CageBody, ShapeBody
from convert.formats.Fusion.TSplineCodec.ReadTspline import ReadTspline

ORACLE = ROOT / 're/Fusion/LocalOracle/FormDocuments/Crease'


def main():
    name = sys.argv[1]
    preparation = json.loads((ORACLE / name / 'Preparation.json').read_text())
    rows = []
    for cage in preparation['cages']:
        surface = ReadTspline((ROOT / cage['tsm_file']).read_bytes())
        body = ShapeBody(surface)
        sides = Rule.EdgeSides(body)
        groups = []
        for members in Rule.CurveGroups(body, sides):
            lower = Rule.EdgeRange(body.Edges[members[0]])[0]
            upper = Rule.EdgeRange(body.Edges[members[-1]])[1]
            pieces = Rule.CurvePieces(body.Edges[members[0]].Curve, sides[members[0]], lower, upper)
            shape = [list(Rule.EdgeRange(body.Edges[index])) for index in members]
            if len(pieces) > 1 or len(members) > 1 or pieces[0][2] != 'tangent':
                groups.append({'shape_edges': members, 'shape_ranges': shape, 'predicted_pieces': [list(piece) for piece in pieces]})
        try:
            CageBody(surface)
            verdict = 'accepted'
        except ValueError as error:
            verdict = 'refused: ' + str(error)
        rows.append({'cage': cage['cage'], 'cage_body': verdict, 'crease_groups': groups})
    report = {'scope': 'Crease rule prediction for probe round ' + name + ', recorded before the Fusion run', 'python': sys.version.split()[0], 'cages': rows}
    (BASE / (name + 'Prediction.json')).write_text(json.dumps(report, indent=1) + '\n')
    print(json.dumps(rows, indent=1))


if __name__ == '__main__':
    main()
