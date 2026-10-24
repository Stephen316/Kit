"""Local point-geometry assembly joints, motion enums and limit probes."""

import json
import traceback
import uuid
from pathlib import Path

import adsk.core
import adsk.fusion


def run(context):
    app = adsk.core.Application.get()
    output = Path(__file__).resolve().parent/("jointmodes-"+uuid.uuid4().hex[:12])
    output.mkdir()
    truth = {"fusion_version": app.version, "samples": [], "errors": []}
    point, value = adsk.core.Point3D.create, adsk.core.ValueInput.createByString
    cases = ("rigid", "revolute", "slider", "cylindrical", "pin_slot", "planar", "ball", "rigid_flipped")
    motion_classes = {"revolute": adsk.fusion.RevoluteJointMotion, "slider": adsk.fusion.SliderJointMotion,
                      "cylindrical": adsk.fusion.CylindricalJointMotion, "pin_slot": adsk.fusion.PinSlotJointMotion,
                      "planar": adsk.fusion.PlanarJointMotion, "ball": adsk.fusion.BallJointMotion}
    limit_values = {"rotationLimits": (-.4, 1.1, .2), "slideLimits": (-.8, 1.8, .3),
                    "primarySlideLimits": (-.7, 1.7, .25), "secondarySlideLimits": (-.9, 2.1, .5),
                    "pitchLimits": (-.25, .55, .1), "yawLimits": (-.35, .65, .15),
                    "rollLimits": (-.45, .75, .2)}
    limit_flags = {("slider", "slideLimits"): (True, False, True),
                   ("cylindrical", "rotationLimits"): (False, True, False),
                   ("cylindrical", "slideLimits"): (True, True, False),
                   ("pin_slot", "rotationLimits"): (True, False, False),
                   ("pin_slot", "slideLimits"): (False, True, True),
                   ("planar", "primarySlideLimits"): (True, False, True),
                   ("planar", "secondarySlideLimits"): (False, True, False),
                   ("ball", "pitchLimits"): (True, False, False),
                   ("ball", "yawLimits"): (False, True, True),
                   ("ball", "rollLimits"): (False, False, True)}
    for case in cases:
        doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        try:
            design = adsk.fusion.Design.cast(doc.products.itemByProductType("DesignProductType"))
            design.designType = adsk.fusion.DesignTypes.ParametricDesignType
            root = design.rootComponent
            occurrences = []
            for index, name in enumerate(("Fixed", "Moving")):
                matrix = adsk.core.Matrix3D.create()
                matrix.translation = adsk.core.Vector3D.create(index*4, index, 0)
                occurrence = root.occurrences.addNewComponent(matrix)
                occurrence.component.name = name
                sketch = occurrence.component.sketches.add(occurrence.component.xYConstructionPlane)
                sketch.sketchCurves.sketchLines.addTwoPointRectangle(point(0, 0, 0), point(1, 1, 0))
                occurrence.component.features.extrudeFeatures.addSimple(sketch.profiles.item(0), value("10 mm"),
                                                                      adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
                occurrences.append(occurrence)
            occurrences[0].isGrounded = True
            geometries = [adsk.fusion.JointGeometry.createByPoint(o.component.originConstructionPoint.createForAssemblyContext(o))
                          for o in occurrences]
            if any(g is None for g in geometries):
                raise RuntimeError("Joint origin point geometry rejected")
            # Fusion moves the first joint occurrence; keep grounded geometry second.
            inputs = root.joints.createInput(geometries[1], geometries[0])
            if case.startswith("rigid"):
                ok = inputs.setAsRigidJointMotion()
            elif case == "revolute":
                ok = inputs.setAsRevoluteJointMotion(2)
            elif case == "slider":
                ok = inputs.setAsSliderJointMotion(0)
            elif case == "cylindrical":
                ok = inputs.setAsCylindricalJointMotion(1)
            elif case == "pin_slot":
                ok = inputs.setAsPinSlotJointMotion(2, 0)
            elif case == "planar":
                ok = inputs.setAsPlanarJointMotion(2)
            else:
                ok = inputs.setAsBallJointMotion(2, 0)
            if not ok:
                raise RuntimeError("Joint motion input rejected")
            inputs.angle = value("35 deg" if case == "rigid_flipped" else "15 deg")
            inputs.offset = value("6 mm" if case == "rigid_flipped" else "3 mm")
            inputs.isFlipped = case == "rigid_flipped"
            joint = root.joints.add(inputs)
            joint.name = "ProbeJoint"
            motion = motion_classes[case].cast(joint.jointMotion) if case in motion_classes else joint.jointMotion
            limits = {}
            for attr, values in limit_values.items():
                if not hasattr(motion, attr):
                    continue
                item = getattr(motion, attr)
                item.minimumValue, item.maximumValue, item.restValue = values
                flags = limit_flags.get((case, attr), (True, True, True))
                item.isMinimumValueEnabled, item.isMaximumValueEnabled, item.isRestValueEnabled = flags
                limits[attr] = {name: getattr(item, name) for name in
                                ("minimumValue", "maximumValue", "restValue", "isMinimumValueEnabled",
                                 "isMaximumValueEnabled", "isRestValueEnabled")}
            directions, vectors, current = {}, {}, {}
            for attr in ("rotationAxis", "slideDirection", "normalDirection", "primarySlideDirection", "pitchDirection", "yawDirection"):
                if hasattr(motion, attr):
                    directions[attr] = getattr(motion, attr)
            for attr in ("rotationAxisVector", "slideDirectionVector", "normalDirectionVector", "primarySlideDirectionVector",
                         "secondarySlideDirectionVector", "pitchDirectionVector", "yawDirectionVector", "rollDirectionVector"):
                if hasattr(motion, attr):
                    vectors[attr] = getattr(motion, attr).asArray()
            for attr in ("rotationValue", "slideValue", "primarySlideValue", "secondarySlideValue", "pitchValue", "yawValue", "rollValue"):
                if hasattr(motion, attr):
                    current[attr] = getattr(motion, attr)
            geometry_truth = []
            for geometry in (joint.geometryOrOriginOne, joint.geometryOrOriginTwo):
                geometry_truth.append({"geometry_type": geometry.geometryType, "key_point_type": geometry.keyPointType,
                                       "origin_cm": geometry.origin.asArray(),
                                       "primary_axis": geometry.primaryAxisVector.asArray(),
                                       "secondary_axis": geometry.secondaryAxisVector.asArray(),
                                       "third_axis": geometry.thirdAxisVector.asArray()})
            sample = {"file": case+".f3d", "settings": {"joint_type": motion.jointType,
                      "is_flipped": joint.isFlipped, "is_locked": joint.isLocked, "is_suppressed": joint.isSuppressed,
                      "angle_radians": joint.angle.value, "offset_cm": joint.offset.value,
                      "occurrence_one_name": joint.occurrenceOne.name, "occurrence_two_name": joint.occurrenceTwo.name,
                      "frame_one": joint.geometryOneTransform.asArray(), "frame_two": joint.geometryTwoTransform.asArray(),
                      "directions": directions, "vectors": vectors, "current_motion_values": current, "limits": limits,
                      "health_state": joint.healthState, "warning": joint.errorOrWarningMessage},
                      "joint_geometry": geometry_truth,
                      "occurrences": [{"name": o.name, "component_name": o.component.name,
                                       "transform": o.transform2.asArray()} for o in occurrences],
                      "parameters": [{"name": p.name, "role": p.role, "value": p.value, "unit": p.unit,
                                      "created_by": getattr(p.createdBy, "name", None)} for p in root.modelParameters]}
            if not design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(output/sample["file"]))):
                raise RuntimeError("Joint export failed")
            truth["samples"].append(sample)
        except Exception:
            truth["errors"].append({"case": case, "error": traceback.format_exc()})
        finally:
            doc.close(False)
            (output/"ground_truth.json").write_text(json.dumps(truth, indent=2))
    (output/"complete.txt").write_text("Joint exports finished; consult errors.\n")
