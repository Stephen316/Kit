"""Research check: rebuild native converted Form BReps from typed bodies.

For each native control archive, extract the typed converted body, feed it to
the production `CreateFormBrep`, and compare the produced `.smbh` journal
entities and `.smb` snapshot entities with the native ones.
Entity tags other than the body tag are normalised to -1 on the native side,
because the source-free builder writes only the body tag.
"""

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
ROOT = HERE.parents[4]

from ExtractBody import extract, face_windows, native_marks, windows_by_tag, without_tags  # noqa: E402

from convert.formats.Fusion.BrepCodec.Journal.Spline.Conversion.ConvertGrid import ConvertGrid  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.Spline.Converted.CreateFormBrep import CreateFormBrep  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.Spline.Converted.GridBody import GridBody  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.Spline.Converted.FormMarks import FormMarks  # noqa: E402

DEFAULT = (
    're/Fusion/LocalOracle/FormDocuments/Grid/Primitives/Plane1x1.f3d',
    're/Fusion/LocalOracle/FormDocuments/Grid/Primitives/Plane3x2.f3d',
    're/Fusion/LocalOracle/FormDocuments/Grid/Primitives/Plane4x4.f3d',
    're/Fusion/LocalOracle/FormDocuments/Grid/Primitives/Plane2x5.f3d',
    're/Fusion/LocalOracle/TSpline/Plane.f3d',
    're/Fusion/LocalOracle/TSpline/Box.f3d',
    're/Fusion/LocalOracle/TSpline/SymmetricBox.f3d',
    're/Fusion/LocalOracle/TSplineCodec/vendor_BoxCreasedControl.f3d',
    're/Fusion/LocalOracle/TSplineCodec/vendor_PlaneCreasedControl.f3d',
)


def compare(native, built):
    if len(native) != len(built):
        return {'equal': False, 'native_count': len(native), 'built_count': len(built)}
    diffs = [index for index, (left, right) in enumerate(zip(native, built)) if left != right]
    return {'equal': not diffs, 'count': len(native), 'first_diffs': diffs[:5]}


def spread(left, right):
    assert len(left) == len(right)
    return max((abs(a - b) for p, q in zip(left, right) for a, b in zip(p, q, strict=True)), default=0.0)


def windows(rows):
    return [(w.ULow, w.UHigh, w.VLow, w.VHigh) for w in rows]


def grid_check(cage, body):
    """Compare the GridBody adapter with the native converted body, label text aside."""
    try:
        built = GridBody(ConvertGrid(cage))
    except ValueError as error:
        return {'converted': False, 'reason': str(error)}
    deviations = [spread(built.PointsCm, body.PointsCm)]
    same = built.Regions == body.Regions and len(built.Edges) == len(body.Edges)
    for left, right in zip(built.Edges, body.Edges):
        same &= (left.StartVertex, left.EndVertex, left.Jumps, left.Convexity, left.Bounds) == (right.StartVertex, right.EndVertex, right.Jumps, right.Convexity, right.Bounds)
        same &= (left.Curve.Knots, left.Curve.Multiplicity) == (right.Curve.Knots, right.Curve.Multiplicity)
        same &= [w.Face for w in left.Windows] == [w.Face for w in right.Windows]
        deviations += [spread(left.Curve.Poles, right.Curve.Poles), spread(windows(left.Windows), windows(right.Windows))]
    for left, right in zip(built.Faces, body.Faces):
        same &= (left.Surface.Jumps, left.Surface.Region, left.DoubleSided, left.Contained) == (right.Surface.Jumps, right.Surface.Region, right.DoubleSided, right.Contained)
        same &= (left.Surface.Cache.KnotsU, left.Surface.Cache.KnotsV) == (right.Surface.Cache.KnotsU, right.Surface.Cache.KnotsV)
        deviations.append(spread(left.Surface.Cache.Points, right.Surface.Cache.Points))
        for a, b in zip(left.Uses, right.Uses, strict=True):
            same &= (a.EdgeIndex, a.Reversed, a.Pcurve.Knots) == (b.EdgeIndex, b.Reversed, b.Pcurve.Knots)
            deviations.append(spread(a.Pcurve.Poles, b.Pcurve.Poles))
    return {
        'converted': True,
        'structure_equal': bool(same),
        'max_abs_deviation': max(deviations),
        'native_labels': {'faces': [f.Label for f in body.Faces], 'edges': [e.Label for e in body.Edges]},
        'kit_labels': {'faces': [f.Label for f in built.Faces], 'edges': [e.Label for e in built.Edges]},
        'native_fits': [u.Fit for f in body.Faces for u in f.Uses],
    }


def run(relative):
    cage, body, model = extract(ROOT / relative)
    stamp, micros = native_marks(model)
    built = CreateFormBrep(cage, body, FormMarks(stamp, micros))
    history = model.Bodies[0].History
    native_history = without_tags(history.Entities[: history.ActiveCount], True)
    snapshot = model.Snapshots[0].Snapshot.Entities
    labels = windows_by_tag(model)
    derived = face_windows(body)
    return {
        'archive': relative,
        'faces': len(body.Faces),
        'edges': len(body.Edges),
        'vertices': len(body.PointsCm),
        'labels': sorted(labels, key=int),
        'progenitor_windows_equal': derived == labels,
        'history': compare(native_history, built.History.Entities),
        'snapshot': compare(snapshot, built.Snapshot.Entities),
        'native_body_tag': history.Entities[1].Prefix.EntityTag,
        'kit_body_tag': built.History.Entities[1].Prefix.EntityTag,
        'grid_body': grid_check(cage, body),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('archives', nargs='*', default=DEFAULT)
    parser.add_argument('--show', type=int, default=-1)
    args = parser.parse_args()
    rows = []
    for relative in args.archives:
        try:
            rows.append(run(relative))
        except Exception as error:  # research census keeps going
            rows.append({'archive': relative, 'error': f'{type(error).__name__}: {error}'})
    print(json.dumps(rows, indent=1))


if __name__ == '__main__':
    main()
