import json
import os
import subprocess
import sys
import time
from pathlib import Path

from ApplicationProtocol import (
    FUSION_PROVIDER,
    encoded,
    file_bytes,
    record,
    require,
    sha256,
    write_new,
)
from FusionExitEvidence import seal_and_watch
from FusionExitRecords import exit_evidence
from MacApplicationPeer import process_peer
from MacProcessExit import PeerUnavailable

FENCE = b"retained disposable restart fence\n"


def run_target(root):
    peer = process_peer(os.getpid())
    write_new(
        root / "target-ready.json",
        encoded({**peer, "executable": os.fspath(peer["executable"])}),
    )
    line = sys.stdin.readline()
    if line.strip() == "replace":
        os.execv(sys.executable, [sys.executable, "-B", "-c", "pass"])


def ready_grant(peer):
    now = time.time()
    provider = {
        "provider": FUSION_PROVIDER,
        "host": {"pid": peer["pid"], "started": "fixture accepted host"},
        "source_sha256": "f" * 64,
    }
    grant = {**provider, "status": "granted", "expires_at": now + 20}
    grant_sha256 = sha256(encoded(grant))
    consumption = {
        **provider,
        "status": "consumed",
        "grant_sha256": grant_sha256,
        "observed_at": now,
    }
    return {
        "status": "restart_readiness_observed",
        "intent_sha256": "1" * 64,
        "peer": peer,
        "provider_source_sha256": provider["source_sha256"],
        "documents": 0,
        "observed_at": now,
        "expires_at": grant["expires_at"],
        "grant": grant,
        "grant_sha256": grant_sha256,
        "consumption": consumption,
        "consumption_sha256": sha256(encoded(consumption)),
    }


def run_observer(root, seconds):
    expected = record(root / "peer.json")
    executable = Path(expected.pop("executable"))
    readiness = ready_grant(expected)

    def verify():
        require(
            file_bytes(root / "fence.json") == FENCE, "fixture lost the retained fence"
        )

    def notify(intent_sha256):
        write_new(root / "armed.json", encoded({"quit_intent_sha256": intent_sha256}))

    try:
        status = seal_and_watch(
            root, readiness, executable, sha256(FENCE), seconds, verify, notify
        )
    except PeerUnavailable as error:
        print(f"{type(error).__name__}: {error}", file=sys.stderr)
        status = {"status": "peer_unavailable"}
    except ValueError as error:
        print(f"{type(error).__name__}: {error}", file=sys.stderr)
        status = {"status": "refused"}
    print(json.dumps(status))


def wait_marker(root, name, process, failure):
    deadline = time.monotonic() + 10
    while True:
        terminated = process.poll() is not None
        try:
            return record(root / name)
        except FileNotFoundError:
            if terminated or time.monotonic() >= deadline:
                break
        time.sleep(0.02)
    try:
        stdout, stderr = process.communicate(timeout=0.1)
    except subprocess.TimeoutExpired as error:
        stdout, stderr = error.stdout, error.stderr
    raise AssertionError(
        f"{failure} (return code {process.returncode!r}, "
        f"stdout {(stdout or '')[-2000:]!r}, stderr {(stderr or '')[-2000:]!r})"
    )


def check_receipt(root, result, armed, case):
    identifier = armed["quit_intent_sha256"]
    intent = file_bytes(root / f"quit-intent-{identifier}.json")
    assert sha256(intent) == identifier
    status = json.loads(intent)
    assert status["readiness"]["consumption"]["status"] == "consumed"
    assert status["fence_sha256"] == sha256(FENCE)
    receipt = root / f"quit-exit-{identifier}.json"
    if case != "exit":
        assert not receipt.exists()
        return
    assert result["quit_intent_sha256"] == identifier
    receipt_bytes = file_bytes(receipt)
    assert result["receipt_sha256"] == sha256(receipt_bytes)
    saved = json.loads(receipt_bytes)
    assert saved == {
        key: value for key, value in result.items() if key != "receipt_sha256"
    }
    assert saved["cause"] == "unverified"
    assert saved["peer"] == status["readiness"]["peer"]
    accepted, observed = exit_evidence(root, identifier, result["receipt_sha256"])
    assert accepted == status["readiness"] and observed == saved
    try:
        exit_evidence(root, identifier, "0" * 64)
    except ValueError:
        pass
    else:
        raise AssertionError(
            "replacement intake accepted the wrong exit receipt digest"
        )


def run_pair(root, target, case):
    ready = wait_marker(
        root, "target-ready.json", target, "Fusion exit target did not become ready"
    )
    peer = process_peer(target.pid)
    assert ready == {
        **peer,
        "executable": os.fspath(peer["executable"]),
    }, "Fusion exit target readiness differs from its exact kernel identity"
    if case == "mismatched":
        peer["started_unix_microseconds"] += 1
    write_new(
        root / "peer.json",
        encoded({**peer, "executable": os.fspath(peer["executable"])}),
    )
    write_new(root / "fence.json", FENCE)
    if case == "gone":
        target.communicate("exit\n", timeout=10)
        assert target.returncode == 0
    observer = subprocess.Popen(
        [
            sys.executable,
            "-B",
            __file__,
            "observe",
            str(root),
            "1" if case == "timeout" else "10",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        armed = (
            None
            if case in ("gone", "mismatched")
            else wait_marker(
                root, "armed.json", observer, "Fusion exit observer did not arm"
            )
        )
        if case == "changed":
            (root / "fence.json").write_bytes(b"changed fixture fence\n")
        if case in ("exit", "replaced", "changed"):
            target.communicate(
                "replace\n" if case == "replaced" else "exit\n", timeout=10
            )
            assert target.returncode == 0
        stdout, stderr = observer.communicate(timeout=12)
        assert observer.returncode == 0, stderr
        result = json.loads(stdout)
        if armed is None:
            assert not list(root.glob("quit-*.json"))
        else:
            check_receipt(root, result, armed, case)
        return result
    finally:
        if observer.poll() is None:
            observer.communicate(timeout=12)


def exercise(root, case):
    target = subprocess.Popen(
        [sys.executable, "-B", __file__, "target", str(root)],
        stdin=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        print(json.dumps(run_pair(root, target, case)))
    finally:
        if target.poll() is None:
            target.communicate("exit\n", timeout=10)


if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "target":
        run_target(Path(sys.argv[2]))
    elif mode == "observe":
        run_observer(Path(sys.argv[2]), int(sys.argv[3]))
    else:
        exercise(Path(sys.argv[2]), sys.argv[3])
