# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import hashlib
import json
from pathlib import Path
import re

# The P03 plan is scoped to one source-derived first blind Boss.
SCOPE = "fusion-source-derived-p03-boss-baseline"

# The accepted source baseline is encoded as measured dimensions in world millimetres.
ORIGINAL_MM = (40, 20, 10)

# Each independent edit is pinned by the source discovery measurement.
EDITS_MM = {"width_mm": 41, "height_mm": 23, "depth_mm": 12}

# The expected native timeline comes from the authored target feature names.
FEATURES = ("RectangleSketch", "BlindBoss")

# Prepared archives are admitted only from this private input roster.
ARCHIVE = "P03-baseline-a.f3d"

# The generation proof retains the exact independent source measurements and archives.
MANIFEST = "P03CandidateEvidence.json"

# Resolve the project from the pinned helper path in either embedded or command-line Python.
REPO = Path(__file__).resolve().parents[4]

# Bind each executable source and the previously licensed healthy control.
AUTHORING = Path("re/Fusion/Reconstruction/DimensionAuthoring")

# Use the existing measurement and process boundary without editing its source.
CAPTURES = Path("re/automation/PairedCaptures")

# The runtime loads this exact roster and the offline verifier resolves it to Git.
PINS = {
    "plan": AUTHORING / "SourceBossPlan.py",
    "runtime": AUTHORING / "SourceBossRun.py",
    "measure": AUTHORING / "SourceBossMeasure.py",
    "verifier": AUTHORING / "SourceBossWitness.py",
    "sketch_custody": AUTHORING / "ProbeAcceptance.py",
    "sketch_receipts": AUTHORING / "VerifyWitness.py",
    "sketch_measurements": AUTHORING / "WitnessMeasurements.py",
    "shape": AUTHORING / "ProbeAcceptanceShape.py",
    "fresh_process": CAPTURES / "FusionFreshProcess.py",
    "helper": CAPTURES / "FusionCapture.py",
    "bindings": CAPTURES / "FusionBindings.py",
    "control": Path(
        "re/Fusion/Study/thinextrudes-c1632bcb5efe/ordinary_rectangle_control.f3d"
    ),
}

# Keep input reads bounded separately from native archive sizes.
METADATA_LIMIT = 1024 * 1024

# Fusion archive input and restored bytes share the existing preparation bounds.
ARCHIVE_LIMIT = 256 * 1024 * 1024


# A failed invariant aborts before the witness can claim completion.
def require(condition, message):
    if not condition:
        raise ValueError(message)


# Accept exact hash strings from the operator's independent custody handoff.
def check_digest(value):
    require(
        isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value),
        "Expected lowercase SHA-256",
    )
    return value


# Seal the bytes that actually cross the licensed process boundary.
def pin(content):
    return {"sha256": hashlib.sha256(content).hexdigest(), "size_bytes": len(content)}


# Refuse oversized, missing or redirected inputs before parsing or executing them.
def read_file(path, limit=METADATA_LIMIT):
    require(
        path.is_file() and not path.is_symlink(),
        f"Expected a direct input file: {path}",
    )
    with path.open("rb") as stream:
        data = stream.read(limit + 1)
    require(0 < len(data) <= limit, f"Input is empty or exceeds its bound: {path}")
    return data


# Match both independently supplied digest and length before consuming any bytes.
def read_pinned(path, expected, limit=METADATA_LIMIT):
    data = read_file(path, limit)
    require(
        all(expected[key] == value for key, value in pin(data).items()),
        f"Pinned bytes changed: {path}",
    )
    return data


# JSON proof keys must have one unambiguous meaning across readers.
def unique_object(pairs):
    result = dict(pairs)
    require(len(result) == len(pairs), "Duplicate witness JSON key")
    return result


# Refuse nonstandard numeric constants in retained observation data.
def reject_constant(value):
    raise ValueError(f"Non-finite witness JSON constant: {value}")


# Preserve actual receipt bytes and verify them before extracting the object.
def read_object(path, digest):
    raw = read_file(path)
    require(
        pin(raw)["sha256"] == check_digest(digest),
        f"Witness JSON digest changed: {path}",
    )
    row = json.loads(
        raw, object_pairs_hook=unique_object, parse_constant=reject_constant
    )
    require(isinstance(row, dict), f"Expected a witness JSON object: {path}")
    return raw, row


# Native code is executed only after its exact content has matched the sealed plan.
def load_helper(relative, expected):
    path = REPO / relative
    source = read_pinned(path, expected)
    scope = {"__name__": "__kit_source_boss_helper__", "__file__": str(path)}
    exec(compile(source, str(path), "exec"), scope)
    return scope


# Local paths cannot redirect prepared or retained evidence through a symlink.
def direct_directory(path):
    path = path.absolute()
    require(
        path.is_dir() and path.resolve() == path,
        f"Expected a direct witness directory: {path}",
    )
    return path


# Both phases use the same exact input archive and offline generation proof.
def prepared_input(root, plan):
    inputs = direct_directory(root / "inputs")
    rows = plan["candidate"]
    require(
        rows["input"]["file"] == ARCHIVE and rows["manifest"]["file"] == MANIFEST,
        "Prepared P03 input names differ",
    )
    archive = inputs / ARCHIVE
    read_pinned(inputs / MANIFEST, rows["manifest"])
    read_pinned(archive, rows["input"], ARCHIVE_LIMIT)
    return archive


# Check the sealed plan scope before running any CAD code or accepting receipts.
def read_plan(path, digest):
    _, plan = read_object(path, digest)
    require(
        type(plan["schema"]) is int
        and plan["schema"] == 1
        and plan["scope"] == SCOPE
        and type(plan["prepared_unix_seconds"]) is int
        and plan["prepared_unix_seconds"] > 0
        and re.fullmatch(r"[0-9a-f]{40}", plan["source_revision"])
        and re.fullmatch(r"[0-9]+(?:\.[0-9]+){2}", plan["fusion_version"])
        and set(plan["pins"]) == set(PINS),
        "Invalid prepared P03 plan",
    )
    prepared_input(path.parent, plan)
    return plan
