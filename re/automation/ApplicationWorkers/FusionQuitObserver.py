import argparse
import functools
import json
import sqlite3
import subprocess
import sys
from pathlib import Path

import ApplicationProtocol as protocol
from ApplicationProtocol import (
    MAC_COCOA_QUIT,
    MAC_QUIT_AUTHORIZATION,
    committed_bytes,
    directory,
    encoded,
    file_bytes,
    macos_automatic_quit,
    owner_lock,
    require,
    sha256,
    validate_configuration,
)
from FusionExitEvidence import seal_and_watch
from FusionQuitAuthorization import authorize
from FusionQuitCustody import FusionQuitCustody
from FusionRestartReadiness import observe_owner
from MacApplicationBundle import pinned_bundle
from MacApplicationPeer import process_peer
from MacProcessExit import PeerUnavailable


def armed(intent_sha256, *, automatic=False):
    action = (
        "Publishing the authorized quit request."
        if automatic
        else "If the owned session is still idle, use the normal Fusion quit command."
    )
    print(
        f"Fusion exit observer armed ({intent_sha256}). " f"{action}",
        file=sys.stderr,
        flush=True,
    )


def watch(installation, store, queue, lifecycle, seconds, *, request_quit=False):
    require(
        sys.platform == "darwin" and 1 <= seconds <= 300,
        "Fusion exit observation requires macOS and a 1 to 300 second wait",
    )
    installation_bytes = file_bytes(installation)
    config = validate_configuration(json.loads(installation_bytes))
    require(
        not request_quit or macos_automatic_quit(config),
        "automatic quit requires the exact installation opt-in",
    )
    pins = (
        [
            sha256(committed_bytes(config, source))
            for source in (
                MAC_COCOA_QUIT,
                MAC_QUIT_AUTHORIZATION,
            )
        ]
        if request_quit
        else None
    )
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

        def publish(identifier, deadline_ns):
            return authorize(
                vars(protocol),
                config,
                root,
                readiness,
                bundle["executable"],
                identifier,
                deadline_ns,
                process_peer,
                *pins,
            )

        return seal_and_watch(
            root,
            readiness,
            bundle["executable"],
            custody.fence_sha256,
            seconds,
            custody.verify,
            functools.partial(armed, automatic=request_quit),
            authorize=publish if pins is not None else None,
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
    parser.add_argument("--request-quit", action="store_true")
    args = parser.parse_args()
    try:
        result = watch(
            args.installation,
            args.store,
            args.queue_receipt,
            args.lifecycle,
            args.wait_seconds,
            request_quit=args.request_quit,
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
