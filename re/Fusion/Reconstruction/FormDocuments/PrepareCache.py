import hashlib
import json
import sys
from dataclasses import replace
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[3]
sys.path.insert(0, str(ROOT / 'src'))
from convert.formats.Fusion.BrepCodec.Journal.Spline.SubtypeRef import SubtypeRef
from convert.formats.Fusion.BrepCodec.Journal.Spline.Writing import MakeTsplSurf as TsplModule
from convert.formats.Fusion.BrepCodec.Journal.Spline.Writing.MakeJumps import MakeJumps
from convert.formats.Fusion.BrepCodec.Journal.Spline.Writing.MakeRefScope import MakeRefScope
from convert.formats.Fusion.BrepCodec.Journal.Spline.Writing.MakeSubtrans import MakeSubtrans
from convert.formats.Fusion.BrepCodec.Journal.Writing.MakeBound import MakeBound
import convert.formats.Fusion.BrepCodec.Journal.Validation.CheckNode
from convert.formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument

WRITERS = (
    'convert.formats.Fusion.BrepCodec.Journal.Spline.Writing.MakeSplineNode',
    'convert.formats.Fusion.BrepCodec.Journal.Spline.Writing.MakeParCurve',
)
ORIGINAL = TsplModule.MakeTsplSurf
SOURCES = {
    'Plane': 're/Fusion/LocalOracle/TSpline/Plane.f3d',
    'Box': 're/Fusion/LocalOracle/TSpline/Box.f3d',
}
TARGET = ROOT / 're/Fusion/LocalOracle/FormDocuments/Cache'
SHIFT = 0.05


def counts(knots, degree):
    return sum(knot.Count for knot in knots) - degree + 1


def none_surface(value):
    if isinstance(value, SubtypeRef):
        return MakeRefScope(value, "surface")
    cache = value.Cache
    interval = lambda knots: (*MakeBound(knots[0].Value), *MakeBound(knots[-1].Value))
    return (
        (15, None),
        (13, 't_spl_sur'),
        (4, value.Revision),
        (21, 2),
        *interval(cache.KnotsU),
        *interval(cache.KnotsV),
        (21, cache.ClosureU),
        (21, cache.ClosureV),
        (21, cache.SingularU),
        (21, cache.SingularV),
        *MakeJumps(value.Jumps),
        (11, None),
        *(field for bound in value.Ranges for field in MakeBound(bound)),
        (21, value.TypeCode),
        *MakeSubtrans(value.Subtrans),
        (4, value.FaceIndex),
        (16, None),
    )


def shifted_surface(value):
    if isinstance(value, SubtypeRef):
        return MakeRefScope(value, "surface")
    cache = value.Cache
    width = counts(cache.KnotsU, cache.DegreeU)
    height = counts(cache.KnotsV, cache.DegreeV)
    if width * height != len(cache.Points):
        raise ValueError('unexpected control net size')
    points = []
    for index, point in enumerate(cache.Points):
        column, row = index % width, index // width
        inside = 0 < column < width - 1 and 0 < row < height - 1
        points.append((point[0], point[1], point[2] + SHIFT) if inside else point)
    return ORIGINAL(replace(value, Cache=replace(cache, Points=tuple(points))))


CHECK_NODE = sys.modules['convert.formats.Fusion.BrepCodec.Journal.Validation.CheckNode'].CheckNode


def rebind(original, replacement):
    for module in list(sys.modules.values()):
        if getattr(module, original.__name__, None) is original:
            setattr(module, original.__name__, replacement)


def emit(model, writer):
    if writer is ORIGINAL:
        return EmitParsed(model)
    skip = lambda entity: None
    skip.__name__ = 'CheckNode'
    writer.__name__ = 'MakeTsplSurf'
    rebind(ORIGINAL, writer)
    rebind(CHECK_NODE, skip)
    try:
        return EmitParsed(model)
    finally:
        rebind(writer, ORIGINAL)
        rebind(skip, CHECK_NODE)


def main():
    TARGET.mkdir(parents=True, exist_ok=True)
    rows = []
    for name, relative in SOURCES.items():
        data = (ROOT / relative).read_bytes()
        model = ReadDocument(data)
        for variant, writer in (('Control', ORIGINAL), ('SurfNone', none_surface), ('SurfShifted', shifted_surface)):
            payload = emit(model, writer)
            path = TARGET / (name + variant + '.f3d')
            path.write_bytes(payload)
            row = {'case': name, 'variant': variant, 'file': str(path.relative_to(ROOT)), 'sha256': hashlib.sha256(payload).hexdigest(), 'source': relative, 'source_sha256': hashlib.sha256(data).hexdigest()}
            if variant == 'Control':
                row['reads_back_equal'] = ReadDocument(payload) == model
            rows.append(row)
    report = {
        'scope': 'Form converted-surface cache authority: unchanged control, t_spl_sur saved with approximation level none, and t_spl_sur caches with interior control points moved',
        'python': sys.version.split()[0],
        'shift_cm': SHIFT,
        'rows': rows,
    }
    (TARGET / 'Preparation.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
