"""Research: which cage edges become B-rep face boundaries.

Rule under test (completion-time line growth):
- Sharp edges (open boundary, creased) are drawn from the start.
- Tracks start at every extraordinary point (interior valence != 4) along each
  smooth outgoing edge, and at the regular end of a sharp chain along its
  straight continuation. A track runs straight through regular vertices.
- A candidate is the straight path of a track up to the first stopper (a
  non-regular vertex or a vertex already drawn). If the stopper is itself a
  track origin heading back along the same path, both ends grow and the
  candidate completes at length / 2, otherwise at length.
- Repeatedly draw the candidate that completes first; ties go to the line
  whose origins have the larger valence, then to the lower origin vertex and
  link. Drawing a line truncates every other candidate at the drawn vertices.
"""

import heapq
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))
from CageGraph import CageGraph  # noqa: E402


def origins(g):
    out = []
    for v in range(g.nverts):
        interior = not g.on_boundary[v] and v not in g.crease_vertices
        if interior and g.valence[v] != 4:
            for link in g.fans[v]:
                if not g.sharp(link):
                    out.append(link)
    # regular ends of sharp chains
    for link in range(len(g.links)):
        if not g.sharp(link):
            continue
        head = g.head[link]
        if not g.is_regular(head):
            continue
        nxt = g.straight(link)
        if nxt is not None and not g.sharp(nxt):
            out.append(nxt)
    return sorted(set(out))


def trace(g, link, drawn_vertices, limit=100000):
    path = [link]
    while True:
        head = g.head[path[-1]]
        if head in drawn_vertices or not g.is_regular(head):
            return path, head
        nxt = g.straight(path[-1])
        if nxt is None or len(path) > limit:
            return path, head
        if nxt == path[0]:
            return path, head
        path.append(nxt)


def boundary_links(g, tie='valence'):
    drawn = [g.sharp(link) for link in range(len(g.links))]
    drawn_vertices = set()
    for link in range(len(g.links)):
        if drawn[link]:
            drawn_vertices.add(g.links[link].VertexIndex)
            drawn_vertices.add(g.head[link])
    starts = origins(g)
    start_set = set(starts)
    live = set(starts)
    while live:
        best = None
        for link in sorted(live):
            origin = g.links[link].VertexIndex
            path, stop = trace(g, link, drawn_vertices)
            back = g.links[path[-1]].Opposite
            two = back in live
            time = len(path) / 2 if two else len(path)
            far = stop if two else origin
            valence = max(g.valence[origin], g.valence[far] if two else 0)
            key = (time, -valence if tie == 'valence' else valence, min(origin, far), link)
            if best is None or key < best[0]:
                best = (key, link, path, two)
        key, link, path, two = best
        for step in path:
            drawn[step] = drawn[g.links[step].Opposite] = True
            drawn_vertices.add(g.links[step].VertexIndex)
            drawn_vertices.add(g.head[step])
        live.discard(link)
        if two:
            live.discard(g.links[path[-1]].Opposite)
        # drop tracks whose first edge is drawn
        for other in list(live):
            if drawn[other]:
                live.discard(other)
    return drawn


def blocks(g, drawn):
    parent = list(range(len(g.faces)))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    for link, value in enumerate(g.links):
        if drawn[link] or value.FaceIndex < 0:
            continue
        other = g.links[value.Opposite].FaceIndex
        if other < 0:
            continue
        a, b = find(value.FaceIndex), find(other)
        if a != b:
            parent[max(a, b)] = min(a, b)
    groups = {}
    for face in range(len(g.faces)):
        groups.setdefault(find(face), []).append(face)
    return sorted((sorted(faces) for faces in groups.values()), key=lambda faces: faces[0])
