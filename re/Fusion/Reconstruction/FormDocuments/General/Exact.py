"""Research: exact one-sided B-spline derivatives for cap sectors."""

import numpy as np


def cox_side(t, i, p, x, left):
    if p == 0:
        if left:
            return 1.0 if t[i] < x <= t[i + 1] else 0.0
        return 1.0 if t[i] <= x < t[i + 1] else 0.0
    a = 0.0 if t[i + p] == t[i] else (x - t[i]) / (t[i + p] - t[i]) * cox_side(t, i, p - 1, x, left)
    b = 0.0 if t[i + p + 1] == t[i + 1] else (t[i + p + 1] - x) / (t[i + p + 1] - t[i + 1]) * cox_side(t, i + 1, p - 1, x, left)
    return a + b


def deriv_basis(knots, x, order, left=False, degree=3):
    """Exact derivative of the given order of every degree-3 basis function, left or right limit."""
    count = len(knots) - degree - 1
    if x <= knots[0]:
        left = False
    if x >= knots[-1]:
        left = True
    p = degree - order
    values = [cox_side(knots, i, p, x, left) for i in range(count + order)]
    for level in range(order):
        deg = p + level + 1
        nxt = []
        for i in range(len(values) - 1):
            a = knots[i + deg] - knots[i]
            b = knots[i + deg + 1] - knots[i + 1]
            nxt.append(deg * ((values[i] / a if a > 0 else 0.0) - (values[i + 1] / b if b > 0 else 0.0)))
        values = nxt
    return np.array(values[:count])


def functional_exact(system, k, s, t, ds=0, dt=0, left_s=False, left_t=False):
    sector = system.sectors[k]
    bi = deriv_basis(sector.knots_i, s, ds, left_s)
    bj = deriv_basis(sector.knots_j, t, dt, left_t)
    row = np.zeros(len(system.keys))
    fixed = 0.0
    for i in range(system.size):
        for j in range(system.size):
            w = bi[i] * bj[j]
            if w == 0.0:
                continue
            key = system.key(k, i, j)
            if key[0] == 'fixed':
                fixed = fixed + w * sector.pole(i, j)
            else:
                row[system.slot[key]] += w
    return row, fixed
