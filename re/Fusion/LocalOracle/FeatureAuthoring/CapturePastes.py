"""Native copy and paste body controls.

Builds parts that copy and paste a body through the public Fusion API
(Features.copyPasteBodies), exports each to Controls/Paste*.f3d, reopens
the export and records the public property dump of every entity
(PEntity.Properties) and the active document schema
(Document.DumpAcitveDocSchema). The dumps go to kit-paste-dumps in the
system temporary directory, outside the repository, because they hold
document identities. Controls/CapturePastes.json keeps only the
observations. Evidence for Kit authoring, not Kit acceptance.
Run only through RunLocked.mjs. Every document opened here is closed.
"""

import hashlib
import json
from pathlib import Path
import tempfile
import traceback

import adsk.core
import adsk.fusion


here = Path(__file__).resolve().parent
root = here / "Controls"
dumps = Path(tempfile.gettempdir()) / "kit-paste-dumps"
dumps.mkdir(parents=True, exist_ok=True)
app = adsk.core.Application.get()
original = app.activeDocument
report = {"fusion_version": app.version, "documents_before": app.documents.count, "scope": "Native copy and paste body controls created through the Fusion API and exported locally; evidence for Kit feature authoring, not Kit acceptance", "controls": []}
FO = adsk.fusion.FeatureOperations
ONLY = globals().get("ONLY")


def checkpoint():
    (root / "CapturePastes.json").write_text(json.dumps(report, indent=2).replace(str(Path(__file__).resolve().parents[4]) + "/", "").replace(str(dumps), "<tmp>/kit-paste-dumps").replace(str(Path.home()), "~") + "\n")


def vi(text):
    return adsk.core.ValueInput.createByString(text)


def pt(x, y, z=0.0):
    return adsk.core.Point3D.create(x, y, z)


def coll(*items):
    value = adsk.core.ObjectCollection.create()
    for item in items:
        value.add(item)
    return value


def base(comp):
    sketch = comp.sketches.add(comp.xYConstructionPlane)
    sketch.name = "Base sketch"
    sketch.sketchCurves.sketchLines.addTwoPointRectangle(pt(0, 0), pt(4, 3))
    extrude = comp.features.extrudeFeatures.addSimple(sketch.profiles.item(0), vi("20 mm"), FO.NewBodyFeatureOperation)
    extrude.name = "Base extrude"
    return extrude.bodies.item(0)


def post(comp):
    sketch = comp.sketches.add(comp.xYConstructionPlane)
    sketch.name = "Post sketch"
    sketch.sketchCurves.sketchCircles.addByCenterRadius(pt(6, 1.5), 0.5)
    extrude = comp.features.extrudeFeatures.addSimple(sketch.profiles.item(0), vi("20 mm"), FO.NewBodyFeatureOperation)
    extrude.name = "Post extrude"
    return extrude.bodies.item(0)


def vertical_edge(body, x, y):
    for edge in body.edges:
        s, e = edge.startVertex.geometry, edge.endVertex.geometry
        if abs(s.x - x) < 1e-6 and abs(e.x - x) < 1e-6 and abs(s.y - y) < 1e-6 and abs(e.y - y) < 1e-6:
            return edge
    raise RuntimeError("Vertical edge not found")


def paste(comp, body, name):
    feature = comp.features.copyPasteBodies.add(body)
    feature.name = name
    return feature


def c_plain(comp):
    paste(comp, base(comp), "Body paste")


def c_fillet(comp):
    body = base(comp)
    feats = comp.features.filletFeatures
    inp = feats.createInput()
    inp.edgeSetInputs.addConstantRadiusEdgeSet(coll(vertical_edge(body, 4, 3)), vi("3 mm"), True)
    feats.add(inp).name = "Corner round"
    paste(comp, comp.bRepBodies.item(0), "Body paste")


def c_twice(comp):
    body = base(comp)
    paste(comp, body, "First paste")
    paste(comp, comp.bRepBodies.item(0), "Second paste")


def c_second(comp):
    base(comp)
    post(comp)
    paste(comp, comp.bRepBodies.itemByName("Body2"), "Post paste")


def dump_entities(path, name):
    doc = app.importManager.importToNewDocument(app.importManager.createFusionArchiveImportOptions(str(path)))
    try:
        entities = json.loads(app.executeTextCommand("PAsset.EntityIds"))
        rows = []
        for identity in entities:
            row = {"identity": identity}
            if identity["entityId"] >= 0:
                try:
                    row["properties"] = json.loads(app.executeTextCommand("PEntity.Properties " + str(identity["entityId"])))
                except Exception:
                    row["error"] = traceback.format_exc()
            rows.append(row)
        (dumps / (name + ".entities.json")).write_text(json.dumps(rows, indent=1) + "\n")
        schema = dumps / (name + ".schema.xml")
        result = app.executeTextCommand('Document.DumpAcitveDocSchema "' + str(schema) + '"')
        return {"entities": len(rows), "properties": sum("properties" in r for r in rows), "schema_reply": result[:200] if result else result}
    finally:
        doc.close(False)


def observe(design):
    comp = design.rootComponent
    bodies = []
    for b in comp.bRepBodies:
        bb = b.boundingBox
        props = b.physicalProperties
        bodies.append({"name": b.name, "solid": b.isSolid, "volume_cm3": b.volume, "area_cm2": b.area, "faces": b.faces.count, "edges": b.edges.count, "vertices": b.vertices.count, "min_cm": bb.minPoint.asArray(), "max_cm": bb.maxPoint.asArray(), "center_cm": props.centerOfMass.asArray(), "surface_types": sorted(f.geometry.surfaceType for f in b.faces)})
    timeline = [{"name": i.name, "object_type": i.entity.objectType if i.entity else None, "health": i.healthState, "message": i.errorOrWarningMessage} for i in design.timeline]
    params = [{"name": p.name, "expression": p.expression, "unit": p.unit} for p in design.allParameters]
    return {"timeline": timeline, "parameters": params, "bodies": bodies}


controls = [("PastePlain", c_plain), ("PasteFillet", c_fillet), ("PasteTwice", c_twice), ("PasteSecond", c_second)]

try:
    for name, build in controls:
        if ONLY is not None and name not in ONLY:
            continue
        entry = {"name": name, "status": "started"}
        report["controls"].append(entry)
        doc = None
        try:
            doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
            design = adsk.fusion.Design.cast(doc.products.itemByProductType("DesignProductType"))
            design.designType = adsk.fusion.DesignTypes.ParametricDesignType
            build(design.rootComponent)
            if not design.computeAll():
                raise RuntimeError("Native control did not recompute")
            entry["observed"] = observe(design)
            path = root / (name + ".f3d")
            if not design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(path))):
                raise RuntimeError("Native control export failed")
            doc.close(False)
            doc = None
            entry["file"] = path.name
            entry["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
            entry["bytes"] = path.stat().st_size
            entry["dump"] = dump_entities(path, name)
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
