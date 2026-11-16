import argparse
import json
import os
import secrets
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import ApplicationProtocol as protocol
import FusionStartupEvidence as startup
from ApplicationProtocol import (
    directory,
    encoded,
    file_bytes,
    owner_lock,
    require,
    sha256,
    sync_directory,
    write_new,
)
from FusionQueueReceipt import seal
from MacApplicationBundle import pinned_bundle
from MacApplicationPeer import process_peer


class StartupUnavailable(ValueError):
    pass


def owner_inputs(installation, lifecycle):
    require(
        sys.platform == "darwin", "Fusion owner startup provisioning requires macOS"
    )
    install_path = directory(installation.parent) / installation.name
    install_bytes = file_bytes(install_path)
    config = protocol.validate_configuration(json.loads(install_bytes))
    require(config["application"] == "fusion", "selected installation is not Fusion")
    lifecycle_path = directory(lifecycle.parent) / lifecycle.name
    lifecycle_bytes = file_bytes(lifecycle_path)
    bundle = pinned_bundle(lifecycle_bytes, sha256(install_bytes))
    return config, install_bytes, sha256(lifecycle_bytes), bundle["executable"]


def prepare(args, config, installation, lifecycle_hash, executable):
    require(
        args.installed_addin.is_absolute()
        and args.installed_addin.name == startup.ADDIN,
        "select the intended absolute KitCaptureRunner installation folder",
    )
    addin = Path(os.path.abspath(args.installed_addin))
    installed = addin / f"{startup.ADDIN}.py"
    parent = directory(args.output.parent)
    output_path = parent / args.output.name
    require(
        args.output.is_absolute()
        and args.output.name not in ("", ".", "..")
        and not output_path.is_relative_to(addin)
        and not addin.is_relative_to(output_path),
        "Fusion startup staging and installed add-in must be separate",
    )
    output = directory(output_path, True)
    staged = directory(output / startup.ADDIN, True)
    profile, bootstrap, manifest = startup.expected_profile(
        vars(protocol),
        config,
        installation,
        lifecycle_hash,
        installed,
        executable,
    )
    seal(staged / installed.name, bootstrap)
    seal(staged / installed.with_suffix(".manifest").name, manifest)
    raw = encoded(profile)
    seal(output / "startup-profile.json", raw)
    return {"status": "startup_copy_prepared", "profile_sha256": sha256(raw)}


def observe(
    args,
    config,
    installation,
    lifecycle_hash,
    executable,
    *,
    launch_binding=None,
    retain=None,
):
    _, candidate = startup.profile_input(vars(protocol), args.profile)
    installed = Path(candidate["installed_bootstrap"])
    pinned = startup.verified_profile(
        vars(protocol),
        config,
        installation,
        args.profile,
        installed,
        lifecycle_hash,
        executable,
    )
    raw, profile = pinned
    peer = startup.executable_peer(process_peer, args.pid)
    require(
        peer["executable"] == os.fspath(executable),
        "startup peer differs from the reviewed application",
    )
    root = directory(directory(config["endpoint"]) / startup.MAILBOX, True)
    with owner_lock(root / "observer.lock"):
        return request_proof(
            args,
            root,
            config,
            installation,
            raw,
            profile,
            peer,
            launch_binding=launch_binding,
            retain=retain,
        )


def request_proof(
    args,
    root,
    config,
    installation,
    raw_profile,
    profile,
    peer,
    *,
    launch_binding=None,
    retain=None,
):
    client = startup.executable_peer(process_peer, os.getpid())
    require(client != peer, "Fusion startup proof needs a separate owner process")
    active = root / startup.ACTIVE
    challenge = secrets.token_hex(24)
    now = time.time()
    request = {
        "version": 1,
        "scope": startup.REQUEST_SCOPE,
        "challenge": challenge,
        "profile_sha256": sha256(raw_profile),
        "peer": peer,
        "client": client,
        "issued_at": now,
        "deadline": now + args.wait_seconds,
    }
    if launch_binding is not None:
        request["launch_binding_sha256"] = launch_binding
    raw = encoded(request)
    write_new(root / f"{challenge}.request.json", raw)
    active.unlink(missing_ok=True)
    write_new(active, raw)
    try:
        reply = wait_response(root, request, time.monotonic() + args.wait_seconds)
        seen = json.loads(reply)
        lifecycle = file_bytes(args.lifecycle)
        verified_bundle = pinned_bundle(lifecycle, sha256(installation))
        expected = {
            "version",
            "scope",
            "startup_context",
            "profile_sha256",
            "request_sha256",
            "peer",
            "observed_at",
            "source_revision",
            "startup_provider_sha256",
            "fusion_version",
        }
        if launch_binding is not None:
            expected.add("launch_binding_sha256")
        require(
            set(seen) == expected
            and seen.get("launch_binding_sha256") == launch_binding
            and type(seen["version"]) is int
            and seen["version"] == 1
            and seen["scope"] == startup.RECEIPT_SCOPE
            and seen["startup_context"] == "vendor_application_startup"
            and seen["profile_sha256"] == request["profile_sha256"]
            and seen["request_sha256"] == sha256(raw)
            and seen["peer"]
            == peer
            == startup.executable_peer(process_peer, peer["pid"])
            and seen["source_revision"] == config["source_revision"]
            and seen["startup_provider_sha256"] == profile["startup_provider_sha256"]
            and request["issued_at"] <= seen["observed_at"] < request["deadline"]
            and seen["observed_at"] <= time.time()
            and file_bytes(args.installation) == installation
            and sha256(lifecycle) == profile["lifecycle_sha256"]
            and os.fspath(verified_bundle["executable"]) == peer["executable"]
            and file_bytes(args.profile) == raw_profile
            and sha256(file_bytes(profile["installed_bootstrap"]))
            == profile["bootstrap_sha256"]
            and sha256(
                file_bytes(
                    Path(profile["installed_bootstrap"]).with_suffix(".manifest")
                )
            )
            == profile["manifest_sha256"]
            and isinstance(seen["fusion_version"], str)
            and 0 < len(seen["fusion_version"]) <= 128,
            "Fusion startup response differs from its exact owner challenge or deployment",
        )
        if retain is not None:
            retain(reply)
        return {
            "status": "vendor_bootstrap_startup_observed",
            "profile_sha256": request["profile_sha256"],
            "receipt_sha256": sha256(reply),
            "source_revision": seen["source_revision"],
            "peer": {key: value for key, value in peer.items() if key != "executable"},
        }
    finally:
        require(file_bytes(active) == raw, "startup challenge pointer changed")
        active.unlink()
        sync_directory(root)


def wait_response(root, request, stop_at):
    path = startup.response_path(root, request["challenge"])
    while time.monotonic() < stop_at and time.time() < request["deadline"]:
        try:
            return file_bytes(path)
        except FileNotFoundError:
            time.sleep(0.05)
    raise StartupUnavailable("fresh Fusion startup proof unavailable")


def main():
    parser = argparse.ArgumentParser(
        description="Stage or observe the opt-in macOS Fusion startup add-in"
    )
    parser.add_argument("--installation", type=Path, required=True)
    parser.add_argument("--lifecycle", type=Path, required=True)
    modes = parser.add_subparsers(dest="mode", required=True)
    stage = modes.add_parser("prepare")
    stage.add_argument("--output", type=Path, required=True)
    stage.add_argument("--installed-addin", type=Path, required=True)
    observation = modes.add_parser("observe")
    observation.add_argument("--profile", type=Path, required=True)
    observation.add_argument("--pid", type=int, required=True)
    observation.add_argument("--wait-seconds", type=int, default=10)
    args = parser.parse_args()
    try:
        inputs = owner_inputs(args.installation, args.lifecycle)
        if args.mode == "prepare":
            result = prepare(args, *inputs)
        else:
            require(
                1 <= args.wait_seconds <= startup.MAX_SECONDS,
                "invalid Fusion startup wait",
            )
            result = observe(args, *inputs)
    except (
        OSError,
        ValueError,
        KeyError,
        TypeError,
        AttributeError,
        OverflowError,
        RecursionError,
        subprocess.SubprocessError,
    ) as error:
        print(
            f"Fusion startup observation unavailable ({type(error).__name__})",
            file=sys.stderr,
        )
        return 1
    print(encoded(result).decode(), end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
