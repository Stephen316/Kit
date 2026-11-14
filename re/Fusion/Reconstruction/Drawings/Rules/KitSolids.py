"""Solids for Kit-authored views in the graft builders.

Kit's DWG author draws each view's edges from the view source's solid. The older graft builders (BuildChildren,
BuildDims, BuildTransplant, BuildAuthored) graft leaves between two Kit builds that must share every handle, so
they author views without edges, as Kit did when they were written: `no_edges()` stubs the edge rule out while
they build. They still pass a solid, because Kit's author requires one: `box_solid` gives a box that fills the
view source bounds.
"""
import contextlib
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[4] / 'src'))

from interchange.brep.curves.BrepCurves import LineCurve  # noqa: E402
from interchange.brep.surfaces.BrepSurfaces import PlaneSurface  # noqa: E402
from interchange.brep.topology.BrepModel import BrepModel  # noqa: E402
from interchange.brep.topology.BrepTopology import (  # noqa: E402
    BrepBody, BrepCoedge, BrepEdge, BrepFace, BrepFaceUse, BrepLoop, BrepRegion, BrepShell, BrepShellUse, BrepVertex,
)
from interchange.geometry.models.VectorSpace import SpaceVector  # noqa: E402

import convert.formats.Fusion.DrawingCodec.Dwg.Author.Views.PlaceViewAction as PlaceViewAction  # noqa: E402

CORNERS = [(i & 1, (i >> 1) & 1, (i >> 2) & 1) for i in range(8)]
SIDES = {(0, 0): (0, 2, 6, 4), (0, 1): (1, 5, 7, 3), (1, 0): (0, 4, 5, 1), (1, 1): (2, 3, 7, 6), (2, 0): (0, 1, 3, 2), (2, 1): (4, 6, 7, 5)}


def vec(values):
    return SpaceVector(x=float(values[0]), y=float(values[1]), z=float(values[2]))


def box_solid(low_cm, high_cm):
    low, high = [v * 10 for v in low_cm], [v * 10 for v in high_cm]
    points = [tuple(high[k] if bits[k] else low[k] for k in range(3)) for bits in CORNERS]
    vertices = [BrepVertex(id=f'v{i}', point=vec(p)) for i, p in enumerate(points)]
    edges, curves, coedges, loops, faces, uses, surfaces, keys = [], [], [], [], [], [], [], {}
    for (axis, side), ring in SIDES.items():
        normal = [0.0, 0.0, 0.0]
        normal[axis] = 1.0 if side else -1.0
        reference = [0.0, 0.0, 0.0]
        reference[(axis + 1) % 3] = 1.0
        face = len(faces)
        surfaces.append(PlaneSurface(id=f's{face}', origin=vec(points[ring[0]]), normal=vec(normal), reference_direction=vec(reference)))
        coedge_ids = []
        for a, b in zip(ring, ring[1:] + ring[:1]):
            key = keys.get((b, a))
            if key is None:
                key = f'e{len(edges)}'
                keys[(a, b)] = key
                length = sum((points[b][k] - points[a][k]) ** 2 for k in range(3)) ** 0.5
                direction = [(points[b][k] - points[a][k]) / length for k in range(3)]
                curves.append(LineCurve(id='c' + key, origin=vec(points[a]), direction=vec(direction)))
                edges.append(BrepEdge(id=key, start_vertex_id=f'v{a}', end_vertex_id=f'v{b}', curve_id='c' + key, start_parameter=0.0, end_parameter=length))
            coedges.append(BrepCoedge(id=f'k{len(coedges)}', edge_id=key, reversed=(b, a) in keys))
            coedge_ids.append(coedges[-1].id)
        loops.append(BrepLoop(id=f'l{face}', coedge_ids=tuple(coedge_ids)))
        faces.append(BrepFace(id=f'f{face}', surface_id=f's{face}', loop_ids=(f'l{face}',)))
        uses.append(BrepFaceUse(id=f'u{face}', face_id=f'f{face}'))
    return BrepModel(
        curves=tuple(curves), surfaces=tuple(surfaces), vertices=tuple(vertices), edges=tuple(edges),
        coedges=tuple(coedges), loops=tuple(loops), faces=tuple(faces), face_uses=tuple(uses),
        shells=(BrepShell(id='shell', face_use_ids=tuple(u.id for u in uses), closed=True),),
        shell_uses=(BrepShellUse(id='shelluse', shell_id='shell'),),
        regions=(BrepRegion(id='region', shell_use_ids=('shelluse',)),), bodies=(BrepBody(id='body', region_ids=('region',)),),
    )


@contextlib.contextmanager
def no_edges():
    saved = PlaceViewAction.ViewEdges
    PlaceViewAction.ViewEdges = lambda *args: ()
    try:
        yield
    finally:
        PlaceViewAction.ViewEdges = saved
