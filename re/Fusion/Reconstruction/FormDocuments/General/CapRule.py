"""Research cap rule: Fusion's G1 cap poles around one extraordinary point (EP), as grip rows.

One entry point, cap_rows(request). The request carries what src's Poles/CapHook.py CapInput holds:
Valence, Sectors (KnotsI, KnotsJ from the EP), Reference rows, the Limit row and Unknown. Reference must hold
the net rows of every unknown key and the poles of every other key the rows below touch (indices up to 7).
The result is one pole row (grip -> coefficient) for every unknown key. No free directions are left.

Unknowns are delta = pole - netref, with netref(ep) = Limit. Rows (c = cos(2 pi / n), kappa = (n - 4) c / (n + 5)):

- hard rows: EP = Limit; G1 along every spoke on [0, 2h] with Fusion's lambda profile; the spoke is quadratic
  on [h, 2h]; C2 of pole rows 2 and 3 at 2h (both directions of every sector);
- window rows: seven exact relations per spoke (WINDOW below), integer coefficients a + b c + r (a2 + b2 c);
- ring rows, one per spoke k:
    L_k = c dA11_k - b2 (dS2_k + dS2_k+1) + b3 (dS3_k + dS3_k+1)
    1/2 (L_k-1 + L_k) + b1 (dS1_k-1 + 2 dS1_k + dS1_k+1) = -kappa (nS1_k - EP) - 9c/(n+5) mean_j (nS1_j - EP)
  where nS1 is the net row of spoke pole 1;
- tangent rows (modes +-1 only): sum_k (cos, sin)(2 pi k / n) [T_k + c V_k] = 0 with
    T_k = 2 b1 dS1_k - b2 dS2_k + b3 dS3_k,  V_k = v1 dS1_k + v2 dS2_k + v3 dS3_k;
- even n: alternating twist  sum_k (-1)^k pole A11_k = 9/(n+5) sum_k (-1)^k netref A11_k.

Knots enter through r = L / (h + L), L the span after the double knot at 2h, taken per spoke (ring, tangent)
and per sector direction (window). Fusion's unit-interval caps give r = 2/3 (L = 2h) and r = 1/2 (L = h); an EP may
mix both. The ring and tangent weights were measured at these two ratios and are written linear in r through
t = 6 (r - 1/2):
    b1 = 9/40 + 17 t/130, b2 = 21/20 + 71 t/130, b3 = 6/5 + 59 t/130,
    v1 = -34 t/936, v2 = -1/24 + 71 t/936, v3 = -1/24 - 59 t/936.
The rule refuses a spoke whose two sectors see different spans after 2h (the shared spoke poles do not hold there).
"""
import math

import numpy as np

# Window relations around spoke k, on delta. Local names: 'S<s>.<i>' is pole i of spoke k + s (s = -1, 0, +1);
# 'A<i><j>' is pole (i, j) of sector k (spoke k is its i axis, spoke k + 1 its j axis); 'B<i><j>' is pole (i, j)
# of sector k - 1 (spoke k - 1 is its i axis, spoke k its j axis). A term (name, a, b, a2, b2) has the coefficient
# a + b c + r (a2 + b2 c), where r is the knot ratio of the direction in which the key has index 4 (missing entries
# are 0). All coefficients are exact integers. The mirror across spoke k maps B<i><j> to A<j><i> and S-1 to S+1;
# every relation is even or odd under it, so the table (and the cap) does not depend on the sector order.
# Seven rows per spoke, exactly the rank the other rows leave open.
WINDOW = (
    ('split 2', (('B12', 1), ('A21', -1))),
    ('split 3', (('B13', 1), ('A31', -1))),
    ('split 4', (('B14', 1), ('A41', -1))),
    ('sector balance', (('A41', 1), ('A14', 1), ('A21', -2), ('A12', -2), ('A31', 2), ('A13', 2),
                        ('A22', 8), ('A23', -8), ('A32', -8), ('A33', 8))),
    ('spoke balance', (('S0.1', -8), ('S0.2', 16), ('S0.3', -12), ('S0.4', 4, 0, 1),
                       ('S+1.1', -8), ('S+1.2', 16), ('S+1.3', -12), ('S+1.4', 4, 0, 1),
                       ('A13', -8), ('A31', -8), ('A33', 32))),
    ('cross-spoke even', (('S0.1', -36, 28), ('S0.2', 66, -54), ('S0.3', -78, 70),
                          ('B11', 18, -18), ('A11', 18, -18), ('B12', -33, 27), ('A21', -33, 27),
                          ('B21', 0, 8), ('A12', 0, 8), ('B13', 39, -19), ('A31', 39, -19),
                          ('B31', 0, -8), ('A13', 0, -8), ('B23', 0, -32), ('A32', 0, -32),
                          ('B33', 0, 32), ('A33', 0, 32))),
    ('cross-spoke odd', (('S-1.1', 9, -28), ('S+1.1', -9, 28), ('S-1.2', -12, 56), ('S+1.2', 12, -56),
                         ('S-1.4', -24, 24, 3), ('S+1.4', 24, -24, -3),
                         ('B22', -24, -64), ('A22', 24, 64), ('B23', 24, 128), ('A32', -24, -128),
                         ('B32', 24, -192), ('A23', -24, 192), ('B33', 72, 384), ('A33', -72, -384))),
)

REACH = 4
SIZE = 8


def ring_weights(r):
    t = 6 * (r - 0.5)
    return 9 / 40 + 17 * t / 130, 21 / 20 + 71 * t / 130, 6 / 5 + 59 * t / 130


def tangent_weights(r):
    t = 6 * (r - 0.5)
    return -34 * t / 936, -1 / 24 + 71 * t / 936, -1 / 24 - 59 * t / 936


def lam_shape(x):
    """Fusion's G1 weight profile in units of the first cap knot h."""
    if x <= 1.0:
        return 1.0 - 2.0 * x / 3.0
    if x <= 2.0:
        return (2.0 - x) ** 2 / 3.0
    return 0.0


def spoke_key(k, n, i, j):
    if i == 0 and j == 0:
        return ('ep',)
    if j == 0:
        return ('spoke', k % n, i)
    if i == 0:
        return ('spoke', (k + 1) % n, j)
    return ('in', k % n, i, j)


def cap_keys(n):
    keys = [('ep',)]
    keys += [('spoke', k, i) for k in range(n) for i in range(1, REACH + 1)]
    keys += [('in', k, i, j) for k in range(n) for i in range(1, REACH + 1) for j in range(1, REACH + 1)
             if (i, j) != (REACH, REACH)]
    return keys


def expand_knots(knots):
    """Knot values from (value, count) pairs or plain values; clamped (multiplicity 4) at the EP."""
    out = []
    for entry in knots:
        if isinstance(entry, (tuple, list)):
            out += [float(entry[0])] * int(entry[1])
        else:
            out.append(float(entry))
    out.sort()
    while out.count(out[0]) < 4:
        out.insert(0, out[0])
    return out


def knot_ratio(knots, h):
    """r = L / (h + L), with L the span after the double knot at 2h."""
    after = [x for x in knots if x > 2 * h + 1e-12]
    span = after[0] - 2 * h
    return span / (h + span)


def _cox(t, i, p, x, left):
    if p == 0:
        if left:
            return 1.0 if t[i] < x <= t[i + 1] else 0.0
        return 1.0 if t[i] <= x < t[i + 1] else 0.0
    a = 0.0 if t[i + p] == t[i] else (x - t[i]) / (t[i + p] - t[i]) * _cox(t, i, p - 1, x, left)
    b = 0.0 if t[i + p + 1] == t[i + 1] else (t[i + p + 1] - x) / (t[i + p + 1] - t[i + 1]) * _cox(t, i + 1, p - 1, x, left)
    return a + b


def deriv_basis(knots, x, order, left=False, degree=3):
    """Derivative of the given order of every cubic basis function at x (right limit unless left)."""
    count = len(knots) - degree - 1
    p = degree - order
    values = [_cox(knots, i, p, x, left) for i in range(count + order)]
    for level in range(order):
        deg = p + level + 1
        nxt = []
        for i in range(len(values) - 1):
            a = knots[i + deg] - knots[i]
            b = knots[i + deg + 1] - knots[i + 1]
            nxt.append(deg * ((values[i] / a if a > 0 else 0.0) - (values[i + 1] / b if b > 0 else 0.0)))
        values = nxt
    return np.array(values[:count])


class _Rows:
    """Rows over unknown keys plus a fixed grip part, built from sector knots and reference rows."""

    def __init__(self, n, knots_i, knots_j, slot, fixed_row):
        self.n, self.knots_i, self.knots_j, self.slot, self.fixed_row = n, knots_i, knots_j, slot, fixed_row

    def pole(self, k, i, j, w, row, fixed):
        key = spoke_key(k, self.n, i, j)
        if key in self.slot:
            row[self.slot[key]] += w
        else:
            fixed += w * self.fixed_row(key)
        return fixed

    def functional(self, k, s, t, ds=0, dt=0):
        bi = deriv_basis(self.knots_i[k], s, ds)
        bj = deriv_basis(self.knots_j[k], t, dt)
        row = np.zeros(len(self.slot))
        fixed = 0.0
        for i in range(SIZE):
            for j in range(SIZE):
                w = bi[i] * bj[j]
                if w != 0.0:
                    fixed = self.pole(k, i, j, w, row, fixed)
        return row, fixed


def hard_rows(n, h, rows):
    """G1 (lambda profile), quadratic spokes on [h, 2h], C2 of pole rows 2 and 3 at 2h. Returns (A, F): A x + F = 0."""
    A, F = [], []
    lam0 = 2.0 * math.cos(2.0 * math.pi / n)
    samples = np.concatenate([np.linspace(0, h, 6), np.linspace(h, 2 * h, 6)])
    for k in range(n):
        for s in samples:
            ra, fa = rows.functional(k, s, 0.0, dt=1)
            rb, fb = rows.functional((k - 1) % n, 0.0, s, ds=1)
            rt, ft = rows.functional(k, s, 0.0, ds=1)
            lam = lam0 * lam_shape(s / h)
            A.append(ra + rb - lam * rt)
            F.append(fa + fb - lam * ft)
    for k in range(n):
        vals = [rows.functional(k, h + h * x / 3.0, 0.0) for x in range(4)]
        A.append(vals[3][0] - 3 * vals[2][0] + 3 * vals[1][0] - vals[0][0])
        F.append(vals[3][1] - 3 * vals[2][1] + 3 * vals[1][1] - vals[0][1])
    for k in range(n):
        for axis in ('s', 't'):
            knots = rows.knots_i[k] if axis == 's' else rows.knots_j[k]
            d = deriv_basis(knots, 2 * h, 2)[:SIZE] - deriv_basis(knots, 2 * h, 2, left=True)[:SIZE]
            for other in (2, 3):
                row = np.zeros(len(rows.slot))
                fixed = 0.0
                for i in range(SIZE):
                    if d[i] != 0:
                        ii, jj = (i, other) if axis == 's' else (other, i)
                        fixed = rows.pole(k, ii, jj, d[i], row, fixed)
                A.append(row)
                F.append(fixed)
    return np.array(A), F


def window_key(name, k, n):
    """Cap key of a local window name around spoke k."""
    if name[0] == 'S':
        s, i = name[1:].split('.')
        return ('spoke', (k + int(s)) % n, int(i))
    sector = k if name[0] == 'A' else k - 1
    return ('in', sector % n, int(name[1]), int(name[2]))


def key_ratio(key, r_i, r_j):
    """Knot ratio of the direction in which a cap key has index 4 (0 when it has none)."""
    if key[0] == 'spoke':
        return r_i[key[1]] if key[2] == 4 else 0.0
    if key[2] == 4:
        return r_i[key[1]]
    if key[3] == 4:
        return r_j[key[1]]
    return 0.0


def window_rows(n, keys, r_i, r_j):
    """The WINDOW relations of every spoke, as rows over keys (on delta). r_i[k], r_j[k]: knot ratios of sector k."""
    slot = {key: m for m, key in enumerate(keys)}
    c = math.cos(2 * math.pi / n)
    rows = []
    for k in range(n):
        for _, terms in WINDOW:
            row = np.zeros(len(keys))
            for name, *coef in terms:
                a, b, a2, b2 = (list(coef) + [0, 0, 0])[:4]
                key = window_key(name, k, n)
                r = key_ratio(key, r_i, r_j)
                row[slot[key]] += a + b * c + r * (a2 + b2 * c)
            rows.append(row)
    return np.array(rows)


def ring_rows(n, keys, r_spoke, netref):
    """Ring rule on delta, one row per spoke, with its right side from the net rows (netref(ep) = Limit)."""
    slot = {key: m for m, key in enumerate(keys)}
    c = math.cos(2 * math.pi / n)
    kappa = (n - 4) * c / (n + 5)
    K = len(keys)
    w = [ring_weights(r) for r in r_spoke]

    def sp(k, i):
        return slot[('spoke', k % n, i)]

    def L(k):
        v = np.zeros(K)
        v[slot[('in', k % n, 1, 1)]] += c
        for kk in (k, k + 1):
            b1, b2, b3 = w[kk % n]
            v[sp(kk, 2)] -= b2
            v[sp(kk, 3)] += b3
        return v
    ep = netref[slot[('ep',)]]
    tang = np.array([netref[sp(k, 1)] - ep for k in range(n)])
    mean = tang.mean(axis=0)
    rows, sides = [], []
    for k in range(n):
        v = (L(k - 1) + L(k)) / 2
        for kk, f in ((k - 1, 1), (k, 2), (k + 1, 1)):
            v[sp(kk, 1)] += f * w[kk % n][0]
        rows.append(v)
        sides.append(-kappa * tang[k] - 9 * c / (n + 5) * mean)
    return np.array(rows), np.array(sides)


def tangent_rows(n, keys, r_spoke):
    """Modes +-1 of T_k + c V_k on delta (two rows)."""
    slot = {key: m for m, key in enumerate(keys)}
    c = math.cos(2 * math.pi / n)
    rows = np.zeros((2, len(keys)))
    for k in range(n):
        b1, b2, b3 = ring_weights(r_spoke[k])
        v1, v2, v3 = tangent_weights(r_spoke[k])
        coef = (2 * b1 + c * v1, -b2 + c * v2, b3 + c * v3)
        for f, phase in enumerate((math.cos(2 * math.pi * k / n), math.sin(2 * math.pi * k / n))):
            for i in (1, 2, 3):
                rows[f, slot[('spoke', k, i)]] += phase * coef[i - 1]
    return rows


def alternating_rows(n, keys, netref):
    """Even n: sum_k (-1)^k delta A11_k = -((n-4)/(n+5)) sum_k (-1)^k netref A11_k."""
    slot = {key: m for m, key in enumerate(keys)}
    row = np.zeros(len(keys))
    for k in range(n):
        row[slot[('in', k, 1, 1)]] = (-1) ** k
    return row[None, :], (-((n - 4) / (n + 5)) * (row @ netref))[None, :]


def _get(obj, name):
    return obj[name] if isinstance(obj, dict) else getattr(obj, name)


def cap_rows(request):
    """Pole rows {key: {grip: coefficient}} for every unknown cap key of one EP (see module doc)."""
    n = _get(request, 'Valence')
    creased = _get(request, 'Creased') if (isinstance(request, dict) and 'Creased' in request) or hasattr(request, 'Creased') else ()
    if any(creased):
        raise ValueError('cap rule covers smooth EPs only')
    keys = cap_keys(n)
    unknown = set(_get(request, 'Unknown'))
    if unknown != set(keys):
        raise ValueError('cap rule expects the reach-4 cap keys as unknowns')
    reference = _get(request, 'Reference')
    limit = _get(request, 'Limit')
    if limit is None:
        raise ValueError('cap rule needs the limit row')
    sectors = _get(request, 'Sectors')
    knots_i = [expand_knots(_get(s, 'KnotsI')) for s in sectors]
    knots_j = [expand_knots(_get(s, 'KnotsJ')) for s in sectors]
    h = knots_i[0][4]
    grips = sorted({g for row in reference.values() for g in row} | set(limit))
    col = {g: m for m, g in enumerate(grips)}

    def dense(row):
        out = np.zeros(len(grips))
        for g, v in row.items():
            out[col[g]] += v
        return out

    def fixed_row(key):
        if key not in reference:
            raise ValueError('cap rule needs the reference row of %r' % (key,))
        return dense(reference[key])
    slot = {key: m for m, key in enumerate(keys)}
    netref = np.array([dense(limit) if key == ('ep',) else dense(reference[key]) for key in keys])
    r_i = [knot_ratio(kn, h) for kn in knots_i]
    r_j = [knot_ratio(kn, h) for kn in knots_j]
    for k in range(n):
        if abs(r_i[k] - r_j[(k - 1) % n]) > 1e-9:
            raise ValueError('cap rule: the two sides of spoke %d see different spans after 2h' % k)
    rows = _Rows(n, knots_i, knots_j, slot, fixed_row)
    A, F = hard_rows(n, h, rows)
    F = np.array([f if isinstance(f, np.ndarray) else np.zeros(len(grips)) for f in F])
    ep = np.zeros((1, len(keys)))
    ep[0, slot[('ep',)]] = 1.0
    blocks = [A, ep]
    sides = [-F, dense(limit)[None, :]]
    W = window_rows(n, keys, r_i, r_j)
    Rr, Rs = ring_rows(n, keys, r_i, netref)
    T = tangent_rows(n, keys, r_i)
    on_delta = [(W, np.zeros((W.shape[0], len(grips)))), (Rr, Rs), (T, np.zeros((2, len(grips))))]
    if n % 2 == 0:
        on_delta.append(alternating_rows(n, keys, netref))
    for M, side in on_delta:
        blocks.append(M)
        sides.append(side + M @ netref)
    C = np.vstack(blocks)
    B = np.vstack(sides)
    scale = np.abs(C).max(axis=1, keepdims=True)
    scale[scale == 0] = 1
    C, B = C / scale, B / scale
    u, s, vt = np.linalg.svd(C, full_matrices=False)
    rank = int((s > 1e-9 * s[0]).sum())
    if rank < len(keys):
        raise ValueError('cap rule leaves %d free directions' % (len(keys) - rank))
    x = vt.T @ ((u.T @ B) / s[:, None])
    return {key: {g: float(v) for g, v in zip(grips, x[m]) if v != 0.0} for m, key in enumerate(keys)}
