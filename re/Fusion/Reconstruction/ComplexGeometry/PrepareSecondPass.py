"""Prepare the second native acceptance pass for complex ASM geometry.

Two inputs are written under re/Fusion/LocalOracle/ComplexGeometry/SecondPass.

Authored: the wider NURBS models of tests/.../Complex/WiderNurbs.py (holes, a pole
collapsed side, periodic seams, analytic plane and cylinder faces sharing edges with
NURBS faces, and a doubly periodic torus) emitted through CreateNurbsBody, with
expected mass properties from independent integration or closed forms.

Subtypes: corpus bodies that hold subtypes Fusion had never opened, each written
once unchanged and once with exactly one typed record edited through the typed
codec. Native cases keep the geometry consistent: spline values are refined by one
knot insertion (same shape, one more pole), and tolerances only grow within the
ACIS ordering (tvertex at least its tedges). Edits that are inconsistent by
construction carry native=False, are never sent to Fusion and are not written; only
their digest is kept. Kit's own emit checks refuse some of them, and the refusal is
recorded instead. Every case
states what the Fusion API should report.

Run with /opt/homebrew/bin/python3.14 -I (ZIP method 93 needs Python 3.14).
"""

import collections
import dataclasses
import hashlib
import json
import math
import sys
import zipfile
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE))

from convert.formats.Fusion.BrepCodec.Journal.Attributes.StitchAttrib import StitchAttrib  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.Attributes.VertedgeAttrib import VertedgeAttrib  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.Complex.Authoring.CreateNurbsBody import CreateNurbsBody  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.Complex.Authoring.NurbsBody import CylinderCarrier, PlaneCarrier  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.Complex.Authoring.SplineEval import PointOnSurface  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.Complex.Grammar.GrammarValue import SubtypeNode  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.Complex.Nodes.TcoedgeNode import TcoedgeNode  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.Complex.Nodes.TedgeNode import TedgeNode  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.Complex.Nodes.TvertexNode import TvertexNode  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.Complex.Spline.BsCurve import BsCurve  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.Complex.Spline.BsSurface import BsSurface  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.EmitJournal import EmitJournal  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.EmitStateSmb import EmitStateSmb  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.ReadJournal import ReadJournal  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.Snapshot.EmitGeometry import EmitGeometry  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.Snapshot.ReadGeometry import ReadGeometry  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.Spline.IntcurveNode import IntcurveNode  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.Spline.ListSubtypes import ListSubtypes  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.Spline.PcurveNode import PcurveNode  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.Spline.SplineNode import SplineNode  # noqa: E402
from tests.convert.formats.FusionCodec.Brep.Complex.NurbsSamples import KNurbsHistory, KNurbsStamp  # noqa: E402
from tests.convert.formats.FusionCodec.Brep.Complex.WiderNurbs import KDomeProfile, KHoleBox, KTorusMajor, KTorusMinor, KTubeProfile, WiderModels  # noqa: E402

import NurbsMath  # noqa: E402

OUT = ROOT / "re/Fusion/LocalOracle/ComplexGeometry/SecondPass"
STUDY = ROOT / "re/Fusion/Study"
ORIGINALS = {
    "lofts-03b4a6f1ce2f/centerline.f3d": "ClLoft",
    "solidsweeps-7d2677669e3d/solid_rigid.f3d": "SumSpl",
    "embosstext-cd769aa41cdf/two_texts.f3d": "CylSpl",
    "sweepnurbspaths-7ded30a4b9ae/polynomial_cubic.f3d": "PcurveForms",
    "solidsweeps-7d2677669e3d/solid_twist.f3d": "Tolerant",
    "patchcontinuity-b9b0be85a281/brep_curvature.f3d": "Stitch",
    "splines-9a18bae21127/splines.f3d": "Vertedge",
    "rulefilletsurfaces-7b26b40f98f7/offsets_one_two_witnesses.f3d": "RuleOffsets",
}
NURBS, PLANE, CYLINDER = "adsk::core::NurbsSurface", "adsk::core::Plane", "adsk::core::Cylinder"
SCOPES = {
    "HoledPatch": "Open bicubic sheet with a rectangular inner loop of four iso-parameter edges with bounded ranges",
    "CollapsedPatch": "Bicubic sheet whose high V pole row collapses to one apex (VSingular 2), three edges and no edge on the singular side",
    "CappedTube": "Closed solid: U-periodic rational revolved NURBS side with a seam edge used twice, plus two planar caps without pcurves",
    "DomedCylinder": "Closed solid: analytic cylinder face with two loops, planar bottom and a U-periodic NURBS dome collapsing to an apex",
    "NurbsTorus": "Closed solid: one doubly periodic rational biquadratic face, one vertex and two seam edges with U and V offsets",
}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def relative(path):
    return str(path.relative_to(ROOT))


def research_surface(value):
    return NurbsMath.Surface(value.UDegree, value.VDegree, value.UKnots, value.UMultiplicity, value.VKnots, value.VMultiplicity, list(value.Poles), list(value.Weights))


def fusion_poles(value):
    poles, weights = NurbsMath.fusion_order(research_surface(value))
    return [list(point) for point in poles], list(weights)


def gauss(order):
    return NurbsMath.legendre(order)


def box_totals(surface, ulow, uhigh, vlow, vhigh, order=16, pieces=4):
    rule = gauss(order)
    ubreaks = sorted({ulow, uhigh} | {value for value in surface.uvec if ulow < value < uhigh})
    vbreaks = sorted({vlow, vhigh} | {value for value in surface.vvec if vlow < value < vhigh})
    area = 0.0
    for ua, ub in zip(ubreaks, ubreaks[1:]):
        for va, vb in zip(vbreaks, vbreaks[1:]):
            for i in range(pieces):
                for j in range(pieces):
                    u0, u1 = ua + (ub - ua) * i / pieces, ua + (ub - ua) * (i + 1) / pieces
                    v0, v1 = va + (vb - va) * j / pieces, va + (vb - va) * (j + 1) / pieces
                    for un, uw in rule:
                        for vn, vw in rule:
                            u = (u0 + u1) / 2 + (u1 - u0) / 2 * un
                            v = (v0 + v1) / 2 + (v1 - v0) / 2 * vn
                            _, su, sv = surface.derivatives(u, v)
                            normal = NurbsMath.cross(su, sv)
                            area += uw * vw * (u1 - u0) * (v1 - v0) / 4 * math.sqrt(sum(x * x for x in normal))
    return area


def bezier(profile, t):
    count = len(profile) - 1
    point = [0.0, 0.0]
    slope = [0.0, 0.0]
    for index, (radius, height) in enumerate(profile):
        weight = math.comb(count, index) * t ** index * (1 - t) ** (count - index)
        point[0] += weight * radius
        point[1] += weight * height
    for index in range(count):
        weight = count * math.comb(count - 1, index) * t ** index * (1 - t) ** (count - 1 - index)
        slope[0] += weight * (profile[index + 1][0] - profile[index][0])
        slope[1] += weight * (profile[index + 1][1] - profile[index][1])
    return point, slope


def pappus(profile, order=24, pieces=16):
    rule = gauss(order)
    totals = dict(volume=0.0, area=0.0, moment=0.0)
    for piece in range(pieces):
        a, b = piece / pieces, (piece + 1) / pieces
        for node, weight in rule:
            t = (a + b) / 2 + (b - a) / 2 * node
            scale = weight * (b - a) / 2
            (radius, height), (dr, dz) = bezier(profile, t)
            totals["volume"] += scale * math.pi * radius * radius * dz
            totals["moment"] += scale * math.pi * radius * radius * height * dz
            totals["area"] += scale * 2 * math.pi * radius * math.hypot(dr, dz)
    return totals


def divergence(model):
    area = volume = 0.0
    moment = [0.0, 0.0, 0.0]
    for face in model.Faces:
        if isinstance(face.Surface, BsSurface):
            totals = NurbsMath.integrate(research_surface(face.Surface), order=16, pieces=6)
            area += totals["area"]
            volume += totals["volume"]
            moment = [m + t for m, t in zip(moment, totals["moment"])]
    return area, volume, moment


def describe_surface(value, label, extra=()):
    surface = research_surface(value)
    poles, weights = fusion_poles(value)
    ulow, uhigh, vlow, vhigh = surface.domain
    grid = [(ulow + (uhigh - ulow) * a, vlow + (vhigh - vlow) * b) for a in (0.13, 0.5, 0.87) for b in (0.21, 0.5, 0.79)] + list(extra)
    samples = []
    for u, v in grid:
        expected = surface.point(u, v)
        production = PointOnSurface(value, u, v)
        if max(abs(a - b) for a, b in zip(expected, production)) > 1e-12:
            raise RuntimeError("Production and research evaluators disagree")
        samples.append(dict(uv=[u, v], pointCm=expected))
    return dict(label=label, degreeU=value.UDegree, degreeV=value.VDegree, countU=surface.ucount, countV=surface.vcount, knotsU=surface.uvec, knotsV=surface.vvec, rational=value.Rational, closureU=value.UClosure, closureV=value.VClosure, singularU=value.USingular, singularV=value.VSingular, controlPointsCm=poles, weights=weights if value.Rational else [], samples=samples)


def expected_coedges(model):
    found = []
    for face_index, face in enumerate(model.Faces):
        if not isinstance(face.Surface, BsSurface):
            continue
        for loop in (face.Uses, *face.Holes):
            for use in loop:
                poles = list(use.Pcurve.Poles)[::-1] if use.Reversed else list(use.Pcurve.Poles)
                found.append(dict(face=face_index, edge=use.EdgeIndex, reversed=use.Reversed, offset=[use.OffsetU, use.OffsetV], controlPoints=[[p[0] + use.OffsetU, p[1] + use.OffsetV] for p in poles]))
    return found


def face_type(face):
    if isinstance(face.Surface, BsSurface):
        return NURBS
    return PLANE if isinstance(face.Surface, PlaneCarrier) else CYLINDER


def expected_body(label, model):
    edges_used = collections.Counter(use.EdgeIndex for face in model.Faces for loop in (face.Uses, *face.Holes) for use in loop)
    solid = all(count == 2 for count in edges_used.values())
    result = dict(solid=solid, faces=len(model.Faces), edges=len(model.Edges), vertices=len(model.PointsCm), faceTypes=sorted(face_type(face) for face in model.Faces), verticesCm=[list(point) for point in model.PointsCm])
    spline_faces = [face.Surface for face in model.Faces if isinstance(face.Surface, BsSurface)]
    extra = [(0.45, 0.5), (0.15, 0.2)] if label == "HoledPatch" else []
    surfaces = [describe_surface(value, f"face{index}", extra) for index, value in enumerate(spline_faces)]
    if label == "HoledPatch":
        ulow, uhigh, vlow, vhigh = KHoleBox
        for surface in surfaces:
            for sample in surface["samples"]:
                u, v = sample["uv"]
                sample["onFace"] = not (ulow < u < uhigh and vlow < v < vhigh)
        full = box_totals(research_surface(spline_faces[0]), 0.0, 1.0, 0.0, 1.0)
        hole = box_totals(research_surface(spline_faces[0]), ulow, uhigh, vlow, vhigh)
        result.update(areaCm2=full - hole, method="Gauss-Legendre over the full patch minus the hole box", fullAreaCm2=full, holeAreaCm2=hole)
    elif label == "CollapsedPatch":
        result.update(areaCm2=box_totals(research_surface(spline_faces[0]), 0.0, 1.0, 0.0, 1.0), method="Gauss-Legendre over the full patch")
    elif label == "CappedTube":
        side = pappus(KTubeProfile)
        bottom, top = KTubeProfile[0], KTubeProfile[-1]
        caps_area = math.pi * bottom[0] ** 2 + math.pi * top[0] ** 2
        volume = side["volume"]
        moment = side["moment"]
        result.update(areaCm2=side["area"] + caps_area, volumeCm3=volume, centerCm=[0.0, 0.0, moment / volume], method="Pappus integrals of the cubic profile plus disc caps")
        nurbs_area, nurbs_volume, nurbs_moment = divergence(model)
        cap_volume = top[1] * math.pi * top[0] ** 2 / 3 - bottom[1] * math.pi * bottom[0] ** 2 / 3
        cap_moment = top[1] ** 2 * math.pi * top[0] ** 2 / 2 - bottom[1] ** 2 * math.pi * bottom[0] ** 2 / 2
        result["crossCheck"] = dict(divergenceAreaCm2=nurbs_area + caps_area, divergenceVolumeCm3=nurbs_volume + cap_volume, divergenceCenterZ=(nurbs_moment[2] + cap_moment) / (nurbs_volume + cap_volume))
    elif label == "DomedCylinder":
        dome = pappus(KDomeProfile)
        rim = KDomeProfile[0]
        radius, height = rim
        volume = math.pi * radius ** 2 * height + dome["volume"]
        moment = math.pi * radius ** 2 * height * height / 2 + dome["moment"]
        result.update(areaCm2=math.pi * radius ** 2 + 2 * math.pi * radius * height + dome["area"], volumeCm3=volume, centerCm=[0.0, 0.0, moment / volume], method="Closed-form cylinder and disc plus Pappus integrals of the cubic dome profile")
        nurbs_area, nurbs_volume, nurbs_moment = divergence(model)
        cylinder_volume = 2 * math.pi * radius ** 2 * height / 3
        result["crossCheck"] = dict(divergenceAreaCm2=nurbs_area + math.pi * radius ** 2 + 2 * math.pi * radius * height, divergenceVolumeCm3=nurbs_volume + cylinder_volume, divergenceCenterZ=nurbs_moment[2] / (nurbs_volume + cylinder_volume))
    elif label == "NurbsTorus":
        result.update(areaCm2=4 * math.pi ** 2 * KTorusMajor * KTorusMinor, volumeCm3=2 * math.pi ** 2 * KTorusMajor * KTorusMinor ** 2, centerCm=[0.0, 0.0, 0.0], method="Closed-form torus area and volume")
        nurbs_area, nurbs_volume, nurbs_moment = divergence(model)
        result["crossCheck"] = dict(divergenceAreaCm2=nurbs_area, divergenceVolumeCm3=nurbs_volume, divergenceCenter=[value / nurbs_volume for value in nurbs_moment])
    if "crossCheck" in result:
        check = result["crossCheck"]
        drift = max(abs(check["divergenceAreaCm2"] - result["areaCm2"]) / result["areaCm2"], abs(check["divergenceVolumeCm3"] - result["volumeCm3"]) / result["volumeCm3"])
        check["relativeDrift"] = drift
        if drift > 1e-9:
            raise RuntimeError(label + " closed-form and divergence integrals disagree by " + str(drift))
    result["surfaces"] = surfaces
    result["coedges"] = expected_coedges(model)
    return result


def prepare_authored(report):
    folder = OUT / "Authored"
    folder.mkdir(parents=True, exist_ok=True)
    for label, model in WiderModels():
        journal = CreateNurbsBody(model, KNurbsHistory, KNurbsStamp)
        history = EmitJournal(journal)
        payload = EmitStateSmb(journal)
        if ReadJournal(history) != journal or ReadGeometry(payload).Entities != journal.Entities or EmitGeometry(ReadGeometry(payload)) != payload:
            raise RuntimeError(label + " does not reread to the same typed model")
        (folder / (label + ".smb")).write_bytes(payload)
        (folder / (label + ".smbh")).write_bytes(history)
        report["authored"].append(dict(label=label, scope=SCOPES[label], target=relative(folder / (label + ".smb")), targetSha256=digest(payload), history=relative(folder / (label + ".smbh")), historySha256=digest(history), records=len(journal.Entities), expected=expected_body(label, model)))
        print(label, digest(payload), flush=True)


def paths(value, predicate, trail=()):
    if predicate(value):
        yield trail
    if isinstance(value, tuple):
        for index, item in enumerate(value):
            yield from paths(item, predicate, trail + (index,))
    elif dataclasses.is_dataclass(value) and not isinstance(value, type) and not isinstance(value, (BsCurve, BsSurface)):
        for field in dataclasses.fields(value):
            yield from paths(getattr(value, field.name), predicate, trail + (field.name,))


def get_at(value, trail):
    for step in trail:
        value = value[step] if isinstance(step, int) else getattr(value, step)
    return value


def set_at(value, trail, new):
    if not trail:
        return new
    step, rest = trail[0], trail[1:]
    if isinstance(step, int):
        items = list(value)
        items[step] = set_at(items[step], rest, new)
        return tuple(items)
    return dataclasses.replace(value, **{step: set_at(getattr(value, step), rest, new)})


def read_member(relative_path, suffix):
    with zipfile.ZipFile(STUDY / relative_path) as archive:
        names = [name for name in archive.namelist() if name.endswith(suffix)]
        if len(names) != 1:
            raise RuntimeError("Expected one " + suffix + " member in " + relative_path)
        return names[0], archive.read(names[0])


def full_vector(knots, multiplicity, degree):
    return NurbsMath.full_knots(knots, multiplicity, degree)


def refine_parameter(knots):
    spans = [(low, high) for low, high in zip(knots, knots[1:]) if high > low]
    low, high = max(spans, key=lambda span: span[1] - span[0])
    return (low + high) / 2.0


def insert_row(vector, degree, points, weights, parameter, rational):
    """Boehm knot insertion on one row; poles outside the affected window are copied exactly."""
    count = len(points)
    span = NurbsMath.find_span(degree, vector, count, parameter)
    new_points, new_weights = [], []
    for index in range(count + 1):
        if index <= span - degree or index > span:
            source = index if index <= span - degree else index - 1
            new_points.append(tuple(points[source]))
            new_weights.append(weights[source])
            continue
        alpha = (parameter - vector[index]) / (vector[index + degree] - vector[index])
        upper, lower = weights[index], weights[index - 1]
        if not rational:
            new_points.append(tuple(alpha * a + (1.0 - alpha) * b for a, b in zip(points[index], points[index - 1])))
            new_weights.append(1.0)
            continue
        weight = upper if upper == lower else alpha * upper + (1.0 - alpha) * lower
        new_points.append(tuple((alpha * upper * a + (1.0 - alpha) * lower * b) / weight for a, b in zip(points[index], points[index - 1])))
        new_weights.append(weight)
    return new_points, new_weights


def insert_value(knots, multiplicity, parameter):
    position = next(index for index, value in enumerate(knots) if value > parameter)
    return tuple(knots[:position]) + (parameter,) + tuple(knots[position:]), tuple(multiplicity[:position]) + (1,) + tuple(multiplicity[position:])


def refine_curve(curve):
    """One knot inserted mid-span: same geometry and parameterisation, one more pole."""
    vector = full_vector(curve.Knots, curve.Multiplicity, curve.Degree)
    parameter = refine_parameter(curve.Knots)
    weights = list(curve.Weights) if curve.Rational else [1.0] * len(curve.Poles)
    points, new_weights = insert_row(vector, curve.Degree, list(curve.Poles), weights, parameter, curve.Rational)
    knots, multiplicity = insert_value(curve.Knots, curve.Multiplicity, parameter)
    edited = dataclasses.replace(curve, Knots=knots, Multiplicity=multiplicity, Poles=tuple(points), Weights=tuple(new_weights) if curve.Rational else curve.Weights)
    return edited, parameter


def refine_surface(surface):
    """One knot inserted mid-span in the first open direction: same geometry, one more pole row or column."""
    along_u = surface.UClosure == 0
    if not along_u and surface.VClosure != 0:
        raise RuntimeError("no open direction to refine")
    uvec = full_vector(surface.UKnots, surface.UMultiplicity, surface.UDegree)
    vvec = full_vector(surface.VKnots, surface.VMultiplicity, surface.VDegree)
    ucount, vcount = len(uvec) - surface.UDegree - 1, len(vvec) - surface.VDegree - 1
    weights = list(surface.Weights) if surface.Rational else [1.0] * len(surface.Poles)
    grid = [[surface.Poles[row * ucount + col] for col in range(ucount)] for row in range(vcount)]
    wgrid = [[weights[row * ucount + col] for col in range(ucount)] for row in range(vcount)]
    if along_u:
        parameter = refine_parameter(surface.UKnots)
        rows = [insert_row(uvec, surface.UDegree, grid[row], wgrid[row], parameter, surface.Rational) for row in range(vcount)]
        poles = [point for points, _ in rows for point in points]
        new_weights = [weight for _, values in rows for weight in values]
        knots, multiplicity = insert_value(surface.UKnots, surface.UMultiplicity, parameter)
        edited = dataclasses.replace(surface, UKnots=knots, UMultiplicity=multiplicity, Poles=tuple(poles), Weights=tuple(new_weights) if surface.Rational else surface.Weights)
    else:
        parameter = refine_parameter(surface.VKnots)
        columns = [insert_row(vvec, surface.VDegree, [grid[row][col] for row in range(vcount)], [wgrid[row][col] for row in range(vcount)], parameter, surface.Rational) for col in range(ucount)]
        poles = [columns[col][0][row] for row in range(vcount + 1) for col in range(ucount)]
        new_weights = [columns[col][1][row] for row in range(vcount + 1) for col in range(ucount)]
        knots, multiplicity = insert_value(surface.VKnots, surface.VMultiplicity, parameter)
        edited = dataclasses.replace(surface, VKnots=knots, VMultiplicity=multiplicity, Poles=tuple(poles), Weights=tuple(new_weights) if surface.Rational else surface.Weights)
    return edited, ("u" if along_u else "v"), parameter


def refinement_drift(before, after, samples=41):
    """Largest distance between the original and refined surfaces on a parameter grid."""
    first, second = research_surface(before), research_surface(after)
    ulow, uhigh, vlow, vhigh = first.domain
    worst = 0.0
    for i in range(samples):
        for j in range(samples):
            u, v = ulow + (uhigh - ulow) * i / (samples - 1), vlow + (vhigh - vlow) * j / (samples - 1)
            worst = max(worst, math.dist(first.point(u, v), second.point(u, v)))
    return worst


def curve_point(curve, parameter):
    vector = full_vector(curve.Knots, curve.Multiplicity, curve.Degree)
    count = len(curve.Poles)
    values = NurbsMath.basis(curve.Degree, vector, count, parameter)
    weights = list(curve.Weights) if curve.Rational else [1.0] * count
    total = sum(value * weight for value, weight in zip(values, weights))
    return [sum(value * weight * pole[axis] for value, weight, pole in zip(values, weights, curve.Poles)) / total for axis in range(curve.Dimension)]


def curve_drift(before, after, samples=201):
    low, high = before.Knots[0], before.Knots[-1]
    return max(math.dist(curve_point(before, low + (high - low) * i / (samples - 1)), curve_point(after, low + (high - low) * i / (samples - 1))) for i in range(samples))


def edit_surface_refine(entities, index):
    trail = next(paths(entities[index], lambda value: isinstance(value, BsSurface)))
    surface = get_at(entities[index], trail)
    edited, direction, parameter = refine_surface(surface)
    before, _ = fusion_poles(surface)
    after, _ = fusion_poles(edited)
    drift = refinement_drift(surface, edited)
    if drift > 1e-12:
        raise RuntimeError("surface refinement changed the geometry by " + repr(drift))
    detail = dict(entity=index, subtype=entities[index].Surface.SubtypeName, direction=direction, insertedKnot=parameter, polesBefore=len(surface.Poles), polesAfter=len(edited.Poles), geometryDriftCm=drift)
    return set_at(entities[index], trail, edited), dict(kind="face_poles", before=before, after=after), detail


def edit_curve_refine(entities, index, dimension, position=0):
    trail = [found for found in paths(entities[index], lambda value: isinstance(value, BsCurve) and value.Dimension == dimension)][position]
    curve = get_at(entities[index], trail)
    edited, parameter = refine_curve(curve)
    drift = curve_drift(curve, edited)
    if drift > 1e-12:
        raise RuntimeError("curve refinement changed the geometry by " + repr(drift))
    detail = dict(entity=index, insertedKnot=parameter, degree=curve.Degree, polesBefore=len(curve.Poles), polesAfter=len(edited.Poles), geometryDrift=drift)
    return set_at(entities[index], trail, edited), [list(p) for p in curve.Poles], [list(p) for p in edited.Poles], detail


def table_definitions(entities):
    table = []
    sites = []
    for index, entity in enumerate(entities):
        for name, slot in ListSubtypes(entity):
            if slot is None:
                table.append((name, index))
            else:
                sites.append((index, name, slot))
    return table, sites


def intcurve_pcurves(entity):
    return [get_at(entity, trail) for trail in paths(entity, lambda value: isinstance(value, BsCurve) and value.Dimension == 2)]


def pcurve_prediction(entities, index, form=None, offset=None):
    node = entities[index]
    form = node.Form if form is None else form
    offset_u = node.OffsetU if offset is None else offset
    curves = intcurve_pcurves(entities[node.CurveRef])
    curve = curves[abs(form) - 1] if len(curves) >= abs(form) else curves[-1]
    poles = [list(p) for p in curve.Poles]
    if form < 0:
        poles = poles[::-1]
    return [[p[0] + offset_u, p[1] + node.OffsetV] for p in poles]


def case_record(report, label, source, member, original, entities_before, entities_after, prediction, detail, covers, model, native=None):
    """Write one case. A case that Kit's own checks refuse to emit records the refusal instead of a mutant."""
    folder = OUT / "Subtypes"
    folder.mkdir(parents=True, exist_ok=True)
    changed = [index for index, (a, b) in enumerate(zip(entities_before, entities_after)) if a != b]
    if len(changed) != 1:
        raise RuntimeError(label + " must edit exactly one record")
    try:
        mutant = EmitGeometry(dataclasses.replace(model, Entities=tuple(entities_after)))
        rejection = None
    except ValueError as error:
        if native is None:
            raise
        mutant, rejection = None, str(error)
    if mutant is not None and ReadGeometry(mutant).Entities != tuple(entities_after):
        raise RuntimeError(label + " mutant does not reread to the edited typed model")
    stem = ORIGINALS[source]
    (folder / (stem + "Original.smb")).write_bytes(original)
    written = mutant is not None and native is None
    if written:
        (folder / (label + "Mutant.smb")).write_bytes(mutant)
    report["subtypes"].append(dict(label=label, covers=covers, source=relative(STUDY / source), sourceSha256=digest((STUDY / source).read_bytes()), member=member, original=relative(folder / (stem + "Original.smb")), originalSha256=digest(original), mutant=relative(folder / (label + "Mutant.smb")) if written else None, mutantSha256=digest(mutant) if mutant is not None else None, kitRejects=rejection, editedRecord=changed[0], editedType=type(entities_before[changed[0]]).__name__, detail=detail, prediction=prediction, native=native is None, notNative=native))
    print(label, digest(mutant) if mutant is not None else "rejected by Kit: " + rejection, flush=True)


def load_snapshot(source):
    member, data = read_member(source, ".smb")
    model = ReadGeometry(data)
    if EmitGeometry(model) != data:
        raise RuntimeError(source + " snapshot is not byte exact")
    return member, data, model


def load_state(source):
    member, data = read_member(source, ".smbh")
    journal = ReadJournal(data)
    if EmitJournal(journal) != data:
        raise RuntimeError(source + " history is not byte exact")
    state = EmitStateSmb(journal)
    model = ReadGeometry(state)
    if EmitGeometry(model) != state:
        raise RuntimeError(source + " emitted state does not reread byte exact")
    return member + " via EmitStateSmb", state, model


def first_index(entities, predicate):
    return next(index for index, value in enumerate(entities) if predicate(value))


def subtype_name(value):
    return getattr(getattr(value, "Surface", None), "SubtypeName", "")


def surface_case(report, label, source, name):
    member, data, model = load_snapshot(source)
    entities = list(model.Entities)
    index = first_index(entities, lambda value: isinstance(value, SplineNode) and subtype_name(value) == name)
    edited, prediction, detail = edit_surface_refine(entities, index)
    after = list(entities)
    after[index] = edited
    case_record(report, label, source, member, data, entities, after, prediction, detail, [name], model)


def curve_ref_case(report):
    source = "embosstext-cd769aa41cdf/two_texts.f3d"
    member, data, model = load_snapshot(source)
    entities = list(model.Entities)
    table, sites = table_definitions(entities)
    owner = first_index(entities, lambda value: isinstance(value, SplineNode) and subtype_name(value) == "cyl_spl_sur")
    slot = next(number for number, (name, index) in enumerate(table) if index == owner and name == "exact_int_cur")
    users = [index for index, family, target in sites if family == "curve" and target == slot and isinstance(entities[index], IntcurveNode)]
    edited, before, after, detail = edit_curve_refine(entities, owner, 3)
    changed = list(entities)
    changed[owner] = edited
    detail.update(definitionSlot=slot, referencingIntcurves=users, note="The refined curve is the cyl_spl_sur profile definition; edges reach it only through a curve subtype reference")
    case_record(report, "CylSplCurveRefine", source, member, data, entities, changed, dict(kind="edge_poles", before=before, after=after, sites=len(users)), detail, ["cyl_spl_sur", "curve reference"], model)


def axis_case(report):
    source = "embosstext-cd769aa41cdf/two_texts.f3d"
    member, data, model = load_snapshot(source)
    entities = list(model.Entities)
    owner = first_index(entities, lambda value: isinstance(value, SplineNode) and subtype_name(value) == "cyl_spl_sur")
    body = entities[owner].Surface.Body
    axis = body[2]
    tilted = (axis[0] + 0.25, axis[1], axis[2])
    edited = dataclasses.replace(entities[owner], Surface=dataclasses.replace(entities[owner].Surface, Body=(*body[:2], tilted, *body[3:])))
    changed = list(entities)
    changed[owner] = edited
    case_record(report, "CylSplAxis", source, member, data, entities, changed, dict(kind="observe_evaluator"), dict(entity=owner, axisBefore=list(axis), axisAfter=list(tilted)), ["cyl_spl_sur"], model, native="Inconsistent by construction: the procedural axis no longer agrees with the stored approximation")


def pairs_prediction(before_entities, after_entities, intcurve, form):
    users = [index for index, value in enumerate(before_entities) if isinstance(value, PcurveNode) and value.CurveRef == intcurve and abs(value.Form) == form]
    return [dict(pcurve=index, form=before_entities[index].Form, offsetU=before_entities[index].OffsetU, offsetV=before_entities[index].OffsetV, before=pcurve_prediction(before_entities, index), after=pcurve_prediction(after_entities, index), sites=1) for index in users]


def form_refine_case(report, label, source, form, covers):
    member, data, model = load_snapshot(source)
    entities = list(model.Entities)
    signed = [index for index, value in enumerate(entities) if isinstance(value, PcurveNode) and value.CurveRef >= 0 and abs(value.Form) == form]
    intcurve = entities[signed[0]].CurveRef
    edited, before, after, detail = edit_curve_refine(entities, intcurve, 2, form - 1)
    changed = list(entities)
    changed[intcurve] = edited
    pairs = pairs_prediction(entities, changed, intcurve, form)
    detail.update(intcurve=intcurve, subtype=entities[intcurve].Curve.SubtypeName, pcurveSlot=form, users=[dict(pcurve=pair["pcurve"], form=pair["form"], offsetU=pair["offsetU"], offsetV=pair["offsetV"]) for pair in pairs])
    case_record(report, label, source, member, data, entities, changed, dict(kind="coedge_pairs", pairs=pairs), detail, covers, model)


def form_cases(report):
    source = "sweepnurbspaths-7ded30a4b9ae/polynomial_cubic.f3d"
    form_refine_case(report, "PcurveFormRefine", source, 1, ["pcurve form 1", "pcurve form -1", "pcurve offset"])
    member, data, model = load_snapshot(source)
    entities = list(model.Entities)
    signed = [index for index, value in enumerate(entities) if isinstance(value, PcurveNode) and value.CurveRef >= 0]
    plus = next(index for index in signed if entities[index].Form == 1)
    minus = next(index for index in signed if entities[index].Form == -1 and entities[index].OffsetU != 0.0)
    changed = list(entities)
    changed[plus] = dataclasses.replace(entities[plus], Form=-1)
    case_record(report, "PcurveFormSign", source, member, data, entities, changed, dict(kind="coedge_poles", before=pcurve_prediction(entities, plus), after=pcurve_prediction(entities, plus, form=-1)), dict(entity=plus, formBefore=1, formAfter=-1, intcurve=entities[plus].CurveRef), ["pcurve form 1", "pcurve form -1"], model, native="Inconsistent by construction: both seam pcurves then run the same way. Fusion exited while this case was running in the run of 2026-11-12 15:10")
    changed = list(entities)
    changed[minus] = dataclasses.replace(entities[minus], OffsetU=0.0)
    case_record(report, "PcurveFormOffset", source, member, data, entities, changed, dict(kind="coedge_poles", before=pcurve_prediction(entities, minus), after=pcurve_prediction(entities, minus, offset=0.0)), dict(entity=minus, offsetBefore=entities[minus].OffsetU, offsetAfter=0.0, intcurve=entities[minus].CurveRef), ["pcurve offset"], model, native="Inconsistent by construction: both seam pcurves then lie on the same side of the periodic domain")


def tolerant_cases(report):
    source = "solidsweeps-7d2677669e3d/solid_twist.f3d"
    form_refine_case(report, "TolerantFormRefine", source, 2, ["pcurve form 2", "int_int_cur"])
    member, data, model = load_snapshot(source)
    entities = list(model.Entities)
    second = first_index(entities, lambda value: isinstance(value, PcurveNode) and value.Form == 2)
    changed = list(entities)
    changed[second] = dataclasses.replace(entities[second], Form=-2)
    case_record(report, "TolerantFormTwo", source, member, data, entities, changed, dict(kind="coedge_poles"), dict(entity=second, formBefore=2, formAfter=-2, intcurve=entities[second].CurveRef), ["pcurve form 2"], model, native="Inconsistent by construction: the pcurve then runs against its coedge")
    tedges = [index for index, value in enumerate(entities) if isinstance(value, TedgeNode)]
    tolerances = collections.Counter(entities[index].Tolerance for index in tedges)
    edge = next(index for index in tedges if tolerances[entities[index].Tolerance] == 1)
    node = entities[edge].Base
    ceiling = min(entities[node.StartVertex].Tolerance, entities[node.EndVertex].Tolerance)
    raised = 2.0e-05
    if not entities[edge].Tolerance < raised < ceiling or raised in tolerances:
        raise RuntimeError("raised tedge tolerance must stay below both tvertex tolerances and be unique")
    changed = list(entities)
    changed[edge] = dataclasses.replace(entities[edge], Tolerance=raised)
    case_record(report, "TolerantEdge", source, member, data, entities, changed, dict(kind="edge_tolerance", before=entities[edge].Tolerance, after=raised), dict(entity=edge, toleranceBefore=entities[edge].Tolerance, toleranceAfter=raised, vertexTolerances=[entities[node.StartVertex].Tolerance, entities[node.EndVertex].Tolerance], note="Raised but kept below both end tvertex tolerances"), ["tedge"], model)
    vertex = first_index(entities, lambda value: isinstance(value, TvertexNode))
    point = list(entities[entities[vertex].Base.PointRef].PositionCm)
    if entities[vertex].Tolerance != entities[vertex].SavedTolerance:
        raise RuntimeError("tvertex tolerance pair differs")
    changed = list(entities)
    changed[vertex] = dataclasses.replace(entities[vertex], Tolerance=6.0e-05, SavedTolerance=6.0e-05)
    case_record(report, "TolerantVertex", source, member, data, entities, changed, dict(kind="vertex_tolerance", pointCm=point, before=entities[vertex].Tolerance, after=6.0e-05, hard=True), dict(entity=vertex, fields=["Tolerance", "SavedTolerance"], before=entities[vertex].Tolerance, after=6.0e-05, note="Both fields are equal in every tvertex of this body, so both are raised together"), ["tvertex"], model)
    changed = list(entities)
    changed[vertex] = dataclasses.replace(entities[vertex], Tolerance=1.0e-05, SavedTolerance=1.0e-05)
    case_record(report, "TolerantOrder", source, member, data, entities, changed, dict(kind="vertex_tolerance"), dict(entity=vertex, before=entities[vertex].Tolerance, after=1.0e-05, adjacentTedgeTolerances=sorted(entities[index].Tolerance for index in tedges if vertex in (entities[index].Base.StartVertex, entities[index].Base.EndVertex))), ["tvertex", "tedge"], model, native="Inconsistent by construction: the tvertex becomes tighter than a tedge that ends at it")
    coedge = first_index(entities, lambda value: isinstance(value, TcoedgeNode) and value.RangeLower == 0.0)
    node = entities[coedge]
    changed = list(entities)
    changed[coedge] = dataclasses.replace(node, RangeUpper=node.RangeUpper * 0.8)
    case_record(report, "TolerantCoedge", source, member, data, entities, changed, dict(kind="observe_coedge_range"), dict(entity=coedge, rangeBefore=[node.RangeLower, node.RangeUpper], rangeAfter=[node.RangeLower, node.RangeUpper * 0.8]), ["tcoedge"], model, native="Inconsistent by construction: the tcoedge range no longer spans its edge")


def stitch_case(report):
    source = "patchcontinuity-b9b0be85a281/brep_curvature.f3d"
    member, data, model = load_snapshot(source)
    entities = list(model.Entities)
    index = first_index(entities, lambda value: isinstance(value, StitchAttrib))
    node = entities[index]
    values = (node.HintValues[0] + 0.125, node.HintValues[1], node.HintValues[2])
    changed = list(entities)
    changed[index] = dataclasses.replace(node, HintValues=values)
    case_record(report, "StitchHint", source, member, data, entities, changed, dict(kind="export_attribute", attribute="stitch_hint-sys-attrib", before=list(node.HintValues), after=list(values)), dict(entity=index, owner=node.Links.OwnerRef, ownerType=type(entities[node.Links.OwnerRef]).__name__, before=list(node.HintValues), after=list(values), note="The API exposes no attribute values, so the bodies are exported from Fusion and decoded"), ["stitch_hint"], model)


def vertedge_case(report):
    source = "splines-9a18bae21127/splines.f3d"
    member, data, model = load_snapshot(source)
    entities = list(model.Entities)
    index = first_index(entities, lambda value: isinstance(value, VertedgeAttrib))
    node = entities[index]
    used = [slot for slot in node.EdgeSlots if slot[0] >= 0]
    dropped = used[-1]
    slots = tuple((-1, 2) if slot == dropped else slot for slot in node.EdgeSlots)
    changed = list(entities)
    changed[index] = dataclasses.replace(node, EdgeSlots=slots)
    case_record(report, "VertedgeSlots", source, member, data, entities, changed, dict(kind="vertex_edges"), dict(entity=index, vertex=node.Links.OwnerRef, slotsBefore=[list(slot) for slot in node.EdgeSlots], slotsAfter=[list(slot) for slot in slots], droppedEdge=dropped[0]), ["vertedge"], model, native="Inconsistent by construction: the non-manifold vertex then omits one of its edges")


def reference_cases(report):
    source = "rulefilletsurfaces-7b26b40f98f7/offsets_one_two_witnesses.f3d"
    member, data, model = load_state(source)
    entities = list(model.Entities)
    table, sites = table_definitions(entities)
    pcurve_site = next((index, slot) for index, family, slot in sites if family == "pcurve" and isinstance(entities[index], PcurveNode))
    owner = table[pcurve_site[1]][1]
    users = [index for index, family, slot in sites if family == "pcurve" and slot == pcurve_site[1]]
    edited, before, after, detail = edit_curve_refine(entities, owner, 2)
    changed = list(entities)
    changed[owner] = edited
    sense = lambda index: entities[index].Reversed
    detail.update(definitionSlot=pcurve_site[1], referencingPcurves=users, ownerReversed=sense(owner), userReversed=[sense(index) for index in users])
    case_record(report, "PcurveRefine", source, member, data, entities, changed, dict(kind="coedge_poles", before=before, after=after, sites=1 + len(users), anyDirection=True), detail, ["pcurve reference", "exp_par_cur"], model)
    curve_site = next((index, slot) for index, family, slot in sites if family == "curve" and isinstance(entities[index], IntcurveNode))
    owner = table[curve_site[1]][1]
    users = [index for index, family, slot in sites if family == "curve" and slot == curve_site[1]]
    edited, before, after, detail = edit_curve_refine(entities, owner, 3)
    changed = list(entities)
    changed[owner] = edited
    detail.update(definitionSlot=curve_site[1], referencingIntcurves=users, definition=table[curve_site[1]][0])
    case_record(report, "CurveRefine", source, member, data, entities, changed, dict(kind="edge_poles", before=before, after=after, sites=1 + len(users)), detail, ["curve reference", table[curve_site[1]][0]], model)


def main():
    report = dict(schema="FusionComplexSecondPreparation/1", status="preparing", authored=[], subtypes=[])
    OUT.mkdir(parents=True, exist_ok=True)
    prepare_authored(report)
    surface_case(report, "ClLoftRefine", "lofts-03b4a6f1ce2f/centerline.f3d", "cl_loft_spl_sur")
    surface_case(report, "SumSplRefine", "solidsweeps-7d2677669e3d/solid_rigid.f3d", "sum_spl_sur")
    surface_case(report, "CylSplRefine", "embosstext-cd769aa41cdf/two_texts.f3d", "cyl_spl_sur")
    curve_ref_case(report)
    axis_case(report)
    form_cases(report)
    tolerant_cases(report)
    stitch_case(report)
    vertedge_case(report)
    reference_cases(report)
    report["status"] = "prepared"
    (OUT / "Preparation.json").write_text(json.dumps(report, indent=1) + "\n")


if __name__ == "__main__":
    main()
