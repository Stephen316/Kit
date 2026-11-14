"""Research: label the grips around an extraordinary point by sector grid coordinates."""

import numpy as np


def unfold(cage, vertex, reach=3, ring=None):
    """Map (k, a, b) with 0 <= a, b <= reach to cage vertices, sector k grid."""
    if ring is None:
        ring = cage.ring(vertex)
    n = len(ring)
    labels = {}
    for k, (face, corner) in enumerate(ring):
        loop = cage.faces[face]
        coords = {loop[corner]: (0, 0), loop[(corner + 1) % 4]: (1, 0), loop[(corner + 2) % 4]: (1, 1), loop[(corner + 3) % 4]: (0, 1)}
        seen = {face}
        queue = [(face, coords)]
        while queue:
            face_now, known = queue.pop()
            loop_now = cage.faces[face_now]
            for v, c in known.items():
                labels.setdefault((k, c[0], c[1]), v)
            for i in range(4):
                p, q = loop_now[i], loop_now[(i + 1) % 4]
                if (q, p) not in cage.half:
                    continue
                other, corner2 = cage.half[(q, p)]
                if other in seen:
                    continue
                loop2 = cage.faces[other]
                cp, cq = np.array(known[p]), np.array(known[q])
                rp = np.array(known[loop_now[(i - 1) % 4]])
                rq = np.array(known[loop_now[(i + 2) % 4]])
                fp, fq = 2 * cp - rp, 2 * cq - rq
                cells = [cp, cq, fp, fq]
                if min(c.min() for c in cells) < 0 or max(c.max() for c in cells) > reach:
                    continue
                if vertex in (loop2[(corner2 + 2) % 4], loop2[(corner2 + 3) % 4]):
                    continue
                new = {q: tuple(cq), p: tuple(cp), loop2[(corner2 + 2) % 4]: tuple(fp), loop2[(corner2 + 3) % 4]: tuple(fq)}
                seen.add(other)
                queue.append((other, new))
    canon = {}
    for (k, a, b), v in labels.items():
        if a == 0 and b == 0:
            key = ('ep',)
        elif a == 0:
            key = ((k + 1) % n, b, 0)
        else:
            key = (k, a, b)
        if key in canon and canon[key] != v:
            raise ValueError('inconsistent unfold at %s' % (key,))
        canon[key] = v
    return n, canon


def express(cage, canon, row, tol=1e-12):
    """Coefficients of a grip row on labelled vertices, plus the leftover weight."""
    out = {}
    used = np.zeros(row.shape[0], dtype=bool)
    for key, v in canon.items():
        grip = cage.grip_of.get(v, v)
        out[key] = row[grip]
        used[grip] = True
    rest = np.abs(row[~used]).max() if (~used).any() else 0.0
    return out, rest
