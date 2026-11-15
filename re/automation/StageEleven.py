"""Replay the pinned P01, P03 and P04 discovery grid in an A03 runner."""

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

from CiBatchRelease import KIND, SCOPE, pending_input, resumed_member
from Corpus import git
from Records import canonical, digest
from Sessions import read_bounded, write_private

ROOT = Path(__file__).resolve().parents[2]
RECEIPTS = {
    "principal": {
        "principal-dispatch": "dispatch.json",
        "principal-plan": "readback.plan.json",
        "principal-measurements": "readback.measurements.json",
        "principal-receipt": "readback.receipt.json",
    },
    "cut": {
        "cut-plan": "plan.json",
        "cut-measurements": "measurements.json",
        "cut-receipt": "receipt.json",
    },
}
EXPECTED_COUNTS = {"P01": 6, "P03": 8, "P04": 11}


def pinned_checkout(revision):
    if (
        not isinstance(revision, str)
        or not re.fullmatch(r"[0-9a-f]{40}", revision)
        or git(ROOT, "rev-parse", "HEAD").decode().strip() != revision
        or git(
            ROOT,
            "status",
            "--porcelain",
            "--untracked-files=all",
            "--",
            "src",
            "re/automation",
        )
    ):
        raise ValueError("stage 11 requires the clean, exact candidate checkout")


def input_bytes(session, descriptor, limit):
    checksum = descriptor["sha256"]
    if (
        not re.fullmatch(r"[0-9a-f]{64}", checksum)
        or descriptor["path"] != f"inputs/{checksum}"
    ):
        raise ValueError("stage 11 input path does not match its content address")
    path = session / descriptor["path"]
    if path.resolve() != path:
        raise ValueError("stage 11 input escapes its private session")
    with path.open("rb") as source:
        content = source.read(limit + 1)
    if len(content) > limit or hashlib.sha256(content).hexdigest() != checksum:
        raise ValueError("stage 11 input differs from its immutable pin")
    return content


def observations(research, inputs, session):
    sys.path.insert(0, str(ROOT / "src"))
    from CutHistoryEvidence import report as cut
    from PrincipalReadbackEvidence import report as principal
    from RectanglePairEvidence import report as rectangles

    sources = {}
    for family, files in RECEIPTS.items():
        directory = research / family
        directory.mkdir()
        for role, name in files.items():
            (directory / name).write_bytes(
                input_bytes(session, inputs[role], 32 * 1024 * 1024)
            )
        sources[family] = directory
    reports, counterexamples = {}, []
    for name, reader, arguments in (
        (
            "principal",
            principal,
            (sources["principal"], inputs["principal-dispatch"]["sha256"]),
        ),
        ("rectangles", rectangles, (counterexamples,)),
        (
            "cut",
            cut,
            (sources["cut"], inputs["cut-receipt"]["sha256"], counterexamples),
        ),
    ):
        try:
            reports[name] = reader(*arguments)
        except (LookupError, ValueError) as error:
            counterexamples.append({"check": name, "reason": str(error)[:2048]})
    return reports, counterexamples


def rectangle_checks(row):
    geometry = row["rectangle"]
    yield geometry["perimeter"]["status"] == "equal", "perimeter comparison"
    yield geometry["frame"]["status"] == "equal", "sketch frame"
    yield geometry["axes"]["status"] == "equal", "axis constraints"
    yield geometry["origin"]["status"] == "equal_anchor", "origin coincidence"
    yield set(geometry["dimensions"]) == {"width_mm", "height_mm"}, "dimension roster"
    for name, dimension in geometry["dimensions"].items():
        yield dimension["status"] == "equal_same_side_and_magnitude", name
    if row["recipe_id"] == "P03":
        yield row["boss"]["status"] == "equal", "signed boss extent"


def cut_checks(row):
    yield row["body"]["status"] == "equal", "final body and independent measurements"
    history = row["history"]
    yield history["status"] == "bounded_role_correspondence", history.get(
        "reason", "history"
    )
    for name in (
        "base_direction",
        "cut_direction",
        "base_extent",
        "cut_extent",
        "cut_support_plane",
    ):
        yield history.get(name, {}).get("status") == "equal", name
    profiles = history.get("profiles", {})
    for name, expected in (
        ("base", "equal"),
        ("cut", "equal"),
        ("cut_positioning", "meaningfully_different"),
    ):
        yield profiles.get(name, {}).get("status") == expected, name


def assess(reports, counterexamples):
    rectangle = reports.get("rectangles", {})
    cut = reports.get("cut", {})
    principal = reports.get("principal", {})
    native = {
        (case["capture"], case["variant"]): case for case in principal.get("cases", [])
    }
    rebuilds = {
        row["variant"]: row["solidworks_rebuild_comparison"]
        for row in cut.get("historical_body_evidence", {}).get("pairs", [])
    }
    rows = [
        (r["recipe_id"], r["variant"], r, rectangle_checks(r))
        for r in rectangle.get("pairs", [])
    ]
    rows.extend(("P04", v, r, cut_checks(r)) for v, r in cut.get("pairs", {}).items())
    saves = {}
    for family, variant, row, checks in rows:
        sources = {name: source["sha256"] for name, source in row["sources"].items()}
        saves.setdefault(family, {})[variant] = sources
        unmet = [description for passed, description in checks if not passed]
        if family == "P04":
            rebuild = rebuilds.get(variant, {})
            if not (
                rebuild.get("counts_exact")
                and rebuild.get("within_declared_tolerances")
            ):
                unmet.append("independent SOLIDWORKS rebuild comparison")
        elif (
            native.get((family, variant), {}).get("native", {}).get("sha256")
            != sources["solidworks"]
        ):
            unmet.append("independent SOLIDWORKS readback pin")
        if unmet:
            counterexamples.append(
                {
                    "recipe": family,
                    "variant": variant,
                    "sources": sources,
                    "checks": unmet,
                }
            )
    counts = {family: len(variants) for family, variants in saves.items()}
    if counts != EXPECTED_COUNTS or len(rows) != sum(EXPECTED_COUNTS.values()):
        counterexamples.append(
            {
                "check": "paired save roster",
                "expected": EXPECTED_COUNTS,
                "observed": counts,
            }
        )
    for family, variants in saves.items():
        baseline, repeat = (
            variants.get(name, {}) for name in ("baseline-a", "baseline-b")
        )
        if not all(
            baseline.get(app) and repeat.get(app) and baseline[app] != repeat[app]
            for app in ("fusion", "solidworks")
        ):
            counterexamples.append(
                {"recipe": family, "check": "distinct repeat-save pins"}
            )
    for name, expected in (
        ("duplicate_geometric_counterpart", "ambiguous"),
        ("missing_perimeter_edge", "different"),
        ("opposite_signed_extent", "different"),
    ):
        if rectangle.get("controls", {}).get(name, {}).get("status") != expected:
            counterexamples.append({"check": name, "expected": expected})
    for name in (
        "public_baseline_solidworks_vs_through_all_fusion",
        "historical_baseline_solidworks_vs_through_all_fusion",
    ):
        if (
            cut.get("termination_difference_control", {}).get(name, {}).get("status")
            != "different"
        ):
            counterexamples.append({"check": name, "expected": "different"})
    return saves


def run(session):
    session = session.resolve()
    packet = read_bounded(session / "job.json")
    job = packet["job"]
    inputs = packet["inputs"]
    expected_roles = {"ci", *(role for family in RECEIPTS.values() for role in family)}
    if (
        packet["session_version"] != 1
        or job["kind"] != KIND
        or set(job["options"]) != {"candidate_revision"}
        or set(inputs) != expected_roles
    ):
        raise ValueError(
            "stage 11 session does not match the paired discovery runner contract"
        )
    revision = job["options"]["candidate_revision"]
    pinned_checkout(revision)
    ci = json.loads(input_bytes(session, inputs["ci"], 65536))
    resumed = canonical(ci) != canonical(pending_input(revision))
    if resumed:
        resumed_member(packet, ci)
    with TemporaryDirectory(prefix="stage-eleven-", dir=session) as directory:
        reports, counterexamples = observations(Path(directory), inputs, session)
    saves = assess(reports, counterexamples)
    pinned_checkout(revision)
    records = {
        "schema": 1,
        "scope": SCOPE,
        "candidate_revision": revision,
        "native_qualified": False,
        "fresh_native_fusion": "unverified",
        "evidence_sha256": {name: digest(report) for name, report in reports.items()},
        "saves": saves,
        "counterexamples": counterexamples,
    }
    if resumed:
        if not counterexamples and (
            digest(records) != ci["stage_record_sha256"]
            or digest(saves) != ci["saves_sha256"]
        ):
            counterexamples.append({"check": "replay differs from the exact parked evidence"})
        records["ci"] = {
            key: ci[key] for key in ("roster_sha256", "observation_sha256", "verification")
        }
    if counterexamples:
        outcome = "rejected"
        reason = "paired discovery grid contains counterexamples or missing comparisons"
    elif resumed:
        outcome = "completed"
        reason = "exact paired research replay and hosted archive compatibility verified"
    else:
        outcome = "waiting_ci"
        reason = "paired discovery grid and repeat saves agreed with independent observations"
    write_private(
        session / "result.json",
        {"outcome": outcome, "reason": reason, "records": records},
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("session", type=Path)
    arguments = parser.parse_args()
    try:
        run(arguments.session)
    except (
        OSError,
        ValueError,
        TypeError,
        KeyError,
        subprocess.SubprocessError,
    ) as error:
        parser.exit(1, f"stage 11 refused: {error}\n")
