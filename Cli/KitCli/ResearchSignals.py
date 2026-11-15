from collections.abc import Iterator
from contextlib import contextmanager as ContextScope
from functools import partial as BindSignal
from signal import SIGINT, SIGTERM, getsignal as GetSignal, signal as SetSignal
from subprocess import Popen
from sys import platform as KPlatform

from KitCli.RouteSignalMut import RouteSignalMut


# signal ownership must precede spawning and restore callers even when process creation fails
@ContextScope
def ResearchSignals() -> Iterator[tuple[list[Popen[bytes]], list[int]]]:
    SignalNumbers = []
    if KPlatform != "win32":
        from signal import SIGCONT, SIGHUP, SIGQUIT, SIGTSTP, SIGUSR1, SIGUSR2

        SignalNumbers = [
            SIGINT,
            SIGTERM,
            SIGHUP,
            SIGQUIT,
            SIGUSR1,
            SIGUSR2,
            SIGTSTP,
            SIGCONT,
        ]
    PendingSignals: list[int] = []
    ChildProcesses: list[Popen[bytes]] = []
    PreviousHandlers = {Number: GetSignal(Number) for Number in SignalNumbers}
    try:
        for SignalNumber in SignalNumbers:
            _ = SetSignal(
                SignalNumber, BindSignal(RouteSignalMut, ChildProcesses, PendingSignals)
            )
        yield ChildProcesses, PendingSignals
    finally:
        for SignalNumber, Handler in PreviousHandlers.items():
            _ = SetSignal(SignalNumber, Handler)
