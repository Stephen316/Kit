import json
import secrets
import subprocess
import sys
import time
from pathlib import Path
from plistlib import dumps

from ApplicationProtocol import encoded, file_bytes, owner_lock, sha256, write_new
from MacApplicationPeer import process_peer
from MacProcessExit import observe_exit, verify_peer, watch_peer


def build_fixture(root):
    bundle = root / "QuitWitness.app"
    binary = bundle / "Contents/MacOS/QuitWitness"
    binary.parent.mkdir(parents=True)
    (bundle / "Contents/Info.plist").write_bytes(
        dumps(
            {
                "CFBundleIdentifier": "org.unicad.kit.appkitquitfixture",
                "CFBundleExecutable": binary.name,
                "CFBundlePackageType": "APPL",
                "LSUIElement": True,
            }
        )
    )
    source = Path(__file__).with_suffix(".m")
    compiled = subprocess.run(
        [
            "/usr/bin/clang",
            "-fobjc-arc",
            "-framework",
            "Cocoa",
            "-o",
            str(binary),
            str(source),
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=25,
    )
    assert compiled.returncode == 0, compiled.stderr
    return binary


def wait_record(path, process):
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        try:
            raw = file_bytes(path)
            return json.loads(raw), raw
        except FileNotFoundError:
            if process.poll() is not None and not path.exists():
                _, stderr = process.communicate(timeout=1)
                raise AssertionError(
                    f"AppKit fixture exited before {path.name}: {stderr}"
                )
            time.sleep(0.025)
    raise AssertionError(f"AppKit fixture did not publish {path.name}")


def check_record(value, attempt, peer, status):
    assert value["attempt_id"] == attempt and value["pid"] == peer["pid"]
    assert value["main_thread"] is True and value["status"] == status


def run_request(root, process, binary, attempt, case):
    observed = process_peer(process.pid)
    assert observed["executable"] == binary
    peer = {key: value for key, value in observed.items() if key != "executable"}
    ready, _ = wait_record(root / "Ready.json", process)
    check_record(ready, attempt, peer, "ready")
    request = encoded({"attempt_id": attempt, "pid": peer["pid"]})
    with owner_lock(root / "dispatch.lock"), watch_peer(peer, binary) as monitor:
        write_new(root / "Request.json", request)
        action, action_bytes = wait_record(root / "Attempt.json", process)
        check_record(action, attempt, peer, "authorization_consumed")
        decision, decision_bytes = wait_record(root / "Delegate.json", process)
        check_record(
            decision, attempt, peer, "accept" if case == "accept" else "cancel"
        )
        event = observe_exit(monitor, peer, 10 if case == "accept" else 0.2)
        if case == "accept":
            assert event is not None
            notification, notification_bytes = wait_record(
                root / "WillTerminate.json", process
            )
            check_record(notification, attempt, peer, "will_terminate")
            assert process.wait(timeout=5) == 0
        else:
            assert event is None and process.poll() is None
            notification_bytes = None
            write_new(root / "Replay.json", request)
            duplicate, _ = wait_record(root / "Duplicate.json", process)
            check_record(duplicate, attempt, peer, "duplicate_refused")
            assert file_bytes(root / "Attempt.json") == action_bytes
            assert file_bytes(root / "Delegate.json") == decision_bytes
            assert not (root / "WillTerminate.json").exists()
            verify_peer(peer, binary)
            assert observe_exit(monitor, peer, 0) is None
    reply_path = root / "Return.json"
    if case == "cancel":
        reply, _ = wait_record(reply_path, process)
        check_record(reply, attempt, peer, "quit_call_returned")
    if case == "cancel-reply-loss":
        assert not reply_path.exists()
    receipt = {
        "scope": "disposable_appkit_quit_witness",
        "case": case,
        "peer": peer,
        "attempt_sha256": sha256(action_bytes),
        "delegate_sha256": sha256(decision_bytes),
        "delegate_decision": decision["status"],
        "returned_receipt_present": reply_path.exists(),
        "duplicate_refused": (root / "Duplicate.json").exists(),
        "will_terminate_sha256": (
            sha256(notification_bytes) if notification_bytes is not None else None
        ),
        "kernel_exit": event,
    }
    write_new(root / "ExitObservation.json", encoded(receipt))
    return receipt


def exercise(root, case):
    binary = build_fixture(root)
    attempt = secrets.token_hex(16)
    process = subprocess.Popen(
        [str(binary), str(root), case, attempt], stderr=subprocess.PIPE, text=True
    )
    try:
        evidence = run_request(root, process, binary, attempt, case)
    finally:
        if process.poll() is None:
            (root / "FixtureStop").touch()
        _, stderr = process.communicate(timeout=10)
        assert process.returncode == 0, stderr
    print(json.dumps(evidence))


if __name__ == "__main__":
    exercise(Path(sys.argv[1]), sys.argv[2])
