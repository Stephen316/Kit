"""Native controls for general sketch profiles, extents and holes.

Builds one-variable parts through the Fusion API and exports them to
Controls/ for decoding. Evidence for Kit authoring, not Kit acceptance.
Run only through RunLocked.mjs. Every document opened here is closed.
"""

import hashlib
import json
import math
from pathlib import Path
import traceback

import adsk.core
import adsk.fusion


root = Path(__file__).resolve().parent / "Controls"
root.mkdir(exist_ok=True)
app = adsk.core.Application.get()
original = app.activeDocument
report = {"fusion_version": app.version, "documents_before": app.documents.count, "scope": "Native profile, extent and hole controls created through the Fusion API and exported locally; evidence for Kit feature authoring, not Kit acceptance", "controls": []}
FO = adsk.fusion.FeatureOperations


def checkpoint():
    (root / "CaptureProfiles.json").write_text(json.dumps(report, indent=2).replace(str(Path(__file__).resolve().parents[4]) + "/", "").replace(str(Path.home()), "~") + "\n")


def vi(text):
    return adsk.core.ValueInput.createByString(text)


def pt(x, y, z=0.0):
    return adsk.core.Point3D.create(x, y, z)


def base(comp, height="20 mm"):
    sk = comp.sketches.add(comp.xYConstructionPlane)
    sk.name = "Base sketch"
    sk.sketchCurves.sketchLines.addTwoPointRectangle(pt(0, 0), pt(4, 3))
    ext = comp.features.extrudeFeatures.addSimple(sk.profiles.item(0), vi(height), FO.NewBodyFeatureOperation)
    ext.name = "Base extrude"
    return ext


def slot(sk, x0, y0, x1, r):
    lines = sk.sketchCurves.sketchLines
    arcs = sk.sketchCurves.sketchArcs
    lower = lines.addByTwoPoints(pt(x0, y0 - r), pt(x1, y0 - r))
    right = arcs.addByCenterStartSweep(pt(x1, y0), lower.endSketchPoint, math.pi)
    upper = lines.addByTwoPoints(right.endSketchPoint, pt(x0, y0 + r))
    arcs.addByCenterStartSweep(pt(x0, y0), upper.endSketchPoint, math.pi)
    sk.isComputeDeferred = False


def concave(sk):
    lines = sk.sketchCurves.sketchLines
    arcs = sk.sketchCurves.sketchArcs
    a = lines.addByTwoPoints(pt(0, 0), pt(4, 0))
    b = lines.addByTwoPoints(a.endSketchPoint, pt(4, 3))
    c = lines.addByTwoPoints(b.endSketchPoint, pt(3, 3))
    d = lines.addByTwoPoints(pt(1, 3), pt(0, 3))
    arcs.addByCenterStartSweep(pt(2, 3), d.startSketchPoint, math.pi)
    lines.addByTwoPoints(d.endSketchPoint, a.startSketchPoint)
    _ = c


def profile_body(comp, draw, name):
    sk = comp.sketches.add(comp.xYConstructionPlane)
    sk.name = name + " sketch"
    draw(sk)
    ext = comp.features.extrudeFeatures.addSimple(sk.profiles.item(0), vi("20 mm"), FO.NewBodyFeatureOperation)
    ext.name = name + " extrude"
    return ext


def c_profile_slot(comp, design):
    profile_body(comp, lambda sk: slot(sk, 1, 1, 3, 1), "Slot")


def c_profile_concave(comp, design):
    profile_body(comp, concave, "Notch")


def c_extrude_two_sided(comp, design):
    sk = comp.sketches.add(comp.xYConstructionPlane)
    sk.name = "Base sketch"
    sk.sketchCurves.sketchLines.addTwoPointRectangle(pt(0, 0), pt(4, 3))
    ext = comp.features.extrudeFeatures
    inp = ext.createInput(sk.profiles.item(0), FO.NewBodyFeatureOperation)
    inp.setTwoSidesExtent(adsk.fusion.DistanceExtentDefinition.create(vi("20 mm")), adsk.fusion.DistanceExtentDefinition.create(vi("5 mm")))
    e = ext.add(inp)
    e.name = "Base extrude"


def c_extrude_flip(comp, design):
    sk = comp.sketches.add(comp.xYConstructionPlane)
    sk.name = "Base sketch"
    sk.sketchCurves.sketchLines.addTwoPointRectangle(pt(0, 0), pt(4, 3))
    ext = comp.features.extrudeFeatures
    inp = ext.createInput(sk.profiles.item(0), FO.NewBodyFeatureOperation)
    inp.setOneSideExtent(adsk.fusion.DistanceExtentDefinition.create(vi("20 mm")), adsk.fusion.ExtentDirections.NegativeExtentDirection)
    e = ext.add(inp)
    e.name = "Base extrude"


def c_blind_cut(comp, design):
    base(comp)
    sk = comp.sketches.add(comp.xYConstructionPlane)
    sk.name = "Pocket sketch"
    sk.sketchCurves.sketchCircles.addByCenterRadius(pt(2, 1.5), 0.5)
    e = comp.features.extrudeFeatures.addSimple(sk.profiles.item(0), vi("10 mm"), FO.CutFeatureOperation)
    e.name = "Pocket extrude"


def c_slot_cut(comp, design):
    base(comp)
    sk = comp.sketches.add(comp.xYConstructionPlane)
    sk.name = "Slot sketch"
    slot(sk, 1.5, 1.5, 2.5, 0.5)
    e = comp.features.extrudeFeatures.addSimple(sk.profiles.item(0), vi("20 mm"), FO.CutFeatureOperation)
    e.name = "Slot extrude"


def c_symmetric_cut(comp, design):
    base(comp)
    sk = comp.sketches.add(comp.xYConstructionPlane)
    sk.name = "Pocket sketch"
    sk.sketchCurves.sketchCircles.addByCenterRadius(pt(2, 1.5), 0.5)
    ext = comp.features.extrudeFeatures
    inp = ext.createInput(sk.profiles.item(0), FO.CutFeatureOperation)
    inp.setSymmetricExtent(vi("20 mm"), True)
    e = ext.add(inp)
    e.name = "Pocket extrude"


def hole_input(comp, kind):
    feats = comp.features.holeFeatures
    if kind == "simple":
        return feats.createSimpleInput(vi("8 mm"))
    if kind == "counterbore":
        return feats.createCounterboreInput(vi("6 mm"), vi("10 mm"), vi("4 mm"))
    return feats.createCountersinkInput(vi("6 mm"), vi("10 mm"), vi("90 deg"))


def place_hole(comp, kind, through, flat):
    body = base(comp).bodies.item(0)
    top = None
    for face in body.faces:
        if face.geometry.surfaceType == adsk.core.SurfaceTypes.PlaneSurfaceType:
            ok, normal = face.evaluator.getNormalAtPoint(face.pointOnFace)
            if normal.z > 0.999:
                top = face
    inp = hole_input(comp, kind)
    inp.setPositionByPoint(top, pt(2, 1.5, 2))
    if through:
        inp.setAllExtent(adsk.fusion.ExtentDirections.PositiveExtentDirection)
    else:
        inp.setDistanceExtent(vi("10 mm"))
    if flat:
        inp.tipAngle = vi("180 deg")
    h = comp.features.holeFeatures.add(inp)
    h.name = "Top hole"


controls = [
    ("ProfileSlot", c_profile_slot),
    ("ProfileConcave", c_profile_concave),
    ("ExtrudeTwoSided", c_extrude_two_sided),
    ("ExtrudeFlip", c_extrude_flip),
    ("ExtrudeBlindCut", c_blind_cut),
    ("ExtrudeSlotCut", c_slot_cut),
    ("ExtrudeSymmetricCut", c_symmetric_cut),
    ("HoleThrough", lambda comp, design: place_hole(comp, "simple", True, False)),
    ("HoleFlat", lambda comp, design: place_hole(comp, "simple", False, True)),
    ("HoleCounterbore", lambda comp, design: place_hole(comp, "counterbore", True, False)),
    ("HoleCounterboreFlat", lambda comp, design: place_hole(comp, "counterbore", False, True)),
    ("HoleCountersink", lambda comp, design: place_hole(comp, "countersink", True, False)),
]


def observe(design):
    comp = design.rootComponent
    bodies = []
    for b in comp.bRepBodies:
        bb = b.boundingBox
        bodies.append({"name": b.name, "solid": b.isSolid, "volume_cm3": b.volume, "area_cm2": b.area, "faces": b.faces.count, "edges": b.edges.count, "vertices": b.vertices.count, "min_cm": bb.minPoint.asArray(), "max_cm": bb.maxPoint.asArray(), "surface_types": sorted(f.geometry.surfaceType for f in b.faces)})
    timeline = [{"name": i.name, "health": i.healthState, "message": i.errorOrWarningMessage} for i in design.timeline]
    params = [{"name": p.name, "expression": p.expression, "value": p.value, "unit": p.unit} for p in design.allParameters]
    return {"timeline": timeline, "parameters": params, "bodies": bodies, "profiles": [s.profiles.count for s in comp.sketches]}


try:
    for name, build in controls:
        entry = {"name": name, "status": "started"}
        report["controls"].append(entry)
        doc = None
        try:
            doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
            design = adsk.fusion.Design.cast(doc.products.itemByProductType("DesignProductType"))
            design.designType = adsk.fusion.DesignTypes.ParametricDesignType
            build(design.rootComponent, design)
            if not design.computeAll():
                raise RuntimeError("Native control did not recompute")
            entry["observed"] = observe(design)
            path = root / (name + ".f3d")
            if not design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(path))):
                raise RuntimeError("Native control export failed")
            entry["file"] = path.name
            entry["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
            entry["bytes"] = path.stat().st_size
            entry["status"] = "captured"
        except Exception:
            entry["status"] = "failed"
            entry["traceback"] = traceback.format_exc()
        finally:
            if doc is not None:
                doc.close(False)
            checkpoint()
    report["status"] = "captured"
except Exception:
    report["status"] = "failed"
    report["traceback"] = traceback.format_exc()
finally:
    if original is not None and original.isValid:
        original.activate()
    report["documents_after"] = app.documents.count
    checkpoint()
