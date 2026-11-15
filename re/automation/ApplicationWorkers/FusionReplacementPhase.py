import json
import re
from pathlib import Path
from tempfile import TemporaryDirectory

from AcknowledgeApplication import stored_bytes
from ApplicationProtocol import BOOTSTRAP, PROTOCOL, committed_bytes, require, sha256
from AuditFusionPhases import StoreSnapshot, audit, phase_row
from MacProcessExit import verify_peer
from StoreRead import read_store


def observe_phase_b(custody, config, bundle, launch):
    custody.verify(retained=False)
    verify_peer(launch["peer"], bundle["executable"])
    result = audit(custody.store, custody.queue, config)
    phase = result["phases"]["b"]
    if phase["state"] != "completed":
        return {
            "status": "replacement_phase_b_pending",
            "controller_state": phase["state"],
        }
    evidence = phase["evidence"]
    require(
        result["status"] == "verified_pair",
        "Fusion Phase B has no accepted fresh-process pair",
    )
    with (
        read_store(custody.database, None, (4,)) as connection,
        TemporaryDirectory(prefix="kit-fusion-replacement-") as temporary,
    ):
        owner = StoreSnapshot(connection, custody.store)
        current = phase_row(owner, custody.queue, "b")
        require(
            current["state"] == "completed"
            and current["receipt"] == evidence["receipt_sha256"]
            and current["result"] == evidence["result_sha256"],
            "accepted Fusion Phase B changed during replacement observation",
        )
        dispatch = json.loads(
            stored_bytes(
                owner,
                evidence["artifacts"]["dispatch"]["sha256"],
                Path(temporary) / "dispatch.json",
            )
        )
    proof = dispatch["proof"]
    peer = launch["peer"]
    require(
        dispatch["host"] == proof["host"] == launch["host"]
        and evidence["process"]["pid"] == peer["pid"]
        and evidence["process"]["start_unix_seconds"]
        == peer["started_unix_microseconds"] // 1_000_000
        and evidence["fusion_version"] == custody.intent["fusion_version"]
        and re.fullmatch("[0-9a-f]{64}", proof["probe_sha256"]),
        "accepted Fusion Phase B differs from the launched process or readiness control",
    )
    for role, filename in (("bootstrap", BOOTSTRAP), ("protocol", PROTOCOL)):
        raw = committed_bytes(config, filename)
        require(
            proof["loaded_sources"][role]
            == {
                "path": filename,
                "sha256": sha256(raw),
                "size_bytes": len(raw),
                "revision": config["source_revision"],
            },
            "Fusion Phase B lacks the reviewed replacement startup source pins",
        )
    custody.verify(retained=False)
    verify_peer(peer, bundle["executable"])
    return {
        "status": "replacement_phase_b_verified",
        "phase_b_receipt_sha256": evidence["receipt_sha256"],
        "phase_b_result_sha256": evidence["result_sha256"],
        "readiness_probe_sha256": proof["probe_sha256"],
        "peer": peer,
        "native_qualified": False,
    }
