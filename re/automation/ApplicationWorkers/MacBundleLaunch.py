import json
import os
import subprocess
import sys
import time
from pathlib import Path
from tempfile import TemporaryDirectory

from ApplicationProtocol import identity, require
from MacApplicationPeer import process_peer

SWIFT = "/usr/bin/swift"


class MacLaunchError(ValueError):
    def __init__(self, invocation):
        self.returncode = invocation.returncode
        self.provider_stderr = invocation.stderr[-2048:].decode(
            "utf-8", errors="replace"
        )
        reason = {
            2: "a running application counterpart prevents replacement launch",
            3: "macOS LaunchServices did not return an exact process",
            4: "macOS LaunchServices reply exceeded the deadline",
            5: "macOS replacement bundle differs from its reviewed pin",
            6: "macOS replacement request custody is unavailable",
            7: "macOS replacement fence changed before launch",
        }.get(
            self.returncode, "macOS replacement launch did not return an exact process"
        )
        super().__init__(reason)


def available(expected_uid=None):
    require(
        sys.platform == "darwin" and os.access(SWIFT, os.X_OK),
        "Fusion replacement launch requires the installed macOS Swift toolchain",
    )
    uid = os.getuid()
    require(
        uid > 0
        and uid == os.geteuid()
        and (expected_uid is None or uid == expected_uid),
        "Fusion replacement launch requires the same unprivileged owner",
    )


def launch_bundle(
    source, bundle, earliest, old_peer, seconds, request_path, request_sha256
):
    available(old_peer["uid"])
    expected = bundle["executable"]
    application = expected.parents[2]
    with TemporaryDirectory(prefix="kit-mac-launch-") as temporary:
        script = Path(temporary) / "MacReplacementLaunch.swift"
        script.write_bytes(source)
        invocation = subprocess.run(
            [
                SWIFT,
                str(script),
                str(application),
                str(expected),
                bundle["bundle_identifier"],
                bundle["info_sha256"],
                bundle["executable_sha256"],
                str(seconds),
                str(request_path),
                request_sha256,
            ],
            capture_output=True,
            check=False,
            timeout=seconds + 5,
        )
    if invocation.returncode != 0 or not 0 < len(invocation.stdout) <= 4096:
        raise MacLaunchError(invocation)
    reply = json.loads(invocation.stdout)
    pid = reply["pid"]
    dispatched = reply["dispatched_at"]
    require(
        reply["bundle"] == str(application)
        and reply["bundle_identifier"] == bundle["bundle_identifier"]
        and reply["executable"] == str(expected)
        and type(pid) is int
        and pid > 0
        and pid != old_peer["pid"]
        and type(dispatched) in (int, float)
        and earliest <= dispatched <= time.time(),
        "macOS provider returned a different or pre-existing application",
    )
    peer = process_peer(pid)
    host = identity(pid)
    require(
        host is not None
        and peer["executable"] == expected
        and peer["uid"] == old_peer["uid"]
        and peer["started_unix_microseconds"] / 1_000_000 >= dispatched
        and peer["started_unix_microseconds"] > old_peer["started_unix_microseconds"]
        and process_peer(pid) == peer,
        "macOS replacement does not match the exact fresh owned executable",
    )
    return {
        "host": host,
        "peer": {key: value for key, value in peer.items() if key != "executable"},
        "dispatched_at": dispatched,
    }
