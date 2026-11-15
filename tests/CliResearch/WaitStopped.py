from subprocess import run as RunProcess
from time import sleep as WaitSeconds


# job control coverage must observe both actual processes stopped before requesting resume
def WaitStopped(ProcessIds: tuple[int, int]) -> None:
    States: list[str] = []
    for _ in range(300):
        States = [
            RunProcess(
                ("ps", "-o", "stat=", "-p", str(ProcessId)),
                capture_output=True,
                text=True,
                check=True,
                timeout=10,
            ).stdout.strip()
            for ProcessId in ProcessIds
        ]
        if all(State.startswith("T") for State in States):
            return
        WaitSeconds(0.01)
    raise AssertionError(f"Research processes did not stop: {States}")
