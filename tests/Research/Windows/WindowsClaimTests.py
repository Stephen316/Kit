import json as JsonCodec
import subprocess as Subprocess
import sys as System
from pathlib import Path as FilePath

import pytest as Pytest

from tests.Research.SupervisorClient import FixtureJob, KRepoRoot, SessionHost

# private child fault injection runs the real transaction before withholding its acknowledgement
KFaultServer = """
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, AUTOMATION)
import ClaimProcess

def lost_reply(stream, response):
    if "result" not in response or response["result"]["job"] is None:
        os._exit(65)
    if MODE == "held":
        time.sleep(60)
    os._exit(66)

ClaimProcess.send_frame = lost_reply
ClaimProcess.run(Path(sys.argv[1]), Path(sys.argv[2]), sys.stdin.buffer, sys.stdout.buffer)
"""

# isolated host processes load the same supervisor and claim transport as the command
KClaimSetup = """
import json
import subprocess
import sys
from pathlib import Path

automation, config, fault = sys.argv[1:]
sys.path.insert(0, automation)
import Adapters
import WindowsClaimTransport
from ClaimWire import ClaimExchangeLost
from RecoveryFence import StaleOwner
from Supervisor import Supervisor, read_config
from WindowsProcess import process_start

host = Supervisor(read_config(config), True)
"""

# the supervisor must surface an uncertain exchange before starting a worker
KClaimFault = """
if fault != "steady":
    WindowsClaimTransport.SERVER = Path(fault)
    Adapters.CONTROLLER_TIMEOUT = 5
    try:
        host.run(2, 20)
    except ClaimExchangeLost:
        print(json.dumps({"claim_lost": True, "helper_closed": host.adapter.claim_helper is None}))
    else:
        raise AssertionError("missing acknowledgement was accepted")
    raise SystemExit(0)
"""

# steady claims must reuse one helper and then refuse a replaced owner
KClaimSteady = """
host.acquire()
host.recover()
host.synchronize()
adapter = host.adapter
adapter.warm_claims = True
first = adapter.ClaimJob("decode", "probe:windows", host.claims / "1-aaaaaaaa.json")
helper = adapter.claim_helper
pid, identity = helper.process.pid, helper.process.identity
second = adapter.ClaimJob("decode", "probe:windows", host.claims / "2-bbbbbbbb.json")
assert first["job"]["id"] == "warm:one" and second["job"]["id"] == "warm:two"
assert "lease_token" not in first and "lease_token" not in second
assert adapter.claim_helper is helper and process_start(pid) == identity
adapter.CloseClaimHelper()
assert process_start(pid) != identity

assert adapter.ClaimJob("decode", "probe:windows", host.claims / "3-cccccccc.json") is None
another = adapter.claim_helper
pid, identity = another.process.pid, another.process.identity
subprocess.run(adapter.command + ["rotate-owner", "--new-owner", "b" * 64], check=True, capture_output=True)
try:
    adapter.ClaimJob("decode", "probe:windows", host.claims / "4-dddddddd.json")
except StaleOwner:
    assert adapter.claim_helper is None and process_start(pid) != identity
    print(json.dumps({"reused": True, "stale_refused": True, "helper_closed": True}))
else:
    raise AssertionError("retired owner acquired a claim")
"""


# each claim scenario needs an isolated supervisor with its own controller owner and windows job
def RunClaimHost(Harness: SessionHost, ModeText: str) -> list[dict[str, object]]:
    SourcePath = KRepoRoot / "re/automation"
    ResultInfo = Subprocess.run(
        [
            System.executable,
            "-c",
            KClaimSetup + KClaimFault + KClaimSteady,
            str(SourcePath),
            str(Harness.ConfigFile),
            ModeText,
        ],
        capture_output=True,
        env=Harness.Environment,
        text=True,
        check=False,
        timeout=45,
    )
    assert ResultInfo.returncode == 0, ResultInfo.stderr
    return [JsonCodec.loads(LineText) for LineText in ResultInfo.stdout.splitlines()]


# a single warm child must reuse its identity and reject a rotated controller owner
@Pytest.mark.skipif(System.platform != "win32", reason="Windows process boundary")
def CheckWarmClaim(TmpPath: FilePath) -> None:
    Harness = SessionHost(TmpPath, {"decode": 2}, {"fixture.decode": "decode"})
    Harness.SubmitJobs(
        [
            FixtureJob(
                "warm:one", "fixture.decode", lease_seconds=60, timeout_seconds=120
            ),
            FixtureJob(
                "warm:two", "fixture.decode", lease_seconds=60, timeout_seconds=120
            ),
        ]
    )
    Events = RunClaimHost(Harness, "steady")
    assert Events[-1] == {"reused": True, "stale_refused": True, "helper_closed": True}


# a committed claim with no reply must survive for exactly one new owner recovery
@Pytest.mark.skipif(System.platform != "win32", reason="Windows process boundary")
@Pytest.mark.parametrize("FailureMode", ["exited", "held"])
def CheckLostClaim(TmpPath: FilePath, FailureMode: str) -> None:
    Harness = SessionHost(TmpPath, {"decode": 1}, {"fixture.decode": "decode"})
    Harness.SubmitJobs(
        [
            FixtureJob(
                "warm:lost", "fixture.decode", lease_seconds=60, timeout_seconds=120
            )
        ]
    )
    SourcePath = KRepoRoot / "re/automation"
    FaultFile = TmpPath / "FaultServer.py"
    _ = FaultFile.write_text(
        f"AUTOMATION = {str(SourcePath)!r}\nMODE = {FailureMode!r}\n" + KFaultServer,
        encoding="utf-8",
    )
    Events = RunClaimHost(Harness, str(FaultFile))
    assert Events[-1] == {"claim_lost": True, "helper_closed": True}
    assert [Event.get("event") for Event in Events].count("claim_transport_failed") == 1
    assert all(Event.get("event") != "started" for Event in Events)
    Pending = Harness.ReadJob("warm:lost")
    assert Pending["state"] == "running" and Pending["attempts"] == 1
    Claims = TmpPath / "SupervisorState" / "claims"
    assert len(list(Claims.glob("*.json"))) == 1
    Hidden = Claims / (".claim-stage-" + "a" * 24)
    _ = Hidden.write_text("interrupted write", encoding="utf-8")
    _ = Harness.RunIdle(IdleSeconds=4, MaxSeconds=20)
    Accepted = Harness.ReadJob("warm:lost")
    assert Accepted["state"] == "completed" and Accepted["attempts"] == 2
    assert not list(Claims.iterdir())
