import json
import os
import runpy
import shutil
import subprocess
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent))

import FusionStartupEvidence as startup
from AppKitQuitDelegateFixture import build_fixture, wait_record
from ApplicationProtocol import STARTUP_MANIFEST, encoded, file_bytes, sha256, write_new
from FusionArchiveControlFixture import attach_control
from FusionReadinessFixture import IdleEventSource, setup

TOOL = Path(__file__).with_name("FusionStartupProvision.py")
ROOT = Path(__file__).resolve().parents[3]


def invoke(installation, lifecycle, *arguments, expected=0):
    outcome = subprocess.run(
        [
            sys.executable,
            "-B",
            str(TOOL),
            "--installation",
            str(installation),
            "--lifecycle",
            str(lifecycle),
            *map(str, arguments),
        ],
        capture_output=True,
        check=False,
        text=True,
        timeout=25,
    )
    assert outcome.returncode == expected, outcome.stdout + outcome.stderr
    return json.loads(outcome.stdout) if not expected else None


def prepare(root, binary, *, installation=None):
    if installation is None:
        installation, endpoint = setup(root)
    else:
        endpoint = Path(json.loads(file_bytes(installation))["endpoint"])
        write_new(
            root / "config.json",
            encoded(
                {
                    "allowed_root": str(ROOT / "re/automation/PairedCaptures"),
                    "dispatch": str(installation),
                }
            ),
        )
    profile = root / "Lifecycle.json"
    bundle = binary.parents[2]
    write_new(
        profile,
        encoded(
            {
                "version": 1,
                "installation_sha256": sha256(file_bytes(installation)),
                "bundle": str(bundle),
                "info_sha256": sha256(file_bytes(bundle / "Contents/Info.plist")),
                "executable_sha256": sha256(file_bytes(binary)),
            }
        ),
    )
    staged = root / "Staged"
    installed = root / startup.ADDIN
    assert (
        invoke(
            installation,
            profile,
            "prepare",
            "--output",
            staged,
            "--installed-addin",
            installed,
        )["status"]
        == "startup_copy_prepared"
    )
    assert not installed.exists()
    shutil.copytree(staged / startup.ADDIN, installed)
    manifest = json.loads(file_bytes(installed / f"{startup.ADDIN}.manifest"))
    default = json.loads(file_bytes(ROOT / STARTUP_MANIFEST))
    assert default["runOnStartup"] is False
    assert manifest == {**default, "runOnStartup": True}
    boot = staged / "startup-profile.json"
    settings = root / "config.json"
    content = {**json.loads(file_bytes(settings)), "startup": str(boot)}
    settings.write_bytes(encoded(content))
    return installation, profile, boot, endpoint


def host(root, case):
    app = IdleEventSource(root, case)
    if case == "loading":
        app.isStartupComplete = False
    adsk = ModuleType("adsk")
    core = ModuleType("adsk.core")
    fusion = ModuleType("adsk.fusion")
    core.Application = SimpleNamespace(get=lambda: app)
    core.CustomEventHandler = object
    adsk.core = core
    adsk.fusion = fusion
    attach_control(app, fusion, ROOT)
    sys.modules.update(adsk=adsk, **{"adsk.core": core, "adsk.fusion": fusion})
    script = root / startup.ADDIN / f"{startup.ADDIN}.py"
    bootstrap = runpy.run_path(str(script))
    runtime = bootstrap["run"].__globals__
    runtime.update(HOME=root, QUEUE=root / "Legacy", IDLE_SECONDS=0.025)
    bootstrap["run"]({"IsApplicationStartup": case != "manual"})
    write_new(root / "ready.json", encoded(runtime["state"]["dispatch"].host))
    try:
        while not (root / "stop").exists():
            app.deliver()
    finally:
        bootstrap["stop"]({})


def exercise(root, binary, case):
    installation, lifecycle, profile, endpoint = prepare(root, binary)
    process = subprocess.Popen(
        [str(binary), sys.base_prefix, __file__, str(root), case],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        ready, _ = wait_record(root / "ready.json", process)
        assert ready["pid"] == process.pid
        observation = ("observe", "--profile", profile, "--pid", process.pid)
        box = endpoint / startup.MAILBOX
        if case != "vendor":
            invoke(
                installation, lifecycle, *observation, "--wait-seconds", "1", expected=1
            )
            assert len(list(box.glob("*.request.json"))) == 1
            assert not list(box.glob("*.response.json"))
            return
        first = invoke(installation, lifecycle, *observation)
        second = invoke(installation, lifecycle, *observation)
        assert (
            first["status"] == second["status"] == "vendor_bootstrap_startup_observed"
        )
        assert first["peer"] == second["peer"] and first["peer"]["pid"] == process.pid
        receipts = {sha256(file_bytes(path)) for path in box.glob("*.response.json")}
        assert (
            receipts == {first["receipt_sha256"], second["receipt_sha256"]}
            and len(receipts) == 2
        )
        invoke(
            installation,
            lifecycle,
            "observe",
            "--profile",
            profile,
            "--pid",
            os.getpid(),
            expected=1,
        )
        manifest = root / startup.ADDIN / f"{startup.ADDIN}.manifest"
        manifest.write_bytes(
            encoded({**json.loads(file_bytes(manifest)), "runOnStartup": False})
        )
        invoke(installation, lifecycle, *observation, expected=1)
        assert len(list(box.glob("*.request.json"))) == 2
    finally:
        (root / "stop").touch()
        try:
            output, errors = process.communicate(timeout=8)
        except subprocess.TimeoutExpired:
            process.kill()
            process.communicate(timeout=5)
            raise
        assert process.returncode == 0, output + errors


def main():
    if len(sys.argv) == 3:
        host(Path(sys.argv[1]), sys.argv[2])
        return
    root = Path(sys.argv[1])
    binary = build_fixture(
        root, name="StartupWitness", executable_source=Path(__file__).with_suffix(".m")
    )
    for case in ("vendor", "manual", "loading"):
        path = root / case
        path.mkdir(mode=0o700)
        exercise(path, binary, case)
    print(
        json.dumps(
            {
                "vendor_startup": True,
                "manual_refused": True,
                "loading_refused": True,
                "wrong_peer_refused": True,
                "manifest_change_refused": True,
                "fresh_receipts": 2,
            }
        )
    )


if __name__ == "__main__":
    main()
