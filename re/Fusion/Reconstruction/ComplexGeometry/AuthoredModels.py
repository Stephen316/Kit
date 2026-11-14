"""Explicit control-point models authored through the production NURBS API."""
from convert.formats.Fusion.BrepCodec.Journal.Complex.Authoring.NurbsBody import NurbsBody, NurbsEdge, NurbsFace, NurbsUse
from convert.formats.Fusion.BrepCodec.Journal.Complex.Authoring.PatchSheet import LinePcurve, PatchSheet
from convert.formats.Fusion.BrepCodec.Journal.Complex.Spline.BsCurve import BsCurve
from convert.formats.Fusion.BrepCodec.Journal.Complex.Spline.BsSurface import BsSurface

from NurbsMath import full_knots

PILLOW_SIDE = 2.0
PILLOW_ORIGIN = (0.5, 0.25, -0.75)


def greville(degree, knots, multiplicity):
    vector = full_knots(knots, multiplicity, degree)
    count = len(vector) - degree - 1
    return [sum(vector[index + 1:index + degree + 1]) / degree for index in range(count)]


def bicubic_patch():
    ugrid = greville(3, (0.0, 0.4, 1.0), (3, 1, 3))
    vgrid = greville(3, (0.0, 1.0), (3, 3))
    heights = ((0.0, 0.2, 0.1, -0.1, 0.0), (0.3, 0.9, 1.1, 0.6, 0.2), (0.1, 0.7, 1.4, 0.8, -0.2), (0.0, -0.1, 0.3, 0.2, 0.1))
    shifts = {(1, 2): (0.15, 0.0), (2, 3): (0.0, -0.1)}
    poles = []
    for row, vvalue in enumerate(vgrid):
        for col, uvalue in enumerate(ugrid):
            dx, dy = shifts.get((row, col), (0.0, 0.0))
            poles.append((0.5 + 3.0 * uvalue + dx, -1.0 + 2.0 * vvalue + dy, heights[row][col]))
    return BsSurface(False, '', 3, 3, 0, 0, 0, 0, (0.0, 0.4, 1.0), (3, 1, 3), (0.0, 1.0), (3, 3), tuple(poles), ())


def rational_patch():
    heights = ((0.0, 0.3, 0.1), (0.2, 1.0, 0.4), (0.4, 1.3, 0.2), (0.1, 0.2, 0.0))
    weights = ((1.0, 0.8, 1.0), (0.9, 0.6, 0.9), (1.1, 0.7, 1.2), (1.0, 0.85, 1.0))
    poles = tuple((-2.0 + 1.5 * col, 1.0 + 1.2 * row, heights[row][col]) for row in range(4) for col in range(3))
    flat = tuple(weights[row][col] for row in range(4) for col in range(3))
    return BsSurface(True, 'both', 2, 2, 0, 0, 0, 0, (0.0, 1.0), (2, 2), (0.0, 0.5, 1.0), (2, 1, 2), poles, flat)


def corner_point(corner):
    return tuple(PILLOW_ORIGIN[axis] + PILLOW_SIDE * corner[axis] for axis in range(3))


def corner_index(corner):
    return corner[0] + 2 * corner[1] + 4 * corner[2]


def pillow_edges():
    edges = []
    for axis in range(3):
        others = [index for index in range(3) if index != axis]
        for first in (0, 1):
            for second in (0, 1):
                start = [0, 0, 0]
                start[others[0]], start[others[1]] = first, second
                end = list(start)
                end[axis] = 1
                a, b = corner_point(start), corner_point(end)
                poles = tuple(tuple(a[k] + (b[k] - a[k]) * step / 3 for k in range(3)) for step in range(4))
                curve = BsCurve(False, 3, 0, (0.0, 1.0), (3, 3), 3, poles, ())
                edges.append(NurbsEdge(corner_index(start), corner_index(end), curve))
    return tuple(edges)


AXES = {'x': (1, 0, 0), 'y': (0, 1, 0), 'z': (0, 0, 1)}
PILLOW_FACES = (
    ('bottom', (0, 0, 0), 'y', 'x', 0.25, 1.0, False),
    ('top', (0, 0, 1), 'x', 'y', 0.5, 1.8, True),
    ('front', (0, 0, 0), 'x', 'z', 0.35, 1.0, False),
    ('back', (0, 1, 0), 'z', 'x', 0.35, 1.0, False),
    ('left', (0, 0, 0), 'z', 'y', 0.35, 1.0, False),
    ('right', (1, 0, 0), 'y', 'z', 0.35, 1.0, False),
)


def pillow_face(edges, origin, uname, vname, bulge, weight, split):
    uaxis, vaxis = AXES[uname], AXES[vname]
    normal = (uaxis[1] * vaxis[2] - uaxis[2] * vaxis[1], uaxis[2] * vaxis[0] - uaxis[0] * vaxis[2], uaxis[0] * vaxis[1] - uaxis[1] * vaxis[0])
    uknots, umult = ((0.0, 0.5, 1.0), (3, 1, 3)) if split else ((0.0, 1.0), (3, 3))
    ugrid, vgrid = greville(3, uknots, umult), greville(3, (0.0, 1.0), (3, 3))
    poles, weights = [], []
    for row, vvalue in enumerate(vgrid):
        for col, uvalue in enumerate(ugrid):
            interior = 0 < row < len(vgrid) - 1 and 0 < col < len(ugrid) - 1
            base = [PILLOW_ORIGIN[k] + PILLOW_SIDE * (origin[k] + uvalue * uaxis[k] + vvalue * vaxis[k]) for k in range(3)]
            poles.append(tuple(base[k] + (bulge * normal[k] if interior else 0.0) for k in range(3)))
            weights.append(weight if interior else 1.0)
    rational = weight != 1.0
    surface = BsSurface(rational, 'both' if rational else '', 3, 3, 0, 0, 0, 0, uknots, umult, (0.0, 1.0), (3, 3), tuple(poles), tuple(weights) if rational else ())
    corners_uv = ((0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0))

    def corner_of(uv):
        return tuple(origin[k] + int(uv[0]) * uaxis[k] + int(uv[1]) * vaxis[k] for k in range(3))

    uses = []
    for side in range(4):
        first, second = corners_uv[side], corners_uv[(side + 1) % 4]
        start, end = corner_index(corner_of(first)), corner_index(corner_of(second))
        edge_index = next(index for index, edge in enumerate(edges) if {edge.StartVertex, edge.EndVertex} == {start, end})
        reverse = edges[edge_index].StartVertex != start
        lead, trail = (second, first) if reverse else (first, second)
        uses.append(NurbsUse(edge_index, reverse, LinePcurve(lead, trail, 0.0, 1.0)))
    return NurbsFace(surface, tuple(uses))


def pillow_box():
    edges = pillow_edges()
    points = tuple(corner_point((index & 1, (index >> 1) & 1, (index >> 2) & 1)) for index in range(8))
    faces = tuple(pillow_face(edges, origin, uname, vname, bulge, weight, split) for _, origin, uname, vname, bulge, weight, split in PILLOW_FACES)
    return NurbsBody(points, edges, faces)


def authored_models():
    return (
        ('AuthoredPatch', PatchSheet(bicubic_patch()), 'Open bicubic B-spline sheet with an interior u knot, explicit 5x4 control net'),
        ('AuthoredRational', PatchSheet(rational_patch()), 'Open rational biquadratic sheet with an interior v knot and varying boundary weights'),
        ('AuthoredPillow', pillow_box(), 'Closed freeform solid: six bicubic faces bulged outward, rational top face with an interior u knot, twelve cubic B-spline edges'),
    )
