import json
import math
import re
import time

from ApplicationProtocol import (
    FUSION_PROVIDER,
    directory,
    file_bytes,
    identity,
    require,
    sha256,
)
from Artifacts import Artifacts
from FusionOwnerRestart import start_seconds
from FusionStartupProvision import owner_inputs
from HostResources import command_output
from MacApplicationBundle import pinned_bundle
from MacApplicationPeer import process_peer
from MacProcessExit import observe_exit, verify_peer, watch_peer
from Records import specification
from ResourceOccupancy import closed_attempt_receipt, stored_record
from StoreRead import read_store
from Supervisor import read_config


def observe(args):
    config_before = file_bytes(args.config)
    config, installation, lifecycle, executable = owner_inputs(
        args.installation, args.lifecycle
    )
    settings = read_config(args.config)
    resource = f"application:{config['installation']}"
    controller = settings["controller"]
    require(
        controller.get("adapter") == "a03"
        and set(controller) == {"adapter", "store"}
        and settings["resources"].get(resource) == 1
        and args.reset_evidence_limit > 0,
        "Fusion reset evidence requires a positive limit and configured capacity-one A03 installation",
    )
    store = directory(controller["store"])
    exact = process_peer(args.reset_evidence_pid)
    host = identity(args.reset_evidence_pid)
    require(
        exact["executable"] == executable
        and host is not None
        and start_seconds(host) == exact["started_unix_microseconds"] // 1_000_000,
        "Fusion reset evidence requires the exact current physical bundle and process lifetime",
    )
    birth = exact["started_unix_microseconds"] / 1_000_000
    if not math.isfinite(birth) or not 0 < birth < time.time():
        raise ValueError("invalid Fusion process birth time")
    cutoff, evidence = count_completed(store, resource, config, host, birth)
    peer = {key: value for key, value in exact.items() if key != "executable"}
    lifecycle_bytes = file_bytes(args.lifecycle)
    require(
        identity(args.reset_evidence_pid) == host
        and file_bytes(args.config) == config_before
        and file_bytes(args.installation) == installation
        and sha256(lifecycle_bytes) == lifecycle
        and pinned_bundle(lifecycle_bytes, sha256(installation))["executable"]
        == executable,
        "Fusion reset observation lost its exact process or owner inputs",
    )
    resident_bytes = native_resident_bytes(peer, executable)
    return {
        "version": 1,
        "scope": "fusion_corroborated_completed_native_requests",
        "installation": config["installation"],
        "source_revision": config["source_revision"],
        "peer": peer,
        "native_resident_bytes": resident_bytes,
        "as_of_unix_seconds": cutoff,
        "comparison_limit": args.reset_evidence_limit,
        "verified_count_reaches_limit": evidence["corroborated"]
        >= args.reset_evidence_limit,
        **evidence,
    }


# the reset report needs resident memory from the pinned application itself
def native_resident_bytes(peer, executable):
    with watch_peer(peer, executable) as monitor:
        try:
            rows = command_output(
                ["/bin/ps", "-p", str(peer["pid"]), "-o", "pid=,uid=,rss="]
            ).splitlines()
        except OSError:
            rows = []
        verify_peer(peer, executable)
        require(
            observe_exit(monitor, peer, 0) is None,
            "macOS application changed while sampling resident memory",
        )
    if len(rows) != 1:
        return None
    fields = rows[0].split()
    if (
        len(fields) != 3
        or fields[:2] != [str(peer["pid"]), str(peer["uid"])]
        or re.fullmatch(r"[1-9][0-9]*", fields[2]) is None
    ):
        return None
    return int(fields[2]) * 1024


def count_completed(store, resource, config, host, birth):
    database = store / "ledger.sqlite3"
    require(
        database.is_file() and not database.is_symlink(),
        "Fusion reset evidence requires an initialized A03 store",
    )
    objects = Artifacts(store, create=False)
    with read_store(database, None, (4,)) as connection:
        matched = connection.execute(
            "SELECT 1 FROM resources WHERE name=? AND capacity=1", (resource,)
        ).fetchone()
        require(
            matched is not None,
            "Fusion reset evidence lacks the stored capacity-one resource",
        )
        cutoff = time.time()
        rows = connection.execute(
            "SELECT id,job_id,generation,number,fingerprint,started,ended,receipt FROM attempts "
            "WHERE outcome='completed' AND ended>=? AND ended<=? ORDER BY id",
            (birth, cutoff),
        ).fetchall()
    return cutoff, match_attempts(objects, rows, resource, config, host, birth)


def match_attempts(objects, rows, resource, config, host, birth):
    seen = set()
    definitions = {}
    counts = {
        "corroborated": 0,
        "duplicate_dispatches": 0,
        "other_peers": 0,
        "unattributed_completions": 0,
    }
    for attempt in rows:
        receipt = closed_attempt_receipt(objects, attempt)
        definition = receipt["snapshot"]["definition_hash"]
        if definition not in definitions:
            definitions[definition] = specification(stored_record(objects, definition))
        spec = definitions[definition]
        require(
            spec["id"] == attempt["job_id"],
            "historical job definition belongs to another claim",
        )
        if resource not in spec["resources"]:
            continue
        outcome, request = native_request(
            objects, receipt, attempt, spec, config, host, birth
        )
        if request is not None:
            if request in seen:
                outcome = "duplicate_dispatches"
            seen.add(request)
        counts[outcome] += 1
    return counts


def native_request(objects, receipt, attempt, spec, config, host, birth):
    require(
        receipt["outcome"] == "completed"
        and receipt["rule_version"] == spec["rule_version"]
        and receipt["tool_version"] == spec["tool_version"],
        "accepted Fusion attempt differs from its historical job contract",
    )
    result = stored_record(objects, receipt["result_sha256"])
    result_body = result.get("result")
    supervisor_receipt = result.get("receipt")
    manifest = result.get("output_artifacts")
    if not (
        spec["tool_version"] == config["source_revision"]
        and result.get("session_version") == 1
        and isinstance(supervisor_receipt, dict)
        and supervisor_receipt.get("receipt_version") == 1
        and supervisor_receipt.get("job_id") == attempt["job_id"]
        and supervisor_receipt.get("attempt") == attempt["number"]
        and supervisor_receipt.get("kind") == spec["kind"]
        and supervisor_receipt.get("orphan") is False
        and supervisor_receipt.get("stop_reason") is None
        and supervisor_receipt.get("exit_status") == 0
        and supervisor_receipt.get("signal") is None
        and result.get("output_artifacts_version") == 1
        and isinstance(result_body, dict)
        and result_body.get("outcome") == "completed"
        and isinstance(manifest, dict)
        and result_body.get("artifacts") == manifest
    ):
        return "unattributed_completions", None
    records = result_body.get("records")
    if not (
        isinstance(records, dict)
        and records.get("application") == "fusion"
        and records.get("installation") == config["installation"]
        and records.get("phase") in ("a", "b")
        and records["phase"] == spec["options"].get("phase")
        and records.get("claim") == "unqualified_dispatch"
        and records.get("native_qualified") is False
    ):
        return "unattributed_completions", None
    reference = manifest.get("dispatch")
    if not isinstance(reference, dict) or set(reference) != {"sha256", "size_bytes"}:
        return "unattributed_completions", None
    raw = file_bytes(objects.path(reference["sha256"]))
    require(
        len(raw) == reference["size_bytes"] and sha256(raw) == reference["sha256"],
        "accepted Fusion dispatch differs from its manifest",
    )
    dispatch = json.loads(raw)
    proof = dispatch.get("proof")
    digest = dispatch.get("request_sha256")
    finished = dispatch.get("finished_at")
    plan = records.get("plan_sha256")
    if not (
        dispatch.get("version") == 1
        and dispatch.get("provider") == FUSION_PROVIDER
        and dispatch.get("installation") == config["installation"]
        and dispatch.get("source_revision") == config["source_revision"]
        and dispatch.get("status") == "completed"
        and dispatch.get("host") == records.get("host")
        and isinstance(proof, dict)
        and proof.get("host") == records.get("host")
        and proof.get("claim") == "unqualified_application_observation"
        and proof.get("phase") == records["phase"]
        and isinstance(plan, str)
        and re.fullmatch("[0-9a-f]{64}", plan)
        and plan == proof.get("plan_sha256")
        and plan == receipt["snapshot"]["inputs"].get("plan", {}).get("sha256")
        and isinstance(digest, str)
        and re.fullmatch("[0-9a-f]{64}", digest)
        and type(finished) in (int, float)
        and attempt["started"] <= finished <= receipt["finished_at"]
    ):
        return "unattributed_completions", None
    if dispatch["host"] != host or finished < birth:
        return "other_peers", None
    return "corroborated", digest
