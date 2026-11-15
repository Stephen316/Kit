import json as JsonCodec

from tests.Research.Applications.DispatchHost import DispatchHost


# a replacement host needs to prove it can distinguish retained application custody from a fresh run
def AssertRetained(Harness: DispatchHost, OldProcessId: int) -> None:
    Second = Harness.StartHost()
    try:
        Harness.WaitHost(Second.pid)
        Client = Harness.StartClient()
        Output, ErrorText = Client.communicate(timeout=30)
        assert Client.returncode == 0, ErrorText
        assert JsonCodec.loads(Output)["outcome"] == "waiting_application"
        assert Second.pid != OldProcessId
        Fence = JsonCodec.loads(
            (Harness.Endpoint / "fence.json").read_text(encoding="utf-8")
        )
        assert Fence["reason"] == "acceptance_required"
        assert list(Harness.Endpoint.glob("jobs/*/fixture.bin"))
    finally:
        Second.terminate()
        _ = Second.communicate(timeout=15)
