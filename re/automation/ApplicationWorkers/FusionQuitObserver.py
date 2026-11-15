import argparse
import json
import sqlite3
import subprocess
import sys
from pathlib import Path

from ApplicationProtocol import (
    directory,
    encoded,
    file_bytes,
    owner_lock,
    require,
    validate_configuration,
)
from FusionExitEvidence import seal_and_watch
from FusionQuitCustody import FusionQuitCustody
from FusionRestartReadiness import observe_owner
from MacApplicationBundle import pinned_bundle
from MacProcessExit import PeerUnavailable


def armed(intent_sha256):
    print(
        f"Fusion exit observer armed ({intent_sha256}). "
        "If the owned session is still idle, use the normal Fusion quit command.",
        file=sys.stderr,
        flush=True,
    )


def watch(installation, store, queue, lifecycle, seconds):
    require(
        sys.platform == "darwin" and 1 <= seconds <= 300,
        "Fusion exit observation requires macOS and a 1 to 300 second wait",
    )
    installation_bytes = file_bytes(installation)
    config = validate_configuration(json.loads(installation_bytes))
    root = directory(config["endpoint"])
    with owner_lock(root / "dispatch.lock"):
        readiness = observe_owner(
            root,
            config,
            installation_bytes,
            installation,
            store,
            queue,
            lifecycle,
            retain_evidence=True,
        )
        custody = FusionQuitCustody(
            root, installation, installation_bytes, store, queue, lifecycle, readiness
        )
        bundle = pinned_bundle(
            custody.lifecycle_bytes, readiness["installation_sha256"]
        )
        return seal_and_watch(
            root,
            readiness,
            bundle["executable"],
            custody.fence_sha256,
            seconds,
            custody.verify,
            armed,
        )


def main():
    parser = argparse.ArgumentParser(
        description="Observe the exact owned Fusion exit after restart readiness"
    )
    parser.add_argument("--installation", required=True, type=Path)
    parser.add_argument("--store", required=True, type=Path)
    parser.add_argument("--queue-receipt", required=True, type=Path)
    parser.add_argument("--lifecycle", required=True, type=Path)
    parser.add_argument("--wait-seconds", type=int, default=60)
    args = parser.parse_args()
    try:
        result = watch(
            args.installation,
            args.store,
            args.queue_receipt,
            args.lifecycle,
            args.wait_seconds,
        )
        print(encoded(result).decode(), end="")
        return 0 if result["status"] == "exact_exit_observed" else 2
    except PeerUnavailable as error:
        print(f"Fusion exit observer refused: {error}", file=sys.stderr)
        return 1
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
        print(f"Fusion exit observer refused ({type(error).__name__})", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
