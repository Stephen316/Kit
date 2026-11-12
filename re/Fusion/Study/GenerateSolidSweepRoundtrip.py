"""Read two owned solid-Sweep archives after importing into unsaved documents."""

import hashlib
import json
from pathlib import Path
import traceback
import uuid

import adsk.core
import adsk.fusion


def run(context):
    app = adsk.core.Application.get()
    base = Path(__file__).resolve().parent
    output = base/("solidsweep-roundtrip-"+uuid.uuid4().hex[:12])
    output.mkdir()
    truth = {"fusion_version": app.version, "samples": [], "errors": [],
             "scope": "Only import two existing owned archives; no save, export or original modification"}

    def body_truth(body):
        if body is None:
            return None
        bounds = body.boundingBox
        return {"kind": body.objectType.split("::")[-1], "name": body.name,
                "entity_token": body.entityToken, "volume_cm3": body.volume,
                "bounding_box_min_cm": bounds.minPoint.asArray(),
                "bounding_box_max_cm": bounds.maxPoint.asArray()}

    def axis_truth(axis):
        if axis is None:
            return None
        geometry = axis.geometry
        return {"kind": axis.objectType.split("::")[-1], "name": getattr(axis, "name", None),
                "entity_token": getattr(axis, "entityToken", None),
                "origin_cm": geometry.origin.asArray(), "direction": geometry.direction.asArray()}

    for filename in ("solid_perpendicular.f3d", "solid_rigid.f3d"):
        source = base/"solidsweeps-7d2677669e3d"/filename
        before = hashlib.sha256(source.read_bytes()).hexdigest()
        doc, design = None, None
        try:
            options = app.importManager.createFusionArchiveImportOptions(str(source))
            if options is None:
                raise RuntimeError("Fusion archive import options returned null")
            doc = app.importManager.importToNewDocument(options)
            if doc is None:
                raise RuntimeError("Fusion archive import returned null")
            design = adsk.fusion.Design.cast(doc.products.itemByProductType("DesignProductType"))
            if design is None:
                raise RuntimeError("Imported document has no Design product")
            sweeps = design.rootComponent.features.sweepFeatures
            feature = sweeps.itemByName("ProbeSolidSweep")
            if feature is None or sweeps.count != 1:
                raise RuntimeError("Expected one study-owned ProbeSolidSweep")
            sample = {"source": str(source), "sha256_before": before, "getter_errors": []}

            def getter(name, read):
                try:
                    return read()
                except Exception:
                    sample["getter_errors"].append({"getter": name, "error": traceback.format_exc()})
                    return None

            sample["solid_orientation_at_end"] = getter("solidOrientation at end", lambda: feature.solidOrientation)
            sample["result_bodies_at_end"] = getter("bodies at end", lambda: [body_truth(body) for body in feature.bodies])
            feature.timelineObject.rollTo(True)
            sample["settings"] = {
                "operation": getter("operation", lambda: feature.operation),
                "solid_orientation": getter("solidOrientation", lambda: feature.solidOrientation),
                "solid_body": getter("solidBody", lambda: body_truth(feature.solidBody)),
                "solid_aligned_axis": getter("solidAlignedAxis", lambda: axis_truth(feature.solidAlignedAxis)),
                "solid_twist_axis": getter("solidTwistAxis", lambda: axis_truth(feature.solidTwistAxis)),
                "twist_angle_radians": getter("twistAngle", lambda: feature.twistAngle.value if feature.twistAngle else None)}
            truth["samples"].append(sample)
        except Exception:
            truth["errors"].append({"source": str(source), "error": traceback.format_exc()})
        finally:
            if design is not None:
                try:
                    design.timeline.moveToEnd()
                except Exception:
                    truth["errors"].append({"source": str(source), "cleanup": "timeline restore", "error": traceback.format_exc()})
            if doc is not None:
                doc.close(False)
            after = hashlib.sha256(source.read_bytes()).hexdigest()
            if after != before:
                truth["errors"].append({"source": str(source), "error": "Original archive SHA256 changed"})
            if truth["samples"] and truth["samples"][-1]["source"] == str(source):
                truth["samples"][-1]["sha256_after"] = after
                truth["samples"][-1]["original_unchanged"] = after == before
            (output/"ground_truth.json").write_text(json.dumps(truth, indent=2))
    (output/"complete.txt").write_text("Solid Sweep read-only import check finished; consult errors.\n")
