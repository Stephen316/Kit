import hashlib
import json
import re
from pathlib import PurePosixPath

from Corpus import git, read_tree


SPEC_SHA256 = "3c93e024f9fbdda50e610bda3b363bf30e8e7cdc914ef0728087befe129951bf"
DISCOVERY = {
    "P01": ("solidworks-75b9308cf13e", 6, "3c389fe4069bece7ecf64f0294d111ce7f44131b2fc576d3f2ac4291e0fec7bf"),
    "P03": ("solidworks-db1390476325", 8, "f2308ae749f3d739746301873a49e997e2cf494f9d459e954403b66b17e22a94"),
    "P04": ("solidworks-c1986308375a", 11, "7fd2fffa3c690998753a80cab81da2f1c2446c9fcec39574e3983a7f4345cae5"),
}
CONTROL = "re/solidworks/examples/.SLDPRT/example.SLDPRT"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def capture_inputs(root, revision):
    entries = read_tree(root, revision)
    base = PurePosixPath("re/automation")

    def read_blob(path):
        blob = entries.get(str(path))
        require(blob is not None, f"missing file in capture revision: {path}")
        return git(root, "cat-file", "blob", blob)

    spec_bytes = read_blob(base / "PairSpecs.json")
    require(digest(spec_bytes) == SPEC_SHA256, "paired specification changed; review discovery inputs")
    specification = json.loads(spec_bytes)
    recipes = {recipe["id"]: recipe for recipe in specification["recipes"] if recipe["id"] in DISCOVERY}
    control_sha = digest(read_blob(CONTROL))
    rows = []
    for recipe_id, (folder, count, receipt_sha) in DISCOVERY.items():
        recipe = recipes[recipe_id]
        require(recipe["split"] == "discovery", f"ineligible discovery case: {recipe_id}")
        directory = base / "PairedCaptures" / recipe_id / folder
        rows.extend(read_capture(directory, recipe, count, receipt_sha, entries, read_blob, control_sha))
    return rows, specification["comparison_tolerances"]


def read_capture(directory, recipe, count, receipt_sha, entries, read_blob, control_sha):
    recipe_id = recipe["id"]
    receipt_bytes = read_blob(directory / "receipt.json")
    require(digest(receipt_bytes) == receipt_sha, f"capture receipt changed: {directory}")
    receipt = json.loads(receipt_bytes)
    measurement_bytes = read_blob(directory / "measurements.json")
    measurements = json.loads(measurement_bytes)
    expected_recipe = json.dumps(recipe, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    require(
        receipt["recipe_id"] == measurements["recipe_id"] == recipe_id
        and receipt["measurements"] == "measurements.json"
        and receipt["measurement_receipt_sha256"] == digest(measurement_bytes)
        and measurements["authoring_recipe_sha256"] == digest(expected_recipe)
        and measurements["specifications_sha256"] == SPEC_SHA256,
        f"capture evidence identity mismatch: {directory}",
    )
    require(
        not receipt["errors"] and not measurements["errors"]
        and receipt["native_files"] == measurements["saves"]
        and measurements["application"].casefold().startswith("solidworks")
        and measurements["exact_application_build"]
        and measurements["authoring_process_id"] != measurements["reopen_process_id"],
        f"capture status is incomplete: {directory}",
    )
    observations = measurements["observations"]
    for control in ("healthy_control_before", "healthy_control_after"):
        reading = observations[control]
        require(
            reading["native_sha256"] == control_sha and reading["body_count"] > 0
            and reading["volume_mm3"] > 0 and not any(reading["open_status"].values()),
            f"unverified control {control}: {directory}",
        )
    files = receipt["native_files"]
    reopened = observations["reopened_files"]
    require(
        len(files) == count == len(reopened) and {row["file"] for row in files} == reopened.keys(),
        f"capture receipt does not cover every reopened file: {directory}",
    )
    evidence = {
        "receipt_sha256": receipt_sha,
        "measurements_sha256": digest(measurement_bytes),
        "recipe_sha256": measurements["authoring_recipe_sha256"],
        "application_build": measurements["exact_application_build"],
        "executable_file_version": measurements["executable_file_version"],
    }
    return [
        capture_asset(directory, recipe_id, file, reopened[file["file"]], entries, read_blob, evidence)
        for file in files
    ]


def capture_asset(directory, recipe_id, file, reading, entries, read_blob, evidence):
    filename = file["file"]
    require(
        isinstance(filename, str) and re.fullmatch(rf"{recipe_id}-solidworks-[A-Za-z0-9_-]+\.SLDPRT", filename),
        f"invalid capture filename in {directory}",
    )
    path = directory / filename
    content = read_blob(path)
    require(
        len(content) == file["size_bytes"] and digest(content) == file["sha256"]
        and not file["save_errors"] and not file["save_warnings"]
        and not any(reading["open_status"].values()),
        f"invalid native capture or reopen evidence: {path}",
    )
    asset = {
        "path": str(path),
        "git_blob": entries[str(path)],
        "kind": "native",
        "format": "sldprt",
        "sha256": file["sha256"],
        "size_bytes": len(content),
        "prefix_hex": content[:16].hex(),
    }
    return recipe_id, asset, content, evidence, reading
