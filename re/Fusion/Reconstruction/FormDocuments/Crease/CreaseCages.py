"""Research: closed Form cages whose crease dihedral angle is set exactly.

The base cage is a box of 2 x n x 1 quads whose twelve cube edges and eight
corners are creased. The top face also carries a creased ridge along y at
x = 1, so the top splits into two halves. Every grip of a top half lies on
creases, and Catmull-Clark style crease rules use only grips on the crease,
so a half whose grips are coplanar converts to a planar face. Rotating the
outer top row of the right half about the ridge axis by theta therefore gives
a crease whose two faces meet at exactly theta along its whole length.
Positive theta folds the right half down (convex ridge), negative folds it
up (valley). A per-row angle twists the half so the angle varies along y.
"""

import hashlib
import json
import math
import sys
from dataclasses import replace
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[4]
sys.path.insert(0, str(ROOT / 'src'))
from convert.formats.Fusion.TSplineCodec.EmitTspline import EmitTspline
from convert.formats.Fusion.TSplineCodec.MakeClosedCage import MakeClosedCage
from convert.formats.Fusion.TSplineCodec.Model.ControlGrip import ControlGrip
from convert.formats.Fusion.TSplineCodec.Model.CreaseData import CreaseData
from convert.formats.Fusion.TSplineCodec.Model.SurfaceHeader import SurfaceHeader
from convert.formats.Fusion.TSplineCodec.ReadTspline import ReadTspline

TARGET = ROOT / 're/Fusion/LocalOracle/FormDocuments/Crease'
HEADER = SurfaceHeader(VersionCount=1)


def grid_box(counts, size):
    lookup = {}
    keys = []
    quads = []

    def index(key):
        if key not in lookup:
            lookup[key] = len(keys)
            keys.append(key)
        return lookup[key]

    for axis in range(3):
        other = [item for item in range(3) if item != axis]
        for side in (0, counts[axis]):
            for first in range(counts[other[0]]):
                for second in range(counts[other[1]]):
                    corners = []
                    for du, dv in ((0, 0), (1, 0), (1, 1), (0, 1)):
                        key = [0, 0, 0]
                        key[axis], key[other[0]], key[other[1]] = side, first + du, second + dv
                        corners.append(tuple(key))
                    a, b, d = corners[0], corners[1], corners[3]
                    normal = [(b[1] - a[1]) * (d[2] - a[2]) - (b[2] - a[2]) * (d[1] - a[1]), (b[2] - a[2]) * (d[0] - a[0]) - (b[0] - a[0]) * (d[2] - a[2]), (b[0] - a[0]) * (d[1] - a[1]) - (b[1] - a[1]) * (d[0] - a[0])]
                    outward = normal[axis] * (1 if side else -1)
                    ordered = corners if outward > 0 else list(reversed(corners))
                    quads.append(tuple(index(key) for key in ordered))
    points = [tuple(size[axis] * key[axis] / counts[axis] for axis in range(3)) for key in keys]
    return keys, points, quads


def bounds_of(key, counts):
    return {(axis, key[axis]) for axis in range(3) if key[axis] in (0, counts[axis])}


def edge_pairs(surface):
    links = surface.Topology.Links
    pairs = {}
    for link in links:
        pairs[link.EdgeIndex] = (link.VertexIndex, links[link.NextLink].VertexIndex)
    return pairs


def crease_sets(surface, keys, counts, ridge, extra_edges=(), loose_edges=()):
    edges, verts = set(), set()
    for edge, (first, second) in edge_pairs(surface).items():
        a, b = keys[first], keys[second]
        cube = len(bounds_of(a, counts) & bounds_of(b, counts)) >= 2
        on_ridge = ridge is not None and a[0] == ridge and b[0] == ridge and a[2] == counts[2] and b[2] == counts[2]
        pair = frozenset((a, b))
        if (cube or on_ridge or pair in extra_edges) and pair not in loose_edges:
            edges.add(edge)
    for index, key in enumerate(keys):
        if len(bounds_of(key, counts)) == 3:
            verts.add(index)
    creased_count = {}
    for edge in edges:
        for vertex in edge_pairs(surface)[edge]:
            creased_count[vertex] = creased_count.get(vertex, 0) + 1
    for vertex, count in creased_count.items():
        if count >= 3:
            verts.add(vertex)
    return tuple(sorted(edges)), tuple(sorted(verts))


def rotate_about_ridge(point, pivot_x, pivot_z, angle_deg):
    x, y, z = point
    radius = x - pivot_x
    angle = math.radians(angle_deg)
    return (pivot_x + radius * math.cos(angle), y, pivot_z - radius * math.sin(angle))


def roof(name, angles, ny=3, scale=1.0, stretch=1.0, ridge_creased=True, loose=()):
    """angles: one fold angle (deg) per outer top-row grip along y, or a single number."""
    counts = (2, ny, 1)
    size = (2.0, ny * stretch, 1.0)
    keys, points, quads = grid_box(counts, size)
    if not isinstance(angles, (list, tuple)):
        angles = [angles] * (ny + 1)
    moved = []
    for key, point in zip(keys, points):
        if key[0] == 2 and key[2] == 1:
            point = rotate_about_ridge(point, 1.0, 1.0, angles[key[1]])
        moved.append(tuple(scale * value for value in point))
    grips = tuple(ControlGrip(round(x, 12), round(y, 12), round(z, 12)) for x, y, z in moved)
    surface = MakeClosedCage(grips, tuple(quads), Header=HEADER)
    loose_pairs = {frozenset(pair) for pair in loose}
    edges, verts = crease_sets(surface, keys, counts, 1 if ridge_creased else None, loose_edges=loose_pairs)
    surface = replace(surface, Creases=CreaseData(edges, verts))
    design = {'layout': 'roof', 'quads': list(counts), 'size_cm': [scale * value for value in size], 'fold_deg_per_row': list(angles), 'scale': scale, 'ridge_creased': ridge_creased, 'loose_edges': [[list(a), list(b)] for a, b in loose], 'creased_edges': len(edges), 'crease_vertices': len(verts)}
    return name, surface, design


def round_one():
    cases = []
    for theta in (0.0, 0.1, 0.3, 0.5, 0.6, 0.65, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95, 1.0, 1.05, 1.1, 1.15, 1.2, 1.5, 2.0, 3.0, 10.0):
        cases.append(roof('Roof%s' % fmt(theta), theta))
    for theta in (-0.5, -0.9, -1.0, -1.1, -2.0):
        cases.append(roof('Roof%s' % fmt(theta), theta))
    for scale in (10.0, 0.1):
        for theta in (0.5, 0.9, 1.1, 2.0):
            cases.append(roof('Roof%sScale%s' % (fmt(theta), fmt(scale)), theta, scale=scale))
    return cases


def pilot():
    return [roof('Roof%s' % fmt(theta), theta) for theta in (0.0, 0.5, 1.0, 2.0, 20.0)]


def linear(first, last, count):
    return [first + (last - first) * index / (count - 1) for index in range(count)]


def round_two():
    cases = []
    for first, last in ((0.0, 3.0), (0.0, 1.5), (-3.0, 3.0), (-0.6, 0.6), (-0.6, 2.0), (0.5, 1.5), (-1.5, 0.3)):
        cases.append(roof('Ramp%sTo%s' % (fmt(first), fmt(last)), linear(first, last, 7), ny=6))
    cases.append(roof('StepEnd2', [0.0, 0.0, 0.0, 0.0, 2.0, 2.0, 2.0], ny=6))
    cases.append(roof('Bump3', [0.0, 0.0, 0.0, 3.0, 0.0, 0.0, 0.0], ny=6))
    cases.append(roof('Bump1', [0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0], ny=6))
    loose = (((1, 0, 1), (1, 1, 1)), ((1, 2, 1), (1, 3, 1)))
    for theta in (0.5, 1.0, 2.0, 5.0, 20.0):
        cases.append(roof('Dart%s' % fmt(theta), theta, loose=loose))
    for theta in (0.5, 0.9, 1.1):
        cases.append(roof('Roof%sLong' % fmt(theta), theta, stretch=4.0))
    return cases


def fmt(value):
    text = ('%.8g' % value).replace('-', 'm').replace('.', 'p')
    return text


def round_three():
    cases = []
    for theta in (0.9999, 0.99999, 1.000001, 1.00001, 1.0001, 1.001, 1.002, 1.0025, 1.0027, 1.003, 1.005, 1.01, 1.02, 1.03, 1.04):
        cases.append(roof('Roof%s' % fmt(theta), theta))
    for theta in (-1.001, -1.01, -1.03):
        cases.append(roof('Roof%s' % fmt(theta), theta))
    return cases


def round_four():
    cases = []
    ramps = ((0.3, -1.5), (-0.3, 1.5), (1.5, -0.3), (2.0, -0.6), (-1.5, 0.5), (-0.5, 1.5), (-1.2, 1.2), (-0.9, 0.9), (-2.5, 3.5), (-1.25, 1.75), (-0.75, 1.05), (-3.25, 2.75), (-2.0, 1.0), (-0.8, 0.4), (-1.6, 0.8), (-0.4, 0.8), (-0.8, 1.6), (-1.2, 2.4))
    for first, last in ramps:
        cases.append(roof('Ramp%sTo%s' % (fmt(first), fmt(last)), linear(first, last, 7), ny=6))
    steps = {'StepSmall': [0.3, 0.3, 0.3, 0.3, 2.0, 2.0, 2.0], 'StepSign': [-0.3, -0.3, -0.3, -0.3, 2.0, 2.0, 2.0], 'StepFlatSmall': [0.0, 0.0, 0.0, 0.0, 0.5, 0.5, 0.5], 'StepConcave': [0.0, 0.0, 0.0, 0.0, -2.0, -2.0, -2.0], 'StepStart2': [2.0, 2.0, 2.0, 2.0, 0.0, 0.0, 0.0]}
    for name, rows in steps.items():
        cases.append(roof(name, rows, ny=6))
    return cases


def round_five():
    cases = []
    for first, last in ((0.0, 1.0006), (0.0, 1.002), (0.0, 1.01), (1.0006, 0.0), (1.002, 0.0), (0.9, 1.0006)):
        cases.append(roof('Ramp%sTo%s' % (fmt(first), fmt(last)), linear(first, last, 7), ny=6))
    for peak in (0.999, 1.002, 1.01):
        height = peak * 48.0 / 46.0
        cases.append(roof('PeakMid%s' % fmt(peak), [0.0, 0.0, 0.0, height, height, 0.0, 0.0], ny=6))
    for peak in (0.999, 1.002):
        height = peak * 1.5
        cases.append(roof('PeakKnot%s' % fmt(peak), [0.0, 0.0, 0.0, height, 0.0, 0.0, 0.0], ny=6))
    return cases


def round_six():
    cases = []
    for offset in (1e-2, 1e-3, 3e-4, 1e-4, 3e-5, 1e-5, 3e-6, 1e-6, 1e-7, 1e-8):
        cases.append(roof('RootOff%s' % fmt(offset), [index - 3.0 - offset for index in range(7)], ny=6))
    cases.append(roof('RootAt5p5', [0.6 * (index - 5.5) for index in range(7)], ny=6))
    cases.append(roof('RootAt0p5', [0.6 * (index - 0.5) for index in range(7)], ny=6))
    cases.append(roof('VeeLarge', [3.0, 2.0, 0.0, 0.0, 0.0, 2.0, 3.0], ny=6))
    cases.append(roof('VeeSmall', [0.6, 0.4, 0.0, 0.0, 0.0, 0.4, 0.6], ny=6))
    cases.append(roof('VeeMixed', [0.6, 0.4, 0.0, 0.0, 0.0, 2.0, 3.0], ny=6))
    return cases


def replay(name, relative):
    from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
    surface = ReadDocument((ROOT / relative).read_bytes()).Forms[0].Surface
    return name, surface, {'layout': 'replay', 'source': relative, 'fold_deg_per_row': [], 'scale': 1.0, 'loose_edges': []}


def round_seven():
    return [
        replay('EditedCreasedPlane', 're/Fusion/LocalOracle/FormDocuments/StencilAccept/Saved/OracleCreasedPlaneFresh.f3d'),
        replay('EditedCreasedBox', 're/Fusion/LocalOracle/FormDocuments/StencilAccept/Saved/OracleCreasedBoxFresh.f3d'),
    ]


def edited(case):
    name, surface, design = case
    design = dict(design, edit_move={'near_cm': [0.0, 0.0, 0.0], 'vector_cm': [0.11, 0.07, 0.13]})
    return name + 'Edited', surface, design


def round_eight():
    cases = []
    for first, last in ((-2.5, 3.5), (-3.25, 2.75), (-0.6, 2.0), (-1.5, 0.3), (-3.0, 3.0)):
        cases.append(edited(roof('Ramp%sTo%s' % (fmt(first), fmt(last)), linear(first, last, 7), ny=6)))
    cases.append(edited(roof('Roof2', 2.0)))
    return cases


PLANE_CARRIER = 're/Fusion/LocalOracle/TSplineCodec/vendor_PlaneCreasedControl.f3d'
PLANE_MOVES = (('Plane31Xm0p4', 31, 'CoordX', -0.4), ('Plane31Xp0p4', 31, 'CoordX', 0.4), ('Plane31Xp0p5', 31, 'CoordX', 0.5), ('Plane12Xp0p2', 12, 'CoordX', 0.2), ('Plane30Xp0p4', 30, 'CoordX', 0.4), ('Plane31Zp0p005', 31, 'CoordZ', 0.005), ('Plane31Zp0p01', 31, 'CoordZ', 0.01), ('Plane12Xm0p2', 12, 'CoordX', -0.2))


def plane_move(name, grip, axis, step):
    from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
    carrier = ReadDocument((ROOT / PLANE_CARRIER).read_bytes()).Forms[0].Surface
    grips = tuple(replace(item, **{axis: getattr(item, axis) + step}) if index == grip else item for index, item in enumerate(carrier.Grips))
    return name, replace(carrier, Grips=grips), {'layout': 'CreasedPlane carrier with one grip moved', 'source': PLANE_CARRIER, 'grip': grip, 'axis': axis, 'step_cm': step, 'fold_deg_per_row': [], 'scale': 1.0, 'loose_edges': []}


def round_nine():
    return [plane_move(*move) for move in PLANE_MOVES]


def round_ten():
    rows = {
        'KnotOneSlope0p6': [0.6 * (index - 1.0) for index in range(7)],
        'KnotOneSlope0p8': [0.8 * (index - 1.0) for index in range(7)],
        'KnotFourSide0p4': [-1.6, -1.2, -0.8, -0.4, 0.0, 0.4, 0.4],
        'KnotFourSide0p6': [-1.6, -1.2, -0.8, -0.4, 0.0, 0.4, 0.6],
        'KnotFourSlope0p6': [-2.4, -1.8, -1.2, -0.6, 0.0, 0.6, 0.6],
        'KnotThreeSide0p9': [-0.9, -0.6, -0.3, 0.0, 0.3, 1.5, 3.0],
        'KnotThreeSide0p3': [-0.3, -0.3, -0.3, 0.0, 0.3, 1.5, 3.0],
        'KnotThreeSlope0p8': [-0.8, -0.8, -0.8, 0.0, 0.8, 1.6, 2.4],
        'Rampm1p3To1p7': [-1.3 + 0.5 * index for index in range(7)],
        'Rampm1p2To1p8': [-1.2 + 0.5 * index for index in range(7)],
    }
    return [roof(name, angles, ny=6) for name, angles in rows.items()]


def round_eleven():
    rows = {
        'Rampm1p6To0p8Again': [-1.6 + 0.4 * index for index in range(7)],
        'Rampm0p6To1p2': [-0.6 + 0.3 * index for index in range(7)],
    }
    for last in (0.7, 0.75, 0.85, 0.9):
        rows['KnotFourEnd%s' % fmt(last)] = [-1.6, -1.2, -0.8, -0.4, 0.0, 0.4, last]
    for last in (1.5, 1.7, 2.0):
        rows['KnotThreeFar%s' % fmt(last)] = [-0.9, -0.6, -0.3, 0.0, 0.3, (0.3 + last) / 2.0, last]
    return [roof(name, angles, ny=6) for name, angles in rows.items()]


def moved(case, shift=(0.0, 0.0, 0.0), turn_deg=0.0):
    name, surface, design = case
    angle = math.radians(turn_deg)
    cos, sin = math.cos(angle), math.sin(angle)
    grips = []
    for grip in surface.Grips:
        x, y, z = grip.CoordX, grip.CoordY, grip.CoordZ
        x, y = cos * x - sin * y, sin * x + cos * y
        grips.append(replace(grip, CoordX=round(x + shift[0], 12), CoordY=round(y + shift[1], 12), CoordZ=round(z + shift[2], 12)))
    return name, replace(surface, Grips=tuple(grips)), dict(design, shift_cm=list(shift), turn_about_z_deg=turn_deg)


def ramp_rows(slope, zero, rows=7):
    return [round(slope * (index - zero), 12) for index in range(rows)]


def round_twelve():
    """Crease split rule: zero position, local symmetry, rigid moves, wide tangent runs, span count."""
    rampE = [-1.6, -1.2, -0.8, -0.4, 0.0, 0.4, 0.8]
    rampF = [-1.6, -1.2, -0.8, -0.4, 0.0, 0.4, 0.85]
    rampC = [-0.6, -0.3, 0.0, 0.3, 0.6, 0.9, 1.2]
    cases = [roof('CtlRampm1p6To0p8', rampE, ny=6), roof('CtlKnotFourEnd0p85', rampF, ny=6), roof('CtlRampm0p6To1p2', rampC, ny=6)]
    shift = (0.123456789, 0.0, 0.987654321)
    cases.append(moved(roof('ShiftRampm1p6To0p8', rampE, ny=6), shift=shift))
    cases.append(moved(roof('ShiftRampm0p6To1p2', rampC, ny=6), shift=shift))
    cases.append(moved(roof('ShiftKnotFourEnd0p85', rampF, ny=6), shift=shift))
    cases.append(moved(roof('TurnRampm1p6To0p8', rampE, ny=6), turn_deg=30.0))
    cases.append(moved(roof('TurnRampm0p6To1p2', rampC, ny=6), turn_deg=30.0))
    rows = {
        'ZeroTwoSymFar': [-0.6, -0.3, 0.0, 0.3, 0.6, 1.2, 1.5],
        'ZeroTwoAsymFour': [-0.6, -0.3, 0.0, 0.3, 0.65, 0.9, 1.2],
        'ZeroTwoAsymZero': [-0.65, -0.3, 0.0, 0.3, 0.6, 0.9, 1.2],
        'ZeroFourSymFar': [-2.0, -1.0, -0.8, -0.4, 0.0, 0.4, 0.8],
        'ZeroFourAsymTwo': [-1.6, -1.2, -0.85, -0.4, 0.0, 0.4, 0.8],
        'ZeroThreeSym': [-0.6, -0.6, -0.3, 0.0, 0.3, 0.6, 1.5],
        'ZeroThreeSymOne': [-0.6, -0.6, -0.3, 0.0, 0.3, 0.7, 1.5],
    }
    for name, angles in rows.items():
        cases.append(roof(name, angles, ny=6))
    for slope, zero in ((0.5, 2.25), (0.5, 2.75), (0.5, 3.5), (0.6, 2.5), (0.7, 2.5), (0.8, 2.5), (0.9, 2.5), (0.6, 2.3)):
        cases.append(roof('RootS%sZ%s' % (fmt(slope), fmt(zero)), ramp_rows(slope, zero), ny=6))
    for slope, zero in ((0.3, 2.0), (0.3, 3.0), (0.3, 6.0), (0.3, 1.0), (0.3, 5.0)):
        cases.append(roof('Ny8S%sZ%s' % (fmt(slope), fmt(zero)), ramp_rows(slope, zero, rows=9), ny=8))
    return cases


def round_thirteen():
    """Off-knot sign change inside a wide tangent run: where Fusion splits."""
    cases = []
    for slope in (0.5, 0.55, 0.6, 0.65):
        for zero in (2.1, 2.3, 2.5, 2.7, 2.9):
            cases.append(roof('WideS%sZ%s' % (fmt(slope), fmt(zero)), ramp_rows(slope, zero), ny=6))
    base = ramp_rows(0.6, 2.5)
    cases.append(roof('WideS0p6Z2p5LeftBig', [-2.5] + base[1:], ny=6))
    cases.append(roof('WideS0p6Z2p5RightBig', base[:-1] + [3.5], ny=6))
    base = ramp_rows(0.5, 2.5)
    cases.append(roof('WideS0p5Z2p5LeftBig', [-2.5] + base[1:], ny=6))
    cases.append(roof('WideS0p5Z2p5RightBig', base[:-1] + [3.5], ny=6))
    for slope, zero in ((0.5, 3.5), (0.6, 3.5), (0.5, 4.5), (0.4, 3.5)):
        cases.append(roof('Ny8WideS%sZ%s' % (fmt(slope), fmt(zero)), ramp_rows(slope, zero, rows=9), ny=8))
    return cases


def kink_rows(left, right, pivot, zero, rows=7):
    start = left * (pivot - zero)
    return [round(left * (index - zero) if index <= pivot else start + right * (index - pivot), 12) for index in range(rows)]


def round_fourteen():
    """Wide tangent run split: slope threshold, local slopes, end size, longer ridges."""
    cases = []
    for slope in (0.56, 0.57, 0.575, 0.58, 0.59):
        cases.append(roof('SlopeS%sZ2p3' % fmt(slope), ramp_rows(slope, 2.3), ny=6))
    for slope in (0.57, 0.575, 0.58):
        cases.append(roof('SlopeS%sZ2p5' % fmt(slope), ramp_rows(slope, 2.5), ny=6))
    for left, right, pivot in ((0.5, 0.6, 2), (0.6, 0.5, 2), (0.6, 0.5, 1), (0.5, 0.6, 1), (0.5, 0.8, 3)):
        cases.append(roof('KinkL%sR%sP%d' % (fmt(left), fmt(right), pivot), kink_rows(left, right, pivot, 2.3), ny=6))
    base = ramp_rows(0.5, 2.3)
    for last in (2.25, 2.75, 3.5):
        cases.append(roof('EndS0p5Z2p3Right%s' % fmt(last), base[:-1] + [last], ny=6))
    for first in (-1.6, -2.0):
        cases.append(roof('EndS0p5Z2p3Left%s' % fmt(first), [first] + base[1:], ny=6))
    for slope, zero in ((0.5, 2.3), (0.6, 2.5), (0.45, 2.5), (0.4, 2.7), (0.4, 3.1), (0.5, 3.3), (0.6, 4.1)):
        cases.append(roof('Ny8S%sZ%s' % (fmt(slope), fmt(zero)), ramp_rows(slope, zero, rows=9), ny=8))
    cases.append(roof('CtlWideS0p6Z2p3', ramp_rows(0.6, 2.3), ny=6))
    return cases


def round_fifteen():
    """Wide tangent run split: mirrored cases, both ends short, steep strong end, long steep runs."""
    cases = [roof('MirS0p6Z3p5', ramp_rows(0.6, 3.5), ny=6), roof('MirS0p6Z3p9', ramp_rows(0.6, 3.9), ny=6)]
    mirrored = (('MirKinkL0p6R0p5P1', [-1.72, -1.22, -0.72, -0.22, 0.28, 0.78, 1.38]), ('MirKinkL0p5R0p8P3', [-2.75, -1.95, -1.15, -0.35, 0.15, 0.65, 1.15]), ('MirWideS0p5Z2p5RightBig', [-3.5, -1.25, -0.75, -0.25, 0.25, 0.75, 1.25]), ('MirEndS0p5Z2p3Right2p75', [-2.75, -1.35, -0.85, -0.35, 0.15, 0.65, 1.15]))
    cases.extend(roof(name, rows, ny=6) for name, rows in mirrored)
    for zero in (2.6, 2.9):
        cases.append(roof('BothS0p4Z%s' % fmt(zero), ramp_rows(0.4, zero), ny=6))
    base = ramp_rows(0.5, 2.3)
    for last in (1.95, 2.05):
        cases.append(roof('EndS0p5Z2p3Right%s' % fmt(last), base[:-1] + [last], ny=6))
    cases.append(roof('KinkL0p5R0p8P4', kink_rows(0.5, 0.8, 4, 2.3), ny=6))
    cases.append(roof('KinkStepThree', [-1.15, -0.65, -0.15, 0.35, 1.05, 1.55, 2.05], ny=6))
    cases.append(roof('KinkSteepEndLong', [-1.65, -0.85, -0.45, -0.05, 0.35, 0.75, 1.15], ny=6))
    cases.append(roof('Ny8EndS0p5Z2p3Leftm1p6', [-1.6] + ramp_rows(0.5, 2.3, rows=9)[1:], ny=8))
    for zero in (3.7, 3.9):
        cases.append(roof('Ny8S0p6Z%s' % fmt(zero), ramp_rows(0.6, zero, rows=9), ny=8))
    return cases


def round_sixteen():
    """Held-out check of the wide tangent run split rule: new shapes, stretched and scaled cages, a turned cage."""
    cases = [
        roof('HoldS0p6Z2p5Stretch2', ramp_rows(0.6, 2.5), ny=6, stretch=2.0),
        roof('HoldS0p5Z2p3Stretch0p5', ramp_rows(0.5, 2.3), ny=6, stretch=0.5),
        roof('HoldS0p6Z2p5Scale2', ramp_rows(0.6, 2.5), ny=6, scale=2.0),
        roof('HoldSteepRootLongLeft', [-1.3, -0.9, -0.5, -0.1, 0.6, 1.3, 2.0], ny=6),
        roof('HoldMirSteepRootLongLeft', [-2.0, -1.3, -0.6, 0.1, 0.5, 0.9, 1.3], ny=6),
        roof('HoldBothEndsSteep', [-1.6, -0.84, -0.44, -0.04, 0.36, 0.76, 1.6], ny=6),
        roof('HoldMirKinkSteepEndLong', [-1.15, -0.75, -0.35, 0.05, 0.45, 0.85, 1.65], ny=6),
        roof('HoldEndLeftEndRight', [-1.6, -0.65, -0.15, 0.35, 0.85, 1.35, 2.25], ny=6),
        roof('HoldS0p6Z2p1Right3p5', ramp_rows(0.6, 2.1)[:-1] + [3.5], ny=6),
        roof('HoldNy8S0p65Z2p3', ramp_rows(0.65, 2.3, rows=9), ny=8),
        roof('HoldNy8S0p45Z3p5', ramp_rows(0.45, 3.5, rows=9), ny=8),
        roof('HoldNy8S0p5Z2p3Right3p5', ramp_rows(0.5, 2.3, rows=9)[:-1] + [3.5], ny=8),
        roof('HoldS0p42Z2p7', ramp_rows(0.42, 2.7), ny=6),
        roof('HoldS0p45Z2p6', ramp_rows(0.45, 2.6), ny=6),
        roof('HoldStepFourFive', [-1.15, -0.65, -0.15, 0.35, 0.85, 1.55, 2.05], ny=6),
        roof('HoldLeftRunSteep', [-1.2, -0.8, -0.1, 0.2, 0.6, 1.0, 1.3], ny=6),
        moved(roof('HoldS0p6Z2p5Turn180', ramp_rows(0.6, 2.5), ny=6), turn_deg=180.0),
        moved(roof('HoldS0p5Z2p3Turn90', ramp_rows(0.5, 2.3), ny=6), shift=(0.25, -0.5, 0.75), turn_deg=90.0),
    ]
    return cases


def mirror_rows(rows):
    return [round(-value, 12) for value in reversed(rows)]


def round_seventeen():
    """Wide tangent run split: how far a steep far side blocks the near knot, both ends confined, slope threshold pins."""
    cases = [
        roof('RchNy8S0p5Z2p1K0p8P6', kink_rows(0.5, 0.8, 6, 2.1, rows=9), ny=8),
        roof('RchNy8S0p4Z2p7K1p2P7', kink_rows(0.4, 1.2, 7, 2.7, rows=9), ny=8),
        roof('RchNy8S0p5Z2p3K1p2P6', kink_rows(0.5, 1.2, 6, 2.3, rows=9), ny=8),
        roof('RchNy8S0p5Z2p3K1p2P7', kink_rows(0.5, 1.2, 7, 2.3, rows=9), ny=8),
        roof('RchNy10S0p5Z2p3K1p2P8', kink_rows(0.5, 1.2, 8, 2.3, rows=11), ny=10),
        roof('RchNy10S0p5Z2p3K1p2P6', kink_rows(0.5, 1.2, 6, 2.3, rows=11), ny=10),
        roof('RchMirNy8S0p5Z2p3Right3p5', mirror_rows(ramp_rows(0.5, 2.3, rows=9)[:-1] + [3.5]), ny=8),
        roof('RchMirNy8S0p5Z2p1K0p8P6', mirror_rows(kink_rows(0.5, 0.8, 6, 2.1, rows=9)), ny=8),
        roof('RchNy8S0p4Z2p7K1p2P6', kink_rows(0.4, 1.2, 6, 2.7, rows=9), ny=8),
    ]
    base = ramp_rows(0.4, 2.7)
    cases.append(roof('BothS0p4Z2p7EndRight', base[:-1] + [1.6], ny=6))
    cases.append(roof('BothS0p4Z2p7EndLeft', [-1.6] + base[1:], ny=6))
    cases.append(roof('BothS0p4Z2p7EndBoth', [-1.6] + base[1:-1] + [1.6], ny=6))
    base = ramp_rows(0.3, 3.95, rows=9)
    cases.append(roof('Ny8BothS0p3Z3p95', base, ny=8))
    cases.append(roof('Ny8BothS0p3Z3p95EndLeft', [-1.65] + base[1:], ny=8))
    cases.append(roof('Ny8BothS0p3Z3p95EndRight', base[:-1] + [1.55], ny=8))
    for slope in (0.5725, 0.5735):
        cases.append(roof('SlopeS%sZ2p3' % fmt(slope), ramp_rows(slope, 2.3), ny=6))
    for stretch in (1.05, 1.04):
        cases.append(roof('SlopeS0p6Z2p3Stretch%s' % fmt(stretch), ramp_rows(0.6, 2.3), ny=6, stretch=stretch))
    return cases


def round_eighteen():
    """Wide tangent run split: slope threshold against span length, and where a steep far side stops blocking the near knot."""
    cases = []
    sweep = ((0.5, 0.44, 2.6, 8), (0.5, 0.37, 3.1, 8), (0.5, 0.31, 3.6, 10), (2.0, 0.74, 2.2, 8), (2.0, 0.88, 2.07, 8), (1.25, 0.59, 2.3, 8), (1.25, 0.625, 2.3, 8), (1.25, 0.66, 2.3, 8), (1.25, 0.7, 2.2, 8), (0.8, 0.555, 2.4, 8), (0.8, 0.527, 2.4, 8), (0.8, 0.5, 2.3, 8), (0.8, 0.47, 2.5, 8))
    for stretch, slope, zero, ny in sweep:
        name = 'StrL%sS%sZ%s' % (fmt(stretch), fmt(slope), fmt(zero))
        cases.append(roof(name, ramp_rows(slope, zero, rows=ny + 1), ny=ny, stretch=stretch))
    cases.append(roof('ScaleL0p5S0p37Z3p1', ramp_rows(0.37, 3.1, rows=9), ny=8, scale=0.5))
    cases.append(roof('ScaleL1p25S0p66Z2p3', ramp_rows(0.66, 2.3, rows=9), ny=8, scale=1.25))
    reach = ((0.3, 3.6, 7, 0.65), (0.3, 3.6, 8, 0.7), (0.3, 3.6, 8, 1.1), (0.4, 2.7, 7, 2.95), (0.4, 2.7, 6, 0.75), (0.55, 2.3, 6, 1.5), (0.55, 2.3, 5, 0.6), (0.45, 2.6, 6, 0.7), (0.45, 2.6, 6, 0.9))
    for slope, zero, pivot, steep in reach:
        name = 'RchNy10S%sZ%sK%sP%d' % (fmt(slope), fmt(zero), fmt(steep), pivot)
        cases.append(roof(name, kink_rows(slope, steep, pivot, zero, rows=11), ny=10))
    return cases


def round_nineteen():
    """Held-out check of the half-width blocking rule, left priority, steep sides and lengths where both slope units agree."""
    base = ramp_rows(0.5, 2.4, rows=9)
    cases = [
        roof('HoldBlkS0p5Z2p4K0p7P6', kink_rows(0.5, 0.7, 6, 2.4, rows=9), ny=8),
        roof('HoldBlkS0p5Z2p4K0p7P5', kink_rows(0.5, 0.7, 5, 2.4, rows=9), ny=8),
        roof('HoldBlkS0p45Z2p88K0p9P6', kink_rows(0.45, 0.9, 6, 2.88, rows=11), ny=10),
        roof('HoldBlkS0p45Z2p88K0p9P7', kink_rows(0.45, 0.9, 7, 2.88, rows=11), ny=10),
        roof('HoldMirBlkS0p5Z2p4K0p7P6', mirror_rows(kink_rows(0.5, 0.7, 6, 2.4, rows=9)), ny=8),
        roof('HoldMirBlkS0p5Z2p4K0p7P5', mirror_rows(kink_rows(0.5, 0.7, 5, 2.4, rows=9)), ny=8),
        roof('HoldShortLeftShallow', [-1.25] + base[1:], ny=8),
        roof('HoldShortLeftShallowBlk', [-1.25] + kink_rows(0.5, 0.7, 5, 2.4, rows=9)[1:], ny=8),
        roof('HoldSteepLeftBlk', [-1.8] + kink_rows(0.5, 0.7, 5, 2.4, rows=9)[1:], ny=8),
        roof('HoldBothSteepLeftShortRight', [-1.4] + ramp_rows(0.4, 2.9)[1:-1] + [1.75], ny=6),
        roof('HoldBothShallowAsym', ramp_rows(0.4, 2.7)[:-1] + [1.45], ny=6),
        roof('HoldNy8S0p62Z3p3', ramp_rows(0.62, 3.3, rows=9), ny=8),
        roof('HoldS0p6Z2p3Stretch0p9', ramp_rows(0.6, 2.3, rows=9), ny=8, stretch=0.9),
        roof('HoldS0p5Z2p3Stretch1p1', ramp_rows(0.5, 2.3, rows=9), ny=8, stretch=1.1),
        roof('HoldS0p6Z2p3Scale0p8', ramp_rows(0.6, 2.3, rows=9), ny=8, scale=0.8),
        roof('HoldS0p5Z2p3Scale1p5', ramp_rows(0.5, 2.3, rows=9), ny=8, scale=1.5),
        moved(roof('HoldBlkS0p5Z2p4K0p7P5Turn45', kink_rows(0.5, 0.7, 5, 2.4, rows=9), ny=8), shift=(1.5, -2.0, 0.5), turn_deg=45.0),
        roof('HoldS0p52Z2p75', ramp_rows(0.52, 2.75, rows=9), ny=8),
    ]
    return cases


def round_twenty():
    """Held-out check of the crossing-slope rule: shallow kinks on either side, odd and long ridges, slopes near the threshold."""
    cases = [
        roof('FinKinkL0p55R0p5P1', kink_rows(0.55, 0.5, 1, 2.3, rows=9), ny=8),
        roof('FinMirKinkL0p55R0p5P1', mirror_rows(kink_rows(0.55, 0.5, 1, 2.3, rows=9)), ny=8),
        roof('FinMirKinkL0p5R0p53P4', mirror_rows(kink_rows(0.5, 0.53, 4, 2.3, rows=9)), ny=8),
        roof('FinNy7S0p5Z2p6', ramp_rows(0.5, 2.6, rows=8), ny=7),
        roof('FinKinkL0p5R0p53P4', kink_rows(0.5, 0.53, 4, 2.3, rows=9), ny=8),
        roof('FinBothLeftShallowShort', [-1.2] + ramp_rows(0.4, 2.7)[1:], ny=6),
        roof('FinS0p6Z2p3Stretch0p95', ramp_rows(0.6, 2.3, rows=9), ny=8, stretch=0.95),
        roof('FinS0p62Z2p3Stretch1p02', ramp_rows(0.62, 2.3, rows=9), ny=8, stretch=1.02),
        roof('FinS0p5Z2p3Stretch0p97', ramp_rows(0.5, 2.3, rows=9), ny=8, stretch=0.97),
        moved(roof('FinKinkL0p55R0p5P1Turn120', kink_rows(0.55, 0.5, 1, 2.3, rows=9), ny=8), shift=(-0.75, 1.25, 0.3), turn_deg=120.0),
        roof('FinNy12S0p4Z2p7', ramp_rows(0.4, 2.7, rows=13), ny=12),
        roof('FinNy12S0p4Z2p7K0p6P5', kink_rows(0.4, 0.6, 5, 2.7, rows=13), ny=12),
        roof('FinS0p35Z3p3', ramp_rows(0.35, 3.3, rows=11), ny=10),
        roof('FinS0p35Z3p3EndLeft', [-1.8] + ramp_rows(0.35, 3.3, rows=11)[1:], ny=10),
        roof('FinS0p56Z2p45', ramp_rows(0.56, 2.45, rows=9), ny=8),
        roof('FinS0p58Z2p45', ramp_rows(0.58, 2.45, rows=9), ny=8),
    ]
    return cases


def round_twentyone():
    """Crossing-slope rule follow-up: right-confined runs whose left side is steeper, unconfined runs that lean, steep left with a steeper right."""
    cases = [
        roof('LeanMirKinkL0p5R0p55P4', mirror_rows(kink_rows(0.5, 0.55, 4, 2.3, rows=9)), ny=8),
        roof('LeanMirKinkL0p45R0p5P5Ny10', mirror_rows(kink_rows(0.45, 0.5, 5, 2.6, rows=11)), ny=10),
        roof('LeanMirKinkL0p5R0p53P3', mirror_rows(kink_rows(0.5, 0.53, 3, 2.4, rows=9)), ny=8),
        roof('LeanMirKinkL0p5R0p6P6', mirror_rows(kink_rows(0.5, 0.6, 6, 2.3, rows=9)), ny=8),
        roof('LeanMirEndLeftMild', mirror_rows(ramp_rows(0.5, 2.3, rows=9)[:-1] + [2.95]), ny=8),
        roof('LeanNeitherLeftKink', kink_rows(0.5, 0.45, 2, 4.5, rows=11), ny=10),
        roof('LeanNeitherRightKink', kink_rows(0.45, 0.5, 6, 4.5, rows=11), ny=10),
        roof('LeanNeitherLeftSteep', [-3.5] + ramp_rows(0.45, 4.5, rows=11)[1:], ny=10),
        roof('LeanLeftSteepRightSteeper', [-1.75] + kink_rows(0.5, 0.9, 4, 2.9, rows=9)[1:], ny=8),
        roof('LeanLeftSteepRightSteeper2', [-1.6] + kink_rows(0.5, 1.2, 4, 2.9, rows=9)[1:], ny=8),
    ]
    return cases


ROUNDS = {'RoundTwentyOne': round_twentyone, 'RoundTwenty': round_twenty,'RoundNineteen': round_nineteen,'RoundEighteen': round_eighteen,'RoundSeventeen': round_seventeen,'RoundSixteen': round_sixteen, 'RoundFifteen': round_fifteen, 'RoundFourteen': round_fourteen, 'RoundThirteen': round_thirteen, 'RoundTwelve': round_twelve, 'RoundEleven': round_eleven, 'RoundTen': round_ten, 'RoundNine': round_nine, 'RoundEight': round_eight, 'Pilot': pilot, 'RoundOne': round_one, 'RoundTwo': round_two, 'RoundThree': round_three, 'RoundFour': round_four, 'RoundFive': round_five, 'RoundSix': round_six, 'RoundSeven': round_seven}


def main():
    name = sys.argv[1]
    folder = TARGET / name
    folder.mkdir(parents=True, exist_ok=True)
    rows = []
    for cage, surface, design in ROUNDS[name]():
        text = EmitTspline(surface)
        if ReadTspline(text) != surface:
            raise RuntimeError('TSM text does not read back')
        path = folder / (cage + '.tsm')
        path.write_bytes(text)
        rows.append({'cage': cage, 'tsm_file': str(path.relative_to(ROOT)), 'tsm_sha256': hashlib.sha256(text).hexdigest(), 'design': design})
        if 'edit_move' in design:
            rows[-1]['edit_move'] = design['edit_move']
    report = {'scope': 'Crease probe round %s: creased roof boxes with a set fold angle on the ridge crease' % name, 'report': name + '/Probe.json', 'python': sys.version.split()[0], 'cages': rows}
    (folder / 'Preparation.json').write_text(json.dumps(report, indent=1) + '\n')
    print(len(rows), 'cages written to', folder.relative_to(ROOT))


if __name__ == '__main__':
    main()
