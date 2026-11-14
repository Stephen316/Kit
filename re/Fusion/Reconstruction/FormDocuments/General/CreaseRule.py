"""Research crease cap rule: Fusion's cap poles at an EP with exactly one creased spoke (n = 3 or n >= 5).

Entry point crease_cap_rows(request), the same request as CapRule.cap_rows (CapInput fields). Derivation and evidence
are in CreaseRuleNotes.md. Unknowns are delta = pole - netref (netref(ep) = Limit); the crease is spoke k0.

- delta = 0 at the EP, on spoke k0 (i = 1..4), on (in, k0, i, 1) and (in, k0-1, 1, i) (i = 2..4);
- hard rows of CapRule without G1 and the quadratic-spoke row of spoke k0;
- WINDOW rows without cross-even at k0 and cross-odd at k0 +- 1, plus odd@(k0+1) + odd@(k0-1) = 0;
- ring rows with nS1_k0 replaced by V = (nA11_k0 + nA11_k0-1) / 2 on the right side;
- the mode-1 tangent row odd about spoke k0; the alternating twist for even n;
- the w0 relation (W0 below) and the odd@(k0+1) relation (odd_side below).
"""
import math

import numpy as np

import CapRule

# w0 relation on delta: (kind, i, j, a, b) with coefficient a + b c. 'S' terms take spokes k0 +- 1, pole j;
# 'A' terms take (in, k0, i, j) + (in, k0-1, j, i).
W0 = (('S', 0, 1, 0.0, -1 / 40), ('S', 0, 2, 3 / 160, 1 / 20), ('S', 0, 3, -3 / 32, 1 / 20),
      ('A', 1, 2, -3 / 160, 3 / 20), ('A', 1, 3, 3 / 32, 0.0), ('A', 2, 2, 0.0, -4 / 5), ('A', 3, 2, 0.0, 1.0))


def odd_side(n, k0, net):
    """Right side of odd@(k0+1) . delta; net(key) gives the net row (net(('ep',)) = Limit)."""
    c = math.cos(2 * math.pi / n)
    ep = net(('ep',))
    at = lambda k, i, j: net(('in', (k0 + k) % n, i, j))
    U1 = 0.5 * (at(0, 1, 1) + at(-1, 1, 1)) - net(('spoke', k0, 1))
    U2 = 0.5 * (at(0, 2, 1) + at(-1, 1, 2)) - net(('spoke', k0, 2))
    A11 = sum(at(k, 1, 1) - ep for k in range(n))
    A12 = sum(at(k, 1, 2) + at(k, 2, 1) - 2 * ep for k in range(n)) / 2
    A22 = sum(at(k, 2, 2) - ep for k in range(n))
    if n == 3:
        return -102 / 5 * A11 + 13 / 10 * U1 - 1 / 5 * U2
    u = 16 * c / (n * (n - 3))
    return u * (U1 - 2 * U2 + A22 - (5 * n + 7) / (2 * (4 * n - 7)) * (4 * A12 - A22))


def crease_delta_rows(n, k0, keys, r_i, r_j, netref):
    """Rows on delta with their right sides (grip rows), everything except the hard rows."""
    slot = {key: m for m, key in enumerate(keys)}
    c = math.cos(2 * math.pi / n)
    G = netref.shape[1]
    net = lambda key: netref[slot[key]]
    rows, sides = [], []

    def add(row, side=None):
        rows.append(row)
        sides.append(np.zeros(G) if side is None else side)
    pinned = [('spoke', k0, i) for i in range(1, 5)] + [('in', k0, i, 1) for i in range(2, 5)]
    pinned += [('in', (k0 - 1) % n, 1, i) for i in range(2, 5)]
    for key in pinned:
        add(np.eye(len(keys))[slot[key]])
    names = [nm for nm, _ in CapRule.WINDOW]
    m = len(names)
    W = CapRule.window_rows(n, keys, r_i, r_j)
    odd = names.index('cross-spoke odd')
    for k in range(n):
        for t, nm in enumerate(names):
            if (nm == 'cross-spoke even' and k == k0) or (t == odd and k in ((k0 + 1) % n, (k0 - 1) % n)):
                continue
            add(W[m * k + t])
    upper, lower = W[m * ((k0 + 1) % n) + odd], W[m * ((k0 - 1) % n) + odd]
    add(upper + lower)
    add(upper, odd_side(n, k0, net))
    smoothed = netref.copy()
    smoothed[slot[('spoke', k0, 1)]] = 0.5 * (net(('in', k0, 1, 1)) + net(('in', (k0 - 1) % n, 1, 1)))
    Rr, _ = CapRule.ring_rows(n, keys, r_i, netref)
    _, Rs = CapRule.ring_rows(n, keys, r_i, smoothed)
    for row, side in zip(Rr, Rs):
        add(row, side)
    T = CapRule.tangent_rows(n, keys, r_i)
    a = 2 * math.pi * k0 / n
    add(math.cos(a) * T[1] - math.sin(a) * T[0])
    if n % 2 == 0:
        Ar, As = CapRule.alternating_rows(n, keys, netref)
        add(Ar[0], As[0])
    w0 = np.zeros(len(keys))
    for kind, i, j, a0, b0 in W0:
        if kind == 'S':
            pair = [('spoke', (k0 + 1) % n, j), ('spoke', (k0 - 1) % n, j)]
        else:
            pair = [('in', k0, i, j), ('in', (k0 - 1) % n, j, i)]
        for key in dict.fromkeys(pair):
            w0[slot[key]] += a0 + b0 * c
    add(w0)
    return np.array(rows), np.array(sides)


def crease_cap_rows(request):
    """Pole rows {key: {grip: coefficient}} for every cap key of one EP with exactly one creased spoke."""
    get = CapRule._get
    n = get(request, 'Valence')
    creased = tuple(get(request, 'Creased'))
    if sum(creased) != 1 or n == 4:
        raise ValueError('crease rule covers one creased spoke at an EP of valence 3 or >= 5')
    k0 = creased.index(True)
    keys = CapRule.cap_keys(n)
    if set(get(request, 'Unknown')) != set(keys):
        raise ValueError('crease rule expects the reach-4 cap keys as unknowns')
    reference, limit = get(request, 'Reference'), get(request, 'Limit')
    sectors = get(request, 'Sectors')
    knots_i = [CapRule.expand_knots(get(s, 'KnotsI')) for s in sectors]
    knots_j = [CapRule.expand_knots(get(s, 'KnotsJ')) for s in sectors]
    h = knots_i[0][4]
    grips = sorted({g for row in reference.values() for g in row} | set(limit))
    col = {g: m for m, g in enumerate(grips)}

    def dense(row):
        out = np.zeros(len(grips))
        for g, v in row.items():
            out[col[g]] += v
        return out
    slot = {key: m for m, key in enumerate(keys)}

    def net_row(key):
        """Reference row; a missing pole 1 is extrapolated as 2 P2 - 2 P3 + P4 along its line (src PolarPole)."""
        if key in reference:
            return dense(reference[key])
        steps = ((2.0, 2), (-2.0, 3), (1.0, 4))
        if key[0] == 'spoke':
            return sum(a * dense(reference[('spoke', key[1], i)]) for a, i in steps)
        if key[2] == 1:
            return sum(a * dense(reference[('in', key[1], i, key[3])]) for a, i in steps)
        return sum(a * dense(reference[('in', key[1], key[2], i)]) for a, i in steps)
    netref = np.array([dense(limit) if key == ('ep',) else net_row(key) for key in keys])
    r_i = [CapRule.knot_ratio(kn, h) for kn in knots_i]
    r_j = [CapRule.knot_ratio(kn, h) for kn in knots_j]
    if any(abs(r - 2 / 3) > 1e-9 for r in r_i + r_j):
        raise ValueError('crease rule was measured at knot ratio 2/3 only')
    A, F = CapRule.hard_rows(n, h, CapRule._Rows(n, knots_i, knots_j, slot, lambda key: dense(reference[key])))
    F = np.array([f if isinstance(f, np.ndarray) else np.zeros(len(grips)) for f in F])
    keep = [t for t in range(len(A)) if not (12 * k0 <= t < 12 * k0 + 12 or t == 12 * n + k0)]
    ep = np.zeros((1, len(keys)))
    ep[0, slot[('ep',)]] = 1.0
    M, S = crease_delta_rows(n, k0, keys, r_i, r_j, netref)
    C = np.vstack([A[keep], ep, M])
    B = np.vstack([-F[keep], dense(limit)[None, :], S + M @ netref])
    scale = np.abs(C).max(axis=1, keepdims=True)
    C, B = C / scale, B / scale
    u, s, vt = np.linalg.svd(C, full_matrices=False)
    rank = int((s > 1e-9 * s[0]).sum())
    if rank < len(keys):
        raise ValueError('crease rule leaves %d free directions' % (len(keys) - rank))
    x = vt.T @ ((u.T @ B) / s[:, None])
    return {key: {g: float(v) for g, v in zip(grips, x[m]) if v != 0.0} for m, key in enumerate(keys)}
