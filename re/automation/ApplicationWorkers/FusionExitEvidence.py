import os
import time

from ApplicationProtocol import (
    FUSION_PROVIDER,
    encoded,
    file_bytes,
    identity,
    require,
    sha256,
    write_new,
)
from MacProcessExit import observe_exit, watch_peer


def seal_and_watch(root, readiness, executable, fence_sha256, seconds, verify, notify):
    require(
        type(seconds) is int
        and 1 <= seconds <= 300
        and readiness["status"] == "restart_readiness_observed"
        and readiness["documents"] == 0
        and readiness["grant"]["status"] == "granted"
        and readiness["consumption"]["status"] == "consumed"
        and readiness["grant"]["provider"]
        == readiness["consumption"]["provider"]
        == FUSION_PROVIDER
        and readiness["grant"]["host"] == readiness["consumption"]["host"]
        and readiness["grant"]["host"]["pid"] == readiness["peer"]["pid"]
        and readiness["grant"]["source_sha256"]
        == readiness["consumption"]["source_sha256"]
        == readiness["provider_source_sha256"]
        and sha256(encoded(readiness["grant"])) == readiness["grant_sha256"]
        and sha256(encoded(readiness["consumption"])) == readiness["consumption_sha256"]
        and readiness["consumption"]["grant_sha256"] == readiness["grant_sha256"]
        and readiness["consumption"]["observed_at"] == readiness["observed_at"]
        and readiness["grant"]["expires_at"] == readiness["expires_at"],
        "Fusion exit watch requires a fresh, consumed readiness grant",
    )
    peer = readiness["peer"]
    watcher = identity(os.getpid())
    require(watcher is not None, "Fusion exit watcher process identity is unavailable")
    with watch_peer(peer, executable) as monitor:
        verify()
        armed_at = time.time()
        require(
            readiness["observed_at"] <= armed_at < readiness["expires_at"],
            "Fusion readiness expired before exit observation was armed",
        )
        intent = {
            "version": 1,
            "scope": "external_fusion_exit_watch",
            "fence_sha256": fence_sha256,
            "armed_at": armed_at,
            "timeout_seconds": seconds,
            "watcher": watcher,
            "readiness": readiness,
        }
        raw = encoded(intent)
        intent_sha256 = sha256(raw)
        path = root / f"quit-intent-{intent_sha256}.json"
        write_new(path, raw)
        deadline = time.monotonic() + seconds
        notify(intent_sha256)
        remaining = deadline - time.monotonic()
        event = observe_exit(monitor, peer, remaining) if remaining > 0 else None
        if event is None or time.monotonic() > deadline:
            return {"status": "exit_unobserved", "quit_intent_sha256": intent_sha256}
        verify()
        require(
            file_bytes(path) == raw and event["observed_at"] >= armed_at,
            "Fusion exit observation differs from its durable armed intent",
        )
        receipt = {
            "version": 1,
            "scope": "external_fusion_exit_observation",
            "status": "exact_exit_observed",
            "quit_intent_sha256": intent_sha256,
            "restart_intent_sha256": readiness["intent_sha256"],
            "fence_sha256": fence_sha256,
            "peer": peer,
            "cause": "unverified",
            **event,
        }
        receipt_bytes = encoded(receipt)
        write_new(root / f"quit-exit-{intent_sha256}.json", receipt_bytes)
        return {**receipt, "receipt_sha256": sha256(receipt_bytes)}
