"""Run inside Autodesk Fusion's Scripts and Add-Ins dialog.

Creates local reference archives and checks ZIP encryption flags. No cloud save.
"""

import hashlib
import json
import math
from pathlib import Path
import traceback
import uuid
import zipfile

import adsk.core
import adsk.fusion


def inspect_archive(path):
    """Read archive members without extracting them or interpreting feature data."""
    members = []
    with zipfile.ZipFile(path) as archive:
        for entry in archive.infolist():
            encrypted = bool(entry.flag_bits & 1)
            item = {
                "name": entry.filename,
                "zip_encrypted": encrypted,
                "zip_compression_method": entry.compress_type,
                "uncompressed_bytes": entry.file_size,
                "compressed_bytes": entry.compress_size,
            }
            if not encrypted and not entry.is_dir():
                if entry.file_size > 64 * 1024 * 1024:
                    raise ValueError("Unexpectedly large reference archive member")
                payload = archive.read(entry)
                item["sha256"] = hashlib.sha256(payload).hexdigest()
                item["first_32_bytes_hex"] = payload[:32].hex()
            members.append(item)
    return {
        "file": path.name,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "members": members,
        "interpretation": (
            "ZIP encryption flags apply only to the archive layer. "
            "They do not establish whether internal payloads use encryption. "
            "Binary headers and hashes alone cannot establish encryption."
        ),
    }


def run(context):
    app = adsk.core.Application.get()
    ui = app.userInterface
    output = Path(__file__).resolve().parent / ("output-" + uuid.uuid4().hex[:12])
    output.mkdir()
    doc = None
    report = {"fusion_version": app.version, "samples": []}
    try:
        doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        design = adsk.fusion.Design.cast(doc.products.itemByProductType("DesignProductType"))
        if design is None:
            raise RuntimeError("New document has no Fusion design product")
        design.designType = adsk.fusion.DesignTypes.ParametricDesignType
        root = design.rootComponent
        sketch = root.sketches.add(root.xYConstructionPlane)
        sketch.sketchCurves.sketchCircles.addByCenterRadius(
            adsk.core.Point3D.create(0, 0, 0), 1.0
        )
        extrudes = root.features.extrudeFeatures
        extrusion_input = extrudes.createInput(
            sketch.profiles.item(0), adsk.fusion.FeatureOperations.NewBodyFeatureOperation
        )
        extent = adsk.fusion.DistanceExtentDefinition.create(
            adsk.core.ValueInput.createByString("7 mm")
        )
        if not extrusion_input.setOneSideExtent(
            extent, adsk.fusion.ExtentDirections.PositiveExtentDirection
        ):
            raise RuntimeError("Could not define the reference extrusion")
        extrusion = extrudes.add(extrusion_input)
        extrusion.name = "ReferenceExtrusion"
        distance = adsk.fusion.DistanceExtentDefinition.cast(extrusion.extentOne).distance
        for name, depth_mm in (
            ("depth07_a", 7), ("depth07_b", 7),
            ("depth13", 13), ("depth29", 29), ("depth07_return", 7),
        ):
            distance.expression = f"{depth_mm} mm"
            if not design.computeAll():
                raise RuntimeError(f"Recompute failed for {name}")
            body = root.bRepBodies.item(0)
            expected_volume_cm3 = math.pi * depth_mm / 10
            if root.bRepBodies.count != 1 or not math.isclose(
                body.volume, expected_volume_cm3, rel_tol=1e-7, abs_tol=1e-9
            ):
                raise RuntimeError(f"Unexpected reference geometry for {name}")
            path = output / (name + ".f3d")
            options = design.exportManager.createFusionArchiveExportOptions(str(path))
            if options is None or not design.exportManager.execute(options):
                raise RuntimeError(f"Fusion archive export failed for {name}")
            sample = inspect_archive(path)
            sample.update({
                "radius_mm": 10,
                "expected_depth_mm": depth_mm,
                "api_depth_cm": distance.value,
                "api_volume_cm3": body.volume,
            })
            report["samples"].append(sample)
            (output / "inspection.json").write_text(json.dumps(report, indent=2))
        doc.close(False)
        doc = None
        ui.messageBox(f"Reference files and archive inspection saved to:\n{output}")
    except Exception:
        # Leave a failed study document open so the error can be investigated.
        error = traceback.format_exc()
        (output / "error.txt").write_text(error)
        ui.messageBox(f"Reference generation failed:\n{error}\nOutput: {output}")
