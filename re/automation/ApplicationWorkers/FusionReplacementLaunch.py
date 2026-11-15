import argparse
import json
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

from ApplicationProtocol import (
    MAC_REPLACEMENT_LAUNCH,
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
from FusionExitRecords import exit_evidence, pin, read_pinned
from FusionQuitCustody import FusionQuitCustody
from FusionReplacementPhase import observe_phase_b
from MacApplicationBundle import pinned_bundle
from MacBundleLaunch import available, launch_bundle


def replacement_paths(root, intent_sha256):
    identifier = pin(intent_sha256)
    return (
        root / f"replacement-launch-{identifier}.json",
        root / f"replacement-peer-{identifier}.json",
    )


def verified_inputs(args, root, config, install_bytes, *, handoff_id=None):
    readiness, exit_record = exit_evidence(
        root, args.quit_intent_sha256, args.quit_exit_sha256
    )
    custody = FusionQuitCustody(
        root,
        args.installation,
        install_bytes,
        args.store,
        args.queue_receipt,
        args.lifecycle,
        readiness,
        handoff_id=handoff_id,
    )
    require(
        config["application"] == "fusion"
        and custody.intent["installation"] == config["installation"]
        and custody.intent["source_revision"] == config["source_revision"]
        and custody.fence_sha256 == exit_record["fence_sha256"]
        and custody.intent["restart_handoff"]["host"]
        == readiness["consumption"]["host"]
        and sha256(committed_bytes(config, RESTART_GRANT))
        == readiness["provider_source_sha256"],
        "Fusion replacement evidence differs from the selected installation",
    )
    bundle = pinned_bundle(custody.lifecycle_bytes, readiness["installation_sha256"])
    return custody, bundle, readiness


def bundle_pins(bundle):
    return {key: value for key, value in bundle.items() if key != "executable"}


def request_launch(args, root, config, install_bytes):
    available()
    source = committed_bytes(config, MAC_REPLACEMENT_LAUNCH)
    request_path, receipt_path = replacement_paths(root, args.quit_intent_sha256)
    with owner_lock(root / "replacement-launch.lock"):
        with owner_lock(root / "dispatch.lock"):
            custody, bundle, readiness = verified_inputs(
                args, root, config, install_bytes
            )
            custody.verify()
            old = readiness["peer"]
            available(old["uid"])
            require(
                identity(old["pid"]) is None, "prior Fusion process ID is still in use"
            )
            with owner_lock(root / "host.lock"):
                require(
                    not receipt_path.exists(), "Fusion replacement was already observed"
                )
                request = {
                    "version": 1,
                    "scope": "owner_fusion_replacement_request",
                    "quit_intent_sha256": args.quit_intent_sha256,
                    "quit_exit_sha256": args.quit_exit_sha256,
                    "restart_intent_sha256": readiness["intent_sha256"],
                    "handoff_id": custody.handoff_id,
                    "installation_sha256": readiness["installation_sha256"],
                    "lifecycle_sha256": readiness["lifecycle_sha256"],
                    "fence_sha256": custody.fence_sha256,
                    "provider_source_sha256": sha256(source),
                    "bundle": bundle_pins(bundle),
                    "requested_at": time.time(),
                }
                request_bytes = encoded(request)
                write_new(request_path, request_bytes)
        observed = launch_bundle(
            source,
            bundle,
            request["requested_at"],
            old,
            args.wait_seconds,
            request_path,
            sha256(request_bytes),
        )
        custody.verify(retained=False)
        require(
            pinned_bundle(file_bytes(args.lifecycle), readiness["installation_sha256"])
            == bundle,
            "reviewed Fusion bundle changed while requesting replacement",
        )
        receipt = {
            "version": 1,
            "scope": "owner_fusion_replacement_observation",
            "status": "replacement_process_observed",
            "launch_request_sha256": sha256(request_bytes),
            "quit_intent_sha256": args.quit_intent_sha256,
            "quit_exit_sha256": args.quit_exit_sha256,
            "startup": "phase_b_evidence_required",
            **observed,
        }
        raw = encoded(receipt)
        write_new(receipt_path, raw)
        return {**receipt, "launch_receipt_sha256": sha256(raw)}


def read_launch(args, root, config, install_bytes):
    request_path, receipt_path = replacement_paths(root, args.quit_intent_sha256)
    launch = read_pinned(receipt_path, args.launch_receipt_sha256)
    request = read_pinned(request_path, launch["launch_request_sha256"])
    require(
        request["version"] == launch["version"] == 1
        and request["scope"] == "owner_fusion_replacement_request"
        and launch["scope"] == "owner_fusion_replacement_observation"
        and launch["status"] == "replacement_process_observed"
        and request["quit_intent_sha256"]
        == launch["quit_intent_sha256"]
        == args.quit_intent_sha256
        and request["quit_exit_sha256"]
        == launch["quit_exit_sha256"]
        == args.quit_exit_sha256,
        "Fusion launch records do not match the immutable exit evidence",
    )
    custody, bundle, readiness = verified_inputs(
        args, root, config, install_bytes, handoff_id=request["handoff_id"]
    )
    require(
        request["restart_intent_sha256"] == readiness["intent_sha256"]
        and request["installation_sha256"] == readiness["installation_sha256"]
        and request["lifecycle_sha256"] == readiness["lifecycle_sha256"]
        and request["bundle"] == bundle_pins(bundle)
        and request["fence_sha256"] == custody.fence_sha256
        and request["provider_source_sha256"]
        == sha256(committed_bytes(config, MAC_REPLACEMENT_LAUNCH))
        and launch["host"]["pid"] == launch["peer"]["pid"] != readiness["peer"]["pid"]
        and launch["peer"]["uid"] == readiness["peer"]["uid"]
        and request["requested_at"]
        <= launch["dispatched_at"]
        <= launch["peer"]["started_unix_microseconds"] / 1_000_000,
        "Fusion launch peer or source pins differ from the reviewed request",
    )
    return observe_phase_b(custody, config, bundle, launch)


def main():
    parser = argparse.ArgumentParser(
        description="Request or verify one owner-directed Fusion replacement"
    )
    parser.add_argument("--installation", required=True, type=Path)
    parser.add_argument("--store", required=True, type=Path)
    parser.add_argument("--queue-receipt", required=True, type=Path)
    parser.add_argument("--lifecycle", required=True, type=Path)
    parser.add_argument("--quit-intent-sha256", required=True)
    parser.add_argument("--quit-exit-sha256", required=True)
    parser.add_argument("--launch-receipt-sha256")
    parser.add_argument("--wait-seconds", type=int, default=60)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--request-launch", action="store_true")
    mode.add_argument("--observe-phase-b", action="store_true")
    args = parser.parse_args()
    try:
        require(
            sys.platform == "darwin"
            and 1 <= args.wait_seconds <= 300
            and args.observe_phase_b == (args.launch_receipt_sha256 is not None),
            "Fusion replacement command requires macOS and the appropriate exact receipt pins",
        )
        install_bytes = file_bytes(args.installation)
        config = validate_configuration(json.loads(install_bytes))
        root = directory(config["endpoint"])
        run = request_launch if args.request_launch else read_launch
        print(encoded(run(args, root, config, install_bytes)).decode(), end="")
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
        print(f"Fusion replacement refused ({type(error).__name__})", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
