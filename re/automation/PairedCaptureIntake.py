import argparse
import hashlib
import json
import math
import re
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path, PurePosixPath

from Corpus import asset_kind, git, read_tree


CAPTURES = "re/automation/PairedCaptures/"
SPECIFICATIONS = "re/automation/PairSpecs.json"
HISTORICAL_CORPUS = "re/automation/Corpus.json"
APPLICATIONS = {
    "fusion": ("Autodesk Fusion", ".f3d"),
    "solidworks": ("SOLIDWORKS", ".SLDPRT"),
}
CONTROLS = {
    "fusion": "re/Fusion/Study/thinextrudes-c1632bcb5efe/ordinary_rectangle_control.f3d",
    "solidworks": "re/solidworks/examples/.SLDPRT/example.SLDPRT",
}
SPLITS = {
    "discovery": "discovery",
    "qualification": "qualification_with_frozen_rules",
    "holdout": "holdout_with_frozen_rules",
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def canonical_digest(recipe):
    return sha256(json.dumps(
        recipe, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8"))


class GitSnapshot:
    def __init__(self, root):
        self.root = root
        self.trees = {}
        self.ancestry = {}

    def tree(self, revision):
        if revision not in self.trees:
            self.trees[revision] = read_tree(self.root, revision)
        return self.trees[revision]

    def blob(self, revision, path):
        entry = self.tree(revision).get(path)
        require(entry is not None, f"{path} is absent from {revision}")
        return git(self.root, "cat-file", "blob", entry)

    def document(self, revision, path):
        return self.parse_document(self.blob(revision, path), path)

    @staticmethod
    def parse_document(data, path):
        require(len(data) <= 32 * 1024 * 1024, f"{path} exceeds the JSON intake limit")
        document = json.loads(data)
        require(isinstance(document, dict), f"{path} is not a JSON object")
        return document

    def introduction(self, revision, path):
        result = git(
            self.root, "log", "--format=%H", "--diff-filter=A", "--no-renames",
            revision, "--", path,
        ).decode("ascii").splitlines()
        require(len(result) == 1, f"{path} does not have a single Git introduction")
        return result[0]

    def preceding_objects(self, revision):
        if revision not in self.ancestry:
            self.ancestry[revision] = set(git(
                self.root, "rev-list", "--objects", "--no-object-names", revision + "^@"
            ).decode("ascii").splitlines())
        return self.ancestry[revision]


def recipe_roster(specs):
    require(specs["specification_version"] == 1, "unsupported paired specifications")
    recipes = {row["id"]: row for row in specs["recipes"]}
    require(len(recipes) == len(specs["recipes"]), "duplicate recipe identity")
    for recipe_id, recipe in recipes.items():
        require(re.fullmatch(r"P[0-9]{2}", recipe_id), "invalid recipe identity")
        split = recipe["split"]
        require(split in SPLITS, f"{recipe_id} has an unknown split")
        reservations = [
            name for name in SPLITS if recipe["family"] in specs["split_policy"][name]
        ]
        require(reservations == [split], f"{recipe_id} conflicts with its family split")
    return recipes


def expected_variants(recipe):
    variants = {"baseline-a", "baseline-b", "units-inch"}
    for edit in recipe["independent_edits"]:
        variants.add(f"edit-{edit['parameter']}-{edit['value']}")
    history = recipe["feature_history"]
    if "revolution" not in history:
        variants.add("plane-yz")
    if "blind-boss" in history and "blind-cut" not in history:
        variants.add("direction-negative")
    if "blind-cut" in history:
        variants.add("termination-through-all")
    return variants


def capture_receipts(tree, recipes):
    receipts = {}
    for path in sorted(tree):
        if not path.startswith(CAPTURES) or not path.endswith("/receipt.json"):
            continue
        parts = PurePosixPath(path[len(CAPTURES):]).parts
        require(len(parts) == 3, f"receipt is outside its recipe capture directory: {path}")
        recipe_id, directory, _ = parts
        match = re.fullmatch(r"(fusion|solidworks)-[a-f0-9]{12}", directory)
        require(recipe_id in recipes and match is not None, f"unexpected capture directory: {path}")
        key = (recipe_id, match[1])
        require(key not in receipts, f"multiple receipts for {recipe_id}/{match[1]}")
        receipts[key] = path
    expected = {(recipe_id, app) for recipe_id in recipes for app in APPLICATIONS}
    require(set(receipts) == expected, f"missing capture receipts: {sorted(expected - set(receipts))}")
    return receipts


def verify_native_files(git_data, revision, receipt_path, recipe, app, saved):
    folder = receipt_path.rsplit("/", 1)[0]
    extension = APPLICATIONS[app][1]
    names = {
        f"{recipe['id']}-{app}-{variant}{extension}": variant
        for variant in expected_variants(recipe)
    }
    require(len(saved) == len(names) and {item["file"] for item in saved} == set(names),
            f"{receipt_path} does not list the exact prescribed variant roster")
    require([names[item["file"]] for item in saved[:2]] == ["baseline-a", "baseline-b"],
            f"{receipt_path} does not start with the two baseline saves")
    tree = git_data.tree(revision)
    inventory = []
    for save in saved:
        path = f"{folder}/{save['file']}"
        data = git_data.blob(revision, path)
        digest = sha256(data)
        require(len(data) == save["size_bytes"] and digest == save["sha256"],
                f"native bytes do not match the receipt: {path}")
        require(save.get("save_errors", 0) == 0 and save.get("save_warnings", 0) == 0,
                f"the receipt records a failed or warned save: {path}")
        inventory.append({
            "path": path,
            "git_blob": tree[path],
            "sha256": digest,
            "size_bytes": len(data),
            "variant": names[save["file"]],
        })
    return inventory


def control_binding(git_data, revision, app, observations, tolerances):
    path = CONTROLS[app]
    digest = sha256(git_data.blob(revision, path))
    before, after = (observations[f"healthy_control_{moment}"] for moment in ("before", "after"))
    for control in (before, after):
        require(control["body_count"] > 0 and control["volume_mm3"] > 0, f"invalid {app} control")
        if app == "fusion":
            require(control["healthy"] is True and control["file"] == path and control["sha256"] == digest,
                    "Fusion control is unhealthy or its identity differs from Git")
            require(math.isclose(control["volume_mm3"], control["expected_volume_mm3"],
                                 rel_tol=tolerances["volume_relative"],
                                 abs_tol=tolerances["volume_mm3_absolute"]),
                    "Fusion control volume differs from the capture expectation")
        else:
            require(control["open_status"] == {"errors": 0, "warnings": 0}
                    and control["native_sha256"] == digest, "SOLIDWORKS control status or hash mismatch")
    require(
        before["body_count"] == after["body_count"]
        and math.isclose(before["volume_mm3"], after["volume_mm3"],
                         rel_tol=tolerances["volume_relative"], abs_tol=tolerances["volume_mm3_absolute"])
        and len(before["center_of_mass_mm"]) == len(after["center_of_mass_mm"]) == 3
        and all(math.isclose(first, second, rel_tol=0, abs_tol=tolerances["length_mm_absolute"])
                for first, second in zip(before["center_of_mass_mm"], after["center_of_mass_mm"], strict=True)),
        f"{app} controls differ across the capture",
    )
    return {"path": path, "sha256": digest}


SOLIDWORKS_HARNESS = CAPTURES + "SolidWorksAuthoring/SolidWorksCapture.cs"
SOLIDWORKS_HARNESS_SHA = "0e90cdfc47f4295e15907505c9870620bb8fab2f82437d57a7f7521c22adb238"


def authoring_provenance(git_data, revision, introduction, app, measurements, specs_digest):
    recipe_id = measurements["recipe_id"]
    if app == "solidworks":
        source_revision = measurements["source_revision"]
        git_data.tree(source_revision)
        require(git(git_data.root, "merge-base", source_revision, introduction).decode("ascii").strip()
                == source_revision, f"{recipe_id} SOLIDWORKS source is outside introduction ancestry")
        require(sha256(git_data.blob(source_revision, SPECIFICATIONS)) == specs_digest,
                f"{recipe_id} SOLIDWORKS authoring specification differs from the pinned source")
        result = {"source_revision": source_revision, "generator_status": "uncommitted_capture_harness"}
        if SOLIDWORKS_HARNESS in git_data.tree(revision):
            require(sha256(git_data.blob(revision, SOLIDWORKS_HARNESS)) == SOLIDWORKS_HARNESS_SHA,
                    "retained SOLIDWORKS capture harness differs from the audited source")
            result.update(
                generator_status="retained_audited_source",
                generator_sha256={SOLIDWORKS_HARNESS: SOLIDWORKS_HARNESS_SHA},
            )
        return result

    require(sha256(git_data.blob(introduction, SPECIFICATIONS)) == specs_digest,
            f"{recipe_id} Fusion authoring specification differs from the pinned source")
    sources = {
        f"{CAPTURES}{recipe_id}/GenerateFusion.py": measurements["generator_sha256"],
    }
    if "shared_capture_sha256" in measurements:
        sources[f"{CAPTURES}FusionCapture.py"] = measurements["shared_capture_sha256"]
    for path, digest in sources.items():
        require(sha256(git_data.blob(introduction, path)) == digest, f"generator digest mismatch: {path}")
    return {
        "source_revision": introduction,
        "generator_status": "verified_committed_source",
        "generator_sha256": sources,
    }


def check_recording(app, recipe, observations, measurements, saves):
    require(all(isinstance(observations[key], dict) and observations[key]
                for key in ("baseline", "fresh_reopen", "unchanged_rebuild")),
            f"{app} has no baseline, reopen, or rebuild record")
    edits = observations["edits"]
    expected = [edit["parameter"] for edit in recipe["independent_edits"]]
    require(all(isinstance(edit["edited"], dict) and edit["edited"]
                and isinstance(edit["restored"], dict) and edit["restored"] for edit in edits),
            f"{app} lacks an edit or restore record")
    names = {PurePosixPath(item["path"]).name: item["variant"] for item in saves}
    expected_variants = {
        name for name in names.values() if not name.startswith(("baseline-", "edit-"))
    }
    if app == "solidworks":
        require([edit["parameter"] for edit in edits] == expected, "SOLIDWORKS edit order mismatch")
        for recorded, specified in zip(edits, recipe["independent_edits"], strict=True):
            require(names[recorded["saved_file"]] == f"edit-{specified['parameter']}-{specified['value']}",
                    "SOLIDWORKS edit record names the wrong export")
        variants = observations["variants"]
        require(len(variants) == len(expected_variants)
                and {item["variant"] for item in variants} == expected_variants
                and all(isinstance(item["reading"], dict) and item["reading"] for item in variants),
                "SOLIDWORKS variant observations differ from the prescribed saves")
        reopened = observations["reopened_files"]
        require(set(reopened) <= set(names), "SOLIDWORKS readback names an unknown save")
        require(all(isinstance(item, dict) and item for item in reopened.values()),
                "SOLIDWORKS readback lacks an observation object")
        diagnostics = {
            names[name] for name, item in reopened.items()
            if item.get("open_status") == {"errors": 0, "warnings": 0}
        }
        author_pid, reopen_pid = (measurements.get(f"{phase}_process_id") for phase in ("authoring", "reopen"))
        return set(names[name] for name in reopened), diagnostics, bool(
            author_pid and reopen_pid and author_pid != reopen_pid
        )

    require([edit["edit"]["parameter"] for edit in edits] == expected, "Fusion edit order mismatch")
    for recorded, specified in zip(edits, recipe["independent_edits"], strict=True):
        require(names[recorded["export"]] == f"edit-{specified['parameter']}-{specified['value']}",
                "Fusion edit record names the wrong export")
    variants = observations.get("variants")
    if variants is None:
        variants = [observations["units_inch"], observations["plane_yz"]]
    require(len(variants) == len(expected_variants)
            and {names[item["export"]] for item in variants} == expected_variants,
            "Fusion variant observations differ from the prescribed saves")
    readbacks = ["baseline-a"]
    for record in [*edits, *variants]:
        if isinstance(record.get("reopened"), dict) and record["reopened"]:
            readbacks.append(names[record["export"]])
    require(len(readbacks) == len(set(readbacks)), "Fusion readback names the same export twice")
    return set(readbacks), set(), False


def inspect_capture(git_data, revision, receipt_path, recipe, app, specs, specs_digest):
    folder = receipt_path.rsplit("/", 1)[0]
    receipt = git_data.document(revision, receipt_path)
    require(receipt["recipe_id"] == recipe["id"] and receipt["measurements"] == "measurements.json"
            and receipt["errors"] == 0, f"capture receipt is invalid: {receipt_path}")
    measurements_path = f"{folder}/measurements.json"
    measurement_bytes = git_data.blob(revision, measurements_path)
    receipt_digest = sha256(measurement_bytes)
    require(receipt_digest == receipt["measurement_receipt_sha256"],
            f"measurement digest mismatch: {measurements_path}")
    measurements = git_data.parse_document(measurement_bytes, measurements_path)
    require(receipt["native_files"] == measurements["saves"] and not measurements["errors"],
            f"receipt and measurement saves or status disagree: {receipt_path}")
    require(measurements["recipe_id"] == recipe["id"]
            and measurements["application"].startswith(APPLICATIONS[app][0])
            and measurements["exact_application_build"] and measurements["authoring_origin"]
            and measurements["world_basis"], f"capture identity or authoring metadata mismatch: {receipt_path}")
    recipe_digest = canonical_digest(recipe)
    require(measurements["specifications_sha256"] == specs_digest
            and measurements["authoring_recipe_sha256"] == recipe_digest, f"recipe digest mismatch: {receipt_path}")
    introduction = git_data.introduction(revision, receipt_path)
    require(all(git_data.tree(revision)[path] == git_data.tree(introduction).get(path)
                for path in (receipt_path, measurements_path)),
            f"capture evidence has changed since introduction: {receipt_path}")
    provenance = authoring_provenance(git_data, revision, introduction, app, measurements, specs_digest)
    files = verify_native_files(git_data, revision, receipt_path, recipe, app, receipt["native_files"])
    require(all(item["git_blob"] == git_data.tree(introduction).get(item["path"]) for item in files),
            f"native files have changed since capture introduction: {receipt_path}")
    previous = git_data.preceding_objects(introduction)
    for item in files:
        item["already_in_introduction_ancestry"] = item["git_blob"] in previous
    observations = measurements["observations"]
    control = control_binding(git_data, revision, app, observations, specs["comparison_tolerances"])
    readbacks, diagnostics, restarted = check_recording(app, recipe, observations, measurements, files)
    variants = {file["variant"] for file in files}
    blockers = []
    if not restarted:
        blockers.append("fresh_application_process_unrecorded")
    if variants - readbacks:
        blockers.append("saved_variant_readback_missing")
    if variants - diagnostics:
        blockers.append("explicit_load_diagnostics_missing")
    if app == "fusion":
        blockers.append("sketch_relation_participants_unrecorded")
    elif provenance["generator_status"] != "retained_audited_source":
        blockers.append("authoring_harness_not_pinned")
    blockers.append("complete_dimension_targets_unrecorded")
    if "face-supported-cut-sketch" in recipe["feature_history"]:
        blockers.append("supporting_face_identity_unrecorded")
    return {
        "recipe_id": recipe["id"],
        "family": recipe["family"],
        "split": recipe["split"],
        "application": app,
        "application_build": measurements["exact_application_build"],
        "executable_file_version": measurements.get("executable_file_version"),
        "canonical_recipe_sha256": recipe_digest,
        "introduction_revision": introduction,
        "receipt": {"path": receipt_path, "sha256": sha256(git_data.blob(revision, receipt_path))},
        "measurements": {"path": measurements_path, "sha256": receipt_digest},
        "authoring_origin": measurements["authoring_origin"],
        "provenance": provenance,
        "control": control,
        "native_files": files,
        "recording_coverage": {
            "readback_count": len(readbacks),
            "missing_readbacks": sorted(variants - readbacks),
            "clean_load_diagnostic_count": len(diagnostics),
            "repeat_save_used_fresh_application_process": restarted,
        },
        "qualification_blockers": blockers,
    }


def protect_aliases(captures, tree, historical):
    owners = {
        item["path"]: capture["family"] for capture in captures for item in capture["native_files"]
    }
    object_ids = {item["git_blob"] for capture in captures for item in capture["native_files"]}
    aliases = defaultdict(set)
    for path, blob_id in tree.items():
        if blob_id in object_ids:
            aliases[blob_id].add(path)
    old_hashes = defaultdict(set)
    require(historical["manifest_version"] == 1, "unsupported historical corpus manifest")
    for asset in historical["assets"]:
        if asset["kind"] == "native":
            old_hashes[asset["sha256"]].add(asset["path"])
    quarantined = set()
    for capture in captures:
        family = capture["family"]
        for item in capture["native_files"]:
            current = aliases[item["git_blob"]] - {item["path"]}
            historical_paths = old_hashes[item["sha256"]]
            item["git_tree_aliases"] = sorted(current)
            item["historical_corpus_aliases"] = sorted(historical_paths)
            if item["already_in_introduction_ancestry"] or historical_paths or any(
                owners.get(path) != family for path in current
            ):
                quarantined.add(family)
    for capture in captures:
        if capture["family"] in quarantined:
            capture["qualification_blockers"].append("native_blob_alias_or_reuse")
            capture["permitted_use"] = "quarantine"
        else:
            capture["permitted_use"] = SPLITS[capture["split"]]
    return sorted(quarantined)


def intake(root, revision):
    git_data = GitSnapshot(root)
    tree = git_data.tree(revision)
    spec_bytes = git_data.blob(revision, SPECIFICATIONS)
    specs_digest = sha256(spec_bytes)
    specs = git_data.parse_document(spec_bytes, SPECIFICATIONS)
    recipes = recipe_roster(specs)
    captures = [
        inspect_capture(git_data, revision, path, recipes[recipe_id], app, specs, specs_digest)
        for (recipe_id, app), path in capture_receipts(tree, recipes).items()
    ]
    listed = {item["path"] for capture in captures for item in capture["native_files"]}
    actual = {path for path in tree if path.startswith(CAPTURES) and asset_kind(path) == "native"}
    require(listed == actual, f"unbound native captures: {sorted(actual - listed)}")
    historical = git_data.document(revision, HISTORICAL_CORPUS)
    quarantined = protect_aliases(captures, tree, historical)
    blocked_recipes = {capture["recipe_id"] for capture in captures if capture["qualification_blockers"]}
    return {
        "report_version": 1,
        "source_revision": revision,
        "specifications_sha256": specs_digest,
        "historical_corpus_source_revision": historical["source_revision"],
        "qualification_scope": "recorded_capture_provenance_and_coverage_only",
        "captures": captures,
        "quarantined_families": quarantined,
        "summary": {
            "paired_recipes": len(recipes),
            "capture_receipts": len(captures),
            "native_files": len(listed),
            "native_files_by_reserved_split": dict(sorted(Counter(
                capture["split"] for capture in captures for _ in capture["native_files"]
            ).items())),
            "qualified_pairs": len(set(recipes) - blocked_recipes),
            "blocked_recipes": sorted(blocked_recipes),
        },
    }


def main():
    parser = argparse.ArgumentParser(description="Bind paired capture receipts to a pinned Git tree")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--revision", required=True, help="full source commit SHA")
    parser.add_argument("--require-pairs", action="store_true")
    args = parser.parse_args()
    try:
        report = intake(args.root, args.revision)
        print(json.dumps(report, indent=2, sort_keys=True, allow_nan=False))
    except (AttributeError, KeyError, OSError, RecursionError, TypeError, ValueError,
            subprocess.SubprocessError) as exc:
        print(f"paired capture intake failed: {exc}", file=sys.stderr)
        return 1
    if report["quarantined_families"] or (args.require_pairs and report["summary"]["blocked_recipes"]):
        print("blocked: paired capture qualification gaps", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
