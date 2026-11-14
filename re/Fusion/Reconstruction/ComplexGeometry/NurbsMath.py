"""Independent research-side NURBS evaluation for acceptance expectations.

This deliberately does not reuse production SplineEval so that the expected
values cross-check the production evaluator. It works on clamped knot vectors
with end multiplicity degree + 1, the convention the Fusion API reports.
"""
import math


def full_knots(knots, multiplicity, degree):
    expanded = [value for value, count in zip(knots, multiplicity) for _ in range(count)]
    lead = degree + 1 - multiplicity[0]
    tail = degree + 1 - multiplicity[-1]
    return [knots[0]] * lead + expanded + [knots[-1]] * tail


def find_span(degree, vector, count, parameter):
    if parameter >= vector[count]:
        span = count - 1
        while vector[span] >= vector[span + 1]:
            span -= 1
        return span
    span = degree
    while vector[span + 1] <= parameter:
        span += 1
    return span


def basis(degree, vector, count, parameter):
    span = find_span(degree, vector, count, parameter)
    values = [0.0] * count
    local = [1.0]
    for level in range(1, degree + 1):
        nxt = [0.0] * (level + 1)
        for offset in range(level):
            index = span - level + 1 + offset
            width = vector[index + level] - vector[index]
            if width > 0:
                ratio = local[offset] / width
                nxt[offset] += ratio * (vector[index + level] - parameter)
                nxt[offset + 1] += ratio * (parameter - vector[index])
        local = nxt
    for offset, value in enumerate(local):
        values[span - degree + offset] = value
    return values


def basis_derivative(degree, vector, count, parameter):
    if degree == 0:
        return [0.0] * count
    lower = basis(degree - 1, vector, count + 1, parameter)
    result = [0.0] * count
    for index in range(count):
        left_width = vector[index + degree] - vector[index]
        right_width = vector[index + degree + 1] - vector[index + 1]
        if left_width > 0:
            result[index] += degree * lower[index] / left_width
        if right_width > 0:
            result[index] -= degree * lower[index + 1] / right_width
    return result


class Surface:
    def __init__(self, udeg, vdeg, uknots, umult, vknots, vmult, poles, weights):
        self.udeg, self.vdeg = udeg, vdeg
        self.uvec = full_knots(uknots, umult, udeg)
        self.vvec = full_knots(vknots, vmult, vdeg)
        self.ucount = len(self.uvec) - udeg - 1
        self.vcount = len(self.vvec) - vdeg - 1
        if len(poles) != self.ucount * self.vcount:
            raise ValueError('pole count mismatch')
        self.poles = poles
        self.weights = weights or [1.0] * len(poles)
        self.domain = (uknots[0], uknots[-1], vknots[0], vknots[-1])

    def derivatives(self, u, v):
        nu = basis(self.udeg, self.uvec, self.ucount, u)
        nv = basis(self.vdeg, self.vvec, self.vcount, v)
        du = basis_derivative(self.udeg, self.uvec, self.ucount, u)
        dv = basis_derivative(self.vdeg, self.vvec, self.vcount, v)
        sums = [[0.0] * 4 for _ in range(3)]
        for row in range(self.vcount):
            for col in range(self.ucount):
                index = row * self.ucount + col
                weight = self.weights[index]
                lifted = [*(value * weight for value in self.poles[index]), weight]
                for slot, factor in enumerate((nu[col] * nv[row], du[col] * nv[row], nu[col] * dv[row])):
                    if factor:
                        for axis in range(4):
                            sums[slot][axis] += factor * lifted[axis]
        point = [value / sums[0][3] for value in sums[0][:3]]
        tangents = [[(sums[slot][axis] - point[axis] * sums[slot][3]) / sums[0][3] for axis in range(3)] for slot in (1, 2)]
        return point, tangents[0], tangents[1]

    def point(self, u, v):
        return self.derivatives(u, v)[0]

    def spans(self):
        ubreaks = sorted(set(self.uvec))
        vbreaks = sorted(set(self.vvec))
        return list(zip(ubreaks, ubreaks[1:])), list(zip(vbreaks, vbreaks[1:]))


def legendre(order):
    nodes = []
    for index in range(1, order + 1):
        guess = math.cos(math.pi * (index - 0.25) / (order + 0.5))
        for _ in range(100):
            prior, current = 1.0, guess
            for degree in range(2, order + 1):
                prior, current = current, ((2 * degree - 1) * guess * current - (degree - 1) * prior) / degree
            slope = order * (guess * current - prior) / (guess * guess - 1)
            step = current / slope
            guess -= step
            if abs(step) < 1e-16:
                break
        prior, current = 1.0, guess
        for degree in range(2, order + 1):
            prior, current = current, ((2 * degree - 1) * guess * current - (degree - 1) * prior) / degree
        slope = order * (guess * current - prior) / (guess * guess - 1)
        nodes.append((guess, 2 / ((1 - guess * guess) * slope * slope)))
    return nodes


def cross(first, second):
    return [first[1] * second[2] - first[2] * second[1], first[2] * second[0] - first[0] * second[2], first[0] * second[1] - first[1] * second[0]]


def integrate(surface, order=12, pieces=4):
    rule = legendre(order)
    totals = dict(area=0.0, volume=0.0, moment=[0.0, 0.0, 0.0])
    uspans, vspans = surface.spans()
    for ulow, uhigh in uspans:
        for vlow, vhigh in vspans:
            for upiece in range(pieces):
                for vpiece in range(pieces):
                    ua = ulow + (uhigh - ulow) * upiece / pieces
                    ub = ulow + (uhigh - ulow) * (upiece + 1) / pieces
                    va = vlow + (vhigh - vlow) * vpiece / pieces
                    vb = vlow + (vhigh - vlow) * (vpiece + 1) / pieces
                    for unode, uweight in rule:
                        for vnode, vweight in rule:
                            u = (ua + ub) / 2 + (ub - ua) / 2 * unode
                            v = (va + vb) / 2 + (vb - va) / 2 * vnode
                            scale = uweight * vweight * (ub - ua) * (vb - va) / 4
                            point, su, sv = surface.derivatives(u, v)
                            normal = cross(su, sv)
                            totals['area'] += scale * math.sqrt(sum(value * value for value in normal))
                            totals['volume'] += scale * sum(point[axis] * normal[axis] for axis in range(3)) / 3
                            for axis in range(3):
                                totals['moment'][axis] += scale * point[axis] * point[axis] * normal[axis] / 2
    return totals


def sample_bounds(surface, count=61):
    ulow, uhigh, vlow, vhigh = surface.domain
    points = [surface.point(ulow + (uhigh - ulow) * i / (count - 1), vlow + (vhigh - vlow) * j / (count - 1)) for i in range(count) for j in range(count)]
    return [[min(point[axis] for point in points) for axis in range(3)], [max(point[axis] for point in points) for axis in range(3)]]


def fusion_order(surface):
    """Fusion NurbsSurface.getData lists poles u-major (index = u * countV + v)."""
    poles = [surface.poles[row * surface.ucount + col] for col in range(surface.ucount) for row in range(surface.vcount)]
    weights = [surface.weights[row * surface.ucount + col] for col in range(surface.ucount) for row in range(surface.vcount)]
    return poles, weights
