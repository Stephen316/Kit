import json as JsonCodec

from tests.Research.Applications.DispatchHost import DispatchHost


# queue assertions must read responses from a separate client process through the real fixture entry point
def RunQueueClient(Harness: DispatchHost, ModeName: str = "echo") -> dict[str, object]:
    Client = Harness.StartClient(ModeName)
    Output, ErrorText = Client.communicate(timeout=30)
    assert Client.returncode == 0, Output + ErrorText
    Result: dict[str, object] = JsonCodec.loads(Output)
    return Result
