import argparse
import json
import os
import re
import secrets
import sqlite3
import subprocess
import sys
import time
from pathlib import Path
from tempfile import TemporaryDirectory

from ApplicationProtocol import (
    FUSION_PROVIDER,
    RESTART_GRANT,
    committed_bytes,
    directory,
    encoded,
    file_bytes,
    identity,
    owner_lock,
    require,
    sha256,
    validate_configuration,
    write_new,
)
from FusionOwnerRestart import record_restart
from FusionRestartGrant import GRANT_SECONDS, MAILBOX, REQUEST_SECONDS
from FusionRestartPeer import match_peer, observe_restart
from MacApplicationBundle import pinned_bundle


def request_response(mailbox, request, host, source_sha256):
    raw = encoded(request)
    operation = request["operation"]
    response_path = mailbox / f"{operation}.response"
    sent = time.time()
    write_new(mailbox / f"{operation}.request", raw)
    while time.time() < request["deadline"]:
        try:
            reply = file_bytes(response_path)
        except FileNotFoundError:
            time.sleep(0.05)
            continue
        evidence = json.loads(reply)
        now = time.time()
        require(
            evidence["version"] == 1
            and evidence["request_sha256"] == sha256(raw)
            and evidence["host"] == host
            and evidence["provider"] == FUSION_PROVIDER
            and evidence["source_sha256"] == source_sha256
            and evidence["status"]
            == ("granted" if operation == "issue" else "consumed")
            and evidence["documents"] == 0
            and sent <= evidence["observed_at"] <= now < request["deadline"],
            "Fusion restart callback refused or differed from the exact fresh request",
        )
        return evidence, sha256(reply)
    raise ValueError("Fusion restart callback missed its deadline")


def prove_readiness(installation, store, queue, lifecycle):
    require(sys.platform == "darwin", "Fusion restart readiness requires macOS")
    installation_bytes = file_bytes(installation)
    config = validate_configuration(json.loads(installation_bytes))
    root = directory(config["endpoint"])
    with owner_lock(root / "dispatch.lock"):
        return observe_owner(
            root, config, installation_bytes, installation, store, queue, lifecycle
        )


def observe_owner(root, config, install_bytes, installation, store, queue, lifecycle):
    proof = observe_restart(installation, store, queue, lifecycle)
    require(
        sha256(install_bytes) == proof["installation_sha256"],
        "Fusion lifecycle installation changed before readiness",
    )
    fence = file_bytes(root / "fence.json")
    handoff = json.loads(fence)
    handoff_id = handoff["job_id"]
    require(
        re.fullmatch("[0-9a-f]{32}", handoff_id),
        "invalid Fusion restart handoff identity",
    )
    path = root / f"restart-intent-{handoff_id}.json"
    raw_intent = file_bytes(path)
    source = sha256(committed_bytes(config, RESTART_GRANT))
    mailbox = directory(root / MAILBOX, True)
    require(
        sha256(raw_intent) == proof["intent_sha256"]
        and encoded(json.loads(raw_intent)["restart_handoff"]) == fence,
        "durable Fusion restart intent changed before readiness",
    )
    client = identity(os.getpid())
    require(client is not None, "Fusion readiness caller identity is unavailable")
    request = {
        "version": 1,
        "operation": "issue",
        "installation": config["installation"],
        "source_revision": config["source_revision"],
        "handoff_id": handoff_id,
        "intent_sha256": proof["intent_sha256"],
        "challenge": secrets.token_hex(24),
        "client": client,
        "deadline": time.time() + REQUEST_SECONDS,
    }
    with TemporaryDirectory(prefix="attempt-", dir=mailbox) as temporary:
        attempt = Path(temporary)
        first, grant_hash = request_response(attempt, request, handoff["host"], source)
        require(
            first["observed_at"]
            < first["expires_at"]
            <= min(request["deadline"], first["observed_at"] + GRANT_SECONDS),
            "Fusion restart grant expiry is invalid",
        )
        verified = record_restart(installation, store, queue, check=True)
        profile = file_bytes(lifecycle)
        bundle = pinned_bundle(profile, proof["installation_sha256"])
        peer = match_peer(handoff, bundle["executable"])
        require(
            verified["intent_sha256"] == proof["intent_sha256"]
            and sha256(profile) == proof["lifecycle_sha256"]
            and {key: value for key, value in bundle.items() if key != "executable"}
            == proof["bundle"]
            and {key: value for key, value in peer.items() if key != "executable"}
            == proof["peer"]
            and time.time() < first["expires_at"],
            "Fusion readiness grant expired or its accepted owner custody changed",
        )
        followup = {
            **request,
            "operation": "consume",
            "grant_sha256": grant_hash,
            "deadline": first["expires_at"],
        }
        final, response_hash = request_response(
            attempt, followup, handoff["host"], source
        )
        require(
            final["grant_sha256"] == grant_hash
            and sha256(file_bytes(attempt / "issue.consumed")) == grant_hash
            and not (attempt / "issue.response").exists()
            and file_bytes(root / "fence.json") == fence,
            "Fusion restart readiness was not consumed from the retained fence",
        )
    return {
        "version": 1,
        "status": "restart_readiness_observed",
        "intent_sha256": proof["intent_sha256"],
        "installation_sha256": proof["installation_sha256"],
        "lifecycle_sha256": proof["lifecycle_sha256"],
        "peer": proof["peer"],
        "provider_source_sha256": source,
        "grant_sha256": grant_hash,
        "consumption_sha256": response_hash,
        "observed_at": final["observed_at"],
        "expires_at": first["expires_at"],
        "documents": final["documents"],
        "native_lifecycle_performed": False,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Obtain a fresh one-use Fusion restart readiness observation"
    )
    parser.add_argument("--installation", required=True, type=Path)
    parser.add_argument("--store", required=True, type=Path)
    parser.add_argument("--queue-receipt", required=True, type=Path)
    parser.add_argument("--lifecycle", required=True, type=Path)
    args = parser.parse_args()
    try:
        result = prove_readiness(
            args.installation, args.store, args.queue_receipt, args.lifecycle
        )
        print(encoded(result).decode(), end="")
        return 0
    except (
        OSError,
        ValueError,
        KeyError,
        TypeError,
        AttributeError,
        OverflowError,
        RecursionError,
        sqlite3.Error,
        subprocess.SubprocessError,
    ) as error:
        print(
            f"Fusion restart readiness refused ({type(error).__name__})",
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
