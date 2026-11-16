import json
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ApplicationProtocol import (
    FUSION_PROVIDER,
    encoded,
    identity,
    pin,
    sha256,
    write_new,
)
from Ledger import Ledger
from MacReplacementFixture import fixture_bundle

RESOURCE = "application:fusion:reset-fixture"
INSTALLATION = "fusion:reset-fixture"
ROOT = Path(__file__).resolve().parents[3]


def setup(root, bundle):
    revision = subprocess.check_output(
        ["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True
    ).strip()
    installation = root / "Installation.json"
    endpoint = root / "endpoint"
    endpoint.mkdir(mode=0o700)
    install = encoded(
        {
            "version": 1,
            "installation": INSTALLATION,
            "application": "fusion",
            "endpoint": str(endpoint),
            "source_root": str(ROOT),
            "source_revision": revision,
        }
    )
    write_new(installation, install)
    lifecycle = root / "Lifecycle.json"
    write_new(
        lifecycle,
        encoded(
            {
                "version": 1,
                "installation_sha256": sha256(install),
                "bundle": str(bundle["executable"].parents[2]),
                "info_sha256": bundle["info_sha256"],
                "executable_sha256": bundle["executable_sha256"],
            }
        ),
    )
    store = root / "Store"
    config = root / "Supervisor.json"
    write_new(
        config,
        encoded(
            {
                "state": "state",
                "controller": {"adapter": "a03", "store": str(store)},
                "registry": "registry.json",
                "pools": {"fusion": {"max_sessions": 1}},
                "resources": {RESOURCE: 1},
            }
        ),
    )
    return revision, installation, lifecycle, config, store


def dispatch_result(root, ledger, job, host, request, revision):
    work = root / "work"
    work.mkdir(mode=0o700, parents=True)
    claim = ledger.claim("fixture:reset")
    assert claim["job"]["id"] == job
    plan = claim["snapshot"]["inputs"]["plan"]["sha256"]
    action = {"host": host, "phase": "a", "plan_sha256": plan}
    dispatch = work / "dispatch.json"
    write_new(
        dispatch,
        encoded(
            {
                "version": 1,
                "provider": FUSION_PROVIDER,
                "installation": INSTALLATION,
                "source_revision": revision,
                "status": "completed",
                "host": host,
                "request_sha256": request,
                "finished_at": time.time(),
                "proof": {**action, "claim": "unqualified_application_observation"},
            }
        ),
    )
    result = {
        "session_version": 1,
        "receipt": {
            "receipt_version": 1,
            "job_id": job,
            "attempt": claim["attempt"],
            "kind": claim["job"]["kind"],
            "orphan": False,
            "stop_reason": None,
            "exit_status": 0,
            "signal": None,
        },
        "result": {
            "outcome": "completed",
            "records": {
                **action,
                "installation": INSTALLATION,
                "application": "fusion",
                "claim": "unqualified_dispatch",
                "native_qualified": False,
            },
            "artifacts": {"dispatch": pin(dispatch, dispatch.name)},
        },
    }
    path = root / "Result.json"
    write_new(path, encoded(result))
    ledger.finish(
        job,
        claim["lease_token"],
        "completed",
        path,
        "disposable native dispatch",
        output_root=work,
    )


def populate(root, store, host, revision):
    plan = root / "Plan.json"
    write_new(plan, b"pinned disposable plan")
    with Ledger(store, create=True) as ledger:
        ledger.resource(RESOURCE, True, 1)
        ledger.bind("fixture:plan", plan)
        for name, request, peer in (
            ("reused", "1" * 64, host),
            ("duplicate", "1" * 64, host),
            ("older", "2" * 64, {**host, "started": "older disposable generation"}),
        ):
            job = f"fixture:{name}"
            ledger.submit(
                {
                    "id": job,
                    "kind": "capture.fusion",
                    "resources": [RESOURCE],
                    "inputs": {
                        "plan": "fixture:plan" if name == "reused" else "fixture:stable"
                    },
                    "options": {"phase": "a"},
                    "rule_version": "fixture@1",
                    "tool_version": revision,
                }
            )
            if name == "duplicate":
                ledger.bind("fixture:stable", plan)
            dispatch_result(root / name, ledger, job, peer, request, revision)
        plan.write_bytes(b"revised disposable plan")
        ledger.bind("fixture:plan", plan)
        dispatch_result(
            root / "second-generation",
            ledger,
            "fixture:reused",
            host,
            "3" * 64,
            revision,
        )
        ledger.submit(
            {
                "id": "fixture:unattributed",
                "kind": "fixture.control",
                "resources": [RESOURCE],
                "inputs": {},
                "rule_version": "fixture@1",
                "tool_version": revision,
            }
        )
        claim = ledger.claim("fixture:reset")
        ledger.finish(
            "fixture:unattributed",
            claim["lease_token"],
            "completed",
            None,
            "controller-only fixture",
            result_record={"fixture_only": True},
        )


def run_report(installation, lifecycle, config, pid, *args):
    command = Path(__file__).with_name("FusionLifecycleOwner.py")
    completed = subprocess.run(
        [
            sys.executable,
            "-B",
            str(command),
            "--installation",
            str(installation),
            "--lifecycle",
            str(lifecycle),
            "--config",
            str(config),
            "--reset-evidence-pid",
            str(pid),
            *args,
        ],
        capture_output=True,
        check=False,
        text=True,
        timeout=25,
    )
    assert completed.returncode == 0, completed.stderr
    return json.loads(completed.stdout)


def exercise(root):
    bundle = fixture_bundle(root)
    revision, installation, lifecycle, config, store = setup(root, bundle)
    child = subprocess.Popen(
        [str(bundle["executable"])],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        host = identity(child.pid)
        assert host is not None, "disposable native process did not become live"
        time.sleep(0.1)
        populate(root, store, host, revision)
        before = (store / "ledger.sqlite3").read_bytes()
        default = run_report(installation, lifecycle, config, child.pid)
        selected = run_report(
            installation, lifecycle, config, child.pid, "--reset-evidence-limit", "2"
        )
        assert (store / "ledger.sqlite3").read_bytes() == before
        assert default["corroborated"] == selected["corroborated"] == 2
        assert selected["duplicate_dispatches"] == 1 and selected["other_peers"] == 1
        assert selected["unattributed_completions"] == 1
        assert (
            default["comparison_limit"] == 50
            and default["verified_count_reaches_limit"] is False
        )
        assert (
            selected["comparison_limit"] == 2
            and selected["verified_count_reaches_limit"] is True
        )
        print(json.dumps(selected))
    finally:
        (root / "NaturalExit").touch()
        try:
            assert child.wait(timeout=10) == 0
        except subprocess.TimeoutExpired:
            child.kill()
            child.wait(timeout=5)
            raise


if __name__ == "__main__":
    exercise(Path(sys.argv[1]))
