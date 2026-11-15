import argparse
import json
import plistlib
import sqlite3
import subprocess
import sys
from pathlib import Path

from ApplicationProtocol import directory, encoded, file_bytes, require, sha256
from FusionOwnerRestart import record_restart, start_seconds
from MacApplicationBundle import pinned_bundle
from MacApplicationPeer import process_peer


def match_peer(handoff, executable):
    host = handoff["host"]
    observed = process_peer(host["pid"])
    started = observed["started_unix_microseconds"]
    require(
        observed["executable"] == executable
        and started // 1_000_000 == start_seconds(host)
        and started / 1_000_000 <= handoff["at"],
        "macOS lifecycle process differs from the accepted Fusion peer or executable",
    )
    return observed


def observe_restart(installation, store, queue, lifecycle):
    require(sys.platform == "darwin", "Fusion restart peer verification requires macOS")
    lifecycle = directory(lifecycle.parent) / lifecycle.name
    profile = file_bytes(lifecycle)
    verified = record_restart(installation, store, queue, check=True)
    intent_path = Path(verified["intent"])
    raw_intent = file_bytes(intent_path)
    require(
        sha256(raw_intent) == verified["intent_sha256"], "Fusion restart intent changed"
    )
    intent = json.loads(raw_intent)
    bundle = pinned_bundle(profile, intent["installation_sha256"])
    peer = match_peer(intent["restart_handoff"], bundle["executable"])
    require(
        record_restart(installation, store, queue, check=True) == verified
        and file_bytes(lifecycle) == profile
        and pinned_bundle(profile, intent["installation_sha256"]) == bundle
        and match_peer(intent["restart_handoff"], bundle["executable"]) == peer,
        "Fusion restart peer changed during observation",
    )
    return {
        "version": 1,
        "status": "restart_peer_verified",
        "installation_sha256": intent["installation_sha256"],
        "intent_sha256": verified["intent_sha256"],
        "lifecycle_sha256": sha256(profile),
        "fusion_version": intent["fusion_version"],
        "bundle": {key: value for key, value in bundle.items() if key != "executable"},
        "peer": {key: value for key, value in peer.items() if key != "executable"},
        "native_lifecycle_performed": False,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Verify the exact macOS peer for a retained Fusion restart intent"
    )
    parser.add_argument("--installation", required=True, type=Path)
    parser.add_argument("--store", required=True, type=Path)
    parser.add_argument("--queue-receipt", required=True, type=Path)
    parser.add_argument("--lifecycle", required=True, type=Path)
    args = parser.parse_args()
    try:
        observed = observe_restart(
            args.installation, args.store, args.queue_receipt, args.lifecycle
        )
        print(encoded(observed).decode(), end="")
        return 0
    except (
        OSError,
        ValueError,
        KeyError,
        TypeError,
        AttributeError,
        OverflowError,
        RecursionError,
        plistlib.InvalidFileException,
        sqlite3.Error,
        subprocess.SubprocessError,
    ) as error:
        print(f"Fusion restart peer refused ({type(error).__name__})", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
