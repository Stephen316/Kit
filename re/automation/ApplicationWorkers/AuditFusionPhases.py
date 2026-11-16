import argparse
import json
import re
import sqlite3
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from AcknowledgeApplication import accepted_output, stored_bytes
from Adapters import copy_verified
from ApplicationProtocol import configuration, record, require, sha256
from Artifacts import Artifacts
from FusionPhasePlan import (
    CASES,
    check_scope_archives,
    check_scope_report,
    phase_identity,
    phase_options,
    phase_paths,
    phase_rule,
    plan_scope,
)
from FusionPhaseTiming import busy_window, phase_timing, validate_window
from FusionTimeoutAudit import inspect_spool, parked_timeout
from OutputManifest import output_manifest
from Records import canonical, digest, label, specification
from StoreRead import read_store


class StoreSnapshot:
    def __init__(self, database, store):
        self.database = database
        self.objects = Artifacts(store, create=False)

    def ReadStatus(self, job):
        rows = self.database.execute(
            "SELECT id,kind,state,reason,generation,fingerprint,attempts,receipt,result,definition,definition_hash "
            "FROM jobs WHERE id=?",
            (job,),
        )
        return {"jobs": [dict(row) for row in rows]}

    def FetchInput(self, checksum, destination):
        return copy_verified(self.objects.path(checksum), destination, checksum)


def read_queue(path):
    return validate_queue(record(path))


def validate_queue(queue):
    scope = plan_scope(queue)
    if scope is None:
        recipes = queue.get("recipes")
        require(
            isinstance(recipes, list)
            and 1 <= len(recipes) <= 4
            and all(
                isinstance(recipe, str) and recipe in {"P01", "P02", "P03", "P04"}
                for recipe in recipes
            )
            and len(set(recipes)) == len(recipes),
            "expected a queued discovery recipe roster",
        )
    else:
        require(queue.get("cases") == list(CASES) and "recipes" not in queue,
                "expected the fixed Fusion scope control roster")
    require(
        isinstance(queue.get("jobs"), dict)
        and set(queue["jobs"]) == {"a", "b"}
        and all(
            isinstance(queue["jobs"][phase], str)
            and re.fullmatch(
                rf"fusion-phase:[0-9a-f]{{64}}:{phase}", queue["jobs"][phase]
            )
            for phase in ("a", "b")
        )
        and queue["jobs"]["a"][:-1] == queue["jobs"]["b"][:-1],
        "queued phase IDs do not form a pair",
    )
    require(
        isinstance(queue.get("plan_sha256"), str)
        and re.fullmatch("[a-f0-9]{64}", queue["plan_sha256"])
        and queue.get("plan_binding") == f"fusion-plan:{queue['plan_sha256']}"
        and isinstance(queue.get("source_revision"), str)
        and re.fullmatch("[a-f0-9]{40}", queue["source_revision"]),
        "queued plan identity is invalid",
    )
    label(queue["installation"])
    label(queue["resource"])
    return queue


def phase_row(owner, queue, phase):
    job = queue["jobs"][phase]
    jobs = owner.ReadStatus(job)["jobs"]
    require(len(jobs) == 1, "queued phase is absent from the controller store")
    row = jobs[0]
    spec = specification(json.loads(row["definition"]))
    parent = queue["jobs"]["a"]
    inputs = {"plan": queue["plan_binding"]}
    scope = plan_scope(queue)
    if phase == "b":
        inputs["phase-a.accepted"] = {"dependency": parent}
        for role in phase_paths(queue, "a"):
            inputs[role] = {"dependency": parent, "artifact": role}
    require(
        row["definition_hash"] == digest(spec)
        and spec["id"] == job
        and spec["kind"] == row["kind"]
        and spec["options"] == phase_options(scope, phase)
        and spec["rule_version"] == phase_rule(scope)
        and spec["tool_version"] == queue["source_revision"]
        and spec["resources"] == [queue["resource"]]
        and spec["inputs"] == inputs
        and spec["depends_on"] == ([parent] if phase == "b" else []),
        "current controller phase definition differs from the queued plan",
    )
    return row


def verify_binding(owner, queue, scratch):
    row = owner.database.execute(
        "SELECT sha256 FROM bindings WHERE name=?",
        (queue["plan_binding"],),
    ).fetchone()
    require(
        row is not None and row["sha256"] == queue["plan_sha256"],
        "queued plan binding differs from its content identity",
    )
    plan = json.loads(stored_bytes(owner, row["sha256"], scratch / "plan.json"))
    require(
        plan_scope(plan) == plan_scope(queue)
        and all(queue[key] == value for key, value in phase_identity(plan).items())
        and plan["source_revision"] == queue["source_revision"],
        "stored plan differs from the queue receipt",
    )
    return plan


def phase_evidence(owner, queue, phase, scratch, *, timing_plan=None):
    scratch.mkdir(mode=0o700)
    row, manifest, raw_dispatch = accepted_output(
        owner, queue["jobs"][phase], scratch, None, None
    )
    dispatch = json.loads(raw_dispatch)
    proof = dispatch["proof"]
    scope = plan_scope(queue)
    expected_paths = phase_paths(queue, phase)
    expected_roles = set(expected_paths)
    require(
        set(manifest) == expected_roles | {"dispatch"}
        and set(dispatch["files"]) == expected_roles,
        "accepted Fusion phase output role set differs",
    )
    files = output_manifest(dispatch["files"])
    if scope is not None:
        require({role: item["path"] for role, item in files.items()} == expected_paths,
                "accepted Fusion scope archive paths differ from their roles")
    require(
        all(
            manifest[role]
            == {key: files[role][key] for key in ("sha256", "size_bytes")}
            for role in expected_roles
        ),
        "accepted artifact manifest differs from the dispatch pins",
    )
    require(
        dispatch["version"] == 1
        and dispatch["status"] == "completed"
        and dispatch["provider"] == "autodesk.fusion.addin"
        and dispatch["source_revision"] == queue["source_revision"]
        and dispatch["installation"] == queue["installation"]
        and proof["phase"] == phase
        and proof["plan_sha256"] == queue["plan_sha256"]
        and proof.get("scope") == scope
        and proof["claim"] == "unqualified_application_observation"
        and dispatch["host"] == proof["host"],
        "accepted Fusion dispatch does not bind this phase, plan and installation",
    )
    handoff = proof.get("restart_handoff")
    if phase == "a":
        require(
            isinstance(handoff, dict)
            and handoff["reason"] == "restart_required"
            and handoff["installation"] == queue["installation"]
            and handoff["plan_sha256"] == queue["plan_sha256"]
            and handoff["host"] == dispatch["host"],
            "accepted phase A dispatch lacks its pinned restart handoff",
        )
    else:
        require(
            handoff is None, "accepted phase B dispatch unexpectedly requires a restart"
        )
    for role, value in manifest.items():
        require(
            owner.objects.verify(value["sha256"]) == value["size_bytes"],
            f"accepted artifact bytes differ for {role}",
        )
    controller = json.loads((scratch / "receipt.json").read_bytes())
    snapshot = controller["snapshot"]
    require(
        digest(snapshot) == row["fingerprint"]
        and snapshot["definition_hash"] == row["definition_hash"]
        and snapshot["inputs"]["plan"]
        == {"binding": queue["plan_binding"], "sha256": queue["plan_sha256"]},
        "accepted attempt's snapshot differs from the queued plan",
    )
    receipt = json.loads(
        stored_bytes(
            owner,
            manifest[f"phase-{phase}.receipt"]["sha256"],
            scratch / "phase-receipt.json",
        )
    )
    name = "measurements" if scope is None else "report"
    previous_key = "previous_measurements_sha256" if scope is None else "previous_phase_report_sha256"
    digest_key = f"{name}_sha256"
    measurements = stored_bytes(
        owner,
        manifest[f"phase-{phase}.{name}"]["sha256"],
        scratch / f"{name}.json",
    )
    observed = json.loads(measurements)
    if scope is not None:
        check_scope_report(receipt, observed, measurements, queue["plan_sha256"], phase)
        check_scope_archives(observed, files, phase)
    version = observed["fusion_version"] if scope is None else observed["application_build"]
    require(
        receipt["schema"] == observed["schema"] == 1
        and receipt["status"] == observed["status"] == "complete"
        and receipt["phase"] == observed["phase"] == phase
        and receipt["plan_sha256"] == observed["plan_sha256"] == queue["plan_sha256"]
        and receipt[digest_key] == sha256(measurements)
        and observed["source_revision"] == queue["source_revision"]
        and version == proof["fusion_version"]
        and observed["errors"] == [],
        "accepted Fusion measurements do not match the phase receipt",
    )
    process = observed["process"]
    require(
        type(process["pid"]) is int
        and process["pid"] > 1
        and dispatch["host"]["pid"] == process["pid"]
        and type(process["start_unix_seconds"]) is int
        and process["start_unix_seconds"] > 0,
        "accepted Fusion process identity differs",
    )
    output = {
        "receipt_sha256": row["receipt"],
        "result_sha256": row["result"],
        digest_key: receipt[digest_key],
        "fusion_version": version,
        "process": process,
        "ended_unix_seconds": observed["ended_unix_seconds"],
        previous_key: observed[previous_key] if scope is None else observed.get(previous_key),
        "artifacts": manifest,
        "dependencies": snapshot["dependencies"],
    }
    if scope is not None:
        output["previous_process"] = observed.get("previous_process")
    if timing_plan is not None:
        output["native_timing"] = phase_timing(
            owner.database, row, controller, dispatch, observed, timing_plan
        )
    return output


def audit(store, queue, installation=None, *, window=None):
    validate_window(window)
    scope = plan_scope(queue)
    if installation is not None:
        require(
            installation["application"] == "fusion"
            and installation["installation"] == queue["installation"]
            and installation["source_revision"] == queue["source_revision"],
            "owner installation differs from the queued Fusion plan",
        )
    database = store / "ledger.sqlite3"
    require(
        database.is_file() and not database.is_symlink(),
        "expected an initialized A03 store",
    )
    phases = {}
    with (
        read_store(database.resolve(), None, (4,)) as connection,
        TemporaryDirectory(prefix="kit-fusion-audit-") as temporary,
    ):
        owner = StoreSnapshot(connection, store)
        scratch = Path(temporary)
        plan = verify_binding(owner, queue, scratch)
        resource = connection.execute(
            "SELECT available FROM resources WHERE name=?",
            (queue["resource"],),
        ).fetchone()
        for phase in ("a", "b"):
            row = phase_row(owner, queue, phase)
            item = {
                key: row[key]
                for key in ("id", "kind", "state", "reason", "generation", "attempts")
            }
            if row["state"] == "completed":
                item["evidence"] = phase_evidence(
                    owner,
                    queue,
                    phase,
                    scratch / phase,
                    timing_plan=plan if window is not None else None,
                )
            elif row["state"] == "waiting_application" and row["result"] is not None:
                timeout = parked_timeout(owner, row, queue, phase, scratch / phase)
                if timeout is not None:
                    item["queue_timeout"] = timeout
            phases[phase] = item
    if installation is not None:
        for phase, item in phases.items():
            if "queue_timeout" in item:
                item["spool_observation"] = inspect_spool(
                    installation, item["queue_timeout"], phase
                )
    require(phases["a"]["kind"] == phases["b"]["kind"], "queued phase job kinds differ")
    if phases["b"]["state"] == "completed":
        require(
            phases["a"]["state"] == "completed",
            "completed repeat phase lacks its current completed first phase",
        )
        first, second = (phases[phase]["evidence"] for phase in ("a", "b"))
        digest_key = "measurements_sha256" if scope is None else "report_sha256"
        previous_key = "previous_measurements_sha256" if scope is None else "previous_phase_report_sha256"
        if scope is not None:
            require(first["previous_process"] is None and second["previous_process"] == first["process"]
                    and second["process"]["start_unix_seconds"] > first["ended_unix_seconds"],
                    "accepted scope report does not bind the exact prior process and its end")
        require(
            first["dependencies"] == {}
            and first[previous_key] is None
            and second["dependencies"]
            == {
                queue["jobs"]["a"]: {
                    "receipt": first["receipt_sha256"],
                    "result": first["result_sha256"],
                }
            }
            and second[previous_key] == first[digest_key]
            and second["fusion_version"] == first["fusion_version"]
            and second["process"]["pid"] != first["process"]["pid"]
            and second["process"]["start_unix_seconds"]
            > first["process"]["start_unix_seconds"]
            and second["process"]["start_unix_seconds"]
            >= int(first["ended_unix_seconds"]),
            "accepted Fusion measurements do not establish a linked fresh-process pair",
        )
    status = "verified_pair" if phases["b"]["state"] == "completed" else "pending"
    if any(item["state"] in {"failed", "rejected"} for item in phases.values()):
        status = "failed"
    output = {
        "status": status,
        "native_qualified": False,
        "launched_application": False,
        "phases": phases,
        "installation": queue["installation"],
        "source_revision": queue["source_revision"],
        "plan_sha256": queue["plan_sha256"],
        "resource": queue["resource"],
        "resource_available": bool(resource is not None and resource["available"]),
    }
    if scope is not None:
        output["scope"] = scope
    if window is not None:
        output["native_busy_time"] = busy_window(phases, *window)
    return output


def main():
    parser = argparse.ArgumentParser(
        description="Audit queued Fusion phase evidence in a read-only A03 snapshot"
    )
    parser.add_argument("--store", type=Path, required=True)
    parser.add_argument("--queue-receipt", type=Path, required=True)
    parser.add_argument("--installation", type=Path)
    parser.add_argument(
        "--busy-window",
        type=float,
        nargs=2,
        metavar=("FROM_UNIX", "UNTIL_UNIX"),
        help="report the measured busy-time lower bound for an audited pair",
    )
    args = parser.parse_args()
    try:
        installation = (
            configuration(args.installation) if args.installation is not None else None
        )
        result = audit(
            args.store,
            read_queue(args.queue_receipt),
            installation,
            window=args.busy_window,
        )
    except (OSError, ValueError, KeyError, TypeError, sqlite3.Error) as error:
        print(
            f"Fusion phase audit: {type(error).__name__}: {error}"[:2048],
            file=sys.stderr,
        )
        return 1
    print(canonical(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
