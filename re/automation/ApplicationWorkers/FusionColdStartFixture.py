import json
import os
import plistlib
import sys
from pathlib import Path

from ApplicationProtocol import file_bytes
from AppKitQuitDelegateFixture import build_fixture
from FusionStartupFixture import prepare
from MacApplicationPeer import process_peer
from MacProcessExit import observe_exit, watch_peer


def stage(root, installation):
    script = Path(__file__).with_name("FusionStartupFixture.py")
    binary = build_fixture(
        root, name="InitialStartupWitness", executable_source=script.with_suffix(".m")
    )
    info = binary.parents[2] / "Contents/Info.plist"
    properties = plistlib.loads(file_bytes(info))
    properties["KitColdStartFixture"] = [
        sys.base_prefix,
        str(script),
        str(root),
        "vendor",
    ]
    info.write_bytes(plistlib.dumps(properties))
    prepare(root, binary, installation=installation)


def interrupt(arguments):
    import FusionOwnerColdStart as owner

    def stop_after_peer(*_):
        os._exit(74)

    owner.ColdStart.prove_startup = stop_after_peer
    sys.argv[1:] = arguments
    return owner.main()


def cleanup(root, endpoint):
    try:
        raw = file_bytes(endpoint / "cold-start-peer.json")
        peer = json.loads(raw)["peer"]
    except FileNotFoundError:
        try:
            target = json.loads(file_bytes(root / "ready.json"))["pid"]
            peer = {
                key: value
                for key, value in process_peer(target).items()
                if key != "executable"
            }
        except (OSError, ValueError):
            (root / "stop").touch()
            return
    executable = root / "InitialStartupWitness.app/Contents/MacOS/InitialStartupWitness"
    with watch_peer(peer, executable) as monitor:
        (root / "stop").touch()
        assert observe_exit(monitor, peer, 10) is not None


if __name__ == "__main__":
    mode, *arguments = sys.argv[1:]
    if mode == "interrupt":
        sys.exit(interrupt(arguments))
    first, second = map(Path, arguments)
    if mode == "stage":
        stage(first, second)
    else:
        cleanup(first, second)
