import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback


REPO = Path(__file__).resolve().parents[3]
CAPTURES = Path("re/automation/PairedCaptures")
TOOL = CAPTURES / "FusionFreshProcess.py"
HELPER = CAPTURES / "FusionCapture.py"
BINDINGS = CAPTURES / "FusionBindings.py"
SPEC = Path("re/automation/PairSpecs.json")
CONTROL = Path("re/Fusion/Study/thinextrudes-c1632bcb5efe/ordinary_rectangle_control.f3d")
RECIPES = ("P01", "P02", "P03", "P04")
SCHEMA = 1


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def file_digest(path):
    return digest(path.read_bytes())


def json_bytes(value):
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()


def write_new(path, content):
    with path.open("xb") as stream:
        stream.write(content)
        stream.flush()
        os.fsync(stream.fileno())


def write_json(path, value):
    content = json_bytes(value)
    write_new(path, content)
    return digest(content)


def git(*arguments):
    return subprocess.check_output(["git", "-C", str(REPO), *arguments])


def committed_file(revision, relative):
    path = REPO / relative
    content = git("show", f"{revision}:{relative.as_posix()}")
    require(not path.is_symlink() and path.read_bytes() == content,
            f"Worktree file differs from Git: {relative}")
    return {"path": relative.as_posix(), "sha256": digest(content), "size_bytes": len(content)}


def pinned_existing(revision, recipe_id):
    directory = CAPTURES / recipe_id
    entries = git("ls-tree", "-r", "--name-only", "-z", revision, "--", directory.as_posix())
    receipts = [Path(name) for name in entries.decode().split("\0")
                if "/fusion-" in name and name.endswith("/receipt.json")]
    require(len(receipts) == 1, f"Expected one committed Fusion receipt for {recipe_id}")
    receipt_path = receipts[0]
    receipt_pin = committed_file(revision, receipt_path)
    receipt = json.loads((REPO / receipt_path).read_bytes())
    require(receipt["recipe_id"] == recipe_id and receipt["measurements"] == "measurements.json"
            and receipt["errors"] == 0, f"Invalid existing receipt for {recipe_id}")
    measurements = committed_file(revision, receipt_path.parent / "measurements.json")
    require(measurements["sha256"] == receipt["measurement_receipt_sha256"],
            f"Existing measurements do not match the receipt: {recipe_id}")
    native = {}
    for label in ("a", "b"):
        name = f"{recipe_id}-fusion-baseline-{label}.f3d"
        records = [record for record in receipt["native_files"] if record["file"] == name]
        require(len(records) == 1, f"Expected one entry for {name}")
        pin = committed_file(revision, receipt_path.parent / name)
        require(pin["sha256"] == records[0]["sha256"] and pin["size_bytes"] == records[0]["size_bytes"],
                f"Existing archive does not match the receipt: {name}")
        native[label] = pin
    variants = {}
    require(2 <= len(receipt["native_files"]) <= 100, "Invalid native capture roster size")
    for record in receipt["native_files"]:
        name = record["file"]
        require(isinstance(name, str) and 1 <= len(name) <= 255 and Path(name).name == name
                and "\\" not in name and name.startswith(f"{recipe_id}-fusion-") and name.endswith(".f3d"),
                f"Invalid capture archive name for {recipe_id}")
        if name in (native["a"]["path"].rsplit("/", 1)[-1], native["b"]["path"].rsplit("/", 1)[-1]):
            continue
        require(name not in variants, f"Duplicate capture archive: {name}")
        pin = committed_file(revision, receipt_path.parent / name)
        require(pin["sha256"] == record["sha256"] and pin["size_bytes"] == record["size_bytes"],
                f"Existing archive does not match the receipt: {name}")
        variants[name] = pin
    require(len(native) + len(variants) == len(receipt["native_files"]), "Capture roster contains duplicate archives")
    return {"receipt": receipt_pin, "measurements": measurements, "archives": native, "variants": variants}


def launcher(tool_path, tool_hash, plan_path, plan_hash, phase):
    return f"""import hashlib
from pathlib import Path

tool = Path({str(tool_path)!r})
source = tool.read_bytes()
if hashlib.sha256(source).hexdigest() != {tool_hash!r}:
    raise RuntimeError("Fusion fresh-process tool changed after preparation")
scope = {{"__name__": "__kit_fusion_fresh_process__", "__file__": str(tool)}}
exec(compile(source, str(tool), "exec"), scope)
scope["run_phase"](Path({str(plan_path)!r}), {plan_hash!r}, {phase!r})
""".encode()


def prepare(output, recipes, include_existing):
    output = output.resolve()
    require(not output.is_relative_to(REPO), "Choose a new output directory outside the repository")
    require(not output.exists(), f"Output already exists: {output}")
    require(len(set(recipes)) == len(recipes), "Each recipe may be selected only once")
    revision = git("rev-parse", "--verify", "HEAD^{commit}").decode().strip()
    pins = {name: committed_file(revision, relative) for name, relative in
            (("tool", TOOL), ("helper", HELPER), ("bindings", BINDINGS), ("specification", SPEC), ("control", CONTROL))}
    plan = {
        "schema": SCHEMA,
        "source_revision": revision,
        "recipes": recipes,
        "pins": pins,
        "existing": {recipe: pinned_existing(revision, recipe) for recipe in recipes} if include_existing else {},
    }
    output.mkdir()
    path = output / "plan.json"
    plan_hash = write_json(path, plan)
    for phase in ("a", "b"):
        write_new(output / f"phase-{phase}.py",
                  launcher(REPO / TOOL, pins["tool"]["sha256"], path, plan_hash, phase))
    return {"run_directory": str(output), "source_revision": revision, "plan_sha256": plan_hash}


def checked_bytes(path, pin):
    require(not path.is_symlink() and path.is_file(), f"Expected a regular input file: {path}")
    content = path.read_bytes()
    require(len(content) == pin["size_bytes"] and digest(content) == pin["sha256"], f"Pinned file changed: {path}")
    return content


def process_info(pid):
    result = subprocess.run(["ps", "-p", str(pid), "-o", "lstart="], capture_output=True, text=True,
                            check=False, env=dict(os.environ, LC_ALL="C", TZ="UTC"))
    if result.returncode == 1 and not result.stdout.strip() and not result.stderr.strip():
        return None
    require(result.returncode == 0 and result.stdout.strip(), f"Could not verify process identity for PID {pid}")
    started = datetime.strptime(result.stdout.strip(), "%a %b %d %H:%M:%S %Y").replace(tzinfo=timezone.utc)
    return {"pid": pid, "start_unix_seconds": int(started.timestamp())}


def load_helper(pin, binding_pin):
    path = REPO / HELPER
    source = checked_bytes(path, pin)
    scope = {"__name__": "__kit_fusion_capture_primitives__", "__file__": str(path)}
    exec(compile(source, str(path), "exec"), scope)
    binding_path = REPO / BINDINGS
    binding_source = checked_bytes(binding_path, binding_pin)
    binding_scope = {"__name__": "__kit_fusion_binding_capture__", "__file__": str(binding_path)}
    exec(compile(binding_source, str(binding_path), "exec"), binding_scope)
    scope["capture_sketch_bindings"] = binding_scope["capture_sketch_bindings"]
    return scope


def last_error(app):
    try:
        code, message = app.getLastError()
        return {"code": code, "description": message}
    except Exception:
        return {"unavailable": traceback.format_exc()}


def import_document(app, source, reading, owned):
    diagnostic = {"return": None, "exception": None, "last_error_on_failure": None,
                  "aggregate_loader_warnings": None,
                  "aggregate_loader_warnings_reason": "The archive import API exposes no warning list"}
    reading["import"] = diagnostic
    try:
        options = app.importManager.createFusionArchiveImportOptions(str(source))
        options.isViewFit = False
        document = app.importManager.importToNewDocument(options)
        diagnostic["return"] = "document" if document is not None else "null"
    except Exception:
        diagnostic["last_error_on_failure"] = last_error(app)
        diagnostic["exception"] = traceback.format_exc()
        raise
    if document is None:
        diagnostic["last_error_on_failure"] = last_error(app)
        raise RuntimeError(f"Fusion returned no document for {source.name}")
    owned.append(document)
    return document


def measure(helper, document, label):
    reading = helper["measure"](document, label)
    design = helper["design_of"](document)
    sketches = design.rootComponent.sketches
    require(len(reading["sketches"]) == sketches.count, "Sketch collection changed during measurement")
    for index, snapshot in enumerate(reading["sketches"]):
        snapshot["bindings"] = helper["capture_sketch_bindings"](sketches.item(index), helper["point_mm"])
    states = {0: "healthy", 1: "warning", 2: "error", 3: "suppressed", 4: "rolled_back", 5: "unknown"}
    for item in reading["feature_tree"]:
        timeline = design.timeline.item(item["index"])
        entity = timeline.entity
        raw = int(timeline.healthState)
        item["health"] = {"raw": raw, "state": states.get(raw, "unrecognized"),
                          "message": getattr(entity, "errorOrWarningMessage", None) if entity is not None else None}
    return reading


# tokens can resolve to multiple descendants after a split, so only unique entities can match
def same_entity(design, first, second):
    left = design.findEntityByToken(first.entityToken)
    right = design.findEntityByToken(second.entityToken)
    return len(left) == len(right) == 1 and left[0] == right[0]


# each observation uses one rollback stage and restores the imported document before export
def measure_at_marker(timeline, feature, before, observe):
    original = timeline.markerPosition
    try:
        expected = feature.index + (0 if before else 1)
        require(feature.rollTo(before) and timeline.markerPosition == expected, "Fusion did not reach the requested timeline marker")
        return {"marker": expected, **observe()}
    except Exception:
        return {"status": "unavailable", "diagnostic": traceback.format_exc()}
    finally:
        if timeline.markerPosition != original:
            timeline.markerPosition = original
        require(timeline.markerPosition == original, "Fusion did not restore the original timeline marker")


# the associated sketch reference must match an actual boss end face at the source stage
def cut_support(helper, design, sketch, boss):
    adsk = helper["adsk"]
    reference = sketch.referencePlane
    face = adsk.fusion.BRepFace.cast(reference) if reference is not None else None
    if face is None:
        return {"status": "unresolved", "reference_type": getattr(reference, "objectType", None)}
    point = face.pointOnFace
    found, normal = face.evaluator.getNormalAtPoint(point)
    require(found and adsk.core.Plane.cast(face.geometry) is not None, "Fusion did not report a planar support normal")
    start_faces, end_faces = boss.startFaces, boss.endFaces
    start_matches = sum(same_entity(design, face, start_faces.item(i)) for i in range(start_faces.count))
    end_matches = sum(same_entity(design, face, end_faces.item(i)) for i in range(end_faces.count))
    body_matches = sum(same_entity(design, face.body, boss.bodies.item(i)) for i in range(boss.bodies.count))
    normal_world = list(normal.asArray())
    point_world_mm = helper["point_mm"](point)
    area_mm2 = face.area * 100
    require(
        all(math.isfinite(value) for value in [*normal_world, *point_world_mm, area_mm2]) and area_mm2 > 0,
        "Fusion reported invalid support geometry",
    )
    return {
        "status": "verified" if (start_matches, end_matches, body_matches) == (0, 1, 1) else "unresolved",
        "reference_type": reference.objectType,
        "boss_start_face_matches": start_matches,
        "boss_end_face_matches": end_matches,
        "boss_body_matches": body_matches,
        "normal_world": normal_world,
        "point_world_mm": point_world_mm,
        "signed_offset_mm": sum(a * b for a, b in zip(point_world_mm, normal_world)),
        "area_mm2": area_mm2,
    }


# an empty or unmatched participant list leaves body ownership unresolved
def cut_participants(design, cut, boss):
    participants = tuple(cut.participantBodies or ())
    bodies = boss.bodies
    matches = [sum(same_entity(design, participant, bodies.item(i)) for i in range(bodies.count))
               for participant in participants]
    return {
        "status": "verified" if matches == [1] else "unresolved",
        "participant_count": len(participants),
        "boss_body_count": bodies.count,
        "boss_body_matches_per_participant": matches,
    }


# preserve the normal import and rebuild observations before running rollback probes
def cut_reference_evidence(helper, document):
    design = helper["design_of"](document)
    timeline = design.timeline
    root = design.rootComponent
    sketch = root.sketches.itemByName("CutSketch")
    extrusions = root.features.extrudeFeatures
    boss = extrusions.itemByName("BlindBoss")
    cuts = [feature for name in ("BlindCut", "ThroughAllCut")
            if (feature := extrusions.itemByName(name)) is not None]
    if sketch is None or boss is None or len(cuts) != 1 or timeline.markerPosition != timeline.count:
        return {"status": "unresolved", "reason": "expected P04 actors at the end of the timeline"}
    (cut,) = cuts
    if not boss.timelineObject.index < sketch.timelineObject.index < cut.timelineObject.index:
        return {"status": "unresolved", "reason": "unexpected P04 feature order"}
    return {
        "scope": "after_normal_recompute",
        "support_after_sketch": measure_at_marker(timeline, sketch.timelineObject, False,
                                                  lambda: cut_support(helper, design, sketch, boss)),
        "participants_before_cut": measure_at_marker(timeline, cut.timelineObject, True,
                                                    lambda: cut_participants(design, cut, boss)),
    }


def recompute(helper, document, result, label, recipe_id=None):
    result["before_recompute"] = measure(helper, document, label + " before recompute")
    result["compute_all_return"] = helper["design_of"](document).computeAll()
    result["after_recompute"] = measure(helper, document, label + " after recompute")
    require(result["compute_all_return"] is True, f"Fusion recompute did not complete: {label}")
    for stage in ("before_recompute", "after_recompute"):
        for feature in result[stage]["feature_tree"]:
            require(feature["health"]["state"] == "healthy" and not feature["suppressed"]
                    and not feature["rolled_back"], f"Unhealthy feature {feature['name']}: {label} {stage}")
    if recipe_id == "P04":
        result["cut_reference_evidence"] = cut_reference_evidence(helper, document)


def check_baseline(helper, recipe, reading):
    basis = helper["BASE_PLANE"][recipe["id"]]
    for key in ("before_recompute", "after_recompute"):
        observed = reading[key]
        comparison = helper["compare"](recipe["id"], basis, recipe["driving_parameters"], observed)
        reading[key + "_comparison"] = comparison
        require(observed["design_type"] == "parametric" and observed["feature_tree"] and comparison["matches"],
                f"{recipe['id']} does not match the parametric baseline: {key}")
        if recipe["id"] in ("P01", "P02"):
            require(observed["body_count"] == 0, f"Unexpected body in {recipe['id']}: {key}")


def read_archive(helper, app, source, pin, owned, reading, recipe_id=None):
    checked_bytes(source, pin)
    reading["native_input"] = pin
    document = import_document(app, source, reading, owned)
    try:
        recompute(helper, document, reading, source.name, recipe_id)
    finally:
        checked_bytes(source, pin)
    return document


def measure_control(helper, app, pin, owned, report, label):
    snapshot = report[label] = {}
    document = read_archive(helper, app, REPO / CONTROL, pin, owned, snapshot)
    reading = snapshot["after_recompute"]
    expected = helper["CONTROL_VOLUME_MM3"]
    require(reading["body_count"] == 1 and reading["volume_mm3"] is not None
            and abs(reading["volume_mm3"] - expected) <= max(1e-6, 1e-9 * expected),
            f"Control failed: {label}")
    helper["close"](document, owned)


def save_archive(helper, document, output, name):
    path = output / name
    require(not path.exists(), f"Capture output already exists: {path}")
    saves = []
    helper["export"](document, path, saves)
    pin = saves[0]
    require(pin["size_bytes"] > 0, f"Fusion created an empty archive: {name}")
    checked_bytes(path, pin)
    return pin


def capture_first(helper, app, recipes, output, owned, report):
    def new_design(application):
        document = application.documents.add(helper["adsk"].core.DocumentTypes.FusionDesignDocumentType)
        require(document is not None, "Fusion did not create an owned design")
        owned.append(document)
        design = helper["design_of"](document)
        design.designType = helper["adsk"].fusion.DesignTypes.ParametricDesignType
        design.fusionUnitsManager.distanceDisplayUnits = helper["adsk"].fusion.DistanceUnits.MillimeterDistanceUnits
        return document, design, design.rootComponent

    helper["new_design"] = new_design
    for recipe in recipes:
        recipe_id = recipe["id"]
        row = report["captures"][recipe_id] = {}
        document = helper["BUILDERS"][recipe_id](app, {"basis": helper["BASE_PLANE"][recipe_id]})
        recompute(helper, document, row, "independently authored baseline A", recipe_id)
        check_baseline(helper, recipe, row)
        row["save_a"] = save_archive(helper, document, output, f"{recipe_id}-fusion-fresh-baseline-a.f3d")
        helper["close"](document, owned)


def prior_capture(output, plan_hash, process):
    receipt = json.loads((output / "phase-a/receipt.json").read_bytes())
    raw = (output / "phase-a/measurements.json").read_bytes()
    require(receipt["schema"] == SCHEMA and receipt["phase"] == "a" and receipt["plan_sha256"] == plan_hash
            and receipt["measurements_sha256"] == digest(raw) and receipt["status"] == "complete",
            "Phase A measurements do not match a complete receipt")
    first = json.loads(raw)
    require(first["phase"] == "a" and first["plan_sha256"] == plan_hash and first["status"] == "complete",
            "Phase A is incomplete or belongs to a different plan")
    old = first["process"]
    require(old["pid"] != process["pid"] and process_info(old["pid"]) is None
            and process["start_unix_seconds"] >= int(first["ended_unix_seconds"])
            and process["start_unix_seconds"] > old["start_unix_seconds"],
            "Phase B requires a new Fusion process started after completion and exit of phase A")
    return first, receipt["measurements_sha256"]


def capture_repeat(helper, app, recipes, output, owned, report, first, existing):
    for recipe in recipes:
        recipe_id = recipe["id"]
        row = report["captures"][recipe_id] = {}
        save_a = first["captures"][recipe_id]["save_a"]
        require(save_a["file"] == f"{recipe_id}-fusion-fresh-baseline-a.f3d", "Unexpected phase A archive name")
        reopened_a = row["fresh_reopen_a"] = {}
        document = read_archive(helper, app, output.parent / "phase-a" / save_a["file"], save_a, owned, reopened_a, recipe_id)
        check_baseline(helper, recipe, reopened_a)
        save_b = row["save_b"] = save_archive(helper, document, output, f"{recipe_id}-fusion-fresh-baseline-b.f3d")
        helper["close"](document, owned)
        reopened_b = row["repeat_readback_b"] = {}
        document = read_archive(helper, app, output / save_b["file"], save_b, owned, reopened_b, recipe_id)
        check_baseline(helper, recipe, reopened_b)
        helper["close"](document, owned)
        if recipe_id in existing:
            original = existing[recipe_id]
            row["existing_source_receipt"] = original["receipt"]
            row["existing_source_measurements"] = original["measurements"]
            for label, pin in original["archives"].items():
                reading = row[f"existing_readback_{label}"] = {}
                document = read_archive(helper, app, REPO / pin["path"], pin, owned, reading, recipe_id)
                check_baseline(helper, recipe, reading)
                helper["close"](document, owned)
            variants = row["existing_variant_readbacks"] = {}
            for name, pin in sorted(original["variants"].items()):
                reading = variants[name] = {}
                document = read_archive(helper, app, REPO / pin["path"], pin, owned, reading, recipe_id)
                helper["close"](document, owned)


def run_phase(plan_path, plan_hash, phase):
    import adsk.core

    require(sys.platform == "darwin", "Fresh-process evidence currently requires the macOS Fusion host")
    require(phase in ("a", "b"), "Invalid capture phase")
    raw = plan_path.read_bytes()
    require(digest(raw) == plan_hash, "Prepared plan changed")
    plan = json.loads(raw)
    recipes = plan["recipes"]
    require(plan["schema"] == SCHEMA and recipes and len(set(recipes)) == len(recipes)
            and all(recipe in RECIPES for recipe in recipes), "Invalid manifest or recipe is reserved")
    require(set(plan["existing"]) <= set(recipes), "Existing evidence includes an unselected recipe")
    pins = plan["pins"]
    spec = json.loads(checked_bytes(REPO / SPEC, pins["specification"]))
    selected = [next(recipe for recipe in spec["recipes"] if recipe["id"] == selected_id) for selected_id in recipes]
    helper = load_helper(pins["helper"], pins["bindings"])
    app = adsk.core.Application.get()
    require(app is not None and app.documents.count == 0, "Use an exclusive Fusion session with no open documents")
    process = process_info(os.getpid())
    require(process is not None, "Fusion process identity could not be measured")
    first = first_hash = None
    if phase == "b":
        first, first_hash = prior_capture(plan_path.parent, plan_hash, process)
        require(first["fusion_version"] == app.version, "Fusion build changed between capture phases")
    for original in plan["existing"].values():
        for key in ("receipt", "measurements"):
            checked_bytes(REPO / original[key]["path"], original[key])
    output = plan_path.parent / f"phase-{phase}"
    output.mkdir()
    report = {
        "schema": SCHEMA, "phase": phase, "status": "started", "plan_sha256": plan_hash,
        "source_revision": plan["source_revision"], "process": process, "fusion_version": app.version,
        "previous_measurements_sha256": first_hash, "pins": pins, "errors": [], "captures": {},
        "started_unix_seconds": time.time(), "claim": "supplemental source evidence",
        "configuration": "none", "basis": {recipe: helper["BASES"][helper["BASE_PLANE"][recipe]] for recipe in recipes},
        "authoring_recipe_sha256": {recipe["id"]: digest(helper["canonical"](recipe)) for recipe in selected},
    }
    owned = []
    try:
        measure_control(helper, app, pins["control"], owned, report, "healthy_control_before")
        if phase == "a":
            capture_first(helper, app, selected, output, owned, report)
        else:
            capture_repeat(helper, app, selected, output, owned, report, first, plan["existing"])
        measure_control(helper, app, pins["control"], owned, report, "healthy_control_after")
    except Exception:
        report["errors"].append(traceback.format_exc())
    finally:
        for document in list(owned):
            try:
                helper["close"](document, owned)
            except Exception:
                report["errors"].append(traceback.format_exc())
        try:
            require(app.documents.count == 0, "Documents remain open after the owned-document cleanup")
        except Exception:
            report["errors"].append(traceback.format_exc())
        report["ended_unix_seconds"] = time.time()
        report["status"] = "failed" if report["errors"] else "complete"
        measurement_hash = write_json(output / "measurements.json", report)
        write_json(output / "receipt.json", {"schema": SCHEMA, "phase": phase, "status": report["status"],
                                            "measurements_sha256": measurement_hash, "plan_sha256": plan_hash})
    require(not report["errors"], f"Fusion evidence capture failed. Read {output / 'measurements.json'}")


def main():
    parser = argparse.ArgumentParser(description="Prepare an isolated two-process Fusion evidence capture")
    parser.add_argument("--output", type=Path, required=True, help="new directory outside the repository")
    parser.add_argument("--recipe", action="append", choices=RECIPES, required=True)
    parser.add_argument("--read-existing", action="store_true", help="also read the exact committed baseline A and B")
    arguments = parser.parse_args()
    print(json.dumps(prepare(arguments.output, arguments.recipe, arguments.read_existing), indent=2))


if __name__ == "__main__":
    main()
